from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.placeholder_node import PlaceholderNode
from ink.nodes.relation_node import RelationNode
from ink.nodes.sub_node import beautified_subs
from ink.nodes.sup_node import beautified_sups
from ink.nodes.symbol_node import SymbolNode
from ink.traces.trace_group import TraceGroup
import xml.etree.cElementTree as ET

beautified_frac_symbol = "⁄"


class FracNode(RelationNode):
    def __init__(self, trace_group: TraceGroup, parent=None, children=None):
        super().__init__(parent=parent, trace_group=trace_group, children=children)

    def add_child(self, child):
        if len(self.children) < 2:
            super().add_child(child)
        else:
            raise ValueError("FracNode can only have two children")

    def remove_node(self, node):
        for i, c in enumerate(self.children):
            if c is None or c is node or c.is_empty():
                self.children[i] = None
        for c in self.children:
            if c is not None:
                c.remove_node(node)

    def is_empty(self):
        return False

    def get_right(self, child_node=None):
        if child_node is None and self.parent is not None:
            return self.parent.get_right(self)
        return None

    def get_left(self, child_node=None):
        if child_node is None and self.parent is not None:
            return self.parent.get_left(self)
        return None

    def get_row_root(self, child=None):
        return super().get_row_root(self) if child is None else child

    def get_base(self):
        return SymbolNode(trace_group=self.trace_group)

    def get_above(self, child=None):
        return self.children[0] if child is None else None

    def get_below(self, child=None):
        return self.children[1] if child is None else None

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None and child is None else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None and child is None else None

    def copy(self, parent=None):
        return FracNode(
            trace_group=self.trace_group.copy(),
            parent=parent,
            children=[c.copy(parent=self) if c is not None else None for c in self.children],
        )

    def as_pretty_formula(self):
        numer = self.get_above().as_pretty_formula()
        denom = self.get_below().as_pretty_formula()
        if len(numer) > 1:
            numer = "{" + numer + "}"
        if len(denom) > 1:
            denom = "{" + denom + "}"
        if len(numer) == 1 and len(denom) == 1:
            if numer in beautified_sups and denom in beautified_subs:
                return beautified_sups[numer] + beautified_frac_symbol + beautified_subs[denom]
        return f"{numer}/{denom}"

    def latex(self):
        above = self.get_above()
        below = self.get_below()
        above_missing = above is None or isinstance(above, AnyRelationNode)
        below_missing = below is None or isinstance(below, AnyRelationNode)
        above_latex = None if above_missing else above.latex()
        below_latex = None if below_missing else below.latex()
        if above_missing and not below_missing:
            return f"\\overline{{{below_latex}}}"
        if below_missing and not above_missing:
            return f"\\underline{{{above_latex}}}"
        if above_missing and below_missing:
            return "-"
        return f"\\frac{{{above_latex}}}{{{below_latex}}}"

    def get_math_ml(self):
        attrib = {}
        if self.trace_group is not None and self.trace_group.math_annotation is not None:
            attrib["xml:id"] = str(self.trace_group.math_annotation)
        mfrac = ET.Element("mfrac", attrib=attrib)
        for c in self.children:
            mfrac.append(c.get_math_ml())
        return mfrac

    def fill_placeholders(self):
        if len(self.children) < 2:
            self.children += [None] * (2 - len(self.children))
        for i in range(2):
            if self.children[i] is None:
                self.children[i] = PlaceholderNode(parent=self)
