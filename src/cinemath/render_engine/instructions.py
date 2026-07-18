"""On-screen instruction / narration banner.

Owns wrapping and relative placement heuristics inside a Region supplied by
StageConductor. Does not encode half-stage or caption-ceiling policy.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, VGroup, VMobject

from cinemath.render_engine.sanitize import unicode_math_char
from cinemath.render_engine.stage import Region, full_frame
from cinemath.render_engine.texutil import escape_latex_text

_TOP_BUFF = 0.2
_BOTTOM_BUFF = 0.32
_CONTENT_BUFF = 0.85

_FONT_SIZE = 34
_FULL_PARBOX_CM = 11.8
_HALF_PARBOX_CM = 6.6
_OVERLAP_PAD = 0.28
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
Box = tuple[float, float, float, float]  # left, right, bottom, top


def build_instruction(
    text: str,
    *,
    color: Any,
    font_size: int = _FONT_SIZE,
    max_width_cm: float | None = None,
    right_stage: bool = False,
) -> VMobject:
    """Wrapped Computer Modern paragraph with inline math; placement via StageConductor."""
    from manim import Tex

    body = format_instruction_body(text)
    if max_width_cm is not None:
        width_cm = max_width_cm
    else:
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
    s = s.translate(str.maketrans({"²": "^2", "³": "^3", "⁴": "^4"}))
    s = s.replace("−", "-").replace("–", "-").replace("—", "-").replace("…", "...")
    s = re.sub(r"√\(([^)]*)\)", r"$\\sqrt{\1}$", s)
    s = s.replace("√", r"$\sqrt{}$")

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
    region: Region | None = None,
    content: Sequence[VMobject] | None = None,
    pin_top: bool = False,
    right_stage: bool | None = None,
) -> None:
    """Fit the banner in ``region``, clear of other mobjects when possible."""
    region = _resolve_region(region, right_stage)
    if pin_top:
        _place_instruction_top(mob, region)
    else:
        items = [m for m in (content or ()) if m is not None and m is not mob]
        if items:
            _place_instruction_smart(mob, region=region, content=items)
        else:
            _place_instruction_top(mob, region)
    _clamp_in_frame(mob, region)


def play_set_instruction(
    scene,
    old: VMobject | None,
    text: str,
    *,
    color: Any,
    region: Region | None = None,
    content: Sequence[VMobject] | None = None,
    pin_top: bool = False,
    right_stage: bool | None = None,
) -> VMobject:
    """Fade to a new instruction banner; returns the new mobject."""
    region = _resolve_region(region, right_stage)
    half = region.center[0] > 0.5
    new_mob = build_instruction(
        text,
        color=color,
        max_width_cm=_HALF_PARBOX_CM if half else _FULL_PARBOX_CM,
    )
    place_instruction(new_mob, region=region, content=content, pin_top=pin_top)
    if old is None:
        scene.play(FadeIn(new_mob), run_time=0.3)
        return new_mob
    scene.play(
        FadeOut(old, shift=UP * 0.1),
        FadeIn(new_mob, shift=DOWN * 0.05),
        run_time=0.4,
    )
    return new_mob


def _resolve_region(region: Region | None, right_stage: bool | None) -> Region:
    if region is not None:
        return region
    if right_stage:
        from cinemath.render_engine.stage import right_active

        return right_active()
    return full_frame()


def _place_instruction_smart(
    mob: VMobject,
    *,
    region: Region,
    content: Sequence[VMobject],
) -> None:
    max_w = min(region.max_w, 6.0 if region.center[0] > 0.5 else region.max_w)
    _fit_width(mob, max_w)
    bounds = _region_box(region)
    content_boxes = [_mob_box(m) for m in content]
    profile = _content_profile(content_boxes)

    anchors: list[Callable[[], None]] = []
    for name in profile:
        if name == "above":
            anchors.append(lambda: _place_above_content(mob, content, region, max_w))
        elif name == "bottom":
            anchors.append(lambda: _place_bottom(mob, region, max_w))
        else:
            anchors.append(lambda: _place_instruction_top(mob, region, max_w))

    best_score = float("-inf")
    best_center = mob.get_center().copy()
    for anchor in anchors:
        anchor()
        score = _score_placement(_mob_box(mob), content_boxes, bounds)
        if score > best_score:
            best_score = score
            best_center = mob.get_center().copy()

    mob.move_to(best_center)
    _maybe_scale_up(mob, content_boxes, bounds)


def _content_profile(content_boxes: Sequence[Box]) -> tuple[str, ...]:
    """Prefer bottom band for tall plots; hug equations from above otherwise."""
    if not content_boxes:
        return ("top", "above", "bottom")
    cy = sum((b[2] + b[3]) for b in content_boxes) / (2 * len(content_boxes))
    height = max(b[3] for b in content_boxes) - min(b[2] for b in content_boxes)
    if cy > 0.35 and height > 2.4:
        return ("bottom", "top", "above")
    if cy < -0.2:
        return ("above", "top", "bottom")
    return ("above", "top", "bottom")


def _place_instruction_top(
    mob: VMobject,
    region: Region,
    max_w: float | None = None,
) -> None:
    _fit_width(mob, max_w if max_w is not None else region.max_w)
    mob.move_to(float(region.center[0]) * RIGHT)
    mob.to_edge(UP, buff=_TOP_BUFF)
    mob.set_x(float(region.center[0]))


def _place_bottom(mob: VMobject, region: Region, max_w: float) -> None:
    _fit_width(mob, max_w)
    mob.to_edge(DOWN, buff=_BOTTOM_BUFF)
    mob.set_x(float(region.center[0]))


def _place_above_content(
    mob: VMobject,
    content: Sequence[VMobject],
    region: Region,
    max_w: float,
) -> None:
    _fit_width(mob, max_w)
    group = VGroup(*content)
    mob.next_to(group, UP, buff=_CONTENT_BUFF)
    mob.set_x(float(group.get_center()[0]))
    if float(mob.get_left()[0]) < region.left:
        mob.shift(RIGHT * (region.left - float(mob.get_left()[0])))
    if float(mob.get_right()[0]) > region.right:
        mob.shift(LEFT * (float(mob.get_right()[0]) - region.right))


def _maybe_scale_up(mob: VMobject, content_boxes: Sequence[Box], bounds: Box) -> None:
    for factor in (1.14, 1.08):
        mob.scale(factor)
        if _score_placement(_mob_box(mob), content_boxes, bounds) > 0:
            return
        mob.scale(1 / factor)


def _score_placement(instr: Box, content_boxes: Sequence[Box], bounds: Box) -> float:
    left, right, bottom, top = bounds
    i_left, i_right, i_bottom, i_top = instr
    if i_left < left or i_right > right or i_bottom < bottom or i_top > top:
        return -1e6
    overlap = sum(_overlap_area(instr, box) for box in content_boxes)
    area = max(0.01, (i_right - i_left) * (i_top - i_bottom))
    return area - overlap * 40.0


def _region_box(region: Region) -> Box:
    return (region.left, region.right, region.bottom, region.top)


def _stage_bounds(right_stage: bool) -> Box:
    """Test helper: stage AABB for full or right-active region."""
    return _region_box(_resolve_region(None, right_stage))


def _mob_box(mob: VMobject) -> Box:
    return (
        float(mob.get_left()[0]),
        float(mob.get_right()[0]),
        float(mob.get_bottom()[1]),
        float(mob.get_top()[1]),
    )


def _overlap_area(a: Box, b: Box, *, pad: float = _OVERLAP_PAD) -> float:
    l1, r1, b1, t1 = a
    l2, r2, b2, t2 = b
    l1 -= pad
    r1 += pad
    b1 -= pad
    t1 += pad
    w = max(0.0, min(r1, r2) - max(l1, l2))
    h = max(0.0, min(t1, t2) - max(b1, b2))
    return w * h


def _unicode_math_to_inline(s: str) -> str:
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
    return re.sub(r"\^(\d+)", r"^{\1}", expr)


def _merge_adjacent_math(s: str) -> str:
    def _join(match: re.Match[str]) -> str:
        left, sep, right = match.group(1), match.group(2), match.group(3)
        if re.search(r"\\[A-Za-z]+\s*$", left) and re.match(r"[A-Za-z]", right):
            return f"${left} {right}$"
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


def _clamp_in_frame(mob: VMobject, region: Region) -> None:
    left_limit, right_limit, bottom_limit, top_limit = _region_box(region)

    if float(mob.get_right()[0]) > right_limit:
        _fit_width(mob, max(0.5, right_limit - float(mob.get_left()[0]) - 0.05))
        mob.set_x(float(region.center[0]))
        mob.to_edge(UP, buff=_TOP_BUFF)
        mob.set_x(float(region.center[0]))

    if float(mob.get_left()[0]) < left_limit:
        mob.shift(RIGHT * (left_limit - float(mob.get_left()[0])))

    if float(mob.get_top()[1]) > top_limit:
        mob.shift(DOWN * (float(mob.get_top()[1]) - top_limit))

    if float(mob.get_bottom()[1]) < bottom_limit:
        mob.shift(UP * (bottom_limit - float(mob.get_bottom()[1])))
