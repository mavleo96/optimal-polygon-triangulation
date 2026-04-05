from ..constants import TOL


class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point(x={self.x:.3f}, y={self.y:.3f})"

    def __str__(self):
        return f"({self.x:.3f}, {self.y:.3f})"

    def __eq__(self, other):
        return abs(self.x - other.x) < TOL and abs(self.y - other.y) < TOL


__all__ = ["Point"]
