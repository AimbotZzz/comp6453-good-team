 Differential ORAM Implementation

A Python implementation of Oblivious RAM (ORAM) with differential write-back optimisation and secure variants. This project provides three ORAM implementations with performance analysis and visualisation tools.

 Overview

This project implements Path ORAM with two novel optimisations:
- Differential Write-back: Reduces write operations by only updating modified buckets
- Secure Differential ORAM: Adds dummy blocks and ring eviction for enhanced security

 Features

- Three ORAM Variants:
  1. Standard Path ORAM with full-path write-back
  2. Differential write-back ORAM (improved performance)
  3. Secure differential ORAM (with dummy blocks and ring eviction)

- Performance Analysis: Comprehensive benchmarking tools comparing all implementations
- Visualisation: Tree structure and stash visualisation for debugging and analysis
- Configurable Parameters: Tree height, bucket size, block count, and security parameters

 Project Structure

```
oram/
├── Core Components
│   ├── block.py                  Block data structure
│   ├── bucket.py                 Bucket container for blocks
│   ├── server_storage.py         Server-side tree storage
│   └── random_leaf.py            Leaf assignment generator
│
├── ORAM Implementations
│   ├── oram_readpath.py          Standard Path ORAM
│   ├── differential_write_back.py  Differential write-back ORAM
│   └── secure_oram.py            Secure differential ORAM
│
├── Testing & Analysis
│   ├── test_oram.py              Basic functionality tests
│   ├── test_Differential_oram.py  Differential ORAM tests
│   ├── secure_oram_test.py       Secure ORAM tests
│   ├── secure_diff_performance.py  Performance benchmarking
│   └── visualize_diff_secure_performance.py  Performance visualisation
│
├── Visualisation
│   ├── demo_show.py              Interactive tree visualisation
│   └── output/                   Generated visualisation images
│
└── Reports & Results
    ├── differential_oram_report.md
    ├── complexity_analysis_report.md
    └── performance_charts_/      Performance analysis charts
```

 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd oram
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
 On Windows
venv\Scripts\activate
 On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install matplotlib networkx numpy pandas
```

 Usage

 Basic ORAM Operations

```python
from oram_readpath import ORAMReadPath

 Initialise ORAM
oram = ORAMReadPath(
    num_blocks=16,     Number of data blocks
    tree_height=5,     Height of binary tree
    bucket_size=4      Blocks per bucket
)

 Write data
oram.access('write', index=0, data=[100, 200])

 Read data
result = oram.access('read', index=0)
print(result.data)   [100, 200]
```

 Differential Write-back ORAM

```python
from differential_write_back import ORAMReadPath as DifferentialORAM

 Same interface as standard ORAM
oram = DifferentialORAM(num_blocks=16, tree_height=5, bucket_size=4)
```

 Secure Differential ORAM

```python
from secure_oram import SecureORAM

 Additional security parameters
oram = SecureORAM(
    num_blocks=16,
    tree_height=5,
    bucket_size=4,
    flush_interval=4   Ring eviction frequency
)
```

 Running Tests

 Unit Tests
```bash
 Test standard ORAM
python test_oram.py

 Test differential ORAM
python test_Differential_oram.py

 Test secure ORAM
python secure_oram_test.py
```

 Performance Benchmarking
```bash
 Run comprehensive performance tests
python secure_diff_performance.py

 Generate performance visualisations
python visualize_diff_secure_performance.py
```

 Interactive Visualisation
```bash
 Visualise ORAM tree structure and operations
python demo_show.py
```

 Performance Analysis

The project includes comprehensive performance analysis tools that measure:
- Read/write operation times
- Stash size evolution
- Speedup compared to standard Path ORAM
- Impact of tree height and bucket size

Performance results are saved as:
- JSON data files: `diff_secure_performance_results_.json`
- Text reports: `diff_secure_performance_report_.txt`
- Visualisation charts in `performance_charts_/`

 Key Algorithms

 Differential Write-back
- Only writes back buckets that have been modified
- Significantly reduces write operations for large trees
- Maintains same security guarantees as standard Path ORAM

 Secure Enhancements
- Dummy Blocks: Padding with fake blocks to hide access patterns
- Ring Eviction: Periodic background eviction to manage stash size
- Randomised Write Patterns: Enhanced obliviousness through probabilistic writes

 Configuration Parameters

- `num_blocks`: Total number of data blocks to store
- `tree_height`: Height of the binary tree (determines capacity)
- `bucket_size`: Maximum blocks per bucket
- `flush_interval`: Frequency of ring eviction (secure variant only)

 Visualisation Output

The `demo_show.py` script generates visualisations showing:
- Tree structure with bucket contents
- Stash contents
- Access paths (highlighted in green)
- Bucket utilisation statistics

Example output saved to `output/oram_round_.png`

 Development

 Adding New ORAM Variants

1. Inherit from base ORAM structure
2. Override `access()` method with custom logic
3. Maintain position map and stash consistency
4. Add corresponding test file

 Extending Performance Analysis

Modify `secure_diff_performance.py` to:
- Add new test configurations
- Include additional metrics
- Compare more variants

 Known Limitations

- Memory usage scales with tree size
- Visualisation limited to reasonable tree sizes
- Performance tests use synthetic workloads

 References

- Path ORAM: Stefanov et al., "Path ORAM: An Extremely Simple Oblivious RAM Protocol"
- Differential techniques inspired by write-optimised storage systems
- Security enhancements based on recent ORAM research
