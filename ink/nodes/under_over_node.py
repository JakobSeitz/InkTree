from ink.nodes.relation_node import RelationNode
from ink.nodes.sub_sup_node import SubSupNode
from ink.nodes.sup_node import SupNode
from ink.nodes.under_node import UnderNode
import xml.etree.cElementTree as ET

# munderover: always 3 children
#   1. base: always one symbol
#   2. below
#   3. above

class UnderOverNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super(UnderOverNode, self).__init__(parent=parent, children=children)

    def add_child(self, child):
        if len(self.children) < 3:
            super(UnderOverNode, self).add_child(child)

    def remove_node(self, node):
        for child in self.children:
            child.remove_node(node)
        for i, child in enumerate(self.children):
            if child == node or child.is_empty(): self.children[i] = None
        if self.children[0] is not None:
            if self.children[1] is None and self.children[2] is None:
                self.replace_with_node(self.children[0])
            elif self.children[1] is None:
                self.replace_with_node(SupNode(parent=self.parent, children=[self.children[0], self.children[2]]))
            elif self.children[2] is None:
                self.replace_with_node(UnderNode(parent=self.parent, children=[self.children[0], self.children[1]]))

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

    def get_above(self, child=None):
        return self.children[2] if child is self.get_base() else None

    def get_below(self, child=None):
        return self.children[1] if child is self.get_base() else None

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None and child is self.get_base() else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None and child is self.get_base() else None

    def copy(self, parent=None):
        return UnderOverNode(parent=parent, children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        if len(self.children) == 3:
            return f"{self.children[0].as_pretty_formula()}[{self.children[1].as_pretty_formula()}][{self.children[2].as_pretty_formula()}]"
        elif len(self.children) == 2:
            return UnderNode(parent=self.parent, children=[self.children[0], self.children[1]]).as_pretty_formula()

    def fix(self):
        for child in self.children:
            child.fix()
        if len(self.children) == 2:
            self.replace_with_node(UnderNode(parent=self.parent, children=[self.children[0], self.children[1]]))

    def latex(self):
        if len(self.children) == 2:
            return UnderNode(parent=self.parent, children=[self.children[0], self.children[1]]).latex()
        return SubSupNode(children=[self.get_base(), self.children[1], self.children[2]]).latex()

    def get_math_ml(self):
        munderover = ET.Element("munderover")
        for child in self.children:
            munderover.append(child.get_math_ml())
        return munderover
