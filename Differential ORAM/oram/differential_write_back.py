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

    def get_path_to_leaf(self, leaf_id):
        return self.server.get_path_nodes(leaf_id)


    def access(self, op, index, data=None):
        old_leaf = self.position_map[index]
        old_path_nodes = self.server.get_path_nodes(old_leaf)

        path_blocks = sum(self.server.read_path(old_leaf), [])
        self.stash.extend(path_blocks)

        for node in old_path_nodes:
            self.server.tree[node] = Bucket()

        result = None
        for blk in self.stash:
            if blk.index == index:
                if op == 'write':
                    blk.data = data
                result = blk.copy()
                break

        self.position_map[index] = self.random_leaf.get_random_leaf()
        new_leaf = self.position_map[index]
        new_path_nodes = self.server.get_path_nodes(new_leaf)

        self.stash = [blk for blk in self.stash if blk.index != index]

        if result is not None:
            self.stash.append(result)
        elif op == 'write':
            result = Block(index=index, data=data)
            self.stash.append(result)

        node_update_map = {n: [] for n in new_path_nodes}

        for blk in self.stash:
            blk_leaf = self.position_map[blk.index]
            blk_path = self.server.get_path_nodes(blk_leaf)
            for i in reversed(range(len(blk_path))):
                node = blk_path[i]
                if node in node_update_map and len(node_update_map[node]) < Bucket.max_size:
                    node_update_map[node].append(blk)
                    break

        updated_nodes = []

        for node_id, blocks in node_update_map.items():
            if blocks:
                bucket = Bucket()
                for blk in blocks:
                    bucket.add_block(blk)
                self.server.tree[node_id] = bucket

                print(f"differential write-back of nodes {node_id}，write {len(blocks)} blocks: {[blk.index for blk in blocks]}")
                updated_nodes.append(node_id)

        print(f"Number of differential write-back nodes: {len(updated_nodes)} / Total path node count: {len(new_path_nodes)}")

        written_blocks = set()
        for blocks in node_update_map.values():
            for blk in blocks:
                written_blocks.add(blk)

        self.stash = [blk for blk in self.stash if blk not in written_blocks]

        return result
