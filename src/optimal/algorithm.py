import math

from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from ..utils import check_valid_diagonal
from .cost import COST_FUNC_MAP, CostFn
from .utils import check_if_consective


def optimal_triangulation(polygon: Polygon, criteria: str) -> tuple[list[Triangle], list[Diagonal]]:
    splits_cache = {}  # (start, end) -> (cost, mid)
    cost_fn = COST_FUNC_MAP[criteria]
    _dp(0, len(polygon) - 1, polygon.vertices, splits_cache, cost_fn)

    triangles, diagonals = _backtrack(0, len(polygon) - 1, polygon.vertices, splits_cache)

    return triangles, diagonals


def _backtrack(
    start: int, end: int, vertices: list[PolygonVertex], cache: dict
) -> tuple[list[Triangle], list[Diagonal]]:
    triangles = []
    diagonals = []

    vstart = vertices[start]
    vend = vertices[end]

    if check_if_consective(vstart, vend):
        return triangles, diagonals

    _, mid = cache[(start, end)]
    vmid = vertices[mid]

    if not check_if_consective(vstart, vmid):
        left_triangles, left_diagonals = _backtrack(start, mid, vertices, cache)
        triangles.extend(left_triangles)
        diagonals.extend(left_diagonals)
        diagonals.append((start, mid))

    triangles.append((start, mid, end))

    if not check_if_consective(vmid, vend):
        right_triangles, right_diagonals = _backtrack(mid, end, vertices, cache)
        triangles.extend(right_triangles)
        diagonals.extend(right_diagonals)
        diagonals.append((mid, end))

    return triangles, diagonals


def _dp(start: int, end: int, vertices: list[PolygonVertex], cache: dict, cost_fn: CostFn) -> float:
    # Return cached result if it exists
    if (start, end) in cache:
        return cache[(start, end)][0]

    # Get the start and end vertices
    n = len(vertices)
    vstart = vertices[start]
    vend = vertices[end]

    # Iterate over all possible candidates for the middle vertex

    best_cost = math.inf
    best_mid = None
    # Note: candidates in range (start, end) exclusive
    cand_length = (end - start - 1) if end > start else (n - start + end - 1)
    for i in range(cand_length):
        mid = (start + i + 1) % n
        vmid = vertices[mid]

        # Check if diag start->mid is valid if not an edge
        consective_check1 = check_if_consective(vstart, vmid)
        diagonal_check1 = check_valid_diagonal(vstart, vmid)
        if not consective_check1 and not diagonal_check1:
            continue

        # Check if diag mid->end is valid if not an edge
        diagonal_check2 = check_valid_diagonal(vmid, vend)
        consective_check2 = check_if_consective(vmid, vend)
        if not consective_check2 and not diagonal_check2:
            continue

        subcosts = []

        if not consective_check1:
            left_subcost = _dp(start, mid, vertices, cache, cost_fn)
            subcosts.append(left_subcost)

        if not consective_check2:
            right_subcost = _dp(mid, end, vertices, cache, cost_fn)
            subcosts.append(right_subcost)

        cost = cost_fn(vstart, vmid, vend, subcosts)

        if cost < best_cost:
            best_cost = cost
            best_mid = mid

    cache.update({(start, end): (best_cost, best_mid)})
    return best_cost


__all__ = ["optimal_triangulation"]
