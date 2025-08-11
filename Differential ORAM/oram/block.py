class Block:
    BLOCK_SIZE = 2

    def __init__(self, leaf_id=-1, index=-1, data=None):
        self.leaf_id = leaf_id
        self.index = index
        self.data = data if data is not None else [0] * Block.BLOCK_SIZE

    def __repr__(self):
        return f"Block(index={self.index}, leaf={self.leaf_id}, data={self.data})"

    def copy(self):
        return Block(self.leaf_id, self.index, self.data[:])