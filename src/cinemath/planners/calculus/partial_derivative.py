"""Partial derivative catalog planner."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.planners.calculus._util import _problem
from cinemath.planners.common import _plan


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


def _handle_partial_derivative(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_partial_derivative(
        _problem(tool_input, name="plan_partial_derivative"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input["variable"]),
        function_name=str(tool_input.get("function_name") or "f"),
    )


PARTIAL_DERIVATIVE_ENTRY: dict[str, Any] = {
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
}
