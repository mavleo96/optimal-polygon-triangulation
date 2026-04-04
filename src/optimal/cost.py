import math
from collections.abc import Callable

CostFn = Callable[[float, float | None, float | None], float]


def sum_length_cost(
    base_cost: float, left_subcost: float | None, right_subcost: float | None
) -> float:
    """
    Sum the length of base diagonal and the diagnols of left and right subtrees.
    """
    cost = base_cost
    if left_subcost is not None:
        cost += left_subcost
    if right_subcost is not None:
        cost += right_subcost
    return cost


def max_length_cost(
    base_cost: float, left_subcost: float | None, right_subcost: float | None
) -> float:
    """
    Return the max of base diagonal and the diagonals of left and right subtrees.
    """
    cands = [base_cost]
    if left_subcost is not None:
        cands.append(left_subcost)
    if right_subcost is not None:
        cands.append(right_subcost)
    return max(cands) if cands else math.inf


def min_length_cost(
    base_cost: float, left_subcost: float | None, right_subcost: float | None
) -> float:
    """
    Return the max of neg of base diagonal and the diagonals of left and right subtrees.
    Note: we use negative to maximize the min cost.
    """
    cands = [-base_cost]
    if left_subcost is not None:
        cands.append(left_subcost)
    if right_subcost is not None:
        cands.append(right_subcost)
    return max(cands) if cands else math.inf


COST_FUNC_MAP = {
    "sum": sum_length_cost,
    "max": max_length_cost,
    "min": min_length_cost,
}

__all__ = ["COST_FUNC_MAP", "CostFn"]
