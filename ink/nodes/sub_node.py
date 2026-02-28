from ink.nodes.relation_node import RelationNode
from ink.nodes.symbol_node import SymbolNode
import xml.etree.cElementTree as ET

beautified_subs = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅",
    "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "-": "₋", "+": "₊", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
    "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ",
}


class SubNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super().__init__(parent=parent, children=children)

    def _to_row(self):
        from ink.nodes.row_node import RowNode
        self.replace_with_node(RowNode(parent=self.parent, children=self.children))

    def add_child(self, child):
        if len(self.children) < 2:
            super().add_child(child)
        # commas and periods are occasionally mis-labeled as subscripts
        if (len(self.children) == 2
                and self.children[1].trace_group is not None
                and self.children[1].trace_group.label in [",", "."]):
            self._to_row()

    def remove_node(self, node):
        for c in self.children:
            if c is not None:
                c.remove_node(node)
        for i, c in enumerate(self.children):
            if c is not None and (c is node or c.is_empty()):
                self.children[i] = None
        if self.children[0] is not None and self.children[1] is None:
            self.replace_with_node(self.children[0])

    def get_row_root(self, child=None):
        return super().get_row_root(self) if child is self.get_base() else child

    def get_right(self, child_node=None):
        if child_node is self.get_base() and self.parent is not None:
            return self.parent.get_right(self)
        return None

    def get_left(self, child_node=None):
        if child_node is self.get_base() and self.parent is not None:
            return self.parent.get_left(self)
        return None

    def get_leftmost_node2(self):
        return self.get_base().get_leftmost_node2()

    def get_base(self):
        return self.children[0]

    def get_local_sub(self):
        return self.children[1]

    def get_sup(self, child=None):
        if self.parent is None or child is self.get_local_sub():
            return None
        return self.parent.get_sup(self)

    def get_sub(self, child=None):
        if child is self.get_local_sub():
            return self.parent.get_sub(self) if self.parent is not None else None
        local_sub = self.get_local_sub()
        if self.parent is None:
            return local_sub
        parent_sub = self.parent.get_sub(self)
        if parent_sub is None:
            return local_sub
        if local_sub in parent_sub.get_all_nodes():
            return parent_sub
        return SubNode(parent=None, children=[local_sub, parent_sub])

    def copy(self, parent=None):
        return SubNode(parent=parent, children=[c.copy(parent=self) for c in self.children])

    def as_pretty_formula(self):
        base = self.get_base().as_pretty_formula()
        sub = self.get_local_sub().as_pretty_formula()
        if all(ch in beautified_subs for ch in sub):
            return base + "".join(beautified_subs[ch] for ch in sub)
        tgs = self.get_local_sub().get_all_trace_groups()
        if len(tgs) > 1:
            sub = "{" + sub + "}"
        return f"{base}_{sub}"

    def latex(self):
        sub = self.get_local_sub()
        sub_latex = sub.latex() if isinstance(sub, SymbolNode) else f"{{{sub.latex()}}}"
        base = self.get_base()
        if base is None:
            return f"{{⠀}}_{sub_latex}"
        base_latex = base.latex() if isinstance(base, SymbolNode) else f"{{{base.latex()}}}"
        return f"{base_latex}_{sub_latex}"

    def fix(self):
        if not self.children:
            if self.parent:
                self.parent.remove_node(self)
            return
        for c in self.children:
            if c is not None:
                c.fix()
        if len(self.children) == 1:
            self.replace_with_node(self.children[0])
            return
        if not isinstance(self.get_base(), SymbolNode):
            from ink.nodes.row_node import RowNode
            if isinstance(self.get_base(), RowNode):
                child_with_sub = self.get_base().get_rightmost_node()
                others = [c for c in self.get_base().children if c is not child_with_sub]
                new_row = RowNode(parent=self, children=others + [SubNode(children=[child_with_sub, self.get_local_sub()])])
                self.replace_with_node(new_row)

    def get_math_ml(self):
        base = self.get_base()
        if isinstance(base, SymbolNode) and base.get_label() == "\\lim":
            munder = ET.Element("munder")
            munder.append(base.get_math_ml())
            munder.append(self.get_local_sub().get_math_ml())
            return munder
        msub = ET.Element("msub")
        msub.append(base.get_math_ml())
        msub.append(self.get_local_sub().get_math_ml())
        return msub
