# InkTree

**InkTree: A Unified Representation of Structured Online Ink**

Reference implementation for the ICDAR 2026 paper. InkTree is a lightweight, ML-oriented format for structured online handwriting that unifies digital ink, structural annotations, and spatial relations into a single self-describing hierarchical object.

---

## Motivation

Online handwriting datasets use heterogeneous source formats — InkML with multi-layer MathML annotations (CROHME, MathWriting+), JSON folder hierarchies (DeepWriting, IAMonDB), SQL dumps (Detexify), or archive-based text segments (Unipen). None share a common loading interface or relation model, requiring per-dataset adapter code before any cross-dataset experiment can begin.

InkTree addresses this by:
- Co-locating strokes, structure, and relation roles in one self-contained object
- Replacing positional child conventions with named semantic keys (`numer`/`denom`, `base`/`sub`/`sup`, ...)
- Using short canonical type strings (`sym`, `frac`, `row`, ...) instead of verbose class names
- Omitting dataset-level metadata (coordinate units, writer demographics, license) from per-sample data; these belong in companion documentation

See [FORMAT_COMPARISON.md](FORMAT_COMPARISON.md) for a field-by-field comparison of what each source format contains versus what InkTree supports.

---

## Format

Each sample is one JSON object stored in a gzip-compressed JSONL file (`.inktree.jsonl.gz`):

```json
{
  "version": "1.0",
  "label": "\\frac{2 1}{5}",
  "node": {
    "type": "frac",
    "numer": {
      "type": "row",
      "children": [
        {"type": "sym", "label": "2", "strokes": [{"x": [25.834, ...], "y": [55.977, ...]}]},
        {"type": "sym", "label": "1", "strokes": [{"x": [26.612, ...], "y": [55.774, ...]}]}
      ]
    },
    "denom": {"type": "sym", "label": "5", "strokes": [{"x": [26.182, ...], "y": [57.736, ...]}]},
    "bar": [{"x": [...], "y": [...]}]
  }
}
```

### Node Types

The `type` field is an **open identifier**, and the table below is the set of **default node types** shipped with this reference implementation — not a closed list. Unknown types decode gracefully via a generic fallback, so anyone can introduce new node types without a format version bump or coordination with this repository. The format is intended to evolve user-driven: while the defaults focus on mathematical expressions, the same mechanism models any structured ink — tables, coordinate systems and plots, words and sentences, drawings and diagrams, chemical formulas, music notation, and beyond.

| Type | Description | Semantic children |
|---|---|---|
| `sym` | Symbol (leaf) | `label`, `strokes` |
| `row` | Horizontal sequence | `children: [...]` |
| `frac` | Fraction | `numer`, `denom`, `bar` |
| `sub` | Subscript | `base`, `sub` |
| `sup` | Superscript | `base`, `sup` |
| `subsup` | Sub + superscript | `base`, `sub`, `sup` |
| `sqrt` | Square root | `inner`, `strokes` |
| `root` | N-th root | `inner`, `index`, `strokes` |
| `under` | Underscript | `base`, `under` |
| `underover` | Over + underscript | `base`, `under`, `over` |
| `matrix` | Rectangular grid (matrix / tabular layout) | `cells: [[node, ...], ...]` (2D row-major; grid position implied by structure) |
| `any` | Undefined relation | `children: [...]` |
| `noisy` | Noise/artifact | `children: [...]` |
| `line` | Multi-line container (groups rows into a multi-line expression, e.g. step-by-step calculation) | `children: [...]` (each child is one line, typically a `row`) |

Notes on `matrix`: delimiters (parentheses, brackets) are sibling `sym` nodes in the surrounding `row`, matching how they appear in the ink. Constructs like binomial coefficients need no dedicated type — `\binom{n}{k}` is a 2×1 `matrix` flanked by parenthesis symbols.

**Extending the format** is a one-line decision, not a schema change: pick a new `type` string and document its semantic child keys. Examples of plausible user-defined types: `word` / `sentence` (text lines with token labels), `table` (header/body cell roles), `axis` / `plot` (coordinate systems with curve strokes), `bond` / `ring` (chemical structures), `arrow` / `box` (diagrams). Older decoders treat unknown types as generic containers and keep all strokes accessible.

---

## Repository Structure

```
inktree/          Core library: encode, decode, I/O, schema
ink/              Trace and node infrastructure (InkML parser, relation nodes)
datasets/         Dataset loaders
  crohme.py              CROHME file manager
  mathwriting.py         MathWriting+ file manager
  json_loader.py         JSON-folder loader (DeepWriting, IAMonDB)
  deepwriting_loader.py  DeepWriting native .npz loader
  iamondb_loader.py      IAMonDB native page-level InkML loader
  detexify_loader.py     Detexify SQL-dump loader
  unipen_loader.py       Unipen .tgz streaming loader
  jsonl_loader.py        Legacy JSONL loader
scripts/
  convert_to_inktree.py   Convert InkML splits → InkTree
  benchmark_multi.py      Full multi-dataset benchmark
  benchmark_variance.py   Multi-run variance / reproducibility benchmark
  dataset_stats.py        Dataset structure statistics
  plot_inktree.py         Visualize an InkTree file
  plot_inkml.py           Visualize an InkML file
  plot_compare.py         Side-by-side InkML vs InkTree comparison
stats/            Benchmark results (JSON + text summary)
```

---

## Benchmark Results

Evaluated across 15 configurations spanning 7 dataset families. Source sizes and load times are measured on each dataset's original format.

### InkML-based datasets (CROHME, CROHME+, MathWriting+)

| Dataset | N | Source MB | ms/s | InkTree MB | ms/s | Size | Speed |
|---|---|---|---|---|---|---|---|
| CROHME 2023 Test | 2,300 | 28.95 | 0.491 | 8.06 | 0.232 | 27.8% | 2.1× |
| CROHME 2019 Test | 1,199 | 9.27 | 0.504 | 2.21 | 0.155 | 23.9% | 3.2× |
| CROHME 2016 Val | 1,147 | 9.28 | 0.448 | 2.32 | 0.169 | 25.0% | 2.7× |
| CROHME 2023 Val | 555 | 7.23 | 0.398 | 2.01 | 0.339 | 27.8% | 1.2× |
| CROHME Real Train | 12,010 | 113.04 | 0.419 | 28.16 | 0.219 | 24.9% | 1.9× |
| CROHME+ Synth.* | 2,000 | 9.46 | 0.214 | 2.19 | 0.063 | 23.2% | 3.4× |
| MW+ Test | 5,739 | 55.52 | 0.583 | 17.61 | 0.242 | 31.7% | 2.4× |
| MW+ Val | 9,336 | 85.52 | 0.410 | 26.21 | 0.185 | 30.6% | 2.2× |
| MW+ Symbols | 6,276 | 11.82 | 0.190 | 2.39 | 0.020 | 20.2% | 9.5× |
| MW+ Train* | 2,000 | 20.26 | 0.372 | 6.09 | 0.169 | 30.1% | 2.2× |
| MW+ Synthetic* | 2,000 | 29.19 | 0.570 | 7.88 | 0.280 | 27.0% | 2.0× |

### Other source formats

| Dataset | Fmt | N | Source MB | ms/s | InkTree MB | ms/s | Size | Speed |
|---|---|---|---|---|---|---|---|---|
| DeepWriting† | .json | 5,159 | 588.3 | 0.562 | 13.2 | 0.257 | 2.2% | 2.2× |
| IAMonDB† | .json | 11,242 | 2,063.6 | 0.731 | 45.7 | 0.339 | 2.2% | 2.2× |
| Detexify† | .sql | 210,454 | 1,058.2 | 0.547 | 181.6 | 0.050 | 17.2% | 10.9× |
| Unipen† | .tgz | 79,452 | 57.1 | 0.147 | 9.3 | 0.014 | 16.2% | 10.3× |

\* Random sample from larger split. † Full converted split. Size = InkTree / source (lower is better). Source MB for DeepWriting and Unipen is the matched-sample equivalent of the full archive/folder (722 MB and 156 MB respectively). JSON source sizes (DeepWriting, IAMonDB) include metadata fields beyond stroke data not stored in InkTree; InkTree retains per-point timestamps where the source provides them (MathWriting+, Detexify, DeepWriting, IAMonDB).

### Reproducibility

Seven representative configurations were repeated five times each (three for Detexify) to measure run-to-run stability; the coefficient of variation of the speedup ratio stays below 14% (median 7.0%). See `stats/benchmark_variance.json` and `scripts/benchmark_variance.py`.

---

## Usage

### Requirements

```bash
pip install -r requirements.txt
```

Python 3.10+. Dependencies: `numpy`, `scipy`, `matplotlib`, `tqdm`.

### Load an InkTree file

```python
from inktree import load_inktree_graphs

graphs = load_inktree_graphs("data/inktree/crohme_2023test.inktree.jsonl.gz")
for g in graphs[:3]:
    print(g.latex())
```

### Convert InkML → InkTree

```python
# Convert a single InkML split:
python scripts/convert_to_inktree.py --split 2023test
# Options: 2023test, 2019test, 2016test

# Or from Python:
from datasets.crohme import CrohmeFileManager
from ink.graph import get_relation_graphs_from_files
from inktree import save_inktree

files = CrohmeFileManager.get_2023test_files()
graphs = get_relation_graphs_from_files(files, keep_undefined=True, interpolate=False)
save_inktree(graphs, "output.inktree.jsonl.gz", labels=[g.latex() for g in graphs])
```

### Load JSON-format datasets (DeepWriting, IAMonDB)

```python
from datasets.json_loader import load_json_dataset

graphs = load_json_dataset("data/Deepwriting Dataset/")
# Returns list[RowNode], one per word sample
```

### Run the full benchmark

```bash
python scripts/benchmark_multi.py
# Outputs: stats/benchmark_multi.json, stats/benchmark_multi.txt

python scripts/benchmark_variance.py
# Multi-run variance analysis: stats/benchmark_variance.json
```

### Visualize

```bash
python scripts/plot_inktree.py --file data/inktree/crohme_2023test.inktree.jsonl.gz --index 0
python scripts/plot_inkml.py --file path/to/sample.inkml
python scripts/plot_compare.py --inkml path/to/sample.inkml
```

---

## Dataset Paths

Loaders expect datasets at the following locations (relative to project root). Datasets are not included in this repository.

| Dataset | Expected path |
|---|---|
| CROHME | `data/CROHME23/INKML/` |
| CROHME+ | `data/CROHME+/` |
| MathWriting+ | `data/MathWriting+/` |
| DeepWriting (JSON) | `data/Deepwriting Dataset/` |
| IAMonDB (JSON) | `data/Iamondb Dataset/` |
| Detexify | `data/detexify.sql` |
| Unipen | `data/unipen-CDROM-train_r01_v07.tgz` |

---

## Citation

```bibtex
@inproceedings{inktree2026,
  title     = {InkTree: A Unified Representation of Structured Online Ink},
  author    = {Seitz, Jakob},
  booktitle = {Proceedings of ICDAR 2026},
  year      = {2026}
}
```

---

## License

This code is released under the [MIT License](LICENSE). The datasets referenced above are subject to their respective original licenses and are not distributed with this repository.
