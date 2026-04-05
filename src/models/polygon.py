from .point import Point


class PolygonVertex:
    def __init__(
        self, index: int, point: Point, next: "PolygonVertex" = None, prev: "PolygonVertex" = None
    ):
        self.index = index
        self.p = point
        self.next = next
        self.prev = prev

    def __repr__(self):
        return f"PolygonVertex(index={self.index}, point={self.p})"

    def __str__(self):
        return f"({self.p.x:.3f}, {self.p.y:.3f})"


class Polygon:
    def __init__(self, vertices: list[Point]):
        self.n = len(vertices)
        self.head, self.vertices = self._build(vertices)
        self.edges = self._build_edges(self.vertices)

    @staticmethod
    def _build(points: list[Point]) -> tuple[PolygonVertex, list[PolygonVertex]]:
        n = len(points)
        vertex_list = [PolygonVertex(i, p) for i, p in enumerate(points)]

        for i in range(n):
            vertex_list[i].next = vertex_list[(i + 1) % n]
            vertex_list[i].prev = vertex_list[(i - 1) % n]

        return vertex_list[0], vertex_list

    @staticmethod
    def _build_edges(vertices: list[PolygonVertex]) -> list[tuple[Point, Point]]:
        return [(v.p, v.next.p) for v in vertices]

    def copy_chain(self) -> PolygonVertex:
        new_head = PolygonVertex(self.head.index, self.head.p)

        curr = self.head
        new_curr = new_head
        while curr.next != self.head:
            new_curr.next = PolygonVertex(curr.next.index, curr.next.p)
            new_curr.next.prev = new_curr
            curr = curr.next
            new_curr = new_curr.next

        # Close the chain
        new_curr.next = new_head
        new_head.prev = new_curr

        return new_head

    def __repr__(self):
        return f"Polygon(head={self.head}, vertices={self.vertices})"

    def __str__(self):
        return f"{' -> '.join([str(v) for v in self.vertices])}"

    def __len__(self):
        return self.n


__all__ = ["PolygonVertex", "Polygon"]
