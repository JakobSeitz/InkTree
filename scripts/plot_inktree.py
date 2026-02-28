"""
Plot CROHME test entries loaded from the InkTree format and compare side-by-side
with the same entries loaded directly from InkML.

Requires the InkTree file to exist at data/inktree/crohme2023_test.inktree.jsonl.gz.
Run scripts/benchmark.py first if it doesn't.

Usage:
    python scripts/plot_inktree.py [--n 4]
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import matplotlib.pyplot as plt
from pathlib import Path

from datasets.crohme import CrohmeFileManager
from ink.graph import load_inkml_file
from inktree.io import load_inktree


INKTREE_PATH = Path(__file__).parent.parent / "data" / "inktree" / "crohme_2023test.inktree.jsonl.gz"


def _plot_graph(graph, ax, title=""):
    for node in graph.get_all_nodes_with_trace_groups():
        for trace in node.trace_group:
            ax.plot(trace.x, trace.y, marker=".", markersize=3, linewidth=1)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(title, fontsize=8)


def main():
    parser = argparse.ArgumentParser(description="Compare InkML vs InkTree rendering side-by-side")
    parser.add_argument("--n", type=int, default=8, help="Number of entries to compare (default: 4)")
    args = parser.parse_args()

    if not INKTREE_PATH.exists():
        print(f"InkTree file not found: {INKTREE_PATH}")
        print("Run `python scripts/benchmark.py` first to convert the dataset.")
        return

    files = CrohmeFileManager.get_2023test_files()
    if not files:
        print("No CROHME 2023 test files found. Check data/CROHME23/INKML/.")
        return

    inktree_samples = load_inktree(INKTREE_PATH)
    n = min(args.n, len(files), len(inktree_samples))
    print(f"Comparing {n} entries: InkML (left) vs InkTree (right)...")

    fig, axes = plt.subplots(n, 2, figsize=(8, 3 * n))
    if n == 1:
        axes = [axes]

    loaded = 0
    inkml_idx = 0
    while loaded < n and inkml_idx < len(files):
        graph_inkml = load_inkml_file(files[inkml_idx])
        inkml_idx += 1
        if graph_inkml is None:
            continue

        graph_inktree, label = inktree_samples[loaded]

        try:
            title = f"${graph_inkml.latex()}$"
        except Exception:
            title = graph_inkml.as_pretty_formula()

        _plot_graph(graph_inkml, axes[loaded][0], title=f"InkML: {title}")
        _plot_graph(graph_inktree, axes[loaded][1], title=f"InkTree: {title}")
        loaded += 1

    plt.suptitle("InkML vs InkTree — CROHME 2023 test", fontsize=12, y=1.01)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
