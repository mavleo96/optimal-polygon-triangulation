from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from ..utils import valid_diagonal


def ear_init(head: PolygonVertex) -> list[int]:
    """
    Initialize ears for the ear clipping algorithm.
    Adapted from Computational geometry in C by Joseph O'Rourke.

    Args:
        head: Head of the polygon

    Returns:
        ears: List of ears
    """
    # Initialize ears list
    ears = []

    # Traverse the polygon
    curr = head
    while True:
        prev = curr.prev
        nxt = curr.next

        # If the diagonal is valid, set the ear to 1, otherwise 0
        ears.append(1 if valid_diagonal(prev, nxt) else 0)

        curr = curr.next
        if curr == head:
            break

    return ears


def ear_clipping_triangulate(polygon: Polygon) -> tuple[list[Triangle], list[Diagonal]]:
    """
    Ear clipping algorithm for polygon triangulation.
    Adapted from Computational geometry in C by Joseph O'Rourke.

    Args:
        polygon: Polygon to triangulate

    Returns:
        triangles: List of triangles
        diagonals: List of diagonals
    """
    assert len(polygon) >= 3, "Polygon must have at least 3 vertices"

    # Copy the polygon
    n = len(polygon)
    head = polygon.copy_chain()

    # Initialize ears
    ears = ear_init(head)

    # Triangulate
    triangles = []
    diagonals = []
    while n > 3:
        # Traverse the polygon
        v2 = head
        while 1:
            # If the vertex is an ear, chop it off
            if ears[v2.index]:
                v3 = v2.next
                v4 = v3.next
                v1 = v2.prev
                v0 = v1.prev

                # Add the triangle to the list
                triangles.append((v1.index, v2.index, v3.index))
                diagonals.append((v1.index, v3.index))

                # Update the ear status of prev and next vertices
                ears[v1.index] = valid_diagonal(v0, v3)
                ears[v3.index] = valid_diagonal(v1, v4)

                # Update the next and previous pointers
                v1.next = v3
                v3.prev = v1

                # Update the head
                head = v3
                n -= 1

            # Move to the next vertex
            v2 = v2.next

            # If we've looped back to the head, break
            if v2 == head:
                break

    # Add the last triangle
    triangles.append((head.prev.index, head.index, head.next.index))

    return triangles, diagonals
