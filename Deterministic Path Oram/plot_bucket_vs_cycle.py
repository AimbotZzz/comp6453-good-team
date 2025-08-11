import pandas as pd
import matplotlib.pyplot as plt

# Read data
df = pd.read_csv("oram_experiment_batch.csv")

# User input constant N
N_fixed = int(input("Please input constant N for analysis (such as 1024, 4096, 16384):"))
df_N = df[df['N'] == N_fixed]

# Draw graph grouped by period
cycle_list = sorted(df_N['evict_cycle'].unique())
colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']

# --- Figure 1: Impact of Bucket Size & Evict Cycle on Read Delay ---
plt.figure(figsize=(10, 5))
for i, cycle in enumerate(cycle_list):
    subset = df_N[df_N['evict_cycle'] == cycle].sort_values('Z')
    plt.plot(subset['Z'], subset['avg_delay(us)']/1000, marker='o', label=f"Evict Cycle={cycle}", color=colors[i % len(colors)])
plt.xlabel("Bucket Size (Z)")
plt.ylabel("Average Read Delay (ms)")
plt.title(f"Impact of Bucket Size & Evict Cycle on Read Delay (N={N_fixed})")
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

# --- Figure 2: Impact of Bucket Size & Evict Cycle on Max Stash---
plt.figure(figsize=(10, 5))
for i, cycle in enumerate(cycle_list):
    subset = df_N[df_N['evict_cycle'] == cycle].sort_values('Z')
    plt.plot(subset['Z'], subset['max_stash'], marker='s', label=f"Evict Cycle={cycle}", color=colors[i % len(colors)])
plt.xlabel("Bucket Size (Z)")
plt.ylabel("Max Stash Size")
plt.title(f"Impact of Bucket Size & Evict Cycle on Max Stash (N={N_fixed})")
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

# --- Figure 3: Impact of Bucket Size & Evict Cycle on Average Stash ---
plt.figure(figsize=(10, 5))
for i, cycle in enumerate(cycle_list):
    subset = df_N[df_N['evict_cycle'] == cycle].sort_values('Z')
    plt.plot(subset['Z'], subset['avg_stash'], marker='s',
             label=f"Evict Cycle={cycle}", color=colors[i % len(colors)])
plt.xlabel("Bucket Size (Z)")
plt.ylabel("Average Stash Size")
plt.title(f"Impact of Bucket Size & Evict Cycle on Average Stash (N={N_fixed})")
plt.legend()
plt.grid(True, linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()
