from bucket import Bucket

class ServerStorage:
    def __init__(self, tree_size, bucket_size=4):
        Bucket.set_max_size(bucket_size)
        self.tree = [Bucket() for _ in range(tree_size)]

    def read_path(self, leaf):
        path = self.get_path_nodes(leaf)
        return [self.tree[node].get_blocks() for node in path]

    def write_path(self, leaf, path_blocks):
        nodes = self.get_path_nodes(leaf)
        for i, blocks in zip(nodes, path_blocks):
            self.tree[i] = Bucket()
            for blk in blocks:
                self.tree[i].add_block(blk)

    def get_path_nodes(self, leaf):
        # return list of indices from root to leaf
        path = []
        while leaf >= 0:
            path.append(leaf)
            leaf = (leaf - 1) // 2 if leaf != 0 else -1
        return list(reversed(path))