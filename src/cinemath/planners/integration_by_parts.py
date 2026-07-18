"""Integration by parts catalog planner (SymPy manualintegrate-backed)."""

from __future__ import annotations

from typing import Any

import sympy as sp
from sympy.integrals.manualintegrate import (
    AlternativeRule,
    CyclicPartsRule,
    PartsRule,
    integral_steps,
    manualintegrate,
)

from cinemath.planners.calculus import _bound, _bound_tex
from cinemath.planners.common import _fmt, _plan


def _find_ibp_step(step: Any) -> PartsRule | CyclicPartsRule | None:
    if isinstance(step, (PartsRule, CyclicPartsRule)):
        return step
    if isinstance(step, AlternativeRule):
        for alt in step.alternatives:
            if isinstance(alt, PartsRule):
                return alt
    return None


def _integral_tex(
    integrand: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
) -> str:
    body = sp.latex(integrand)
    var = sp.latex(variable)
    if lower is None or upper is None:
        return rf"\int {body}\,d{var}"
    lo = _bound_tex(lower, str(variable))
    hi = _bound_tex(upper, str(variable))
    return rf"\int_{{{lo}}}^{{{hi}}} {body}\,d{var}"


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
    assert parts.second_step is not None
    remainder_antideriv = parts.second_step.eval()
    antideriv = sp.simplify(u * v - remainder_antideriv)
    remainder_integrand = sp.simplify(v * du)

    setup = _integral_tex(integrand, variable, lower=lower, upper=upper)
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
        {
            "title": f"{round_label}: apply $\\int u\\,dv = uv - \\int v\\,du$",
            "explanation": "Substitute into the integration-by-parts formula.",
            "math": [
                setup,
                rf"= {sp.latex(u)}\,{sp.latex(v)} - \int {sp.latex(remainder_integrand)}\,d{variable}",
                rf"= {sp.latex(antideriv)}",
            ],
        },
    ]
    return steps, antideriv


def _plan_cyclic(
    problem: str,
    *,
    expr: sp.Expr,
    variable: sp.Symbol,
    cyclic: CyclicPartsRule,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> dict[str, Any]:
    var = variable
    setup = _integral_tex(expr, var, lower=lower, upper=upper)
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

    answer, answer_tex = _finalize_answer(expr, var, antideriv, lower, upper, steps)
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": [
                {"tool": "equation_board"},
                {"tool": "show_answer", "tex": answer_tex, "caption": "Antiderivative"},
            ],
        }
    )


def _finalize_answer(
    expr: sp.Expr,
    variable: sp.Symbol,
    antideriv: sp.Expr,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
    steps: list[dict[str, Any]],
) -> tuple[str, str]:
    if lower is not None and upper is not None:
        value = sp.integrate(expr, (variable, lower, upper))
        value_tex = sp.latex(value)
        antideriv_tex = sp.latex(antideriv)
        lo_tex, hi_tex = _bound_tex(lower, str(variable)), _bound_tex(upper, str(variable))
        steps.append(
            {
                "title": "Evaluate at the bounds",
                "explanation": "Apply the Fundamental Theorem of Calculus.",
                "math": [
                    rf"\left[{antideriv_tex}\right]_{{{lo_tex}}}^{{{hi_tex}}}",
                    f"= {value_tex}",
                ],
            }
        )
        return value_tex, rf"\int_{{{lo_tex}}}^{{{hi_tex}}} {sp.latex(expr)}\,d{variable} = {value_tex}"

    antideriv_tex = sp.latex(antideriv)
    return f"{antideriv_tex} + C", f"{antideriv_tex} + C"


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

    step_root = integral_steps(expr, var)
    ibp = _find_ibp_step(step_root)
    if ibp is None:
        raise ValueError("expression does not admit an integration-by-parts strategy")

    if isinstance(ibp, CyclicPartsRule):
        return _plan_cyclic(problem, expr=expr, variable=var, cyclic=ibp, lower=lo, upper=hi)

    parts = ibp
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
        setup = _integral_tex(expr, var, lower=lo, upper=hi)
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
        setup = _integral_tex(expr, var, lower=lo, upper=hi)
        steps = [
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
        ]
        round_steps, antideriv = _parts_round_steps(
            variable=var,
            integrand=expr,
            parts=parts,
            round_label="Apply",
            lower=lo,
            upper=hi,
        )
        steps.extend(round_steps)

        # If manualintegrate needed a deeper tree, note the verified result.
        verified = sp.simplify(manualintegrate(expr, var))
        if sp.simplify(verified - antideriv) != 0:
            steps.append(
                {
                    "title": "Simplify",
                    "explanation": "Combine terms to reach the antiderivative.",
                    "math": [rf"= {sp.latex(verified)}"],
                }
            )
            antideriv = verified

    answer, answer_tex = _finalize_answer(expr, var, antideriv, lo, hi, steps)
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": [
                {"tool": "equation_board"},
                {"tool": "show_answer", "tex": answer_tex, "caption": "Result"},
            ],
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
        "Integration by parts for products (e.g. x*exp(x), polynomial*trig). "
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
