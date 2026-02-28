"""
Compute detailed dataset statistics for CROHME 2023 Test set.
Paper-ready numbers: graph structure, symbol distribution, format sizes.

Usage (from project root):
    python scripts/dataset_stats.py

Outputs:
    stats/crohme2023_test_stats.json
    stats/crohme2023_test_stats.txt
"""

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from datasets.crohme import CrohmeFileManager
from ink.graph import get_relation_graphs_from_files
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.noisy_node import NoisyNode

STATS_DIR = ROOT / "stats"
STATS_DIR.mkdir(parents=True, exist_ok=True)


def graph_depth(node, d=0):
    if not node.children:
        return d
    return max(graph_depth(c, d + 1) for c in node.children if c is not None)


def collect_stats(graphs):
    n_nodes_list = []
    n_symbols_list = []
    n_strokes_list = []
    depths = []
    node_types = Counter()
    symbol_labels = Counter()
    n_undefined = 0

    for g in graphs:
        all_nodes = g.get_all_nodes()
        n_nodes_list.append(len(all_nodes))

        syms = [n for n in all_nodes if isinstance(n, SymbolNode)]
        n_symbols_list.append(len(syms))

        strokes = sum(len(s.trace_group.traces) for s in syms if s.trace_group)
        n_strokes_list.append(strokes)

        depths.append(graph_depth(g))

        for n in all_nodes:
            node_types[type(n).__name__] += 1

        if any(isinstance(n, AnyRelationNode) for n in all_nodes):
            n_undefined += 1

        for s in syms:
            if s.trace_group:
                symbol_labels[s.trace_group.label] += 1

    def _stats(lst):
        lst = sorted(lst)
        n = len(lst)
        return {
            "min": lst[0],
            "max": lst[-1],
            "mean": round(sum(lst) / n, 2),
            "median": lst[n // 2],
        }

    return {
        "n_graphs": len(graphs),
        "n_undefined_relations": n_undefined,
        "nodes_per_graph": _stats(n_nodes_list),
        "symbols_per_graph": _stats(n_symbols_list),
        "strokes_per_graph": _stats(n_strokes_list),
        "graph_depth": _stats(depths),
        "node_type_counts": dict(node_types.most_common()),
        "top_30_symbols": dict(symbol_labels.most_common(30)),
        "unique_symbols": len(symbol_labels),
        "total_symbols": sum(symbol_labels.values()),
        "total_strokes": sum(n_strokes_list),
    }


def _mean(lst):
    return sum(lst) / len(lst) if lst else 0


print("Loading CROHME 2023 test graphs from InkML ...")
files = CrohmeFileManager.get_2023test_files()
graphs = get_relation_graphs_from_files(files, keep_undefined=True, interpolate=False)
print(f"Loaded {len(graphs)} graphs.")

stats = collect_stats(graphs)

# Save JSON
out_json = STATS_DIR / "crohme2023_test_stats.json"
with open(out_json, "w") as f:
    json.dump(stats, f, indent=2)

# Paper-ready text table
def _row(label, s):
    return (f"  {label:<30} min={s['min']:>4}  max={s['max']:>4}  "
            f"mean={s['mean']:>6.1f}  median={s['median']:>4}")

txt = f"""
Dataset Statistics – CROHME 2023 Test Set
==========================================

Samples          : {stats['n_graphs']}
Unique symbols   : {stats['unique_symbols']}
Total symbols    : {stats['total_symbols']}
Total strokes    : {stats['total_strokes']}
Graphs with undefined relations: {stats['n_undefined_relations']}

Graph structure (per formula):
{_row('Nodes', stats['nodes_per_graph'])}
{_row('Symbol nodes', stats['symbols_per_graph'])}
{_row('Strokes', stats['strokes_per_graph'])}
{_row('Tree depth', stats['graph_depth'])}

Node type distribution:
"""
for ntype, cnt in sorted(stats["node_type_counts"].items(), key=lambda x: -x[1]):
    pct = 100 * cnt / sum(stats["node_type_counts"].values())
    txt += f"  {ntype:<25} {cnt:>6}  ({pct:.1f}%)\n"

txt += "\nTop 30 symbols by frequency:\n"
for label, cnt in stats["top_30_symbols"].items():
    pct = 100 * cnt / stats["total_symbols"]
    txt += f"  {label:<20} {cnt:>6}  ({pct:.2f}%)\n"

print(txt)

out_txt = STATS_DIR / "crohme2023_test_stats.txt"
with open(out_txt, "w") as f:
    f.write(txt)

print(f"Stats saved → {out_json}")
print(f"Table saved → {out_txt}")
