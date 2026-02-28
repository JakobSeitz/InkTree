from ink.nodes.relation_node import RelationNode
from ink.nodes.symbol_node import SymbolNode
import xml.etree.cElementTree as ET

beautified_sups = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
    "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ",
    "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ",
    "m": "ᵐ", "n": "ⁿ", "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ",
    "t": "ᵗ", "u": "ᵘ", "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
}


class SupNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super().__init__(parent=parent, children=children)

    def add_child(self, child):
        if len(self.children) < 2:
            super().add_child(child)

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

    def get_local_sup(self):
        return self.children[1]

    def get_sub(self, child=None):
        if self.parent is None or child is self.get_local_sup():
            return None
        return self.parent.get_sub(self)

    def get_sup(self, child=None):
        if child is self.get_local_sup():
            return self.parent.get_sup(self) if self.parent is not None else None
        local_sup = self.get_local_sup()
        if self.parent is None:
            return local_sup
        parent_sup = self.parent.get_sup(self)
        if parent_sup is None:
            return local_sup
        if local_sup in parent_sup.get_all_nodes():
            return parent_sup
        return SupNode(parent=None, children=[local_sup, parent_sup])

    def copy(self, parent=None):
        return SupNode(parent=parent, children=[c.copy(parent=self) for c in self.children])

    def as_pretty_formula(self):
        base = self.get_base().as_pretty_formula()
        sup = self.get_local_sup().as_pretty_formula()
        if all(ch in beautified_sups for ch in sup):
            return base + "".join(beautified_sups[ch] for ch in sup)
        tgs = self.get_local_sup().get_all_trace_groups()
        if len(tgs) > 1:
            sup = "{" + sup + "}"
        return f"{base}^{sup}"

    def latex(self):
        sup = self.get_local_sup()
        sup_latex = sup.latex() if isinstance(sup, SymbolNode) else f"{{{sup.latex()}}}"
        base = self.get_base()
        if base is None:
            return f"{{⠀}}^{sup_latex}"
        base_latex = base.latex() if isinstance(base, SymbolNode) else f"{{{base.latex()}}}"
        return f"{base_latex}^{sup_latex}"

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
                child_with_sup = self.get_base().get_rightmost_node()
                others = [c for c in self.get_base().children if c is not child_with_sup]
                new_row = RowNode(parent=self, children=others + [SupNode(children=[child_with_sup, self.get_local_sup()])])
                self.replace_with_node(new_row)

    def get_math_ml(self):
        from ink.nodes.sub_node import SubNode
        base = self.get_base()
        if isinstance(base, SubNode):
            msubsup = ET.Element("msubsup")
            msubsup.append(base.get_base().get_math_ml())
            msubsup.append(base.get_local_sub().get_math_ml())
            msubsup.append(self.get_local_sup().get_math_ml())
            return msubsup
        msup = ET.Element("msup")
        msup.append(base.get_math_ml())
        msup.append(self.get_local_sup().get_math_ml())
        return msup
