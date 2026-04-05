"""
Runs triangulation analysis on a test suite of polygons.

Outputs:
    raw.csv                — metrics for each polygon, each algorithm
    comparison.csv         — mean ± std of normalized metrics for each algorithm
    comparison_by_type.csv — mean ± std of normalized metrics for each algorithm by polygon type
    time.csv               — runtime vs n for random polygons (ear clipping + optimal sum)

Usage:
    python run_analysis.py --test-suite-dir testing_suite --output-dir results
"""

import argparse
import os
import sys
import time
from functools import partial
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.getcwd())

from src.ear_clipping import ear_clipping_triangulation
from src.models import Polygon
from src.optimal import optimal_triangulation
from src.utils.geometry import distance
from src.utils.io import read_input
from src.utils.validation import validate_polygon_input, validate_triangulation

ALGOS = {
    "ear_clipping": ear_clipping_triangulation,
    "optimal_sum": partial(optimal_triangulation, criteria="sum"),
    "optimal_max": partial(optimal_triangulation, criteria="max"),
    "optimal_min": partial(optimal_triangulation, criteria="min"),
}
NORM_METRICS = ["norm_dlength", "norm_max_dlength", "norm_min_dlength"]
TIME_ALGOS = ["ear_clipping", "optimal_sum"]


def _compute_metrics(polygon: Polygon, diagonals: list[tuple[int, int]]) -> dict:
    n = len(polygon)
    vertices = polygon.vertices

    edge_lengths = [distance(vertices[i].p, vertices[(i + 1) % n].p) for i in range(n)]
    total_edge_length = sum(edge_lengths)
    mean_edge_length = total_edge_length / n

    diagonal_lengths = [distance(vertices[i].p, vertices[j].p) for i, j in diagonals]
    total_diagonal_length = sum(diagonal_lengths)
    mean_diagonal_length = total_diagonal_length / (n - 3)
    max_diagonal_length = max(diagonal_lengths)
    min_diagonal_length = min(diagonal_lengths)

    return {
        "total_elength": total_edge_length,
        "mean_elength": mean_edge_length,
        "total_dlength": total_diagonal_length,
        "mean_dlength": mean_diagonal_length,
        "max_dlength": max_diagonal_length,
        "min_dlength": min_diagonal_length,
        "norm_dlength": mean_diagonal_length / mean_edge_length,
        "norm_max_dlength": max_diagonal_length / mean_edge_length,
        "norm_min_dlength": min_diagonal_length / mean_edge_length,
    }


def _agg(series: pd.Series, stat: str) -> float | None:
    """Safely aggregates a series — returns None if column missing or all NaN."""
    if series is None or series.dropna().empty:
        return None
    return getattr(series, stat)()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-suite-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    rows, errors = [], []

    for f in tqdm(sorted(args.test_suite_dir.iterdir()), desc="Analysing", unit="polygon"):
        parts = f.stem.rsplit("_", 3)
        n = int(parts[2])
        polygon_type = parts[0]
        vertices = read_input(f)

        try:
            validate_polygon_input(vertices)
        except Exception as e:
            errors.append(f"Invalid {f.name}: {e}")
            continue

        polygon = Polygon(vertices)

        for algo, fn in ALGOS.items():
            row = {"id": f.stem, "polygon_type": polygon_type, "n": n, "algo": algo}
            try:
                t0 = time.perf_counter()
                _, diagonals = fn(polygon)
                elapsed = time.perf_counter() - t0

                validate_triangulation(polygon, diagonals)

                metrics = _compute_metrics(polygon, diagonals)
                row["time"] = elapsed
                row.update(metrics)
            except Exception as e:
                errors.append(f"{algo} failed {f.name}: {e}")

            rows.append(row)

    if errors:
        print(f"\n{len(errors)} error(s):\n" + "\n".join(f"  {e}" for e in errors))

    df = pd.DataFrame(rows)

    # --- 1. raw.csv ---
    df.to_csv(args.output_dir / "raw.csv", index=False)

    # --- 2. comparison.csv ---
    agg_dict = {
        f"{metric}_{stat}": (metric, stat) for metric in NORM_METRICS for stat in ["mean", "std"]
    }
    comparison = df.groupby("algo", as_index=False).agg(**agg_dict)
    comparison.to_csv(args.output_dir / "comparison.csv", index=False)

    # --- 3. comparison_by_type.csv ---
    comparison_by_type = df.groupby(["polygon_type", "algo"], as_index=False).agg(**agg_dict)
    comparison_by_type.to_csv(args.output_dir / "comparison_by_type.csv", index=False)

    # --- 4. time.csv — random polygons only, ear clipping + optimal sum ---
    time_df = df[(df.polygon_type == "random") & df.algo.isin(TIME_ALGOS)]
    agg_dict = {f"time_{stat}": ("time", stat) for stat in ["mean", "std"]}
    time_df = time_df.groupby(["algo", "n"], as_index=False).agg(**agg_dict)
    time_df.to_csv(args.output_dir / "time.csv", index=False)

    print(f"\nResults written to {args.output_dir}/")
    print("  raw.csv, comparison.csv, comparison_by_type.csv, time.csv")


if __name__ == "__main__":
    main()
