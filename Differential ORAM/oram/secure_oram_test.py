from secure_oram import SecureORAM
import random

def test_secure_oram_multiple_rounds():
    print("Initialize Secure ORAM")
    num_blocks = 10
    tree_height = 16
    bucket_size = 8
    total_rounds = 20

    oram = SecureORAM(num_blocks=num_blocks, tree_height=tree_height, bucket_size=bucket_size)
    latest_written_data = {}

    print("\n Initial write:")
    for i in range(num_blocks):
        data = [i * 10, i * 10 + 1]
        oram.access('write', i, data)
        latest_written_data[i] = data

    print("\n Multi-round mixed access test:")
    for r in range(total_rounds):
        print(f"\n--- Round {r + 1} ---")
        for _ in range(num_blocks):
            index = random.randint(0, num_blocks - 1)
            op = random.choice(['read', 'write'])

            if op == 'write':
                data = [random.randint(1000, 9999), random.randint(1000, 9999)]
                result = oram.access('write', index, data)
                latest_written_data[index] = data
                print(f" write Block {index}: {result}")

                leaf = oram.position_map[index]
                path_nodes = oram.get_path_to_leaf(leaf)
                print(f" Write path: {path_nodes}")
                for node_id in path_nodes:
                    bucket = oram.server.tree[node_id]
                    blk_ids = [blk.index if blk.index != -1 else "dummy" for blk in bucket.get_blocks()]
                    print(f" Node {node_id}: {blk_ids}")

                if oram.access_counter % oram.flush_interval == 0:
                    ring_leaf = oram.eviction_ring[(oram.eviction_pointer - 1) % oram.num_leaves]
                    ring_path = oram.get_path_to_leaf(ring_leaf)
                    print(f"Ring eviction path: {ring_path}")
                    for node_id in ring_path:
                        bucket = oram.server.tree[node_id]
                        blk_ids = [blk.index if blk.index != -1 else "dummy" for blk in bucket.get_blocks()]
                        print(f" Node {node_id}: {blk_ids}")

            else:
                result = oram.access('read', index)
                print(f" read Block {index}: {result.data if result else None}")
                expected = latest_written_data.get(index)
                if expected and result.data != expected:
                    print(f"Data mismatch: Block {index} expected {expected}, actual {result.data}")

    print("\n Final verification:")
    for i in range(num_blocks):
        result = oram.access('read', i)
        expected = latest_written_data[i]
        print(f" Block {i} Current data: {result.data}")
        if result.data != expected:
            print(f" Data mismatch: Block {i} expected {expected}, actual {result.data}")
        else:
            print(f" Block {i} Data consistency")

if __name__ == "__main__":
    test_secure_oram_multiple_rounds()
