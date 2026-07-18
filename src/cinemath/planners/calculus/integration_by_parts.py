"""Integration by parts catalog planner (SymPy manualintegrate-backed)."""

from __future__ import annotations

from typing import Any

import sympy as sp
from sympy.integrals.manualintegrate import (
    CyclicPartsRule,
    PartsRule,
    integral_steps,
    manualintegrate,
)

from cinemath.planners.calculus.bounds import _bound
from cinemath.planners.calculus.integral_common import (
    definite_integral_visuals,
    finalize_answer,
    find_ibp_step,
    integral_tex,
    verify_catalog_antideriv,
    walk_integral_steps,
)
from cinemath.planners.common import _plan


def _parts_round_steps(
    *,
    variable: sp.Symbol,
    integrand: sp.Expr,
    parts: PartsRule,
    round_label: str,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> tuple[list[dict[str, Any]], sp.Expr]:
    """One application of integration by parts."""
    u, dv = parts.u, parts.dv
    du = sp.diff(u, variable)
    v = parts.v_step.eval()
    remainder_integrand = sp.simplify(v * du)
    remainder_steps, remainder_antideriv = walk_integral_steps(
        remainder_integrand,
        variable,
        lower=lower,
        upper=upper,
        include_setup=False,
    )
    remainder_antideriv = verify_catalog_antideriv(
        remainder_antideriv,
        remainder_integrand,
        variable,
    )
    antideriv = sp.simplify(u * v - remainder_antideriv)

    setup = integral_tex(integrand, variable, lower=lower, upper=upper)
    steps: list[dict[str, Any]] = [
        {
            "title": f"{round_label}: choose $u$ and $dv$",
            "explanation": (
                "Use LIATE as a guide: pick $u$ so that $du$ simplifies, "
                "and $dv$ so that $v=\\int dv$ is easy."
            ),
            "math": [
                rf"u = {sp.latex(u)}",
                rf"dv = {sp.latex(dv)}\,d{variable}",
            ],
        },
        {
            "title": f"{round_label}: compute $du$ and $v$",
            "explanation": "Differentiate $u$ and integrate $dv$.",
            "math": [
                rf"du = {sp.latex(du)}\,d{variable}",
                rf"v = \int {sp.latex(dv)}\,d{variable} = {sp.latex(v)}",
            ],
        },
    ]
    steps.extend(remainder_steps)
    steps.append(
        {
            "title": f"{round_label}: apply $\\int u\\,dv = uv - \\int v\\,du$",
            "explanation": "Substitute into the integration-by-parts formula.",
            "math": [
                setup,
                rf"= {sp.latex(u)}\,{sp.latex(v)} - \int {sp.latex(remainder_integrand)}\,d{variable}",
                rf"= {sp.latex(antideriv)}",
            ],
        }
    )
    return steps, antideriv


def try_integration_by_parts_steps(
    expr: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
    include_setup: bool = True,
) -> tuple[list[dict[str, Any]], sp.Expr] | None:
    """Build IBP teaching steps, or None if the integrand does not need IBP."""
    step_root = integral_steps(expr, variable)
    ibp = find_ibp_step(step_root)
    if ibp is None:
        return None

    var_name = str(variable)
    setup = integral_tex(expr, variable, lower=lower, upper=upper)
    steps: list[dict[str, Any]] = []
    if include_setup:
        steps.append(
            {
                "title": "Set up the integral",
                "explanation": "Identify the integrand.",
                "math": [setup],
            }
        )
    steps.append(
        {
            "title": "Integration by parts formula",
            "explanation": "Recall $\\int u\\,dv = uv - \\int v\\,du$.",
            "math": [r"\int u\,dv = uv - \int v\,du"],
        }
    )

    if isinstance(ibp, CyclicPartsRule):
        for index, parts in enumerate(ibp.parts_rules, start=1):
            round_steps, _ = _parts_round_steps(
                variable=variable,
                integrand=expr,
                parts=parts,
                round_label=f"Round {index}",
                lower=lower,
                upper=upper,
            )
            steps.extend(round_steps)
        antideriv = sp.simplify(ibp.eval())
        steps.append(
            {
                "title": "Solve for the integral",
                "explanation": (
                    "After repeated integration by parts the original integral "
                    "reappears. Collect like terms and solve for it."
                ),
                "math": [rf"= {sp.latex(antideriv)}"],
            }
        )
        return steps, antideriv

    round_steps, antideriv = _parts_round_steps(
        variable=variable,
        integrand=expr,
        parts=ibp,
        round_label="Apply",
        lower=lower,
        upper=upper,
    )
    steps.extend(round_steps)
    verified = sp.simplify(manualintegrate(expr, variable))
    if sp.simplify(verified - antideriv) != 0:
        steps.append(
            {
                "title": "Simplify",
                "explanation": "Combine terms to reach the antiderivative.",
                "math": [rf"= {sp.latex(verified)}"],
            }
        )
        antideriv = verified
    return steps, antideriv


def _plan_cyclic(
    problem: str,
    *,
    expression: str,
    var_name: str,
    expr: sp.Expr,
    variable: sp.Symbol,
    cyclic: CyclicPartsRule,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> dict[str, Any]:
    var = variable
    setup = integral_tex(expr, var, lower=lower, upper=upper)
    steps: list[dict[str, Any]] = [
        {
            "title": "Set up the integral",
            "explanation": "The integrand is a product where integration by parts cycles back.",
            "math": [setup],
        },
        {
            "title": "Integration by parts formula",
            "explanation": "Recall $\\int u\\,dv = uv - \\int v\\,du$.",
            "math": [r"\int u\,dv = uv - \int v\,du"],
        },
    ]

    for i, parts in enumerate(cyclic.parts_rules, start=1):
        round_steps, _ = _parts_round_steps(
            variable=var,
            integrand=expr,
            parts=parts,
            round_label=f"Round {i}",
            lower=lower,
            upper=upper,
        )
        steps.extend(round_steps)

    coeff = sp.simplify(cyclic.coefficient)
    antideriv = sp.simplify(cyclic.eval())
    steps.append(
        {
            "title": "Solve for the integral",
            "explanation": (
                "After two rounds the original integral reappears. "
                "Collect like terms and solve for it."
            ),
            "math": [
                rf"I = {sp.latex(antideriv)}",
            ],
        }
    )
    if coeff != 0:
        steps[-1]["math"].insert(0, rf"\text{{Coefficient on }} I \text{{ is }} {sp.latex(coeff)}")

    answer, answer_tex = finalize_answer(expr, var, antideriv, lower, upper, steps)
    caption = "Value" if lower is not None and upper is not None else "Antiderivative"
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": definite_integral_visuals(
                expression=expression,
                variable=var_name,
                lower=lower,
                upper=upper,
                answer_tex=answer_tex,
                caption=caption,
            ),
        }
    )


def plan_integration_by_parts(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
    u: str | None = None,
    dv: str | None = None,
) -> dict[str, Any]:
    """Build a step-by-step integration-by-parts lesson."""
    var = sp.symbols(variable)
    expr = sp.sympify(expression)
    lo = _bound(lower) if lower is not None else None
    hi = _bound(upper) if upper is not None else None

    if u is not None and dv is not None:
        u_expr = sp.sympify(u)
        dv_expr = sp.sympify(dv)
        if sp.simplify(u_expr * dv_expr - expr) != 0:
            raise ValueError("u*dv must equal the integrand")
        du = sp.diff(u_expr, var)
        v = sp.integrate(dv_expr, var)
        remainder = sp.simplify(v * du)
        remainder_antideriv = manualintegrate(remainder, var)
        antideriv = sp.simplify(u_expr * v - remainder_antideriv)
        setup = integral_tex(expr, var, lower=lo, upper=hi)
        steps: list[dict[str, Any]] = [
            {
                "title": "Set up the integral",
                "explanation": "Identify the integrand.",
                "math": [setup],
            },
            {
                "title": "Integration by parts formula",
                "explanation": "Recall $\\int u\\,dv = uv - \\int v\\,du$.",
                "math": [r"\int u\,dv = uv - \int v\,du"],
            },
            {
                "title": "Choose $u$ and $dv$",
                "explanation": "Use the given (or chosen) split.",
                "math": [
                    rf"u = {sp.latex(u_expr)}",
                    rf"dv = {sp.latex(dv_expr)}\,d{variable}",
                ],
            },
            {
                "title": "Compute $du$ and $v$",
                "explanation": "Differentiate $u$ and integrate $dv$.",
                "math": [
                    rf"du = {sp.latex(du)}\,d{variable}",
                    rf"v = {sp.latex(v)}",
                ],
            },
            {
                "title": "Apply the formula",
                "explanation": "Substitute into $\\int u\\,dv = uv - \\int v\\,du$.",
                "math": [
                    setup,
                    rf"= {sp.latex(u_expr)}\,{sp.latex(v)} - \int {sp.latex(remainder)}\,d{variable}",
                    rf"= {sp.latex(antideriv)}",
                ],
            },
        ]
    else:
        built = try_integration_by_parts_steps(expr, var, lower=lo, upper=hi)
        if built is None:
            raise ValueError("expression does not admit an integration-by-parts strategy")
        steps, antideriv = built

    answer, answer_tex = finalize_answer(expr, var, antideriv, lo, hi, steps)
    caption = "Value" if lo is not None and hi is not None else "Antiderivative"
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": definite_integral_visuals(
                expression=expression,
                variable=variable,
                lower=lo,
                upper=hi,
                answer_tex=answer_tex,
                caption=caption,
            ),
        }
    )


def _handle_integration_by_parts(tool_input: dict[str, Any]) -> dict[str, Any]:
    problem = str(tool_input.get("problem_statement") or "").strip()
    if not problem:
        raise ValueError("plan_integration_by_parts requires problem_statement")
    lower = tool_input.get("lower")
    upper = tool_input.get("upper")
    return plan_integration_by_parts(
        problem,
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=lower if lower is not None else None,
        upper=upper if upper is not None else None,
        u=str(tool_input["u"]) if tool_input.get("u") is not None else None,
        dv=str(tool_input["dv"]) if tool_input.get("dv") is not None else None,
    )


INTEGRATION_BY_PARTS_ENTRY: dict[str, Any] = {
    "name": "plan_integration_by_parts",
    "description": (
        "Integration by parts for products (e.g. x*exp(x), polynomial*exp, polynomial*trig). "
        "Expression uses * and **. Optional lower/upper for definite integrals; "
        "omit both for indefinite (+C). Optional u and dv overrides."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "problem_statement": {
                "type": "string",
                "description": "Normalized problem statement with math in $...$.",
            },
            "expression": {"type": "string"},
            "variable": {"type": "string"},
            "lower": {"type": ["number", "string", "null"]},
            "upper": {"type": ["number", "string", "null"]},
            "u": {"type": "string"},
            "dv": {"type": "string"},
        },
        "required": ["problem_statement", "expression"],
    },
    "handler": _handle_integration_by_parts,
}
