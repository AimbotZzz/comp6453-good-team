import os
import random

_can_show = True
try:
    import matplotlib
    matplotlib.use("TkAgg")
except Exception:
    _can_show = False

import matplotlib.pyplot as plt
import networkx as nx

from secure_oram import SecureORAM
from bucket import Bucket

def build_tree_edges(tree_size: int):
    edges = []
    for i in range(1, tree_size):
        parent = (i - 1) // 2
        edges.append((parent, i))
    return edges


def hierarchy_pos_fixed(tree_size: int, tree_height: int, vert_gap: float = 1.6):
    pos = {}
    for level in range(tree_height):
        y = -level * vert_gap
        nodes_in_level = 2 ** level
        spacing = 1.0 / max(1, nodes_in_level)
        for i in range(nodes_in_level):
            node_idx = (2 ** level - 1) + i
            if node_idx >= tree_size:
                continue
            x = (i + 0.5) * spacing
            pos[node_idx] = (x, y)
    return pos

def format_bucket_label(bucket, max_items: int = 6) -> str:
    items = []
    for blk in getattr(bucket, "blocks", []):
        idx = getattr(blk, "index", None)
        items.append("D" if idx == -1 else str(idx))

    if not items:
        return "-"

    if len(items) > max_items:
        return ",".join(items[:max_items]) + ",…"
    return ",".join(items)


def draw_oram_tree(oram: SecureORAM, stash, access_leaf=None,
                   round_num: int = None, save: bool = True, outdir: str = "output"):
    tree_size = len(oram.server.tree)
    tree_height = oram.tree_height

    cap = Bucket.max_size if Bucket.max_size is not None else 0

    max_nodes_last_level = 2 ** (tree_height - 1)
    fig_w = max(12, min(32, int(1.0 * max_nodes_last_level) + 8))
    fig_h = max(8, int(2 + 1.2 * tree_height))

    fig = plt.figure(figsize=(fig_w, fig_h))
    ax = plt.gca()

    G = nx.Graph()
    G.add_nodes_from(range(tree_size))
    G.add_edges_from(build_tree_edges(tree_size))
    pos = hierarchy_pos_fixed(tree_size, tree_height, vert_gap=1.6)

    node_labels = {}
    node_colors = []
    path_nodes = set()
    if access_leaf is not None:
        try:
            path_nodes = set(oram.server.get_path_nodes(access_leaf))
        except Exception:
            path_nodes = set()

    for i in range(tree_size):
        bucket = oram.server.tree[i]
        used = len(getattr(bucket, "blocks", []))
        base = format_bucket_label(bucket, max_items=6)
        label = f"{base}  ({used}/{cap})" if cap else base
        node_labels[i] = label
        node_colors.append("lightgreen" if i in path_nodes else "lightblue")

    # 绘制
    nx.draw(
        G, pos,
        with_labels=False,
        node_color=node_colors,
        node_size=1800,
        linewidths=1.0,
        width=1.0,
        ax=ax
    )
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, ax=ax)

    stash_labels = []
    for blk in stash:
        idx = getattr(blk, "index", None)
        stash_labels.append("D" if idx == -1 else str(idx))
    stash_str = ", ".join(stash_labels) if stash_labels else "Empty"

    display_bucket_size = Bucket.max_size if Bucket.max_size is not None else "N/A"
    text_lines = [
        f"Stash: {stash_str}",
        f"Blocks in stash: {len(stash)}",
        f"Tree height: {tree_height}",
        f"Bucket size: {display_bucket_size}",   # ★ 不再是 N/A
        f"Flush interval: {getattr(oram, 'flush_interval', 'N/A')}",
    ]
    if round_num is not None:
        text_lines.insert(0, f"Round #{round_num}")

    ax.text(
        1.02, 0.5, "\n".join(text_lines),
        transform=ax.transAxes,
        fontsize=10,
        va="center",
        ha="left",
        bbox=dict(facecolor="white", edgecolor="black", boxstyle="round,pad=0.4")
    )

    ax.set_title("SecureORAM — Tree & Stash Visualization", fontsize=14, pad=16)
    ax.set_axis_off()
    plt.tight_layout()

    # 保存图片
    if save:
        os.makedirs(outdir, exist_ok=True)
        fname = f"oram_round_{round_num if round_num is not None else 'init'}.png"
        fpath = os.path.join(outdir, fname)
        plt.savefig(fpath, dpi=150, bbox_inches="tight")
        print(f"[Saved] {fpath}")

    if _can_show:
        try:
            plt.show()
        except Exception:
            pass

    plt.close(fig)

def run_demo(
    num_blocks: int = 8,
    tree_height: int = 4,
    bucket_size: int = 3,
    flush_interval: int = 4,
    rounds: int = 6,
    save_each_round: bool = True
):
    oram = SecureORAM(
        num_blocks=num_blocks,
        tree_height=tree_height,
        bucket_size=bucket_size,
        flush_interval=flush_interval
    )

    for i in range(num_blocks):
        data = [i, i + 100]
        oram.access("write", i, data)

    draw_oram_tree(oram, oram.stash, access_leaf=None, round_num=0, save=save_each_round)

    for r in range(1, rounds + 1):
        index = random.randint(0, num_blocks - 1)
        op = random.choice(["read", "write"])

        leaf_before = oram.position_map[index]

        if op == "write":
            payload = [index, 1000 + r]
            print(f"\n=== Round {r}: {op.upper()} block {index} data={payload} ===")
            oram.access(op, index, payload)
        else:
            print(f"\n=== Round {r}: {op.upper()} block {index} ===")
            oram.access(op, index)

        draw_oram_tree(oram, oram.stash, access_leaf=leaf_before, round_num=r, save=save_each_round)


if __name__ == "__main__":
    run_demo(
        num_blocks=12,
        tree_height=5,
        bucket_size=3,
        flush_interval=4,
        rounds=8,
        save_each_round=True
    )
