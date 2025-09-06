import asyncio
import re
import binascii
from logging import Logger
from Crypto.Protocol.SecretSharing import Shamir
from sqlcipher3 import dbapi2 as sqlcipher

class Sss:
    def __init__(self, db_path : str, logger : Logger):
        self.db_path = db_path
        self.logger = logger
        self.done = asyncio.Event()
        self.pw = None
        self.shares = dict()
        self.writers = set()
        print('PyKMIP SSS: please use CLI to enter shards.')
        asyncio.run(self.run())

    def __call__(self):
        return self.pw

    async def run(self):
        server = await asyncio.start_unix_server(self.connection_handler, path='/tmp/pykmip-sss.sock')
        async with server:
            await self.done.wait()
            for writer in self.writers:
                try:
                    await asyncio.wait_for(writer.drain(), timeout=0.1)
                except:
                    pass
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
        self.writers.add(writer)
        writer.write(b'PKMIP-SSS v1\n')
        well_formed_shard = re.compile(r'^\d+,[0-9a-fA-F]{32}$')
        while True:
            writer.write(f'SHARES:{len(self.shares)}\n'.encode())
            message = await reader.read(4096)
            message = message.decode('ascii').strip()
            if message.upper() == 'COMMIT':
                pw = self.combine_shares()
                works = self.validate_password(pw)
                if works:
                    for writer_ in self.writers:
                        writer_.write(b'DONE\n')
                    self.pw = pw
                    self.done.set()
                    break
                else:
                    self.shares = dict()
                    continue
            elif well_formed_shard.match(message):
                idx, share = message.split(',')
                idx = int(idx)
                share = binascii.unhexlify(share)
                old_share = self.shares.get(idx)
                if share == old_share:
                    writer.write(f'REPEATED #{idx}\n'.encode())
                else:
                    self.shares[idx] = share
                    writer.write(f'UPDATED #{idx}\n'.encode())
                    self.logger.info(f'Shard #{idx} entered.')
            elif not message:
                self.writers.remove(writer)
                break
            else:
                writer.write('INPUT ERROR\n'.encode())