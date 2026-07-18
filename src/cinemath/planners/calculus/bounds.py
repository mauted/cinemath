"""Shared bound parsing for calculus planners."""

from __future__ import annotations

import sympy as sp


def _bound(raw: float | int | str) -> sp.Expr:
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in {"oo", "inf", "+inf", "infinity", "+infinity"}:
            return sp.oo
        if s in {"-oo", "-inf", "-infinity"}:
            return -sp.oo
        return sp.sympify(raw)
    return sp.sympify(raw)


def bound_is_finite(b: sp.Expr | None) -> bool:
    return b is not None and b not in (sp.oo, -sp.oo)


def bound_as_float(b: sp.Expr) -> float:
    if b in (sp.oo, -sp.oo):
        raise ValueError("cannot convert infinite bound to float")
    return float(sp.N(b))


def _bound_tex(b: sp.Expr, variable: str) -> str:
    if b is sp.oo:
        return r"\infty"
    if b is -sp.oo:
        return r"-\infty"
    if isinstance(b, sp.Integer):
        return str(int(b))
    return sp.latex(b)
