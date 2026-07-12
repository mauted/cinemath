"""LaTeX text helpers (Computer Modern)."""

from __future__ import annotations

from manim import Tex, VMobject

from cinemath.render_engine.sanitize import to_plain_tex_text

_ESCAPE = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex_text(text: str) -> str:
    """Escape plain text so it is safe inside LaTeX."""
    return "".join(_ESCAPE.get(ch, ch) for ch in text)


def plain_tex(text: str, *, font_size: int = 36, color: str | None = None) -> VMobject:
    """Render non-math copy with the LaTeX (Computer Modern) font."""
    cleaned = to_plain_tex_text(text.strip())
    body = escape_latex_text(cleaned)
    mob = Tex(rf"\textrm{{{body}}}", font_size=font_size)
    if color is not None:
        mob.set_color(color)
    return mob


def caption_tex(
    text: str,
    *,
    font_size: int = 24,
    color: str | None = None,
    width_cm: float = 10.0,
) -> VMobject:
    """Deprecated helper — prefer ``instructions.build_instruction`` + place."""
    from cinemath.render_engine.instructions import build_instruction

    return build_instruction(text, color=color or "#888888", font_size=font_size)
