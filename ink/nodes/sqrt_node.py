from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.relation_node import RelationNode
from ink.nodes.row_node import RowNode
from ink.nodes.symbol_node import SymbolNode
import xml.etree.cElementTree as ET


class SqrtNode(RelationNode):
    def __init__(self, trace_group, parent=None, children=None):
        super(SqrtNode, self).__init__(parent=parent, trace_group=trace_group, children=children)

    def add_child(self, child):
        # correct sqrts: some have two children, this is weird af use mrow as single child instead
        # => now every root has exactly one child
        if len(self.children) == 1:
            children = self.children
            self.children = []
            row_node = RowNode(parent=self, children=children + [child])
            self.children = [row_node]
        else:
            super(SqrtNode, self).add_child(child)

    def remove_node(self, node):
        self.children = [child if child is not None and child != node and not child.is_empty() else None for child in self.children]
        for child in self.children:
            if child is not None: child.remove_node(node)

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
        return SymbolNode(trace_group=self.trace_group)  # copy of parent with only this trace group

    def get_below(self, child=None):
        return self.children[0] if child is None else None

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None and child is None else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None and child is None else None

    def copy(self, parent=None):
        return SqrtNode(parent=parent,
                        trace_group=self.trace_group.copy(),
                        children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        base = self.get_below().as_pretty_formula()
        if len(self.get_below().get_all_trace_groups()) > 1:
            base = "{" + base + "}"
        return f"√{base}"

    def latex(self):
        below = self.get_below()
        below_latex = "{⠀}" if below is None or isinstance(below, AnyRelationNode) else below.latex()
        return "\\sqrt{" + below_latex + "}"

    def get_math_ml(self):
        attrib = {}
        if self.trace_group is not None and self.trace_group.math_annotation is not None:
            attrib["xml:id"] = str(self.trace_group.math_annotation)
        msqrt = ET.Element("msqrt", attrib=attrib)
        for child in self.children:
            msqrt.append(child.get_math_ml())
        return msqrt
