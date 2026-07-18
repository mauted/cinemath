"""Optional local verification of teacher-plan answers."""

from __future__ import annotations

import json
from typing import Any

import sympy as sp

from cinemath.arithmetic import (
    analyze_long_addition,
    analyze_long_division,
    analyze_long_multiplication,
    analyze_long_subtraction,
)


def verify_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a verification report without mutating the plan."""
    tools = [str(v.get("tool")) for v in plan.get("visuals") or [] if isinstance(v, dict)]
    report: dict[str, Any] = {"checked": False, "ok": True, "notes": [], "tools": tools}

    if _first_visual(plan, "plot_2d") is not None:
        return _verify_quadratic(plan, report)
    if _first_visual(plan, "plot_lines_2d") is not None:
        return _verify_linear_system_2d(plan, report)
    if _first_visual(plan, "plot_planes_3d") is not None:
        return _verify_linear_system_3d(plan, report)
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


def verify_feedback_message(report: dict[str, Any]) -> str:
    """User message asking the freeform teacher to fix a failed verification."""
    payload = {k: v for k, v in report.items() if k != "tools"}
    return (
        "Your lesson plan failed local verification. "
        "Fix the mathematics in your JSON plan and return ONLY corrected JSON.\n\n"
        f"Verification report:\n{json.dumps(payload, indent=2)}"
    )


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
        report["notes"].append("Root mismatch.")
    else:
        report["notes"].append("Roots match SymPy.")
    return report


def _verify_linear_system_2d(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "plot_lines_2d")
    assert visual is not None
    eqs = visual["equations"]
    x, y = sp.symbols("x y")
    system = [
        sp.Eq(eq["a"] * x + eq["b"] * y, eq["c"])
        for eq in eqs
    ]
    sol = sp.solve(system, [x, y], dict=True)
    if len(sol) != 1:
        report["ok"] = False
        report["notes"].append("System does not have a unique solution.")
        return report
    computed = {"x": float(sp.N(sol[0][x])), "y": float(sp.N(sol[0][y]))}
    claimed = {"x": float(visual["solution"]["x"]), "y": float(visual["solution"]["y"])}
    report["computed_solution"] = computed
    report["claimed_solution"] = claimed
    if any(abs(computed[k] - claimed[k]) > 1e-6 for k in ("x", "y")):
        report["ok"] = False
        report["notes"].append("2x2 system solution mismatch.")
    else:
        report["notes"].append("2x2 system matches SymPy.")
    return report


def _verify_linear_system_3d(plan: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    report["checked"] = True
    visual = _first_visual(plan, "plot_planes_3d")
    assert visual is not None
    eqs = visual["equations"]
    x, y, z = sp.symbols("x y z")
    system = [
        sp.Eq(eq["a"] * x + eq["b"] * y + eq["c"] * z, eq["d"])
        for eq in eqs
    ]
    sol = sp.solve(system, [x, y, z], dict=True)
    if len(sol) != 1:
        report["ok"] = False
        report["notes"].append("System does not have a unique solution.")
        return report
    computed = {
        "x": float(sp.N(sol[0][x])),
        "y": float(sp.N(sol[0][y])),
        "z": float(sp.N(sol[0][z])),
    }
    claimed = {
        "x": float(visual["solution"]["x"]),
        "y": float(visual["solution"]["y"]),
        "z": float(visual["solution"]["z"]),
    }
    report["computed_solution"] = computed
    report["claimed_solution"] = claimed
    if any(abs(computed[k] - claimed[k]) > 1e-6 for k in ("x", "y", "z")):
        report["ok"] = False
        report["notes"].append("3x3 system solution mismatch.")
    else:
        report["notes"].append("3x3 system matches SymPy.")
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
        report["notes"].append("Integral value mismatch.")
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
        report["notes"].append("Product mismatch.")
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
        report["notes"].append("Quotient mismatch.")
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
        report["notes"].append("Sum mismatch.")
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
        report["notes"].append("Difference mismatch.")
    else:
        report["notes"].append("Difference matches local arithmetic.")
    return report


def _first_visual(plan: dict[str, Any], tool: str) -> dict[str, Any] | None:
    for visual in plan.get("visuals") or []:
        if isinstance(visual, dict) and visual.get("tool") == tool:
            return visual
    return None
