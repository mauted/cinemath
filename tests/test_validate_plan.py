"""Unit tests for teacher plan validation."""

from __future__ import annotations

import pytest

from cinemath.validate_plan import PlanValidationError, validate_plan


def test_validate_plan_accepts_cases() -> None:
    plan = validate_plan(
        {
            "version": 2,
            "problem": "Solve for $x$.",
            "answer": "x = 2 or x = 3",
            "steps": [
                {
                    "title": "Split cases",
                    "explanation": "Use the zero-product property.",
                    "math": ["(x-2)(x-3)=0"],
                    "cases": [
                        {"math": ["x-2=0", "x=2"]},
                        {"math": ["x-3=0", "x=3"]},
                    ],
                }
            ],
            "visuals": [{"tool": "equation_board"}],
        }
    )
    assert len(plan["steps"][0]["cases"]) == 2


def test_validate_plan_rejects_empty_case_math() -> None:
    with pytest.raises(PlanValidationError, match=r"cases\[0\]\.math must be non-empty"):
        validate_plan(
            {
                "version": 2,
                "problem": "Solve for $x$.",
                "answer": "x = 2",
                "steps": [
                    {
                        "title": "Bad step",
                        "explanation": "No usable case math.",
                        "math": ["x^2=4"],
                        "cases": [{"math": ["  "]}],
                    }
                ],
                "visuals": [{"tool": "equation_board"}],
            }
        )
