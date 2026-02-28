"""
Plot a few CROHME test entries loaded from InkML.

Usage:
    python scripts/plot_inkml.py [--n 6] [--no-arrows]
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib.pyplot as plt
from datasets.crohme import CrohmeFileManager
from ink.graph import load_inkml_file
from ink.visualize import TraceVisualizer


def main():
    parser = argparse.ArgumentParser(description="Plot CROHME test entries from InkML")
    parser.add_argument("--n", type=int, default=6, help="Number of entries to plot (default: 6)")
    parser.add_argument("--no-arrows", action="store_true", help="Disable relation arrows")
    args = parser.parse_args()

    files = CrohmeFileManager.get_2023test_files()
    if not files:
        print("No CROHME 2023 test files found. Check data/CROHME23/INKML/.")
        return

    n = min(args.n, len(files))
    cols = min(3, n)
    rows = (n + cols - 1) // cols

    print(f"Plotting {n} InkML entries from CROHME 2023 test set...")

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    if n == 1:
        axes = [[axes]]
    elif rows == 1:
        axes = [axes]

    loaded = 0
    for i, path in enumerate(files):
        if loaded >= n:
            break
        graph = load_inkml_file(path)
        if graph is None:
            continue

        row, col = loaded // cols, loaded % cols
        ax = axes[row][col]

        for node in graph.get_all_nodes_with_trace_groups():
            for trace in node.trace_group:
                ax.plot(trace.x, trace.y, marker=".", markersize=3, linewidth=1)

        ax.set_aspect("equal")
        ax.invert_yaxis()
        ax.axis("off")
        try:
            ax.set_title(f"${graph.latex()}$", fontsize=9)
        except Exception:
            ax.set_title(graph.as_pretty_formula(), fontsize=9)
        loaded += 1

    # hide any unused subplots
    for idx in range(loaded, rows * cols):
        axes[idx // cols][idx % cols].axis("off")

    plt.suptitle("CROHME 2023 — InkML", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
