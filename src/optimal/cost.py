from collections.abc import Callable

CostFn = Callable[[float | None, float | None, float | None], float | None]


def sum_length_cost(
    base_cost: float | None, left_subcost: float | None, right_subcost: float | None
) -> float:
    """
    Sum the length of base diagonal and the diagnols of left and right subtrees.
    """
    cost = 0
    if base_cost is not None:
        cost += base_cost
    if left_subcost is not None:
        cost += left_subcost
    if right_subcost is not None:
        cost += right_subcost
    return cost


def max_length_cost(
    base_cost: float | None, left_subcost: float | None, right_subcost: float | None
) -> float | None:
    """
    Return the max of base diagonal and the diagonals of left and right subtrees.
    """
    cands = []
    if base_cost is not None:
        cands.append(base_cost)
    if left_subcost is not None:
        cands.append(left_subcost)
    if right_subcost is not None:
        cands.append(right_subcost)
    return max(cands) if cands else None


def min_length_cost(
    base_cost: float | None, left_subcost: float | None, right_subcost: float | None
) -> float | None:
    """
    Return the max of neg of base diagonal and the diagonals of left and right subtrees.
    Note: To maximize the shortest diagonal, we negate distances and minimize
          This is equivalent to: max(d1, d2, ...) = -min(-d1, -d2, ...)
          Since _dp minimizes cost, negating converts maximization to minimization.
    """
    cands = []
    if base_cost is not None:
        cands.append(-base_cost)
    if left_subcost is not None:
        cands.append(left_subcost)
    if right_subcost is not None:
        cands.append(right_subcost)
    return max(cands) if cands else None


COST_FUNC_MAP = {
    "sum": sum_length_cost,
    "max": max_length_cost,
    "min": min_length_cost,
}

__all__ = ["COST_FUNC_MAP", "CostFn"]
