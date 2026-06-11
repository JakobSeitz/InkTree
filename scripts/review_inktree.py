"""
Visual QA review of all converted InkTree datasets.

For each dataset, draws a grid of randomly sampled inks with their labels so
conversion correctness and rendering consistency can be checked by eye.
One PNG per dataset is written to data/review_plots/.

Usage (from project root):
    python scripts/review_inktree.py                       # all datasets, 12 samples each
    python scripts/review_inktree.py --datasets detexify unipen --n 24
    python scripts/review_inktree.py --annotate            # symbol labels at stroke centroids
    python scripts/review_inktree.py --seed 7              # different random samples
"""

import argparse
import gzip
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.mathtext import MathTextParser

from inktree.decode import decode_graph_sample

INKTREE_DIR = ROOT / "data" / "inktree"
OUT_DIR = ROOT / "data" / "review_plots"

# Canonical current files only (skips stale Feb runs and _t duplicates)
DATASETS = {
    "crohme_2023test":     "crohme_2023test.inktree.jsonl.gz",
    "crohme_2019test":     "crohme_2019test.inktree.jsonl.gz",
    "crohme_2016val":      "crohme_2016val.inktree.jsonl.gz",
    "crohme_2023val":      "crohme_2023val.inktree.jsonl.gz",
    "crohme_real_train":   "crohme_real_train.inktree.jsonl.gz",
    "crohmeplus_synthetic": "crohmeplus_synthetic.inktree.jsonl.gz",
    "mwplus_test":         "mwplus_test.inktree.jsonl.gz",
    "mwplus_val":          "mwplus_val.inktree.jsonl.gz",
    "mwplus_symbols":      "mwplus_symbols.inktree.jsonl.gz",
    "mwplus_train":        "mwplus_train.inktree.jsonl.gz",
    "mwplus_synthetic":    "mwplus_synthetic.inktree.jsonl.gz",
    "deepwriting":         "deepwriting.inktree.jsonl.gz",
    "iamondb":             "iamondb.inktree.jsonl.gz",
    "detexify":            "detexify.inktree.jsonl.gz",
    "unipen":              "unipen.inktree.jsonl.gz",
}

_mathtext_parser = MathTextParser("agg")

# Distinct colors for trace groups (segmentation visualization)
TG_COLORS = plt.cm.tab20.colors

# (node class name) → list of (child_index, relation_label); base/anchor is drawn from
SEMANTIC_RELATIONS = {
    "FracNode":      [(0, "numer"), (1, "denom")],
    "SubNode":       [(1, "sub")],
    "SupNode":       [(1, "sup")],
    "SubSupNode":    [(1, "sub"), (2, "sup")],
    "SqrtNode":      [(0, "inner")],
    "RootNode":      [(0, "inner"), (1, "index")],
    "UnderNode":     [(1, "under")],
    "UnderOverNode": [(1, "under"), (2, "over")],
}
# For these, the arrow source is children[0] (the base); for frac/sqrt/root it is
# the structural node's own strokes (bar / radical) or the whole-node centroid.
BASE_IS_CHILD0 = {"SubNode", "SupNode", "SubSupNode", "UnderNode", "UnderOverNode"}


def subtree_centroid(node):
    """Centroid over all stroke points in a node's subtree (None if no strokes)."""
    xs, ys = [], []
    for tg in node.get_all_trace_groups():
        for trace in tg:
            xs.extend(trace.x)
            ys.extend(trace.y)
    if not xs:
        return None
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _draw_arrow(ax, src, dst, label, color="#444444", curve=False):
    x0, y0 = src
    x1, y1 = dst
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    if dist == 0:
        return
    # Panel scale, used to keep curvature and label offsets visible even for
    # very short arrows (otherwise the label box completely covers the arrow).
    bb = ax.dataLim
    diag = math.hypot(bb.width, bb.height) or 1.0
    rad = 0.0
    if curve:
        rad = 0.25 if dist > 0.2 * diag else 0.5
    ax.annotate(
        "", xy=dst, xytext=src,
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, shrinkA=2, shrinkB=4,
                        connectionstyle=f"arc3,rad={rad}"),
    )
    if label:
        # Place the label beside the arc apex (perpendicular to the arrow),
        # never on top of the arrow itself. arc3's control point sits at
        # mid + rad*(dy,-dx) in display coords; with the inverted y-axis this
        # is (-dy, dx) in data coords.
        nx, ny = -dy / dist, dx / dist
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        off = rad * 0.5 * dist + 0.045 * diag
        ax.text(mx + nx * off, my + ny * off, label, fontsize=5.5, color=color,
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec=color, lw=0.4, alpha=0.9))


def draw_relations(node, ax):
    """Recursively draw relation arrows between subtree centroids."""
    class_name = type(node).__name__

    if class_name in SEMANTIC_RELATIONS:
        if class_name in BASE_IS_CHILD0:
            anchor_node = node.children[0] if node.children else None
            src = subtree_centroid(anchor_node) if anchor_node is not None else None
        else:
            # frac/sqrt/root: anchor at own strokes (bar/radical) if present
            own = node.trace_group
            if own is not None and own.traces:
                xs = [x for t in own.traces for x in t.x]
                ys = [y for t in own.traces for y in t.y]
                src = (sum(xs) / len(xs), sum(ys) / len(ys))
            else:
                src = subtree_centroid(node)
        if src is not None:
            for child_idx, rel_label in SEMANTIC_RELATIONS[class_name]:
                if child_idx < len(node.children) and node.children[child_idx] is not None:
                    dst = subtree_centroid(node.children[child_idx])
                    if dst is not None and dst != src:
                        _draw_arrow(ax, src, dst, rel_label, curve=True)

    elif class_name in ("RowNode", "LineNode"):
        # reading order / line order: light arrows between consecutive children
        label = "line" if class_name == "LineNode" else None
        prev = None
        for child in node.children:
            if child is None:
                continue
            cur = subtree_centroid(child)
            if cur is not None:
                if prev is not None:
                    _draw_arrow(ax, prev, cur, label, color="#aaaaaa")
                prev = cur

    elif class_name == "MatrixNode":
        for row in node.rows():
            prev = None
            for cell in row:
                if cell is None:
                    continue
                cur = subtree_centroid(cell)
                if cur is not None:
                    if prev is not None:
                        _draw_arrow(ax, prev, cur, "cell", color="#aaaaaa")
                    prev = cur

    for child in node.children:
        if child is not None:
            draw_relations(child, ax)


def plot_sample_relations(graph, label: str, ax, sample_idx: int = None, fontsize: float = 7):
    """Plot ink with one color per trace group plus relation arrows."""
    n_strokes = 0
    for i, node in enumerate(graph.get_all_nodes_with_trace_groups()):
        color = TG_COLORS[i % len(TG_COLORS)]
        for trace in node.trace_group:
            ax.plot(trace.x, trace.y, color=color, linewidth=1.4, solid_capstyle="round")
            n_strokes += 1
    draw_relations(graph, ax)
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    if label is not None:
        prefix = f"#{sample_idx}  " if sample_idx is not None else ""
        ax.set_title(f"{prefix}{format_title(label)}", fontsize=fontsize)
    return n_strokes


def reservoir_sample_lines(path: Path, k: int, seed: int) -> tuple[list[str], int]:
    """Reservoir-sample k raw JSONL lines without decoding the whole file."""
    rng = random.Random(seed)
    reservoir: list[str] = []
    total = 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total += 1
            if len(reservoir) < k:
                reservoir.append(line)
            else:
                j = rng.randrange(total)
                if j < k:
                    reservoir[j] = line
    return reservoir, total


def effective_label(graph, label: str) -> str:
    """Fallback for samples with empty top-level label (e.g. DeepWriting/IAMonDB):
    concatenate the symbol labels from the tree."""
    if label and label.strip():
        return label
    syms = [
        node.trace_group.label
        for node in graph.get_all_nodes_with_trace_groups()
        if node.trace_group.label
    ]
    return "".join(syms)


def format_title(label: str, max_len: int = 45) -> str:
    """Render label as mathtext only for real LaTeX (contains a backslash command),
    otherwise show plain text — avoids misrendering of e.g. detexify keys with
    underscores, while keeping math formulas readable."""
    label = (label or "").strip().replace("\n", " ⏎ ")
    if len(label) > max_len:
        label = label[:max_len] + "…"
    if "\\" not in label:
        return label
    candidate = f"${label}$"
    try:
        _mathtext_parser.parse(candidate, dpi=72, prop=None)
        return candidate
    except Exception:
        return label


def plot_sample(graph, label: str, ax, annotate: bool, sample_idx: int):
    n_strokes = 0
    for node in graph.get_all_nodes_with_trace_groups():
        tg = node.trace_group
        for trace in tg:
            ax.plot(trace.x, trace.y, marker=".", markersize=1.5, linewidth=0.9)
            n_strokes += 1
        if annotate and tg.label and tg.traces:
            xs = [x for t in tg.traces for x in t.x]
            ys = [y for t in tg.traces for y in t.y]
            if xs and ys:
                ax.annotate(
                    tg.label,
                    (sum(xs) / len(xs), max(ys)),
                    fontsize=6, color="red", ha="center", va="bottom",
                    annotation_clip=False,
                )
    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    title = format_title(label)
    ax.set_title(f"#{sample_idx}  {title}", fontsize=7)
    return n_strokes


def review_dataset(name: str, filename: str, n: int, seed: int, annotate: bool, relations: bool) -> bool:
    path = INKTREE_DIR / filename
    if not path.exists():
        print(f"  SKIP {name}: {path} not found")
        return False

    lines, total = reservoir_sample_lines(path, n, seed)
    cols = 3
    rows = (len(lines) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.5, rows * 2.8))
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    empty = 0
    for i, line in enumerate(lines):
        sample = json.loads(line)
        graph, label = decode_graph_sample(sample)
        label = effective_label(graph, label)
        if relations:
            n_strokes = plot_sample_relations(graph, label, axes[i], sample_idx=i)
        else:
            n_strokes = plot_sample(graph, label, axes[i], annotate, sample_idx=i)
        if n_strokes == 0:
            empty += 1
            axes[i].set_title(f"#{i}  ⚠ NO STROKES", fontsize=7, color="red")
    for ax in axes[len(lines):]:
        ax.axis("off")

    mode = ", relations+segmentation" if relations else ""
    fig.suptitle(f"{name}  ({filename}, N={total}, showing {len(lines)} random samples, seed={seed}{mode})", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    suffix = "_relations" if relations else ""
    out = OUT_DIR / f"{name}{suffix}.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    warn = f"  ⚠ {empty} samples without strokes!" if empty else ""
    print(f"  OK   {name}: N={total} → {out.relative_to(ROOT)}{warn}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Visual QA review of converted InkTree datasets")
    parser.add_argument("--n", type=int, default=12, help="Samples per dataset (default: 12)")
    parser.add_argument("--datasets", nargs="*", default=None,
                        help=f"Subset to review (default: all). Available: {', '.join(DATASETS)}")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--annotate", action="store_true", help="Draw symbol labels at stroke centroids")
    parser.add_argument("--relations", action="store_true",
                        help="Color each trace group distinctly and draw relation arrows (segmentation + structure QA)")
    args = parser.parse_args()

    selected = args.datasets or list(DATASETS)
    unknown = [d for d in selected if d not in DATASETS]
    if unknown:
        parser.error(f"Unknown dataset(s): {unknown}. Available: {', '.join(DATASETS)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Reviewing {len(selected)} dataset(s), {args.n} samples each → {OUT_DIR.relative_to(ROOT)}/")
    for name in selected:
        review_dataset(name, DATASETS[name], args.n, args.seed, args.annotate, args.relations)
    print("Done.")


if __name__ == "__main__":
    main()
