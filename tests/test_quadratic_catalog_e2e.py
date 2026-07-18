"""End-to-end test: plan_quadratic catalog planner (full I/O)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from catalog_io import format_catalog_io, run_catalog_io

GOLDEN_PATH = Path(__file__).parent / "golden" / "quadratic_roots_io.json"

QUADRATIC_TOOL_INPUT = {
    "problem_statement": "Solve for $x$: $x^2 - 5x + 6 = 0$.",
    "a": 1,
    "b": -5,
    "c": 6,
}


@pytest.fixture
def quadratic_io() -> dict:
    return run_catalog_io("plan_quadratic", QUADRATIC_TOOL_INPUT)


def test_quadratic_catalog_e2e(quadratic_io: dict) -> None:
    io = quadratic_io

    assert io["planner"] == "plan_quadratic"
    assert io["tool_input"] == QUADRATIC_TOOL_INPUT

    plan = io["plan"]
    assert plan["problem"] == QUADRATIC_TOOL_INPUT["problem_statement"]
    assert plan["answer"] == "x = 2, x = 3"
    assert len(plan["steps"]) == 6

    factor_math = [line for step in plan["steps"] if step["title"] == "Split the middle term" for line in step["math"]]
    assert factor_math == ["x^{2} - 2x - 3x + 6 = 0"]
    group_step = next(s for s in plan["steps"] if s["title"] == "Factor by grouping")
    assert "(x - 2)(x - 3) = 0" in group_step["math"][-1]

    solve_step = next(s for s in plan["steps"] if s["title"] == "Solve for x")
    assert solve_step["math"] == []
    assert solve_step["cases"] == [
        {"math": ["x - 2 = 0", "x = 2"]},
        {"math": ["x - 3 = 0", "x = 3"]},
    ]

    plot = next(v for v in plan["visuals"] if v["tool"] == "plot_2d")
    assert plot["coefficients"] == {"a": 1.0, "b": -5.0, "c": 6.0}
    assert plot["roots"] == [2.0, 3.0]

    answer_visual = next(v for v in plan["visuals"] if v["tool"] == "show_answer")
    assert answer_visual["tex"] == r"x=2,\; x=3"

    animation = io["animation"]
    assert animation["scene_count"] >= 3
    assert any("plot" in str(sid) for sid in animation["scene_ids"])
    board_scene = next(scene for scene in animation["scenes"] if scene["id"] == "board_1")
    assert any(action["op"] == "fork" for action in board_scene["actions"])


def test_quadratic_io_matches_golden_snapshot(quadratic_io: dict) -> None:
    snapshot = {
        "planner": quadratic_io["planner"],
        "tool_input": quadratic_io["tool_input"],
        "plan": quadratic_io["plan"],
        "animation_summary": {
            "scene_count": quadratic_io["animation"]["scene_count"],
            "scene_ids": quadratic_io["animation"]["scene_ids"],
        },
    }
    assert snapshot == json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_print_quadratic_io_for_inspection(
    quadratic_io: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    print(format_catalog_io(quadratic_io), end="")
    captured = capsys.readouterr()
    assert "=== PLAN ===" in captured.out
    assert "x = 2, x = 3" in captured.out
