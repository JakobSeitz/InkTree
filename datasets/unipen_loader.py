"""
Load Unipen .tgz archive into RelationNode graphs.

The archive contains:
  data/<category>/<writer>/<file>.dat   – segment files (.SEGMENT CHARACTER entries)
  include/<writer>/data/<file>.dat      – stroke data (.PEN_DOWN / .PEN_UP + X Y lines)

In the archive the segment files appear FIRST (~21 K files, ~4 MB total) and
the include files appear AFTER them (~7.8 K files, ~490 MB uncompressed).
A single forward-streaming pass:
  1. buffers all segment file contents in memory (tiny, ~4 MB)
  2. caches all include file contents in memory (~490 MB raw text)
  then processes the buffered segments against the include cache.

This avoids any backward gzip seeks (which would require re-decompressing
from the start of the archive and would make random access O(archive_size)
per sample).

Each CHARACTER segment maps a stroke-index range to a character label.
Returns one SymbolNode per character segment.
"""

import re
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ink.traces.trace import Trace
from ink.traces.trace_group import TraceGroup
from ink.nodes.symbol_node import SymbolNode


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
UNIPEN_TGZ = DATA_DIR / "unipen-CDROM-train_r01_v07.tgz"


def _parse_segment_dat(content: str):
    """Return (include_rel_path, list of (start, end, label))."""
    include_path = None
    segments = []
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('.INCLUDE'):
            include_path = line.split(None, 1)[1].strip()
        elif line.startswith('.SEGMENT CHARACTER'):
            m = re.match(r'\.SEGMENT CHARACTER (\d+)(?:-(\d+))? \? "(.*)"', line)
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else start
                label = m.group(3)
                segments.append((start, end, label))
    return include_path, segments


def _parse_include_dat(content: str) -> list[list[tuple[int, int]]]:
    """Parse stroke data from a Unipen include file. Returns list of strokes."""
    strokes = []
    current = []
    recording = False
    for line in content.splitlines():
        line = line.strip()
        if line == '.PEN_DOWN':
            current = []
            recording = True
        elif line == '.PEN_UP':
            if current:
                strokes.append(current)
            recording = False
        elif recording and re.match(r'^-?\d+ -?\d+$', line):
            x, y = map(int, line.split())
            current.append((x, -y))  # invert Y
    if recording and current:
        strokes.append(current)
    return strokes


def load_unipen(max_samples: int = None) -> list[SymbolNode]:
    """Load Unipen tgz archive → list of SymbolNode.

    Uses a single forward-streaming pass through the gzip archive:
      • Segment files (first in archive, ~4 MB total) are buffered in memory.
      • Include files (later in archive, ~490 MB uncompressed) are cached as
        raw text.
    After the pass the buffered segments are processed against the cache.
    """
    if not UNIPEN_TGZ.exists():
        raise FileNotFoundError(f"Unipen archive not found: {UNIPEN_TGZ}")

    # Buffer segment file content (small: ~21 K × ~200 B = ~4 MB)
    seg_buffer: list[tuple[str, str]] = []   # (member.name, raw_text)
    # Cache include file content (large: ~7.8 K × ~62 KB avg = ~490 MB)
    include_cache: dict[str, str] = {}       # member.name → raw_text

    with tarfile.open(str(UNIPEN_TGZ), 'r:gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith('.dat'):
                continue

            raw = tar.extractfile(member)
            if raw is None:
                continue
            text = raw.read().decode('latin1', errors='ignore')

            if '/include/' in member.name:
                include_cache[member.name] = text
            elif '/data/' in member.name and '/include/' not in member.name:
                seg_buffer.append((member.name, text))

    # Process buffered segment files using the cached include data
    nodes: list[SymbolNode] = []
    for seg_name, content in seg_buffer:
        if max_samples is not None and len(nodes) >= max_samples:
            break

        include_rel, segments = _parse_segment_dat(content)
        if not include_rel or not segments:
            continue

        base_prefix = seg_name.rsplit('/data/', 1)[0]
        include_name = f"{base_prefix}/include/{include_rel}"

        inc_content = include_cache.get(include_name)
        if inc_content is None:
            continue

        strokes = _parse_include_dat(inc_content)
        if not strokes:
            continue

        for start_idx, end_idx, label in segments:
            if max_samples is not None and len(nodes) >= max_samples:
                break
            if end_idx >= len(strokes):
                continue
            stroke_block = strokes[start_idx: end_idx + 1]
            traces = []
            for i, pts in enumerate(stroke_block):
                x = [p[0] for p in pts]
                y = [p[1] for p in pts]
                if x:
                    traces.append(Trace(x, y, inkml_id=i))
            if traces:
                tg = TraceGroup(traces=traces, label=label)
                nodes.append(SymbolNode(trace_group=tg))

    return nodes
