from block import Block
from random_leaf import RandomLeafGenerator
from server_storage import ServerStorage
from bucket import Bucket
import random

class SecureORAM:
    def __init__(self, num_blocks, tree_height, bucket_size=4, flush_interval=4):
        self.num_blocks = num_blocks
        self.tree_height = tree_height
        self.num_leaves = 2 ** (tree_height - 1)
        self.random_leaf = RandomLeafGenerator(self.num_leaves)
        self.position_map = {i: self.random_leaf.get_random_leaf() for i in range(num_blocks)}
        self.stash = []
        self.access_counter = 0
        self.flush_interval = flush_interval
        self.eviction_pointer = 0
        self.eviction_ring = list(range(self.num_leaves))
        self.diff_write_counter = 0
        self.server = ServerStorage(tree_size=2**tree_height - 1, bucket_size=bucket_size)

    def get_path_to_leaf(self, leaf_id):
        return self.server.get_path_nodes(leaf_id)

    def _prepare_bucket(self, blocks):
        while len(blocks) < Bucket.max_size:
            blocks.append(Block())
        random.shuffle(blocks)
        bucket = Bucket()
        for blk in blocks:
            bucket.add_block(blk)
        return bucket

    def access(self, op, index, data=None):
        self.access_counter += 1

        old_leaf = self.position_map[index]
        old_path_nodes = self.get_path_to_leaf(old_leaf)
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

        new_leaf = self.random_leaf.get_random_leaf()
        self.position_map[index] = new_leaf
        new_path_nodes = self.get_path_to_leaf(new_leaf)

        self.stash = [blk for blk in self.stash if blk.index != index]
        if result is not None:
            result.leaf_id = new_leaf
            self.stash.append(result)
        elif op == 'write':
            self.stash.append(Block(leaf_id=new_leaf, index=index, data=data))

        node_update_map = {n: [] for n in new_path_nodes}
        for blk in self.stash:
            if blk.index == -1:
                continue
            blk_path = self.get_path_to_leaf(self.position_map[blk.index])
            for node in reversed(blk_path):
                if node in node_update_map and len(node_update_map[node]) < Bucket.max_size:
                    node_update_map[node].append(blk)
                    break

        num_fake = len(new_path_nodes) // 2
        fake_nodes = random.sample(new_path_nodes, num_fake)
        for node in fake_nodes:
            if not node_update_map[node]:
                node_update_map[node] = []

        written_blocks = set()

        for node_id in new_path_nodes:
            if node_id in node_update_map:
                for blk in node_update_map[node_id]:
                    if blk.index != -1:
                        written_blocks.add(blk)
                bucket = self._prepare_bucket(node_update_map[node_id])
                self.server.tree[node_id] = bucket

        actual_write_count = sum(1 for blocks in node_update_map.values() if any(b.index != -1 for b in blocks))
        if actual_write_count > 0:
            self.diff_write_counter += 1
            if self.diff_write_counter % 3 == 0:
                ring_leaf = self.eviction_ring[self.eviction_pointer]
                path_nodes = self.get_path_to_leaf(ring_leaf)
                eviction_map = {n: [] for n in path_nodes}
                for blk in self.stash:
                    if blk.index == -1:
                        continue
                    blk_path = self.get_path_to_leaf(self.position_map[blk.index])
                    for node in reversed(blk_path):
                        if node in eviction_map and len(eviction_map[node]) < Bucket.max_size:
                            eviction_map[node].append(blk)
                            written_blocks.add(blk)
                            break
                for node_id in path_nodes:
                    bucket = self._prepare_bucket(eviction_map[node_id])
                    self.server.tree[node_id] = bucket
                self.eviction_pointer = (self.eviction_pointer + 1) % self.num_leaves

        self.stash = [blk for blk in self.stash if blk not in written_blocks]

        return result
