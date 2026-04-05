from ..constants import TOL
from ..models import Point, PolygonVertex


def check_orientation(p: Point, q: Point, r: Point) -> int:
    """
    Returns 1 if left turn, -1 if right turn, 0 if collinear

    Args:
        p: First point.
        q: Second point.
        r: Third point.

    Returns:
        Returns 1 if left turn, -1 if right turn, 0 if collinear.
    """
    cp = _cross_product(p, q, r)
    if abs(cp) < TOL:
        return 0
    elif cp > 0:
        return 1
    else:
        return -1


def check_intersection(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
    """
    Checks if segments p1->p2 and q1->q2 properly intersect.
    Note: 1. shared endpoints are not considered as intersections.
          2. endpoint on segment is considered as intersection.

    Args:
        p1: First endpoint of segment p1->p2.
        p2: Second endpoint of segment p1->p2.
        q1: First endpoint of segment q1->q2.
        q2: Second endpoint of segment q1->q2.

    Returns:
        True if the segments properly intersect, False otherwise.
    """
    # Orient of q1 w.r.t. p1->p2
    o1 = check_orientation(p1, p2, q1)
    if o1 == 0 and q1 != p1 and q1 != p2 and _on_segment(p1, p2, q1):
        # q1 is on p1->p2
        return True

    # Orient of q2 w.r.t. p1->p2
    o2 = check_orientation(p1, p2, q2)
    if o2 == 0 and q2 != p1 and q2 != p2 and _on_segment(p1, p2, q2):
        # q2 is on p1->p2
        return True

    # Orient of p1 w.r.t. q1->q2
    o3 = check_orientation(q1, q2, p1)
    if o3 == 0 and p1 != q1 and p1 != q2 and _on_segment(q1, q2, p1):
        # p1 is on q1->q2
        return True

    # Orient of p2 w.r.t. q1->q2
    o4 = check_orientation(q1, q2, p2)
    if o4 == 0 and p2 != q1 and p2 != q2 and _on_segment(q1, q2, p2):
        # p2 is on q1->q2
        return True

    # If not shared endpoints and orientations are different, then they properly intersect
    # If o1 != o2 then q1 and q2 lie on opposite sides of p1->p2
    # If o3 != o4 then p1 and p2 lie on opposite sides of q1->q2
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0 and o1 != o2 and o3 != o4:
        return True

    return False


def check_valid_diagonal(v1: PolygonVertex, v2: PolygonVertex) -> bool:
    """
    Checks if v1->v2 is a valid diagonal.

    Checks:
        1. v1->v2 is inside cone v1->v1.next and v1->v1.prev
        2. v2->v1 is inside cone v2->v2.next and v2->v2.prev
        3. v1->v2 does not intersect any other edge

    Args:
        v1: First vertex.
        v2: Second vertex.

    Returns:
        True if v1->v2 is a valid diagonal, False otherwise.
    """
    # INCONE CHECKS

    # A. check v1->v2 is inside cone v1->v1.next and v1->v1.prev
    v1_prev = v1.prev
    v1_next = v1.next

    # check 1: v2 vs v1->v1.next
    check1 = check_orientation(v1.p, v1_next.p, v2.p)
    # check 2: v2 vs v1->v1.prev
    check2 = check_orientation(v1_prev.p, v1.p, v2.p)

    # if v1 is convex / collinear, then check1 and check2 should be right turns
    if check_orientation(v1_prev.p, v1.p, v1_next.p) <= 0:
        in_cone = check1 == -1 and check2 == -1
    # if v1 is reflex, then check1 and check2 should be both left turns
    else:
        in_cone = not (check1 == 1 and check2 == 1)

    if not in_cone:
        return False

    # B. check v2->v1 is inside cone v2->v2.next and v2->v2.prev
    v2_prev = v2.prev
    v2_next = v2.next

    # check 1: v1 vs v2->v2.next
    check1 = check_orientation(v2.p, v2_next.p, v1.p)
    # check 2: v1 vs v2->v2.prev
    check2 = check_orientation(v2_prev.p, v2.p, v1.p)

    # if v2 is convex / collinear, then check1 and check2 should be right turns
    if check_orientation(v2_prev.p, v2.p, v2_next.p) <= 0:
        in_cone_opp = check1 == -1 and check2 == -1
    # if v2 is reflex, then check1 and check2 should be both left turns
    else:
        in_cone_opp = not (check1 == 1 and check2 == 1)

    if not in_cone_opp:
        return False

    # POLYGON INTERSECT CHECK

    curr = v1
    nxt = v1.next
    while True:
        # check if curr->nxt intersects v1->v2
        if check_intersection(curr.p, nxt.p, v1.p, v2.p):
            return False

        # move to next edge
        curr = nxt
        nxt = nxt.next

        # break on loop back to start
        if curr == v1:
            break

    return True


def distance(p1: Point, p2: Point) -> float:
    """Returns the euclidean distance between two points"""
    return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5


def _cross_product(p: Point, q: Point, r: Point) -> float:
    """Returns the cross product of the vectors pq and pr"""
    return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """Checks if r lies on segment pq, assuming p, q, r are collinear"""
    return (
        min(p.x, q.x) - TOL <= r.x <= max(p.x, q.x) + TOL
        and min(p.y, q.y) - TOL <= r.y <= max(p.y, q.y) + TOL
    )


__all__ = ["check_orientation", "check_intersection", "check_valid_diagonal"]
