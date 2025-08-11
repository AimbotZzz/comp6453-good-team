import matplotlib
matplotlib.use('TkAgg')
matplotlib.rcParams['font.family'] = 'SimHei'
matplotlib.rcParams['axes.unicode_minus'] = False

import random
from differential_write_back import ORAMReadPath
import pandas as pd
import matplotlib.pyplot as plt

NUM_BLOCKS = 32
TREE_HEIGHT = 16  # log2(N_leaves) + 1
NUM_BUCKETS = 8

oram = ORAMReadPath(num_blocks=NUM_BLOCKS, tree_height=TREE_HEIGHT, bucket_size=NUM_BUCKETS)

print("Differential ORAM test initialization")
print(f"Blocks: {NUM_BLOCKS}, Tree Height: {TREE_HEIGHT}")

access_log = []

print("\n Initial write of all block:")
for i in range(NUM_BLOCKS):
    data = [i, i + 100]
    path = oram.get_path_to_leaf(oram.position_map.get(i, random.randint(0, 2 ** (TREE_HEIGHT - 1) - 1)))
    result = oram.access('write', i, data)
    access_log.append(("write", i, data, result.leaf_id, path))
    print(f"Write Block {i} -> {result}, path: {path}")

print("\n Read block and verify content:")
for i in range(NUM_BLOCKS):
    path = oram.get_path_to_leaf(oram.position_map[i])
    result = oram.access('read', i)
    access_log.append(("read", i, result.data, result.leaf_id, path))
    print(f"Read Block {i} -> {result}, path: {path}")

print("\n Random mixed access test:")
for _ in range(10):
    op = random.choice(['read', 'write'])
    index = random.randint(0, NUM_BLOCKS - 1)
    path = oram.get_path_to_leaf(oram.position_map[index])
    if op == 'write':
        data = [random.randint(1000, 2000), random.randint(2000, 3000)]
        result = oram.access(op, index, data)
    else:
        result = oram.access(op, index)
        data = result.data
    access_log.append((op, index, data, result.leaf_id, path))
    print(f"{op.title()} Block {index} -> {result}, 路径: {path}")

df = pd.DataFrame(access_log, columns=["op", "index", "data", "leaf", "path"])
leaf_counts = df["leaf"].value_counts().sort_index()

plt.figure(figsize=(10, 4))
plt.bar(leaf_counts.index, leaf_counts.values)
plt.title("Per-leaf access and mapping frequency")
plt.xlabel("Leaf ID")
plt.ylabel("Access Count")
plt.grid(True)
plt.tight_layout()
plt.show()
