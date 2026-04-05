import math

from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from ..utils.geometry import check_valid_diagonal, distance
from .cost import COST_FUNC_MAP, CostFn

_Cache = dict[tuple[int, int], tuple[float, int | None]]


def optimal_triangulation(
    polygon: Polygon, criteria: str, return_cache: bool = False
) -> tuple[list[Triangle], list[Diagonal]] | tuple[list[Triangle], list[Diagonal], _Cache]:
    n = len(polygon)
    costs_cache = [[None] * n for _ in range(n)]
    splits_cache = [[None] * n for _ in range(n)]

    cost_fn = COST_FUNC_MAP[criteria]
    _dp(0, n - 1, polygon.vertices, splits_cache, costs_cache, cost_fn)

    if return_cache:
        return _backtrack(0, n - 1, polygon.vertices, splits_cache), (splits_cache, costs_cache)
    else:
        return _backtrack(0, n - 1, polygon.vertices, splits_cache)


def _dp(
    start: int,
    end: int,
    vertices: list[PolygonVertex],
    splits_cache: _Cache,
    costs_cache: _Cache,
    cost_fn: CostFn,
) -> float | None:
    # Return cached result if available
    if splits_cache[start][end] is not None:
        return costs_cache[start][end]

    # Get the start and end vertices
    n = len(vertices)
    vstart = vertices[start]
    vend = vertices[end]

    # Base case: subproblem is a polygon edge
    if vstart.next == vend:
        # Note: special cost None for edges
        splits_cache[start][end] = -1
        costs_cache[start][end] = None
        return None

    # If not valid split, return
    if not _is_edge(start, end, n) and not check_valid_diagonal(vstart, vend):
        splits_cache[start][end] = -1
        costs_cache[start][end] = math.inf
        return math.inf

    # Update the previous and next pointers
    # Note: Since vstart->vend is a valid diagonal, we can safely cut the polygon
    #       This makes checking valid diagonals faster in child calls.
    start_prev = vstart.prev
    end_next = vend.next
    vstart.prev = vend
    vend.next = vstart

    # Initialize best cost and best mid
    best_cost = math.inf
    best_mid = -1

    # Get the base cost
    # Note: base_cost is None if (start, end) is a polygon edge
    #       polygon edges are excluded from all cost criteria.
    base_cost = distance(vstart.p, vend.p) if not _is_edge(start, end, n) else None

    # Note: candidates in range (start, end) exclusive
    cand_length = (end - start - 1) if end > start else (n - start + end - 1)
    for i in range(cand_length):
        mid = (start + i + 1) % n

        # Get the left and right subtree costs
        left_subcost = _dp(start, mid, vertices, splits_cache, costs_cache, cost_fn)
        right_subcost = _dp(mid, end, vertices, splits_cache, costs_cache, cost_fn)

        # Compute the cost
        cost = cost_fn(base_cost, left_subcost, right_subcost)

        # Update the best cost and best mid if the current cost is better
        if cost is not None and cost < best_cost:
            best_cost = cost
            best_mid = mid

    # Cache the result
    splits_cache[start][end] = best_mid
    costs_cache[start][end] = best_cost

    # Restore the previous and next pointers
    vstart.prev = start_prev
    vend.next = end_next

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
    mid = cache[start][end]
    if mid == -1:
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


def _is_edge(start, end, n):
    return abs(start - end) == 1 or (start == 0 and end == n - 1)


__all__ = ["optimal_triangulation"]
