"""Feynman-diagram layouts for the animation DSL."""

from __future__ import annotations

from typing import Any

from manim import (
    DOWN,
    LEFT,
    ORIGIN,
    PI,
    RIGHT,
    UP,
    Arc,
    Circle,
    Dot,
    Line,
    MathTex,
    VGroup,
    VMobject,
)

from mathanim.render_engine.sanitize import to_math_tex

# Tree decay + one-loop layouts used by QFT tools.
PROCESSES = frozenset(
    {
        "1_to_2",
        "loop_bubble",
        "four_point_loop",
        "yukawa_triangle",
    }
)


def build_feynman(obj: dict[str, Any], *, color: Any, accent: Any) -> VMobject:
    process = obj.get("process", "1_to_2")
    if process == "1_to_2":
        return _one_to_two(obj, color=color, accent=accent)
    if process == "loop_bubble":
        return _loop_bubble(obj, color=color, accent=accent)
    if process == "four_point_loop":
        return _four_point_loop(obj, color=color, accent=accent)
    if process == "yukawa_triangle":
        return _yukawa_triangle(obj, color=color, accent=accent)
    raise ValueError(f"Unsupported Feynman process: {process}")


def _label(tex: str, *, font_size: int, color: Any) -> MathTex:
    return MathTex(to_math_tex(tex), font_size=font_size, color=color)


def _one_to_two(obj: dict[str, Any], *, color: Any, accent: Any) -> VMobject:
    scale = float(obj.get("scale", 1.0))
    labels = obj["labels"]
    left = LEFT * 2.4 * scale
    vertex = ORIGIN
    up_right = RIGHT * 2.2 * scale + UP * 1.2 * scale
    down_right = RIGHT * 2.2 * scale + DOWN * 1.2 * scale

    parts: list[VMobject] = [
        Line(left, vertex, color=color, stroke_width=4),
        Line(vertex, up_right, color=color, stroke_width=4),
        Line(vertex, down_right, color=color, stroke_width=4),
        Dot(vertex, radius=0.08 * scale, color=accent),
    ]
    lab_in = _label(labels.get("in") or "A", font_size=34, color=color)
    lab_in.next_to(left, LEFT, buff=0.2)
    lab_o1 = _label(labels.get("out1") or "b", font_size=34, color=color)
    lab_o1.next_to(up_right, RIGHT, buff=0.15)
    lab_o2 = _label(labels.get("out2") or "c", font_size=34, color=color)
    lab_o2.next_to(down_right, RIGHT, buff=0.15)
    parts.extend([lab_in, lab_o1, lab_o2])
    if labels.get("vertex"):
        vlab = _label(labels["vertex"], font_size=28, color=accent)
        vlab.next_to(ORIGIN, DOWN, buff=0.25)
        parts.append(vlab)
    return VGroup(*parts)


def _loop_bubble(obj: dict[str, Any], *, color: Any, accent: Any) -> VMobject:
    """Self-energy style: external — loop — external."""
    scale = float(obj.get("scale", 1.0))
    labels = obj.get("labels") or {}
    radius = 0.85 * scale
    left = LEFT * (2.2 * scale)
    right = RIGHT * (2.2 * scale)
    loop = Circle(radius=radius, color=color, stroke_width=4)
    loop.move_to(ORIGIN)
    parts: list[VMobject] = [
        Line(left, LEFT * radius, color=color, stroke_width=4),
        loop,
        Line(RIGHT * radius, right, color=color, stroke_width=4),
        Dot(LEFT * radius, radius=0.07 * scale, color=accent),
        Dot(RIGHT * radius, radius=0.07 * scale, color=accent),
    ]
    if labels.get("left"):
        lab = _label(labels["left"], font_size=30, color=color)
        lab.next_to(left, LEFT, buff=0.18)
        parts.append(lab)
    if labels.get("right"):
        lab = _label(labels["right"], font_size=30, color=color)
        lab.next_to(right, RIGHT, buff=0.18)
        parts.append(lab)
    if labels.get("loop"):
        lab = _label(labels["loop"], font_size=26, color=accent)
        lab.next_to(loop, UP, buff=0.2)
        parts.append(lab)
    return VGroup(*parts)


def _four_point_loop(obj: dict[str, Any], *, color: Any, accent: Any) -> VMobject:
    """One-loop correction to a four-scalar (or mixed) vertex."""
    scale = float(obj.get("scale", 1.0))
    labels = obj.get("labels") or {}
    radius = 0.75 * scale
    loop = Circle(radius=radius, color=color, stroke_width=4)
    dirs = [
        UP * 1.15 + LEFT * 1.15,
        UP * 1.15 + RIGHT * 1.15,
        DOWN * 1.15 + RIGHT * 1.15,
        DOWN * 1.15 + LEFT * 1.15,
    ]
    attach = [
        UP * radius * 0.72 + LEFT * radius * 0.72,
        UP * radius * 0.72 + RIGHT * radius * 0.72,
        DOWN * radius * 0.72 + RIGHT * radius * 0.72,
        DOWN * radius * 0.72 + LEFT * radius * 0.72,
    ]
    parts: list[VMobject] = [loop]
    for tip, base in zip(dirs, attach):
        tip_pt = tip * scale
        base_pt = base * scale
        parts.append(Line(base_pt, tip_pt, color=color, stroke_width=4))
        parts.append(Dot(base_pt, radius=0.06 * scale, color=accent))

    keys = ("ul", "ur", "lr", "ll")
    for key, tip in zip(keys, dirs):
        tex = labels.get(key) or labels.get("ext") or r"\phi"
        lab = _label(tex, font_size=28, color=color)
        tip_pt = tip * scale
        norm = float((tip[0] ** 2 + tip[1] ** 2) ** 0.5) or 1.0
        lab.next_to(tip_pt, tip / norm, buff=0.12)
        parts.append(lab)
    if labels.get("loop"):
        lab = _label(labels["loop"], font_size=24, color=accent)
        lab.move_to(ORIGIN)
        parts.append(lab)
    return VGroup(*parts)


def _yukawa_triangle(obj: dict[str, Any], *, color: Any, accent: Any) -> VMobject:
    """Triangle loop with one scalar and two fermion legs (Yukawa vertex correction)."""
    scale = float(obj.get("scale", 1.0))
    labels = obj.get("labels") or {}
    top = UP * 1.35 * scale
    left = LEFT * 1.55 * scale + DOWN * 0.85 * scale
    right = RIGHT * 1.55 * scale + DOWN * 0.85 * scale
    # Fermion arc (upper) + scalar base + closing sides.
    arc = Arc(
        radius=1.55 * scale,
        start_angle=PI * 0.15,
        angle=PI * 0.7,
        color=color,
        stroke_width=4,
    )
    arc.move_arc_center_to(DOWN * 0.35 * scale)
    parts: list[VMobject] = [
        Line(left, top, color=color, stroke_width=4),
        Line(top, right, color=color, stroke_width=4),
        Line(left, right, color=color, stroke_width=3.5),
        arc,
        Dot(top, radius=0.07 * scale, color=accent),
        Dot(left, radius=0.07 * scale, color=accent),
        Dot(right, radius=0.07 * scale, color=accent),
    ]
    # External stubs.
    scalar_tip = top + UP * 0.95 * scale
    psi_in = left + LEFT * 0.95 * scale + DOWN * 0.2 * scale
    psi_out = right + RIGHT * 0.95 * scale + DOWN * 0.2 * scale
    parts.extend(
        [
            Line(top, scalar_tip, color=color, stroke_width=4),
            Line(psi_in, left, color=color, stroke_width=4),
            Line(right, psi_out, color=color, stroke_width=4),
        ]
    )
    for tex, point, direction in (
        (labels.get("scalar") or r"\phi", scalar_tip, UP),
        (labels.get("in") or r"\psi", psi_in, LEFT),
        (labels.get("out") or r"\bar\psi", psi_out, RIGHT),
    ):
        lab = _label(tex, font_size=28, color=color)
        lab.next_to(point, direction, buff=0.12)
        parts.append(lab)
    if labels.get("loop"):
        lab = _label(labels["loop"], font_size=24, color=accent)
        lab.move_to(DOWN * 0.05 * scale)
        parts.append(lab)
    return VGroup(*parts)
