from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.frac_node import FracNode
from ink.nodes.lines_node import LineNode
from ink.nodes.root_node import RootNode
from ink.nodes.row_node import RowNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.sub_node import SubNode
from ink.nodes.sup_node import SupNode
from ink.nodes.sub_sup_node import SubSupNode
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.under_node import UnderNode
from ink.nodes.under_over_node import UnderOverNode


def create_relation_node(type, parent=None, trace_group=None, children=None):
    match type:
        case "mrow":
            return RowNode(parent=parent, children=children)
        case "mstyle":
            return RowNode(parent=parent, children=children)
        case "msub":
            return SubNode(parent=parent, children=children)
        case "msup":
            return SupNode(parent=parent, children=children)
        case "msubsup":
            return SubSupNode(parent=parent, children=children)
        case "mn":
            return SymbolNode(parent=parent, trace_group=trace_group)
        case "mi":
            return SymbolNode(parent=parent, trace_group=trace_group)
        case "mo":
            return SymbolNode(parent=parent, trace_group=trace_group)
        case "msqrt":
            return SqrtNode(parent=parent, trace_group=trace_group, children=children)
        case "mroot":
            return RootNode(parent=parent, trace_group=trace_group, children=children)
        case "mfrac":
            return FracNode(parent=parent, trace_group=trace_group, children=children)
        case "munder":
            return UnderNode(parent=parent, children=children)
        case "munderover":
            return UnderOverNode(parent=parent, children=children)
        case "mline":
            return LineNode(parent=parent, children=children)
        case _:
            raise ValueError(f"Unknown type: {type}")

def get_undefined_node_from_trace_groups(trace_groups, latex=None):
    if len(trace_groups) == 1: return SymbolNode(trace_group=trace_groups[0])
    return AnyRelationNode(children=[SymbolNode(trace_group=trace_group) for trace_group in trace_groups], latex=latex)