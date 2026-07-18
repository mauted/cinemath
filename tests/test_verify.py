"""Unit tests for freeform plan verification."""

from __future__ import annotations

import copy
import json

from cinemath.verify import verify_feedback_message, verify_plan


def _quadratic_plan(*, roots: list[float]) -> dict:
    return {
        "version": 2,
        "problem": "Solve for $x$: $x^2 - 5x + 6 = 0$.",
        "answer": " or ".join(f"x = {r:g}" for r in roots),
        "steps": [],
        "visuals": [
            {
                "tool": "plot_2d",
                "equation": "x^2-5x+6=0",
                "coefficients": {"a": 1.0, "b": -5.0, "c": 6.0},
                "roots": roots,
            },
            {"tool": "show_answer", "tex": "x=2", "caption": "Solutions"},
        ],
    }


def test_verify_does_not_mutate_plan() -> None:
    plan = _quadratic_plan(roots=[9.0, 10.0])
    snapshot = copy.deepcopy(plan)

    report = verify_plan(plan)

    assert report["checked"] is True
    assert report["ok"] is False
    assert plan == snapshot


def test_verify_feedback_message_includes_report() -> None:
    report = {
        "checked": True,
        "ok": False,
        "notes": ["Root mismatch."],
        "computed_roots": [2.0, 3.0],
        "claimed_roots": [9.0, 10.0],
        "tools": ["plot_2d"],
    }

    message = verify_feedback_message(report)

    assert "failed local verification" in message
    payload = json.loads(message.split("Verification report:\n", 1)[1])
    assert payload["ok"] is False
    assert "tools" not in payload
