from ..models import Diagonal, Polygon, PolygonVertex, Triangle
from ..utils.geometry import check_valid_diagonal


def init_ears(head: PolygonVertex) -> list[int]:
    """
    Initialize ears for the ear clipping algorithm.
    A vertex is an ear if the diagonal between its neighbors is valid.
    Adapted from Computational geometry in C by Joseph O'Rourke.

    Args:
        head: Head of the polygon

    Returns:
        ears: List of ears
    """
    assert head.index == 0, "Head must be the first vertex"

    # Initialize ears list
    ears = []

    # Traverse the polygon
    curr = head
    while True:
        prev = curr.prev
        nxt = curr.next

        # If the diagonal is valid, set the ear to 1, otherwise 0
        ears.append(1 if check_valid_diagonal(prev, nxt) else 0)

        curr = curr.next
        if curr == head:
            break

    return ears


def ear_clipping_triangulation(polygon: Polygon) -> tuple[list[Triangle], list[Diagonal]]:
    """
    Ear clipping algorithm for simple polygon triangulation.
    Adapted from Computational geometry in C by Joseph O'Rourke.

    Time complexity: O(n²). Does not mutate the input polygon.
    Space complexity: O(n).

    Args:
        polygon: Polygon to triangulate

    Returns:
        triangles: n-2 triangles as (i, j, k) index triples.
        diagonals: n-3 diagonals as (i, j) index pairs, excluding polygon edges.
    """
    assert len(polygon) >= 3, "Polygon must have at least 3 vertices"

    # Copy the polygon
    n = len(polygon)
    head = polygon.copy_chain()

    # Initialize ears
    ears = init_ears(head)

    # Triangulate
    triangles = []
    diagonals = []
    # outer loop: repeats until only a triangle remains
    while n > 3:
        # inner loop: scans for the next ear starting from head
        v2 = head
        while 1:
            # If the vertex is an ear, chop it off
            if ears[v2.index]:
                v3 = v2.next
                v4 = v3.next
                v1 = v2.prev
                v0 = v1.prev

                triangles.append((v1.index, v2.index, v3.index))
                diagonals.append((v1.index, v3.index))

                # Only v1 and v3 may have changed ear status — their neighbor
                # structure changed when v2 was removed from the linked list.
                ears[v1.index] = check_valid_diagonal(v0, v3)
                ears[v3.index] = check_valid_diagonal(v1, v4)

                v1.next = v3
                v3.prev = v1

                head = v3
                n -= 1

            # Move to the next vertex
            v2 = v2.next

            # If we've looped back to the head, break
            if v2 == head:
                break

    # Remaining three vertices form the last triangle — no diagonal added.
    triangles.append((head.prev.index, head.index, head.next.index))

    return triangles, diagonals


__all__ = ["ear_clipping_triangulation", "init_ears"]
