from oram_readpath import ORAMReadPath

num_blocks = 16
tree_height = 8
bucket_size = 6

oram = ORAMReadPath(num_blocks=num_blocks, tree_height=tree_height, bucket_size=bucket_size)

print("Initialize ORAM test")
print(f"Num of blocks: {num_blocks}, Tree height : {tree_height}, number of leaves: {2**(tree_height - 1)}")

print("\n Write phase:")
for i in range(num_blocks):
    data = [i * 100, i * 100 + 1]
    path = oram.get_path_to_leaf(oram.position_map.get(i, oram.random_leaf.get_random_leaf()))
    result = oram.access('write', i, data)
    print(f"write Block {i}: {result}, Initial mapping path: {oram.position_map[i]}, path: {path}")

print("\n Second write:")
for i in range(num_blocks):
    data = [i * 100 + 10, i * 100 + 11]
    path = oram.get_path_to_leaf(oram.position_map[i])
    result = oram.access('write', i, data)
    print(f"Rewrite block {i}: {result}, new path: {oram.position_map[i]}, path: {path}")

print("\n Verification read phase:")
correct = 0
for i in range(num_blocks):
    path = oram.get_path_to_leaf(oram.position_map[i])
    result = oram.access('read', i)
    expected = [i * 100 + 10, i * 100 + 11]

    if result is None:
        status = f" Error: Block not found {i}（result=None）"
    elif result.data == expected:
        status = "Correct"
        correct += 1
    else:
        status = f"Error: Data mismatch，expected: {expected}，actual: {result.data}"

    print(f"read Block {i}: {result}, Mapping path: {oram.position_map[i]}, path: {path}, {status}")

print(f"\n Verification pass rate: {correct}/{num_blocks} blocks Correct")
