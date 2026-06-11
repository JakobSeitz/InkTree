import xml.etree.cElementTree as ET

from ink.nodes.relation_node import RelationNode


class MatrixNode(RelationNode):
    """Rectangular grid of cell nodes (matrix / tabular layout region).

    Cells are stored row-major in `children`; `n_cols` defines the grid shape.
    Grid position is implied by structure (children[i * n_cols + j] = cell (i, j)),
    so no ID-based cell relations are needed. Delimiters (parentheses, brackets)
    are not part of the matrix itself; they are sibling symbol nodes in the
    surrounding row, matching how they appear in the ink.
    """

    def __init__(self, n_cols: int, children=None, parent=None):
        super().__init__(parent=parent, children=children)
        self.n_cols = n_cols

    def rows(self):
        """Return cells as a list of rows (each a list of nodes)."""
        return [self.children[i:i + self.n_cols] for i in range(0, len(self.children), self.n_cols)]

    def get_sup(self, child=None):
        return None

    def get_sub(self, child=None):
        return None

    def get_above(self, child=None):
        return None

    def get_below(self, child=None):
        return None

    def copy(self, parent=None):
        return MatrixNode(
            n_cols=self.n_cols,
            parent=parent,
            children=[c.copy(parent=self) if c is not None else None for c in self.children],
        )

    def as_pretty_formula(self):
        return "[" + "; ".join(
            ", ".join(c.as_pretty_formula() for c in row if c is not None) for row in self.rows()
        ) + "]"

    def latex(self):
        body = " \\\\ ".join(
            " & ".join(c.latex() if c is not None else "" for c in row) for row in self.rows()
        )
        return f"\\begin{{matrix}} {body} \\end{{matrix}}"

    def get_math_ml(self):
        mtable = ET.Element("mtable")
        for row in self.rows():
            mtr = ET.SubElement(mtable, "mtr")
            for cell in row:
                mtd = ET.SubElement(mtr, "mtd")
                if cell is not None:
                    mtd.append(cell.get_math_ml())
        return mtable
