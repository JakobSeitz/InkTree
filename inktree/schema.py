"""
InkTree format constants and schema documentation.

Node type mapping (InkML/MathML class name → InkTree short identifier):

  SymbolNode      → "sym"
  RowNode         → "row"
  FracNode        → "frac"
  SubNode         → "sub"
  SupNode         → "sup"
  SubSupNode      → "subsup"
  SqrtNode        → "sqrt"
  RootNode        → "root"
  UnderNode       → "under"
  UnderOverNode   → "underover"
  AnyRelationNode → "any"
  NoisyNode       → "noisy"
  LineNode        → "line"

Child key semantics per node type:

  row:       {"children": [...]}
  sym:       {"label": "...", "strokes": [{"x": [...], "y": [...]}]}
  frac:      {"numer": node, "denom": node}
  sub:       {"base": node, "sub": node}
  sup:       {"base": node, "sup": node}
  subsup:    {"base": node, "sub": node, "sup": node}
  sqrt:      {"inner": node}
  root:      {"inner": node, "index": node}
  under:     {"base": node, "under": node}
  underover: {"base": node, "under": node, "over": node}
  any:       {"children": [...]}
  noisy:     {"children": [...]}
  line:      {}

Top-level sample structure:
  {
    "version": "1.0",
    "label": "<LaTeX ground truth>",
    "node": <root node object>
  }
"""

INKTREE_VERSION = "1.0"

# Node type → InkTree short identifier
NODE_TYPE_TO_SHORT = {
    "SymbolNode":      "sym",
    "RowNode":         "row",
    "FracNode":        "frac",
    "SubNode":         "sub",
    "SupNode":         "sup",
    "SubSupNode":      "subsup",
    "SqrtNode":        "sqrt",
    "RootNode":        "root",
    "UnderNode":       "under",
    "UnderOverNode":   "underover",
    "AnyRelationNode": "any",
    "NoisyNode":       "noisy",
    "LineNode":        "line",
    # fallback
    "RelationNode":    "any",
    "PlaceholderNode": "any",
}

SHORT_TO_NODE_TYPE = {v: k for k, v in NODE_TYPE_TO_SHORT.items()}

# Coordinate rounding precision
COORD_DECIMALS = 4
