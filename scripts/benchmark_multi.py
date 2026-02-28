"""
Multi-dataset benchmark: Original Format vs. InkTree

Measures file size and load-time for every dataset and compares the original
source format against InkTree loading.

Source formats benchmarked
--------------------------
  InkML    – raw XML (full parse + MathML relation-graph construction)
               used for CROHME and MathWriting+
  .json    – JSON folder hierarchy (DeepWriting, IAMonDB)
  .sql     – PostgreSQL dump (Detexify)
  .tgz     – Unipen CDROM archive (Unipen)

Datasets covered
----------------
  CROHME (via InkML)
    • CROHME 2023 Test  (2 300 expressions)
    • CROHME 2019 Test  (1 199)
    • CROHME 2016 Val   (1 147)
    • CROHME 2023 Val   (  555)
    • CROHME Real Train (12 010)

  MathWriting+ (via InkML)
    • MW+ Test          (5 739, full)
    • MW+ Val           (9 336, full)
    • MW+ Symbols       (6 276, full)
    • MW+ Train         (143 106, sampled INKML_SAMPLE_N)
    • MW+ Synthetic     (85 962, sampled INKML_SAMPLE_N)

  Other datasets (original proprietary formats)
    • DeepWriting  (.json folder,  6 333 word samples)
    • IAMonDB      (.json folder, 11 242 word samples)
    • Detexify     (.sql,  210 454 samples)
    • Unipen       (.tgz,  ~79 000 character samples)

Usage (from project root):
    python scripts/benchmark_multi.py

Outputs:
    stats/benchmark_multi.json
    stats/benchmark_multi.txt
    data/inktree/<dataset_name>.inktree.jsonl.gz   (for each split)
"""

import gzip
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datasets.crohme import CrohmeFileManager
from datasets.mathwriting import MathWritingFileManager
from datasets.json_loader import load_json_dataset, get_json_files
from datasets.detexify_loader import load_detexify, count_detexify
from datasets.unipen_loader import load_unipen
from ink.graph import get_relation_graphs_from_files
from inktree import save_inktree, load_inktree_graphs

# ── Config ──────────────────────────────────────────────────────────────────

STATS_DIR    = ROOT / "stats"
INKTREE_DIR  = ROOT / "data" / "inktree"

INKML_SAMPLE_N  = 2_000   # cap for very large InkML splits
ORIG_SAMPLE_N   = 5_000   # cap for very large original-format datasets

RANDOM_SEED = 42

for d in [STATS_DIR, INKTREE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

random.seed(RANDOM_SEED)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() else 0


def _inkml_dir_size(files: list) -> int:
    return sum(os.path.getsize(f) for f in files if os.path.exists(f))


def _maybe_sample(files: list, n: int) -> tuple[list, bool]:
    if len(files) <= n:
        return files, False
    return random.sample(files, n), True


def _save_and_load_inktree(graphs, labels, inktree_out: Path) -> tuple[float, int, float, int]:
    """Save graphs as InkTree, then time a full reload. Returns (t_save, bytes, t_load, n)."""
    t0 = time.perf_counter()
    save_inktree(graphs, inktree_out, labels=labels)
    t_save = time.perf_counter() - t0
    inktree_bytes = _file_size(inktree_out)

    t0 = time.perf_counter()
    loaded = load_inktree_graphs(inktree_out)
    t_inktree = time.perf_counter() - t0
    return t_save, inktree_bytes, t_inktree, len(loaded)


def _make_labels(graphs) -> list[str]:
    labels = []
    for g in graphs:
        try:
            labels.append(g.latex())
        except Exception:
            labels.append("")
    return labels


# ── InkML benchmark (CROHME / MathWriting+) ──────────────────────────────────

def benchmark_inkml_dataset(
    name: str,
    files: list,
    inktree_out: Path,
    sample_n: int = None,
) -> dict:
    sampled = False
    if sample_n is not None and len(files) > sample_n:
        files, sampled = _maybe_sample(files, sample_n)

    n_files = len(files)
    print(f"\n  [{name}]  {n_files} files{' (sampled)' if sampled else ''}")

    # Parse InkML → graphs
    t0 = time.perf_counter()
    graphs = get_relation_graphs_from_files(files, keep_undefined=True, interpolate=False)
    t_source = time.perf_counter() - t0
    n = len(graphs)
    source_bytes = _inkml_dir_size(files)

    print(f"    InkML  parse: {t_source:.3f}s  ({t_source/max(n,1)*1000:.3f} ms/sample)  "
          f"{source_bytes/1e6:.2f} MB")

    if n == 0:
        print(f"    WARNING: no graphs parsed for {name}")
        return {"name": name, "n_files": n_files, "n_graphs": 0, "error": "no graphs"}

    # Save + load InkTree
    t_save, inktree_bytes, t_inktree, _ = _save_and_load_inktree(
        graphs, _make_labels(graphs), inktree_out
    )
    print(f"    InkTree save: {t_save:.3f}s  {inktree_bytes/1e6:.2f} MB")
    print(f"    InkTree load: {t_inktree:.3f}s  ({t_inktree/n*1000:.3f} ms/sample)")

    return {
        "name": name,
        "source": "inkml",
        "sampled": sampled,
        "sample_n": sample_n if sampled else None,
        "n_files": n_files,
        "n_graphs": n,
        "source_format": {
            "format": "InkML",
            "total_bytes": source_bytes,
            "mb": round(source_bytes / 1e6, 4),
            "kb_per_sample": round(source_bytes / n / 1000, 4),
            "load_time_s": round(t_source, 4),
            "ms_per_sample": round(t_source / n * 1000, 4),
        },
        "inktree_gz": {
            "total_bytes": inktree_bytes,
            "mb": round(inktree_bytes / 1e6, 4),
            "kb_per_sample": round(inktree_bytes / n / 1000, 4),
            "load_time_s": round(t_inktree, 4),
            "ms_per_sample": round(t_inktree / n * 1000, 4),
            "speedup": round(t_source / max(t_inktree, 1e-9), 3),
            "size_ratio": round(inktree_bytes / max(source_bytes, 1), 4),
        },
    }


# ── Original-format benchmark (DeepWriting / IAMonDo / Detexify / Unipen) ────

def benchmark_original_dataset(
    name: str,
    format_label: str,
    source_bytes: int,
    loader_fn,           # callable() → list[RelationNode]
    inktree_out: Path,
    n_total: int = None,
    sample_n: int = None,
) -> dict:
    """
    Benchmark a dataset whose original format is loaded by loader_fn().

    source_bytes  – size of the raw source file(s) on disk
    n_total       – total sample count if known (for sampling annotation)
    sample_n      – if not None and n_total > sample_n, we pass sample_n to loader
    """
    sampled = sample_n is not None and n_total is not None and n_total > sample_n
    load_arg = sample_n if sampled else None

    print(f"\n  [{name}]  {format_label} source  "
          f"{source_bytes/1e6:.1f} MB"
          + (f"  → sampling {load_arg}" if sampled else ""))

    # Load original format
    t0 = time.perf_counter()
    graphs = loader_fn(load_arg) if load_arg is not None else loader_fn()
    t_source = time.perf_counter() - t0
    n = len(graphs)

    if n == 0:
        print(f"    WARNING: no graphs loaded for {name}")
        return {"name": name, "source": "original", "n_graphs": 0, "error": "no graphs"}

    # Scale reported bytes proportionally when sampled
    if sampled and n_total and n_total > 0:
        source_bytes_rep = int(source_bytes * n / n_total)
    else:
        source_bytes_rep = source_bytes

    print(f"    {format_label} load: {t_source:.3f}s  "
          f"({t_source/n*1000:.3f} ms/sample)  {source_bytes_rep/1e6:.2f} MB")

    # Save + load InkTree
    t_save, inktree_bytes, t_inktree, _ = _save_and_load_inktree(
        graphs, _make_labels(graphs), inktree_out
    )
    print(f"    InkTree  save: {t_save:.3f}s  {inktree_bytes/1e6:.2f} MB")
    print(f"    InkTree  load: {t_inktree:.3f}s  ({t_inktree/n*1000:.3f} ms/sample)")

    return {
        "name": name,
        "source": "original",
        "source_format_label": format_label,
        "sampled": sampled,
        "sample_n": load_arg if sampled else None,
        "n_total": n_total,
        "n_graphs": n,
        "source_format": {
            "format": format_label,
            "total_bytes_full": source_bytes,
            "total_bytes_rep": source_bytes_rep,
            "mb_full": round(source_bytes / 1e6, 4),
            "mb_rep": round(source_bytes_rep / 1e6, 4),
            "kb_per_sample": round(source_bytes / (n_total or n) / 1000, 4),
            "load_time_s": round(t_source, 4),
            "ms_per_sample": round(t_source / n * 1000, 4),
        },
        "inktree_gz": {
            "total_bytes": inktree_bytes,
            "mb": round(inktree_bytes / 1e6, 4),
            "kb_per_sample": round(inktree_bytes / n / 1000, 4),
            "load_time_s": round(t_inktree, 4),
            "ms_per_sample": round(t_inktree / n * 1000, 4),
            "speedup": round(t_source / max(t_inktree, 1e-9), 3),
            "size_ratio": round(inktree_bytes / max(source_bytes_rep, 1), 4),
        },
    }


# ── Main ─────────────────────────────────────────────────────────────────────

results = []

print("=" * 70)
print("InkTree Multi-Dataset Benchmark")
print("=" * 70)

# ── Section A: InkML-based CROHME datasets ───────────────────────────────────

print("\n\n[A] CROHME – InkML source")
print("-" * 50)


def _get_crohme_2023val_files():
    from datasets.crohme import InkML_path
    val_dir = os.path.join(InkML_path, "val", "CROHME2023_val")
    return [os.path.join(val_dir, f) for f in os.listdir(val_dir)
            if f.endswith(".inkml")]


def _get_crohmeplus_synthetic_files():
    """Combined CROHME+ synthetic splits (gen_LaTeX_2019, gen_LaTeX_2023, gen_syntactic)."""
    base = ROOT / "data" / "CROHME+"
    files = []
    for d in ["gen_LaTeX_data_CROHME_2019",
              "gen_LaTeX_data_CROHME_2023_corpus",
              "gen_syntactic_data"]:
        path = base / d
        if path.is_dir():
            files += [str(p) for p in path.rglob("*.inkml")]
    return files


crohme_inkml_datasets = [
    ("CROHME 2023 Test",   CrohmeFileManager.get_2023test_files,   "crohme_2023test",       None),
    ("CROHME 2019 Test",   CrohmeFileManager.get_2019test_files,   "crohme_2019test",       None),
    ("CROHME 2016 Val",    CrohmeFileManager.get_2016test_files,   "crohme_2016val",        None),
    ("CROHME 2023 Val",    _get_crohme_2023val_files,              "crohme_2023val",        None),
    ("CROHME Real Train",  CrohmeFileManager.get_real_train_files, "crohme_real_train",     None),
    ("CROHME+ Synth.",     _get_crohmeplus_synthetic_files,        "crohmeplus_synthetic",  INKML_SAMPLE_N),
]

for label, file_fn, slug, cap in crohme_inkml_datasets:
    try:
        files = file_fn()
        r = benchmark_inkml_dataset(label, files, INKTREE_DIR / f"{slug}.inktree.jsonl.gz",
                                    sample_n=cap)
        results.append(r)
    except Exception as e:
        print(f"  ERROR {label}: {e}")
        results.append({"name": label, "error": str(e)})

# ── Section B: MathWriting+ – InkML source ──────────────────────────────────

print("\n\n[B] MathWriting+ – InkML source")
print("-" * 50)

mw_inkml_datasets = [
    ("MW+ Test",      MathWritingFileManager.get_test_files,     "mwplus_test",      None),
    ("MW+ Val",       MathWritingFileManager.get_val_files,       "mwplus_val",       None),
    ("MW+ Symbols",   MathWritingFileManager.get_symbol_files,    "mwplus_symbols",   None),
    ("MW+ Train",     MathWritingFileManager.get_train_files,     "mwplus_train",     INKML_SAMPLE_N),
    ("MW+ Synthetic", MathWritingFileManager.get_synthetic_files, "mwplus_synthetic", INKML_SAMPLE_N),
]

for label, file_fn, slug, cap in mw_inkml_datasets:
    try:
        files = file_fn()
        r = benchmark_inkml_dataset(label, files,
                                    INKTREE_DIR / f"{slug}.inktree.jsonl.gz",
                                    sample_n=cap)
        results.append(r)
    except Exception as e:
        print(f"  ERROR {label}: {e}")
        results.append({"name": label, "error": str(e)})

# ── Section C: Original-format datasets ──────────────────────────────────────

print("\n\n[C] Other datasets – original source formats")
print("-" * 50)

# DeepWriting (JSON folder hierarchy)
try:
    dw_root = ROOT / "data" / "Deepwriting Dataset"
    dw_json_files = get_json_files(dw_root)
    dw_bytes = sum(f.stat().st_size for f in dw_json_files)

    def _load_deepwriting():
        return load_json_dataset(dw_root)

    r = benchmark_original_dataset(
        "DeepWriting", ".json",
        source_bytes=dw_bytes,
        loader_fn=_load_deepwriting,
        inktree_out=INKTREE_DIR / "deepwriting.inktree.jsonl.gz",
        n_total=None,
        sample_n=None,
    )
    results.append(r)
except Exception as e:
    print(f"  ERROR DeepWriting: {e}")
    results.append({"name": "DeepWriting", "error": str(e)})

# IAMonDB (JSON folder hierarchy)
try:
    iam_root = ROOT / "data" / "Iamondb Dataset"
    iam_json_files = get_json_files(iam_root)
    iam_bytes = sum(f.stat().st_size for f in iam_json_files)

    def _load_iamondb():
        return load_json_dataset(iam_root)

    r = benchmark_original_dataset(
        "IAMonDB", ".json",
        source_bytes=iam_bytes,
        loader_fn=_load_iamondb,
        inktree_out=INKTREE_DIR / "iamondb.inktree.jsonl.gz",
        n_total=None,
        sample_n=None,
    )
    results.append(r)
except Exception as e:
    print(f"  ERROR IAMonDB: {e}")
    results.append({"name": "IAMonDB", "error": str(e)})

# Detexify (.sql)
try:
    sql_path = ROOT / "data" / "detexify.sql"
    sql_bytes = sql_path.stat().st_size
    n_detexify = count_detexify()

    r = benchmark_original_dataset(
        "Detexify", ".sql",
        source_bytes=sql_bytes,
        loader_fn=load_detexify,
        inktree_out=INKTREE_DIR / "detexify.inktree.jsonl.gz",
        n_total=n_detexify,
        sample_n=None,   # load ALL 210 K samples
    )
    results.append(r)
except Exception as e:
    print(f"  ERROR Detexify: {e}")
    results.append({"name": "Detexify", "error": str(e)})

# Unipen (.tgz)
try:
    tgz_path = ROOT / "data" / "unipen-CDROM-train_r01_v07.tgz"
    tgz_bytes = tgz_path.stat().st_size

    r = benchmark_original_dataset(
        "Unipen", ".tgz",
        source_bytes=tgz_bytes,
        loader_fn=load_unipen,
        inktree_out=INKTREE_DIR / "unipen.inktree.jsonl.gz",
        n_total=None,    # exact count comes from the loader
        sample_n=None,   # load ALL samples (streaming loader, no seek penalty)
    )
    results.append(r)
except Exception as e:
    print(f"  ERROR Unipen: {e}")
    results.append({"name": "Unipen", "error": str(e)})


# ── Save JSON ─────────────────────────────────────────────────────────────────

out_json = STATS_DIR / "benchmark_multi.json"
with open(out_json, "w") as f:
    json.dump(results, f, indent=2)
print(f"\n\nSaved → {out_json}")

# ── Print summary table ───────────────────────────────────────────────────────

lines = []
lines.append("\nInkTree Multi-Dataset Benchmark – Summary")
lines.append("=" * 95)

# InkML-based datasets
lines.append("\n[A+B] InkML-based datasets (CROHME + MathWriting+)\n")
lines.append(f"{'Dataset':<22} {'N':>6}  {'Source MB':>10} {'Source ms':>10}  "
             f"{'InkTree MB':>11} {'InkTree ms':>11}  {'Size×':>7} {'Speed×':>7}")
lines.append("-" * 95)

for r in results:
    if r.get("source") != "inkml" or "error" in r:
        continue
    sf = r.get("source_format", {})
    itr = r.get("inktree_gz", {})
    n = r["n_graphs"]
    tag = f"*{r['sample_n']}" if r.get("sampled") else ""
    lines.append(
        f"{r['name'] + tag:<22} {n:>6}  "
        f"{sf.get('mb', 0):>10.2f} {sf.get('ms_per_sample', 0):>10.3f}  "
        f"{itr.get('mb', 0):>11.2f} {itr.get('ms_per_sample', 0):>11.3f}  "
        f"{itr.get('size_ratio', 0):>7.3f} {itr.get('speedup', 0):>7.2f}×"
    )

# Original-format datasets
lines.append("\n[C] Other datasets (original source formats)\n")
lines.append(f"{'Dataset':<22} {'N':>6}  {'Fmt':>10} {'Source MB':>10} {'Source ms':>10}  "
             f"{'InkTree MB':>11} {'InkTree ms':>11}  {'Size×':>7} {'Speed×':>7}")
lines.append("-" * 95)

for r in results:
    if r.get("source") != "original" or "error" in r:
        continue
    sf = r.get("source_format", {})
    itr = r.get("inktree_gz", {})
    n = r["n_graphs"]
    tag = f"*{r['sample_n']}" if r.get("sampled") else ""
    lines.append(
        f"{r['name'] + tag:<22} {n:>6}  "
        f"{sf.get('format','')[:10]:>10} {sf.get('mb_rep', sf.get('mb_full',0)):>10.2f} "
        f"{sf.get('ms_per_sample', 0):>10.3f}  "
        f"{itr.get('mb', 0):>11.2f} {itr.get('ms_per_sample', 0):>11.3f}  "
        f"{itr.get('size_ratio', 0):>7.3f} {itr.get('speedup', 0):>7.2f}×"
    )

lines.append("\n* = sampled from larger split")
lines.append("Size× = InkTree size / source size (lower is better)")
lines.append("Speed× = source load time / InkTree load time (higher is better)")

table_str = "\n".join(lines)
print(table_str)

out_txt = STATS_DIR / "benchmark_multi.txt"
with open(out_txt, "w") as f:
    f.write(table_str)
print(f"\nTable → {out_txt}")
