"""
Multi-run variance benchmark for InkTree paper.

Runs a representative subset of configurations N_RUNS times each to measure
run-to-run stability of the speedup ratio. Results are written to
stats/benchmark_variance.json.

Selected configurations (spanning the full speedup range):
  - CROHME 2023 Test   (InkML, mid speedup ~2.1×)
  - CROHME Real Train  (InkML, mid speedup ~1.9×)
  - MW+ Symbols        (InkML, high speedup ~9.5×)
  - DeepWriting        (.json, ~2.2×)
  - IAMonDB            (.json, ~2.2×)
  - Detexify           (.sql,  ~10.9×)  -- N_RUNS_SLOW runs due to file size
  - Unipen             (.tgz,  ~10.3×)

Usage (from project root):
    python scripts/benchmark_variance.py
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datasets.crohme import CrohmeFileManager
from datasets.mathwriting import MathWritingFileManager
from datasets.json_loader import load_json_dataset
from datasets.detexify_loader import load_detexify
from datasets.unipen_loader import load_unipen
from ink.graph import get_relation_graphs_from_files
from inktree import load_inktree_graphs

N_RUNS       = 5   # runs for fast/medium datasets
N_RUNS_SLOW  = 3   # runs for Detexify (large SQL file)

INKTREE_DIR = ROOT / "data" / "inktree"
STATS_DIR   = ROOT / "stats"


def _time_fn(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def _stats(times: list[float]) -> dict:
    import statistics
    mean = statistics.mean(times)
    std  = statistics.stdev(times) if len(times) > 1 else 0.0
    return {
        "times_s": [round(t, 4) for t in times],
        "mean_s":  round(mean, 4),
        "std_s":   round(std,  4),
        "cv_pct":  round(std / mean * 100, 2) if mean > 0 else 0.0,
    }


def run_inkml(name: str, files: list, inktree_path: Path, n_runs: int) -> dict:
    print(f"\n[{name}]  {len(files)} files  →  {n_runs} runs")
    src_times, it_times = [], []
    n = 0
    for i in range(n_runs):
        t = _time_fn(lambda: get_relation_graphs_from_files(files, keep_undefined=True, interpolate=False))
        src_times.append(t)
        graphs = get_relation_graphs_from_files(files, keep_undefined=True, interpolate=False)
        n = len(graphs)
        t = _time_fn(lambda: load_inktree_graphs(inktree_path))
        it_times.append(t)
        print(f"  run {i+1}: src={src_times[-1]:.3f}s  it={it_times[-1]:.3f}s  "
              f"speedup={src_times[-1]/it_times[-1]:.3f}×")

    speedups = [s / i for s, i in zip(src_times, it_times)]
    return {
        "name": name, "n_graphs": n,
        "source": _stats(src_times),
        "inktree": _stats(it_times),
        "speedup": {
            "values": [round(x, 3) for x in speedups],
            "mean":   round(sum(speedups) / len(speedups), 3),
            "std":    round((sum((x - sum(speedups)/len(speedups))**2 for x in speedups) / max(len(speedups)-1,1))**0.5, 3),
            "cv_pct": round((sum((x - sum(speedups)/len(speedups))**2 for x in speedups) / max(len(speedups)-1,1))**0.5 / (sum(speedups)/len(speedups)) * 100, 2),
        },
    }


def run_original(name: str, loader_fn, inktree_path: Path, n_runs: int) -> dict:
    print(f"\n[{name}]  →  {n_runs} runs")
    src_times, it_times = [], []
    n = 0
    for i in range(n_runs):
        t = _time_fn(loader_fn)
        src_times.append(t)
        graphs = loader_fn()
        n = len(graphs)
        t = _time_fn(lambda: load_inktree_graphs(inktree_path))
        it_times.append(t)
        print(f"  run {i+1}: src={src_times[-1]:.3f}s  it={it_times[-1]:.3f}s  "
              f"speedup={src_times[-1]/it_times[-1]:.3f}×")

    speedups = [s / i for s, i in zip(src_times, it_times)]
    return {
        "name": name, "n_graphs": n,
        "source": _stats(src_times),
        "inktree": _stats(it_times),
        "speedup": {
            "values": [round(x, 3) for x in speedups],
            "mean":   round(sum(speedups) / len(speedups), 3),
            "std":    round((sum((x - sum(speedups)/len(speedups))**2 for x in speedups) / max(len(speedups)-1,1))**0.5, 3),
            "cv_pct": round((sum((x - sum(speedups)/len(speedups))**2 for x in speedups) / max(len(speedups)-1,1))**0.5 / (sum(speedups)/len(speedups)) * 100, 2),
        },
    }


def main():
    results = []

    # ── InkML datasets ──────────────────────────────────────────────────────

    results.append(run_inkml(
        "CROHME 2023 Test",
        CrohmeFileManager.get_2023test_files(),
        INKTREE_DIR / "crohme_2023test.inktree.jsonl.gz",
        N_RUNS,
    ))

    results.append(run_inkml(
        "CROHME Real Train",
        CrohmeFileManager.get_real_train_files(),
        INKTREE_DIR / "crohme_real_train.inktree.jsonl.gz",
        N_RUNS,
    ))

    results.append(run_inkml(
        "MW+ Symbols",
        MathWritingFileManager.get_symbol_files(),
        INKTREE_DIR / "mwplus_symbols.inktree.jsonl.gz",
        N_RUNS,
    ))

    # ── Non-InkML datasets ───────────────────────────────────────────────────

    results.append(run_original(
        "DeepWriting",
        lambda: load_json_dataset(ROOT / "data" / "Deepwriting Dataset"),
        INKTREE_DIR / "deepwriting.inktree.jsonl.gz",
        N_RUNS,
    ))

    results.append(run_original(
        "IAMonDB",
        lambda: load_json_dataset(ROOT / "data" / "Iamondb Dataset"),
        INKTREE_DIR / "iamondb.inktree.jsonl.gz",
        N_RUNS,
    ))

    results.append(run_original(
        "Detexify",
        load_detexify,
        INKTREE_DIR / "detexify.inktree.jsonl.gz",
        N_RUNS_SLOW,
    ))

    results.append(run_original(
        "Unipen",
        load_unipen,
        INKTREE_DIR / "unipen.inktree.jsonl.gz",
        N_RUNS,
    ))

    out = STATS_DIR / "benchmark_variance.json"
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out}")

    # Summary table
    print("\n" + "="*65)
    print(f"{'Dataset':<22}  {'Speedup mean':>12}  {'±std':>6}  {'CV%':>5}")
    print("="*65)
    for r in results:
        sp = r["speedup"]
        print(f"{r['name']:<22}  {sp['mean']:>10.3f}×  {sp['std']:>6.3f}  {sp['cv_pct']:>4.1f}%")


if __name__ == "__main__":
    main()
