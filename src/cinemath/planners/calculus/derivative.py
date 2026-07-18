"""Ordinary derivative catalog planner."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.planners.common import _plan


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
