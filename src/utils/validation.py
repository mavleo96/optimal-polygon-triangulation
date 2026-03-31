from ..models import Point
from .geometry import intersection_check


def validate_input(points: list[Point]) -> None:
    """
    Validates the input points.

    Checks:
    - A. vertex count check: n >= 3
    - B. no duplicate points
    - C. no self-intersections
    - D. clockwise check

    Args:
        points: List of points.
    """
    n = len(points)

    # A. vertex count check: n >= 3
    if n < 3:
        raise ValueError(f"Polygon must have at least 3 vertices, got {n}")

    # B. no duplicate points
    for i in range(n):
        for j in range(i + 1, n):
            if points[i] == points[j]:
                raise ValueError(f"Vertices {i} and {j} coincide — polygon is not simple")

    # C. no self-intersections
    # Note: pinch point case is handled by ensuring no duplicate points at check B.
    if not _check_self_intersections(points):
        raise ValueError("Polygon has self-intersections")

    # D. clockwise check
    if not _check_clockwise(points):
        raise ValueError("Polygon is not clockwise")


def _check_clockwise(points: list[Point]) -> bool:
    """
    Checks if the polygon defined by points is clockwise.
    Uses shoelace formula — signed area is negative for CW in y-up coordinates.
    O(n) area check.
    """
    n = len(points)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y - points[i].y * points[j].x
    return area < 0


def _check_self_intersections(points: list[Point]) -> bool:
    """
    Checks if the polygon defined by points has self-intersections.
    O(n²) edge pair check.
    """
    n = len(points)
    edges = [(points[i], points[(i + 1) % n]) for i in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            # Note: intersection_check will return False on shared endpoints.
            if intersection_check(edges[i][0], edges[i][1], edges[j][0], edges[j][1]):
                return False
    return True
