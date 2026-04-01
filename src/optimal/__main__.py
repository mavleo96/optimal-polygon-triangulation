import argparse

from ..models import Polygon
from ..utils import read_input, validate_polygon_input, validate_triangulation
from .algorithm import optimal_triangulation


def main():
    parser = argparse.ArgumentParser(description="Optimal algorithm for polygon triangulation")
    parser.add_argument("--input_file", type=str, help="Path to the input file")
    parser.add_argument("--output_file", type=str, help="Path to the output file")
    parser.add_argument(
        "--criteria",
        type=str,
        help="Criteria to use for the triangulation",
        choices=["min", "max", "sum"],
    )
    parser.add_argument("--validate", action="store_true", help="Validate the triangulation")
    args = parser.parse_args()

    # Parse and validate input
    vertices = read_input(args.input_file)
    validate_polygon_input(vertices)

    # Initialize polygon
    polygon = Polygon(vertices)

    # Triangulate
    _, diagonals = optimal_triangulation(polygon, args.criteria)

    # Validate triangulation
    if args.validate:
        validate_triangulation(polygon, diagonals)

    # Write output
    with open(args.output_file, "w") as f:
        f.write("\n".join([f"{i} {j}" for i, j in diagonals]) + "\n")


if __name__ == "__main__":
    main()
