"""
Decode an InkTree dict back into a RelationNode graph.

This is the inverse of encode.py and reconstructs the full object graph
using the same node classes as the recognition pipeline.
"""

from ink.nodes.relation_node import RelationNode
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.row_node import RowNode
from ink.nodes.frac_node import FracNode
from ink.nodes.sub_node import SubNode
from ink.nodes.sup_node import SupNode
from ink.nodes.sub_sup_node import SubSupNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.root_node import RootNode
from ink.nodes.under_node import UnderNode
from ink.nodes.under_over_node import UnderOverNode
from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.noisy_node import NoisyNode
from ink.nodes.lines_node import LineNode
from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup


def _decode_stroke(d: dict) -> Trace:
    t = d.get("t")
    return Trace(x=d["x"], y=d["y"], t=t)


def _decode_node(d: dict, parent=None) -> RelationNode:
    if d is None:
        return None

    node_type = d.get("type", "any")

    if node_type == "sym":
        tg = TraceGroup(
            traces=[_decode_stroke(s) for s in d.get("strokes", [])],
            label=d.get("label", ""),
        )
        return SymbolNode(parent=parent, trace_group=tg)

    if node_type == "frac":
        bar_strokes = [_decode_stroke(s) for s in d.get("bar", [])]
        tg = TraceGroup(traces=bar_strokes, label="-")
        node = FracNode(parent=parent, trace_group=tg)
        numer = _decode_node(d.get("numer"), parent=node)
        denom = _decode_node(d.get("denom"), parent=node)
        node.children = [numer, denom]
        return node

    if node_type == "sub":
        node = SubNode(parent=parent)
        base = _decode_node(d.get("base"), parent=node)
        sub  = _decode_node(d.get("sub"),  parent=node)
        node.children = [base, sub]
        return node

    if node_type == "sup":
        node = SupNode(parent=parent)
        base = _decode_node(d.get("base"), parent=node)
        sup  = _decode_node(d.get("sup"),  parent=node)
        node.children = [base, sup]
        return node

    if node_type == "subsup":
        node = SubSupNode(parent=parent)
        base = _decode_node(d.get("base"), parent=node)
        sub  = _decode_node(d.get("sub"),  parent=node)
        sup  = _decode_node(d.get("sup"),  parent=node)
        node.children = [base, sub, sup]
        return node

    if node_type == "sqrt":
        sqrt_strokes = [_decode_stroke(s) for s in d.get("strokes", [])]
        tg = TraceGroup(traces=sqrt_strokes, label="\\sqrt")
        node = SqrtNode(parent=parent, trace_group=tg)
        inner = _decode_node(d.get("inner"), parent=node)
        node.children = [inner]
        return node

    if node_type == "root":
        root_strokes = [_decode_stroke(s) for s in d.get("strokes", [])]
        tg = TraceGroup(traces=root_strokes, label="\\sqrt")
        node = RootNode(parent=parent, trace_group=tg)
        inner = _decode_node(d.get("inner"), parent=node)
        index = _decode_node(d.get("index"), parent=node)
        node.children = [inner, index]
        return node

    if node_type == "under":
        node = UnderNode(parent=parent)
        base  = _decode_node(d.get("base"),  parent=node)
        under = _decode_node(d.get("under"), parent=node)
        node.children = [base, under]
        return node

    if node_type == "underover":
        node = UnderOverNode(parent=parent)
        base  = _decode_node(d.get("base"),  parent=node)
        under = _decode_node(d.get("under"), parent=node)
        over  = _decode_node(d.get("over"),  parent=node)
        node.children = [base, under, over]
        return node

    if node_type == "row":
        node = RowNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in d.get("children", [])]
        return node

    if node_type == "noisy":
        node = NoisyNode(parent=parent)
        node.children = [_decode_node(c, parent=node) for c in d.get("children", [])]
        return node

    if node_type == "line":
        return LineNode(parent=parent)

    # fallback: any / unknown
    node = AnyRelationNode(parent=parent)
    node.children = [_decode_node(c, parent=node) for c in d.get("children", [])]
    return node


def decode_graph(node_dict: dict) -> RelationNode:
    """Decode an InkTree node dict into a RelationNode (without sample wrapper)."""
    return _decode_node(node_dict)


def decode_graph_sample(sample: dict) -> tuple:
    """Decode a full InkTree sample. Returns (root_node, label)."""
    label = sample.get("label", "")
    root = _decode_node(sample.get("node"))
    return root, label
