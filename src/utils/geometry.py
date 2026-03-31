from ..constants import TOL
from ..models import Point


def orientation_check(p: Point, q: Point, r: Point) -> int:
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


def intersection_check(p1: Point, p2: Point, q1: Point, q2: Point) -> bool:
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
    o1 = orientation_check(p1, p2, q1)
    if o1 == 0 and q1 != p1 and q1 != p2 and _on_segment(p1, p2, q1):
        # q1 is on p1->p2
        return True

    # Orient of q2 w.r.t. p1->p2
    o2 = orientation_check(p1, p2, q2)
    if o2 == 0 and q2 != p1 and q2 != p2 and _on_segment(p1, p2, q2):
        # q2 is on p1->p2
        return True

    # Orient of p1 w.r.t. q1->q2
    o3 = orientation_check(q1, q2, p1)
    if o3 == 0 and p1 != q1 and p1 != q2 and _on_segment(q1, q2, p1):
        # p1 is on q1->q2
        return True

    # Orient of p2 w.r.t. q1->q2
    o4 = orientation_check(q1, q2, p2)
    if o4 == 0 and p2 != q1 and p2 != q2 and _on_segment(q1, q2, p2):
        # p2 is on q1->q2
        return True

    # If not shared endpoints and orientations are different, then they properly intersect
    # If o1 != o2 then q1 and q2 lie on opposite sides of p1->p2
    # If o3 != o4 then p1 and p2 lie on opposite sides of q1->q2
    if o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0 and o1 != o2 and o3 != o4:
        return True

    return False


def _cross_product(p: Point, q: Point, r: Point) -> float:
    """Returns the cross product of the vectors pq and pr"""
    return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)


def _on_segment(p: Point, q: Point, r: Point) -> bool:
    """Checks if r lies on segment pq, assuming p, q, r are collinear"""
    return (
        min(p.x, q.x) - TOL <= r.x <= max(p.x, q.x) + TOL
        and min(p.y, q.y) - TOL <= r.y <= max(p.y, q.y) + TOL
    )


__all__ = ["orientation_check", "intersection_check"]
