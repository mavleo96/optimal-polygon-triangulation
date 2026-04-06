import matplotlib.pyplot as plt
from adjustText import adjust_text

from ..models import Diagonal, Polygon

COLOR_POLYGON = "#FDF8EC"  # warm ivory fill
COLOR_EDGE = "#3D2B00"  # dark brown (crisp edges)
COLOR_VERTEX = "#B8860B"  # dark goldenrod (dots)
COLOR_EAR = "#E63946"  # red (pops against gold)
COLOR_DIAGONAL = "#7A5C00"  # deep gold (dashed lines)

ARROWPROPS_VERTEX = dict(
    arrowstyle="->",
    color=COLOR_EDGE,
    lw=0.5,
    shrinkA=5,
    shrinkB=5,
)

ARROWPROPS_DIAGONAL = dict(
    arrowstyle="->",
    color=COLOR_DIAGONAL,
    lw=0.5,
    shrinkA=5,
    shrinkB=5,
)


def visualize_polygon(
    polygon: Polygon,
    ears: list[int] | None = None,
    diagonals: list[Diagonal] | None = None,
    title: str | None = None,
    **kwargs,
) -> plt.Axes:
    """
    Visualizes a polygon with optional ear highlighting and diagonal overlay.

    Args:
        polygon:   Polygon to visualize.
        ears:      List of integers, one per vertex — 1 if the vertex is an ear, 0 otherwise.
        diagonals: List of Diagonal pairs to draw as diagonals.
        title:     Optional plot title.

    Returns:
        The matplotlib axes where the polygon was drawn.
    """
    ax = kwargs.get("ax", None)
    fontsize = kwargs.get("fontsize", 7)
    linewidth = kwargs.get("linewidth", 1.2)
    vertex_size = kwargs.get("vertex_size", 20)
    diagonal_labels = kwargs.get("diagonal_labels", False)
    vertex_labels = kwargs.get("vertex_labels", False)

    n = len(polygon)
    xs = [v.p.x for v in polygon.vertices]
    ys = [v.p.y for v in polygon.vertices]

    if ax is None:
        figsize = kwargs.get("figsize", (4, 4))
        _, ax = plt.subplots(figsize=figsize)

    ax.set_aspect("equal")
    ax.axis("off")

    if title:
        ax.set_title(title, fontsize=fontsize * 1.5, pad=12)

    # polygon edges
    for i in range(n):
        j = (i + 1) % n
        ax.plot(
            [xs[i], xs[j]],
            [ys[i], ys[j]],
            COLOR_EDGE,
            linewidth=linewidth,
            zorder=1,
        )

    # Polygon interior color
    ax.fill(xs, ys, COLOR_POLYGON, zorder=2)

    # diagonals
    if diagonals:
        diagonal_texts = []
        for i, j in diagonals:
            a = polygon.vertices[i]
            b = polygon.vertices[j]
            ax.plot(
                [a.p.x, b.p.x],
                [a.p.y, b.p.y],
                COLOR_DIAGONAL,
                linewidth=linewidth * 0.75,
                linestyle="--",
                zorder=3,
            )
            if diagonal_labels:
                mid_x = (a.p.x + b.p.x) / 2
                mid_y = (a.p.y + b.p.y) / 2

                diagonal_texts.append(
                    ax.text(
                        mid_x,
                        mid_y,
                        f"({i},{j})",
                        fontsize=fontsize * 0.75,
                        color=COLOR_DIAGONAL,
                        ha="center",
                        va="center",
                    )
                )

        if diagonal_labels and diagonal_texts:
            adjust_text(
                diagonal_texts,
                ax=ax,
                expand_points=(1.5, 1.5),
                expand_text=(1.5, 1.5),
                arrowprops=ARROWPROPS_DIAGONAL,
            )

    # vertices — color by ear status
    if ears is not None:
        colors = [COLOR_EAR if e == 1 else COLOR_VERTEX for e in ears]
    else:
        colors = [COLOR_VERTEX] * n
    ax.scatter(xs, ys, c=colors, s=vertex_size, zorder=3)

    # vertex index labels
    if vertex_labels:
        vertex_texts = []
        for i in range(n):
            vertex_texts.append(
                ax.text(xs[i], ys[i], str(i), fontsize=fontsize, ha="center", va="center", zorder=4)
            )
        adjust_text(
            vertex_texts,
            ax=ax,
            expand_points=(1.5, 1.5),
            expand_text=(1.5, 1.5),
            arrowprops=ARROWPROPS_VERTEX,
        )

    return ax


__all__ = ["visualize_polygon"]
