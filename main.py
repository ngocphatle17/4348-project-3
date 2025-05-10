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
NODE_HEADER_FORMAT = '>QQQ'
MAX_KEYS = 19
MAX_CHILDREN = 20
KEY_VAL_FORMAT = '>Q'

class BTreeNode:
    def __init__(self, block_id, parent_id, num_keys=0, keys=None, values=None, children=None):
        self.block_id = block_id
        self.parent_id = parent_id
        self.num_keys = num_keys
        self.keys = keys or [0] * MAX_KEYS
        self.values = values or [0] * MAX_KEYS
        self.children = children or [0] * MAX_CHILDREN

    def serialize(self):
        header = struct.pack(NODE_HEADER_FORMAT, self.block_id, self.parent_id, self.num_keys)
        keys = struct.pack(KEY_VAL_FORMAT * MAX_KEYS, *self.keys)
        values = struct.pack(KEY_VAL_FORMAT * MAX_KEYS, *self.values)
        children = struct.pack(KEY_VAL_FORMAT * MAX_CHILDREN, *self.children)
        return (header + keys + values + children).ljust(BLOCK_SIZE, b'\x00')

    @staticmethod
    def deserialize(data):
        block_id, parent_id, num_keys = struct.unpack(NODE_HEADER_FORMAT, data[:24])
        keys = list(struct.unpack(KEY_VAL_FORMAT * MAX_KEYS, data[24:24 + MAX_KEYS * 8]))
        values = list(struct.unpack(KEY_VAL_FORMAT * MAX_KEYS, data[24 + MAX_KEYS * 8:24 + 2 * MAX_KEYS * 8]))
        children = list(struct.unpack(KEY_VAL_FORMAT * MAX_CHILDREN, data[24 + 2 * MAX_KEYS * 8:24 + 2 * MAX_KEYS * 8 + MAX_CHILDREN * 8]))
        return BTreeNode(block_id, parent_id, num_keys, keys, values, children)
    def write_node(self, node):
        self.open()
        self.file.seek(node.block_id * BLOCK_SIZE)
        self.file.write(node.serialize())
        self.close()

    def read_node(self, block_id):
        self.open()
        self.file.seek(block_id * BLOCK_SIZE)
        data = self.file.read(BLOCK_SIZE)
        self.close()
        return BTreeNode.deserialize(data)
    def create(self):
        if os.path.exists(self.filename):
            print("Error: file already exists")
            return
        self.write_header()
        print(f"Created index file {self.filename}")
    def insert(self, key, value):
        root_id, next_block_id = self.read_header()
        if root_id == 0:
            root = BTreeNode(next_block_id, 0, 1, [key] + [0] * (MAX_KEYS - 1), [value] + [0] * (MAX_KEYS - 1), [0] * MAX_CHILDREN)
            self.write_node(root)
            self.open()
            self.file.seek(8)
            self.file.write(struct.pack('>Q', root.block_id))
            self.file.write(struct.pack('>Q', next_block_id + 1))
            self.close()
            print(f"Inserted root key {key}, value {value} into block {root.block_id}")
            return
        node = self.read_node(root_id)
        if node.num_keys < MAX_KEYS:
            idx = 0
            while idx < node.num_keys and node.keys[idx] < key:
                idx += 1
            for j in range(node.num_keys, idx, -1):
                node.keys[j] = node.keys[j - 1]
                node.values[j] = node.values[j - 1]
            node.keys[idx] = key
            node.values[idx] = value
            node.num_keys += 1
            self.write_node(node)
            print(f"Inserted key {key}, value {value} into root node")
        else:
            print("Insertion failed: Node full. Splitting not implemented in this simplified version.")