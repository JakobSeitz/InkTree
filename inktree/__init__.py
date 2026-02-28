"""
InkTree – a lightweight, ML-oriented representation for structured online handwriting.

Unifies digital ink, structural nodes, and spatial relations in a single
self-describing hierarchical format. Designed for handwritten mathematics
with relation-graph annotations (CROHME, MathWriting, etc.).

Key design goals vs. InkML + JSONL:
- No ID-based cross-references (strokes embedded directly in structural nodes)
- Semantic child keys (numer/denom, base/sub/sup) instead of positional arrays
- Short, readable type identifiers
- Compact float representation (4 decimal places)
- Optional timestamp field (omitted when absent)
- Top-level LaTeX ground-truth label
"""

from .encode import encode_graph, encode_graph_sample
from .decode import decode_graph, decode_graph_sample
from .io import load_inktree, load_inktree_graphs, save_inktree, INKTREE_VERSION

__all__ = [
    "encode_graph",
    "encode_graph_sample",
    "decode_graph",
    "decode_graph_sample",
    "load_inktree",
    "load_inktree_graphs",
    "save_inktree",
    "INKTREE_VERSION",
]
