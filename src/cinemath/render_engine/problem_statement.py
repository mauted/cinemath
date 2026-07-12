"""Problem-statement intro: format + Write animation helpers."""

from __future__ import annotations

from typing import Any

from manim import ORIGIN, VMobject, Write

from cinemath.render_engine.instructions import format_instruction_body

_FONT_SIZE = 30
_PARBOX_CM = 12.0
_MAX_W = 12.2
_MAX_H = 5.5


def build_statement(
    text: str,
    *,
    color: Any,
    font_size: int = _FONT_SIZE,
) -> VMobject:
    """Centered, wrapped problem statement with inline math support."""
    from manim import Tex

    body = format_instruction_body(text)
    if not body:
        body = r"\textit{(no problem statement)}"
    return Tex(
        rf"\parbox{{{_PARBOX_CM:.1f}cm}}{{\centering {body}}}",
        font_size=font_size,
        color=color,
    )


def place_statement(mob: VMobject) -> None:
    """Fit inside the frame and center."""
    w = float(mob.width)
    h = float(mob.height)
    scale = min(_MAX_W / max(w, 1e-6), _MAX_H / max(h, 1e-6), 1.0)
    if scale < 0.999:
        mob.scale(scale)
    mob.move_to(ORIGIN)


def play_write_statement(scene, mob: VMobject, *, run_time: float = 1.6) -> None:
    """Draw the statement on as if writing it on the board."""
    place_statement(mob)
    scene.play(Write(mob), run_time=run_time)
