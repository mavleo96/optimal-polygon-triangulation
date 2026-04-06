import math

from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from ..utils.geometry import check_valid_diagonal, distance
from .cost import COST_FUNC_MAP, CostFn

_Cache = list[list[float | None]]


def optimal_triangulation(
    polygon: Polygon, criteria: str, return_cache: bool = False
) -> tuple[list[Triangle], list[Diagonal]] | tuple[list[Triangle], list[Diagonal], _Cache, _Cache]:
    """
    Optimal triangulation of a simple polygon using interval dynamic programming.

    Optimality is defined by the given criteria:
        - "minsum": minimize the total length of all diagonals
        - "minimax": minimize the length of the longest diagonal
        - "maximin": maximize the length of the shortest diagonal

    Time complexity:  O(n³)
    Space complexity: O(n²)

    Args:
        polygon:      Polygon to triangulate.
        criteria:     Optimality criterion.
        return_cache: If True, also returns the DP cache tables.

    Returns:
        (triangles, diagonals) if return_cache is False.
        (triangles, diagonals, (splits_cache, costs_cache)) if return_cache is True.

        triangles: n-2 triangles as (i, j, k) index triples.
        diagonals: n-3 diagonals as (i, j) index pairs, excluding polygon edges.
        splits_cache: n×n array where splits_cache[i][j] is the optimal split vertex
                      for subproblem (i, j).
        costs_cache:  n×n array where costs_cache[i][j] is the optimal cost
                      for subproblem (i, j).
    """
    assert len(polygon) >= 3, "Polygon must have at least 3 vertices"
    assert criteria in COST_FUNC_MAP, "Invalid criteria"

    n = len(polygon)
    cost_fn = COST_FUNC_MAP[criteria]

    # Initialize caches
    costs_cache = [[None] * n for _ in range(n)]
    splits_cache = [[None] * n for _ in range(n)]

    # Compute the optimal triangulation
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
    """
    Recursive memoized DP over polygon sub-arcs.

    Computes the optimal cost to triangulate the sub-polygon defined by the
    clockwise arc from vertices[start] to vertices[end], where (start, end)
    is either a polygon edge or a previously verified valid diagonal.

    To restrict diagonal validity checks to the current sub-arc (O(k) instead
    of O(n)), the linked list is temporarily modified: vend.next is set to
    vstart and vstart.prev is set to vend, making them adjacent. This is safe
    because (start, end) has already been verified as a valid diagonal, so
    the polygon can be cleanly split at this chord. Pointers are restored
    before returning.

    Cache sentinel values:
        splits_cache[i][j] = None  → subproblem not yet computed
        splits_cache[i][j] = -1    → base case (consecutive) or no valid split
        splits_cache[i][j] = k     → optimal split vertex is k

        costs_cache[i][j] = None      → base case (polygon edge, no diagonals)
        costs_cache[i][j] = math.inf  → no valid triangulation exists
        costs_cache[i][j] = float     → optimal cost

    Args:
        start:        Start vertex index of the sub-arc.
        end:          End vertex index of the sub-arc.
        vertices:     Full polygon vertex list.
        splits_cache: n×n memoization table for optimal split vertices.
        costs_cache:  n×n memoization table for optimal costs.
        cost_fn:      Cost function defining the optimality criterion.

    Returns:
        cost: Optimal cost for this subproblem, or None if (start, end) is a polygon edge.
    """
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

    # Early exit: (start, end) is not a polygon edge and not a valid diagonal —
    # this subproblem cannot be triangulated from the parent's context.
    if not _is_edge(start, end, n) and not check_valid_diagonal(vstart, vend):
        splits_cache[start][end] = -1
        costs_cache[start][end] = math.inf
        return math.inf

    # Temporarily restrict the linked list to the sub-arc [start, end].
    # This makes check_valid_diagonal in child calls traverse only sub-arc edges
    # (O(k)) rather than the full polygon (O(n)).
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

        left_subcost = _dp(start, mid, vertices, splits_cache, costs_cache, cost_fn)
        right_subcost = _dp(mid, end, vertices, splits_cache, costs_cache, cost_fn)

        cost = cost_fn(base_cost, left_subcost, right_subcost)

        if cost is not None and cost < best_cost:
            best_cost = cost
            best_mid = mid

    splits_cache[start][end] = best_mid
    costs_cache[start][end] = best_cost

    # Restore the linked list to its original state
    vstart.prev = start_prev
    vend.next = end_next

    return best_cost


def _backtrack(
    start: int, end: int, vertices: list[PolygonVertex], cache: _Cache
) -> tuple[list[Triangle], list[Diagonal]]:
    """
    Reconstructs the optimal triangulation by backtracking through the split table.

    Each call owns exactly one triangle (start, mid, end) and one diagonal
    (start, end) if it is not a polygon edge. Child calls recursively add their
    own triangles and diagonals for the left sub-arc (start, mid) and right
    sub-arc (mid, end).

    Args:
        start:    Start vertex index of the sub-arc.
        end:      End vertex index of the sub-arc.
        vertices: Full polygon vertex list.
        cache:    splits_cache table from _dp.

    Returns:
        triangles: n-2 triangles as (i, j, k) index triples.
        diagonals: n-3 diagonals as (i, j) index pairs, excluding polygon edges.

    Raises:
        ValueError: If cache[start][end] == -1 for a non-consecutive pair,
                    indicating no valid triangulation was found (should not
                    occur if _dp completed successfully).
    """
    triangles = []
    diagonals = []

    vstart = vertices[start]
    vend = vertices[end]

    if vstart.next == vend:
        return triangles, diagonals

    mid = cache[start][end]
    if mid == -1:
        raise ValueError(f"No valid split for interval ({start}, {end})")

    # This level owns triangle (start, mid, end) and diagonal (start, end)
    # if (start, end) is not a polygon edge. Child calls own their own base edges.
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


def _is_edge(start: int, end: int, n: int) -> bool:
    return abs(start - end) == 1 or (start == 0 and end == n - 1)


__all__ = ["optimal_triangulation"]
