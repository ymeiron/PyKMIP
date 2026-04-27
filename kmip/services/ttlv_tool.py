import re, sys, io, json, argparse, select, base64
from datetime import datetime, UTC
import xml.etree.ElementTree as ET
import kmip.core.enums
from typing import Optional, Any

enums = sys.modules['kmip.core.enums']

def to_pascal(s: str) -> str:
    return ''.join(w.capitalize() for w in s.split('_') if w)

def pascal_to_snake(s: str) -> str:
    return re.sub(r'(?<!^)([A-Z])', r'_\1', s).upper()

def decode(data: bytes):
    output: str = ''
    def process(data, level=0):
        nonlocal output
        item_tag = int.from_bytes(data[:3])
        item_tag = kmip.core.enums.Tags(item_tag).name
        indent = ' ' * level
        item_type = data[3]
        item_type = kmip.core.enums.ItemType(item_type).name
        item_length = int.from_bytes(data[4:8])
        data = data[8:8+item_length]
        if item_type != 'STRUCTURE':
            representation = '????'
            match item_type:
                case 'INTEGER':
                    representation = f'"{int.from_bytes(data)}"'
                case 'TEXT_STRING':
                    representation = json.dumps(data.decode())
                case 'ENUMERATION':
                    try:
                        enum = getattr(enums, to_pascal(item_tag))
                        representation = '"' + to_pascal(enum(int.from_bytes(data)).name) + '"'
                    except:
                        representation = f'"0x{int.from_bytes(data):08x}"'
                case 'DATE_TIME':
                    timestamp = int.from_bytes(data)
                    representation = '"' + datetime.fromtimestamp(timestamp, UTC).isoformat() + '"'
                case _:
                    representation = json.dumps(data)
            output += f'{indent}<{to_pascal(item_tag)} type="{to_pascal(item_type)}" value={representation} />\n'
            return item_length, item_type
        else:
            output += f'{indent}<{to_pascal(item_tag)}>\n'
            
        while data:
            internal_length, internal_type = process(data, level+2)
            padding = 0
            if internal_type in ['INTEGER', 'ENUMERATION']:
                padding = 4
            elif internal_type in ['TEXT_STRING', 'BYTE_STRING']:
                if internal_length % 8 == 0:
                    padding = 0
                else:
                    padding = (internal_length//8 + 1)*8 - internal_length
            jump = internal_length + padding + 8
            data = data[jump:]
        output += f'{indent}</{to_pascal(item_tag)}>\n'
        return item_length, item_type
    process(data)
    output = output[:-1]
    return output


class KmipNode:
    def __init__(self, tag_name: str, type_name: str, data: Optional[str] = None):
        self.tag_name: str = tag_name
        self.tag_number: int = kmip.core.enums.Tags[pascal_to_snake(tag_name)].value
        self.type_name: str = type_name
        self.type_number: int = kmip.core.enums.ItemType[pascal_to_snake(type_name)].value
        self.padding: int = 0
        self.data: Any = data
        self.data_encoded: Optional[bytes] = None
        self.children = []
        if type_name == 'Structure':
            self.size = 0 # will be set later
            return
        if data is None:
            raise RuntimeError('Expected a value')
        match type_name:
            case 'Integer':
                self.data = int(data)
                self.size = 4
                self.padding = 4
                self.data_encoded = self.data.to_bytes(4)
            case 'LongInteger':
                self.data = int(data)
                self.size = 8
                self.data_encoded = self.data.to_bytes(8)
            case 'BigInteger':
                raise NotImplemented
            case 'Enumeration':
                self.size = 4
                self.padding = 4
                enum = getattr(enums, tag_name)
                self.data_encoded = enum[pascal_to_snake(data)].value.to_bytes(4)
            case 'Boolean':
                if data in ['True', 'true', '1']:
                    self.data = True
                elif data in ['False', 'false', '0']:
                    self.data = False
                else:
                    raise RuntimeError(f'Unknown boolean value: {data}')
                self.size = 8
                self.data_encoded = self.data.to_bytes(8)
            case 'TextString' | 'ByteString':
                # If it's a byte string, it's probably in hex or something?
                self.data_encoded = data.encode()
                self.size = len(self.data_encoded)
                self.padding = 0 if self.size % 8 == 0 else 8 - self.size % 8
            case 'DateTime':
                raise NotImplemented
            case 'Interval':
                raise NotImplemented
            case _:
                raise RuntimeError('Unknown type')
        
    def add_child(self, child):
        if self.type_name != 'Structure':
            raise RuntimeError('Only structure type can add children')
        self.children.append(child)

def build_kmip_tree(elem, size=0) -> KmipNode:
    tag_name = elem.tag
    type_name = elem.attrib.get('type', 'Structure')
    if type_name == 'Structure':
        node = KmipNode(tag_name, type_name)
        size = 0
        for child in elem:
            child_node = build_kmip_tree(child, size)
            node.add_child(child_node)
            size += 8 + child_node.size + child_node.padding
        node.size = size
        return node
    data = elem.attrib['value']
    return KmipNode(tag_name, type_name, data)

def serialize_kmip_tree(kmip_tree: KmipNode) -> bytes:
    output = io.BytesIO()
    def walk(node: KmipNode):
        nonlocal output
        output.write(node.tag_number.to_bytes(3))
        output.write(node.type_number.to_bytes(1))
        output.write(node.size.to_bytes(4))
        if node.type_name != 'Structure':
            if node.data_encoded is None:
                raise RuntimeError('Got None in data_encoded')
            output.write(node.data_encoded)
            if node.padding:
                output.write(b'\0' * node.padding)
        for child in node.children:
            walk(child)
    walk(kmip_tree)
    return output.getvalue()

def main():
    parser = argparse.ArgumentParser(prog='ttlv-tool')
    subparsers = parser.add_subparsers(dest='command', required=True)

    decode_parser = subparsers.add_parser('decode', help='Decode a TTLV stream to XML')
    decode_parser.add_argument('-o', '--output', help='output file')
    decode_parser.add_argument('-i', '--input', help='input file')

    encode_parser = subparsers.add_parser('encode', help='Encode XML to a TTLV stream')
    encode_parser.add_argument('--force', action='store_true')
    encode_parser.add_argument('-o', '--output', help='output file')
    encode_parser.add_argument('-i', '--input', help='input file')
    encode_parser.add_argument('-f', '--format', choices=['binary', 'hex', 'base64'], default='binary', help='output format')

    args = parser.parse_args()

    piped_input_flag = sys.stdin in select.select([sys.stdin], [], [], 0)[0]
    piped_output_flag = not sys.stdout.isatty()
    if piped_input_flag and args.input:
        print('Error: an input file is specified with -i or --input, but also data is piped in')
        sys.exit(1)
    if piped_output_flag and args.output:
        print('Error: an output file is specified with -o or --output, but also data is piped out')
        sys.exit(1)
    if piped_input_flag:
        data = sys.stdin.buffer.read()
    elif args.input:
        with open(args.input, 'rb') as f:
            data = f.read()
    else:
        print('Error: no input data')
        sys.exit(1)
    if args.output:
        output_stream = open(args.output, 'wb')
    else:
        output_stream = sys.stdout.buffer

    if args.command == 'decode':
        xml_string = decode(data)
        output_stream.write(xml_string.encode())
    elif args.command == 'encode':
        try:
            xml_tree = ET.fromstring(data.decode())
        except:
            print('Error: input does not appear to be XML')
            sys.exit(1)
        kmip_tree = build_kmip_tree(xml_tree)
        encoded = serialize_kmip_tree(kmip_tree)
        match args.format:
            case 'hex':
                output = encoded.hex().encode()
            case 'base64':
                output = base64.b64encode(encoded)
            case 'binary':
                output = encoded
        output_stream.write(output)

    if not piped_output_flag:
        print()
    if args.output:
        output_stream.close()
