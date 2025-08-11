# tests/test_functional_iter.py
import importlib
import random
import pytest

# -------- resolve API from oram.py --------
@pytest.fixture(scope="module")
def api():
    """
    Resolve the ORAM class and Operation enum from the tested module.
    """
    m = importlib.import_module("deterministic_oram_optimised")
    ORAM = (
        getattr(m, "DeterministicPathORAM", None)
        or getattr(m, "PathORAM", None)
        or getattr(m, "ORAM", None)
    )
    Op = getattr(m, "Operation", None)
    assert ORAM is not None, "Cannot find ORAM class (DeterministicPathORAM/PathORAM/ORAM)."
    assert Op is not None, "Cannot find Operation enum in module."
    return m, ORAM, Op


# ------------------ 0) baseline correctness ------------------
def test_unwritten_reads_none(api):
    m, ORAM, Op = api
    oram = ORAM(num_blocks=8, bucket_size=2, seed=123)
    assert oram.access(Op.READ, 0) is None
    assert oram.access(Op.READ, 7) is None


def test_write_then_read_consistency(api):
    m, ORAM, Op = api
    oram = ORAM(num_blocks=16, bucket_size=2, seed=7)
    for i in range(10):
        data = [i, i * 10]
        oram.access(Op.WRITE, i, data)
        out = oram.access(Op.READ, i)
        assert out == data


def test_random_trace_consistency(api):
    m, ORAM, Op = api
    N = 32
    oram = ORAM(num_blocks=N, bucket_size=3, seed=99)
    last = {}
    rnd = random.Random(123)
    for _ in range(5 * N):
        idx = rnd.randrange(N)
        if rnd.choice([True, False]):
            val = [idx + 1000, idx + 2000]
            oram.access(Op.WRITE, idx, val)
            last[idx] = val
        else:
            out = oram.access(Op.READ, idx)
            if idx in last:
                assert out == last[idx]
            else:
                assert out is None


# -------- 1) path legality under iterator-based grouped eviction --------
def test_eviction_legality_on_path(api):
    """
    After reading a path into stash and running eviction to that same path,
    every real block written on that path must be placed on a bucket that lies
    on its *current* leaf's path at that level.
    """
    m, ORAM, Op = api
    N, Z = 32, 4
    oram = ORAM(num_blocks=N, bucket_size=Z, seed=11)

    # Warm-up so paths actually contain real blocks
    for i in range(20):
        oram.access(Op.WRITE, i, [i, 100 + i])

    # Choose an old_leaf (use a block's current leaf)
    target = 7
    old_leaf = oram.position_map.get(target)

    # Bring the old path into stash, then evict to the same path
    # (Method names follow previous version; if you hid them, expose tiny test hooks.)
    oram._read_path_to_stash(old_leaf)
    oram._evict_to_path(old_leaf)

    # Verify legality: at each level, bucket index must match block's current path
    for lvl in range(oram.num_levels):
        bidx = oram.get_bucket_index(old_leaf, lvl)
        bucket = oram.storage.buckets[bidx]  # read as stored
        for blk in bucket.blocks:
            if getattr(blk, "index", -1) == -1:
                continue
            blk_leaf = oram.position_map.get(blk.index)
            expected = oram.get_bucket_index(blk_leaf, lvl)
            assert bidx == expected, (
                f"Illegal placement: block {blk.index} placed at bucket {bidx} "
                f"(level {lvl}), but its path index is {expected}"
            )


# -------- 2) deterministic-eviction period (frequency control) --------
def test_det_evict_period_controls_frequency(api, monkeypatch):
    """
    Check that scheduled deterministic eviction triggers at the configured frequency.
    We wrap the method to count calls.
    """
    m, ORAM, Op = api
    N, Z, steps = 16, 2, 4 * 16

    o1 = ORAM(num_blocks=N, bucket_size=Z, seed=1, det_evict_period=1)
    o2 = ORAM(num_blocks=N, bucket_size=Z, seed=1, det_evict_period=4)

    calls1 = {"n": 0}
    calls2 = {"n": 0}

    real1 = o1._perform_deterministic_eviction
    real2 = o2._perform_deterministic_eviction

    def wrap1():
        calls1["n"] += 1
        return real1()

    def wrap2():
        calls2["n"] += 1
        return real2()

    monkeypatch.setattr(o1, "_perform_deterministic_eviction", wrap1, raising=True)
    monkeypatch.setattr(o2, "_perform_deterministic_eviction", wrap2, raising=True)

    # Warm-up
    for i in range(N):
        o1.access(Op.WRITE, i, [i, i])
        o2.access(Op.WRITE, i, [i, i])

    calls1["n"] = 0
    calls2["n"] = 0

    for s in range(steps):
        idx = s % N
        if s % 2 == 0:
            o1.access(Op.READ, idx)
            o2.access(Op.READ, idx)
        else:
            o1.access(Op.WRITE, idx, [s, s + 1])
            o2.access(Op.WRITE, idx, [s, s + 1])

    assert calls1["n"] == steps, f"period=1 should fire every access, got {calls1['n']}"
    assert calls2["n"] == steps // 4, f"period=4 should fire once per 4 accesses, got {calls2['n']}"


# -------- 3) position-map remap sanity (should actually change leaves) --------
def test_position_map_remap_changes_leaf(api):
    m, ORAM, Op = api
    N = 32
    oram = ORAM(num_blocks=N, bucket_size=3, seed=0)
    idx = 5
    initial = oram.position_map.get(idx)
    changed = False
    # Issue multiple accesses to induce remaps
    for t in range(20):
        if t % 2 == 0:
            oram.access(Op.READ, idx)
        else:
            oram.access(Op.WRITE, idx, [t, t])
        if oram.position_map.get(idx) != initial:
            changed = True
            break
    assert changed, "Position map leaf for the block should change after some accesses."


