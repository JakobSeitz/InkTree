from ink.nodes.any_relation_node import AnyRelationNode
from ink.nodes.placeholder_node import PlaceholderNode
from ink.nodes.relation_node import RelationNode
from ink.nodes.sqrt_node import SqrtNode
from ink.nodes.symbol_node import SymbolNode
import xml.etree.cElementTree as ET


# children:
#   1. under the root
#   2. "over" the root


class RootNode(RelationNode):
    def __init__(self, trace_group, parent=None, children=None):
        super(RootNode, self).__init__(parent=parent, trace_group=trace_group, children=children)

    def add_child(self, child):
        if len(self.children) < 2:
            super(RootNode, self).add_child(child)
        else:
            raise ValueError("Root node can only have two children")  # no occurrence found

    def remove_node(self, node):
        self.children = [child if child != node and not (child is None or child.is_empty()) else None for child in self.children]
        for child in self.children:
            if child is not None: child.remove_node(node)
        if self.children[0] is not None and self.children[1] is None:
            self.replace_with_node(SqrtNode(trace_group=self.trace_group, parent=self.parent, children=[self.children[0]]))

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

    def get_above(self, child=None):
        return self.children[1] if child is None else None

    def get_below(self, child=None):
        return self.children[0] if child is None else None

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None and child is None else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None and child is None else None

    def copy(self, parent=None):
        return RootNode(parent=parent,
                        trace_group=self.trace_group.copy(),
                        children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        base = self.get_below().as_pretty_formula()
        if len(base) > 1:
            base = "(" + base + ")"
        under = self.get_above().as_pretty_formula()
        if under == "3": return f"∛{base}"
        if under == "4": return f"∜{base}"
        return f"√[{under}]{base}"

    def latex(self):
        above = self.get_above()
        below = self.get_below()
        above_latex = "⠀" if above is None or isinstance(above, AnyRelationNode) else above.latex()
        below_latex = "⠀" if below is None or isinstance(below, AnyRelationNode) else below.latex()
        return f"\\sqrt[{above_latex}]{{{below_latex}}}"

    def get_math_ml(self):
        attrib = {}
        if self.trace_group is not None and self.trace_group.math_annotation is not None:
            attrib["xml:id"] = str(self.trace_group.math_annotation)
        mroot = ET.Element("mroot", attrib=attrib)
        for child in self.children:
            mroot.append(child.get_math_ml())
        return mroot

    def fill_placeholders(self):
        if len(self.children) < 1:
            self.children.append(None)
        if self.children[0] is None:
            self.children[0] = PlaceholderNode(parent=self)
