from .point import Point
from .polygon import Polygon, PolygonVertex

type Triangle = tuple[int, int, int]
type Diagonal = tuple[int, int]


__all__ = ["Point", "PolygonVertex", "Polygon", "Triangle", "Diagonal"]
