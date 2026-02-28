"""
Load IAMonDo InkML files into RelationNode graphs.

IAMonDo InkML is page-level: each file contains multiple text lines / words.
We extract Word-level traceView groups and return one RowNode per word.

The trace format uses multi-channel differential encoding (X, Y, T, F) as
defined in the W3C InkML spec, section 7.  First point is absolute; subsequent
points use first-difference (') and second-difference (") notation.
"""

import re
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import xml.etree.ElementTree as ET

from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.row_node import RowNode


# ---------------------------------------------------------------------------
# Trace decoder (multi-channel differential IAMonDo format)
# ---------------------------------------------------------------------------

def _decode_trace(trace_str: str, total_channels: int = 4, x_idx: int = 0, y_idx: int = 1):
    """Decode a multi-channel differential InkML trace string → list of (x,y)."""
    tokens = re.findall(r"['\"]?-?\d+(?:\.\d+)?", trace_str.replace('\n', ' '))

    values = [0.0] * total_channels
    deltas = [0.0] * total_channels
    results = []
    ch = 0
    first = True

    for tok in tokens:
        if tok.startswith('"'):
            d2 = float(tok[1:])
            d = deltas[ch] + d2
            values[ch] += d
            deltas[ch] = d
        elif tok.startswith("'"):
            d = float(tok[1:])
            values[ch] += d
            deltas[ch] = d
        else:
            val = float(tok)
            if first:
                values[ch] = val
                deltas[ch] = 0.0
            else:
                values[ch] += val
                deltas[ch] = val

        ch += 1
        if ch == total_channels:
            ch = 0
            first = False
            results.append((values[x_idx], values[y_idx]))

    return results


# ---------------------------------------------------------------------------
# XML parser for IAMonDo page-level InkML
# ---------------------------------------------------------------------------

def _load_iamondb_file(path) -> list[RowNode]:
    """Parse one IAMonDo InkML file → list of RowNode (one per Word segment)."""
    tree = ET.parse(str(path))
    root = tree.getroot()

    # Collect all traces by id
    traces_by_id: dict[str, list[tuple[float, float]]] = {}
    XML_NS = '{http://www.w3.org/XML/1998/namespace}'
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'trace':
            tid = (elem.get(f'{XML_NS}id') or elem.get('id')
                   or elem.get('{http://www.w3.org/2003/InkML}id') or '')
            if tid and elem.text:
                pts = _decode_trace(elem.text.strip())
                if pts:
                    traces_by_id[tid] = pts

    def _extract_word_rows(node, depth=0) -> list[RowNode]:
        """Recursively walk traceView tree, emit RowNode at Word level."""
        tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
        if tag not in ('traceView', 'ink'):
            return []

        # Determine annotation type
        ann_type = ''
        transcript = ''
        for child in node:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'annotation':
                if child.get('type') == 'type':
                    ann_type = (child.text or '').strip()
                elif child.get('type') == 'transcription':
                    transcript = (child.text or '').strip()

        # Word → collect all child trace refs and build RowNode
        if ann_type == 'Word':
            trace_refs = []
            for child in node:
                child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                if child_tag == 'traceView':
                    ref = child.get('traceDataRef', '')
                    if ref.startswith('#'):
                        ref = ref[1:]
                    if ref in traces_by_id:
                        trace_refs.append(ref)

            if not trace_refs:
                return []

            # Build a single SymbolNode with all traces for the word
            traces = []
            for i, ref in enumerate(trace_refs):
                pts = traces_by_id[ref]
                x = [p[0] for p in pts]
                y = [p[1] for p in pts]
                traces.append(Trace(x, y, inkml_id=i))

            tg = TraceGroup(traces=traces, label=transcript or '')
            return [RowNode(children=[SymbolNode(trace_group=tg)])]

        # Otherwise recurse
        rows = []
        for child in node:
            rows.extend(_extract_word_rows(child, depth + 1))
        return rows

    return _extract_word_rows(root)


def load_iamondb_files(paths) -> list[RowNode]:
    """Load all IAMonDo InkML files → flat list of RowNode."""
    all_rows = []
    for p in paths:
        try:
            all_rows.extend(_load_iamondb_file(p))
        except Exception:
            pass
    return all_rows


def get_iamondb_files() -> list[Path]:
    """Return all IAMonDo InkML file paths."""
    data_dir = Path(__file__).resolve().parent.parent / "data" / "IAMonDo-db-1.0"
    return sorted(data_dir.glob("*.inkml"))
