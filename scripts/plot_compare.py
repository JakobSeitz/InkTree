"""
Visuelle Vergleichs-Plots: Source-Format (InkML / JSONL) vs. InkTree

Zeigt N Samples nebeneinander:  links = Original-Format, rechts = InkTree.
Mit --complex werden bevorzugt Formeln mit Bruch/Wurzel-Nodes ausgesucht.

Verfügbare Datasets (--dataset):
  InkML-Quellen:
    crohme_2023test   CROHME 2023 Test (2 300)
    crohme_2019test   CROHME 2019 Test (1 199)
    crohme_2016val    CROHME 2016 Val  (1 147)
    crohme_2023val    CROHME 2023 Val  (  555)
    crohme_real_train CROHME Real Train (12 024)
    mwplus_test       MathWriting+ Test  (5 739)
    mwplus_val        MathWriting+ Val   (9 336)
    mwplus_symbols    MathWriting+ Symbols (6 276)
    mwplus_train      MathWriting+ Train (sample)
    mwplus_synthetic  MathWriting+ Synthetic (sample)

  JSONL-Quellen:
    unipen            Unipen (79 452)
    deepwriting       DeepWriting (4 087)
    iamondb           IAMonDB (11 242)
    detexify          Detexify (210 454)

Beispiel-Aufrufe:
    python scripts/plot_compare.py --dataset crohme_2023test --n 8 --complex
    python scripts/plot_compare.py --dataset mwplus_test --n 6
    python scripts/plot_compare.py --dataset unipen --n 8 --offset 100
    python scripts/plot_compare.py --dataset iamondb --n 6 --complex
    python scripts/plot_compare.py --all                 # alle Datasets, je 2 Samples
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path

from inktree.io import load_inktree
from datasets.jsonl_loader import load_jsonl
from ink.nodes.frac_node import FracNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.root_node import RootNode


INKTREE_DIR = Path(ROOT) / "data" / "inktree"
JSONL_DIR   = Path(ROOT) / "data" / "jsonl"

# ── Dataset-Definitionen ─────────────────────────────────────────────────────

def _inkml_loader(file_getter_fn):
    """Gibt (load_fn, inktree_path, title) zurück für InkML-Quellen."""
    def loader(max_n):
        from ink.graph import load_inkml_file
        files = file_getter_fn()
        graphs, sources = [], []
        for f in files:
            if len(graphs) >= max_n:
                break
            g = load_inkml_file(f)
            if g is not None:
                graphs.append(g)
                sources.append(os.path.basename(f))
        return graphs, sources
    return loader


def _jsonl_loader(jsonl_path):
    def loader(max_n):
        graphs = load_jsonl(jsonl_path, max_samples=max_n)
        sources = [jsonl_path.name] * len(graphs)
        return graphs, sources
    return loader


def _get_crohme_2023val_files():
    from datasets.crohme import InkML_path
    val_dir = os.path.join(InkML_path, "val", "CROHME2023_val")
    return [os.path.join(val_dir, f) for f in os.listdir(val_dir) if f.endswith(".inkml")]


DATASETS = {
    # slug: (source_loader_fn, inktree_file, display_title)
    "crohme_2023test": (
        _inkml_loader(lambda: __import__('datasets.crohme', fromlist=['CrohmeFileManager']).CrohmeFileManager.get_2023test_files()),
        INKTREE_DIR / "crohme_2023test.inktree.jsonl.gz",
        "CROHME 2023 Test",
    ),
    "crohme_2019test": (
        _inkml_loader(lambda: __import__('datasets.crohme', fromlist=['CrohmeFileManager']).CrohmeFileManager.get_2019test_files()),
        INKTREE_DIR / "crohme_2019test.inktree.jsonl.gz",
        "CROHME 2019 Test",
    ),
    "crohme_2016val": (
        _inkml_loader(lambda: __import__('datasets.crohme', fromlist=['CrohmeFileManager']).CrohmeFileManager.get_2016test_files()),
        INKTREE_DIR / "crohme_2016val.inktree.jsonl.gz",
        "CROHME 2016 Val",
    ),
    "crohme_2023val": (
        _inkml_loader(_get_crohme_2023val_files),
        INKTREE_DIR / "crohme_2023val.inktree.jsonl.gz",
        "CROHME 2023 Val",
    ),
    "crohme_real_train": (
        _inkml_loader(lambda: __import__('datasets.crohme', fromlist=['CrohmeFileManager']).CrohmeFileManager.get_real_train_files()),
        INKTREE_DIR / "crohme_real_train.inktree.jsonl.gz",
        "CROHME Real Train",
    ),
    "mwplus_test": (
        _inkml_loader(lambda: __import__('datasets.mathwriting', fromlist=['MathWritingFileManager']).MathWritingFileManager.get_test_files()),
        INKTREE_DIR / "mwplus_test.inktree.jsonl.gz",
        "MathWriting+ Test",
    ),
    "mwplus_val": (
        _inkml_loader(lambda: __import__('datasets.mathwriting', fromlist=['MathWritingFileManager']).MathWritingFileManager.get_val_files()),
        INKTREE_DIR / "mwplus_val.inktree.jsonl.gz",
        "MathWriting+ Val",
    ),
    "mwplus_symbols": (
        _inkml_loader(lambda: __import__('datasets.mathwriting', fromlist=['MathWritingFileManager']).MathWritingFileManager.get_symbol_files()),
        INKTREE_DIR / "mwplus_symbols.inktree.jsonl.gz",
        "MathWriting+ Symbols",
    ),
    "mwplus_train": (
        _inkml_loader(lambda: __import__('datasets.mathwriting', fromlist=['MathWritingFileManager']).MathWritingFileManager.get_train_files()),
        INKTREE_DIR / "mwplus_train.inktree.jsonl.gz",
        "MathWriting+ Train (sample)",
    ),
    "mwplus_synthetic": (
        _inkml_loader(lambda: __import__('datasets.mathwriting', fromlist=['MathWritingFileManager']).MathWritingFileManager.get_synthetic_files()),
        INKTREE_DIR / "mwplus_synthetic.inktree.jsonl.gz",
        "MathWriting+ Synthetic (sample)",
    ),
    "unipen": (
        _jsonl_loader(JSONL_DIR / "unipen.jsonl.gz"),
        INKTREE_DIR / "unipen.inktree.jsonl.gz",
        "Unipen",
    ),
    "deepwriting": (
        _jsonl_loader(JSONL_DIR / "deep_writing.jsonl.gz"),
        INKTREE_DIR / "deep_writing.inktree.jsonl.gz",
        "DeepWriting",
    ),
    "iamondb": (
        _jsonl_loader(JSONL_DIR / "iamondb.jsonl.gz"),
        INKTREE_DIR / "iamondb.inktree.jsonl.gz",
        "IAMonDB",
    ),
    "detexify": (
        _jsonl_loader(JSONL_DIR / "detexify.jsonl.gz"),
        INKTREE_DIR / "detexify.inktree.jsonl.gz",
        "Detexify",
    ),
}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _has_complex_structure(graph):
    """True wenn der Graph einen Bruch oder eine Wurzel enthält."""
    for node in graph.get_all_nodes():
        if isinstance(node, (FracNode, SqrtNode, RootNode)):
            return True
    return False


def _count_node_types(graph):
    """Gibt dict mit Anzahl pro Node-Typ zurück (für den Titel)."""
    from collections import Counter
    c = Counter(type(n).__name__ for n in graph.get_all_nodes())
    return c


def _plot_graph(graph, ax, title="", color_by_type=True):
    """Plottet alle Traces eines Graphen, farblich nach Node-Typ."""
    TYPE_COLORS = {
        "SymbolNode":   "#4C72B0",
        "FracNode":     "#DD8452",
        "SqrtNode":     "#55A868",
        "RootNode":     "#C44E52",
        "RowNode":      "#8172B3",
        "SupNode":      "#937860",
        "SubNode":      "#DA8BC3",
        "SubSupNode":   "#8C8C8C",
        "UnderNode":    "#CCB974",
        "UnderOverNode":"#64B5CD",
    }
    default_color = "#999999"

    nodes_with_tg = graph.get_all_nodes_with_trace_groups()
    if not nodes_with_tg:
        ax.text(0.5, 0.5, "(keine Traces)", ha="center", va="center",
                transform=ax.transAxes, fontsize=7, color="red")
    else:
        for node in nodes_with_tg:
            tg = node.trace_group
            if tg is None or len(tg) == 0:
                continue
            color = TYPE_COLORS.get(type(node).__name__, default_color) if color_by_type else None
            for trace in tg:
                ax.plot(trace.x, trace.y,
                        color=color, marker=".", markersize=2, linewidth=1,
                        alpha=0.85)

    ax.set_aspect("equal")
    ax.invert_yaxis()
    ax.axis("off")
    ax.set_title(title, fontsize=7, pad=2)


def _make_title(graph, prefix):
    """Erstellt Titelzeile als plain text (kein Matplotlib-LaTeX-Rendering)."""
    try:
        label = graph.latex() or ""
        if len(label) > 50:
            label = label[:50] + "…"
        counts = _count_node_types(graph)
        has_frac = counts.get("FracNode", 0)
        has_sqrt = counts.get("SqrtNode", 0) + counts.get("RootNode", 0)
        markers = []
        if has_frac: markers.append(f"frac×{has_frac}")
        if has_sqrt: markers.append(f"sqrt×{has_sqrt}")
        info = "  " + ", ".join(markers) if markers else ""
        # Plain-text: Backslash als \\, $ als \$ – alles lesbar, kein Render-Crash
        safe_label = label.replace("\\", "\\\\").replace("$", r"\$")
        return f"{prefix}{info}\n{safe_label}" if safe_label else f"{prefix}{info}"
    except Exception:
        return prefix


def plot_dataset(slug, n=6, offset=0, find_complex=False, save_path=None):
    """Lädt und plottet N Samples eines Datasets im Vergleich InkML vs. InkTree."""
    if slug not in DATASETS:
        print(f"Unbekanntes Dataset: '{slug}'. Verfügbar: {list(DATASETS.keys())}")
        return

    source_loader, inktree_path, title = DATASETS[slug]

    if not inktree_path.exists():
        print(f"InkTree-Datei nicht gefunden: {inktree_path}")
        print("Führe zuerst 'python scripts/benchmark_multi.py' aus.")
        return

    # ── Source-Graphs laden ──────────────────────────────────────────────────
    print(f"Lade Source-Graphs für {title}…")
    load_n = offset + (n * 20 if find_complex else n)   # extra für Filterung
    src_graphs, _ = source_loader(load_n)

    # ── InkTree laden ────────────────────────────────────────────────────────
    print(f"Lade InkTree aus {inktree_path.name}…")
    inktree_samples = load_inktree(inktree_path)

    # ── Samples auswählen ────────────────────────────────────────────────────
    def pick(graphs, want_complex):
        result = []
        for g in graphs[offset:]:
            if len(result) >= n:
                break
            if want_complex and not _has_complex_structure(g):
                continue
            result.append(g)
        # Fallback: wenn --complex keine Treffer, alle nehmen
        if not result:
            result = graphs[offset:offset + n]
        return result

    src_sel  = pick(src_graphs, find_complex)
    tree_sel = pick([g for g, _ in inktree_samples], find_complex)

    actual_n = min(len(src_sel), len(tree_sel))
    if actual_n == 0:
        print("Keine Samples gefunden.")
        return

    # ── Plot ─────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(actual_n, 2, figsize=(10, 3.5 * actual_n),
                              squeeze=False)
    fig.suptitle(f"{title}  —  Links: Source-Format  |  Rechts: InkTree  "
                 f"{'(Bruch/Wurzel bevorzugt)' if find_complex else ''}",
                 fontsize=11, y=1.0)

    for i in range(actual_n):
        sg = src_sel[i]
        tg = tree_sel[i]
        _plot_graph(sg,  axes[i][0], title=_make_title(sg,  "Source"))
        _plot_graph(tg,  axes[i][1], title=_make_title(tg,  "InkTree"))

    # Legende für Node-Farben
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color="#4C72B0", lw=2, label="SymbolNode"),
        Line2D([0], [0], color="#DD8452", lw=2, label="FracNode (Bruchstrich)"),
        Line2D([0], [0], color="#55A868", lw=2, label="SqrtNode (Wurzel)"),
        Line2D([0], [0], color="#C44E52", lw=2, label="RootNode (n-te Wurzel)"),
        Line2D([0], [0], color="#8172B3", lw=2, label="RowNode"),
        Line2D([0], [0], color="#937860", lw=2, label="SupNode"),
    ]
    fig.legend(handles=legend_items, loc="lower center", ncol=3,
               fontsize=8, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout(rect=[0, 0.04, 1, 0.97])

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Gespeichert: {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_all_datasets(n_per_dataset=2, save_dir=None):
    """Erstellt für jedes Dataset einen schnellen Überblick mit n_per_dataset Samples."""
    for slug in DATASETS:
        print(f"\n=== {slug} ===")
        save_path = None
        if save_dir:
            save_path = Path(save_dir) / f"compare_{slug}.png"
        try:
            plot_dataset(slug, n=n_per_dataset, find_complex=True,
                         save_path=save_path)
        except Exception as e:
            print(f"  FEHLER bei {slug}: {e}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Visueller Vergleich Source-Format vs. InkTree",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dataset", "-d",
        choices=list(DATASETS.keys()),
        default="crohme_2023test",
        help="Welches Dataset anzeigen (default: crohme_2023test)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Alle Datasets nacheinander plotten (je --n Samples)",
    )
    parser.add_argument(
        "--n", type=int, default=6,
        help="Anzahl Samples pro Dataset (default: 6)",
    )
    parser.add_argument(
        "--offset", type=int, default=0,
        help="Erste N Samples überspringen (default: 0)",
    )
    parser.add_argument(
        "--complex", action="store_true",
        help="Bevorzuge Formeln mit Brüchen oder Wurzeln",
    )
    parser.add_argument(
        "--save-dir",
        metavar="DIR",
        default=None,
        help="Plots als PNG in dieses Verzeichnis speichern statt anzeigen",
    )
    args = parser.parse_args()

    if args.save_dir:
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)
        matplotlib.use("Agg")   # kein Display nötig, muss vor pyplot-Import gesetzt werden

    if args.all:
        plot_all_datasets(n_per_dataset=args.n, save_dir=args.save_dir)
    else:
        save_path = None
        if args.save_dir:
            save_path = Path(args.save_dir) / f"compare_{args.dataset}.png"
        plot_dataset(
            args.dataset,
            n=args.n,
            offset=args.offset,
            find_complex=args.complex,
            save_path=save_path,
        )


if __name__ == "__main__":
    main()
