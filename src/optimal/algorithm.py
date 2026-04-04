import math

from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from .cost import COST_FUNC_MAP, CostFn
from .utils import check_if_valid_split, distance

_Cache = dict[tuple[int, int], tuple[float, int | None]]


def optimal_triangulation(polygon: Polygon, criteria: str) -> tuple[list[Triangle], list[Diagonal]]:
    splits_cache = {}  # (start, end) -> (cost, mid)
    cost_fn = COST_FUNC_MAP[criteria]
    _dp(0, len(polygon) - 1, polygon.vertices, splits_cache, cost_fn)
    return _backtrack(0, len(polygon) - 1, polygon.vertices, splits_cache)


def _dp(
    start: int, end: int, vertices: list[PolygonVertex], cache: _Cache, cost_fn: CostFn
) -> float | None:
    # Return cached result if available
    if (start, end) in cache:
        return cache[(start, end)][0]

    # Get the start and end vertices
    n = len(vertices)
    vstart = vertices[start]
    vend = vertices[end]

    # Base case: if consecutive, return None
    if vstart.next == vend:
        return None

    # Initialize best cost and best mid
    best_cost = math.inf
    best_mid = None

    # Get the base cost
    # Note: base_cost is None if (start, end) is a polygon edge
    #       polygon edges are excluded from all cost criteria.
    base_cost = distance(vstart.p, vend.p) if vend.next != vstart else None

    # Note: candidates in range (start, end) exclusive
    cand_length = (end - start - 1) if end > start else (n - start + end - 1)
    for i in range(cand_length):
        mid = (start + i + 1) % n
        vmid = vertices[mid]

        # Check if the split is valid
        if not check_if_valid_split(vstart, vmid, vend):
            continue

        # Get the left and right subtree costs
        left_subcost = _dp(start, mid, vertices, cache, cost_fn)
        right_subcost = _dp(mid, end, vertices, cache, cost_fn)

        # Compute the cost
        cost = cost_fn(base_cost, left_subcost, right_subcost)

        # Update the best cost and best mid if the current cost is better
        if cost is not None and cost <= best_cost:
            best_cost = cost
            best_mid = mid

    # Cache the result
    cache[(start, end)] = (best_cost, best_mid)

    return best_cost


def _backtrack(
    start: int, end: int, vertices: list[PolygonVertex], cache: _Cache
) -> tuple[list[Triangle], list[Diagonal]]:
    triangles = []
    diagonals = []

    vstart = vertices[start]
    vend = vertices[end]

    # If consecutive, return
    if vstart.next == vend:
        return triangles, diagonals

    # Get the best mid
    _, mid = cache[(start, end)]
    if mid is None:
        raise ValueError(f"No valid split for interval ({start}, {end})")

    # (start, end) is the base edge of this subproblem.
    # Add it as a diagonal if it is not a polygon edge.
    # Child calls will add their own base edges recursively.
    triangles.append((start, mid, end))
    if vend.next != vstart:
        diagonals.append((start, end))

    # Backtrack the left subtree; add the triangles and diagonals
    left_triangles, left_diagonals = _backtrack(start, mid, vertices, cache)
    triangles.extend(left_triangles)
    diagonals.extend(left_diagonals)

    # Backtrack the right subtree; add the triangles and diagonals
    right_triangles, right_diagonals = _backtrack(mid, end, vertices, cache)
    triangles.extend(right_triangles)
    diagonals.extend(right_diagonals)

    return triangles, diagonals


__all__ = ["optimal_triangulation"]
