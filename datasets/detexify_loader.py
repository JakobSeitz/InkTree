"""
Load Detexify .sql dump into RelationNode graphs.

The SQL file is an uncompressed PostgreSQL dump with a COPY block:
  COPY samples (id, key, strokes) FROM stdin;
  <id>\t<key>\t<strokes_python_literal>
  \.

Each entry is a LaTeX symbol (key) with one or more strokes, each stroke
being a list of [x, y] or [x, y, t] points.

Returns one SymbolNode per sample.
"""

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from ink.nodes.symbol_node import SymbolNode


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _parse_sql_block(sql_text: str):
    """Extract (key, strokes) pairs from the COPY block."""
    match = re.search(
        r"COPY samples\s*\([^)]*\)\s*FROM stdin;\n(.*?)\n\\\.[ \t]*\n",
        sql_text,
        re.DOTALL,
    )
    if not match:
        # Try without trailing newline
        match = re.search(
            r"COPY samples\s*\([^)]*\)\s*FROM stdin;\n(.*?)\n\\\.",
            sql_text,
            re.DOTALL,
        )
    if not match:
        raise ValueError("No valid COPY block found in SQL file.")

    rows = []
    for line in match.group(1).splitlines():
        parts = line.split('\t')
        if len(parts) != 3:
            continue
        _, key, strokes_str = parts
        try:
            strokes = ast.literal_eval(strokes_str)
            rows.append((key, strokes))
        except Exception:
            continue
    return rows


def load_detexify(max_samples: int = None) -> list[SymbolNode]:
    """Load Detexify SQL dump → list of SymbolNode."""
    sql_path = DATA_DIR / "detexify.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"detexify.sql not found: {sql_path}")

    with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
        sql_text = f.read()

    rows = _parse_sql_block(sql_text)

    nodes = []
    for key, strokes in rows:
        if max_samples is not None and len(nodes) >= max_samples:
            break
        traces = []
        for i, stroke in enumerate(strokes):
            if not stroke:
                continue
            if isinstance(stroke[0], (list, tuple)):
                pts = stroke
            else:
                pts = [stroke]
            x = [float(p[0]) for p in pts]
            y = [float(p[1]) for p in pts]
            if x:
                traces.append(Trace(x, y, inkml_id=i))
        if traces:
            tg = TraceGroup(traces=traces, label=key)
            nodes.append(SymbolNode(trace_group=tg))

    return nodes


def count_detexify() -> int:
    sql_path = DATA_DIR / "detexify.sql"
    if not sql_path.exists():
        return 0
    count = 0
    in_block = False
    with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'COPY samples' in line and 'FROM stdin' in line:
                in_block = True
                continue
            if in_block:
                if line.strip() == '\\.':
                    break
                if '\t' in line:
                    count += 1
    return count
