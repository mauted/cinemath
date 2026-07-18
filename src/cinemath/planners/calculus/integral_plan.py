"""Shared plan assembly for single-variable integral catalog planners."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.planners.calculus.bounds import _bound
from cinemath.planners.calculus.integral_common import (
    definite_integral_visuals,
    finalize_answer,
)
from cinemath.planners.common import _plan

INTEGRAL_INPUT_PROPERTIES: dict[str, Any] = {
    "problem_statement": {
        "type": "string",
        "description": "Normalized problem statement with math in $...$.",
    },
    "expression": {"type": "string"},
    "variable": {"type": "string"},
    "lower": {"type": ["number", "string", "null"]},
    "upper": {"type": ["number", "string", "null"]},
}


def parse_integral_args(
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
) -> tuple[sp.Expr, sp.Symbol, sp.Expr | None, sp.Expr | None]:
    var = sp.symbols(variable)
    expr = sp.sympify(expression)
    lo = _bound(lower) if lower is not None else None
    hi = _bound(upper) if upper is not None else None
    return expr, var, lo, hi


def build_integral_plan(
    problem: str,
    *,
    expression: str,
    variable: str,
    expr: sp.Expr,
    var: sp.Symbol,
    steps: list[dict[str, Any]],
    antideriv: sp.Expr,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> dict[str, Any]:
    answer, answer_tex = finalize_answer(expr, var, antideriv, lower, upper, steps)
    caption = "Value" if lower is not None and upper is not None else "Antiderivative"
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": definite_integral_visuals(
                expression=expression,
                variable=variable,
                lower=lower,
                upper=upper,
                answer_tex=answer_tex,
                caption=caption,
            ),
        }
    )
