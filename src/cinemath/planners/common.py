"""Shared planner helpers."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.plan.schema import PLAN_VERSION
from cinemath.plan.validate import validate_plan

def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6g}"


def _term_tex(coef: float, symbol: str, *, leading: bool = False) -> str:
    if abs(coef) < 1e-12:
        return ""
    mag = _fmt(abs(coef))
    body = symbol if abs(abs(coef) - 1) < 1e-9 else f"{mag}{symbol}"
    if leading:
        return f"-{body}" if coef < 0 else body
    return f" - {body}" if coef < 0 else f" + {body}"


def _line_eq_tex(a: float, b: float, c: float) -> str:
    left = _term_tex(a, "x", leading=True) + _term_tex(b, "y")
    return f"{left or '0'} = {_fmt(c)}"


def _plane_eq_tex(a: float, b: float, c: float, d: float) -> str:
    left = (
        _term_tex(a, "x", leading=True)
        + _term_tex(b, "y")
        + _term_tex(c, "z")
    )
    return f"{left or '0'} = {_fmt(d)}"


def _sym_coef(value: float) -> sp.Expr:
    if abs(value - round(value)) < 1e-9:
        return sp.Integer(int(round(value)))
    return sp.Rational(sp.nsimplify(value))


def _quadratic_equation_tex(a: float, b: float, c: float) -> str:
    """School-style quadratic, e.g. x^2 - 5x + 6 = 0."""
    x = sp.symbols("x")
    poly = _sym_coef(a) * x**2 + _sym_coef(b) * x + _sym_coef(c)
    return sp.latex(poly) + " = 0"


def _quadratic_equation_plain(a: float, b: float, c: float) -> str:
    """Compact equation for plot_2d, e.g. x^2 - 5x + 6 = 0."""
    return _quadratic_equation_tex(a, b, c).replace("{", "").replace("}", "").replace(" ", "")


def _quadratic_factored_tex(a: float, b: float, c: float) -> str:
    x = sp.symbols("x")
    poly = _sym_coef(a) * x**2 + _sym_coef(b) * x + _sym_coef(c)
    roots = sorted(float(sp.N(r)) for r in sp.solve(poly, x) if r.is_real)
    if not roots:
        return sp.latex(sp.factor(poly, x))
    factors = []
    for root in roots:
        if abs(root - round(root)) < 1e-9:
            r = int(round(root))
            if r >= 0:
                factors.append(f"(x - {r})")
            else:
                factors.append(f"(x + {-r})")
        else:
            factors.append(f"\\left(x - {_fmt(root)}\\right)")
    body = "".join(factors)
    a_int = _sym_coef(a)
    if a_int == 1:
        return body
    if a_int == -1:
        return f"-{body}"
    return f"{sp.latex(a_int)}{body}"


def _quadratic_check_tex(a: float, b: float, c: float, root: float) -> str:
    r = _fmt(root)
    b_sign = "+" if b >= 0 else "-"
    c_sign = "+" if c >= 0 else "-"
    return rf"{r}^{{2}} {b_sign} {_fmt(abs(b))}({r}) {c_sign} {_fmt(abs(c))} = 0"


def _int_coef(value: float) -> int | None:
    if abs(value - round(value)) < 1e-9:
        return int(round(value))
    return None


def _find_factor_pair(sum_target: int, product_target: int) -> tuple[int, int] | None:
    """Integers p, q with p+q=sum_target and pq=product_target."""
    if product_target == 0:
        if sum_target == 0:
            return (0, 0)
        return None
    seen: set[tuple[int, int]] = set()
    limit = max(abs(product_target) * 2, 32)
    for p in range(-limit, limit + 1):
        if p == 0:
            continue
        if product_target % p != 0:
            continue
        q = product_target // p
        key = (min(p, q), max(p, q))
        if key in seen:
            continue
        seen.add(key)
        if p + q == sum_target:
            ordered = (p, q) if p > q else (q, p)
            return ordered
    return None


def _x_shift_tex(p: int) -> str:
    """Binomial x+p in factored form, e.g. p=-2 -> x-2."""
    if p >= 0:
        return f"x + {p}"
    return f"x - {abs(p)}"


def _split_quadratic_tex(a: int, p: int, q: int, c: int) -> str:
    """Expanded form with middle term split, e.g. x^2 - 2x - 3x + 6 = 0."""
    if a == 1:
        lead = "x^{2}"
    elif a == -1:
        lead = "-x^{2}"
    else:
        lead = f"{a}x^{{2}}"
    p_term = f"- {abs(p)}x" if p < 0 else (f"+ {p}x" if p != 1 else "+ x")
    q_term = f"- {abs(q)}x" if q < 0 else (f"+ {q}x" if q != 1 else "+ x")
    c_term = f"+ {c}" if c >= 0 else f"- {abs(c)}"
    return f"{lead} {p_term} {q_term} {c_term} = 0"


def _group_quadratic_tex(a: int, p: int, q: int, c: int) -> str:
    """Factor by grouping, e.g. x(x-2) - 3(x-2) = 0."""
    if a == 1 or a == -1:
        inner = _x_shift_tex(p)
        if a == 1:
            first = f"x({inner})"
        else:
            first = f"-x({inner})"
        if q == 1:
            second = f"+ ({inner})"
        elif q == -1:
            second = f"- ({inner})"
        elif q > 0:
            second = f"+ {q}({inner})"
        else:
            second = f"- {abs(q)}({inner})"
        return f"{first} {second} = 0"
    x = sp.symbols("x")
    part1 = sp.factor(_sym_coef(a) * x**2 + _sym_coef(p) * x)
    part2 = sp.factor(_sym_coef(q) * x + _sym_coef(c))
    return sp.latex(part1) + " + " + sp.latex(part2) + " = 0"


def _pair_summary_tex(p: int, q: int, product: int, total: int) -> str:
    return rf"({p}) \cdot ({q}) = {product},\quad ({p}) + ({q}) = {total}"


def _quadratic_factor_steps(a: float, b: float, c: float) -> list[dict[str, Any]]:
    """Deterministic factor-by-grouping steps when an integer pair exists."""
    ai, bi, ci = _int_coef(a), _int_coef(b), _int_coef(c)
    if ai is None or bi is None or ci is None or ai == 0:
        return []

    if ai == 1 or ai == -1:
        pair = _find_factor_pair(bi, ci)
        if pair is None:
            return []
        p, q = pair
        product_label = ci
        return [
            {
                "title": "Find two numbers",
                "explanation": (
                    f"Find two numbers that multiply to ${product_label}$ "
                    f"and add to ${_fmt(bi)}$."
                ),
                "math": [_pair_summary_tex(p, q, product_label, bi)],
            },
            {
                "title": "Split the middle term",
                "explanation": (
                    f"Rewrite the ${_fmt(bi)}x$ term using ${p}$ and ${q}$."
                ),
                "math": [_split_quadratic_tex(ai, p, q, ci)],
            },
            {
                "title": "Factor by grouping",
                "explanation": "Group the four terms and pull out the common binomial.",
                "math": [
                    _group_quadratic_tex(ai, p, q, ci),
                    f"{_quadratic_factored_tex(a, b, c)} = 0",
                ],
            },
        ]

    # ac method for a != 1
    pair = _find_factor_pair(bi, ai * ci)
    if pair is None:
        return []
    p, q = pair
    return [
        {
            "title": "Find two numbers",
            "explanation": (
                f"Multiply $a \\cdot c = {_fmt(ai)} \\cdot {_fmt(ci)} = {_fmt(ai * ci)}$. "
                f"Find two numbers that multiply to ${_fmt(ai * ci)}$ "
                f"and add to ${_fmt(bi)}$."
            ),
            "math": [_pair_summary_tex(p, q, ai * ci, bi)],
        },
        {
            "title": "Split the middle term",
            "explanation": f"Rewrite the ${_fmt(bi)}x$ term using ${p}$ and ${q}$.",
            "math": [_split_quadratic_tex(ai, p, q, ci)],
        },
        {
            "title": "Factor by grouping",
            "explanation": "Group and pull out the common binomial.",
            "math": [
                _group_quadratic_tex(ai, p, q, ci),
                f"{_quadratic_factored_tex(a, b, c)} = 0",
            ],
        },
    ]


def _factor_zero_lines(roots: list[float]) -> list[str]:
    lines: list[str] = []
    for root in roots:
        r = int(round(root)) if abs(root - round(root)) < 1e-9 else None
        if r is not None:
            lines.append(f"{_x_shift_tex(-r)} = 0")
        else:
            lines.append(f"x - {_fmt(root)} = 0")
    return lines


def _plan(raw: dict[str, Any]) -> dict[str, Any]:
    raw["version"] = PLAN_VERSION
    return validate_plan(raw)


class CatalogFreeform(Exception):
    """Catalog planners cannot teach this problem; use the freeform LLM teacher."""


def _problem(tool_input: dict[str, Any], *, name: str) -> str:
    problem = str(tool_input.get("problem_statement") or "").strip()
    if not problem:
        raise ValueError(f"{name} requires problem_statement")
    return problem


