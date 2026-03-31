"""
Polygon test suite generator using the `polygenerator` library
(https://github.com/bast/polygenerator, MIT license).

Generates three categories of simple polygons:
    - random_polygon:        general random simple polygon (2-opt heuristic, Auer & Held 1996)
    - star_shaped_polygon:   star-shaped polygon (angle-sort with random radii)
    - convex_polygon:        convex polygon (Valtr's algorithm via stackoverflow.com/a/47358689)

Notes:
    - Author of polygenerator notes that it the library does not scale well beyond ~100 points
      for random_polygon (O(n^2) 2-opt heuristic); use --max-points <= 100 for reliable generation.
    - A fixed random seed is used for reproducibility.

Output structure:
    <output-dir>/
        random_polygon/       polygon_<n>_<i>.txt
        star_shaped_polygon/  polygon_<n>_<i>.txt
        convex_polygon/       polygon_<n>_<i>.txt

File format (one vertex per line, clockwise order):
    x1 y1
    x2 y2
    ...

Example Usage:
    python generate_testing_suite.py \
        --min-points 5 \
        --max-points 100 \
        --n-per-size 5 \
        --output-dir testing_suite
"""

import argparse
import os
import random
import sys
from pathlib import Path

from polygenerator import (
    random_convex_polygon,
    random_polygon,
    random_star_shaped_polygon,
)

sys.path.insert(0, os.getcwd())

from src.models import Point
from src.utils import validate_polygon_input

RANDOM_SEED = 0
STEP_SIZE = 5


def main():
    parser = argparse.ArgumentParser(
        description="Generate a polygon test suite for triangulation algorithm comparison."
    )
    parser.add_argument(
        "--min-points", type=int, default=5, help="Minimum number of polygon vertices"
    )
    parser.add_argument(
        "--max-points", type=int, default=100, help="Maximum number of polygon vertices"
    )
    parser.add_argument(
        "--n-per-size", type=int, default=5, help="Number of polygons per vertex count"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("testing_suite"), help="Output directory"
    )
    args = parser.parse_args()

    random.seed(RANDOM_SEED)

    if args.max_points > 100:
        print(
            f"Warning: --max-points={args.max_points} exceeds 100. "
            "random_polygon generation may be slow or fail for large n."
        )

    polygon_types = {
        "random_polygon": random_polygon,
        "star_shaped_polygon": random_star_shaped_polygon,
        "convex_polygon": random_convex_polygon,
    }

    # Create output directories
    for type_name in polygon_types.keys():
        (args.output_dir / type_name).mkdir(parents=True, exist_ok=True)

    # Generate testing suite
    for num_points in range(args.min_points, args.max_points + 1, STEP_SIZE):
        for i in range(args.n_per_size):
            for type_name, generator in polygon_types.items():
                while True:
                    # Note: 1. polygenerator generates counterclockwise polygons, so we
                    #          reverse them to clockwise order
                    #       2. polygenerator may generate polygons that are not simple, so we
                    #          validate and regenerate if necessary
                    polygon = generator(num_points=num_points)[::-1]
                    try:
                        validate_polygon_input([Point(x=x, y=y) for x, y in polygon])
                        break
                    except Exception:
                        continue

                with open(
                    args.output_dir / type_name / f"polygon_{num_points}_{i:04d}.txt", "w"
                ) as f:
                    f.write("\n".join(f"{x} {y}" for x, y in polygon))

    count = (
        args.n_per_size
        * len(polygon_types)
        * len(range(args.min_points, args.max_points + 1, STEP_SIZE))
    )
    print(f"Generated {count} polygons in {args.output_dir}")


if __name__ == "__main__":
    main()
