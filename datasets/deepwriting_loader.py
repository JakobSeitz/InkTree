"""
Load DeepWriting .npz files into RelationNode graphs.

Format:
  strokes      – object array, each element is (N, 3) float32: [dx, dy, pen_up]
  char_labels  – object array, each element is (N,) int32 char index per point
  soc_labels   – start-of-character flags per point
  eoc_labels   – end-of-character flags per point
  texts        – text string per sample
  alphabet     – list of characters (index 0 = space/unknown)

One .npz file = training or validation split.

We build one RowNode per sample by:
  1. Reconstructing absolute (x, y) from cumulative-sum of deltas
  2. Segmenting points into character strokes via char_labels / eoc
  3. Wrapping each character segment in a SymbolNode
  4. Returning a RowNode containing the symbols
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from ink.nodes.symbol_node import SymbolNode
from ink.nodes.row_node import RowNode


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _npz_to_row_nodes(npz_path) -> list[RowNode]:
    d = np.load(str(npz_path), allow_pickle=True)
    strokes_arr = d['strokes']        # object array
    char_labels_arr = d['char_labels']
    alphabet = list(d['alphabet'])

    rows = []
    for sample_idx in range(len(strokes_arr)):
        stroke_data = strokes_arr[sample_idx]   # (N, 3): dx, dy, pen_up
        char_lab = char_labels_arr[sample_idx]  # (N,) int32

        if len(stroke_data) == 0:
            continue

        # Reconstruct absolute coordinates
        dx = stroke_data[:, 0].astype(float)
        dy = stroke_data[:, 1].astype(float)
        x = np.cumsum(dx)
        y = np.cumsum(dy)
        pen_up = stroke_data[:, 2]  # 1 = pen lifted after this point

        # Group into physical strokes by pen_up flag
        stroke_segs: list[tuple[list, list, list]] = []  # (x_pts, y_pts, char_ids)
        seg_x, seg_y, seg_c = [], [], []
        for i in range(len(x)):
            seg_x.append(float(x[i]))
            seg_y.append(float(y[i]))
            seg_c.append(int(char_lab[i]))
            if pen_up[i] == 1 or i == len(x) - 1:
                if seg_x:
                    stroke_segs.append((seg_x, seg_y, seg_c))
                seg_x, seg_y, seg_c = [], [], []

        # Group strokes into characters by dominant char label
        # A character = consecutive strokes sharing the same majority char_label
        char_to_strokes: dict[tuple, list] = {}
        # Use (char_idx, occurrence) to handle repeated chars; track by run
        char_runs: list[tuple[int, list]] = []
        for sx, sy, sc in stroke_segs:
            if not sc:
                continue
            # majority vote
            from collections import Counter
            majority = Counter(sc).most_common(1)[0][0]
            if char_runs and char_runs[-1][0] == majority:
                char_runs[-1][1].append((sx, sy))
            else:
                char_runs.append((majority, [(sx, sy)]))

        if not char_runs:
            continue

        symbols = []
        trace_id = 0
        for char_idx, strk_list in char_runs:
            char_label = alphabet[char_idx] if char_idx < len(alphabet) else ''
            traces = []
            for sx, sy in strk_list:
                traces.append(Trace(sx, sy, inkml_id=trace_id))
                trace_id += 1
            if traces:
                tg = TraceGroup(traces=traces, label=char_label)
                symbols.append(SymbolNode(trace_group=tg))

        if symbols:
            rows.append(RowNode(children=symbols))

    return rows


def load_deepwriting(split: str = "training") -> list[RowNode]:
    """Load DeepWriting samples. split = 'training' or 'validation'."""
    path = DATA_DIR / f"deepwriting_{split}.npz"
    if not path.exists():
        raise FileNotFoundError(f"DeepWriting file not found: {path}")
    return _npz_to_row_nodes(path)


def get_deepwriting_paths() -> list[Path]:
    return [p for p in [
        DATA_DIR / "deepwriting_training.npz",
        DATA_DIR / "deepwriting_validation.npz",
    ] if p.exists()]
