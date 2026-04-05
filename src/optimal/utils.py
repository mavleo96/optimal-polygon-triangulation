from ..models import PolygonVertex
from ..utils.geometry import check_valid_diagonal


def check_if_valid_split(vstart: PolygonVertex, vmid: PolygonVertex, vend: PolygonVertex) -> bool:
    """
    Checks if polygon can be split into valid subproblems

    1. Check if start->mid is a valid diagonal if not an edge
    2. Check if mid->end is a valid diagonal if not an edge
    """
    # Check if diagonal start->mid is valid if not an edge
    if vstart.next != vmid and not check_valid_diagonal(vstart, vmid):
        return False

    # Check if diagonal mid->end is valid if not an edge
    if vmid.next != vend and not check_valid_diagonal(vmid, vend):
        return False

    return True


__all__ = ["check_if_valid_split"]
