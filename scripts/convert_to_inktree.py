"""
Convert CROHME InkML files to the InkTree format.

Reads all 2023 test InkML files and writes a single
data/inktree/crohme2023_test.inktree.jsonl.gz file.

Usage:
    python scripts/convert_to_inktree.py [--split {2023test,2019test,2016test}]
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from tqdm import tqdm

from datasets.crohme import CrohmeFileManager
from ink.graph import load_inkml_file
from inktree.io import save_inktree

OUT_DIR = Path(__file__).parent.parent / "data" / "inktree"

SPLITS = {
    "2023test": CrohmeFileManager.get_2023test_files,
    "2019test": CrohmeFileManager.get_2019test_files,
    "2016test": CrohmeFileManager.get_2016test_files,
}


def convert(split: str):
    get_files = SPLITS[split]
    files = get_files()
    if not files:
        print(f"No files found for split '{split}'. Check data/CROHME23/INKML/.")
        return

    out_path = OUT_DIR / f"crohme_{split}.inktree.jsonl.gz"
    print(f"Converting {len(files)} InkML files → {out_path}")

    graphs = []
    skipped = 0
    for path in tqdm(files, desc="Parsing InkML"):
        graph = load_inkml_file(path)
        if graph is None:
            skipped += 1
            continue
        graphs.append(graph)

    print(f"Parsed {len(graphs)} graphs ({skipped} skipped / undefined relations).")
    save_inktree(graphs, out_path)
    print(f"Saved to {out_path}  ({out_path.stat().st_size / 1024:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="Convert CROHME InkML to InkTree format")
    parser.add_argument(
        "--split",
        choices=list(SPLITS.keys()),
        default="2023test",
        help="Which dataset split to convert (default: 2023test)",
    )
    args = parser.parse_args()
    convert(args.split)


if __name__ == "__main__":
    main()
