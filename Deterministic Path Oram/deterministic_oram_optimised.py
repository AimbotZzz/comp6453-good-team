import math
import random
from enum import Enum
import encryption  # AES-CTR encryption module

# ---------- enums ----------
class Operation(Enum):
    READ = 1
    WRITE = 2

# ---------- Block with encryption ----------
class Block:
    def __init__(self, leaf_id=-1, index=-1, data=None):
        self.leaf_id = leaf_id
        self.index = index
        self.data = data[:] if data is not None else None
        self.encrypted_blob = None  # bytes or None

    def is_dummy(self):
        return self.index == -1

    def copy(self):
        # Preserve plaintext (if present) and ciphertext (if present)
        b = Block(self.leaf_id, self.index,
                  None if self.data is None else self.data[:])
        if self.encrypted_blob is not None:
            b.encrypted_blob = self.encrypted_blob[:]  # keep ciphertext
        return b

    def encrypt(self):
        # no-op if already ciphertext
        if self.data is None:
            return
        import encryption
        self.encrypted_blob = encryption.encrypt_data(self.data)
        self.data = None

    def decrypt(self):
        # no-op if already plaintext
        if self.encrypted_blob is None:
            return
        import encryption
        self.data = encryption.decrypt_data(self.encrypted_blob)
        self.encrypted_blob = None

# ---------- Bucket ----------
class Bucket:
    def __init__(self, capacity):
        self.capacity = capacity
        self.blocks = [Block() for _ in range(capacity)]

    def get_blocks(self):
        return self.blocks

    def add_block(self, block: Block):
        for i, b in enumerate(self.blocks):
            if b.is_dummy():
                self.blocks[i] = block.copy()
                return True
        return False

    def remove_block(self, block: Block):
        for i, b in enumerate(self.blocks):
            if not b.is_dummy() and b.index == block.index:
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
        # index -> Block (may be plaintext if just written, or ciphertext if loaded from storage)
        self.blocks = {}

    def add(self, block: Block):
        if block.is_dummy():
            return
        # Store a copy as-is (do NOT force decrypt/encrypt here)
        self.blocks[block.index] = block.copy()

    def find(self, index: int):
        """
        Return a *decrypted copy* of the block for reading/updating.
        The object stored in the stash remains unchanged (still ciphertext/plaintext as stored).
        """
        blk = self.blocks.get(index)
        if blk is None:
            return None
        tmp = blk.copy()
        tmp.decrypt()   # on-demand decryption of the returned copy only
        return tmp

    def read_plain(self, index: int):
        blk = self.find(index)
        return None if blk is None else blk.data

    def update_plain(self, index: int, new_data):
        blk = self.blocks.get(index)
        if blk is None:
            blk = Block(index=index, data=new_data[:])
        else:
            # ensure we edit plaintext
            blk.decrypt()
            blk.data = new_data[:]
            blk.encrypted_blob = None
        self.blocks[index] = blk

    def remove(self, block: Block):
        self.blocks.pop(block.index, None)

    def size(self):
        return len(self.blocks)

    def iter_blocks(self):
        return self.blocks.values()

    def iter_items(self):
        return self.blocks.items()

# ---------- PositionMap ----------
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

# ---------- Untrusted Storage ----------
class Storage:
    def __init__(self, num_buckets, bucket_capacity):
        self.bucket_capacity = bucket_capacity
        self.buckets = [Bucket(bucket_capacity) for _ in range(num_buckets)]

    def read_bucket(self, idx):
        # return a structural copy; DO NOT decrypt here
        return self.buckets[idx].copy()

    def write_bucket(self, idx, bucket: Bucket):
        # ensure all real blocks are encrypted before persisting
        out = bucket.copy()
        for blk in out.blocks:
            if not blk.is_dummy():
                blk.encrypt()  # no-op if already ciphertext
        self.buckets[idx] = out

# ---------- Deterministic Path ORAM ----------
class DeterministicPathORAM:
    def __init__(self, num_blocks, bucket_size, seed=None, det_evict_period=1):
        """
        det_evict_period:
            - 1  : run deterministic eviction every access (current behavior)
            - K>1: run it every K accesses
            - 0/None: disable deterministic eviction
        """
        self.num_blocks = num_blocks
        self.bucket_size = bucket_size
        self.num_leaves = 1 << math.ceil(math.log2(num_blocks))
        self.num_levels = int(math.log2(self.num_leaves)) + 1
        self.num_buckets = (1 << self.num_levels) - 1

        self.storage = Storage(self.num_buckets, bucket_size)
        self.position_map = PositionMap(num_blocks, self.num_leaves, seed)
        self.stash = Stash()
        self.eviction_sequence = self._build_reverse_lex_leaves()
        self.evict_ptr = 0

        # periodic deterministic eviction
        self.det_evict_period = det_evict_period
        self._op_count = 0  # counts accesses to throttle deterministic eviction

        self._shuffle_groups = False

    def _build_reverse_lex_leaves(self):
        h = self.num_levels - 1
        leaves = list(range(self.num_leaves))
        def rev_key(leaf):
            return format(leaf, f"0{h}b")[::-1]
        return sorted(leaves, key=rev_key)

    def get_bucket_index(self, leaf, level):
        h = self.num_levels - 1
        return (1 << level) - 1 + (leaf >> (h - level))

    def _read_path_to_stash(self, leaf):
        for lvl in range(self.num_levels):
            idx = self.get_bucket_index(leaf, lvl)
            bucket = self.storage.read_bucket(idx)
            for blk in bucket.get_blocks():
                if not blk.is_dummy():
                    self.stash.add(blk)

    def _deepest_shared_level(self, leaf_a: int, leaf_b: int) -> int:
        """
        Return the deepest tree level (0..h) that lies on both paths(root->leaf_a, root->leaf_b).
        Level 0 is the root; h = self.num_levels - 1 is the leaf level.
        """
        h = self.num_levels - 1
        lvl = 0  # root is always shared
        for i in range(1, self.num_levels):  # 1..h
            bit_a = (leaf_a >> (h - i)) & 1
            bit_b = (leaf_b >> (h - i)) & 1
            if bit_a == bit_b:
                lvl = i
            else:
                break
        return lvl

    def _path_bucket_indices(self, leaf: int):
        """
        Return the list of bucket indices (level 0..h) along the path to `leaf`.
        Precomputing this avoids repeated get_bucket_index calls.
        """
        h = self.num_levels - 1
        return [(1 << lvl) - 1 + (leaf >> (h - lvl)) for lvl in range(self.num_levels)]

    def _evict_to_path(self, old_leaf: int):
        """
        Group-based greedy eviction (optimized to avoid large snapshots):
        1) Group by deepest shared level with old_leaf, but store only indices (ints), not Block objects.
        2) Bottom-up fill: each level places up to Z blocks from its own group.
        Notes:
        - We do NOT decrypt blocks here; eviction doesn't need payload plaintext.
        - Storage.write_bucket() will encrypt any plaintext blocks before persisting.
        - Avoids list(self.stash.all_blocks()) to reduce allocations and GC pressure.
        """
        path_idx = self._path_bucket_indices(old_leaf)

        # 1) Build groups: level -> list of candidate *indices* (not Blocks)
        groups = [[] for _ in range(self.num_levels)]
        for idx, blk in self.stash.iter_items():  # zero-copy view
            #
            if idx == -1:
                continue
            blk_leaf = self.position_map.get(idx)
            lvl = self._deepest_shared_level(blk_leaf, old_leaf)
            groups[lvl].append(idx)

        if self._shuffle_groups:
            for g in groups:
                random.shuffle(g)

        # 2) Bottom-up placement
        to_remove = []  # indices to delete from stash at the end
        for lvl in reversed(range(self.num_levels)):
            bidx = path_idx[lvl]
            bucket = Bucket(self.bucket_size)

            take = min(self.bucket_size, len(groups[lvl]))
            for _ in range(take):
                idx = groups[lvl].pop()  # O(1)
                blk = self.stash.blocks[idx]  # direct reference, avoid copying large collections
                bucket.add_block(blk)
                to_remove.append(idx)

            # Write bucket back (Storage ensures encryption of real blocks)
            self.storage.write_bucket(bidx, bucket)

        # 3) Remove placed blocks from stash *after* traversal to avoid mutating during iteration
        for idx in to_remove:
            self.stash.remove(Block(index=idx))

    def _perform_deterministic_eviction(self):
        leaf = self.eviction_sequence[self.evict_ptr]
        self.evict_ptr = (self.evict_ptr + 1) % len(self.eviction_sequence)
        self._read_path_to_stash(leaf)
        self._evict_to_path(leaf)

    def access(self, op: Operation, block_index: int, new_data=None):
        if block_index < 0 or block_index >= self.num_blocks:
            raise IndexError
        old_leaf = self.position_map.get(block_index)
        self._read_path_to_stash(old_leaf)

        blk = self.stash.find(block_index)
        result = None
        if op == Operation.WRITE:
            self.stash.update_plain(block_index, new_data)
        else:
            result = self.stash.read_plain(block_index)

        self.position_map.remap(block_index)
        self._evict_to_path(old_leaf)

        self._op_count += 1
        # run deterministic eviction only every det_evict_period accesses (if > 0)
        if self.det_evict_period and (self._op_count % self.det_evict_period == 0):
            self._perform_deterministic_eviction()

        return result

    def stash_size(self):
        return self.stash.size()

    def debug_state(self):
        print("Position map:", self.position_map.dump())
        print("Stash:", [b.index for b in self.stash.iter_blocks()])
