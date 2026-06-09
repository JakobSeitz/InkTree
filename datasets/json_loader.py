"""
Load JSON-format handwriting datasets (DeepWriting, IAMonDB) into RowNode graphs.

Each JSON file contains samples keyed as sample0, sample1, ..., each with:
  - word_stroke / points / strokes  : flat list of point dicts with 'x' and 'y' keys
  - wholeword_segments              : list of word dicts with chars[].{char, ranges}
  - word_segments_chars             : list of {char, start, end} dicts (fallback)

Each sample becomes one RowNode whose children are SymbolNodes (one per character).
Character strokes are identified by index ranges into the flat point list.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.row_node import RowNode


def _extract_flat_xyt(sample: dict) -> tuple[list, list, list | None]:
    """Return flat (xs, ys, ts) from word_stroke, points, or strokes.

    ts is None when no timestamp field ('ts') is present.
    DeepWriting stores x/y/ts as strings; IAMonDB stores them as floats.
    """
    for key in ("word_stroke", "points"):
        ws = sample.get(key)
        if isinstance(ws, list) and ws and isinstance(ws[0], dict) and "x" in ws[0]:
            xs = [float(p["x"]) for p in ws if "x" in p]
            ys = [float(p["y"]) for p in ws if "y" in p]
            ts = [float(p["ts"]) for p in ws if "ts" in p] if any("ts" in p for p in ws) else None
            if ts and len(ts) != len(xs):
                ts = None
            return xs, ys, ts

    ws = sample.get("strokes")
    if isinstance(ws, list):
        xs, ys, ts = [], [], []
        has_ts = False
        for stroke in ws:
            if isinstance(stroke, list):
                for p in stroke:
                    if isinstance(p, dict) and "x" in p and "y" in p:
                        xs.append(float(p["x"]))
                        ys.append(float(p["y"]))
                        if "ts" in p:
                            ts.append(float(p["ts"]))
                            has_ts = True
        if xs:
            return xs, ys, (ts if has_ts and len(ts) == len(xs) else None)

    return [], [], None


def _extract_flat_xy(sample: dict) -> tuple[list, list]:
    xs, ys, _ = _extract_flat_xyt(sample)
    return xs, ys


def _sample_to_row_node(sample: dict) -> RowNode | None:
    """Convert one JSON sample dict to a RowNode, or None if unparseable."""
    xs, ys, ts = _extract_flat_xyt(sample)
    if not xs:
        return None

    n_pts = len(xs)
    symbols = []
    trace_id = 0

    # Prefer wholeword_segments (present in both DeepWriting and IAMonDB)
    whole = sample.get("wholeword_segments")
    if isinstance(whole, list) and whole:
        for word in whole:
            if not isinstance(word, dict):
                continue
            for ch_obj in word.get("chars", []):
                if not isinstance(ch_obj, dict):
                    continue
                ch = ch_obj.get("char", "") or ""
                ranges = ch_obj.get("ranges", [])
                traces = []
                for rng in ranges:
                    rng_xs, rng_ys, rng_ts = [], [], []
                    for idx in rng:
                        i = int(idx)
                        if 0 <= i < n_pts:
                            rng_xs.append(xs[i])
                            rng_ys.append(ys[i])
                            if ts is not None:
                                rng_ts.append(ts[i])
                    if rng_xs:
                        t_arg = rng_ts if rng_ts else None
                        traces.append(Trace(rng_xs, rng_ys, t=t_arg, inkml_id=trace_id))
                        trace_id += 1
                if traces:
                    tg = TraceGroup(traces=traces, label=ch)
                    symbols.append(SymbolNode(trace_group=tg))
        if symbols:
            return RowNode(children=symbols)

    # Fallback: word_segments_chars with {char, start, end}
    wsc = sample.get("word_segments_chars")
    if isinstance(wsc, list) and wsc:
        for seg in wsc:
            if not isinstance(seg, dict):
                continue
            s = int(seg.get("start", seg.get("s", 0)))
            e = int(seg.get("end", seg.get("e", s)))
            if s > e:
                s, e = e, s
            s = max(0, s)
            e = min(n_pts - 1, e)
            if s > e:
                continue
            ch = seg.get("char", seg.get("c", "")) or ""
            t_arg = ts[s : e + 1] if ts is not None else None
            tg = TraceGroup(
                traces=[Trace(xs[s : e + 1], ys[s : e + 1], t=t_arg, inkml_id=trace_id)],
                label=ch,
            )
            trace_id += 1
            symbols.append(SymbolNode(trace_group=tg))
        if symbols:
            return RowNode(children=symbols)

    return None


def get_json_files(root_dir: str | Path) -> list[Path]:
    """Return sorted list of all .json files under root_dir."""
    root = Path(root_dir)
    return sorted(root.rglob("*.json"))


_SAMPLE_KEY_RE = re.compile(rb'"sample\d+"\s*:')


def count_json_samples(root_dir: str | Path) -> int:
    """Count raw samples in JSON files (sample0/sample1/... entries)."""
    total = 0
    for json_path in get_json_files(root_dir):
        try:
            with open(json_path, "rb") as f:
                content = f.read()
        except Exception:
            continue
        matches = _SAMPLE_KEY_RE.findall(content)
        total += len(matches) if matches else 1
    return total


def load_json_dataset(root_dir: str | Path, max_samples: int = None) -> list[RowNode]:
    """Load all JSON samples under root_dir into RowNode graphs.

    Parameters
    ----------
    root_dir    : root directory containing (nested) JSON files
    max_samples : if not None, stop after this many successfully loaded graphs
    """
    rows: list[RowNode] = []
    for json_path in get_json_files(root_dir):
        if max_samples is not None and len(rows) >= max_samples:
            break
        try:
            with open(json_path, encoding="utf-8") as f:
                obj = json.load(f)
        except Exception:
            continue

        # Extract sample0, sample1, ... in order
        sample_keys = sorted(
            [k for k in obj if k.startswith("sample")],
            key=lambda k: int(k[6:]) if k[6:].isdigit() else 0,
        )
        if not sample_keys and isinstance(obj, dict):
            sample_keys = [""]  # treat whole dict as a single sample

        for key in sample_keys:
            if max_samples is not None and len(rows) >= max_samples:
                break
            sample = obj[key] if key else obj
            if not isinstance(sample, dict):
                continue
            try:
                row = _sample_to_row_node(sample)
                if row is not None:
                    rows.append(row)
            except Exception:
                pass

    return rows
