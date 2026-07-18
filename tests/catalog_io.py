"""Run a catalog planner through plan → animation and collect I/O."""

from __future__ import annotations

import json
from typing import Any

from cinemath.catalog import run_catalog
from cinemath.render_engine.validate import validate_animation
from cinemath.templates import compile_plan


def run_catalog_io(planner: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Execute one catalog planner end-to-end (no LLM, no Manim render)."""
    plan = run_catalog(planner, tool_input)
    if plan is None:
        raise ValueError(f"planner {planner!r} returned None (freeform)")

    animation = validate_animation(compile_plan(plan))
    return {
        "planner": planner,
        "tool_input": tool_input,
        "plan": plan,
        "animation": {
            "scene_count": len(animation.get("scenes") or []),
            "scene_ids": [s.get("id") for s in animation.get("scenes") or []],
            "scenes": animation.get("scenes"),
        },
    }


def format_catalog_io(io: dict[str, Any]) -> str:
    """Pretty-print full catalog pipeline I/O."""
    blocks = [
        ("PLANNER", io["planner"]),
        ("TOOL INPUT", io["tool_input"]),
        ("PLAN", io["plan"]),
        (
            "ANIMATION (summary)",
            {
                "scene_count": io["animation"]["scene_count"],
                "scene_ids": io["animation"]["scene_ids"],
            },
        ),
        ("ANIMATION (scenes)", io["animation"]["scenes"]),
    ]
    parts: list[str] = []
    for title, payload in blocks:
        parts.append(f"=== {title} ===")
        parts.append(json.dumps(payload, indent=2, ensure_ascii=False))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
