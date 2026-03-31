from pathlib import Path

from ..models import Point


def read_input(file_path: str | Path) -> list[Point]:
    """
    Reads a text file and returns an ordered list of points.

    File format (one point per line):
        x1 y1
        x2 y2
        ...

    Args:
        file_path: Path to the input file.

    Returns:
        Ordered list of points.
    """
    lines = Path(file_path).read_text().splitlines()
    lines = [line.strip() for line in lines if line.strip()]

    points = []
    for i, line in enumerate(lines, start=1):
        coords = line.split()
        if len(coords) != 2:
            raise ValueError(f"Line {i}: expected 2 coordinates, got {len(coords)}: '{line}'")
        points.append(Point(float(coords[0]), float(coords[1])))

    return points


__all__ = ["read_input"]
