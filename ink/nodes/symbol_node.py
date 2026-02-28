import json
import pathlib

from ink.nodes.relation_node import RelationNode
from ink.traces.trace_group import TraceGroup
import xml.etree.cElementTree as ET

# Load Unicode display names from JSON (latex → unicode char)
try:
    _map_path = pathlib.Path(__file__).with_name("latex_to_unicode.json")
    with _map_path.open(encoding="utf-8") as f:
        LATEX_TO_UNICODE = json.load(f)
except Exception:
    LATEX_TO_UNICODE = {}

# Inline overrides take priority over the JSON mapping
_inline_beautified = {
    '\\Delta': 'Δ', '\\alpha': 'α', '\\beta': 'β', '\\cos': 'cos', '\\div': '÷',
    '\\exists': '∃', '\\forall': '∀', '\\gamma': 'γ', '\\geq': '≥', '\\gt': '>',
    '\\in': '∈', '\\infty': '∞', '\\int': '∫', '\\lambda': 'λ', '\\ldots': '…',
    '\\leq': '≤', '\\lim': 'lim', '\\log': 'log', '\\lt': '<', '\\mu': 'μ',
    '\\neq': '≠', '\\phi': 'ϕ', '\\pi': 'π', '\\pm': '±', '\\prime': '′',
    '\\rightarrow': '→', '\\sigma': 'σ', '\\sin': 'sin', '\\sqrt': '√',
    '\\sum': '∑', '\\tan': 'tan', '\\theta': 'θ', '\\times': '×',
    '\\{': '{', '\\}': '}', '\\colon': ':', '\\cdot': '·', '\\%': '%',
    '\\delta': 'δ', '\\epsilon': 'ε', '\\Omega': 'Ω', '\\omega': 'ω',
    '\\partial': '∂', '\\rho': 'ρ', '\\psi': 'ψ', '\\tau': 'τ', '\\nu': 'ν',
    '\\xi': 'ξ', '\\eta': 'η', '\\Gamma': 'Γ', '\\Phi': 'Φ', '\\chi': 'χ',
    '\\zeta': 'ζ', '\\kappa': 'κ', '\\Pi': 'Π', '\\Psi': 'Ψ', '\\Lambda': 'Λ',
    '\\Theta': 'Θ', '\\Xi': 'Ξ', '\\varphi': 'φ',
    '\\Rightarrow': '⇒', '\\Leftarrow': '⇐', '\\Leftrightarrow': '⇔',
    '\\N': 'ℕ', '\\Z': 'ℤ', '\\R': 'ℝ', '\\Q': 'ℚ', '\\C': 'ℂ',
    '\\approx': '≈', '\\wedge': '∧', '\\vee': '∨',
    '\\cup': '∪', '\\cap': '∩', '\\emptyset': '∅', '\\subseteq': '⊆',
    '\\star': '★', '\\circ': '○', '\\square': '□',
}
beautified_symbols = {**LATEX_TO_UNICODE, **_inline_beautified}

# LaTeX normalisation applied at output time (display aliases → canonical form)
latex_replacements = {
    '\\gt': '>',
    '\\lt': '<',
    '\\square': '□',
    '\\D': '\\mathbb{D}', '\\R': '\\mathbb{R}', '\\N': '\\mathbb{N}',
    '\\Z': '\\mathbb{Z}', '\\Q': '\\mathbb{Q}', '\\C': '\\mathbb{C}',
    '\\W': '\\mathbb{W}', '\\L': '\\mathbb{L}',
}

_operators = {
    '!', '\\!', '+', ',', '-', '.', '/', '\\div', '\\pm', '\\times', '\\cdot', '\\colon',
    '=', '\\neq', '\\leq', '\\geq', '<', '>', '\\lt', '\\gt', '\\in', '\\prime', "'",
    '\\ldots', '\\dots', '\\equiv', '\\approx', '\\sim', '\\propto', '\\simeq',
    ':', ';', '\\neg', '\\tilde', '\\ge', '\\le',
    '\\rightarrow', '\\to', '\\Rightarrow', '\\Leftarrow', '\\Leftrightarrow',
    '\\rightleftharpoons', '\\mapsto', '\\leftrightarrow', '\\hookrightarrow',
    '\\longrightarrow', '\\iff', '\\supset', '\\subset', '\\notin', '\\cup', '\\cap',
    '\\setminus', '\\emptyset', '\\subseteq', '\\supseteq', '\\star', '\\diamondsuit',
    '\\circ', '\\square', '*', '\\wedge', '\\vee', '\\top', '\\perp', '\\vdash',
    '\\Vdash', '\\sum', '\\exists', '\\forall', '\\prod', '\\int', '\\sqrt',
    '\\sin', '\\cos', '\\tan', '\\lim', '\\log', '\\%', '‰', '?',
    '\\dagger', '\\frac', '\\gg', '\\hbar', '\\iint', '\\ll', '\\models', '\\mp',
    '\\ni', '\\odot', '\\oint', '\\ominus', '\\oplus', '\\otimes', '\\overline',
    '\\subsetneq', '\\triangleq', '\\underline', '\\vdots', '\\vec', '\\backslash',
    '\\|', '|', '\\cong', '(', '[', '\\{', ')', ']', '\\}',
}


class SymbolNode(RelationNode):
    def __init__(self, trace_group: TraceGroup, parent=None):
        super().__init__(parent=parent, trace_group=trace_group, children=[])
        # Normalise common label aliases on ingestion
        if trace_group is not None:
            if trace_group.label == "<":
                trace_group.label = "\\lt"
            elif trace_group.label == ">":
                trace_group.label = "\\gt"

    def get_base(self):
        return self

    def get_leftmost_node(self):
        return self

    def get_rightmost_node(self):
        return self

    def get_leftmost_node2(self):
        return self

    def remove_node(self, node):
        pass  # leaf node — nothing to remove

    def is_empty(self):
        return False

    def add_child(self, child):
        pass  # symbol nodes have no children

    def get_label(self):
        return self.trace_group.label if self.trace_group is not None and self.trace_group.label is not None else "None"

    def copy(self, parent=None):
        return SymbolNode(trace_group=self.trace_group.copy(), parent=parent)

    def as_pretty_formula(self):
        label = self.get_label()
        return beautified_symbols.get(label, label)

    def latex(self):
        label = self.get_label()
        return latex_replacements.get(label, label)

    def get_math_ml(self):
        label = self.get_label()
        attrib = {}
        if self.trace_group is not None and self.trace_group.math_annotation is not None:
            attrib["xml:id"] = str(self.trace_group.math_annotation)
        if label.isdigit():
            el = ET.Element("mn", attrib=attrib)
        elif label in _operators:
            el = ET.Element("mo", attrib=attrib)
        else:
            el = ET.Element("mi", attrib=attrib)
        el.text = label
        return el
