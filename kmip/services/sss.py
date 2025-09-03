import socket
import re
import binascii
from Crypto.Protocol.SecretSharing import Shamir
from sqlcipher3 import dbapi2 as sqlcipher

class Sss_listener:
    def __init__(self, db_path, logger=None):
        self.db_path = db_path
        self.logger = logger
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('localhost', 5066))
        self.server.listen(5)
    
    def combine_shares(self, shares):
        pwb = Shamir.combine(shares)
        pw = binascii.hexlify(pwb).decode('ascii')
        self.logger.info("Shards completed.")
        return pw

    def validate_password(self, pw: str):
        db = sqlcipher.connect(self.db_path) # assuming it has been set
        db.execute(f"pragma key='{pw}';")
        try:
            db.execute('select * from sqlite_master;').fetchall()
            db.close()
        except sqlcipher.Error as er:
            return False
        return True
    
    def listen(self):
        wfs = re.compile(r'^\d+,([0-9a-fA-F]+)$') # well-formed shard
        shares = []
        i = 0
        connections = []
        while True:
            try:
                connection, address = self.server.accept()
                connection.setblocking(False)
                connections.append(connection)
            except BlockingIOError:
                pass
    
            for connection in connections:
                try:
                    message = connection.recv(4096).strip()
                    if message == b'commit': 
                        pw = self.combine_shares(shares)
                        works = self.validate_password(pw)
                        if works:
                            self.server.shutdown(2)
                            return pw
                        else:
                            i = 0
                            shares = []
                            connection.send(f"Database access failed due to incorrect shards. Please try again. \n".encode())
                    else:
                        try:
                            if wfs.match(message.decode('ascii')):
                                print(f'Got shard#{i}.')
                                sh = message.decode('ascii').split(',')
                                try:
                                    shares.append((int(sh[0]), binascii.unhexlify(sh[1])))
                                    i=i+1
                                    self.logger.info(
                                        "Shard #{0} entered.".format(sh[0])
                                    )
                                except Exception as e:
                                    connection.send(f"not a shard of known command or error {e}!\n".encode())
                                    pass
                            else:
                                connection.send(f"Not a shard or a known command!\n".encode())
                        except Exception as e:
                            pass
      
                except BlockingIOError:
                    continue