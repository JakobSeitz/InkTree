"""
Generate the InkTree showcase figure: segmentation colors + relation arrows
across content types and source datasets, to illustrate format generality.

Row 1: math formulas  (CROHME, CROHME+, MathWriting+, MathWriting+ Synthetic)
Row 2: text sentences (DeepWriting, IAMonDB)
Row 3: symbols        (Detexify, Unipen)

Outputs:
    assets/showcase.png        (for README, committed)
    paper/figures/showcase.pdf (for the paper)

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
from datasets.json_loader import get_json_files, _sample_to_row_node

ASSETS_OUT = ROOT / "assets" / "showcase.png"
PAPER_OUT = ROOT / "paper" / "figures" / "showcase.pdf"

N_COLS = 4


def clean_detexify_label(key: str) -> str:
    """'amssymb-OT1-_gg' → '\\gg', 'latex2e-OT1-[' → '['."""
    tail = key.rsplit("-", 1)[-1]
    label = "\\" + tail[1:] if tail.startswith("_") else tail
    # text-mode commands mathtext cannot render → math-mode equivalent
    return {"\\textchi": "\\chi", "\\textless": "<", "\\textgreater": ">"}.get(label, label)


def recover_sentences(root_dir: Path, indices: set[int]) -> dict[int, str]:
    """Reconstruct sentence text (with spaces) from the source JSON word labels.

    The converted DeepWriting/IAMonDB files have empty top-level labels and no
    word boundaries (chars are flattened into one row), so joining sym labels
    loses the spaces. The source `wholeword_segments[].ocr_label` entries are
    per word; walking the files in loader order recovers the i-th sentence.
    """
    sentences: dict[int, str] = {}
    i = 0
    for json_path in get_json_files(root_dir):
        try:
            obj = json.load(open(json_path, encoding="utf-8"))
        except Exception:
            continue
        keys = sorted(
            [k for k in obj if k.startswith("sample")],
            key=lambda k: int(k[6:]) if k[6:].isdigit() else 0,
        )
        for key in keys:
            sample = obj[key]
            if not isinstance(sample, dict):
                continue
            try:
                row = _sample_to_row_node(sample)
            except Exception:
                row = None
            if row is None:
                continue
            if i in indices:
                words = [
                    w.get("ocr_label", "") or ""
                    for w in sample.get("wholeword_segments", [])
                    if isinstance(w, dict)
                ]
                sentences[i] = " ".join(w for w in words if w).strip()
                if len(sentences) == len(indices):
                    return sentences
            i += 1
    return sentences


def load_sample(filename: str, index: int):
    """Load one sample by line index from a JSONL.gz file."""
    with gzip.open(INKTREE_DIR / filename, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i == index:
                return json.loads(line)
    raise IndexError(f"{filename}: index {index} out of range")


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


def main():
    # Sentence labels recovered from the source JSON (converted files lack them)
    dw_sent = recover_sentences(ROOT / "data" / "Deepwriting Dataset", {0, 50})
    iam_sent = recover_sentences(ROOT / "data" / "Iamondb Dataset", {65, 98})

    # Panel spec: (dataset tag, filename, sample index, label override/cleaner, axis margin)
    # Formula indices were hand-picked from find_structured_crohme() candidates.
    rows = [
        ("Formulas", [
            ("CROHME", "crohme_2023test.inktree.jsonl.gz", 65, None),
            ("CROHME+", "crohmeplus_synthetic.inktree.jsonl.gz", 26, None),
            ("MathWriting+", "mwplus_test.inktree.jsonl.gz", 15, None),
            ("MathWriting+ Synth.", "mwplus_synthetic.inktree.jsonl.gz", 99, None),
        ], 0.05),
        ("Text", [
            ("DeepWriting", "deepwriting.inktree.jsonl.gz", 0, dw_sent.get(0)),
            ("DeepWriting", "deepwriting.inktree.jsonl.gz", 50, dw_sent.get(50)),
            ("IAMonDB", "iamondb.inktree.jsonl.gz", 65, iam_sent.get(65)),
            ("IAMonDB", "iamondb.inktree.jsonl.gz", 98, iam_sent.get(98)),
        ], 0.05),
        ("Symbols", [
            ("Detexify", "detexify.inktree.jsonl.gz", 0, clean_detexify_label),
            ("Detexify", "detexify.inktree.jsonl.gz", 1, clean_detexify_label),
            ("Unipen", "unipen.inktree.jsonl.gz", 1, None),
            ("Unipen", "unipen.inktree.jsonl.gz", 4801, None),
        ], 0.6),  # extra margin so single symbols don't fill the panel
    ]

    fig, axes = plt.subplots(
        len(rows), N_COLS,
        figsize=(N_COLS * 3.2, 6.2),
        gridspec_kw={"height_ratios": [1.3, 0.85, 0.85]},
    )

    for r, (row_title, panels, margin) in enumerate(rows):
        for c, (tag, filename, index, label_spec) in enumerate(panels):
            ax = axes[r][c]
            sample = load_sample(filename, index)
            graph, label = decode_graph_sample(sample)
            if callable(label_spec):
                label = label_spec(effective_label(graph, label))
            elif label_spec:
                label = label_spec
            else:
                label = effective_label(graph, label)
            plot_sample_relations(graph, label, ax, fontsize=7)
            ax.margins(margin)
            ax.text(0.5, -0.12, tag, transform=ax.transAxes,
                    fontsize=6, color="0.45", ha="center", va="top")
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
