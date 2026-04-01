import math

from ..models import Polygon, PolygonVertex
from ..utils import check_valid_diagonal
from .cost import COST_FUNC_MAP, CostFn
from .utils import check_if_consective


def optimal_triangulation(polygon: Polygon, criteria: str):
    cache = {}
    cost_fn = COST_FUNC_MAP[criteria]
    cost, optimal_diagonals = _dp(0, len(polygon) - 1, polygon.vertices, cache, cost_fn)
    return cost, optimal_diagonals


def _dp(start: int, end: int, vertices: list[PolygonVertex], cache: dict, cost_fn: CostFn):
    if (start, end) in cache:
        return cache[(start, end)]

    n = len(vertices)
    vstart = vertices[start]
    vend = vertices[end]

    # # Base case: the start and end are consecutive
    # if check_if_consective(vertices[start], vertices[end]):
    #     return 0, []

    best_cost = math.inf
    best_diagonals = []

    # Recursive case: find the optimal triangulation between the start and end
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

        diagonals = []
        subcosts = []

        if not consective_check1:
            left_subcost, left_diagonals = _dp(start, mid, vertices, cache, cost_fn)
            diagonals.extend(left_diagonals)
            subcosts.append(left_subcost)
            diagonals.append((start, mid))

        if not consective_check2:
            right_subcost, right_diagonals = _dp(mid, end, vertices, cache, cost_fn)
            diagonals.extend(right_diagonals)
            subcosts.append(right_subcost)
            diagonals.append((mid, end))

        cost = cost_fn(vstart, vmid, vend, subcosts)

        if cost < best_cost:
            best_cost = cost
            best_diagonals = diagonals

    cache.update({(start, end): (best_cost, best_diagonals)})
    return best_cost, best_diagonals


__all__ = ["optimal_triangulation"]
