"""
Dataset manager for MathWriting+ InkML files.

MathWriting+ is an enriched version of the MathWriting dataset with full
symbol-level trace group annotations (segmentation), maintained in the same
directory layout as the original MathWriting dataset.

Directory layout (data/MathWriting+/):
    Test/       – 5 739 test expressions
    Val/        – 9 336 validation expressions
    Train/      – 143 106 training expressions
    Symbols/    – 6 276 individual handwritten symbols
    Synthetic/  – 85 962 synthetically generated expressions
"""

import os
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_MW_ROOT = _PROJECT_ROOT / "data" / "MathWriting+"


class MathWritingFileManager:
    """Locate InkML files in the MathWriting+ directory tree."""

    @staticmethod
    def _get_files(split: str) -> list[str]:
        split_dir = _MW_ROOT / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"MathWriting+ split directory not found: {split_dir}")
        return sorted(str(p) for p in split_dir.glob("*.inkml"))

    @staticmethod
    def get_test_files() -> list[str]:
        return MathWritingFileManager._get_files("Test")

    @staticmethod
    def get_val_files() -> list[str]:
        return MathWritingFileManager._get_files("Val")

    @staticmethod
    def get_train_files() -> list[str]:
        return MathWritingFileManager._get_files("Train")

    @staticmethod
    def get_symbol_files() -> list[str]:
        return MathWritingFileManager._get_files("Symbols")

    @staticmethod
    def get_synthetic_files() -> list[str]:
        return MathWritingFileManager._get_files("Synthetic")
