"""Catalog registry: classify tools and dispatch."""

from __future__ import annotations

from typing import Any, Callable

from cinemath.planners.algebra import (
    plan_linear,
    plan_linear_system_2d,
    plan_linear_system_3d,
    plan_percent_off,
    plan_quadratic,
)
from cinemath.planners.arithmetic.planner import (
    plan_long_add,
    plan_long_divide,
    plan_long_multiply,
    plan_long_subtract,
)
from cinemath.planners.calculus import (
    CALCULUS_ENTRIES,
    Order,
    plan_definite_integral,
    plan_derivative,
    plan_double_integral,
    plan_integration_by_parts,
    plan_partial_derivative,
    plan_partial_fractions,
    plan_trig_substitution,
    plan_triple_integral,
    plan_u_substitution,
)
from cinemath.planners.common import CatalogFreeform, _problem

Handler = Callable[[dict[str, Any]], dict[str, Any]]

_PROBLEM = {
    "type": "string",
    "description": "Normalized problem statement with math in $...$.",
}

CLASSIFY_SYSTEM = """
You classify math problems. Call exactly ONE tool with extracted parameters.
Do NOT solve the problem. Do NOT write JSON lesson plans.

Catalog planners (each returns a full teacher plan.json):
plan_quadratic, plan_linear, plan_linear_system_2d, plan_linear_system_3d,
plan_percent_off, plan_derivative, plan_double_integral,
plan_integration_by_parts, plan_partial_fractions, plan_trig_substitution,
plan_u_substitution, plan_definite_integral, plan_partial_derivative,
plan_triple_integral, plan_long_multiply, plan_long_divide, plan_long_add,
plan_long_subtract.

Integration technique (pick the first matching rule):
- plan_integration_by_parts: products needing IBP (x*exp(x), poly*exp, poly*trig, ln*poly).
- plan_partial_fractions: rational functions (poly)/(poly) after factoring the denominator.
- plan_trig_substitution: sqrt of a quadratic (a^2-x^2, a^2+x^2, x^2-a^2), including
  after completing the square.
- plan_u_substitution: chain-rule / composition forms, and trig powers that rewrite then
  substitute (e.g. 2x*exp(x**2), sin^n cos^m, sqrt(e^{ax}-c)).
- plan_definite_integral: elementary antiderivatives only (power rule, sin/cos/exp, FTC /
  improper limits). Never use when a specialized technique applies.
- teach_freeform: stacked or exotic integrals that need multiple techniques chained
  (e.g. sqrt(tan x)), or when no single catalog planner can walk the full solution.

Omit lower and upper for indefinite integrals (+C). Include them for definite/improper
(use 'oo' for infinity). Do NOT use teach_freeform for standard Calc 2 integration
exercises when a catalog planner fits.
Use plan_derivative for ordinary derivatives d/dx.
Use plan_partial_derivative for partial derivatives (Calc 3).
Use plan_double_integral / plan_triple_integral for box regions in R^2 and R^3.
Use teach_freeform for proofs, series proofs, vector calculus, or anything else.
""".strip()

def _handle_quadratic(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_quadratic(
        _problem(tool_input, name="plan_quadratic"),
        a=float(tool_input["a"]),
        b=float(tool_input["b"]),
        c=float(tool_input["c"]),
    )


def _handle_linear(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_linear(
        _problem(tool_input, name="plan_linear"),
        left=str(tool_input["left"]),
        right=str(tool_input["right"]),
        variable=str(tool_input.get("variable") or "x"),
    )


def _handle_linear_system_2d(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_linear_system_2d(
        _problem(tool_input, name="plan_linear_system_2d"),
        a1=float(tool_input["a1"]),
        b1=float(tool_input["b1"]),
        c1=float(tool_input["c1"]),
        a2=float(tool_input["a2"]),
        b2=float(tool_input["b2"]),
        c2=float(tool_input["c2"]),
    )


def _handle_linear_system_3d(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_linear_system_3d(
        _problem(tool_input, name="plan_linear_system_3d"),
        a1=float(tool_input["a1"]),
        b1=float(tool_input["b1"]),
        c1=float(tool_input["c1"]),
        d1=float(tool_input["d1"]),
        a2=float(tool_input["a2"]),
        b2=float(tool_input["b2"]),
        c2=float(tool_input["c2"]),
        d2=float(tool_input["d2"]),
        a3=float(tool_input["a3"]),
        b3=float(tool_input["b3"]),
        c3=float(tool_input["c3"]),
        d3=float(tool_input["d3"]),
    )


def _handle_percent_off(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_percent_off(
        _problem(tool_input, name="plan_percent_off"),
        original_price=float(tool_input["original_price"]),
        percent_off=float(tool_input["percent_off"]),
    )


def _handle_derivative(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_derivative(
        _problem(tool_input, name="plan_derivative"),
        expression=str(tool_input["expression"]),
        variable=str(tool_input.get("variable") or "x"),
    )


def _handle_double_integral(tool_input: dict[str, Any]) -> dict[str, Any]:
    order = str(tool_input.get("order") or "dy_dx")
    if order not in {"dy_dx", "dx_dy"}:
        raise ValueError("order must be dy_dx or dx_dy")
    return plan_double_integral(
        _problem(tool_input, name="plan_double_integral"),
        integrand=str(tool_input["integrand"]),
        x_min=float(tool_input["x_min"]),
        x_max=float(tool_input["x_max"]),
        y_min=float(tool_input["y_min"]),
        y_max=float(tool_input["y_max"]),
        order=order,  # type: ignore[arg-type]
    )


def _handle_long_multiply(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_long_multiply(
        _problem(tool_input, name="plan_long_multiply"),
        multiplicand=str(tool_input["multiplicand"]),
        multiplier=str(tool_input["multiplier"]),
    )


def _handle_long_divide(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_long_divide(
        _problem(tool_input, name="plan_long_divide"),
        dividend=str(tool_input["dividend"]),
        divisor=str(tool_input["divisor"]),
    )


def _handle_long_add(tool_input: dict[str, Any]) -> dict[str, Any]:
    raw = tool_input.get("addends") or []
    return plan_long_add(
        _problem(tool_input, name="plan_long_add"),
        addends=[str(a) for a in raw],
    )


def _handle_long_subtract(tool_input: dict[str, Any]) -> dict[str, Any]:
    return plan_long_subtract(
        _problem(tool_input, name="plan_long_subtract"),
        minuend=str(tool_input["minuend"]),
        subtrahend=str(tool_input["subtrahend"]),
    )


def _entry(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
    handler: Handler,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {"problem_statement": _PROBLEM, **properties},
            "required": ["problem_statement", *required],
        },
        "handler": handler,
    }


_CATALOG: list[dict[str, Any]] = [
    _entry(
        "plan_quadratic",
        "Quadratic $ax^2+bx+c=0$ with real roots.",
        {"a": {"type": "number"}, "b": {"type": "number"}, "c": {"type": "number"}},
        ["a", "b", "c"],
        _handle_quadratic,
    ),
    _entry(
        "plan_linear",
        "Single linear equation in one unknown; SymPy sides e.g. left='2*x+5', right='17'.",
        {
            "left": {"type": "string"},
            "right": {"type": "string"},
            "variable": {"type": "string"},
        },
        ["left", "right"],
        _handle_linear,
    ),
    _entry(
        "plan_linear_system_2d",
        "2x2 linear system: a1*x + b1*y = c1 and a2*x + b2*y = c2 (unique solution).",
        {
            "a1": {"type": "number"},
            "b1": {"type": "number"},
            "c1": {"type": "number"},
            "a2": {"type": "number"},
            "b2": {"type": "number"},
            "c2": {"type": "number"},
        },
        ["a1", "b1", "c1", "a2", "b2", "c2"],
        _handle_linear_system_2d,
    ),
    _entry(
        "plan_linear_system_3d",
        "3x3 linear system: three planes a*x + b*y + c*z = d (unique solution).",
        {
            "a1": {"type": "number"},
            "b1": {"type": "number"},
            "c1": {"type": "number"},
            "d1": {"type": "number"},
            "a2": {"type": "number"},
            "b2": {"type": "number"},
            "c2": {"type": "number"},
            "d2": {"type": "number"},
            "a3": {"type": "number"},
            "b3": {"type": "number"},
            "c3": {"type": "number"},
            "d3": {"type": "number"},
        },
        ["a1", "b1", "c1", "d1", "a2", "b2", "c2", "d2", "a3", "b3", "c3", "d3"],
        _handle_linear_system_3d,
    ),
    _entry(
        "plan_percent_off",
        "Percent discount: original price and percent off (e.g. $80 at 25% off).",
        {
            "original_price": {"type": "number"},
            "percent_off": {"type": "number"},
        },
        ["original_price", "percent_off"],
        _handle_percent_off,
    ),
    _entry(
        "plan_derivative",
        "Differentiate a polynomial, e.g. expression='3*x**4 - 2*x**2 + 7'.",
        {
            "expression": {"type": "string"},
            "variable": {"type": "string"},
        },
        ["expression"],
        _handle_derivative,
    ),
    _entry(
        "plan_double_integral",
        "Double integral over a rectangle; integrand uses * and **.",
        {
            "integrand": {"type": "string"},
            "x_min": {"type": "number"},
            "x_max": {"type": "number"},
            "y_min": {"type": "number"},
            "y_max": {"type": "number"},
            "order": {"type": "string", "enum": ["dy_dx", "dx_dy"]},
        },
        ["integrand", "x_min", "x_max", "y_min", "y_max"],
        _handle_double_integral,
    ),
    _entry(
        "plan_long_multiply",
        "Long multiplication.",
        {
            "multiplicand": {"type": "string"},
            "multiplier": {"type": "string"},
        },
        ["multiplicand", "multiplier"],
        _handle_long_multiply,
    ),
    _entry(
        "plan_long_divide",
        "Long division.",
        {
            "dividend": {"type": "string"},
            "divisor": {"type": "string"},
        },
        ["dividend", "divisor"],
        _handle_long_divide,
    ),
    _entry(
        "plan_long_add",
        "Long addition.",
        {
            "addends": {"type": "array", "items": {"type": "string"}, "minItems": 2},
        },
        ["addends"],
        _handle_long_add,
    ),
    _entry(
        "plan_long_subtract",
        "Long subtraction.",
        {
            "minuend": {"type": "string"},
            "subtrahend": {"type": "string"},
        },
        ["minuend", "subtrahend"],
        _handle_long_subtract,
    ),
]

for _calc in CALCULUS_ENTRIES:
    _CATALOG.append(
        _entry(
            _calc["name"],
            _calc["description"],
            {
                k: v
                for k, v in _calc["input_schema"]["properties"].items()
                if k != "problem_statement"
            },
            [r for r in _calc["input_schema"]["required"] if r != "problem_statement"],
            _calc["handler"],
        )
    )

_HANDLERS: dict[str, Handler] = {entry["name"]: entry["handler"] for entry in _CATALOG}

CLASSIFY_TOOLS: list[dict[str, Any]] = [
    {
        "name": entry["name"],
        "description": entry["description"],
        "input_schema": entry["input_schema"],
    }
    for entry in _CATALOG
] + [
    {
        "name": "teach_freeform",
        "description": "Fallback when no catalog planner fits; LLM writes plan.json.",
        "input_schema": {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        },
    }
]


def run_catalog(name: str, tool_input: dict[str, Any]) -> dict[str, Any] | None:
    """Dispatch a classify tool call. Returns plan.json, or None for freeform."""
    if name == "teach_freeform":
        return None
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown catalog planner: {name}")
    try:
        return handler(tool_input)
    except CatalogFreeform:
        return None
