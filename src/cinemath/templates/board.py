"""Equation-board scenes: DSL for algebra chains and simple forks.

Playback (scroll, morph, fork) lives in ``render_engine.equation_chain``.
Captions prefer teacher ``explanation`` prose (see ``narration``).

After a ``fork``, ``branch_tips`` tracks the last equation id on each branch so
later steps can continue leaves independently instead of re-deriving from the stem.
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
    """Build one continuous board scene from teacher steps."""
    if not steps:
        return None

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []
    spine_id: str | None = None
    branch_tips: list[str] | None = None
    eq_i = 0

    opening = caption or next((step_narration(step) for step in steps if step_narration(step)), "Working")
    saw_opening = False

    def next_id() -> str:
        nonlocal eq_i
        oid = f"{sid}_eq{eq_i}"
        eq_i += 1
        return oid

    def append_chain(prev: str | None, tex: str) -> str:
        oid = next_id()
        objects.append(dsl.math(oid, tex.strip(), at="center", font_size=font_size))
        if prev is None:
            actions.append(dsl.write(oid))
        else:
            actions.append(dsl.derive(prev, oid))
        actions.append(dsl.wait(0.4))
        return oid

    for step in steps:
        narr = step_narration(step)
        maths = [m for m in (step.get("math") or []) if str(m).strip()]
        cases = [case for case in (step.get("cases") or []) if case.get("math")]

        if narr:
            if not saw_opening and narr == opening:
                saw_opening = True
                actions.append(dsl.wait(read_wait(narr)))
            else:
                actions.append(dsl.set_caption(narr))
                actions.append(dsl.wait(read_wait(narr)))
                saw_opening = True

        local_prev = spine_id
        if maths:
            if branch_tips is not None:
                # Parallel branches are active: spine math starts a fresh chain.
                branch_tips = None
                local_prev = None
            for tex in maths:
                local_prev = append_chain(local_prev, tex)
            spine_id = local_prev

        if cases:
            if branch_tips is not None and len(branch_tips) == len(cases):
                new_tips: list[str] = []
                for tip, case in zip(branch_tips, cases, strict=True):
                    lines = [m for m in case["math"] if str(m).strip()]
                    prev = tip
                    for tex in lines:
                        prev = append_chain(prev, tex)
                    new_tips.append(prev)
                branch_tips = new_tips
                spine_id = None
                continue

            anchor_id = local_prev if local_prev is not None else spine_id
            if anchor_id is None:
                raise ValueError("equation_board cases require prior math")

            first_ids: list[str] = []
            tails: list[tuple[str, list[str]]] = []
            for case in cases:
                lines = [m for m in case["math"] if str(m).strip()]
                first_id = next_id()
                objects.append(dsl.math(first_id, lines[0].strip(), at="center", font_size=font_size))
                first_ids.append(first_id)
                tails.append((first_id, lines[1:]))

            actions.append(dsl.fork(anchor_id, *first_ids))
            actions.append(dsl.wait(0.4))

            new_tips = []
            for branch_id, lines in tails:
                prev = branch_id
                for tex in lines:
                    prev = append_chain(prev, tex)
                new_tips.append(prev)
            branch_tips = new_tips
            spine_id = anchor_id

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
