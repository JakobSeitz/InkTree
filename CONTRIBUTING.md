# Contributing to InkTree

Thanks for your interest! InkTree is intended to evolve **user-driven** — both the reference implementation and the format itself. Contributions of any size are welcome.

## Code contributions

1. Fork the repository and create a feature branch.
2. Make your changes. Match the existing code style; keep dependencies minimal (`numpy`, `scipy`, `matplotlib`, `tqdm`).
3. If you touch the encoder/decoder, verify the roundtrip: encode → decode → re-encode must be stable (see `inktree/encode.py` / `inktree/decode.py`).
4. Open a pull request with a short description of what and why.

Bug reports and questions go to [Issues](../../issues); format-design conversations to [Discussions](../../discussions).

## Proposing a new node type

The `type` field is an **open identifier** — you do not need permission or a format version bump to use a custom node type in your own data. Unknown types decode gracefully as generic containers, so your files stay readable by every InkTree implementation.

If a type is useful beyond your project, propose it for the default set:

1. **Pick a short type string** (lowercase, like `sym`, `frac`, `matrix`) and define its **semantic child keys** (like `numer`/`denom` for `frac`).
2. **Show a minimal example sample** (JSON) and, ideally, real ink it models.
3. **Explain what existing types cannot express.** Prefer composition over new types — e.g. `\binom{n}{k}` needs no `binom` type, it is a 2×1 `matrix` flanked by parenthesis symbols.
4. Open an issue using the *Node type proposal* template (or start a Discussion if it is still vague).

Design guidelines that proposals are checked against:

- **Named semantic keys**, not positional child conventions or ID cross-references.
- **Self-contained samples** — no references outside the node tree.
- **Structure implies position** where possible (e.g. `matrix` cells carry no explicit grid coordinates).
- Dataset-level metadata (units, writer info, licensing) stays out of per-sample data.

Domains we would love to see covered: tables, coordinate systems and plots, words and sentences, drawings and diagrams, chemical formulas, music notation.

## Adding a dataset loader

Loaders for new datasets live in `datasets/` (one file per source format, see `datasets/json_loader.py` for a template). A loader should return relation-graph nodes (`ink/nodes/`) so the standard encoder handles InkTree serialization. Please include a benchmark entry (`scripts/benchmark_multi.py`) if you can share reproducible numbers.

## License

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE).
