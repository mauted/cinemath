"""Trigonometric substitution steps for square-root quadratics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import sympy as sp
from sympy.integrals.manualintegrate import SqrtQuadraticRule, integral_steps

from cinemath.planners.calculus._util import _problem
from cinemath.planners.calculus.integral_common import (
    integral_tex,
    walk_integral_steps,
)
from cinemath.planners.calculus.integral_plan import (
    INTEGRAL_INPUT_PROPERTIES,
    build_integral_plan,
    parse_integral_args,
)

TrigKind = Literal["sin", "tan", "sec"]


@dataclass(frozen=True)
class _SqrtQuadratic:
    coeff: sp.Expr
    quad_coeff: sp.Expr
    linear_coeff: sp.Expr
    const_coeff: sp.Expr


@dataclass(frozen=True)
class _TrigSetup:
    kind: TrigKind
    shift: sp.Expr
    inner_name: str
  # u = var - shift; when shift is 0, inner_name matches var
    scale: sp.Expr
    var_expr: sp.Expr
    d_var: sp.Expr
    radical: sp.Expr


def _extract_sqrt_quadratic(integrand: sp.Expr, variable: sp.Symbol) -> _SqrtQuadratic | None:
    coeff, body = integrand.as_independent(variable, as_Add=False)
    if not body.is_Pow or body.exp != sp.Rational(1, 2):
        return None
    inner = body.base
    if not inner.has(variable):
        return None
    try:
        poly = sp.Poly(inner, variable)
    except sp.polys.polyerrors.PolynomialError:
        return None
    if poly.degree() != 2:
        return None
    quad, linear, const = poly.all_coeffs()
    if quad == 0:
        return None
    return _SqrtQuadratic(sp.simplify(coeff), quad, linear, const)


def _needs_trig_substitution(expr: sp.Expr, variable: sp.Symbol) -> bool:
    root = integral_steps(expr, variable)
    if isinstance(root, SqrtQuadraticRule):
        return True
    return _extract_sqrt_quadratic(expr, variable) is not None


def _classify_quadratic_form(
    const: sp.Expr,
    quad: sp.Expr,
) -> TrigKind | None:
    """Classify A + B*u^2 inside a square root."""
    if quad.is_positive and const.is_positive:
        return "tan"
    if quad.is_positive and const.is_negative:
        return "sec"
    if quad.is_negative and const.is_positive:
        return "sin"
    return None


def _build_trig_setup(
    form: _SqrtQuadratic,
    variable: sp.Symbol,
) -> _TrigSetup | None:
    quad = form.quad_coeff
    linear = form.linear_coeff
    const = form.const_coeff

    shift = sp.Integer(0)
    inner_name = str(variable)
    if linear != 0:
        shift = sp.simplify(-linear / (2 * quad))
        inner_name = "u"

    shifted_const = sp.simplify(const - linear**2 / (4 * quad))
    kind = _classify_quadratic_form(shifted_const, quad)
    if kind is None:
        return None

    if kind == "tan":
        scale = sp.sqrt(sp.simplify(shifted_const / quad))
    elif kind == "sec":
        scale = sp.sqrt(sp.simplify(-shifted_const / quad))
    else:
        scale = sp.sqrt(sp.simplify(shifted_const / -quad))

    theta = sp.Symbol("theta")
    if kind == "tan":
        radical_theta = sp.sqrt(shifted_const) * sp.sec(theta)
        d_var = sp.simplify(scale * sp.sec(theta) ** 2)
        var_expr = sp.simplify(scale * sp.tan(theta))
    elif kind == "sec":
        radical_theta = sp.sqrt(-shifted_const) * sp.tan(theta)
        d_var = sp.simplify(scale * sp.sec(theta) * sp.tan(theta))
        var_expr = sp.simplify(scale * sp.sec(theta))
    else:
        radical_theta = sp.sqrt(shifted_const) * sp.cos(theta)
        d_var = sp.simplify(scale * sp.cos(theta))
        var_expr = sp.simplify(scale * sp.sin(theta))

    return _TrigSetup(
        kind=kind,
        shift=shift,
        inner_name=inner_name,
        scale=scale,
        var_expr=var_expr,
        d_var=d_var,
        radical=radical_theta,
    )


def _shifted_radicand(
    form: _SqrtQuadratic,
    inner: sp.Symbol,
) -> sp.Expr:
    return sp.simplify(
        form.const_coeff
        - form.linear_coeff**2 / (4 * form.quad_coeff)
        + form.quad_coeff * inner**2
    )


def _form_explanation(kind: TrigKind) -> str:
    mapping = {
        "sin": (
            "The radicand has the form $a^{2} - bx^{2}$, so use a sine substitution."
        ),
        "tan": (
            "The radicand has the form $a^{2} + bx^{2}$, so use a tangent substitution."
        ),
        "sec": (
            "The radicand has the form $bx^{2} - a^{2}$, so use a secant substitution."
        ),
    }
    return mapping[kind]


def _substitution_lines(
    setup: _TrigSetup,
    variable: sp.Symbol,
    *,
    radicand_tex: str,
) -> list[str]:
    trig_name = {"sin": r"\sin", "tan": r"\tan", "sec": r"\sec"}[setup.kind]
    lines: list[str] = []
    if setup.shift != 0:
        lines.append(
            rf"{setup.inner_name} = {sp.latex(variable)} - {sp.latex(setup.shift)}"
        )
    lines.extend(
        [
            rf"{sp.latex(variable)} = {sp.latex(setup.scale)} "
            rf"{trig_name}{{\left(\theta\right)}}",
            rf"d{sp.latex(variable)} = {sp.latex(setup.d_var)}\,d\theta",
            rf"\sqrt{{{radicand_tex}}} = {sp.latex(setup.radical)}",
        ]
    )
    return lines


def _back_substitute(
    antideriv: sp.Expr,
    setup: _TrigSetup,
    variable: sp.Symbol,
    theta: sp.Symbol,
) -> sp.Expr:
    inner = variable - setup.shift
    scale = setup.scale
    if setup.kind == "sin":
        substitutions = [
            (sp.sin(theta), inner / scale),
            (sp.cos(theta), sp.sqrt(1 - inner**2 / scale**2)),
            (sp.tan(theta), inner / sp.sqrt(scale**2 - inner**2)),
        ]
    elif setup.kind == "tan":
        substitutions = [
            (sp.tan(theta), inner / scale),
            (sp.sec(theta), sp.sqrt(1 + inner**2 / scale**2)),
            (sp.cos(theta), scale / sp.sqrt(scale**2 + inner**2)),
            (sp.sin(theta), inner / sp.sqrt(scale**2 + inner**2)),
        ]
    else:
        substitutions = [
            (sp.sec(theta), inner / scale),
            (sp.tan(theta), sp.sqrt(inner**2 / scale**2 - 1)),
            (sp.cos(theta), scale / inner),
            (sp.sin(theta), sp.sqrt(inner**2 - scale**2) / inner),
        ]
    result = antideriv
    for lhs, rhs in substitutions:
        result = sp.simplify(result.xreplace({lhs: rhs}))
    return sp.simplify(result)


def try_trig_substitution_steps(
    expr: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
) -> tuple[list[dict[str, Any]], sp.Expr] | None:
    """Show trig substitution for integrals of the form coeff*sqrt(quadratic)."""
    form = _extract_sqrt_quadratic(expr, variable)
    if form is None or not _needs_trig_substitution(expr, variable):
        return None

    setup = _build_trig_setup(form, variable)
    if setup is None:
        return None

    theta = sp.Symbol("theta")
    setup_tex = integral_tex(expr, variable, lower=lower, upper=upper)
    inner = sp.Symbol(setup.inner_name) if setup.shift != 0 else variable
    radicand_tex = sp.latex(
        _shifted_radicand(form, inner) if setup.shift != 0 else expr**2
    )
    steps: list[dict[str, Any]] = [
        {
            "title": "Set up the integral",
            "explanation": "Identify the integrand and variable of integration.",
            "math": [setup_tex],
        }
    ]

    if setup.shift != 0:
        steps.append(
            {
                "title": "Complete the square",
                "explanation": (
                    "Rewrite the quadratic under the square root as a perfect square "
                    "plus a constant."
                ),
                "math": [
                    rf"{setup.inner_name} = {sp.latex(variable)} - {sp.latex(setup.shift)}",
                    rf"\sqrt{{{sp.latex(expr**2)}}} = \sqrt{{{sp.latex(_shifted_radicand(form, inner))}}}",
                ],
            }
        )

    steps.append(
        {
            "title": "Use trigonometric substitution",
            "explanation": _form_explanation(setup.kind),
            "math": _substitution_lines(
                setup,
                variable,
                radicand_tex=radicand_tex,
            ),
        }
    )

    rewritten = sp.simplify(form.coeff * setup.radical * setup.d_var)
    theta_steps, antideriv_theta = walk_integral_steps(
        rewritten, theta, include_setup=False
    )
    verified_theta = sp.simplify(sp.integrate(rewritten, theta))
    if sp.simplify(sp.diff(verified_theta, theta) - rewritten) != 0:
        return None
    if sp.simplify(verified_theta - antideriv_theta) != 0:
        antideriv_theta = verified_theta
    steps.append(
        {
            "title": "Rewrite the integral",
            "explanation": "Substitute into the integral and simplify in terms of $\\theta$.",
            "math": [
                rf"\int {sp.latex(expr)}\,d{sp.latex(variable)} "
                rf"= \int {sp.latex(rewritten)}\,d{sp.latex(theta)}",
            ],
        }
    )
    for sub in theta_steps[1:]:
        math = sub.get("math") or []
        if (
            sub["title"] == "Integrate"
            and math
            and math[0].startswith(r"= \int")
        ):
            continue
        steps.append(
            {
                "title": sub["title"],
                "explanation": sub["explanation"],
                "math": math,
            }
        )
    steps.append(
        {
            "title": "Integrate in $\\theta$",
            "explanation": "Antidifferentiate the trigonometric integrand.",
            "math": [
                rf"\int {sp.latex(rewritten)}\,d\theta "
                rf"= {sp.latex(antideriv_theta)}",
            ],
        }
    )

    antideriv = _back_substitute(antideriv_theta, setup, variable, theta)
    expected = sp.simplify(sp.integrate(expr, variable))
    if sp.simplify(antideriv - expected) != 0:
        antideriv = expected

    steps.append(
        {
            "title": "Substitute back",
            "explanation": (
                f"Use a right triangle (or the identities from the substitution) to "
                f"rewrite the result in terms of ${sp.latex(variable)}$."
            ),
            "math": [rf"= {sp.latex(antideriv)}"],
        }
    )
    return steps, antideriv


def plan_trig_substitution(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str | None = None,
    upper: float | str | None = None,
) -> dict[str, Any]:
    """Integrate √(quadratic) forms with an explicit trig substitution."""
    expr, var, lo, hi = parse_integral_args(
        expression=expression,
        variable=variable,
        lower=lower,
        upper=upper,
    )
    result = try_trig_substitution_steps(expr, var, lower=lo, upper=hi)
    if result is None:
        raise ValueError(
            "plan_trig_substitution requires an integrand of the form "
            "coeff*sqrt(a + b*x + c*x**2) suitable for sin/tan/sec substitution"
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


def _handle_trig_substitution(tool_input: dict[str, Any]) -> dict[str, Any]:
    lower = tool_input.get("lower")
    upper = tool_input.get("upper")
    return plan_trig_substitution(
        _problem(tool_input, name="plan_trig_substitution"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=lower if lower is not None else None,
        upper=upper if upper is not None else None,
    )


TRIG_SUBSTITUTION_ENTRY: dict[str, Any] = {
    "name": "plan_trig_substitution",
    "description": (
        "Trigonometric substitution for sqrt of a quadratic "
        "(forms a^2 - x^2, a^2 + x^2, x^2 - a^2, including after completing the square). "
        "Expression uses * and **. Include lower/upper for definite or improper integrals; "
        "omit both for indefinite (+C)."
    ),
    "input_schema": {
        "type": "object",
        "properties": dict(INTEGRAL_INPUT_PROPERTIES),
        "required": ["problem_statement", "expression"],
    },
    "handler": _handle_trig_substitution,
}
