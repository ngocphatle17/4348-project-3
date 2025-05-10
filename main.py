import os
import struct

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"
HEADER_FORMAT = '>8sQQ'

class BTreeIndex:
    def __init__(self, filename):
        self.filename = filename
        self.file = None

    def open(self, mode='rb+'):
        self.file = open(self.filename, mode)

    def close(self):
        if self.file:
            self.file.close()

    def write_header(self, root_id=0, next_block_id=1):
        self.open('wb+')
        data = struct.pack(HEADER_FORMAT, MAGIC, root_id, next_block_id)
        self.file.write(data.ljust(BLOCK_SIZE, b'\x00'))
        self.close()

    def read_header(self):
        self.open()
        self.file.seek(0)
        data = self.file.read(BLOCK_SIZE)
        magic, root_id, next_block_id = struct.unpack(HEADER_FORMAT, data[:24])
        if magic != MAGIC:
            raise Exception("Invalid index file format")
        self.close()
        return root_id, next_block_id