import random
import pytest
from deterministic_oram import (
    DeterministicPathORAM,
    Operation
)

# ---- fixtures ----
@pytest.fixture
def small_oram():
    return DeterministicPathORAM(num_blocks=8, bucket_size=2, seed=42)

# ---- unit / invariant tests ----
def test_unwritten_reads_none(small_oram):
    for i in range(8):
        assert small_oram.access(Operation.READ, i) is None

def test_write_then_read_consistency(small_oram):
    for i in range(8):
        data = [i, i * 10]
        small_oram.access(Operation.WRITE, i, new_data=data)
        out = small_oram.access(Operation.READ, i)
        assert out == data, f"block {i} expected {data}, got {out}"

def test_stash_no_duplicates_after_access(small_oram):
    # access same block multiple times and ensure stash invariant
    small_oram.access(Operation.WRITE, 3, new_data=[3, 30])
    small_oram.access(Operation.WRITE, 3, new_data=[303, 3030])
    stash_blocks = [b.index for b in small_oram.stash.all_blocks()]
    assert len(stash_blocks) == len(set(stash_blocks)), "Duplicates in stash"

def test_position_map_reproducible():
    o1 = DeterministicPathORAM(num_blocks=16, bucket_size=2, seed=123)
    o2 = DeterministicPathORAM(num_blocks=16, bucket_size=2, seed=123)
    # before any access they should have same position map
    assert o1.position_map.dump() == o2.position_map.dump()
    # after identical accesses, still same
    o1.access(Operation.WRITE, 5, new_data=[5,50])
    o2.access(Operation.WRITE, 5, new_data=[5,50])
    assert o1.position_map.dump() == o2.position_map.dump()

# ---- integration-style tests ----
def test_worst_case_trace_stability():
    N = 16
    oram = DeterministicPathORAM(num_blocks=N, bucket_size=4, seed=7)
    # run multiple full cycles over 0..N-1 writing
    for _ in range(5):
        for i in range(N):
            oram.access(Operation.WRITE, i, new_data=[i, i])
    # stash should not be huge
    assert oram.stash_size() < N, "Stash grew too large in worst case"

def test_random_trace_consistency():
    N = 10
    oram = DeterministicPathORAM(num_blocks=N, bucket_size=3, seed=99)
    history = {}
    for step in range(50):
        idx = random.randrange(N)
        if random.choice([True, False]):
            val = [idx + step, idx * 2 + step]
            oram.access(Operation.WRITE, idx, new_data=val)
            history[idx] = val
        else:
            out = oram.access(Operation.READ, idx)
            if idx in history:
                assert out == history[idx]
            else:
                assert out is None

