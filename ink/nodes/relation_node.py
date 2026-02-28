from ink.traces.trace_group import TraceGroup


class RelationNode:
    def __init__(self, parent=None, trace_group=None, children=None):
        self.parent = parent
        self.trace_group: TraceGroup = trace_group
        self.children = []
        self.bad_labeled = False
        self.set_children(children or [])

    def __len__(self):
        return len(self.children)

    def __str__(self):
        return self.as_pretty_formula()

    # ── child management ────────────────────────────────────────────────────

    def set_children(self, children):
        self.children = []
        for child in children:
            self.add_child(child)

    def add_child(self, child):
        if child is not None:
            child.parent = self
        self.children.append(child)

    def replace_child(self, old_child, new_child):
        self.children = [new_child if c is old_child else c for c in self.children]
        if new_child is not None:
            new_child.parent = self
        self.fix()
        if old_child is not None:
            old_child.parent = None

    def replace_with_node(self, node):
        if self.parent is not None:
            self.parent.replace_child(self, node)
        else:
            self.__class__ = node.__class__
            self.trace_group = node.trace_group
            self.parent = None
            self.children = []
            self.bad_labeled = getattr(node, "bad_labeled", False)
            self.set_children(node.children)

    def remove_node(self, node):
        self.set_children([c for c in self.children if c is not node])
        for child in self.children:
            child.remove_node(node)
        self.set_children([c for c in self.children if c is not None and not c.is_empty()])
        if self.parent is not None:
            if len(self.children) == 1:
                self.replace_with_node(self.children[0])
            elif len(self.children) == 0:
                self.parent.remove_node(self)

    def is_empty(self):
        return len(self.children) == 0 or all(c is None or c.is_empty() for c in self.children)

    # ── navigation ──────────────────────────────────────────────────────────

    def get_right(self, child_node=None):
        return self.parent.get_right(self) if self.parent is not None else None

    def get_left(self, child_node=None):
        return self.parent.get_left(self) if self.parent is not None else None

    def get_row_root(self, child=None):
        return self.parent.get_row_root(self) if self.parent is not None else self

    def get_all_right(self, ref_node) -> list['RelationNode']:
        if self is ref_node:
            return [self]
        idx = next(i for i, c in enumerate(self.children) if ref_node in c.get_all_nodes())
        return self.children[idx].get_all_right(ref_node) + self.children[idx + 1:]

    def get_all_left(self, ref_node) -> list['RelationNode']:
        if self is ref_node:
            return [self]
        idx = next(i for i, c in enumerate(self.children) if ref_node in c.get_all_nodes())
        return self.children[idx].get_all_left(ref_node) + self.children[:idx]

    def get_leftmost_node(self):
        base = self.get_base()
        return self if base is None else base.get_leftmost_node()

    def get_leftmost_node2(self):
        return self

    def get_rightmost_node(self):
        return self.get_base().get_rightmost_node()

    def get_rightmost_node2(self):
        return self

    def get_base(self):
        return self

    def get_sup(self, child=None):
        return self.parent.get_sup(self) if self.parent is not None else None

    def get_sub(self, child=None):
        return self.parent.get_sub(self) if self.parent is not None else None

    def get_above(self, child=None):
        return self.parent.get_above(self) if self.parent is not None else None

    def get_below(self, child=None):
        return self.parent.get_below(self) if self.parent is not None else None

    # ── traversal ───────────────────────────────────────────────────────────

    def get_all_nodes(self) -> list['RelationNode']:
        result = [self]
        for c in self.children:
            if c is not None:
                result += c.get_all_nodes()
        return result

    def get_all_nodes_with_trace_groups(self) -> list['RelationNode']:
        result = [self] if self.trace_group is not None else []
        for c in self.children:
            if c is not None:
                result += c.get_all_nodes_with_trace_groups()
        return result

    def get_all_trace_groups(self) -> list[TraceGroup]:
        result = [self.trace_group] if self.trace_group is not None else []
        for c in self.children:
            if c is not None and isinstance(c, RelationNode):
                result += c.get_all_trace_groups()
        return result

    # ── formula representations ──────────────────────────────────────────────

    def as_pretty_formula(self):
        return f"undef: {[c.as_pretty_formula() for c in self.children]}"

    def latex(self):
        return None

    # ── graph operations ────────────────────────────────────────────────────

    def copy(self, parent=None):
        return RelationNode(
            parent=parent,
            trace_group=self.trace_group.copy() if self.trace_group is not None else None,
            children=[c.copy(parent=self) for c in self.children],
        )

    def fix(self):
        for c in self.children:
            if c is not None:
                c.fix()

    def contains_undefined_relations(self):
        return any(c.contains_undefined_relations() for c in self.children if c is not None)

    # ── MathML export ────────────────────────────────────────────────────────

    def get_math_ml(self):
        raise NotImplementedError()
