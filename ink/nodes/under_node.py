from ink.nodes.relation_node import RelationNode
from ink.nodes.sub_node import SubNode
import xml.etree.cElementTree as ET

# munder:
#   one leaf node with one/multiple stuff below
#   only works for \\sum, \\lim in examples

class UnderNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super(UnderNode, self).__init__(parent=parent, children=children)

    def add_child(self, child):
        super(UnderNode, self).add_child(child)

    def remove_node(self, node):
        for child in self.children:
            child.remove_node(node)
        for i, child in enumerate(self.children):
            if child == node or child.is_empty(): self.children[i] = None
        if self.children[0] is not None and self.children[1] is None:
            self.replace_with_node(self.children[0])

    def get_row_root(self, child=None):
        return super().get_row_root(self) if child == self.get_base() else child

    def get_right(self, child_node=None):
        if child_node == self.get_base() and self.parent is not None:
            return self.parent.get_right(self)
        return None

    def get_left(self, child_node=None):
        if child_node == self.get_base() and self.parent is not None:
            return self.parent.get_left(self)
        return None

    def get_leftmost_node2(self):
        return self.get_base().get_leftmost_node2()

    def get_base(self):
        return self.children[0]

    def get_below(self, child=None):
        return self.children[1] if child is self.get_base() else None

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None and child is self.get_base() else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None and child is self.get_base() else None

    def copy(self, parent=None):
        return UnderNode(parent=parent, children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        return f"{self.children[0].as_pretty_formula()}[{self.children[1].as_pretty_formula()}]"

    def latex(self):
        return SubNode(children=[self.get_base(), self.children[1]]).latex()

    def get_math_ml(self):
        munder = ET.Element("munder")
        for child in self.children:
            munder.append(child.get_math_ml())
        return munder
