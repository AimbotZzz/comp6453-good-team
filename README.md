# comp6453-good-team

This repository contains two separate implementations of Path ORAM variants, each located in its own folder:

## 1. `Differential/`
- **Description:** Implements the standard *Differential* Path ORAM baseline with corresponding optimizations.
- **Contents:**
  - `demo.py` — quick interactive demo (correctness, ciphertext-at-rest, runtime).
  - `README.md` — detailed description of the differential implementation, optimizations, and testing.
  - Source code and test files.

## 2. `Deterministic/`
- **Description:** Implements *Deterministic* Path ORAM with multiple security and performance optimizations, including:
  - AES encryption for CPA security.
  - On-demand decryption.
  - Grouped eviction for faster block placement.
  - Adjustable deterministic eviction scheduling period.
- **Contents:**
  - `demo.py` — quick interactive demo (correctness, ciphertext-at-rest, runtime comparison with different parameters).
  - `README.md` — detailed explanation of the deterministic implementation, optimizations, and test coverage.
  - Source code and test files.
