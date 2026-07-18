"""Algebra and precalculus catalog planners."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.planners.common import (
    _factor_zero_lines,
    _find_factor_pair,
    _fmt,
    _group_quadratic_tex,
    _int_coef,
    _line_eq_tex,
    _pair_summary_tex,
    _plane_eq_tex,
    _plan,
    _quadratic_check_tex,
    _quadratic_equation_plain,
    _quadratic_equation_tex,
    _quadratic_factor_steps,
    _quadratic_factored_tex,
    _split_quadratic_tex,
    _sym_coef,
    _term_tex,
    _x_shift_tex,
)

def plan_quadratic(problem: str, *, a: float, b: float, c: float) -> dict[str, Any]:
    x = sp.symbols("x")
    poly = _sym_coef(a) * x**2 + _sym_coef(b) * x + _sym_coef(c)
    roots = sorted(float(sp.N(r)) for r in sp.solve(poly, x) if r.is_real)
    if not roots:
        raise ValueError("quadratic has no real roots")
    equation = _quadratic_equation_tex(a, b, c)
    factored = _quadratic_factored_tex(a, b, c)
    root_tex = r",\; ".join(f"x={_fmt(r)}" for r in roots)
    factor_steps = _quadratic_factor_steps(a, b, c)
    if not factor_steps:
        factor_steps = [
            {
                "title": "Factor",
                "explanation": "Factor into linear factors.",
                "math": [f"{factored} = 0"],
            }
        ]

    steps: list[dict[str, Any]] = [
        {
            "title": "Identify the quadratic",
            "explanation": (
                f"Standard form $ax^{{2}}+bx+c=0$ with "
                f"$a={_fmt(a)}$, $b={_fmt(b)}$, $c={_fmt(c)}$."
            ),
            "math": [equation],
        },
        *factor_steps,
        {
            "title": "Solve for x",
            "explanation": "Set each factor equal to zero.",
            "math": [],
            "cases": [
                {"math": [line, f"x = {_fmt(root)}"]}
                for line, root in zip(_factor_zero_lines(roots), roots, strict=False)
            ],
        },
        {
            "title": "Verify",
            "explanation": "Substitute each root back into the original equation.",
            "math": [],
            "cases": [{"math": [_quadratic_check_tex(a, b, c, r)]} for r in roots],
        },
    ]
    return _plan(
        {
            "problem": problem,
            "answer": ", ".join(f"x = {_fmt(r)}" for r in roots),
            "steps": steps,
            "visuals": [
                {
                    "tool": "plot_2d",
                    "equation": _quadratic_equation_plain(a, b, c),
                    "coefficients": {"a": a, "b": b, "c": c},
                    "roots": roots,
                },
                {"tool": "equation_board"},
                {"tool": "show_answer", "tex": root_tex, "caption": "Solutions"},
            ],
        }
    )


def plan_linear(
    problem: str, *, left: str, right: str, variable: str = "x"
) -> dict[str, Any]:
    var = sp.symbols(variable)
    lhs, rhs = sp.sympify(left), sp.sympify(right)
    sol = sp.solve(sp.Eq(lhs, rhs), var)
    if len(sol) != 1:
        raise ValueError(f"expected one solution, got {sol}")
    value = float(sp.N(sol[0]))
    equation = f"{sp.latex(lhs)} = {sp.latex(rhs)}"
    return _plan(
        {
            "problem": problem,
            "answer": f"{variable} = {_fmt(value)}",
            "steps": [
                {
                    "title": "Write the equation",
                    "explanation": f"Solve for ${variable}$.",
                    "math": [equation],
                },
                {
                    "title": "Isolate the variable",
                    "explanation": "Use inverse operations.",
                    "math": [equation, f"{variable} = {_fmt(value)}"],
                },
            ],
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": f"{variable}={_fmt(value)}",
                    "caption": "Solution",
                },
            ],
        }
    )


def plan_linear_system_2d(
    problem: str,
    *,
    a1: float,
    b1: float,
    c1: float,
    a2: float,
    b2: float,
    c2: float,
) -> dict[str, Any]:
    """Solve ``a1 x + b1 y = c1`` and ``a2 x + b2 y = c2`` (unique solution)."""
    x, y = sp.symbols("x y")
    eqs = [
        sp.Eq(a1 * x + b1 * y, c1),
        sp.Eq(a2 * x + b2 * y, c2),
    ]
    sol = sp.solve(eqs, [x, y], dict=True)
    if len(sol) != 1:
        raise ValueError("expected a unique solution for the 2x2 system")
    sx = float(sp.N(sol[0][x]))
    sy = float(sp.N(sol[0][y]))
    eq1 = _line_eq_tex(a1, b1, c1)
    eq2 = _line_eq_tex(a2, b2, c2)
    ans = f"x = {_fmt(sx)},\\; y = {_fmt(sy)}"
    return _plan(
        {
            "problem": problem,
            "answer": ans,
            "steps": [
                {
                    "title": "Write the system",
                    "explanation": "Two linear equations in two unknowns.",
                    "math": [eq1, eq2],
                },
                {
                    "title": "Solve by elimination",
                    "explanation": "Eliminate one variable, then back-substitute.",
                    "math": [ans],
                },
                {
                    "title": "Check",
                    "explanation": "Substitute the solution into both equations.",
                    "math": [
                        rf"{_fmt(a1)}({_fmt(sx)}) + ({_fmt(b1)})({_fmt(sy)}) = {_fmt(c1)}",
                        rf"{_fmt(a2)}({_fmt(sx)}) + ({_fmt(b2)})({_fmt(sy)}) = {_fmt(c2)}",
                    ],
                },
            ],
            "visuals": [
                {
                    "tool": "plot_lines_2d",
                    "equations": [
                        {"a": a1, "b": b1, "c": c1},
                        {"a": a2, "b": b2, "c": c2},
                    ],
                    "solution": {"x": sx, "y": sy},
                },
                {"tool": "equation_board"},
                {"tool": "show_answer", "tex": ans, "caption": "Solution"},
            ],
        }
    )


def plan_linear_system_3d(
    problem: str,
    *,
    a1: float,
    b1: float,
    c1: float,
    d1: float,
    a2: float,
    b2: float,
    c2: float,
    d2: float,
    a3: float,
    b3: float,
    c3: float,
    d3: float,
) -> dict[str, Any]:
    """Solve three planes ``a x + b y + c z = d`` with a unique solution."""
    x, y, z = sp.symbols("x y z")
    eqs = [
        sp.Eq(a1 * x + b1 * y + c1 * z, d1),
        sp.Eq(a2 * x + b2 * y + c2 * z, d2),
        sp.Eq(a3 * x + b3 * y + c3 * z, d3),
    ]
    sol = sp.solve(eqs, [x, y, z], dict=True)
    if len(sol) != 1:
        raise ValueError("expected a unique solution for the 3x3 system")
    sx = float(sp.N(sol[0][x]))
    sy = float(sp.N(sol[0][y]))
    sz = float(sp.N(sol[0][z]))
    p1 = _plane_eq_tex(a1, b1, c1, d1)
    p2 = _plane_eq_tex(a2, b2, c2, d2)
    p3 = _plane_eq_tex(a3, b3, c3, d3)
    ans = f"x = {_fmt(sx)},\\; y = {_fmt(sy)},\\; z = {_fmt(sz)}"
    return _plan(
        {
            "problem": problem,
            "answer": ans,
            "steps": [
                {
                    "title": "Write the system",
                    "explanation": "Three linear equations in three unknowns.",
                    "math": [p1, p2, p3],
                },
                {
                    "title": "Solve the linear system",
                    "explanation": "Use elimination (or matrices) to find the unique point.",
                    "math": [ans],
                },
                {
                    "title": "Check one equation",
                    "explanation": "Verify the solution in the first plane.",
                    "math": [
                        rf"{_fmt(a1)}({_fmt(sx)}) + ({_fmt(b1)})({_fmt(sy)}) + ({_fmt(c1)})({_fmt(sz)}) = {_fmt(d1)}"
                    ],
                },
            ],
            "visuals": [
                {
                    "tool": "plot_planes_3d",
                    "equations": [
                        {"a": a1, "b": b1, "c": c1, "d": d1},
                        {"a": a2, "b": b2, "c": c2, "d": d2},
                        {"a": a3, "b": b3, "c": c3, "d": d3},
                    ],
                    "solution": {"x": sx, "y": sy, "z": sz},
                },
                {"tool": "equation_board"},
                {"tool": "show_answer", "tex": ans, "caption": "Solution"},
            ],
        }
    )


def plan_percent_off(
    problem: str, *, original_price: float, percent_off: float
) -> dict[str, Any]:
    discount = original_price * percent_off / 100
    sale = original_price - discount
    pct = _fmt(percent_off)
    orig = _fmt(original_price)
    disc = _fmt(discount)
    sale_s = _fmt(sale)
    return _plan(
        {
            "problem": problem,
            "answer": f"${sale_s}",
            "steps": [
                {
                    "title": "Find the discount amount",
                    "explanation": f"The discount is {pct}% of the original price.",
                    "math": [
                        rf"\text{{discount}} = {pct}\% \times {orig} = {disc}",
                    ],
                },
                {
                    "title": "Subtract from the original price",
                    "explanation": "Sale price equals original minus discount.",
                    "math": [
                        rf"\text{{sale}} = {orig} - {disc} = {sale_s}",
                    ],
                },
            ],
            "visuals": [
                {"tool": "equation_board"},
                {
                    "tool": "show_answer",
                    "tex": rf"\${sale_s}",
                    "caption": "Sale price",
                },
            ],
        }
    )


