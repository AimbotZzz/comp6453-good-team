import time
import random
import csv
from deterministic_oram_optimised import DeterministicPathORAM, Operation

# 2 ** 16, 2 ** 18, 2 ** 20
Z_list = [2, 3, 4, 5, 8]
N_list = [2 ** 10, 2 ** 12, 2 ** 14]
evict_cycle_list = [1, 2, 4, 8, 16]
NUM_OPS = 20000

results = []

for N in N_list:
    for Z in Z_list:
        for evict_cycle in evict_cycle_list:
            print(f"Running: N={N}, Z={Z}, evict_cycle={evict_cycle}")
            oram = DeterministicPathORAM(num_blocks=N, bucket_size=Z, seed=42, det_evict_period=evict_cycle)
            max_stash = 0
            max_stash_count = 0
            stash_sum = 0
            delay_sum = 0
            op_count = 0
            max_delay = 0

            for step in range(NUM_OPS):
                idx = random.randrange(N)
                op = random.choice([Operation.READ, Operation.WRITE])
                data = [idx, step] if op == Operation.WRITE else None
                t0 = time.perf_counter()
                oram.access(op, idx, new_data=data)
                t1 = time.perf_counter()
                delay = (t1 - t0) * 1e6  # μs

                # stash count
                stash_sz = oram.stash_size()
                if stash_sz > max_stash:
                    max_stash = stash_sz
                    max_stash_count = 1
                elif stash_sz == max_stash:
                    max_stash_count += 1

                stash_sum += stash_sz
                delay_sum += delay
                max_delay = max(max_delay, delay)
                op_count += 1

            avg_stash = stash_sum / op_count
            avg_delay = delay_sum / op_count

            results.append({
                "N": N,
                "Z": Z,
                "evict_cycle": evict_cycle,
                "max_stash": max_stash,
                "max_stash_count": max_stash_count,
                "avg_stash": round(avg_stash, 2),
                "avg_delay(us)": round(avg_delay, 2),
                "max_delay(us)": round(max_delay, 2)
            })
            print(f"  -> max_stash={max_stash}, peak_count={max_stash_count}, avg_stash={avg_stash:.2f}, avg_delay={avg_delay:.2f}μs, max_delay={max_delay:.2f}μs")

# write into CSV
with open("oram_experiment_batch.csv", "w", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
print("All experiment is finished, and results are saved in oram_experiment_batch.csv")
