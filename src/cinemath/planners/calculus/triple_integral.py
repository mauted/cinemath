"""Triple integral over a rectangular box."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.planners.calculus._util import _problem
from cinemath.planners.common import _fmt, _plan


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


TRIPLE_INTEGRAL_ENTRY: dict[str, Any] = {
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
}
