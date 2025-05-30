import os
import struct
import sys

BLOCK_SIZE = 512
MAGIC = b"4348PRJ3"
HEADER_FORMAT = '>8sQQ'
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
        keys = struct.pack('>' + 'Q' * MAX_KEYS, *self.keys)
        values = struct.pack('>' + 'Q' * MAX_KEYS, *self.values)
        children = struct.pack('>' + 'Q' * MAX_CHILDREN, *self.children)

        return (header + keys + values + children).ljust(BLOCK_SIZE, b'\x00')

    @staticmethod
    def deserialize(data):
        block_id, parent_id, num_keys = struct.unpack(NODE_HEADER_FORMAT, data[:24])
        keys = list(struct.unpack('>' + 'Q' * MAX_KEYS, data[24:24 + MAX_KEYS * 8]))
        values = list(struct.unpack('>' + 'Q' * MAX_KEYS, data[24 + MAX_KEYS * 8:24 + 2 * MAX_KEYS * 8]))
        children = list(struct.unpack('>' + 'Q' * MAX_CHILDREN, data[24 + 2 * MAX_KEYS * 8:24 + 2 * MAX_KEYS * 8 + MAX_CHILDREN * 8]))
        return BTreeNode(block_id, parent_id, num_keys, keys, values, children)


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
            keys = [0] * MAX_KEYS
            values = [0] * MAX_KEYS
            keys[0] = key
            values[0] = value
            root = BTreeNode(next_block_id, 0, 1, keys, values, [0] * MAX_CHILDREN)
            self.write_node(root)
            self.open()
            self.file.seek(8)
            self.file.write(struct.pack('>Q', root.block_id))
            self.file.write(struct.pack('>Q', next_block_id + 1))
            self.close()
            print(f"Inserted root key {key}, value {value} into block {root.block_id}")
            return

        node = self.read_node(root_id)
        if key in node.keys[:node.num_keys]:
            print(f"Key {key} already exists")
            return
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

    def search(self, key):
        root_id, _ = self.read_header()
        node = self.read_node(root_id)
        for i in range(node.num_keys):
            if node.keys[i] == key:
                print(f"Found: key={key}, value={node.values[i]}")
                return
        print(f"Error: key {key} not found")

    def print_all(self):
        self.open()
        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        self.file.seek(BLOCK_SIZE)
        while self.file.tell() < size:
            data = self.file.read(BLOCK_SIZE)
            node = BTreeNode.deserialize(data)
            for i in range(node.num_keys):
                print(f"{node.keys[i]}: {node.values[i]}")
        self.close()

    def extract(self, output_csv):
        if os.path.exists(output_csv):
            print("Error: output file already exists")
            return
        self.open()
        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        self.file.seek(BLOCK_SIZE)
        with open(output_csv, 'w') as out:
            while self.file.tell() < size:
                data = self.file.read(BLOCK_SIZE)
                node = BTreeNode.deserialize(data)
                for i in range(node.num_keys):
                    out.write(f"{node.keys[i]},{node.values[i]}\n")
        self.close()
        print(f"Extracted index data to {output_csv}")

    def load_from_csv(self, csv_file):
        if not os.path.exists(csv_file):
            print("Error: CSV file does not exist")
            return
        try:
            with open(csv_file, 'r') as f:
                for line in f:
                    if ',' not in line:
                        continue
                    key_str, val_str = line.strip().split(',')
                    key, value = int(key_str), int(val_str)
                    self.insert(key, value)
            print(f"Loaded data from {csv_file}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

def main():
    args = sys.argv
    if len(args) < 3:
        print("Usage:\n  create <file>\n  insert <file> <key> <value>\n  search <file> <key>\n  print <file>\n  extract <file> <csv>\n  load <file> <csv>")
        return

    command, filename = args[1], args[2]
    btree = BTreeIndex(filename)

    if command == "create":
        btree.create()
    elif command == "insert" and len(args) == 5:
        key, val = int(args[3]), int(args[4])
        btree.insert(key, val)
    elif command == "search" and len(args) == 4:
        key = int(args[3])
        btree.search(key)
    elif command == "print":
        btree.print_all()
    elif command == "extract" and len(args) == 4:
        output_csv = args[3]
        btree.extract(output_csv)
    elif command == "load" and len(args) == 4:
        csv_file = args[3]
        try:
            btree.read_header()
        except:
            print("Error: file is not a valid index file")
            return
        btree.load_from_csv(csv_file)
    else:
        print("Invalid command or arguments")

if __name__ == '__main__':
    main()