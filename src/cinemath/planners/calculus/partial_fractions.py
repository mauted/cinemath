"""Partial-fractions catalog planner."""

from __future__ import annotations

from typing import Any

from cinemath.planners.calculus._util import _problem
from cinemath.planners.calculus.integral_common import try_partial_fraction_steps
from cinemath.planners.calculus.integral_plan import (
    INTEGRAL_INPUT_PROPERTIES,
    build_integral_plan,
    parse_integral_args,
)


def plan_partial_fractions(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
) -> dict[str, Any]:
    """Integrate a rational function with explicit partial-fraction steps."""
    expr, var, lo, hi = parse_integral_args(
        expression=expression,
        variable=variable,
        lower=lower,
        upper=upper,
    )
    result = try_partial_fraction_steps(expr, var, lower=lo, upper=hi)
    if result is None:
        raise ValueError(
            "plan_partial_fractions requires a rational integrand whose "
            "denominator factors into linears / irreducible quadratics"
        )
    steps, antideriv = result
    return build_integral_plan(
        problem,
        expression=expression,
        variable=variable,
        expr=expr,
        var=var,
        steps=steps,
        antideriv=antideriv,
        lower=lo,
        upper=hi,
    )


def _handle_partial_fractions(tool_input: dict[str, Any]) -> dict[str, Any]:
    lower = tool_input.get("lower")
    upper = tool_input.get("upper")
    return plan_partial_fractions(
        _problem(tool_input, name="plan_partial_fractions"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=lower if lower is not None else None,
        upper=upper if upper is not None else None,
    )


PARTIAL_FRACTIONS_ENTRY: dict[str, Any] = {
    "name": "plan_partial_fractions",
    "description": (
        "Partial-fraction decomposition for rational integrands "
        "(polynomial over polynomial). Expression uses * and **. "
        "Include lower/upper for definite or improper integrals; omit both for indefinite (+C)."
    ),
    "input_schema": {
        "type": "object",
        "properties": dict(INTEGRAL_INPUT_PROPERTIES),
        "required": ["problem_statement", "expression"],
    },
    "handler": _handle_partial_fractions,
}
