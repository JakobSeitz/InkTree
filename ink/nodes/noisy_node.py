"""
NoisyNode wraps a clean formula graph alongside stray stroke symbols (noise).
"""

from ink.nodes.relation_node import RelationNode
from ink.nodes.symbol_node import SymbolNode


class NoisyNode(RelationNode):
    def __init__(self, base_relation: RelationNode, noise_nodes: list[SymbolNode], parent=None):
        super().__init__(parent=parent, trace_group=None,
                         children=[base_relation] + noise_nodes)
        self.base_relation = base_relation
        self.noise_nodes = noise_nodes

    def latex(self):
        return self.base_relation.latex()

    def as_pretty_formula(self):
        return f"{self.base_relation.as_pretty_formula()} + noise[{len(self.noise_nodes)}]"

    def get_all_trace_groups(self):
        result = self.base_relation.get_all_trace_groups()
        for n in self.noise_nodes:
            result += n.get_all_trace_groups()
        return result

    def get_base(self):
        return self.base_relation

    def copy(self, parent=None):
        return NoisyNode(
            base_relation=self.base_relation.copy(parent=self),
            noise_nodes=[n.copy(parent=self) for n in self.noise_nodes],
            parent=parent,
        )

    def replace_child(self, old_child, new_child):
        super().replace_child(old_child, new_child)
        if old_child is self.base_relation:
            self.base_relation = new_child
        self.noise_nodes = [c for c in self.children[1:] if isinstance(c, SymbolNode)]

    def remove_node(self, node):
        if node in self.noise_nodes:
            self.noise_nodes = [n for n in self.noise_nodes if n is not node]
            self.set_children(([self.base_relation] if self.base_relation else []) + self.noise_nodes)
            if self.parent and not self.children:
                self.parent.remove_node(self)
            return
        if node is self.base_relation:
            if self.parent:
                self.parent.remove_node(self)
            else:
                self.set_children([])
            return
        if self.base_relation:
            self.base_relation.remove_node(node)
            self.noise_nodes = [n for n in self.noise_nodes if n is not None and not n.is_empty()]
            self.set_children([self.base_relation] + self.noise_nodes)
