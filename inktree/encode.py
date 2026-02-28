"""
Encode a RelationNode graph into the InkTree format (dict).

The InkTree format eliminates ID-based cross-references and uses semantic
child keys (numer/denom, base/sub/sup, etc.) instead of positional arrays.
Strokes are embedded directly inside symbol nodes with rounded coordinates.
"""

from .schema import NODE_TYPE_TO_SHORT, COORD_DECIMALS, INKTREE_VERSION


def _r(values: list) -> list:
    """Round a list of floats to COORD_DECIMALS places."""
    return [round(v, COORD_DECIMALS) for v in values]


def _encode_stroke(trace) -> dict:
    """Encode a single Trace as a compact dict without null/ID fields."""
    d = {"x": _r(trace.x), "y": _r(trace.y)}
    if trace.t is not None:
        d["t"] = trace.t
    return d


def _encode_node(node) -> dict:
    """Recursively encode a RelationNode into an InkTree dict."""
    class_name = type(node).__name__
    short = NODE_TYPE_TO_SHORT.get(class_name, "any")

    if class_name == "SymbolNode":
        tg = node.trace_group
        return {
            "type": "sym",
            "label": tg.label if tg is not None else "",
            "strokes": [_encode_stroke(t) for t in tg.traces] if tg is not None else [],
        }

    if class_name == "FracNode":
        # children[0] = numerator (above), children[1] = denominator (below)
        # trace_group holds the fraction bar stroke(s)
        ch = node.children
        d = {
            "type": "frac",
            "numer": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "denom": _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
        }
        tg = node.trace_group
        if tg is not None and tg.traces:
            d["bar"] = [_encode_stroke(t) for t in tg.traces]
        return d

    if class_name == "SubNode":
        # children[0] = base, children[1] = subscript
        ch = node.children
        return {
            "type": "sub",
            "base": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "sub":  _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
        }

    if class_name == "SupNode":
        # children[0] = base, children[1] = superscript
        ch = node.children
        return {
            "type": "sup",
            "base": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "sup":  _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
        }

    if class_name == "SubSupNode":
        # children[0] = base, children[1] = subscript, children[2] = superscript
        ch = node.children
        return {
            "type": "subsup",
            "base": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "sub":  _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
            "sup":  _encode_node(ch[2]) if len(ch) > 2 and ch[2] is not None else None,
        }

    if class_name == "SqrtNode":
        # children[0] = radicand; trace_group holds the radical symbol stroke(s)
        ch = node.children
        d = {
            "type": "sqrt",
            "inner": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
        }
        tg = node.trace_group
        if tg is not None and tg.traces:
            d["strokes"] = [_encode_stroke(t) for t in tg.traces]
        return d

    if class_name == "RootNode":
        # children[0] = inner/radicand, children[1] = index; trace_group = radical stroke(s)
        ch = node.children
        d = {
            "type": "root",
            "inner": _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "index": _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
        }
        tg = node.trace_group
        if tg is not None and tg.traces:
            d["strokes"] = [_encode_stroke(t) for t in tg.traces]
        return d

    if class_name == "UnderNode":
        # children[0] = base, children[1] = underscript
        ch = node.children
        return {
            "type": "under",
            "base":  _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "under": _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
        }

    if class_name == "UnderOverNode":
        # children[0] = base, children[1] = under, children[2] = over
        ch = node.children
        return {
            "type": "underover",
            "base":  _encode_node(ch[0]) if len(ch) > 0 and ch[0] is not None else None,
            "under": _encode_node(ch[1]) if len(ch) > 1 and ch[1] is not None else None,
            "over":  _encode_node(ch[2]) if len(ch) > 2 and ch[2] is not None else None,
        }

    # RowNode, AnyRelationNode, NoisyNode, LineNode, fallback: generic children list
    d = {"type": short}
    if node.children:
        d["children"] = [_encode_node(c) for c in node.children if c is not None]
    return d


def encode_graph(root_node) -> dict:
    """Encode a root RelationNode into an InkTree node dict (without sample wrapper)."""
    return _encode_node(root_node)


def encode_graph_sample(root_node, label: str = "") -> dict:
    """Encode a full sample: version + label + root node."""
    return {
        "version": INKTREE_VERSION,
        "label": label,
        "node": _encode_node(root_node),
    }
