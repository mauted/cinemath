"""3D graphing: axes, surfaces, z-range sampling, and camera/caption helpers."""

from __future__ import annotations

from typing import Any

from manim import DEGREES, DOWN, FadeIn, ThreeDAxes, ThreeDScene, VMobject

from mathanim.render_engine.validate import compile_expr2

SURFACE_RESOLUTION = 28
DEFAULT_PHI = 70.0
DEFAULT_THETA = -40.0


def build_axes3d(obj: dict[str, Any]) -> ThreeDAxes:
    return ThreeDAxes(
        x_range=obj["x_range"],
        y_range=obj["y_range"],
        z_range=obj["z_range"],
        x_length=float(obj.get("x_length", 5.5)),
        y_length=float(obj.get("y_length", 4.5)),
        z_length=float(obj.get("z_length", 3.2)),
        tips=True,
    )


def build_surface(obj: dict[str, Any], axes: ThreeDAxes, *, color: Any) -> VMobject:
    res = int(obj.get("resolution", SURFACE_RESOLUTION))
    return axes.plot_surface(
        compile_expr2(obj["expr"]),
        u_range=obj["x_range"][:2],
        v_range=obj["y_range"][:2],
        resolution=(res, res),
        colorscale=[(color, 0.0), (color, 1.0)],
        fill_opacity=float(obj.get("opacity", 0.75)),
    )


def place_axes3d(mob: VMobject, obj: dict[str, Any] | None = None) -> None:
    # Slight drop keeps the surface clear of the fixed caption band.
    mob.move_to(DOWN * 0.45)


def sample_z_range(
    expr: str,
    x_range: list[float] | tuple[float, float],
    y_range: list[float] | tuple[float, float],
    *,
    samples: int = 12,
    pad: float = 0.12,
    include_zero: bool = True,
) -> list[float]:
    """
    z-axis limits from sampling the surface over the domain.

    Do not use the integral *value* — that measures volume, not height.
    """
    f = compile_expr2(expr)
    x0, x1 = float(x_range[0]), float(x_range[1])
    y0, y1 = float(y_range[0]), float(y_range[1])
    zs: list[float] = [0.0] if include_zero else []
    for i in range(samples + 1):
        x = x0 + (x1 - x0) * i / samples
        for j in range(samples + 1):
            y = y0 + (y1 - y0) * j / samples
            try:
                zs.append(float(f(x, y)))
            except Exception:
                continue
    if not zs:
        return [0.0, 8.0, 2.0]
    lo, hi = min(zs), max(zs)
    nonnegative = include_zero and lo >= -1e-9
    if include_zero:
        lo = min(lo, 0.0)
    if abs(hi - lo) < 1e-9:
        hi = lo + 1.0
    span = hi - lo
    if not nonnegative:
        lo -= pad * span
    hi += pad * span
    if nonnegative:
        lo = 0.0
    step = _nice_step(hi - lo)
    return [float(_floor_to(lo, step)), float(_ceil_to(hi, step)), float(step)]


def enter_3d(
    scene: ThreeDScene,
    *,
    phi: float = DEFAULT_PHI,
    theta: float = DEFAULT_THETA,
    run_time: float = 0.7,
) -> None:
    scene.move_camera(phi=phi * DEGREES, theta=theta * DEGREES, run_time=run_time)


def exit_3d(scene: ThreeDScene, *, run_time: float = 0.45) -> None:
    scene.move_camera(phi=0, theta=-90 * DEGREES, run_time=run_time)


def fix_caption_in_frame(scene: ThreeDScene, caption: VMobject | None) -> None:
    """Keep the caption flat while the camera orbits the surface."""
    if caption is None:
        return
    scene.add_fixed_in_frame_mobjects(caption)


def unfix_caption(scene: ThreeDScene, caption: VMobject | None) -> None:
    if caption is None:
        return
    try:
        scene.remove_fixed_in_frame_mobjects(caption)
    except Exception:
        pass


def reveal_surface(
    scene: ThreeDScene,
    axes: VMobject,
    surface: VMobject,
    *,
    run_time: float = 1.1,
) -> None:
    """Axes first, then fade the surface in (reads better than simultaneous Create)."""
    scene.play(FadeIn(axes), run_time=0.45)
    scene.play(FadeIn(surface), run_time=run_time)


def axes3d_object(
    oid: str,
    *,
    x_range: list[float],
    y_range: list[float],
    z_range: list[float],
    x_length: float = 5.5,
    y_length: float = 4.5,
    z_length: float = 3.2,
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "axes3d",
        "x_range": x_range,
        "y_range": y_range,
        "z_range": z_range,
        "x_length": x_length,
        "y_length": y_length,
        "z_length": z_length,
    }


def surface_object(
    oid: str,
    *,
    axes: str,
    expr: str,
    x_range: list[float],
    y_range: list[float],
    color: str = "blue",
    opacity: float = 0.75,
    resolution: int = SURFACE_RESOLUTION,
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "surface",
        "axes": axes,
        "expr": expr,
        "x_range": x_range,
        "y_range": y_range,
        "color": color,
        "opacity": opacity,
        "resolution": resolution,
    }


def _nice_step(span: float) -> float:
    if span <= 0:
        return 1.0
    raw = span / 5.0
    for step in (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0):
        if step >= raw * 0.8:
            return step
    return max(1.0, round(raw))


def _floor_to(v: float, step: float) -> float:
    import math

    return math.floor(v / step) * step


def _ceil_to(v: float, step: float) -> float:
    import math

    return math.ceil(v / step) * step
