"""
Generate the InkTree showcase figure: segmentation colors + relation arrows
across three very different source datasets (CROHME formulas, DeepWriting
sentences, Detexify symbols) to illustrate format generality.

Outputs:
    assets/showcase.png        (for README, committed)
    paper/fig/showcase.pdf     (for the paper)

Usage (from project root):
    python scripts/make_showcase.py
"""

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from inktree.decode import decode_graph_sample
from scripts.review_inktree import plot_sample_relations, effective_label, INKTREE_DIR


def clean_detexify_label(key: str) -> str:
    """'amssymb-OT1-_gg' → '\\gg', 'latex2e-OT1-[' → '['."""
    tail = key.rsplit("-", 1)[-1]
    label = "\\" + tail[1:] if tail.startswith("_") else tail
    # text-mode commands mathtext cannot render → math-mode equivalent
    return {"\\textchi": "\\chi"}.get(label, label)

ASSETS_OUT = ROOT / "assets" / "showcase.png"
PAPER_OUT = ROOT / "paper" / "figures" / "showcase.pdf"

N_COLS = 4


def load_samples(filename: str, indices: list[int]):
    """Load specific sample indices (sorted single pass) from a JSONL.gz file."""
    wanted = set(indices)
    found = {}
    with gzip.open(INKTREE_DIR / filename, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i in wanted:
                found[i] = json.loads(line)
                if len(found) == len(wanted):
                    break
    return [found[i] for i in indices]


def find_structured_crohme(filename: str, n: int, max_strokes: int = 14) -> list[int]:
    """Pick formula samples that contain frac/sqrt/sup structure but stay compact."""
    picked = []
    with gzip.open(INKTREE_DIR / filename, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if ('"frac"' in line or '"sqrt"' in line) and ('"sup"' in line or '"sub"' in line):
                if line.count('"x"') <= max_strokes:
                    picked.append(i)
                    if len(picked) == n:
                        break
    return picked


def find_short_samples(filename: str, n: int, min_strokes: int, max_strokes: int,
                       max_chars: int = None) -> list[int]:
    """Pick samples within a stroke-count range (keeps panels readable).
    max_chars additionally limits the symbol count (e.g. single words)."""
    picked = []
    with gzip.open(INKTREE_DIR / filename, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not (min_strokes <= line.count('"x"') <= max_strokes):
                continue
            if max_chars is not None and line.count('"label"') - 1 > max_chars:
                continue
            picked.append(i)
            if len(picked) == n:
                break
    return picked


def main():
    rows = [
        ("CROHME (math formulas, InkML)", "crohme_2023test.inktree.jsonl.gz",
         find_structured_crohme("crohme_2023test.inktree.jsonl.gz", N_COLS), None),
        # hand-picked single-word samples (multi-word labels concatenate without
        # spaces because the converted files have no top-level label)
        ("DeepWriting (cursive text, JSON)", "deepwriting.inktree.jsonl.gz",
         [11, 209, 846, 1441], None),
        ("Detexify (isolated symbols, SQL)", "detexify.inktree.jsonl.gz",
         find_short_samples("detexify.inktree.jsonl.gz", N_COLS, 2, 4), clean_detexify_label),
    ]

    fig, axes = plt.subplots(len(rows), N_COLS, figsize=(N_COLS * 3.2, len(rows) * 2.2))

    for r, (row_title, filename, indices, label_fn) in enumerate(rows):
        samples = load_samples(filename, indices)
        for c, sample in enumerate(samples):
            graph, label = decode_graph_sample(sample)
            label = effective_label(graph, label)
            if label_fn is not None:
                label = label_fn(label)
            plot_sample_relations(graph, label, axes[r][c], fontsize=7)
        axes[r][0].set_ylabel(row_title, fontsize=8)
        axes[r][0].axis("on")
        axes[r][0].set_xticks([])
        axes[r][0].set_yticks([])
        for spine in axes[r][0].spines.values():
            spine.set_visible(False)

    fig.tight_layout()
    ASSETS_OUT.parent.mkdir(parents=True, exist_ok=True)
    PAPER_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS_OUT, dpi=160, bbox_inches="tight")
    fig.savefig(PAPER_OUT, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {ASSETS_OUT.relative_to(ROOT)} and {PAPER_OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
