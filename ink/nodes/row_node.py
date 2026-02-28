from ink.nodes.relation_node import RelationNode
import xml.etree.cElementTree as ET

# usually len of 2 or 1, but can be more


class RowNode(RelationNode):
    def __init__(self, parent=None, children=None):
        super(RowNode, self).__init__(parent=parent, children=children)

    def get_right(self, child_node=None):
        if self.children[-1] == child_node:
            return self.parent.get_right(self) if self.parent else None
        return RowNode(children=self.children[self.children.index(child_node) + 1:])

    def get_left(self, child_node=None):
        if self.children[0] == child_node:
            return self.parent.get_left(self) if self.parent else None
        return RowNode(self.children[:self.children.index(child_node) - 1])

    def get_leftmost_node(self):
        return self.children[0].get_leftmost_node()

    def get_leftmost_node2(self):
        return self.children[0].get_leftmost_node2()

    def get_rightmost_node2(self):
        return self.children[-1].get_rightmost_node2()

    def get_rightmost_node(self):
        return self.children[-1].get_leftmost_node()

    def get_sup(self, child=None):
        if child == self.children[-1] and self.parent is not None:
            return self.parent.get_sup(self)
        return None

    def get_sub(self, child=None):
        if child == self.children[-1] and self.parent is not None:
            return self.parent.get_sub(self)
        return None

    def copy(self, parent=None):
        return RowNode(parent=parent, children=[child.copy(parent=self) for child in self.children])

    def as_pretty_formula(self):
        return "".join([child.as_pretty_formula() for child in self.children])

    def latex(self):
        tokenized = [child.latex() for child in self.children]
        index_stacks = [[] for _ in range(3)] # 0: {, 1: [, 2: (
        for i, token in enumerate(tokenized):
            if token == "\\{": index_stacks[0].append(i)
            elif token in ["[", "("]: index_stacks["{[(".index(token)].append(i)
            elif token in ["\\}", "]", ")"]:
                if token == "\\}": index_stack = index_stacks[0]
                else: index_stack = index_stacks["}])".index(token)]
                if len(index_stack) > 0:
                    opening_index = index_stack.pop()
                else:
                    continue
                if token == "\\}":
                    tokenized[opening_index] = "\\left\\{"
                    tokenized[i] = "\\right\\}"
                else:
                    tokenized[opening_index] = "\\left" + tokenized[opening_index]
                    tokenized[i] = "\\right" + tokenized[i]
        # convert s i n to \\sin, c o s to \\cos, l o g to \\log, l i m to \\lim, t a n to \\tan
        for i, token0 in enumerate(tokenized):
            if i + 2 < len(tokenized):
                token1 = tokenized[i + 1]
                token2 = tokenized[i + 2]
                if token0 == "s" and token1 == "i" and token2 == "n":
                    tokenized = tokenized[:i] + ["\\sin"] + tokenized[i + 3:]
                elif token0 == "c" and token1 == "o" and token2 == "s":
                    tokenized = tokenized[:i] + ["\\cos"] + tokenized[i + 3:]
                elif token0 == "l" and token1 == "o" and token2 == "g":
                    tokenized = tokenized[:i] + ["\\log"] + tokenized[i + 3:]
                elif token0 == "l" and token1 == "i" and token2 == "m":
                    tokenized = tokenized[:i] + ["\\lim"] + tokenized[i + 3:]
                elif token0 == "t" and token1 == "a" and token2 == "n":
                    tokenized = tokenized[:i] + ["\\tan"] + tokenized[i + 3:]
        # merge repetitive dot tokens into ellipsis operators
        def _collapse_runs(tokens, target: str, replacement: str):
            collapsed = []
            i = 0
            while i < len(tokens):
                if tokens[i] != target:
                    collapsed.append(tokens[i])
                    i += 1
                    continue
                j = i
                while j < len(tokens) and tokens[j] == target:
                    j += 1
                run = j - i
                while run >= 3:
                    collapsed.append(replacement)
                    run -= 3
                collapsed.extend([target] * run)
                i = j
            return collapsed

        tokenized = _collapse_runs(tokenized, ".", "\\ldots")
        tokenized = _collapse_runs(tokenized, "\\cdot", "\\cdots")
        return " ".join(tokenized)

    def fix(self):
        for child in self.children:
            child.fix()
        # disable stacking of row nodes (flatten)
        for child in self.children:
            if isinstance(child, RowNode):
                row_children = child.children
                i = self.children.index(child)
                self.set_children(self.children[:i] + row_children + self.children[i+1:])
        if len(self.children) == 1:
            self.replace_with_node(self.children[0])

    def get_math_ml(self):
        mrow_root = ET.Element("mrow")
        current_mrow = mrow_root
        for i, child in enumerate(self.children):
            math_ml = child.get_math_ml()
            if i == 0 or i == len(self.children) - 1:
                current_mrow.append(math_ml)
            else:
                new_mrow = ET.SubElement(current_mrow, "mrow")
                new_mrow.append(math_ml)
                current_mrow = new_mrow
        return mrow_root
