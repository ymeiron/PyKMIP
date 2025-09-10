import asyncio
import re
import binascii
from logging import Logger
from Crypto.Protocol.SecretSharing import Shamir
from sqlcipher3 import dbapi2 as sqlcipher

socket_path = '/tmp/pykmip-sss.sock'
version = 1

class Sss:
    def __init__(self, db_path : str, logger : Logger):
        self.db_path = db_path
        self.logger = logger
        self.done = asyncio.Event()
        self.pw = None
        self.shares = dict()
        print('PyKMIP SSS: please use CLI to enter shards.')
        asyncio.run(self.run())

    def __call__(self):
        return self.pw

    async def run(self):
        server = await asyncio.start_unix_server(self.connection_handler, path=socket_path)
        async with server:
            await self.done.wait()
            server.abort_clients()

    def combine_shares(self):
        try:
            pwb = Shamir.combine(list(self.shares.items()))
        except:
            return None
        pw = binascii.hexlify(pwb).decode('ascii')
        self.logger.info("Shards completed.")
        return pw

    def validate_password(self, pw: str | None) -> bool:
        if pw is None:
            return False
        db = sqlcipher.connect(self.db_path) # assuming it has been set
        db.execute(f"pragma key='{pw}';")
        try:
            db.execute('select * from sqlite_master;').fetchall()
            db.close()
        except sqlcipher.Error as er:
            return False
        return True

    async def connection_handler(self, reader, writer):
        self.logger.info(f'SSS: client connected')
        writer.write(f'PYKMIP-SSS v{version}\n'.encode())
        well_formed_shard = re.compile(r'^\d+,[0-9a-fA-F]{32}$')
        try:
            while True:
                writer.write(f'SHARES:{len(self.shares)}\n'.encode())
                message = await reader.read(4096)
                message = message.decode('ascii').strip()
                if message.upper() == 'COMMIT':
                    self.logger.info(f'SSS: trying to combine shards')
                    pw = self.combine_shares()
                    works = self.validate_password(pw)
                    if works:
                        writer.write(b'DONE\n')
                        await writer.drain()
                        self.logger.info(f'SSS: done')
                        self.pw = pw
                        self.done.set()
                        break
                    else:
                        self.logger.info(f'SSS: failure')
                        self.shares = dict()
                        continue
                elif well_formed_shard.match(message):
                    idx, share = message.split(',')
                    idx = int(idx)
                    share = binascii.unhexlify(share)
                    old_share = self.shares.get(idx)
                    if share == old_share:
                        writer.write(f'REPEATED #{idx}\n'.encode())
                        self.logger.info(f'SSS: shard #{idx} repeated')
                    else:
                        self.shares[idx] = share
                        writer.write(f'UPDATED #{idx}\n'.encode())
                        self.logger.info(f'SSS: shard #{idx} entered')
                elif not message:
                    break
                else:
                    writer.write('INPUT ERROR\n'.encode())
        except Exception as e:
            self.logger.info(f'SSS: client error: {e}')

### CLI ###
import argparse

async def get_messages(reader: asyncio.StreamReader) -> list[str]:
    buffer = await reader.read(1024)
    return buffer.decode().strip().split('\n', 1)

async def client(threshold):
    try:
        reader, writer = await asyncio.open_unix_connection(socket_path)
    except:
        print('Error: no PyKMIP instance waiting for SSS')
        exit(1)

    if threshold is None:
        while True:
            threshold = input('How many shares are we expecting? ')
            try:
                threshold = int(threshold)
                if threshold <= 0: raise ValueError
                break
            except:
                print('Expecting a positive integer')

    messages = await get_messages(reader)
    if len(messages) == 1: # We expect number of shares to come immediately after the hello
        messages += await get_messages(reader)

    hello_msg, entered_shares_msg = messages
    
    if hello_msg != f'PYKMIP-SSS v{version}':
        print('Protocol error')
        exit(1)
        
    entered_shares = int(entered_shares_msg[7:])
    if entered_shares == 1:
        print('1 share has been entered already')
    elif entered_shares > 1:
        print(f'{entered_shares} shares have been entered already')
        
    print('Enter your shares of the secret line by line. Enter a blank line to finish.')
    line = input().strip()
    while line:
        if match := re.match(r'^(\d+),[0-9a-fA-F]{32}$', line):
            share_id = int(match.group(1))
            try:
                writer.write(line.encode())
                await writer.drain()
            except ConnectionResetError:
                print('Error: PyKMIP no longer waiting for SSS')
                exit(1)
            
            messages = await get_messages(reader)
            if len(messages) == 1: # We expect number of shares to come immediately after the input acknowledgement
                messages += await get_messages(reader)

            acknowledgement_msg, entered_shares_msg = messages
            
            entered_shares = int(entered_shares_msg[7:])
            
            if acknowledgement_msg.startswith('UPDATED'):
                print(f'Share #{share_id} updated. Currently there are {entered_shares} share(s)')
            if acknowledgement_msg.startswith('REPEATED'):
                print(f'Share #{share_id} has already been entered')
            
            if entered_shares >= threshold:
                print('Threshold reached, attempting to decrypt database...')
                writer.write('COMMIT\n'.encode())
                await writer.drain()
                
                messages = await get_messages(reader)
                if messages[0] == 'DONE':
                    print('Success!')
                    exit(0)
                else:
                    print('Failure: please enter all shares again')
                    exit(1)
        else:
            print('Invalid input')
        line = input().strip()

def main():
    parser = argparse.ArgumentParser(prog='pykmip-sss', description='Enter shares of a shared secret')
    parser.add_argument('-t', '--threshold', type=int)
    args = parser.parse_args()
    asyncio.run(client(args.threshold))