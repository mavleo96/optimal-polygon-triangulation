import math
from collections.abc import Callable

from ..models import PolygonVertex
from .utils import check_if_consective, distance

CostFn = Callable[[PolygonVertex, PolygonVertex, PolygonVertex, list[float]], float]


def sum_length_cost(
    v1: PolygonVertex, v2: PolygonVertex, v3: PolygonVertex, subcosts: list[float]
) -> float:
    cost = 0
    if not check_if_consective(v1, v2):
        cost += distance(v1.p, v2.p)
    if not check_if_consective(v2, v3):
        cost += distance(v2.p, v3.p)
    cost += sum(subcosts)
    return cost


def max_length_cost(
    v1: PolygonVertex, v2: PolygonVertex, v3: PolygonVertex, subcosts: list[float]
) -> float:
    cost = -math.inf
    if not check_if_consective(v1, v2):
        cost = max(cost, distance(v1.p, v2.p))
    if not check_if_consective(v2, v3):
        cost = max(cost, distance(v2.p, v3.p))
    cost = max([cost, *subcosts])
    return cost


def min_length_cost(
    v1: PolygonVertex, v2: PolygonVertex, v3: PolygonVertex, subcosts: list[float]
) -> float:
    cost = -math.inf
    if not check_if_consective(v1, v2):
        cost = max(cost, -distance(v1.p, v2.p))
    if not check_if_consective(v2, v3):
        cost = max(cost, -distance(v2.p, v3.p))
    cost = max([cost, *subcosts])
    return cost


COST_FUNC_MAP = {
    "sum": sum_length_cost,
    "max": max_length_cost,
    "min": min_length_cost,
}

__all__ = ["COST_FUNC_MAP"]
