"""
I/O helpers for reading and writing InkTree files (.inktree.jsonl.gz).

File format: gzip-compressed JSONL, one JSON object per line.
Each line is a full InkTree sample (version + label + node tree).
"""

import gzip
import json
from pathlib import Path
from typing import List, Tuple

from ink.nodes.relation_node import RelationNode

from .schema import INKTREE_VERSION
from .encode import encode_graph_sample
from .decode import decode_graph_sample

INKTREE_SUFFIX = ".inktree.jsonl.gz"


def save_inktree(
    graphs: List[RelationNode],
    out_path: Path,
    labels: List[str] = None,
) -> Path:
    """
    Save a list of RelationNode graphs to an InkTree JSONL.gz file.

    Parameters
    ----------
    graphs:   List of root RelationNode objects.
    out_path: Output file path (should end with .inktree.jsonl.gz).
    labels:   Optional list of LaTeX ground-truth labels (same length as graphs).

    Returns
    -------
    The actual path written.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if labels is None:
        labels = [""] * len(graphs)

    with gzip.open(out_path, "wt", encoding="utf-8") as fh:
        for graph, label in zip(graphs, labels):
            sample = encode_graph_sample(graph, label=label)
            fh.write(json.dumps(sample, separators=(",", ":")))
            fh.write("\n")

    return out_path


def load_inktree(path: Path) -> List[Tuple[RelationNode, str]]:
    """
    Load an InkTree JSONL.gz file.

    Returns
    -------
    List of (root_node, label) tuples.
    """
    path = Path(path)
    results = []
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            sample = json.loads(line)
            root, label = decode_graph_sample(sample)
            results.append((root, label))
    return results


def load_inktree_graphs(path: Path) -> List[RelationNode]:
    """Convenience wrapper: load only the RelationNode graphs (discard labels)."""
    return [g for g, _ in load_inktree(path)]
