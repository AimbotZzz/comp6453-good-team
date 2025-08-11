from block import Block
from random_leaf import RandomLeafGenerator
from server_storage import ServerStorage
from bucket import Bucket

class ORAMReadPath:
    def __init__(self, num_blocks, tree_height, bucket_size=4):
        self.num_blocks = num_blocks
        self.tree_height = tree_height
        self.num_leaves = 2 ** (tree_height - 1)

        self.random_leaf = RandomLeafGenerator(self.num_leaves)
        self.position_map = {i: self.random_leaf.get_random_leaf() for i in range(num_blocks)}
        self.stash = []
        self.server = ServerStorage(tree_size=2**tree_height - 1, bucket_size=bucket_size)

    def get_path_to_leaf(self, leaf):
        return self.server.get_path_nodes(leaf)

    def access(self, op, index, data=None):
        leaf = self.position_map[index]
        path_blocks = sum(self.server.read_path(leaf), [])

        self.stash.extend(path_blocks)
        self.server.write_path(leaf, [[] for _ in range(self.tree_height)])

        result = None
        for blk in self.stash:
            if blk.index == index:
                if op == 'write':
                    blk.data = data
                result = blk.copy()
                break

        self.position_map[index] = self.random_leaf.get_random_leaf()
        self.stash = [blk for blk in self.stash if blk.index != index]

        if result is not None:
            self.stash.append(result)
        else:
            if op == 'write':
                result = Block(index=index, data=data)
                self.stash.append(result)

        # Rebuild path
        new_path = [[] for _ in range(self.tree_height)]
        for blk in self.stash:
            blk_leaf = self.position_map[blk.index]
            path_nodes = self.server.get_path_nodes(blk_leaf)
            for i in reversed(range(self.tree_height)):
                if len(new_path[i]) < Bucket.max_size:
                    new_path[i].append(blk)
                    break
        self.server.write_path(self.position_map[index], new_path)

        return result
