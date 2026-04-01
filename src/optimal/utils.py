from ..models import Point, PolygonVertex


def check_if_consective(v1: PolygonVertex, v2: PolygonVertex) -> bool:
    return v1.next == v2


def distance(p1: Point, p2: Point):
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


__all__ = ["check_if_consective", "distance"]
