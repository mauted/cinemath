"""U-substitution catalog planner."""

from __future__ import annotations

from typing import Any

from sympy.integrals.manualintegrate import RewriteRule, integral_steps

from cinemath.planners.calculus._util import _problem
from cinemath.planners.calculus.integral_common import (
    find_u_step,
    reject_unwalkable_integral,
    requires_specialized_technique,
    walk_integral_steps,
)
from cinemath.planners.calculus.integral_plan import (
    INTEGRAL_INPUT_PROPERTIES,
    build_integral_plan,
    parse_integral_args,
)


def _admits_u_substitution(expr, variable) -> bool:
    specialized = requires_specialized_technique(expr, variable)
    if specialized == "plan_u_substitution":
        return True
    if specialized is not None:
        return False
    root = integral_steps(expr, variable)
    return isinstance(root, RewriteRule)


def plan_u_substitution(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
) -> dict[str, Any]:
    """Integrate with explicit u-substitution (and any preparatory rewrites)."""
    expr, var, lo, hi = parse_integral_args(
        expression=expression,
        variable=variable,
        lower=lower,
        upper=upper,
    )
    reject_unwalkable_integral(expr, var)
    if not _admits_u_substitution(expr, var):
        raise ValueError(
            "plan_u_substitution requires a composition / chain-rule form or a "
            "trig-power rewrite that leads to substitution"
        )
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


def _handle_u_substitution(tool_input: dict[str, Any]) -> dict[str, Any]:
    lower = tool_input.get("lower")
    upper = tool_input.get("upper")
    return plan_u_substitution(
        _problem(tool_input, name="plan_u_substitution"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=lower if lower is not None else None,
        upper=upper if upper is not None else None,
    )


U_SUBSTITUTION_ENTRY: dict[str, Any] = {
    "name": "plan_u_substitution",
    "description": (
        "U-substitution (and trig power rewrites that lead to substitution). "
        "Use for composition / chain-rule forms such as 2x*exp(x**2), "
        "sin^n(x)cos^m(x), or sqrt(e^{ax}-c). Expression uses * and **. "
        "Include lower/upper for definite or improper integrals; omit both for indefinite (+C)."
    ),
    "input_schema": {
        "type": "object",
        "properties": dict(INTEGRAL_INPUT_PROPERTIES),
        "required": ["problem_statement", "expression"],
    },
    "handler": _handle_u_substitution,
}
