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
| `any` | Undefined relation | `children: [...]` |
| `noisy` | Noise/artifact | `children: [...]` |
| `line` | Horizontal line | — |

The `type` field is an open identifier: unknown types decode gracefully via a generic fallback, allowing schema extension without a version bump.

---

## Repository Structure

```
inktree/          Core library: encode, decode, I/O, schema
ink/              Trace and node infrastructure (InkML parser, relation nodes)
datasets/         Dataset loaders
  crohme.py         CROHME file manager
  mathwriting.py    MathWriting+ file manager
  json_loader.py    JSON-folder loader (DeepWriting, IAMonDB)
  detexify_loader.py
  unipen_loader.py
  jsonl_loader.py   Legacy JSONL loader
scripts/
  convert_to_inktree.py   Convert InkML splits → InkTree
  benchmark_multi.py      Full multi-dataset benchmark
  dataset_stats.py        Dataset structure statistics
  plot_inktree.py         Visualize an InkTree file
  plot_inkml.py           Visualize an InkML file
  plot_compare.py         Side-by-side InkML vs InkTree comparison
stats/            Benchmark results (JSON + text summary)
plots/            Comparison plots (InkML vs InkTree rendering)
```

---

## Benchmark Results

Evaluated across 15 configurations spanning 7 dataset families. Source sizes and load times are measured on each dataset's original format.

### InkML-based datasets (CROHME, CROHME+, MathWriting+)

| Dataset | N | Source MB | ms/s | InkTree MB | ms/s | Size | Speed |
|---|---|---|---|---|---|---|---|
| CROHME 2023 Test | 2,300 | 28.95 | 0.572 | 8.06 | 0.233 | 27.8% | 2.5× |
| CROHME 2019 Test | 1,199 | 9.27 | 0.505 | 2.21 | 0.154 | 23.9% | 3.3× |
| CROHME 2016 Val | 1,147 | 9.28 | 0.472 | 2.32 | 0.164 | 25.0% | 2.9× |
| CROHME 2023 Val | 555 | 7.23 | 0.413 | 2.01 | 0.324 | 27.8% | 1.3× |
| CROHME Real Train | 12,010 | 113.04 | 0.465 | 28.16 | 0.222 | 24.9% | 2.1× |
| CROHME+ Synth.* | 2,000 | 9.46 | 0.336 | 2.19 | 0.098 | 23.2% | 3.4× |
| MW+ Test | 5,739 | 55.52 | 0.536 | 17.61 | 0.208 | 31.7% | 2.6× |
| MW+ Val | 9,336 | 85.52 | 0.543 | 26.21 | 0.186 | 30.6% | 2.9× |
| MW+ Symbols | 6,276 | 11.82 | 0.076 | 2.39 | 0.017 | 20.2% | 4.4× |
| MW+ Train* | 2,000 | 20.09 | 0.869 | 6.06 | 0.225 | 30.2% | 3.9× |
| MW+ Synthetic* | 2,000 | 29.81 | 0.741 | 8.04 | 0.273 | 27.0% | 2.7× |

### Other source formats

| Dataset | Fmt | N | Source MB | ms/s | InkTree MB | ms/s | Size | Speed |
|---|---|---|---|---|---|---|---|---|
| DeepWriting† | .json | 5,159 | 722.2 | 0.506 | 6.2 | 0.270 | 0.9%† | 1.9× |
| IAMonDB† | .json | 11,242 | 2,063.6 | 0.700 | 28.0 | 0.267 | 1.4%† | 2.6× |
| Detexify† | .sql | 210,454 | 1,058.2 | 0.545 | 78.1 | 0.030 | 7.4% | 18.4× |
| Unipen† | .tgz | 79,452 | 155.8 | 0.149 | 9.3 | 0.014 | 5.9% | 10.3× |

\* Random sample from larger split. † Full split. Size = InkTree / source (lower is better). Source MB for DeepWriting and Unipen is the full archive/folder size; the paper normalizes these to the matched sample universe (588 MB and 57 MB respectively). JSON source sizes (DeepWriting, IAMonDB) include metadata fields beyond stroke data not stored in InkTree.

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
  author    = {Anonymous Authors},
  booktitle = {Proceedings of ICDAR 2026},
  year      = {2026}
}
```
