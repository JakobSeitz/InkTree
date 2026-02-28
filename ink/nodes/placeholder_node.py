from ink.nodes.relation_node import RelationNode
import xml.etree.cElementTree as ET


class PlaceholderNode(RelationNode):
    def __init__(self, trace_group=None, parent=None):
        super().__init__(trace_group=trace_group, parent=parent, children=[])

    def latex(self):
        return "{}"

    def as_pretty_formula(self):
        return "□"

    def get_base(self):
        return None

    def get_leftmost_node(self):
        return self

    def copy(self, parent=None):
        tg = self.trace_group.copy() if self.trace_group is not None else None
        return PlaceholderNode(trace_group=tg, parent=parent)

    def get_math_ml(self):
        mi = ET.Element("mi")
        mi.text = "□"
        return mi
