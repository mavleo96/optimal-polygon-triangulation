from .point import Point
from .polygon import Polygon, PolygonVertex

Triangle = tuple[int, int, int]
Diagonal = tuple[int, int]


__all__ = ["Point", "PolygonVertex", "Polygon", "Triangle", "Diagonal"]
