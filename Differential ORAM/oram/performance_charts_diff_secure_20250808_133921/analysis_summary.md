# Differential Write-back ORAM: Three Strategy Comparison

Data file: diff_secure_performance_results_20250808_133912.json

- Config B32-H16-S8:
  - Read (ms): Full-path=0.546, Differential=0.013, Secure-Diff=0.313
  - Write (ms): Full-path=0.029, Differential=0.016, Secure-Diff=0.107
  - Mixed (ms): Full-path=1.001, Differential=0.013, Secure-Diff=0.650
  - Stash: Full-path=580, Differential=0, Secure-Diff=12739
  - Read speedup (x): Diff=41.49x, Secure-Diff=1.74x

- Config B64-H16-S8:
  - Read (ms): Full-path=2.002, Differential=0.013, Secure-Diff=0.550
  - Write (ms): Full-path=0.045, Differential=0.012, Secure-Diff=0.131
  - Mixed (ms): Full-path=1.433, Differential=0.013, Secure-Diff=1.138
  - Stash: Full-path=1161, Differential=0, Secure-Diff=23651
  - Read speedup (x): Diff=154.20x, Secure-Diff=3.64x

- Config B128-H17-S8:
  - Read (ms): Full-path=5.347, Differential=0.015, Secure-Diff=0.888
  - Write (ms): Full-path=0.451, Differential=0.014, Secure-Diff=0.291
  - Mixed (ms): Full-path=4.853, Differential=0.014, Secure-Diff=1.902
  - Stash: Full-path=6972, Differential=0, Secure-Diff=40592
  - Read speedup (x): Diff=365.99x, Secure-Diff=6.02x

