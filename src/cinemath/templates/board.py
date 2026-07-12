"""Equation-board scenes: DSL for continuous algebra chains.

Playback (scroll → morph) lives in ``render_engine.equation_chain``.
Captions prefer teacher ``explanation`` prose (see ``narration``).
"""

from __future__ import annotations

from typing import Any

from cinemath.templates import dsl
from cinemath.templates.narration import read_wait, step_narration


def equation_board_scene(
    sid: str,
    steps: list[dict[str, Any]],
    *,
    caption: str | None = None,
    font_size: int = 36,
    pin: bool = True,
) -> dict[str, Any] | None:
    """
    Build one continuous board scene from teacher steps.

    First math line is written near the top; each following line is derived
    underneath (renderer scrolls first, then morphs). Caption updates use the
    step's spoken explanation when present.
    """
    lines: list[tuple[str, str]] = []  # (caption_for_line, tex)
    for step in steps:
        maths = [m for m in (step.get("math") or []) if str(m).strip()]
        if not maths:
            # Explanation-only steps still get a narration beat (no new equation).
            narr = step_narration(step)
            if narr:
                lines.append((narr, ""))
            continue
        narr = step_narration(step)
        for j, tex in enumerate(maths):
            # Narration once per teacher step (on the first math line).
            line_caption = narr if j == 0 else ""
            lines.append((line_caption, tex.strip()))

    # Drop empty placeholder rows that somehow have neither caption nor math.
    lines = [(c, t) for c, t in lines if c or t]
    if not lines:
        return None

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    prev_id: str | None = None
    eq_i = 0

    opening = caption or next((c for c, _ in lines if c), "Working")
    saw_opening = False

    for line_caption, tex in lines:
        if line_caption:
            if not saw_opening and line_caption == opening:
                # Scene already faded this caption in; just give reading time.
                saw_opening = True
                actions.append(dsl.wait(read_wait(line_caption)))
            else:
                actions.append(dsl.set_caption(line_caption))
                actions.append(dsl.wait(read_wait(line_caption)))
                saw_opening = True

        if not tex:
            # Narration-only beat (no board line).
            continue

        oid = f"{sid}_eq{eq_i}"
        eq_i += 1
        at = "upper" if prev_id is None else "center"
        objects.append(dsl.math(oid, tex, at=at, font_size=font_size))
        if prev_id is None:
            actions.append(dsl.write(oid))
        else:
            actions.append(dsl.derive(prev_id, oid))
        actions.append(dsl.wait(0.4))
        prev_id = oid

    if not objects:
        return None

    actions.append(dsl.wait(0.35))
    return dsl.scene(
        sid,
        caption=opening,
        objects=objects,
        actions=actions,
        pin=pin,
    )
