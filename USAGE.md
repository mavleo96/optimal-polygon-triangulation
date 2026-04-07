# Usage

## Requirements

- Python 3.12+
- Dependencies listed in `pyproject.toml`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## File Formats

**Input** — one vertex per line, clockwise order:

```
x1 y1
x2 y2
...
```

**Output** — one diagonal per line as vertex index pairs:

```
i j
k l
...
```

An *n*-vertex polygon produces exactly *n* − 3 diagonals.

---

## CLI — Optimal Triangulation

```bash
python -m src.optimal \
  --input_file  polygon.txt   \
  --output_file diagonals.txt \
  --criteria    minsum        \
  --validate
```

`--criteria` accepts `minsum`, `minimax`, or `maximin` — see README for definitions.
`--validate` runs correctness checks on the output.

---

## CLI — Ear Clipping

```bash
python -m src.ear_clipping \
  --input_file  polygon.txt   \
  --output_file diagonals.txt \
  --validate
```

---

## Generate Test Suite

```bash
python scripts/generate_testing_suite.py \
  --min-points  5             \
  --max-points  100           \
  --n-per-size  20            \
  --output-dir  testing_suite
```

Generates random, star-shaped, and convex polygon instances at each size step.
Files are named `{type}_polygon_{n}_{i:04d}.txt`.

> **Note:** Keep `--max-points` at or below 100. The random polygon generator uses
> a 2-opt heuristic (Auer & Held 1996) with O(n²) complexity and becomes unreliable
> beyond n = 100.

---

## Run Analysis

```bash
python scripts/run_analysis.py \
  --test-suite-dir testing_suite \
  --output-dir     results
```

| Output file              | Description                                                    |
|--------------------------|----------------------------------------------------------------|
| `raw.csv`                | Per-polygon, per-algorithm metrics                             |
| `comparison.csv`         | Mean ± std per algorithm across all polygon types              |
| `comparison_by_type.csv` | Mean ± std per algorithm and polygon type                      |
| `time.csv`               | Runtime vs *n* for random polygons (ear clipping and `minsum`) |
