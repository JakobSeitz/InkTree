from ink.nodes.relation_node import RelationNode
from ink.nodes.row_node import RowNode
from ink.nodes.sub_node import SubNode
from ink.nodes.sup_node import SupNode
import xml.etree.cElementTree as ET


# always 3 children
#   1. base: usually one symbol, there is one exception in validation dataset
#   2. sub
#   3. sup

class SubSupNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super(SubSupNode, self).__init__(parent=parent, children=children)

    def add_child(self, child):
        if len(self.children) < 3:
            super(SubSupNode, self).add_child(child)

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
                self.replace_with_node(SubNode(parent=self.parent, children=[self.children[0], self.children[1]]))

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

    def get_local_sup(self):
        return self.children[2]

    def get_local_sub(self):
        return self.children[1]

    def get_sup(self, child=None):
        if child is self.get_local_sup():
            return self.parent.get_sup(self) if self.parent is not None else None
        if child is self.get_local_sub():
            return None

        local_sup = self.get_local_sup()
        if self.parent is None:
            return local_sup
        parent_sup = self.parent.get_sup(self)
        if parent_sup is None:
            return local_sup
        else:
            return SupNode(parent=None, children=[local_sup, parent_sup])

    def get_sub(self, child=None):
        if child is self.get_local_sub():
            return self.parent.get_sub(self) if self.parent is not None else None
        if child is self.get_local_sup():
            return None

        local_sub = self.get_local_sub()

        if self.parent is None:
            return local_sub
        parent_sub = self.parent.get_sub(self)
        if parent_sub is None:
            return local_sub
        else:
            return SubNode(parent=None, children=[local_sub, parent_sub])

    def copy(self, parent=None):
        return SubSupNode(parent=parent, children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        base = self.get_base().as_pretty_formula()
        sub = self.get_local_sub()
        sub_text = sub.as_pretty_formula()
        sup = self.get_local_sup()
        sup_text = sup.as_pretty_formula()
        if len(sub.get_all_trace_groups()) > 1:
            sub_text = "{" + sub_text + "}"
        if len(sup.get_all_trace_groups()) > 1:
            sup_text = "{" + sup_text + "}"
        return f"{base}_{sub_text}^{sup_text}"

    def latex(self):
        return SupNode(children=[SubNode(children=[self.get_base(), self.get_local_sub()]), self.get_local_sup()]).latex()

    def fix(self):
        for child in self.children:
            child.fix()
        # note: sometimes sub sup is wrong ordered
        sub_child = self.children[1]
        sup_child = self.children[2]
        child1_tgs = sub_child.get_all_trace_groups()
        child2_tgs = sup_child.get_all_trace_groups()
        avg_sub_child = sum([tg.get_center()[1] for tg in child1_tgs]) / len(child1_tgs)
        avg_sup_child = sum([tg.get_center()[1] for tg in child2_tgs]) / len(child2_tgs)
        if avg_sub_child < avg_sup_child:  # sub is above sup
            self.children[1] = sup_child  # sub
            self.children[2] = sub_child  # sup
        if isinstance(self.get_base(), RowNode):
            child_with_sub_sup = self.get_base().get_rightmost_node()
            other_children = [child for child in self.get_base().children if child != child_with_sub_sup]
            new_row_node = RowNode(parent=self, children=other_children + [SubSupNode(children=[child_with_sub_sup, self.get_local_sub(), self.get_local_sup()])])
            self.replace_with_node(new_row_node)

    def get_math_ml(self):
        msubsup = ET.Element("msubsup")
        for child in self.children:
            math_ml = child.get_math_ml()
            msubsup.append(math_ml)
        return msubsup
