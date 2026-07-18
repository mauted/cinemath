"""Double integral over a rectangle."""

from __future__ import annotations

from typing import Any, Literal

import sympy as sp

from cinemath.planners.common import _fmt, _plan

Order = Literal["dy_dx", "dx_dy"]


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
