"""
Fallback node used when no structured relation graph could be parsed from InkML.
Filter these out with node.contains_undefined_relations().
"""

from ink.nodes.relation_node import RelationNode
import xml.etree.cElementTree as ET


class AnyRelationNode(RelationNode):
    def __init__(self, parent=None, children=None, latex=None):
        super().__init__(parent=parent, children=children)
        self.pre_defined_latex = latex

    def as_pretty_formula(self):
        if not self.children:
            return ""
        if len(self.children) == 1:
            return self.children[0].as_pretty_formula()
        prefix = f"Any [{self.pre_defined_latex}]" if self.pre_defined_latex else "Any"
        return f"{prefix}: " + " ".join(c.as_pretty_formula() for c in self.children)

    def get_all_right(self, ref_node):
        raise Exception("AnyRelationNode does not support get_all_right")

    def get_all_left(self, ref_node):
        raise Exception("AnyRelationNode does not support get_all_left")

    def get_leftmost_node(self):
        if len(self.children) == 1:
            return self.children[0].get_leftmost_node()
        return self

    def get_leftmost_node2(self):
        if len(self.children) == 1:
            return self.children[0].get_leftmost_node2()
        if not self.children:
            return None
        raise Exception("AnyRelationNode does not support get_leftmost_node2")

    def get_rightmost_node(self):
        if len(self.children) == 1:
            return self.children[0].get_rightmost_node()
        if not self.children:
            return None
        raise Exception("AnyRelationNode does not support get_rightmost_node")

    def get_base(self):
        if len(self.children) == 1:
            return self.children[0].get_base()
        if not self.children:
            return None
        raise Exception("AnyRelationNode does not support get_base")

    def copy(self, parent=None):
        return AnyRelationNode(
            parent=parent,
            children=[c.copy(parent=self) for c in self.children],
            latex=self.pre_defined_latex,
        )

    def latex(self):
        return "" if self.pre_defined_latex is None else self.pre_defined_latex.replace("$", "")

    def contains_undefined_relations(self):
        return True

    def get_math_ml(self):
        root = ET.Element("any")
        for c in self.children:
            root.append(c.get_math_ml())
        return root
