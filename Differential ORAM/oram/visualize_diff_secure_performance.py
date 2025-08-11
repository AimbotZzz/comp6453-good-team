import json
import os
import re
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def find_latest_results(root_dir: str) -> str:
    pattern = re.compile(r"^diff_secure_performance_results_\d{8}_\d{6}\.json$")
    candidates = [f for f in os.listdir(root_dir) if pattern.match(f)]
    if not candidates:
        raise FileNotFoundError('No diff_secure_performance_results_*.json found')
    candidates.sort()
    return os.path.join(root_dir, candidates[-1])


def load_results(json_path: str) -> dict:
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_output_dir() -> str:
    out_dir = f"performance_charts_diff_secure_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def sort_key(r):
    return (r.get('num_blocks', 0), r.get('tree_height', 0), r.get('bucket_size', 0))


def group_results(data: list):
    # 返回有序列表，确保配置顺序一致
    return sorted([r for r in data if 'error' not in r], key=sort_key)


def plot_grouped_bars(ax, x_labels, groups, series_labels, title, ylabel):
    x = np.arange(len(x_labels))
    width = 0.22
    offsets = np.linspace(-width, width, num=len(groups))
    for i, values in enumerate(groups):
        ax.bar(x + offsets[i], values, width=width, label=series_labels[i], alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=30, ha='right')
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True, alpha=0.3)


def main(json_path: str | None = None):
    root = os.path.dirname(__file__)
    json_file = json_path or find_latest_results(root)
    data = load_results(json_file)
    out_dir = ensure_output_dir()

    full = group_results(data['full_path'])
    diff = group_results(data['differential'])
    sdiff = group_results(data['secure_differential'])

    # 对齐配置（以 full 为基准）
    def make_key(r):
        return (r['num_blocks'], r['tree_height'], r['bucket_size'])
    base_keys = [make_key(r) for r in full]
    def pick(series):
        m = {make_key(r): r for r in series}
        return [m.get(k) for k in base_keys]
    diff_a = pick(diff)
    sdiff_a = pick(sdiff)

    labels = [f"B{b}-H{h}-S{k}" for (b, h, k) in base_keys]

    # Read/Write/Mixed times (ms)
    to_ms = lambda arr, key: [r[key] * 1000 if r else None for r in arr]
    full_read = to_ms(full, 'avg_read_time')
    diff_read = to_ms(diff_a, 'avg_read_time')
    sdiff_read = to_ms(sdiff_a, 'avg_read_time')

    full_write = to_ms(full, 'avg_write_time')
    diff_write = to_ms(diff_a, 'avg_write_time')
    sdiff_write = to_ms(sdiff_a, 'avg_write_time')

    full_mixed = to_ms(full, 'avg_mixed_time')
    diff_mixed = to_ms(diff_a, 'avg_mixed_time')
    sdiff_mixed = to_ms(sdiff_a, 'avg_mixed_time')

    # stash
    full_stash = [r['final_stash_size'] if r else None for r in full]
    diff_stash = [r['final_stash_size'] if r else None for r in diff_a]
    sdiff_stash = [r['final_stash_size'] if r else None for r in sdiff_a]

    # Plot: read time
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_grouped_bars(ax, labels,
                      [full_read, diff_read, sdiff_read],
                      ['Full-path', 'Differential', 'Differential + Dummy + Ring'],
                      'Average Read Time (ms)', 'ms')
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, 'read_time_comparison.png'), dpi=300); plt.close()

    # Plot: write time
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_grouped_bars(ax, labels,
                      [full_write, diff_write, sdiff_write],
                      ['Full-path', 'Differential', 'Differential + Dummy + Ring'],
                      'Average Write Time (ms)', 'ms')
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, 'write_time_comparison.png'), dpi=300); plt.close()

    # Plot: mixed time
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_grouped_bars(ax, labels,
                      [full_mixed, diff_mixed, sdiff_mixed],
                      ['Full-path', 'Differential', 'Differential + Dummy + Ring'],
                      'Average Mixed Operation Time (ms)', 'ms')
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, 'mixed_time_comparison.png'), dpi=300); plt.close()

    # Plot: stash size
    fig, ax = plt.subplots(figsize=(14, 6))
    plot_grouped_bars(ax, labels,
                      [full_stash, diff_stash, sdiff_stash],
                      ['Full-path', 'Differential', 'Differential + Dummy + Ring'],
                      'Final Stash Size', 'count')
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, 'stash_size_comparison.png'), dpi=300); plt.close()

    # Speedup over full-path (x): for diff/sdiff
    def compute_speedup(base, target):
        vals = []
        for b, t in zip(base, target):
            if b and t and t > 0:
                vals.append(b / t)
            else:
                vals.append(None)
        return vals

    diff_speed_read = compute_speedup(full_read, diff_read)
    sdiff_speed_read = compute_speedup(full_read, sdiff_read)
    diff_speed_write = compute_speedup(full_write, diff_write)
    sdiff_speed_write = compute_speedup(full_write, sdiff_write)
    diff_speed_mixed = compute_speedup(full_mixed, diff_mixed)
    sdiff_speed_mixed = compute_speedup(full_mixed, sdiff_mixed)

    fig, axs = plt.subplots(3, 1, figsize=(14, 14))
    plot_grouped_bars(axs[0], labels, [diff_speed_read, sdiff_speed_read], ['Differential', 'Differential + Dummy + Ring'], 'Speedup over Full-path - Read (x)', 'x')
    plot_grouped_bars(axs[1], labels, [diff_speed_write, sdiff_speed_write], ['Differential', 'Differential + Dummy + Ring'], 'Speedup over Full-path - Write (x)', 'x')
    plot_grouped_bars(axs[2], labels, [diff_speed_mixed, sdiff_speed_mixed], ['Differential', 'Differential + Dummy + Ring'], 'Speedup over Full-path - Mixed (x)', 'x')
    plt.tight_layout(); plt.savefig(os.path.join(out_dir, 'speedup_vs_full.png'), dpi=300); plt.close()

    # Text summary
    summary_path = os.path.join(out_dir, 'analysis_summary.md')
    large_tree_indices = [i for i, (b, h, k) in enumerate(base_keys) if h >= 16]
    lines = []
    lines.append('# Differential Write-back ORAM: Three Strategy Comparison\n\n')
    lines.append(f"Data file: {os.path.basename(json_file)}\n\n")
    if large_tree_indices:
        for i in large_tree_indices:
            cfg = labels[i]
            lines.append(f"- Config {cfg}:\n")
            lines.append(f"  - Read (ms): Full-path={full_read[i]:.3f}, Differential={diff_read[i]:.3f}, Secure-Diff={sdiff_read[i]:.3f}\n")
            lines.append(f"  - Write (ms): Full-path={full_write[i]:.3f}, Differential={diff_write[i]:.3f}, Secure-Diff={sdiff_write[i]:.3f}\n")
            lines.append(f"  - Mixed (ms): Full-path={full_mixed[i]:.3f}, Differential={diff_mixed[i]:.3f}, Secure-Diff={sdiff_mixed[i]:.3f}\n")
            lines.append(f"  - Stash: Full-path={full_stash[i]}, Differential={diff_stash[i]}, Secure-Diff={sdiff_stash[i]}\n")
            lines.append(f"  - Read speedup (x): Diff={diff_speed_read[i]:.2f}x, Secure-Diff={sdiff_speed_read[i]:.2f}x\n\n")
    else:
        lines.append('No large-tree config (H>=16) detected. Please check test parameters.\n')

    with open(summary_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"Charts and summary written to: {out_dir}")


if __name__ == '__main__':
    # 允许通过环境变量 JSON_FILE 指定输入
    json_path = os.environ.get('JSON_FILE')
    main(json_path)

