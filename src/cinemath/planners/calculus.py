"""Calculus catalog planners (single- and multivariable)."""

from __future__ import annotations

from typing import Any, Literal

import sympy as sp

from cinemath.planners.common import _fmt, _plan

Order = Literal["dy_dx", "dx_dy"]

def plan_derivative(
    problem: str, *, expression: str, variable: str = "x"
) -> dict[str, Any]:
    var = sp.symbols(variable)
    expr = sp.sympify(expression)
    deriv = sp.diff(expr, var)
    expr_tex, deriv_tex = sp.latex(expr), sp.latex(deriv)
    return _plan(
        {
            "problem": problem,
            "answer": deriv_tex,
            "steps": [
                {
                    "title": "Identify the function",
                    "explanation": f"Differentiate with respect to ${variable}$.",
                    "math": [f"f({variable}) = {expr_tex}"],
                },
                {
                    "title": "Apply the power rule",
                    "explanation": "Differentiate term by term.",
                    "math": [f"f'({variable}) = {deriv_tex}"],
                },
            ],
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": f"f'({variable}) = {deriv_tex}",
                    "caption": "Derivative",
                },
            ],
        }
    )


def plan_double_integral(
    problem: str,
    *,
    integrand: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    order: Order = "dy_dx",
) -> dict[str, Any]:
    x, y = sp.symbols("x y")
    expr = sp.sympify(integrand)
    if order == "dy_dx":
        inner = sp.integrate(expr, (y, y_min, y_max))
        value = sp.integrate(inner, (x, x_min, x_max))
        inner_latex = rf"\int_{{{_fmt(y_min)}}}^{{{_fmt(y_max)}}} {sp.latex(expr)}\,dy"
        outer_latex = rf"\int_{{{_fmt(x_min)}}}^{{{_fmt(x_max)}}} {inner_latex}\,dx"
    else:
        inner = sp.integrate(expr, (x, x_min, x_max))
        value = sp.integrate(inner, (y, y_min, y_max))
        inner_latex = rf"\int_{{{_fmt(x_min)}}}^{{{_fmt(x_max)}}} {sp.latex(expr)}\,dx"
        outer_latex = rf"\int_{{{_fmt(y_min)}}}^{{{_fmt(y_max)}}} {inner_latex}\,dy"
    numeric = float(sp.N(value))
    integrand_tex = sp.latex(expr)
    body = integrand.replace("**", "^").replace("*", "")
    return _plan(
        {
            "problem": problem,
            "answer": _fmt(numeric),
            "steps": [
                {
                    "title": "Set up the integral",
                    "explanation": (
                        f"Rectangle: $x \\in [{_fmt(x_min)}, {_fmt(x_max)}]$, "
                        f"$y \\in [{_fmt(y_min)}, {_fmt(y_max)}]$."
                    ),
                    "math": [rf"\iint_R {integrand_tex}\,dA"],
                },
                {
                    "title": "Iterate",
                    "explanation": "Write as an iterated integral.",
                    "math": [outer_latex],
                },
                {
                    "title": "Evaluate",
                    "explanation": "Integrate and substitute bounds.",
                    "math": [outer_latex, f"= {_fmt(numeric)}"],
                },
            ],
            "visuals": [
                {
                    "tool": "show_region_rectangle",
                    "integrand": integrand,
                    "x_min": x_min,
                    "x_max": x_max,
                    "y_min": y_min,
                    "y_max": y_max,
                    "order": order,
                    "value": numeric,
                },
                {"tool": "equation_board"},
                {
                    "tool": "plot_surface_3d",
                    "integrand": integrand,
                    "x_min": x_min,
                    "x_max": x_max,
                    "y_min": y_min,
                    "y_max": y_max,
                },
                {
                    "tool": "show_answer",
                    "tex": rf"\iint_R {body}\,dA = {_fmt(numeric)}",
                    "caption": "Final value",
                },
            ],
        }
    )


def _bound(raw: float | int | str) -> sp.Expr:
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in {"oo", "inf", "+inf", "infinity", "+infinity"}:
            return sp.oo
        if s in {"-oo", "-inf", "-infinity"}:
            return -sp.oo
        return sp.sympify(raw)
    return sp.sympify(raw)


def _bound_tex(b: sp.Expr, variable: str) -> str:
    if b is sp.oo:
        return r"\infty"
    if b is -sp.oo:
        return r"-\infty"
    if isinstance(b, sp.Integer):
        return str(int(b))
    return sp.latex(b)

def plan_definite_integral(
    problem: str,
    *,
    expression: str,
    variable: str = "x",
    lower: float | str,
    upper: float | str,
) -> dict[str, Any]:
    """Evaluate integral _lower^upper expression d(variable); bounds may be ``oo``."""
    var = sp.symbols(variable)
    expr = sp.sympify(expression)
    lo, hi = _bound(lower), _bound(upper)
    value = sp.integrate(expr, (var, lo, hi))
    expr_tex = sp.latex(expr)
    lo_tex, hi_tex = _bound_tex(lo, variable), _bound_tex(hi, variable)
    setup = rf"\int_{{{lo_tex}}}^{{{hi_tex}}} {expr_tex}\,d{variable}"
    improper = lo is sp.oo or lo is -sp.oo or hi is sp.oo or hi is -sp.oo
    steps: list[dict[str, Any]] = [
        {
            "title": "Set up the integral",
            "explanation": (
                "This is an improper integral - take a limit of a proper integral."
                if improper
                else "Identify the integrand and integration limits."
            ),
            "math": [setup],
        },
        {
            "title": "Evaluate",
            "explanation": "Antiderivative and bounds (SymPy verified).",
            "math": [setup, f"= {sp.latex(value)}"],
        },
    ]
    answer = sp.latex(value)
    return _plan(
        {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": rf"{setup} = {answer}",
                    "caption": "Value",
                },
            ],
        }
    )


def plan_partial_derivative(
    problem: str,
    *,
    expression: str,
    variable: str,
    function_name: str = "f",
) -> dict[str, Any]:
    """Partial derivative partial f/partial variable for a multivariable expression."""
    sym = sp.symbols(variable)
    expr = sp.sympify(expression)
    deriv = sp.diff(expr, sym)
    expr_tex = sp.latex(expr)
    deriv_tex = sp.latex(deriv)
    return _plan(
        {
            "problem": problem,
            "answer": deriv_tex,
            "steps": [
                {
                    "title": "Function",
                    "explanation": f"Treat other variables as constants; differentiate with respect to ${variable}$.",
                    "math": [rf"{function_name} = {expr_tex}"],
                },
                {
                    "title": "Partial derivative",
                    "explanation": rf"Apply $\partial/\partial {variable}$.",
                    "math": [rf"\frac{{\partial {function_name}}}{{\partial {variable}}} = {deriv_tex}"],
                },
            ],
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": rf"\frac{{\partial {function_name}}}{{\partial {variable}}} = {deriv_tex}",
                    "caption": "Partial derivative",
                },
            ],
        }
    )


def plan_triple_integral(
    problem: str,
    *,
    integrand: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
    order: str = "dz_dy_dx",
) -> dict[str, Any]:
    """Triple integral over a rectangular box (Calc 3)."""
    x, y, z = sp.symbols("x y z")
    expr = sp.sympify(integrand)
    # dz dy dx
    inner = sp.integrate(expr, (z, z_min, z_max))
    mid = sp.integrate(inner, (y, y_min, y_max))
    value = sp.integrate(mid, (x, x_min, x_max))
    numeric = float(sp.N(value))
    integrand_tex = sp.latex(expr)
    setup = (
        rf"\int_{{{_fmt(x_min)}}}^{{{_fmt(x_max)}}} \int_{{{_fmt(y_min)}}}^{{{_fmt(y_max)}}} "
        rf"\int_{{{_fmt(z_min)}}}^{{{_fmt(z_max)}}} {integrand_tex}\,dz\,dy\,dx"
    )
    return _plan(
        {
            "problem": problem,
            "answer": _fmt(numeric),
            "steps": [
                {
                    "title": "Region",
                    "explanation": (
                        f"Box: $x \\in [{_fmt(x_min)}, {_fmt(x_max)}]$, "
                        f"$y \\in [{_fmt(y_min)}, {_fmt(y_max)}]$, "
                        f"$z \\in [{_fmt(z_min)}, {_fmt(z_max)}]$."
                    ),
                    "math": [rf"\iiint_E {integrand_tex}\,dV"],
                },
                {
                    "title": "Iterate",
                    "explanation": "Write as an iterated integral (order: dz dy dx).",
                    "math": [setup],
                },
                {
                    "title": "Evaluate",
                    "explanation": "Integrate and substitute bounds.",
                    "math": [setup, f"= {_fmt(numeric)}"],
                },
            ],
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": rf"\iiint_E {integrand_tex}\,dV = {_fmt(numeric)}",
                    "caption": "Final value",
                },
            ],
        }
    )

def _problem(tool_input: dict[str, Any], *, name: str) -> str:
    problem = str(tool_input.get("problem_statement") or "").strip()
    if not problem:
        raise ValueError(f"{name} requires problem_statement")
    return problem


def _handle_definite_integral(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_definite_integral(
        _problem(tool_input, name="plan_definite_integral"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
        lower=tool_input["lower"],
        upper=tool_input["upper"],
    )


def _handle_partial_derivative(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_partial_derivative(
        _problem(tool_input, name="plan_partial_derivative"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input["variable"]),
        function_name=str(tool_input.get("function_name") or "f"),
    )


def _handle_triple_integral(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_triple_integral(
        _problem(tool_input, name="plan_triple_integral"),
        integrand=str(tool_input["integrand"]),
        x_min=float(tool_input["x_min"]),
        x_max=float(tool_input["x_max"]),
        y_min=float(tool_input["y_min"]),
        y_max=float(tool_input["y_max"]),
        z_min=float(tool_input["z_min"]),
        z_max=float(tool_input["z_max"]),
        order=str(tool_input.get("order") or "dz_dy_dx"),
    )


CALCULUS_ENTRIES: list[dict[str, Any]] = [
    {
        "name": "plan_definite_integral",
        "description": (
            "Definite or improper integral: expression uses * and **; "
            "lower/upper are numbers or 'oo' for infinity."
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
                "lower": {"type": ["number", "string"]},
                "upper": {"type": ["number", "string"]},
            },
            "required": ["problem_statement", "expression", "lower", "upper"],
        },
        "handler": _handle_definite_integral,
    },
    {
        "name": "plan_partial_derivative",
        "description": (
            "Partial derivative of expression w.r.t. one variable; "
            "e.g. expression='x**2*y + sin(x*y)', variable='x'."
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
                "function_name": {"type": "string"},
            },
            "required": ["problem_statement", "expression", "variable"],
        },
        "handler": _handle_partial_derivative,
    },
    {
        "name": "plan_triple_integral",
        "description": "Triple integral over a rectangular box; integrand uses * and **.",
        "input_schema": {
            "type": "object",
            "properties": {
                "problem_statement": {
                    "type": "string",
                    "description": "Normalized problem statement with math in $...$.",
                },
                "integrand": {"type": "string"},
                "x_min": {"type": "number"},
                "x_max": {"type": "number"},
                "y_min": {"type": "number"},
                "y_max": {"type": "number"},
                "z_min": {"type": "number"},
                "z_max": {"type": "number"},
                "order": {"type": "string"},
            },
            "required": [
                "problem_statement",
                "integrand",
                "x_min",
                "x_max",
                "y_min",
                "y_max",
                "z_min",
                "z_max",
            ],
        },
        "handler": _handle_triple_integral,
    },
]

from cinemath.planners.integration_by_parts import INTEGRATION_BY_PARTS_ENTRY, plan_integration_by_parts  # noqa: E402

CALCULUS_ENTRIES.append(INTEGRATION_BY_PARTS_ENTRY)
