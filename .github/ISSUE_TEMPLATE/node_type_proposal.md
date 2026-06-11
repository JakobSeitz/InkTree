---
name: Node type proposal
about: Propose a new default node type for the InkTree format
title: "[node type] <short-type-string>"
labels: format, enhancement
---

## Type string

<!-- Short lowercase identifier, e.g. `table`, `bond`, `axis` -->

## Semantic child keys

<!-- Name and meaning of each key, e.g. for `frac`: `numer` (numerator node), `denom` (denominator node), `bar` (fraction bar strokes) -->

| Key | Type | Meaning |
|---|---|---|
| | | |

## Minimal example sample

```json
{
  "version": "1.0",
  "label": "...",
  "node": {
    "type": "...",
    "...": "..."
  }
}
```

## What existing types cannot express this

<!-- Why is composition of existing types (row, matrix, any, ...) not enough? -->

## Real-world data (optional)

<!-- Dataset / ink samples this type would model; screenshots welcome -->
