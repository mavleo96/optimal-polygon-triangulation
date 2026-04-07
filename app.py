import io
import math
import os
import sys

import matplotlib
import pandas as pd
import plotly.graph_objects as go

matplotlib.use("Agg")
import gradio as gr
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ear_clipping.algorithm import ear_clipping_triangulation
from src.models import Point, Polygon
from src.optimal.algorithm import optimal_triangulation
from src.utils.geometry import distance
from src.utils.io import read_input
from src.utils.validation import validate_polygon_input

# ── Constants ─────────────────────────────────────────────────────────────────

DATA_MAX = 10.0
CANVAS_PX = 500

C_BG = "#F8F8F0"
C_POLYGON = "#FDF8EC"
C_EDGE = "#3D2B00"
C_VERTEX = "#B8860B"
C_DIAGONAL = "#7A5C00"
C_ACTIVE = "#1565C0"

# DP table: state codes written by _precompute_anim_states and read by make_dp_table_figure
_ST_PENDING = 0
_ST_ACTIVE = 1  # "enter" event — subproblem in progress
_ST_OPTIMAL = 2  # "exit" with valid split
_ST_EXPLORED = 3  # "exit" with no valid split
_ST_INVALID = 4  # diagonal is geometrically invalid
_ST_DIAG = 5  # diagonal cell (i == j) — not a DP state
_ST_LOWER = 6  # lower-triangle cell — not a DP state
_ST_EDGE = 7  # consecutive polygon edge — not a DP state
_ST_CURR = 8  # currently active cell

# Cell background and text colors indexed by state code (light theme)
_DP_BG = [
    "#f1f2f8",  # 0 pending
    "#dbeafe",  # 1 in-stack
    "#dcfce7",  # 2 optimal
    "#fef9c3",  # 3 explored
    "#fee2e2",  # 4 invalid
    "#f4f5fb",  # 5 diagonal
    "#f8f9fc",  # 6 lower triangle (matches bg — hidden)
    "#f0fdf4",  # 7 polygon edge
    "#2563eb",  # 8 active
]
_DP_TC = [
    "#9ca3af",  # pending    — recedes
    "#1e40af",  # in-stack   — dark blue
    "#15803d",  # optimal    — dark green
    "#854d0e",  # explored   — dark amber
    "#991b1b",  # invalid    — dark red
    "#cbd5e1",  # diagonal   — subtle
    "#f8f9fc",  # lower      — invisible
    "#16a34a",  # edge       — green
    "#ffffff",  # active     — white
]
# Discrete step colorscale: integer z=k maps to _DP_BG[k]; precomputed once
_DP_COLORSCALE = [[0.0, _DP_BG[0]]]
for _k in range(8):
    _mid = (_k + 0.5) / 8
    _DP_COLORSCALE += [[_mid - 1e-9, _DP_BG[_k]], [_mid, _DP_BG[_k + 1]]]
_DP_COLORSCALE.append([1.0, _DP_BG[8]])

_CSS = """
.canvas-img .image-container,
.canvas-img .upload-container,
.canvas-img .wrap,
.canvas-img figure { background: #F8F8F0 !important; }
.narration-box { min-height: 54px; }
.narration-box > div { min-height: 54px; }
"""

# ── Helpers ───────────────────────────────────────────────────────────────────


def _fmt(v) -> str:
    if v is None:
        return "-"
    if math.isinf(v):
        return "∞"
    return f"{v:.3f}"


def _fmt_cost(v) -> str:
    """Format a DP cost for display in the table (2 d.p., empty string for None)."""
    if v is None:
        return ""
    if isinstance(v, float) and math.isinf(v):
        return "∞"
    return f"{v:.2f}"


def _points_info(pts: list) -> str:
    if not pts:
        return ""
    return "\n".join(
        [f"n = {len(pts)} vertices"]
        + [f"  {i}: ({p[0]:.2f}, {p[1]:.2f})" for i, p in enumerate(pts)]
    )


def _diag_lengths(polygon: Polygon, diagonals: list) -> list[float]:
    return [distance(polygon.vertices[i].p, polygon.vertices[j].p) for i, j in diagonals]


def _is_polygon_edge(a: int, b: int, n: int) -> bool:
    return abs(a - b) == 1 or (a == 0 and b == n - 1) or (b == 0 and a == n - 1)


def _polygon_coords(polygon: Polygon) -> tuple[list, list]:
    return [v.p.x for v in polygon.vertices], [v.p.y for v in polygon.vertices]


def _fig_to_image(fig, tight: bool = False) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, **({"bbox_inches": "tight"} if tight else {}))
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).copy()


def build_polygon(pts: list) -> Polygon:
    points = [Point(p[0], p[1]) for p in pts]
    validate_polygon_input(points)
    return Polygon(points)


# ── Tab 1: canvas rendering ───────────────────────────────────────────────────


def _make_canvas_image(pts: list, finished: bool = False) -> Image.Image:
    fig = plt.figure(figsize=(CANVAS_PX / 100, CANVAS_PX / 100), facecolor=C_BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, DATA_MAX)
    ax.set_ylim(0, DATA_MAX)
    ax.set_facecolor(C_BG)
    ax.axis("off")

    n = len(pts)

    # polygon fill (3+ points only)
    if n >= 3:
        ax.add_patch(MplPolygon(pts, closed=True, fc=C_POLYGON, ec=None, zorder=1))

    # edges between consecutive vertices
    if n >= 2:
        for i in range(n - 1):
            ax.plot(
                [pts[i][0], pts[i + 1][0]],
                [pts[i][1], pts[i + 1][1]],
                color=C_EDGE,
                lw=1.8,
                zorder=2,
            )

    # closing edge — solid if finished, dashed preview otherwise
    if n >= 3:
        ax.plot(
            [pts[-1][0], pts[0][0]],
            [pts[-1][1], pts[0][1]],
            color=C_EDGE,
            zorder=2,
            **(dict(lw=1.8) if finished else dict(lw=1, ls="--", alpha=0.4)),
        )

    # vertices + labels
    for i, p in enumerate(pts):
        ax.scatter(p[0], p[1], c=C_VERTEX, s=60, zorder=4)
        ax.annotate(
            str(i),
            (p[0], p[1]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=9,
            fontweight="bold",
            color=C_EDGE,
        )

    return _fig_to_image(fig)


# ── Tab 3: triangulation figure ───────────────────────────────────────────────


def make_triangulation_figure(polygon: Polygon, triangles: list, diagonals: list) -> go.Figure:
    xs, ys = _polygon_coords(polygon)
    n = len(xs)
    fig = go.Figure()

    # triangle fills
    fill_x, fill_y = [], []
    for tri in triangles:
        for k in range(3):
            fill_x.append(xs[tri[k]])
            fill_y.append(ys[tri[k]])
        fill_x += [xs[tri[0]], None]
        fill_y += [ys[tri[0]], None]
    if fill_x:
        fig.add_trace(
            go.Scatter(
                x=fill_x,
                y=fill_y,
                fill="toself",
                fillcolor="rgba(253,248,236,0.85)",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    _add_polygon_edges(fig, xs, ys, n, width=1.8)

    # diagonals
    diag_x, diag_y = [], []
    for i, j in diagonals:
        diag_x += [xs[i], xs[j], None]
        diag_y += [ys[i], ys[j], None]
    if diag_x:
        fig.add_trace(
            go.Scatter(
                x=diag_x,
                y=diag_y,
                mode="lines",
                line=dict(color=C_DIAGONAL, width=1.2, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(color=C_VERTEX, size=7),
            text=[str(i) for i in range(n)],
            textposition="top right",
            textfont=dict(size=8, color=C_EDGE),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        xaxis=dict(range=[0, DATA_MAX], visible=False, fixedrange=True),
        yaxis=dict(range=[0, DATA_MAX], visible=False, scaleanchor="x", fixedrange=True),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=5, r=5, t=35, b=5),
        showlegend=False,
        dragmode=False,
    )
    return fig


# ── Tab 2: animation helpers ──────────────────────────────────────────────────


def _precompute_anim_states(trace: list, n: int) -> list[tuple]:
    """
    Precompute the full DP state sequence once after _run.
    Returns a list of (dp_state, dp_cost, dp_splits) snapshots — one per trace step.
    Each snapshot is a shallow-copy of the evolving state at that step, built
    incrementally in O(total_events) total instead of O(total_events²).
    """
    dp_state = [[0] * n for _ in range(n)]
    dp_cost = [[None] * n for _ in range(n)]
    dp_splits = [[None] * n for _ in range(n)]
    snapshots = []
    for e in trace:
        ea, eb, et = e["start"], e["end"], e["event"]
        if et == "invalid":
            dp_state[ea][eb] = _ST_INVALID
            dp_cost[ea][eb] = math.inf
        elif et == "enter":
            dp_state[ea][eb] = _ST_ACTIVE
        elif et == "exit":
            dp_cost[ea][eb] = e.get("best_cost")
            dp_splits[ea][eb] = e.get("best_mid", -1)
            dp_state[ea][eb] = _ST_OPTIMAL if dp_splits[ea][eb] != -1 else _ST_EXPLORED
        snapshots.append(
            (
                [row[:] for row in dp_state],
                [row[:] for row in dp_cost],
                [row[:] for row in dp_splits],
            )
        )
    return snapshots


def _reconstruct_arc_tris(
    a: int,
    b: int,
    n: int,
    dp_splits: list,
    dp_state: list,
    _memo: dict = None,
) -> list[tuple]:
    if _memo is None:
        _memo = {}
    key = (a, b)
    if key in _memo:
        return _memo[key]
    if _is_polygon_edge(a, b, n) or dp_state[a][b] not in (2, 3):
        return _memo.setdefault(key, [])
    mid = dp_splits[a][b]
    if mid is None or mid == -1:
        return _memo.setdefault(key, [])
    result = (
        [(a, mid, b)]
        + _reconstruct_arc_tris(a, mid, n, dp_splits, dp_state, _memo)
        + _reconstruct_arc_tris(mid, b, n, dp_splits, dp_state, _memo)
    )
    _memo[key] = result
    return result


def _add_polygon_edges(fig: go.Figure, xs: list, ys: list, n: int, width: float) -> None:
    ex, ey = [], []
    for i in range(n):
        j = (i + 1) % n
        ex += [xs[i], xs[j], None]
        ey += [ys[i], ys[j], None]
    fig.add_trace(
        go.Scatter(
            x=ex,
            y=ey,
            mode="lines",
            line=dict(color=C_EDGE, width=width),
            showlegend=False,
            hoverinfo="skip",
        )
    )


def _build_arc(a: int, b: int, n: int) -> list[int]:
    arc, cur = [], a
    while True:
        arc.append(cur)
        if cur == b:
            break
        cur = (cur + 1) % n
    return arc


def _add_arc_fill(fig: go.Figure, xs: list, ys: list, arc: list[int], fillcolor: str) -> None:
    fig.add_trace(
        go.Scatter(
            x=[xs[v] for v in arc] + [xs[arc[0]]],
            y=[ys[v] for v in arc] + [ys[arc[0]]],
            fill="toself",
            fillcolor=fillcolor,
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )


def _make_poly_figure(
    xs,
    ys,
    n,
    a,
    b,
    ev,
    event,
    stack_frames,
    dp_cost,
    dp_splits,
    dp_state,
) -> go.Figure:
    fig = go.Figure()
    arc = _build_arc(a, b, n)
    arc_set = set(arc)

    stack_pairs = [s for s in stack_frames if s != (a, b)]
    stack_diags = [(sa, sb) for sa, sb in stack_pairs if not _is_polygon_edge(sa, sb, n)]
    held_left_diags: list[tuple] = []
    if stack_pairs:
        pa, pb = stack_pairs[-1]
        if pb == b and pa != a and not _is_polygon_edge(pa, a, n):
            held_left_diags = [(pa, a)]

    # polygon background
    fig.add_trace(
        go.Scatter(
            x=xs + [xs[0]],
            y=ys + [ys[0]],
            fill="toself",
            fillcolor=C_POLYGON,
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # ancestor arc fills
    for depth, (pa, pb) in enumerate(stack_pairs):
        anc_arc = _build_arc(pa, pb, n)
        if len(anc_arc) >= 3:
            alpha = max(0.02, 0.07 - depth * 0.015)
            _add_arc_fill(fig, xs, ys, anc_arc, f"rgba(21,101,192,{alpha:.3f})")

    if ev == "try_mid":
        mid = event["mid"]
        cost = event.get("cost")
        is_valid_split = cost is not None and not math.isinf(cost)
        left_arc = _build_arc(a, mid, n)
        right_arc = _build_arc(mid, b, n)
        if len(left_arc) >= 2:
            _add_arc_fill(fig, xs, ys, left_arc, "rgba(76,175,80,0.22)")
        if len(right_arc) >= 2:
            _add_arc_fill(fig, xs, ys, right_arc, "rgba(255,152,0,0.22)")
        if is_valid_split:
            fig.add_trace(
                go.Scatter(
                    x=[xs[a], xs[mid], xs[b], xs[a]],
                    y=[ys[a], ys[mid], ys[b], ys[a]],
                    fill="toself",
                    fillcolor="#FFE082",
                    line=dict(color="#F57F17", width=2),
                    opacity=0.75,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    elif ev == "exit":
        arc_tris = _reconstruct_arc_tris(a, b, n, dp_splits, dp_state)
        if arc_tris:
            tri_x, tri_y = [], []
            for ta, tm, tb in arc_tris:
                tri_x += [xs[ta], xs[tm], xs[tb], xs[ta], None]
                tri_y += [ys[ta], ys[tm], ys[tb], ys[ta], None]
            fig.add_trace(
                go.Scatter(
                    x=tri_x,
                    y=tri_y,
                    fill="toself",
                    fillcolor="rgba(46,125,50,0.20)",
                    line=dict(color="#2E7D32", width=1.2),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        elif len(arc) >= 3:
            _add_arc_fill(fig, xs, ys, arc, "rgba(21,101,192,0.07)")

    elif ev == "cache_hit":
        arc_tris = _reconstruct_arc_tris(a, b, n, dp_splits, dp_state)
        if arc_tris:
            tri_x, tri_y = [], []
            for ta, tm, tb in arc_tris:
                tri_x += [xs[ta], xs[tm], xs[tb], xs[ta], None]
                tri_y += [ys[ta], ys[tm], ys[tb], ys[ta], None]
            fig.add_trace(
                go.Scatter(
                    x=tri_x,
                    y=tri_y,
                    fill="toself",
                    fillcolor="rgba(38,166,154,0.18)",
                    line=dict(color="#26A69A", width=1.2),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        elif len(arc) >= 3:
            _add_arc_fill(fig, xs, ys, arc, "rgba(38,166,154,0.07)")

    elif ev == "enter" and len(arc) >= 3:
        _add_arc_fill(fig, xs, ys, arc, "rgba(21,101,192,0.07)")

    elif ev == "invalid" and len(arc) >= 3:
        _add_arc_fill(fig, xs, ys, arc, "rgba(198,40,40,0.07)")

    _add_polygon_edges(fig, xs, ys, n, width=2)

    # ancestor chords
    if stack_diags:
        sdx, sdy = [], []
        for sa, sb in stack_diags:
            sdx += [xs[sa], xs[sb], None]
            sdy += [ys[sa], ys[sb], None]
        fig.add_trace(
            go.Scatter(
                x=sdx,
                y=sdy,
                mode="lines",
                line=dict(color="#90CAF9", width=1.5, dash="dot"),
                opacity=0.55,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # held-left chords
    if held_left_diags:
        hldx, hldy = [], []
        for ha, hb in held_left_diags:
            hldx += [xs[ha], xs[hb], None]
            hldy += [ys[ha], ys[hb], None]
        fig.add_trace(
            go.Scatter(
                x=hldx,
                y=hldy,
                mode="lines",
                line=dict(color="#26A69A", width=2, dash="dash"),
                opacity=0.80,
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # try_mid: sub-diagonal lines + cached cost labels
    if ev == "try_mid":
        mid = event["mid"]
        for (va, vb), color, bg in [
            ((a, mid), "#2E7D32", "rgba(232,245,233,0.92)"),
            ((mid, b), "#BF360C", "rgba(255,243,224,0.92)"),
        ]:
            if not _is_polygon_edge(va, vb, n):
                fig.add_trace(
                    go.Scatter(
                        x=[xs[va], xs[vb]],
                        y=[ys[va], ys[vb]],
                        mode="lines",
                        line=dict(color=color, width=2.5),
                        showlegend=False,
                        hoverinfo="skip",
                    )
                )
                cv = dp_cost[va][vb]
                if cv is not None:
                    mx, my = (xs[va] + xs[vb]) / 2, (ys[va] + ys[vb]) / 2
                    cost_str = "∞" if (isinstance(cv, float) and math.isinf(cv)) else f"{cv:.3f}"
                    fig.add_annotation(
                        x=mx,
                        y=my,
                        text=f"<b>{cost_str}</b>",
                        showarrow=False,
                        font=dict(size=9, color=color),
                        bgcolor=bg,
                        bordercolor=color,
                        borderwidth=1,
                        xanchor="center",
                        yanchor="middle",
                    )

    # arc boundary
    arc_ex, arc_ey = [], []
    for i in range(len(arc) - 1):
        u, v = arc[i], arc[i + 1]
        arc_ex += [xs[u], xs[v], None]
        arc_ey += [ys[u], ys[v], None]

    if ev == "invalid":
        if arc_ex:
            fig.add_trace(
                go.Scatter(
                    x=arc_ex,
                    y=arc_ey,
                    mode="lines",
                    line=dict(color="#C62828", width=2.5),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        fig.add_trace(
            go.Scatter(
                x=[xs[a], xs[b]],
                y=[ys[a], ys[b]],
                mode="lines",
                line=dict(color="#C62828", width=2.5, dash="dash"),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    else:
        if arc_ex:
            arc_color = "#2E7D32" if ev in ("exit", "cache_hit") else C_ACTIVE
            fig.add_trace(
                go.Scatter(
                    x=arc_ex,
                    y=arc_ey,
                    mode="lines",
                    line=dict(color=arc_color, width=2.5),
                    opacity=0.85,
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
        if not _is_polygon_edge(a, b, n):
            chord_color = "#2E7D32" if ev in ("exit", "cache_hit") else C_ACTIVE
            chord_dash = "solid" if ev in ("exit", "cache_hit") else "dash"
            fig.add_trace(
                go.Scatter(
                    x=[xs[a], xs[b]],
                    y=[ys[a], ys[b]],
                    mode="lines",
                    line=dict(color=chord_color, width=2, dash=chord_dash),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # exit/cache_hit cost label on chord
    if ev in ("exit", "cache_hit") and not _is_polygon_edge(a, b, n):
        cost_val = event.get("best_cost") if ev == "exit" else dp_cost[a][b]
        if cost_val is not None and not (isinstance(cost_val, float) and math.isinf(cost_val)):
            mx, my = (xs[a] + xs[b]) / 2, (ys[a] + ys[b]) / 2
            label = f"<b>{cost_val:.3f}</b>" + (" ✓" if ev == "cache_hit" else "")
            fig.add_annotation(
                x=mx,
                y=my,
                text=label,
                showarrow=False,
                font=dict(size=10, color="#1B5E20"),
                bgcolor="rgba(232,245,233,0.95)",
                bordercolor="#2E7D32",
                borderwidth=1.5,
                xanchor="center",
                yanchor="middle",
            )

    # vertices
    apex = event.get("mid") if ev == "try_mid" else None
    colors, sizes, bcolors, bwidths = [], [], [], []
    for i in range(n):
        if i == apex:
            colors.append("#F57F17")
            sizes.append(14)
            bcolors.append("#E65100")
            bwidths.append(2)
        elif i in (a, b):
            colors.append(C_ACTIVE)
            sizes.append(12)
            bcolors.append("#0D47A1")
            bwidths.append(2)
        elif i in arc_set:
            colors.append(C_ACTIVE)
            sizes.append(9)
            bcolors.append(C_ACTIVE)
            bwidths.append(1)
        else:
            colors.append(C_VERTEX)
            sizes.append(8)
            bcolors.append(C_EDGE)
            bwidths.append(1)

    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(color=colors, size=sizes, line=dict(color=bcolors, width=bwidths)),
            text=[str(i) for i in range(n)],
            textposition="top right",
            textfont=dict(size=10, color=C_EDGE),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    pad = DATA_MAX * 0.12
    fig.update_layout(
        xaxis=dict(range=[-pad, DATA_MAX + pad], visible=False, fixedrange=True),
        yaxis=dict(range=[-pad, DATA_MAX + pad], visible=False, scaleanchor="x", fixedrange=True),
        plot_bgcolor=C_BG,
        paper_bgcolor=C_BG,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        dragmode=False,
    )
    return fig


def make_dp_table_figure(dp_state, dp_cost, n, a, b, ev, stack_frames) -> go.Figure:
    stack_set = set(stack_frames)

    tick_vals = list(range(n))
    tick_text = [str(i) for i in tick_vals]

    z_grid, annotations = [], []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                code, label = _ST_DIAG, str(i)
            elif i > j:
                code, label = _ST_LOWER, ""
            elif i == a and j == b:
                code = _ST_CURR
                cv = dp_cost[i][j]
                label = (
                    _fmt_cost(cv) if ev in ("exit", "cache_hit") and cv is not None else f"{i},{j}"
                )
            elif (j - i) == 1:
                code, label = _ST_EDGE, "—"
            else:
                st = dp_state[i][j]
                # IN_STACK overrides pending/active states but not settled ones (st ≤ 1)
                code = _ST_ACTIVE if (i, j) in stack_set and st <= 1 else st
                cv = dp_cost[i][j]
                label = _fmt_cost(cv) if cv is not None else ""
            row.append(code)
            if label:
                bold = code in (_ST_OPTIMAL, _ST_CURR, _ST_INVALID)
                annotations.append(
                    dict(
                        x=j,
                        y=i,
                        text=f"<b>{label}</b>" if bold else label,
                        showarrow=False,
                        font=dict(size=11, color=_DP_TC[code], family="ui-monospace, monospace"),
                        xref="x",
                        yref="y",
                    )
                )
        z_grid.append(row)

    fig = go.Figure(
        go.Heatmap(
            z=z_grid,
            colorscale=_DP_COLORSCALE,
            zmin=0,
            zmax=8,
            showscale=False,
            xgap=3,
            ygap=3,
            hoverinfo="skip",
        )
    )

    tick_font = dict(size=11, color="#6b7280", family="ui-monospace, monospace")
    axis_title_font = dict(size=10, color="#9ca3af")
    fig.update_layout(
        annotations=annotations,
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            side="top",
            title=dict(text="end →", font=axis_title_font, standoff=4),
            tickfont=tick_font,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
        ),
        yaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            autorange="reversed",
            title=dict(text="start", font=axis_title_font, standoff=4),
            tickfont=tick_font,
            showgrid=False,
            zeroline=False,
            fixedrange=True,
            scaleanchor="x",
            scaleratio=1,
        ),
        plot_bgcolor="#f8f9fc",
        paper_bgcolor="#f8f9fc",
        margin=dict(l=40, r=10, t=50, b=10),
        dragmode=False,
    )
    return fig


def _make_narration(ev, event, a, b, n, total, step_idx, dp_cost) -> str:
    hdr = f"**Step {step_idx + 1} / {total}**"

    if ev == "enter":
        cands = (b - a - 1) if b > a else (n - a + b - 1)
        return (
            f"{hdr} — computing **dp[{a}][{b}]**"
            f"&nbsp;·&nbsp; {cands} candidate split vertices to try"
        )

    if ev == "try_mid":
        mid = event["mid"]
        lc = _fmt(event.get("left_cost"))
        rc = _fmt(event.get("right_cost"))
        tc = _fmt(event.get("cost"))
        cur_cost = event.get("cost")
        best_so_far = event.get("_best_so_far", math.inf)

        if cur_cost is not None and math.isinf(cur_cost):
            verdict = f"**invalid** — dp[{a}][{mid}] or dp[{mid}][{b}] is ∞"
        elif cur_cost is not None and cur_cost < best_so_far:
            verdict = "**new best**"
        else:
            verdict = "not better than current best"

        return (
            f"{hdr} — **dp[{a}][{b}]** &nbsp; trying apex **{mid}** → △({a}, {mid}, {b})\n\n"
            f"dp[{a}][{mid}] `{lc}` + dp[{mid}][{b}] `{rc}` = **`{tc}`**"
            f" &nbsp;→&nbsp; {verdict}"
        )

    if ev == "exit":
        km = event.get("best_mid", -1)
        cost = _fmt(event.get("best_cost"))
        if km == -1:
            return f"{hdr} — **dp[{a}][{b}]** &nbsp; no valid split found"
        return (
            f"{hdr} — **dp[{a}][{b}] = {cost}** &nbsp; best split: vertex **{km}**"
            f" → optimal triangulation shown"
        )

    if ev == "invalid":
        return f"{hdr} — diagonal **({a},{b})** is invalid &nbsp;→&nbsp; **dp[{a}][{b}] = ∞**"

    if ev == "cache_hit":
        cost = _fmt(dp_cost[a][b])
        return f"{hdr} — **dp[{a}][{b}] = {cost}** &nbsp; *(cached — triangulation already known)*"

    return f"{hdr} — {ev} ({a}, {b})"


def _bt_narration_text(step_idx: int, total: int, s: dict) -> str:
    diag_part = (
        f" &nbsp;·&nbsp; diagonal **({s['diagonal'][0]}, {s['diagonal'][1]})**"
        if s["diagonal"]
        else " &nbsp;·&nbsp; *polygon edge — no diagonal*"
    )
    return (
        f"**Step {step_idx + 1} / {total}** — triangle **({s['a']}, {s['mid']}, {s['b']})**"
        + diag_part
    )


def _gen_backtrack_steps(n: int, dp_splits: list) -> list[dict]:
    """
    Generate pre-order backtracking steps from dp_splits.
    splits_cache sentinel values: None = uncomputed, -1 = base/invalid, k>=0 = valid split.
    """
    steps: list[dict] = []
    triangles_so_far: list[tuple] = []
    diags_so_far: list[tuple] = []

    def _walk(a: int, b: int) -> None:
        if (a + 1) % n == b:  # consecutive vertices — polygon edge base case
            return
        mid = dp_splits[a][b]
        # None = never computed, -1 = no valid split — neither produces a triangle
        if mid is None or mid < 0:
            return
        diag = (a, b) if not _is_polygon_edge(a, b, n) else None
        steps.append(
            {
                "a": a,
                "mid": mid,
                "b": b,
                "diagonal": diag,
                "triangles_so_far": list(triangles_so_far),
                "diags_so_far": list(diags_so_far),
            }
        )
        triangles_so_far.append((a, mid, b))
        if diag is not None:
            diags_so_far.append(diag)
        _walk(a, mid)
        _walk(mid, b)

    _walk(0, n - 1)
    return steps


def make_backtrack_frame(polygon: Polygon, bt_steps: list[dict], step_idx: int) -> go.Figure | None:
    if not bt_steps or step_idx < 0 or step_idx >= len(bt_steps):
        return None

    xs, ys = _polygon_coords(polygon)
    n = len(polygon)
    step = bt_steps[step_idx]
    a, mid, b = step["a"], step["mid"], step["b"]

    fig = go.Figure()

    # polygon background
    fig.add_trace(
        go.Scatter(
            x=xs + [xs[0]],
            y=ys + [ys[0]],
            fill="toself",
            fillcolor=C_POLYGON,
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # committed triangles
    if step["triangles_so_far"]:
        tri_x, tri_y = [], []
        for ta, tm, tb in step["triangles_so_far"]:
            tri_x += [xs[ta], xs[tm], xs[tb], xs[ta], None]
            tri_y += [ys[ta], ys[tm], ys[tb], ys[ta], None]
        fig.add_trace(
            go.Scatter(
                x=tri_x,
                y=tri_y,
                fill="toself",
                fillcolor="rgba(76,175,80,0.22)",
                line=dict(color="#388E3C", width=1.0),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # current triangle
    fig.add_trace(
        go.Scatter(
            x=[xs[a], xs[mid], xs[b], xs[a]],
            y=[ys[a], ys[mid], ys[b], ys[a]],
            fill="toself",
            fillcolor="rgba(56,142,60,0.45)",
            line=dict(color="#1B5E20", width=2.5),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    _add_polygon_edges(fig, xs, ys, n, width=2)

    # committed diagonals
    if step["diags_so_far"]:
        dx, dy = [], []
        for da, db in step["diags_so_far"]:
            dx += [xs[da], xs[db], None]
            dy += [ys[da], ys[db], None]
        fig.add_trace(
            go.Scatter(
                x=dx,
                y=dy,
                mode="lines",
                line=dict(color=C_DIAGONAL, width=1.4, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # current diagonal
    if step["diagonal"] is not None:
        da, db = step["diagonal"]
        fig.add_trace(
            go.Scatter(
                x=[xs[da], xs[db]],
                y=[ys[da], ys[db]],
                mode="lines",
                line=dict(color="#1B5E20", width=2.5),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # vertices
    colors = [
        ("#F57F17" if i == mid else (C_ACTIVE if i in (a, b) else C_VERTEX)) for i in range(n)
    ]
    sizes = [(14 if i == mid else (12 if i in (a, b) else 8)) for i in range(n)]
    fig.add_trace(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            marker=dict(color=colors, size=sizes),
            text=[str(i) for i in range(n)],
            textposition="top right",
            textfont=dict(size=10, color=C_EDGE),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    pad = DATA_MAX * 0.12
    fig.update_layout(
        xaxis=dict(range=[-pad, DATA_MAX + pad], visible=False, fixedrange=True),
        yaxis=dict(range=[-pad, DATA_MAX + pad], visible=False, scaleanchor="x", fixedrange=True),
        plot_bgcolor=C_BG,
        paper_bgcolor=C_BG,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        dragmode=False,
    )
    return fig


def make_animation_frame(
    polygon: Polygon,
    trace: list,
    step_idx: int,
    precomputed: list,
) -> tuple:
    if not trace or step_idx < 0 or step_idx >= len(trace):
        return None, None, "*No trace data.*"

    event = trace[step_idx]
    n = len(polygon)
    xs, ys = _polygon_coords(polygon)
    a, b = event["start"], event["end"]
    ev = event["event"]

    dp_state, dp_cost, dp_splits = precomputed[step_idx]
    stack_frames = event.get("stack", [])

    poly_fig = _make_poly_figure(
        xs, ys, n, a, b, ev, event, stack_frames, dp_cost, dp_splits, dp_state
    )
    table_fig = make_dp_table_figure(dp_state, dp_cost, n, a, b, ev, stack_frames)
    narr = _make_narration(ev, event, a, b, n, len(trace), step_idx, dp_cost)

    return poly_fig, table_fig, narr


# ── Gradio app ────────────────────────────────────────────────────────────────

with gr.Blocks(title="Optimal Polygon Triangulation", css=_CSS) as demo:
    gr.Markdown(
        "# Optimal Polygon Triangulation\nInterval DP with memoization · O(n³) time · O(n²) space"
    )

    polygon_pts = gr.State([])
    polygon_finished = gr.State(False)
    anim_trace = gr.State([])
    anim_precomputed = gr.State([])  # precomputed (dp_state, dp_cost, dp_splits) per step
    anim_polygon = gr.State(None)  # cached Polygon object — avoid rebuilding each tick
    is_playing = gr.State(False)
    bt_steps_state = gr.State([])
    bt_polygon = gr.State(None)  # cached Polygon object for backtrack tab
    bt_is_playing = gr.State(False)

    # ── Tab 1 ─────────────────────────────────────────────────────────────────
    with gr.Tab("1  Build Polygon"):
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Row():
                    undo_btn = gr.Button("Undo", size="sm")
                    clear_btn = gr.Button("Clear", size="sm")
                    finish_btn = gr.Button("Finish", size="sm", variant="primary")
                canvas_img = gr.Image(
                    value=_make_canvas_image([]),
                    interactive=True,
                    sources=[],
                    width=CANVAS_PX,
                    height=CANVAS_PX,
                    type="pil",
                    show_label=False,
                    buttons=[],
                    elem_classes=["canvas-img"],
                )
            with gr.Column(scale=1):
                poly_info = gr.Textbox(label="Polygon info", lines=20, interactive=False)

        with gr.Row():
            with gr.Column():
                gr.Markdown("**Upload polygon** — one vertex per line: `x y`")
                upload_file = gr.File(label="Upload .txt", file_types=[".txt"])

        def _canvas_click(pts, evt: gr.SelectData):
            x = round(max(0.0, min(DATA_MAX, evt.index[0] / CANVAS_PX * DATA_MAX)), 2)
            y = round(max(0.0, min(DATA_MAX, (CANVAS_PX - evt.index[1]) / CANVAS_PX * DATA_MAX)), 2)
            for p in pts:
                if abs(p[0] - x) < 0.15 and abs(p[1] - y) < 0.15:
                    return _make_canvas_image(pts), pts, _points_info(pts), False
            new_pts = pts + [[x, y]]
            return _make_canvas_image(new_pts), new_pts, _points_info(new_pts), False

        def _finish(pts):
            info = _points_info(pts)
            if len(pts) < 3:
                return gr.update(), f"{info}\nNeed at least 3 vertices".strip(), False
            try:
                build_polygon(pts)
                return (
                    _make_canvas_image(pts, finished=True),
                    f"{info}\nValid polygon".strip(),
                    True,
                )
            except ValueError as e:
                return gr.update(), f"{info}\n{e}".strip(), False

        def _undo(pts):
            new_pts = pts[:-1] if pts else []
            return _make_canvas_image(new_pts), new_pts, _points_info(new_pts), False

        def _clear():
            return _make_canvas_image([]), [], "", False

        def _upload(f, cur_pts):
            if f is None:
                return gr.update(), cur_pts, _points_info(cur_pts), False
            try:
                raw = read_input(f.name)
                xs = [p.x for p in raw]
                ys = [p.y for p in raw]
                mn_x, mn_y = min(xs), min(ys)
                span = max(max(xs) - mn_x, max(ys) - mn_y, 1e-9)
                pts = [
                    [round(1 + (p.x - mn_x) / span * 8, 2), round(1 + (p.y - mn_y) / span * 8, 2)]
                    for p in raw
                ]
                build_polygon(pts)
                return (
                    _make_canvas_image(pts, finished=True),
                    pts,
                    f"{_points_info(pts)}\nValid polygon",
                    True,
                )
            except ValueError as e:
                return gr.update(), cur_pts, f"{_points_info(cur_pts)}\n{e}".strip(), False
            except Exception as e:
                return gr.update(), cur_pts, f"{_points_info(cur_pts)}\nError: {e}".strip(), False

        canvas_img.select(
            _canvas_click, [polygon_pts], [canvas_img, polygon_pts, poly_info, polygon_finished]
        )
        finish_btn.click(_finish, [polygon_pts], [canvas_img, poly_info, polygon_finished])
        undo_btn.click(_undo, [polygon_pts], [canvas_img, polygon_pts, poly_info, polygon_finished])
        clear_btn.click(_clear, [], [canvas_img, polygon_pts, poly_info, polygon_finished])
        upload_file.change(
            _upload,
            [upload_file, polygon_pts],
            [canvas_img, polygon_pts, poly_info, polygon_finished],
        )

    # ── Tab 2 ─────────────────────────────────────────────────────────────────
    with gr.Tab("2  DP Animation"):
        with gr.Row():
            criteria_sel = gr.Radio(
                choices=["minsum", "minimax", "maximin"],
                value="minsum",
                label="Optimality criterion",
                info=(
                    "minsum = min total length  |  minimax = min longest diagonal  | "
                    " maximin = max shortest diagonal"
                ),
            )
            run_btn = gr.Button("Run", variant="primary")

        with gr.Tabs():
            with gr.Tab("Phase 1: DP Fill"):
                with gr.Row():
                    with gr.Column(scale=1):
                        anim_poly = gr.Plot(label="Polygon")
                    with gr.Column(scale=1):
                        anim_dp_table = gr.Plot(label="DP Table")

                step_narration = gr.Markdown(
                    "*Run the algorithm to begin.*", elem_classes=["narration-box"]
                )
                with gr.Row():
                    prev_btn = gr.Button("Prev", size="sm")
                    step_slider = gr.Slider(
                        minimum=0, maximum=1, step=1, value=0, label="Step", scale=4
                    )
                    next_btn = gr.Button("Next", size="sm")
                    play_btn = gr.Button("Play", size="sm", variant="secondary")
                    speed_slider = gr.Slider(
                        minimum=0.5,
                        maximum=5.0,
                        value=1.5,
                        step=0.5,
                        label="Speed (steps/s)",
                        scale=2,
                    )

                timer = gr.Timer(value=1.0 / 1.5, active=False)
                cur_step = gr.State(0)

            with gr.Tab("Phase 2: Backtracking"):
                bt_poly_plot = gr.Plot(label="Triangulation")
                bt_narration = gr.Markdown(
                    "*Run the algorithm to begin.*", elem_classes=["narration-box"]
                )
                with gr.Row():
                    bt_prev_btn = gr.Button("Prev", size="sm")
                    bt_step_slider = gr.Slider(
                        minimum=0, maximum=1, step=1, value=0, label="Step", scale=4
                    )
                    bt_next_btn = gr.Button("Next", size="sm")
                    bt_play_btn = gr.Button("Play", size="sm", variant="secondary")
                    bt_speed_slider = gr.Slider(
                        minimum=0.5,
                        maximum=5.0,
                        value=1.5,
                        step=0.5,
                        label="Speed (steps/s)",
                        scale=2,
                    )

                bt_timer = gr.Timer(value=1.0 / 1.5, active=False)
                bt_cur_step = gr.State(0)

        def _run(pts, criteria):
            _empty = (
                gr.update(),
                None,
                "*Need at least 3 vertices.*",
                [],
                [],
                None,
                gr.update(maximum=0, value=0),
                0,
                False,
                gr.update(active=False),
                "Play",
                None,
                "*Need at least 3 vertices.*",
                [],
                None,
                gr.update(maximum=0, value=0),
                0,
            )
            if len(pts) < 3:
                return _empty
            try:
                polygon = build_polygon(pts)
                (ft, fd), tracer = optimal_triangulation(polygon, criteria, return_trace=True)
                splits_cache = tracer.splits_cache
                # drop base_case events (polygon edges — nothing to show)
                trace = [e for e in tracer.events if e["event"] != "base_case"]
                # annotate try_mid with best-cost-so-far for O(1) narration
                _best: dict[tuple, float] = {}
                for e in trace:
                    if e["event"] == "try_mid":
                        key = (e["start"], e["end"])
                        e["_best_so_far"] = _best.get(key, math.inf)
                        c = e.get("cost")
                        if c is not None and c < _best.get(key, math.inf):
                            _best[key] = c

                # precompute DP state for all steps — O(total_events) total
                precomputed = _precompute_anim_states(trace, len(polygon))

                bt_steps = _gen_backtrack_steps(len(polygon), splits_cache)

                pf, th, narr = make_animation_frame(polygon, trace, 0, precomputed)
                bt_fig = make_backtrack_frame(polygon, bt_steps, 0)
                s0 = bt_steps[0] if bt_steps else None
                bt_narr = (
                    _bt_narration_text(0, len(bt_steps), s0) if s0 else "*No backtracking steps.*"
                )
                return (
                    pf,
                    th,
                    narr,
                    trace,
                    precomputed,
                    polygon,
                    gr.update(maximum=max(0, len(trace) - 1), value=0),
                    0,
                    False,
                    gr.update(active=False),
                    "Play",
                    bt_fig,
                    bt_narr,
                    bt_steps,
                    polygon,
                    gr.update(maximum=max(0, len(bt_steps) - 1), value=0),
                    0,
                )
            except Exception as e:
                err = f"*Error: {e}*"
                return (
                    gr.update(),
                    None,
                    err,
                    [],
                    [],
                    None,
                    gr.update(maximum=0, value=0),
                    0,
                    False,
                    gr.update(active=False),
                    "Play",
                    None,
                    "*Error during backtracking.*",
                    [],
                    None,
                    gr.update(maximum=0, value=0),
                    0,
                )

        def _goto(step, trace, precomputed, polygon):
            if not trace or polygon is None:
                return gr.update(), gr.update(), "*Run the algorithm first.*", step
            pf, th, narr = make_animation_frame(polygon, trace, int(step), precomputed)
            return pf, th, narr, int(step)

        def _prev(step, trace, precomputed, polygon):
            return _goto(max(0, step - 1), trace, precomputed, polygon)

        def _next(step, trace, precomputed, polygon):
            return _goto(min(len(trace) - 1, step + 1), trace, precomputed, polygon)

        def _toggle_play(playing, spd):
            new_playing = not playing
            return (
                new_playing,
                gr.update(active=new_playing, value=1.0 / spd),
                "Pause" if new_playing else "Play",
            )

        def _tick(step, trace, precomputed, polygon):
            if not trace or polygon is None:
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    step,
                    gr.update(),
                    gr.update(active=False),
                    "Play",
                )
            new_step = min(len(trace) - 1, step + 1)
            pf, th, narr = make_animation_frame(polygon, trace, new_step, precomputed)
            at_end = new_step >= len(trace) - 1
            return (
                pf,
                th,
                narr,
                new_step,
                gr.update(value=new_step),
                gr.update(active=not at_end),
                "Play" if at_end else gr.update(),
            )

        def _bt_render(step, bt_steps, polygon):
            if not bt_steps or polygon is None:
                return None, "*Run the algorithm first.*"
            step = int(step)
            return make_backtrack_frame(polygon, bt_steps, step), _bt_narration_text(
                step, len(bt_steps), bt_steps[step]
            )

        def _bt_goto(step, bt_steps, polygon):
            fig, narr = _bt_render(step, bt_steps, polygon)
            return fig, narr, int(step)

        def _bt_prev(step, bt_steps, polygon):
            return _bt_goto(max(0, step - 1), bt_steps, polygon)

        def _bt_next(step, bt_steps, polygon):
            return _bt_goto(min(len(bt_steps) - 1, step + 1), bt_steps, polygon)

        _bt_toggle_play = _toggle_play

        def _bt_tick(step, bt_steps, polygon):
            if not bt_steps or polygon is None:
                return None, gr.update(), step, gr.update(), gr.update(active=False), "Play"
            new_step = min(len(bt_steps) - 1, step + 1)
            fig, narr = _bt_render(new_step, bt_steps, polygon)
            at_end = new_step >= len(bt_steps) - 1
            return (
                fig,
                narr,
                new_step,
                gr.update(value=new_step),
                gr.update(active=not at_end),
                "Play" if at_end else gr.update(),
            )

        _anim_out = [anim_poly, anim_dp_table, step_narration]
        _anim_state = [anim_trace, anim_precomputed, anim_polygon]
        _bt_state = [bt_steps_state, bt_polygon]

        run_btn.click(
            _run,
            [polygon_pts, criteria_sel],
            [
                *_anim_out,
                *_anim_state,
                step_slider,
                cur_step,
                is_playing,
                timer,
                play_btn,
                bt_poly_plot,
                bt_narration,
                *_bt_state,
                bt_step_slider,
                bt_cur_step,
            ],
        )
        prev_btn.click(_prev, [cur_step, *_anim_state], [*_anim_out, cur_step])
        next_btn.click(_next, [cur_step, *_anim_state], [*_anim_out, cur_step])
        step_slider.change(_goto, [step_slider, *_anim_state], [*_anim_out, cur_step])
        play_btn.click(_toggle_play, [is_playing, speed_slider], [is_playing, timer, play_btn])
        speed_slider.change(
            lambda s, p: gr.update(value=1.0 / s) if p else gr.update(),
            [speed_slider, is_playing],
            [timer],
        )
        timer.tick(
            _tick, [cur_step, *_anim_state], [*_anim_out, cur_step, step_slider, timer, play_btn]
        )

        bt_prev_btn.click(
            _bt_prev, [bt_cur_step, *_bt_state], [bt_poly_plot, bt_narration, bt_cur_step]
        )
        bt_next_btn.click(
            _bt_next, [bt_cur_step, *_bt_state], [bt_poly_plot, bt_narration, bt_cur_step]
        )
        bt_step_slider.change(
            _bt_goto, [bt_step_slider, *_bt_state], [bt_poly_plot, bt_narration, bt_cur_step]
        )
        bt_play_btn.click(
            _bt_toggle_play,
            [bt_is_playing, bt_speed_slider],
            [bt_is_playing, bt_timer, bt_play_btn],
        )
        bt_speed_slider.change(
            lambda s, p: gr.update(value=1.0 / s) if p else gr.update(),
            [bt_speed_slider, bt_is_playing],
            [bt_timer],
        )
        bt_timer.tick(
            _bt_tick,
            [bt_cur_step, *_bt_state],
            [bt_poly_plot, bt_narration, bt_cur_step, bt_step_slider, bt_timer, bt_play_btn],
        )

    # ── Tab 3 ─────────────────────────────────────────────────────────────────
    with gr.Tab("3  Comparison"):
        compare_btn = gr.Button("Run Triangulations", variant="primary")

        with gr.Row():
            img_ear = gr.Plot(label="Ear Clipping")
            img_sum = gr.Plot(label="Optimal DP — Min Sum of Diagonals")
        with gr.Row():
            img_max = gr.Plot(label="Optimal DP — Min Longest Diagonal")
            img_min = gr.Plot(label="Optimal DP — Max Shortest Diagonal")

        compare_tbl = gr.Dataframe(
            label="Summary",
            interactive=False,
            column_widths=["220px", "180px", "180px", "180px"],
        )

        def _compare(pts):
            if len(pts) < 3:
                return None, None, None, None, None
            try:
                polygon = build_polygon(pts)
                tris_ear, diags_ear = ear_clipping_triangulation(polygon)
                tris_sum, diags_sum = optimal_triangulation(polygon, "minsum")
                tris_max, diags_max = optimal_triangulation(polygon, "minimax")
                tris_min, diags_min = optimal_triangulation(polygon, "maximin")

                def stats(diags):
                    ls = _diag_lengths(polygon, diags)
                    if not ls:
                        return 0.0, 0.0, 0.0
                    return round(sum(ls), 4), round(max(ls), 4), round(min(ls), 4)

                df = pd.DataFrame(
                    [
                        ["Ear Clipping", *stats(diags_ear)],
                        ["Optimal DP — Min Sum", *stats(diags_sum)],
                        ["Optimal DP — Min Longest", *stats(diags_max)],
                        ["Optimal DP — Max Shortest", *stats(diags_min)],
                    ],
                    columns=["Algorithm", "Sum of diagonals", "Max diagonal", "Min diagonal"],
                )
                return (
                    make_triangulation_figure(polygon, tris_ear, diags_ear),
                    make_triangulation_figure(polygon, tris_sum, diags_sum),
                    make_triangulation_figure(polygon, tris_max, diags_max),
                    make_triangulation_figure(polygon, tris_min, diags_min),
                    df,
                )
            except Exception as e:
                return None, None, None, None, pd.DataFrame([{"Error": str(e)}])

        compare_btn.click(
            _compare, [polygon_pts], [img_ear, img_sum, img_max, img_min, compare_tbl]
        )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft(), footer_links=[])
