"""Basic definite / improper / indefinite integral catalog planner."""

from __future__ import annotations

from typing import Any

from cinemath.planners.calculus._util import _problem
from cinemath.planners.calculus.integral_common import (
    reject_unwalkable_integral,
    requires_specialized_technique,
    walk_integral_steps,
)
from cinemath.planners.calculus.integral_plan import (
    INTEGRAL_INPUT_PROPERTIES,
    build_integral_plan,
    parse_integral_args,
)


def plan_definite_integral(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
) -> dict[str, Any]:
    """Evaluate a basic integral with stepped antiderivative work."""
    expr, var, lo, hi = parse_integral_args(
        expression=expression,
        variable=variable,
        lower=lower,
        upper=upper,
    )
    specialized = requires_specialized_technique(expr, var)
    if specialized is not None:
        raise ValueError(
            f"Use {specialized} for this integrand; plan_definite_integral is for "
            "elementary antiderivatives only (power rule, sin/cos/exp, FTC)."
        )
    reject_unwalkable_integral(expr, var)
    steps, antideriv = walk_integral_steps(expr, var, lower=lo, upper=hi)
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


def _handle_definite_integral(tool_input: dict[str, Any]) -> dict[str, Any]:
    lower = tool_input.get("lower")
    upper = tool_input.get("upper")
    return plan_definite_integral(
        _problem(tool_input, name="plan_definite_integral"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=lower if lower is not None else None,
        upper=upper if upper is not None else None,
    )


DEFINITE_INTEGRAL_ENTRY: dict[str, Any] = {
    "name": "plan_definite_integral",
    "description": (
        "Basic definite, improper, or indefinite integral only: power rule, elementary "
        "sin/cos/exp, and FTC evaluation. Expression uses * and **. "
        "Include lower/upper for definite or improper integrals (use 'oo' for infinity); "
        "omit both for indefinite (+C). Do NOT use for u-sub, partial fractions, "
        "trig substitution, or integration by parts."
    ),
    "input_schema": {
        "type": "object",
        "properties": dict(INTEGRAL_INPUT_PROPERTIES),
        "required": ["problem_statement", "expression"],
    },
    "handler": _handle_definite_integral,
}
