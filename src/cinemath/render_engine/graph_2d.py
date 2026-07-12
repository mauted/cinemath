"""2D graphing: axes, plots, region geometry, and vertical layout."""

from __future__ import annotations

from typing import Any

from manim import DOWN, RIGHT, UP, Axes, Dot, VGroup, VMobject

from cinemath.render_engine.validate import compile_expr

# Default plot footprint (leaves room for a title label + caption).
PLOT_AT = [0.0, -0.9]
PLOT_X_LENGTH = 6.5
PLOT_Y_LENGTH = 3.0
LABEL_AT = "title"

# When to paint area under/inside a curve.
# - "none": stroke only (roots, function shape, most algebra graphs)
# - "x_axis": shade between the curve and the x-axis (integrals, net area)
SHADE_NONE = "none"
SHADE_X_AXIS = "x_axis"
_SHADE_ALIASES = {
    None: SHADE_NONE,
    False: SHADE_NONE,
    "false": SHADE_NONE,
    "none": SHADE_NONE,
    "off": SHADE_NONE,
    True: SHADE_X_AXIS,
    "true": SHADE_X_AXIS,
    "x_axis": SHADE_X_AXIS,
    "axis": SHADE_X_AXIS,
    "under": SHADE_X_AXIS,
}


def normalize_shade(value: Any) -> str:
    if isinstance(value, str):
        key: Any = value.strip().lower()
    else:
        key = value
    if key in _SHADE_ALIASES:
        return _SHADE_ALIASES[key]
    raise ValueError(f"Unknown plot shade mode {value!r}; use 'none' or 'x_axis'")


def build_axes(obj: dict[str, Any], *, color: Any) -> Axes:
    step = float(obj["x_range"][2]) if len(obj.get("x_range") or []) > 2 else 1.0
    y_step = float(obj["y_range"][2]) if len(obj.get("y_range") or []) > 2 else 1.0
    # Whole-number ticks → no ".0"; fractional steps keep one decimal.
    decimals = 0 if abs(step - round(step)) < 1e-9 and abs(y_step - round(y_step)) < 1e-9 else 1
    return Axes(
        x_range=obj["x_range"],
        y_range=obj["y_range"],
        x_length=float(obj.get("x_length", PLOT_X_LENGTH)),
        y_length=float(obj.get("y_length", PLOT_Y_LENGTH)),
        tips=True,
        axis_config={
            "color": color,
            "include_numbers": True,
            "font_size": 22,
            "tip_length": 0.18,
            # Manim defaults to excluding 0 at the origin; keep it labeled.
            "numbers_to_exclude": [],
            "decimal_number_config": {"num_decimal_places": decimals},
        },
    )


def integer_axis_range(
    lo: float,
    hi: float,
    *,
    step: float = 1.0,
    pad: float = 0.0,
) -> list[float]:
    """Snap ``[lo, hi]`` to integer (or step) boundaries so ticks are 0,1,2,… not 0.5,1.5,…"""
    import math

    if hi < lo:
        lo, hi = hi, lo
    a = math.floor((lo - pad) / step) * step
    b = math.ceil((hi + pad) / step) * step
    if abs(b - a) < step:
        b = a + step
    return [float(a), float(b), float(step)]


def build_plot(obj: dict[str, Any], axes: Axes, *, color: Any) -> VMobject:
    """
    Build a 2D function graph.

    Shading is opt-in via ``shade`` / ``fill_opacity``. Default is stroke-only so
    root-finding / shape plots are not filled between the curve endpoints
    (Manim closes the path; a non-zero fill paints the parabolic segment).
    """
    kwargs: dict[str, Any] = {"color": color}
    if obj.get("x_range") is not None:
        kwargs["x_range"] = obj["x_range"][:2]
    curve = axes.plot(compile_expr(obj["expr"]), **kwargs)
    # Always start stroke-only; shade is a separate area mobject when requested.
    curve.set_fill(opacity=0)
    curve.set_stroke(color=color, width=float(obj.get("stroke_width", 4)), opacity=1)

    shade = normalize_shade(obj.get("shade", SHADE_NONE))
    # Explicit fill_opacity>0 without shade still means "shade to x-axis".
    fill_opacity = float(obj.get("fill_opacity", 0.0))
    if shade == SHADE_NONE and fill_opacity <= 0:
        return curve

    if shade == SHADE_NONE:
        shade = SHADE_X_AXIS
    if fill_opacity <= 0:
        fill_opacity = 0.35

    if shade == SHADE_X_AXIS:
        x0, x1 = _plot_x_span(obj, axes)
        area = axes.get_area(
            curve,
            x_range=[x0, x1],
            color=color,
            opacity=fill_opacity,
        )
        return VGroup(area, curve)

    return curve


def _plot_x_span(obj: dict[str, Any], axes: Axes) -> tuple[float, float]:
    if obj.get("x_range") is not None:
        return float(obj["x_range"][0]), float(obj["x_range"][1])
    return float(axes.x_range[0]), float(axes.x_range[1])


def build_axes_dot(obj: dict[str, Any], axes: Axes, *, color: Any) -> Dot:
    return Dot(axes.c2p(*obj["at"]), color=color)


def place_axes(mob: VMobject, obj: dict[str, Any]) -> None:
    at = obj.get("at", PLOT_AT)
    if isinstance(at, str):
        # Named slots are resolved by the builder; graph templates should use coords.
        return
    mob.move_to(float(at[0]) * RIGHT + float(at[1]) * UP)


def auto_y_range(
    expr: str,
    x0: float,
    x1: float,
    *,
    samples: int = 40,
    pad: float = 0.15,
    include: list[float] | None = None,
    max_step: float | None = 1.0,
) -> list[float]:
    """Pick a y-range that fits the curve on [x0, x1]."""
    f = compile_expr(expr)
    ys: list[float] = list(include or [])
    for i in range(samples + 1):
        x = x0 + (x1 - x0) * i / samples
        try:
            ys.append(float(f(x)))
        except Exception:
            continue
    if not ys:
        return [-4.0, 8.0, 1.0]
    lo, hi = min(ys), max(ys)
    if abs(hi - lo) < 1e-9:
        lo, hi = lo - 1.0, hi + 1.0
    span = hi - lo
    lo -= pad * span
    hi += pad * span
    # Keep x-axis visible when roots matter.
    lo = min(lo, -0.5)
    hi = max(hi, 0.5)
    step = _nice_step(hi - lo)
    if max_step is not None:
        step = min(step, float(max_step))
    return [float(_floor_to(lo, step)), float(_ceil_to(hi, step)), float(step)]


def region_outline(
    axes_id: str,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    color: str = "yellow",
    fill_id: str | None = "R",
    fill_opacity: float = 0.25,
) -> list[dict[str, Any]]:
    """DSL objects: optional filled polygon + four border lines for rectangle R."""
    objs: list[dict[str, Any]] = []
    if fill_id is not None:
        objs.append(
            {
                "id": fill_id,
                "type": "polygon",
                "axes": axes_id,
                "points": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
                "color": color,
                "opacity": fill_opacity,
            }
        )
    corners = [
        ([x0, y0], [x1, y0]),
        ([x1, y0], [x1, y1]),
        ([x1, y1], [x0, y1]),
        ([x0, y1], [x0, y0]),
    ]
    for i, (start, end) in enumerate(corners, start=1):
        objs.append(
            {
                "id": f"L{i}",
                "type": "line",
                "axes": axes_id,
                "start": start,
                "end": end,
                "color": color,
            }
        )
    return objs


def build_polygon(obj: dict[str, Any], axes: Axes, *, color: Any) -> VMobject:
    from manim import Polygon

    pts = [axes.c2p(*p) for p in obj["points"]]
    poly = Polygon(*pts, color=color, fill_color=color, fill_opacity=float(obj.get("opacity", 0.25)))
    poly.set_stroke(color=color, width=2)
    return poly


def layout_label_above_chrome(
    labels: list[VMobject],
    chrome: list[VMobject],
    *,
    buff: float = 0.4,
    caption_ceiling: float = 2.7,
) -> None:
    """Stack labels above axes/plots; drop geometry if labels hit the caption band."""
    if not labels or not chrome:
        return

    chrome_group = VGroup(*chrome)
    for lab in labels:
        lab.next_to(chrome_group, UP, buff=buff)

    highest = max(float(lab.get_top()[1]) for lab in labels)
    if highest > caption_ceiling:
        drop = highest - caption_ceiling + 0.15
        chrome_group.shift(DOWN * drop)
        for lab in labels:
            lab.next_to(chrome_group, UP, buff=buff)


def axes_object(
    oid: str,
    *,
    x_range: list[float],
    y_range: list[float],
    at: list[float] | None = None,
    x_length: float = PLOT_X_LENGTH,
    y_length: float = PLOT_Y_LENGTH,
    color: str = "white",
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "axes",
        "x_range": x_range,
        "y_range": y_range,
        "at": at if at is not None else list(PLOT_AT),
        "x_length": x_length,
        "y_length": y_length,
        "color": color,
    }


def flow_field_object(
    oid: str,
    *,
    axes: str,
    beta_x: str,
    beta_y: str,
    grid: list[int] | None = None,
    color: str = "yellow",
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "flow_field",
        "axes": axes,
        "beta_x": beta_x,
        "beta_y": beta_y,
        "grid": list(grid or [7, 6]),
        "color": color,
    }


def build_flow_field(obj: dict[str, Any], axes: Axes, *, color: Any) -> VMobject:
    """Sample a 2D arrow field for RG flow ``(beta_x(x,y), beta_y(x,y))``."""
    from manim import Arrow

    from cinemath.render_engine.validate import compile_expr2

    fx = compile_expr2(obj["beta_x"])
    fy = compile_expr2(obj["beta_y"])
    x0, x1, _ = axes.x_range
    y0, y1, _ = axes.y_range
    nx, ny = int(obj.get("grid", [7, 6])[0]), int(obj.get("grid", [7, 6])[1])
    nx = max(3, nx)
    ny = max(3, ny)

    # Avoid the axes origin clutter; inset slightly from the frame edges.
    xs = [x0 + (x1 - x0) * (i + 0.5) / nx for i in range(nx)]
    ys = [y0 + (y1 - y0) * (j + 0.5) / ny for j in range(ny)]

    # Normalize arrow length in data units relative to the densest spacing.
    dx = (x1 - x0) / nx
    dy = (y1 - y0) / ny
    target = 0.35 * min(dx, dy)

    arrows: list[VMobject] = []
    for x in xs:
        for y in ys:
            try:
                vx = float(fx(x, y))
                vy = float(fy(x, y))
            except Exception:
                continue
            speed = (vx * vx + vy * vy) ** 0.5
            if speed < 1e-9:
                continue
            scale = target / speed
            start = axes.c2p(x, y)
            end = axes.c2p(x + vx * scale, y + vy * scale)
            arrows.append(
                Arrow(
                    start,
                    end,
                    color=color,
                    buff=0,
                    stroke_width=2.2,
                    tip_length=0.12,
                    max_tip_length_to_length_ratio=0.4,
                )
            )
    return VGroup(*arrows) if arrows else VGroup()


def plot_object(
    oid: str,
    *,
    axes: str,
    expr: str,
    color: str = "blue",
    x_range: list[float] | None = None,
    shade: str | bool = SHADE_NONE,
    fill_opacity: float | None = None,
) -> dict[str, Any]:
    """
    DSL plot. ``shade='none'`` (default) for curve-only; ``shade='x_axis'`` for
    integral-style area between the graph and the x-axis.
    """
    obj: dict[str, Any] = {
        "id": oid,
        "type": "plot",
        "axes": axes,
        "expr": expr,
        "color": color,
        "shade": normalize_shade(shade),
    }
    if x_range is not None:
        obj["x_range"] = x_range
    if fill_opacity is not None:
        obj["fill_opacity"] = float(fill_opacity)
    return obj


def _nice_step(span: float) -> float:
    if span <= 0:
        return 1.0
    raw = span / 5.0
    for step in (0.5, 1.0, 2.0, 5.0, 10.0, 20.0):
        if step >= raw * 0.8:
            return step
    return max(1.0, round(raw))


def _floor_to(v: float, step: float) -> float:
    import math

    return math.floor(v / step) * step


def _ceil_to(v: float, step: float) -> float:
    import math

    return math.ceil(v / step) * step
