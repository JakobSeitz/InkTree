from ink.nodes.relation_node import RelationNode


class LineNode(RelationNode):
    def __init__(self, children=None, parent=None):
        super().__init__(parent=parent, children=children)

    def as_pretty_formula(self):
        return " \n ".join(c.as_pretty_formula() for c in self.children)

    def get_sup(self, child=None):
        return None

    def get_sub(self, child=None):
        return None

    def get_above(self, child=None):
        return None

    def get_below(self, child=None):
        return None

    def get_all_right(self, ref_node):
        idx = next(i for i, c in enumerate(self.children) if ref_node in c.get_all_nodes())
        return self.children[:idx] + self.children[idx].get_all_right(ref_node) + self.children[idx + 1:]

    def get_all_lines(self):
        result = []
        for c in self.children:
            if isinstance(c, LineNode):
                result += c.get_all_lines()
            else:
                result.append(c)
        return result

    def get_base(self):
        return self.get_topmost_line()

    def get_topmost_line(self):
        return self.get_all_lines()[0]

    def get_leftmost_node2(self):
        return self.get_topmost_line().get_leftmost_node2()

    def copy(self, parent=None):
        return LineNode(parent=parent, children=[c.copy(parent=self) for c in self.children])

    def latex(self):
        return "\n".join(c.latex() for c in self.children)
