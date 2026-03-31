import argparse

from ..models import Polygon
from ..utils import read_input, validate_input
from .algorithm import ear_clipping_triangulate


def main():
    parser = argparse.ArgumentParser(description="Ear clipping algorithm for polygon triangulation")
    parser.add_argument("--input_file", type=str, help="Path to the input file")
    parser.add_argument("--output_file", type=str, help="Path to the output file")
    args = parser.parse_args()

    # Parse and validate input
    vertices = read_input(args.input_file)
    validate_input(vertices)

    # Initialize polygon
    polygon = Polygon(vertices)

    # Triangulate
    triangles, _ = ear_clipping_triangulate(polygon)

    # Write output
    with open(args.output_file, "w") as f:
        for triangle in triangles:
            f.write(f"{triangle[0].index} {triangle[1].index} {triangle[2].index}\n")


if __name__ == "__main__":
    main()
