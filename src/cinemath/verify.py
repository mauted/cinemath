"""Optional local verification of teacher-plan answers."""

from __future__ import annotations

from typing import Any

import sympy as sp

from cinemath.arithmetic import (
    analyze_long_addition,
    analyze_long_division,
    analyze_long_multiplication,
    analyze_long_subtraction,
)


def verify_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a verification report; may correct answer for known visual tools."""
    tools = [str(v.get("tool")) for v in plan.get("visuals") or [] if isinstance(v, dict)]
    report: dict[str, Any] = {"checked": False, "ok": True, "notes": [], "tools": tools}

    if _first_visual(plan, "plot_2d") is not None:
        return _verify_quadratic(plan, report)
    if _first_visual(plan, "show_region_rectangle") is not None:
        return _verify_double_integral(plan, report)
    if _first_visual(plan, "paper_long_multiply") is not None:
        return _verify_long_multiplication(plan, report)
    if _first_visual(plan, "paper_long_divide") is not None:
        return _verify_long_division(plan, report)
    if _first_visual(plan, "paper_long_add") is not None:
        return _verify_long_addition(plan, report)
    if _first_visual(plan, "paper_long_subtract") is not None:
        return _verify_long_subtraction(plan, report)

    report["notes"].append("No symbolic checker for these visual tools; skipped.")
    return report


def _verify_quadratic(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "plot_2d")
    assert visual is not None
    coeff = visual["coefficients"]
    a, b, c = coeff["a"], coeff["b"], coeff["c"]
    x = sp.symbols("x")
    roots = sp.solve(a * x**2 + b * x + c, x)
    numeric = sorted(float(sp.N(r)) for r in roots if r.is_real)
    claimed = sorted(float(r) for r in visual["roots"])
    report["computed_roots"] = numeric
    report["claimed_roots"] = claimed
    if len(numeric) != len(claimed) or any(abs(left - right) > 1e-6 for left, right in zip(numeric, claimed)):
        report["ok"] = False
        report["notes"].append("Root mismatch; correcting plot_2d roots and answer from SymPy.")
        visual["roots"] = numeric
        plan["answer"] = " or ".join(f"x = {_fmt(r)}" for r in numeric)
        _update_show_answer(plan, _quadratic_answer_tex(numeric), caption="Solutions")
    else:
        report["notes"].append("Roots match SymPy.")
    return report


def _verify_double_integral(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "show_region_rectangle")
    assert visual is not None
    x, y = sp.symbols("x y")
    try:
        integrand = sp.sympify(visual["integrand"])
    except Exception as exc:
        report["ok"] = False
        report["notes"].append(f"Could not parse integrand: {exc}")
        return report

    if visual["order"] == "dy_dx":
        value = sp.integrate(
            sp.integrate(integrand, (y, visual["y_min"], visual["y_max"])),
            (x, visual["x_min"], visual["x_max"]),
        )
    else:
        value = sp.integrate(
            sp.integrate(integrand, (x, visual["x_min"], visual["x_max"])),
            (y, visual["y_min"], visual["y_max"]),
        )
    computed = float(sp.N(value))
    claimed = float(visual["value"])
    report["computed_value"] = computed
    report["claimed_value"] = claimed
    if abs(computed - claimed) > 1e-6:
        report["ok"] = False
        report["notes"].append("Integral value mismatch; correcting rectangle value and answer.")
        visual["value"] = computed
        plan["answer"] = _fmt(computed)
        _update_show_answer(plan, _double_integral_answer_tex(visual, computed), caption="Final value")
    else:
        report["notes"].append("Integral value matches SymPy.")
    return report


def _verify_long_multiplication(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "paper_long_multiply")
    assert visual is not None
    computed = analyze_long_multiplication(visual["multiplicand"], visual["multiplier"])["product"]
    claimed = visual["product"]
    report["computed_product"] = computed
    report["claimed_product"] = claimed
    if computed != claimed or plan["answer"] != computed:
        report["ok"] = False
        report["notes"].append("Product mismatch; correcting from local arithmetic.")
        visual["product"] = computed
        plan["answer"] = computed
    else:
        report["notes"].append("Product matches local arithmetic.")
    return report


def _verify_long_division(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "paper_long_divide")
    assert visual is not None
    analysis = analyze_long_division(visual["dividend"], visual["divisor"])
    computed = analysis["quotient"]
    claimed = visual["quotient"]
    report["computed_quotient"] = computed
    report["claimed_quotient"] = claimed
    if computed != claimed or plan["answer"] != computed:
        report["ok"] = False
        report["notes"].append("Quotient mismatch; correcting from local arithmetic.")
        visual["quotient"] = computed
        plan["answer"] = computed
    else:
        report["notes"].append("Quotient matches local arithmetic.")
    if not analysis["terminated"]:
        report["notes"].append("Decimal expansion did not terminate within the local digit budget.")
    return report


def _verify_long_addition(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "paper_long_add")
    assert visual is not None
    computed = analyze_long_addition(list(visual["addends"]))["sum"]
    claimed = visual["sum"]
    report["computed_sum"] = computed
    report["claimed_sum"] = claimed
    if computed != claimed or plan["answer"] != computed:
        report["ok"] = False
        report["notes"].append("Sum mismatch; correcting from local arithmetic.")
        visual["sum"] = computed
        plan["answer"] = computed
    else:
        report["notes"].append("Sum matches local arithmetic.")
    return report


def _verify_long_subtraction(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "paper_long_subtract")
    assert visual is not None
    try:
        computed = analyze_long_subtraction(visual["minuend"], visual["subtrahend"])["difference"]
    except ValueError as exc:
        report["ok"] = False
        report["notes"].append(str(exc))
        return report
    claimed = visual["difference"]
    report["computed_difference"] = computed
    report["claimed_difference"] = claimed
    if computed != claimed or plan["answer"] != computed:
        report["ok"] = False
        report["notes"].append("Difference mismatch; correcting from local arithmetic.")
        visual["difference"] = computed
        plan["answer"] = computed
    else:
        report["notes"].append("Difference matches local arithmetic.")
    return report


def _first_visual(plan: dict[str, Any], tool: str) -> dict[str, Any] | None:
    for visual in plan.get("visuals") or []:
        if isinstance(visual, dict) and visual.get("tool") == tool:
            return visual
    return None


def _update_show_answer(plan: dict[str, Any], tex: str, *, caption: str) -> None:
    visual = _first_visual(plan, "show_answer")
    if visual is None:
        return
    visual["tex"] = tex
    visual["caption"] = caption


def _quadratic_answer_tex(roots: list[float]) -> str:
    return r" \quad\text{or}\quad ".join(f"x={_fmt(root)}" for root in roots)


def _double_integral_answer_tex(visual: dict[str, Any], value: float) -> str:
    body = str(visual["integrand"]).replace("**", "^").replace("*", "").replace(" ", "")
    return rf"\iint_R {body}\,dA = {_fmt(value)}"


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6g}"
