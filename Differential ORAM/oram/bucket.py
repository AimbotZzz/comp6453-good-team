class Bucket:
    max_size = None

    @staticmethod
    def set_max_size(size):
        Bucket.max_size = size

    @staticmethod
    def reset():
        Bucket.max_size = None

    def __init__(self):
        if Bucket.max_size is None:
            raise Exception("Bucket max_size not set. Call Bucket.set_max_size() first.")
        self.blocks = []

    def add_block(self, blk):
        if len(self.blocks) < Bucket.max_size:
            self.blocks.append(blk)

    def get_blocks(self):
        return self.blocks[:]

    def remove_block(self, index):
        for i, blk in enumerate(self.blocks):
            if blk.index == index:
                return self.blocks.pop(i)
        return None