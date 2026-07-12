"""On-screen instruction / narration banner.

Owns wrapping, half-frame vs full-frame width, and top placement so copy
never crops off the edge (Manim ``font_size`` scales TeX parboxes).

Prose is mixed text + inline math: unicode glyphs, ``$...$``, and
algebra-like tokens (``y^2``, ``6xy^2``) render as real TeX math.
"""

from __future__ import annotations

import re
from typing import Any

from manim import DOWN, RIGHT, UP, FadeIn, FadeOut, VMobject

from cinemath.render_engine.sanitize import unicode_math_char
from cinemath.render_engine.texutil import escape_latex_text

# Manim frame is ~14.2 wide (±7.1). Leave side margins.
_FULL_MAX_W = 12.6
_HALF_MAX_W = 5.8
_HALF_CENTER_X = 3.35
_TOP_BUFF = 0.22
_FONT_SIZE = 26
_FULL_PARBOX_CM = 11.5
_HALF_PARBOX_CM = 6.4

# Already-delimited inline math.
_DELIM_MATH = re.compile(r"\$.+?\$|\\\(.+?\\\)")

# ASCII / TeX tokens that should be typeset as math inside prose.
_MATH_TOKEN = re.compile(
    r"(?:"
    r"\\[A-Za-z]+(?:\{[^{}]*\})*(?:_\{[^{}]*\}|_\w)*(?:\^\{[^{}]*\}|\^\w)*"
    r"|\|[A-Za-z\\]+\|(?:\^\d+)?"
    r"|\d*[A-Za-z][A-Za-z0-9]*(?:\^\d+)+(?:[A-Za-z]+\^\d+)*"
    r")"
)

_DASH_CHARS = {"-", "–", "—", "−"}


def build_instruction(
    text: str,
    *,
    color: Any,
    font_size: int = _FONT_SIZE,
    right_stage: bool = False,
) -> VMobject:
    """Wrapped Computer Modern paragraph with inline math; width finalized by place."""
    from manim import Tex

    body = format_instruction_body(text)
    # Stage-aware parbox: wrap at the right width so larger fonts stay readable
    # instead of being built wide and then scaled down.
    width_cm = _HALF_PARBOX_CM if right_stage else _FULL_PARBOX_CM
    return Tex(
        rf"\parbox{{{width_cm:.1f}cm}}{{\raggedright {body}}}",
        font_size=font_size,
        color=color,
    )


def format_instruction_body(text: str) -> str:
    """Turn teacher prose into a TeX fragment safe inside a ``\\parbox``."""
    s = " ".join(text.strip().split())
    if not s:
        return ""
    # Superscript digits → ASCII carets so algebra mathify can catch them.
    s = s.translate(str.maketrans({"²": "^2", "³": "^3", "⁴": "^4"}))
    # Normalize dashes before wrapping math (avoid ``$\sqrt{1 $-$ x}$`` breakage).
    s = s.replace("−", "-").replace("–", "-").replace("—", "-").replace("…", "...")
    # √(expr) → inline sqrt math.
    s = re.sub(r"√\(([^)]*)\)", r"$\\sqrt{\1}$", s)
    s = s.replace("√", r"$\sqrt{}$")

    # Unicode glyphs → inline math, but never rewrite inside existing ``$...$``.
    pieces: list[str] = []
    pos = 0
    for match in _DELIM_MATH.finditer(s):
        if match.start() > pos:
            pieces.append(_unicode_math_to_inline(s[pos : match.start()]))
        pieces.append(match.group(0))
        pos = match.end()
    if pos < len(s):
        pieces.append(_unicode_math_to_inline(s[pos:]))
    s = _merge_adjacent_math("".join(pieces))

    pieces = []
    pos = 0
    for match in _DELIM_MATH.finditer(s):
        if match.start() > pos:
            pieces.append(_mathify_text_segment(s[pos : match.start()]))
        pieces.append(_normalize_delimited_math(match.group(0)))
        pos = match.end()
    if pos < len(s):
        pieces.append(_mathify_text_segment(s[pos:]))
    return _merge_adjacent_math("".join(pieces))


def place_instruction(
    mob: VMobject,
    *,
    right_stage: bool = False,
) -> None:
    """Fit width to the active stage and pin under the top edge."""
    max_w = _HALF_MAX_W if right_stage else _FULL_MAX_W
    _fit_width(mob, max_w)
    if right_stage:
        mob.move_to(RIGHT * _HALF_CENTER_X)
        mob.to_edge(UP, buff=_TOP_BUFF)
        # to_edge recenters horizontally — restore right-half anchor.
        mob.set_x(_HALF_CENTER_X)
    else:
        mob.to_edge(UP, buff=_TOP_BUFF)
    _clamp_in_frame(mob, right_stage=right_stage)


def play_set_instruction(
    scene,
    old: VMobject | None,
    text: str,
    *,
    color: Any,
    right_stage: bool = False,
) -> VMobject:
    """Fade to a new instruction banner; returns the new mobject."""
    new_mob = build_instruction(text, color=color, right_stage=right_stage)
    place_instruction(new_mob, right_stage=right_stage)
    if old is None:
        scene.play(FadeIn(new_mob), run_time=0.3)
        return new_mob
    scene.play(
        FadeOut(old, shift=UP * 0.1),
        FadeIn(new_mob, shift=DOWN * 0.05),
        run_time=0.4,
    )
    return new_mob


def _unicode_math_to_inline(s: str) -> str:
    """Map unicode math glyphs to inline ``$...$`` (merge step combines runs)."""
    out: list[str] = []
    for ch in s:
        tex = unicode_math_char(ch)
        if tex is not None:
            out.append(f"${tex}$" if tex.startswith("\\") or tex == "-" else escape_latex_text(tex))
        elif ch in _DASH_CHARS and ch != "-":
            out.append("-")
        else:
            out.append(ch)
    return "".join(out)


def _mathify_text_segment(segment: str) -> str:
    """Escape prose; wrap algebra / TeX-command tokens in ``$...$``."""
    if not segment:
        return ""
    parts: list[str] = []
    pos = 0
    for match in _MATH_TOKEN.finditer(segment):
        if match.start() > pos:
            parts.append(escape_latex_text(segment[pos : match.start()]))
        token = match.group(0)
        if token.startswith("\\"):
            parts.append(f"${token}$")
        else:
            parts.append(f"${_caret_braces(token)}$")
        pos = match.end()
    if pos < len(segment):
        parts.append(escape_latex_text(segment[pos:]))
    return "".join(parts)


def _normalize_delimited_math(chunk: str) -> str:
    if chunk.startswith("\\(") and chunk.endswith("\\)"):
        inner = chunk[2:-2]
        return f"${_caret_braces(inner)}$"
    if chunk.startswith("$") and chunk.endswith("$"):
        return f"${_caret_braces(chunk[1:-1])}$"
    return chunk


def _caret_braces(expr: str) -> str:
    """Normalize ``x^2`` → ``x^{2}`` inside math."""
    return re.sub(r"\^(\d+)", r"^{\1}", expr)


def _merge_adjacent_math(s: str) -> str:
    """Collapse ``$a$$b$`` / ``$a$ $b$`` into one math group (repeat)."""

    def _join(match: re.Match[str]) -> str:
        left, sep, right = match.group(1), match.group(2), match.group(3)
        # Avoid gluing ``\pi`` + ``M`` into the unknown command ``\piM``.
        if re.search(r"\\[A-Za-z]+\s*$", left) and re.match(r"[A-Za-z]", right):
            return f"${left} {right}$"
        # Keep a space when the source had one between identifier-like chunks
        # (e.g. ``$M^{2}$ $Phi^{2}$`` should not become ``$M^{2}Phi^{2}$``).
        if sep and re.search(r"[A-Za-z0-9}]$", left) and re.match(r"[A-Za-z\\]", right):
            return f"${left} {right}$"
        return f"${left}{right}$"

    prev = None
    while prev != s:
        prev = s
        s = re.sub(r"\$([^$]+)\$(\s*)\$([^$]+)\$", _join, s)
    return s


def _fit_width(mob: VMobject, max_w: float) -> None:
    w = float(mob.width)
    if w > max_w and w > 1e-6:
        mob.scale(max_w / w)


def _clamp_in_frame(mob: VMobject, *, right_stage: bool) -> None:
    right_limit = 6.9
    left_limit = 0.4 if right_stage else -6.9
    top_limit = 3.85

    if float(mob.get_right()[0]) > right_limit:
        _fit_width(mob, max(0.5, right_limit - float(mob.get_left()[0]) - 0.05))
        if right_stage:
            mob.set_x(_HALF_CENTER_X)
        mob.to_edge(UP, buff=_TOP_BUFF)
        if right_stage:
            mob.set_x(_HALF_CENTER_X)

    if float(mob.get_left()[0]) < left_limit:
        mob.shift(RIGHT * (left_limit - float(mob.get_left()[0])))

    if float(mob.get_top()[1]) > top_limit:
        mob.shift(DOWN * (float(mob.get_top()[1]) - top_limit))
