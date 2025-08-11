# demo.py
import time, random, sys, inspect
from deterministic_oram_optimised import DeterministicPathORAM as OptORAM, Operation

# Optional baseline for a quick A/B; if missing or same as Opt, we’ll do period=1 vs 4
try:
    from deterministic_oram import DeterministicPathORAM as BaseORAM
except Exception:
    BaseORAM = None

def has_param(cls, name: str) -> bool:
    try:
        sig = inspect.signature(cls.__init__)
        return name in sig.parameters
    except Exception:
        return False

def new_oram(Cls, num_blocks, bucket_size, seed, period):
    """Instantiate ORAM, passing det_evict_period only if supported."""
    kwargs = dict(num_blocks=num_blocks, bucket_size=bucket_size, seed=seed)
    if has_param(Cls, "det_evict_period"):
        kwargs["det_evict_period"] = period
    return Cls(**kwargs)

# ---- pretty helpers ----
def hr(msg=""):
    print("\n" + "=" * 64)
    if msg:
        print(msg)
        print("-" * 64)

def sample_ciphertext_blob(oram):
    """Grab any real block from storage and return a short hex preview of its ciphertext."""
    for bucket in oram.storage.buckets:
        for blk in bucket.blocks:
            if getattr(blk, "index", -1) != -1 and getattr(blk, "encrypted_blob", None):
                blob = blk.encrypted_blob
                return (blk.index, blob[:16].hex() + ("..." if len(blob) > 16 else ""))
    return (None, None)

def tiny_bench(ORAM, label, N=256, Z=4, period=1, steps=None, seed=42):
    if steps is None:
        steps = 3 * N
    rnd = random.Random(seed)
    oram = new_oram(ORAM, N, Z, seed, period)
    # warmup: write once
    for i in range(N):
        oram.access(Operation.WRITE, i, [i, i])
    t0 = time.perf_counter()
    for s in range(steps):
        idx = rnd.randrange(N)
        if s & 1:
            oram.access(Operation.WRITE, idx, [s, s + 1])
        else:
            oram.access(Operation.READ, idx)
    dt = time.perf_counter() - t0
    print(f"{label}: {1e3*dt/steps:.3f} ms/access  (N={N}, Z={Z}, period={period if has_param(ORAM,'det_evict_period') else 'n/a'})")
    return dt / steps

# ---- 1) correctness quick check ----
hr("Deterministic Path ORAM — quick correctness")
oram = new_oram(OptORAM, num_blocks=16, bucket_size=2, seed=7, period=1)
print("WRITE block 3 -> [3, 30]")
oram.access(Operation.WRITE, 3, [3, 30])
print("READ  block 3 =>", oram.access(Operation.READ, 3))

# ---- 2) ciphertext-at-rest + on-demand decrypt demonstration ----
hr("Ciphertext at rest & on-demand decryption")
# write a few
for i in range(6):
    oram.access(Operation.WRITE, i, [i, 100 + i])

idx, blob_preview = sample_ciphertext_blob(oram)
print(f"Stored cipher preview: block={idx}, encrypted_blob[:16]={blob_preview}")
print("Now issue READ for that block to show plaintext appears only on access:")
pt = oram.access(Operation.READ, idx)
print(f"READ block {idx} => plaintext {pt}")

# ---- 3) fair runtime comparison (lower is better) ----
hr("Runtime comparison (fair, same code)")

FAIR_N, FAIR_Z = 4096, 4  # bigger N to smooth noise; adjust if your laptop struggles
STEPS = 3 * FAIR_N

# (A) Same class, only change eviction period
a = tiny_bench(OptORAM, "Optimized (period=1)", N=FAIR_N, Z=FAIR_Z, period=1, steps=STEPS)
b = tiny_bench(OptORAM, "Optimized (period=4)", N=FAIR_N, Z=FAIR_Z, period=4, steps=STEPS)
if a > 0:
    print(f"Latency reduction (p=1 -> p=4): {(a-b)/a*100:.1f}%")

# (B) Optional: disable AES to isolate structural gains
try:
    import encryption as _enc
    real_enc, real_dec = _enc.encrypt_data, _enc.decrypt_data

    def _noop_enc(words, key=_enc.AES_KEY):  # no-op encryption
        # serialize to bytes to keep sizes, but no actual AES
        return b"__NOENC__" + b"".join(int(x).to_bytes(4, "big") for x in words)

    def _noop_dec(blob, key=_enc.AES_KEY):
        if blob.startswith(b"__NOENC__"):
            pt = blob[len(b"__NOENC__"):]
            return [int.from_bytes(pt[i:i+4], "big") for i in range(0, len(pt), 4)]
        return real_dec(blob, key)

    _enc.encrypt_data, _enc.decrypt_data = _noop_enc, _noop_dec
    c = tiny_bench(OptORAM, "Optimized (period=1, AES off)", N=FAIR_N, Z=FAIR_Z, period=1, steps=STEPS)
    d = tiny_bench(OptORAM, "Optimized (period=4, AES off)", N=FAIR_N, Z=FAIR_Z, period=4, steps=STEPS)
    if c > 0:
        print(f"[AES off] Latency reduction (p=1 -> p=4): {(c-d)/c*100:.1f}%")
finally:
    # restore AES if it exists
    try:
        _enc.encrypt_data, _enc.decrypt_data = real_enc, real_dec
    except Exception:
        pass
