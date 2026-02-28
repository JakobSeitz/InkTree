# InkTree vs. Source Format — Field Comparison

Comparison of what each source format contains vs. what InkTree **as a format** supports.
This is independent of what any specific converter currently extracts.

---

## Design philosophy: InkTree vs. companion metadata

InkTree deliberately separates two categories of information:

| Category | Where it lives | Rationale |
|---|---|---|
| **Training-relevant data** — strokes (x/y/t), structural hierarchy, labels | **InkTree sample** (`.inktree.jsonl.gz`) | Loaded at training time; must be compact, fast, self-contained |
| **Dataset-level context** — coordinate units, license, writer demographics, device specs, split definitions | **Companion metadata** (dataset card, README, or sidecar JSON) | Needed once for documentation/reproducibility; not per-sample |

Fields marked **→ companion** below are *not ignored* — they are intentionally kept out of
the per-sample format and belong in a dataset-level description file. This keeps the
per-sample format simple and the training loop free of non-signal data.

### What belongs in companion metadata (examples)
- **Coordinate units**: are x/y in pixels, mm, or arbitrary device units? (varies per dataset)
- **Timestamp units and epoch**: ms since pen-down, Unix epoch ms, or relative offsets?
- **License / terms of use**
- **Writer demographics**: handedness, age, native language, education, profession
- **Device / sensor specs**: pen model, sampling rate, pressure resolution
- **Split definitions**: which sample IDs belong to train/val/test
- **Dataset version and source**

---

## InkTree format capabilities (per sample)

```json
{
  "version": "1.0",
  "label": "<LaTeX formula / character string / key>",
  "node": {
    "type": "<sym | row | word | frac | sub | sup | subsup | sqrt | root | ...>",
    "label": "...",
    "strokes": [{"x": [...], "y": [...], "t": [...]}],
    "children": [...]
  }
}
```

- **x, y** — stroke coordinates (rounded to 4 decimal places)
- **t** — timestamps, natively supported per point (unit documented in companion metadata)
- **Any typed node** — `type` is an open string; unknown types decode via generic fallback
- **Named semantic child keys** — numer/denom, base/sub/sup, inner/index, bar, strokes
- **Labels at any node level** — `label` field valid on sym, word, row, or any custom node

---

## CROHME (InkML)

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ | ✓ | Unit → companion (device-dependent pixels) |
| Symbol labels | ✓ traceGroup | ✓ | |
| Relation hierarchy | ✓ MathML traceGroups | ✓ typed node tree | |
| LaTeX expression | ✓ `annotation type="truth"` | ✓ | Also re-derivable via `node.latex()` |
| MathML encoding | ✓ `annotationXML` | ✓ | Re-generated via `node.get_math_ml()` (built-in) |
| Writer ID | ✓ `annotation type="writer"` | → companion | Per-writer aggregation, not per-sample signal |
| Copyright / source lab | ✓ `annotation type="copyright"` | → companion | License info |
| UI form identifier | ✓ `annotation type="UI"` | → companion | Dataset-internal bookkeeping |

---

## MathWriting+ (InkML)

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ | ✓ | Unit → companion |
| Timestamps (T channel, ms) | ✓ per point | ✓ | Unit (ms relative) → companion |
| Symbol labels | ✓ traceGroup | ✓ | |
| Relation hierarchy | ✓ | ✓ | |
| LaTeX label | ✓ | ✓ | Also re-derivable via `node.latex()` |
| MathML encoding | ✓ | ✓ | Re-generated via `node.get_math_ml()` (built-in) |
| Normalized LaTeX | ✓ `normalizedLabel` | — | Derivable by normalizing the LaTeX label |
| Sample ID | ✓ `sampleId` hash | → companion | Traceability; not a training signal |
| Split tag | ✓ `splitTagOriginal` | → companion | Split definition belongs in dataset card |
| Creation method (human/synth.) | ✓ `inkCreationMethod` | → companion | Dataset-level property |
| Copyright | ✓ | → companion | License info |

---

## DeepWriting & IAMonDB (JSON folders, shared format)

Both datasets use the same JSON structure. IAMonDB additionally has a `pressure` field per point.

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ | ✓ | Unit → companion (device pixels) |
| Timestamps (`ts` per point, ms) | ✓ | ✓ | Unit → companion |
| Character labels | ✓ `chars[].char` | ✓ | |
| Word-level label | ✓ `ocr_label` / `recognized_label` | ✓ | Via `word` node with `label` field |
| Sentence text | ✓ `word_ascii` | ✓ | Reconstructable from labels; or top-level `label` |
| Pen pressure (IAMonDB only) | ✓ per point | — | Not in current schema; absent from most datasets |
| User ID | ✓ `user_id` | → companion | Writer demographics / privacy |
| Word form / source system | ✓ | → companion | Dataset bookkeeping |
| Image file paths (word/char) | ✓ | — | External refs; InkTree is self-contained |
| Segmentation / recognition validity flags | ✓ | — | Curation metadata; applied before conversion |

---

## Detexify (PostgreSQL SQL dump)

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ | ✓ | Unit → companion |
| Timestamps (Unix ms per point) | ✓ | ✓ | Epoch semantics → companion |
| Full symbol key | ✓ e.g. `latex2e-OT1-_textless` | ✓ stored as label | Package and encoding recoverable from label |
| Sample ID (integer) | ✓ | → companion | Traceability |

---

## IAMonDo (InkML, document-level)

IAMonDo represents full handwritten documents with mixed object types — text paragraphs,
diagrams, drawings, lists, and editorial markings — in a deeply nested `traceView` hierarchy.
Traces use 4-channel delta encoding (X, Y, T, F where F = pen force/pressure).

### Document node type hierarchy in IAMonDo
```
Document
└── Textblock
│   └── Textline  (transcription: full line text)
│       └── Word  (transcription: word text)
│           └── Correction
├── Diagram
│   ├── Drawing
│   └── Textline → Word
├── List
│   └── Textline → Word
└── Marking
    ├── Marking_Underline
    ├── Marking_Angle
    ├── Marking_Bracket
    ├── Marking_Sideline
    └── Textline → Word
```

### Field comparison

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ delta-encoded | ✓ | Decoded to absolute by parser; unit → companion |
| Timestamps (T channel, ms) | ✓ per point | ✓ | Unit → companion |
| Pen force / pressure (F channel) | ✓ per point | — | Not in current schema |
| Document hierarchy | ✓ nested `traceView` + `annotation type="type"` | ✓ | Via open type system: `type="document"`, `type="textblock"`, etc. |
| Textline / Word transcriptions | ✓ `annotation type="transcription"` | ✓ | Via `label` field on any node |
| Correction nodes | ✓ `type="Correction"` with transcription | ✓ | Via `type="correction"` node with `label` |
| Drawing / Diagram regions | ✓ `type="Drawing"`, `type="Diagram"` | ✓ | Via `type="drawing"`, `type="diagram"` with children |
| List structure | ✓ `type="List"` | ✓ | Via `type="list"` node |
| Marking types | ✓ `Marking_Underline`, `_Angle`, `_Bracket`, `_Sideline` | ✓ | Via corresponding `type` strings |
| Author metadata | ✓ (birthday, sex, citizenship, profession, education, native language) | → companion | Writer profile; belongs in dataset card |
| Page bounds | ✓ `annotation type="Page Bounds"` | → companion | Rendering / layout context |
| Pen device info | ✓ (manufacturer, model, serial number, pen ID) | → companion | Sensor spec; not a training signal |
| Canvas transform (affine matrix) | ✓ `<canvasTransform>` | — | Applied during parsing; result is absolute coordinates |

### Key insight: InkTree beyond formula content
IAMonDo demonstrates that InkTree's open type system generalises to full document structure.
Every IAMonDo node type (`document`, `textblock`, `textline`, `word`, `drawing`, `diagram`,
`list`, `marking`, `correction`, `marking_underline`, …) maps directly to a valid InkTree
node — unknown types decode gracefully via the generic `children` fallback in older decoders.
A complete IAMonDo page would be a single InkTree sample with `type="document"` at the root.

---

## Unipen (.tgz archive)

| Field | Source | InkTree | Note |
|---|---|---|---|
| x, y coordinates | ✓ | ✓ | Unit → companion |
| Character labels | ✓ include hierarchy | ✓ | |
| Writer context | ✓ archive path structure | → companion | Writer demographics |

---

## Summary

### InkTree per-sample support

| Category | InkTree | Note |
|---|---|---|
| x, y coordinates | ✓ | Core ink data |
| Timestamps (t) | ✓ | Native `t` field; unit documented in companion metadata |
| Symbol / character labels | ✓ | `label` on `sym` nodes |
| Word-level labels | ✓ | `label` on `word` nodes |
| Relation hierarchy (math) | ✓ | Typed nodes with semantic child keys |
| Document structure (IAMonDo style) | ✓ | Open type system — Document/Textblock/Textline/Word/Drawing/Diagram/List/Marking/Correction all valid |
| MathML | ✓ | Re-generated via `node.get_math_ml()` |
| LaTeX expression | ✓ | Stored and re-derivable via `node.latex()` |
| Pen pressure | — | Not in current schema; absent from most datasets |

### Deliberately in companion metadata (not per-sample)

| Category | Examples | Rationale |
|---|---|---|
| Coordinate units | pixels, mm, device units | Dataset-level constant; wasteful to repeat per sample |
| Timestamp semantics | ms-relative, Unix epoch | Dataset-level constant |
| License / terms of use | CC-BY, research-only, … | Legal; not a training signal |
| Writer demographics | handedness, age, native language, education | Privacy-sensitive; useful for bias analysis, not training |
| Device / sensor specs | pen model, sampling rate, pressure resolution | Sensor calibration; not per-sample |
| Split definitions | train/val/test membership | Stored in filename or sidecar; not inside samples |
| Dataset version & source | DOI, release date, origin lab | Provenance / reproducibility |
| Curation flags | segmentation validity, OCR correctness | Applied before conversion; not needed at load time |

### Note on size ratios
The extreme compression ratios for DeepWriting (0.9%) and IAMonDB (1.4%)
are primarily because the JSON source files spend most of their bytes on
metadata (image paths, OCR labels, validity flags) rather than stroke coordinates.
A stroke-only JSON baseline would yield much smaller ratios.
