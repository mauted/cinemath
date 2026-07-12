"""Map teacher plans → animation scripts via local visual tools."""

from __future__ import annotations

from . import dsl
from .problem_statement import problem_statement_scene
from .tools import compile_visuals


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    scenes = compile_visuals(plan)
    scenes = [problem_statement_scene(plan["problem"]), *scenes]
    return dsl.script(
        plan["problem"],
        plan["answer"],
        [step["title"] for step in plan["steps"]],
        scenes,
    )
