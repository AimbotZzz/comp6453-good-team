# Deterministic Path ORAM Implementation

A Python implementation of Path ORAM with deterministic eviction scheduling and multiple performance/security optimisations. 
This variant builds on the baseline Path ORAM by introducing deterministic access patterns for evaluation purposes while minimising the associated performance cost.

## Overview

This project implements a deterministic Path ORAM variant with several optimisations:

- **AES-based Block Encryption**: Ensures confidentiality of stored blocks in server storage.
- **On-demand Decryption**: Decrypts only when a specific block is accessed, reducing redundant cryptographic operations.
- **Grouped Eviction**: Pre-groups stash blocks by the deepest eligible level to reduce eviction scans.
- **Configurable Eviction Period**: Runs deterministic eviction only every _K_ accesses to cut overhead.
- **Functional Test Suite**: Validates correctness and absence of plaintext leakage.

## Features

- Deterministic Path ORAM core with position map, stash, and bucket storage.
- Optimised stash access to avoid unnecessary decryption and memory copies.
- Flexible eviction parameters to explore performance/security trade-offs.
- Full functional testing coverage to ensure correctness.

## Project Structure

```
.
├── deterministic_oram.py               # Baseline deterministic ORAM
├── deterministic_oram_optimised.py     # Optimised deterministic ORAM
├── encryption.py                        # AES encryption utilities
├── test_functional_iter.py              # Functional tests for correctness & security
├── batch_test_oram_encrypted.py         # Batch performance test runner
├── plot_bucket_vs_cycle.py              # Visualisation of eviction patterns
└── oram_experiment_batch.csv            # Recorded performance data
```

## Installation

```bash
pip install pycryptodome pytest
```

## Usage

### Basic Access
```python
from deterministic_oram_optimised import DeterministicPathORAM, Operation

oram = DeterministicPathORAM(num_blocks=16, bucket_size=2, seed=42)
oram.access(Operation.WRITE, 0, [100, 200])
print(oram.access(Operation.READ, 0))   # [100, 200]
```

## Running Functional Tests

```bash
pytest test_functional_iter.py
```

## Performance Analysis

This variant reduces time complexity in critical operations:

- **Read Path**: Skips decrypting irrelevant blocks — cost proportional to actual logical hits.
- **Eviction**: Groups candidate blocks to avoid scanning the stash for every bucket.
- **Eviction Scheduling**: Reduces eviction frequency to amortise cost over multiple accesses.

The impact of each optimisation is measured via `batch_test_oram_encrypted.py` and visualised with `plot_bucket_vs_cycle.py`.

## References

- Stefanov et al., “Path ORAM: An Extremely Simple Oblivious RAM Protocol”, CCS 2013.
- Original deterministic ORAM scheduling from Github, https://github.com/obliviousram/PathORAM.
