import math
import random
from enum import Enum


# ---------- enums ----------
class Operation(Enum):
    READ = 1
    WRITE = 2


# ---------- Block ----------
class Block:
    def __init__(self, leaf_id=-1, index=-1, data=None):
        self.leaf_id = leaf_id
        self.index = index
        self.data = data[:] if data is not None else None  # can be arbitrary payload

    def is_dummy(self):
        return self.index == -1

    def copy(self):
        return Block(self.leaf_id, self.index, None if self.data is None else self.data[:])


# ---------- Bucket ----------
class Bucket:
    def __init__(self, capacity):
        self.capacity = capacity
        # initialize with dummy blocks
        self.blocks = [Block() for _ in range(capacity)]

    def get_blocks(self):
        return self.blocks

    def add_block(self, block: Block):
        for i, b in enumerate(self.blocks):
            if b.is_dummy():
                self.blocks[i] = block.copy()
                return True
        return False  # full

    def remove_block(self, block: Block):
        for i, b in enumerate(self.blocks):
            if (not b.is_dummy()) and b.index == block.index:
                self.blocks[i] = Block()
                return True
        return False

    def copy(self):
        newb = Bucket(self.capacity)
        newb.blocks = [blk.copy() for blk in self.blocks]
        return newb


# ---------- Stash ----------
class Stash:
    def __init__(self):
        self.blocks = {}  # map from index to Block

    def add(self, block: Block):
        if block.is_dummy():
            return
        self.blocks[block.index] = block.copy()  # replace existing if any

    def find(self, index):
        return self.blocks.get(index, None)

    def remove(self, block: Block):
        self.blocks.pop(block.index, None)

    def size(self):
        return len(self.blocks)

    def all_blocks(self):
        return list(self.blocks.values())

    def __str__(self):
        return f"Stash(size={self.size()}, blocks={[b.index for b in self.all_blocks()]})"



# ---------- Position Map ----------
class PositionMap:
    def __init__(self, num_blocks, num_leaves, seed=None):
        self.num_leaves = num_leaves
        self.rng = random.Random(seed)
        self.map = [self.rng.randrange(num_leaves) for _ in range(num_blocks)]

    def get(self, block_index):
        return self.map[block_index]

    def remap(self, block_index):
        new_leaf = self.rng.randrange(self.num_leaves)
        self.map[block_index] = new_leaf
        return new_leaf

    def dump(self):
        return list(self.map)


# ---------- Untrusted Storage (tree of buckets in flat array) ----------
class Storage:
    def __init__(self, num_buckets, bucket_capacity):
        self.buckets = [Bucket(bucket_capacity) for _ in range(num_buckets)]
        self.bucket_capacity = bucket_capacity

    def read_bucket(self, idx):
        # return a copy to simulate fetch
        return self.buckets[idx].copy()

    def write_bucket(self, idx, bucket: Bucket):
        self.buckets[idx] = bucket.copy()


# ---------- Deterministic Path ORAM with deterministic eviction schedule ----------
class DeterministicPathORAM:
    def __init__(self, num_blocks, bucket_size, seed=None):
        self.num_blocks = num_blocks
        self.bucket_size = bucket_size
        self.seed = seed
        # compute number of leaves = next power of two >= num_blocks
        self.num_leaves = 1 << math.ceil(math.log2(num_blocks))
        self.num_levels = int(math.log2(self.num_leaves)) + 1  # total levels including root level 0
        self.num_buckets = (1 << self.num_levels) - 1  # full binary tree

        self.storage = Storage(self.num_buckets, bucket_size)
        self.position_map = PositionMap(num_blocks, self.num_leaves, seed)
        self.stash = Stash()
        self.eviction_sequence = self._build_reverse_lex_leaves()
        self.evict_ptr = 0  # pointer into eviction sequence

        # initialize all buckets to dummy (already done in constructors)

    def _build_reverse_lex_leaves(self):
        # leaves are numbers 0..num_leaves-1, represent as bitstrings of length h
        h = self.num_levels - 1
        leaves = list(range(self.num_leaves))

        # key is reversed bitstring; for reverse lexicographic over paths
        def rev_key(leaf):
            b = format(leaf, f"0{h}b")
            return b[::-1]  # reverse string

        sorted_leaves = sorted(leaves, key=rev_key)
        return sorted_leaves

    def get_bucket_index(self, leaf, level):
        # level 0 is root. bucket indices: (1 << level) -1 + (leaf >> (h - level))
        h = self.num_levels - 1
        return (1 << level) - 1 + (leaf >> (h - level))

    def _read_path_to_stash(self, leaf):
        for level in range(self.num_levels):
            idx = self.get_bucket_index(leaf, level)
            bucket = self.storage.read_bucket(idx)
            for blk in bucket.get_blocks():
                if not blk.is_dummy():
                    self.stash.add(blk)

    def _evict_to_path(self, leaf):
        # greedy: for levels from bottom up, try to place stash blocks that belong to this path
        old_stash_blocks = list(self.stash.all_blocks())
        # we will build new buckets for this path
        for level in reversed(range(self.num_levels)):
            bucket_idx = self.get_bucket_index(leaf, level)
            new_bucket = Bucket(self.bucket_size)
            placed = []
            count = 0
            for blk in old_stash_blocks:
                if count >= self.bucket_size:
                    break
                # check if block's current position_map leaf path includes this bucket at this level
                assigned_leaf = self.position_map.get(blk.index)
                if self.get_bucket_index(assigned_leaf, level) == bucket_idx:
                    # place it
                    new_bucket.add_block(blk)
                    placed.append(blk)
                    count += 1
            # fill remaining with dummy (already dummy-inited)
            # remove placed from stash
            for p in placed:
                self.stash.remove(p)
            # write bucket back
            self.storage.write_bucket(bucket_idx, new_bucket)

    def _perform_deterministic_eviction(self):
        # pick next leaf in eviction sequence and evict to that path
        leaf = self.eviction_sequence[self.evict_ptr]
        self.evict_ptr = (self.evict_ptr + 1) % len(self.eviction_sequence)
        # read that path into stash and then evict greedily to it
        self._read_path_to_stash(leaf)
        self._evict_to_path(leaf)

    def access(self, op: Operation, block_index: int, new_data=None):
        if block_index < 0 or block_index >= self.num_blocks:
            raise IndexError("block_index out of range")
        # 1. Get old leaf and read its path
        old_leaf = self.position_map.get(block_index)
        self._read_path_to_stash(old_leaf)

        # 2. Access (read or write)
        result = None
        target = self.stash.find(block_index)
        if op == Operation.WRITE:
            if target is None:
                blk = Block(self.position_map.get(block_index), block_index, new_data)
                self.stash.add(blk)
            else:
                # update in stash
                target.data = new_data[:]
        else:  # READ
            if target is not None:
                result = target.data[:]
            else:
                result = None  # not present yet

        # 3. Remap the block's leaf (even if read)
        self.position_map.remap(block_index)

        # 4. Evict to the accessed path (standard write-back)
        self._evict_to_path(old_leaf)

        # 5. Deterministic eviction on scheduled path
        self._perform_deterministic_eviction()

        return result

    def stash_size(self):
        return self.stash.size()

    def debug_state(self):
        print("Position map sample:", self.position_map.dump()[:min(8, len(self.position_map.map))])
        print(self.stash)


# ---------- simple test / demo ----------
def simple_sanity_check():
    print("==== Deterministic Path ORAM Sanity Check ====")
    N = 8  # number of logical blocks
    Z = 2  # bucket capacity
    oram = DeterministicPathORAM(num_blocks=N, bucket_size=Z, seed=123)

    # ---- new: sanity check for unwritten block ----
    print("\n[Sanity] Read unwritten block 0 (should be None):")
    val0 = oram.access(Operation.READ, 0)
    print("Read block 0 =>", val0)
    assert val0 is None, f"Expected None for unwritten block 0, got {val0}"
    print("✅ Unwritten block returns None as expected.")

    # write sequentially, then read back
    for i in range(N):
        print(f"\nAccess WRITE block {i} with data={[i, i*10]}")
        oram.access(Operation.WRITE, i, new_data=[i, i * 10])
        print("Stash after write:", oram.stash_size())
        # immediate read
        val = oram.access(Operation.READ, i)
        print(f"Read back block {i} =>", val)
        assert val == [i, i * 10], f"Mismatch for block {i}"
        print("Stash size:", oram.stash_size())

    # random accesses
    print("\nRandom access pattern (reads/writes):")
    for i in range(5):
        idx = random.randrange(N)
        if random.choice([True, False]):
            print(f"WRITE block {idx} new_data={[idx + 100, idx + 200]}")
            oram.access(Operation.WRITE, idx, new_data=[idx + 100, idx + 200])
        else:
            v = oram.access(Operation.READ, idx)
            print(f"READ block {idx} =>", v)
        print("Stash:", oram.stash_size())

    print("\nFinal ORAM stash and position map:")
    oram.debug_state()



if __name__ == "__main__":
    simple_sanity_check()
