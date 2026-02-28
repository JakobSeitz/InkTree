"""
Load legacy JSONL.gz datasets into RelationNode graphs.

The legacy JSONL format stores each sample as a serialized RelationNode tree
using full Python class names and explicit trace_group dicts. This loader
reconstructs the live object graph from that representation.

Usage:
    from datasets.jsonl_loader import load_jsonl, count_jsonl_samples

    graphs = load_jsonl("data/jsonl/unipen.jsonl.gz")
    n = count_jsonl_samples("data/jsonl/unipen.jsonl.gz")
"""

import gzip
import json
from pathlib import Path

from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.frac_node import FracNode
from ink.nodes.lines_node import LineNode
from ink.nodes.noisy_node import NoisyNode
from ink.nodes.relation_node import RelationNode
from ink.nodes.root_node import RootNode
from ink.nodes.row_node import RowNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.sub_node import SubNode
from ink.nodes.sub_sup_node import SubSupNode
from ink.nodes.sup_node import SupNode
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.under_node import UnderNode
from ink.nodes.under_over_node import UnderOverNode
from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup


def _decode_trace(d: dict) -> Trace:
    return Trace(x=d["x"], y=d["y"], t=d.get("t"))


def _decode_trace_group(d: dict) -> TraceGroup:
    if d is None:
        return TraceGroup(traces=[], label="")
    traces = [_decode_trace(t) for t in d.get("traces", [])]
    return TraceGroup(
        traces=traces,
        label=d.get("label", ""),
        xml_id=d.get("xml_id"),
        math_annotation=d.get("math_annotation"),
    )


def _decode_node(d: dict, parent=None) -> RelationNode:
    if d is None:
        return None

    node_type = d.get("type", "AnyRelationNode")
    tg = _decode_trace_group(d.get("trace_group")) if "trace_group" in d else None
    children_dicts = d.get("children", [])

    if node_type == "SymbolNode":
        return SymbolNode(parent=parent, trace_group=tg)

    if node_type == "RowNode":
        node = RowNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "FracNode":
        node = FracNode(parent=parent, trace_group=tg or TraceGroup(traces=[], label="-"))
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "SupNode":
        node = SupNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "SubNode":
        node = SubNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "SubSupNode":
        node = SubSupNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "SqrtNode":
        node = SqrtNode(parent=parent, trace_group=tg or TraceGroup(traces=[], label="\\sqrt"))
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "RootNode":
        node = RootNode(parent=parent, trace_group=tg or TraceGroup(traces=[], label="\\sqrt"))
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "UnderNode":
        node = UnderNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "UnderOverNode":
        node = UnderOverNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "NoisyNode":
        node = NoisyNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    if node_type == "LineNode":
        node = LineNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
        return node

    # fallback: AnyRelationNode or unknown
    node = AnyRelationNode(parent=parent)
    node.children = [_decode_node(c, parent=node) for c in children_dicts if c is not None]
    return node


def load_jsonl(path, max_samples: int = None) -> list:
    """
    Load a legacy JSONL.gz file and return a list of RelationNode graphs.

    Args:
        path: Path to the .jsonl.gz file.
        max_samples: If set, load at most this many samples.

    Returns:
        List of RelationNode root objects.
    """
    path = Path(path)
    graphs = []
    opener = gzip.open if str(path).endswith(".gz") else open

    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                node = _decode_node(d)
                if node is not None:
                    graphs.append(node)
            except Exception:
                continue
            if max_samples is not None and len(graphs) >= max_samples:
                break

    return graphs


def count_jsonl_samples(path) -> int:
    """Count samples in a JSONL.gz file without fully deserializing them."""
    path = Path(path)
    count = 0
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count
