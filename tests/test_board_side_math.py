"""Tests for equation-board side_math scratch columns."""

from __future__ import annotations

from cinemath.planners.calculus.partial_fractions import plan_partial_fractions
from cinemath.render_engine.validate import validate_animation
from cinemath.templates import compile_plan
from cinemath.templates.board import equation_board_scene


def test_equation_board_side_math_emits_fork_and_fade() -> None:
    scene = equation_board_scene(
        "board_test",
        [
            {
                "title": "Set up",
                "explanation": "Start the integral.",
                "math": [r"\int \frac{1}{x}\,dx"],
            },
            {
                "title": "Algebra",
                "explanation": "Solve for coefficients on the side.",
                "side_begin": True,
                "side_hold": r"\frac{1}{x}",
                "side_math": [
                    r"\frac{1}{x} = \frac{a_0}{x}",
                    r"1 = a_0",
                    r"a_0 = 1",
                ],
            },
            {
                "title": "Continue",
                "explanation": "Return to the main integral.",
                "close_side": True,
                "break_spine": True,
                "math": [r"\int \frac{1}{x}\,dx = \log{|x|}"],
            },
        ],
    )
    assert scene is not None
    ops = [action["op"] for action in scene["actions"]]
    assert "fork" in ops
    assert "fade_out" in ops
    fork = next(action for action in scene["actions"] if action["op"] == "fork")
    assert fork["from"].endswith("_eq0")
    fade = next(action for action in scene["actions"] if action["op"] == "fade_out")
    assert len(fade["targets"]) >= 2
    write_ops = [action for action in scene["actions"] if action["op"] == "write"]
    assert any(target.endswith("_eq0") for action in write_ops for target in action["targets"])
    post_fade_write = scene["actions"][scene["actions"].index(fade) + 1 :]
    assert any(action["op"] == "write" for action in post_fade_write)


def test_partial_fraction_plan_uses_side_column() -> None:
    plan = plan_partial_fractions(
        r"Evaluate $\int \frac{4}{x^2+5x-14}\,dx$.",
        expression="4/(x**2+5*x-14)",
        variable="x",
    )
    assert any(step.get("side_math") for step in plan["steps"])
    assert any(step.get("side_begin") for step in plan["steps"])
    assert any(step.get("close_side") for step in plan["steps"])
    animation = validate_animation(compile_plan(plan))
    board = next(scene for scene in animation["scenes"] if scene["id"].startswith("board_"))
    assert any(action["op"] == "fork" for action in board["actions"])
    assert any(action["op"] == "fade_out" for action in board["actions"])
