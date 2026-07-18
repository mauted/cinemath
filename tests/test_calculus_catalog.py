"""Unit tests for Calc 2/3 catalog planners."""

from __future__ import annotations

import pytest

from cinemath.calculus_catalog import (
    plan_definite_integral,
    plan_integration_by_parts,
    plan_partial_derivative,
    plan_partial_fractions,
    plan_trig_substitution,
    plan_triple_integral,
    plan_u_substitution,
)
from cinemath.catalog import run_catalog
from cinemath.render_engine.validate import validate_animation
from cinemath.templates import compile_plan


def test_plan_integration_by_parts_definite() -> None:
    plan = plan_integration_by_parts(
        "Evaluate $\\int_0^1 x e^x\\,dx$.",
        expression="x*exp(x)",
        variable="x",
        lower=0,
        upper=1,
    )
    assert plan["answer"] == "1"
    titles = [s["title"] for s in plan["steps"]]
    assert "Set up the integral" in titles
    assert any("choose" in t.lower() for t in titles)
    assert any("bounds" in t.lower() for t in titles)
    assert len(plan["steps"]) >= 5
    animation = validate_animation(compile_plan(plan))
    assert any(s["id"].startswith("board_") for s in animation["scenes"])


def test_plan_integration_by_parts_indefinite() -> None:
    plan = plan_integration_by_parts(
        r"Find $\int x e^x\,dx$.",
        expression="x*exp(x)",
        variable="x",
    )
    assert "+ C" in plan["answer"]
    assert "e^{x}" in plan["answer"]


def test_plan_integration_by_parts_manual_u_dv() -> None:
    plan = plan_integration_by_parts(
        "Integrate.",
        expression="x*exp(x)",
        variable="x",
        u="x",
        dv="exp(x)",
    )
    assert "+ C" in plan["answer"]


def test_run_catalog_integration_by_parts() -> None:
    plan = run_catalog(
        "plan_integration_by_parts",
        {
            "problem_statement": "Evaluate the integral.",
            "expression": "x*exp(x)",
            "variable": "x",
            "lower": 0,
            "upper": 1,
        },
    )
    assert plan is not None
    assert plan["answer"] == "1"


def test_plan_definite_integral_sin_steps() -> None:
    plan = plan_definite_integral(
        r"Evaluate $\int_0^{\pi/2} \sin(x)\,dx$.",
        expression="sin(x)",
        variable="x",
        lower=0,
        upper="pi/2",
    )
    assert plan["answer"] == "1"
    assert len(plan["steps"]) >= 3
    titles = [s["title"] for s in plan["steps"]]
    assert "Set up the integral" in titles
    assert any("bounds" in t.lower() for t in titles)
    assert plan["visuals"][0]["tool"] == "plot_integral_1d"
    bounds = next(s for s in plan["steps"] if "bounds" in s["title"].lower())
    assert len(bounds["math"]) >= 3
    assert r"\cos{\left(\frac{\pi}{2}" in bounds["math"][1]
    assert bounds["math"][-1] == "= 1"


def test_plan_definite_integral_rejects_u_sub() -> None:
    with pytest.raises(ValueError, match="plan_u_substitution"):
        plan_definite_integral(
            r"Evaluate $\int 2x e^{x^2}\,dx$.",
            expression="2*x*exp(x**2)",
            variable="x",
        )


def test_plan_partial_fractions_indefinite_has_no_plot() -> None:
    plan = plan_partial_fractions(
        r"Evaluate $\int \frac{4}{x^2+5x-14}\,dx$.",
        expression="4/(x**2+5*x-14)",
        variable="x",
    )
    assert all(v["tool"] != "plot_integral_1d" for v in plan["visuals"])


def test_compile_definite_integral_plot_scene() -> None:
    plan = plan_definite_integral(
        r"Evaluate $\int_0^{\pi/2} \sin(x)\,dx$.",
        expression="sin(x)",
        variable="x",
        lower=0,
        upper="pi/2",
    )
    animation = validate_animation(compile_plan(plan))
    assert any(s["id"].startswith("plot_integral_1d_") for s in animation["scenes"])


def test_plan_partial_fractions_indefinite() -> None:
    plan = plan_partial_fractions(
        r"Evaluate $\int \frac{4}{x^2+5x-14}\,dx$.",
        expression="4/(x**2+5*x-14)",
        variable="x",
    )
    assert "+ C" in plan["answer"]
    titles = [s["title"] for s in plan["steps"]]
    assert "Write the decomposition form" in titles
    assert "Equate coefficients" in titles
    assert any(step.get("side_math") for step in plan["steps"])
    assert any("substitution" in t.lower() for t in titles)
    assert len(plan["steps"]) >= 8


def test_plan_partial_fractions_quadratic_factors() -> None:
    plan = plan_partial_fractions(
        r"Evaluate $\int \frac{8 + t + 6t^{2} - 12t^{3}}{(3t^{2} + 4)(t^{2} + 7)} \, dt$.",
        expression="(8+t+6*t**2-12*t**3)/((3*t**2+4)*(t**2+7))",
        variable="t",
    )
    titles = [s["title"] for s in plan["steps"]]
    assert "Clear denominators" in titles
    assert "Equate coefficients" in titles
    assert any("arctan" in t.lower() or "substitution" in t.lower() for t in titles)
    assert len(plan["steps"]) >= 12


def test_plan_partial_fractions_long_division() -> None:
    plan = plan_partial_fractions(
        r"Evaluate $\int \frac{6x^{2} - 3x}{(x - 2)(x + 4)}\,dx$.",
        expression="(6*x**2-3*x)/((x-2)*(x+4))",
        variable="x",
    )
    titles = [s["title"] for s in plan["steps"]]
    assert "Polynomial long division" in titles
    assert any(t.startswith("Polynomial part:") for t in titles)
    assert "+ C" in plan["answer"]


def test_plan_u_substitution_nested_uses_distinct_vars() -> None:
    plan = plan_u_substitution(
        r"Evaluate $\int \sqrt{e^{8x} - 9} \, dx$.",
        expression="sqrt(exp(8*x)-9)",
        variable="x",
    )
    math_lines = [line for step in plan["steps"] for line in step.get("math", [])]
    assert any("u = e^{8 x}" in line for line in math_lines)
    assert any("v = \\sqrt{u - 9}" in line for line in math_lines)
    assert all("d_u" not in line for line in math_lines)
    assert any("\\,du" in line for line in math_lines)
    assert any("\\,dv" in line for line in math_lines)
    subs = [s for s in plan["steps"] if s["title"] == "Substitute back"]
    assert "Replace $v$ with" in subs[0]["explanation"]
    assert "Replace $u$ with" in subs[1]["explanation"]


def test_plan_u_substitution_trig_powers() -> None:
    plan = plan_u_substitution(
        r"Evaluate $\int \sin^3(x)\cos^4(x)\,dx$.",
        expression="sin(x)**3*cos(x)**4",
        variable="x",
    )
    assert "+ C" in plan["answer"]
    assert len(plan["steps"]) >= 4


def test_plan_integration_by_parts_improper() -> None:
    plan = plan_integration_by_parts(
        r"Evaluate $\int_0^\infty (1+2x)e^{-x}\,dx$.",
        expression="(1+2*x)*exp(-x)",
        variable="x",
        lower=0,
        upper="oo",
    )
    assert plan["answer"] == "3"
    titles = [s["title"] for s in plan["steps"]]
    assert any("choose" in t.lower() for t in titles)
    choose = next(s for s in plan["steps"] if "choose" in s["title"].lower())
    assert r"u = 2 x + 1" in choose["math"][0] or r"u = 2x + 1" in choose["math"][0].replace(" ", "")
    assert "e^{- x}" in choose["math"][1] or "e^{-x}" in choose["math"][1].replace(" ", "")


def test_plan_improper_integral() -> None:
    plan = plan_definite_integral(
        r"Evaluate $\int_1^\infty \frac{dx}{x^2}$.",
        expression="1/x**2",
        variable="x",
        lower=1,
        upper="oo",
    )
    assert plan["answer"] == "1"


def test_plan_mit_sine_integral() -> None:
    plan = plan_definite_integral(
        r"Evaluate $\int_0^{\pi/2} \sin(x)\,dx$.",
        expression="sin(x)",
        variable="x",
        lower=0,
        upper="pi/2",
    )
    assert plan["answer"] == "1"


def test_plan_partial_derivative() -> None:
    plan = plan_partial_derivative(
        r"Find $\partial f/\partial x$ for $f(x,y)=x^2 y + \sin(xy)$.",
        expression="x**2*y + sin(x*y)",
        variable="x",
    )
    assert "2 x y" in plan["answer"] or "2xy" in plan["answer"].replace(" ", "")


def test_plan_triple_integral_box() -> None:
    plan = plan_triple_integral(
        r"Evaluate $\iiint_E xyz\,dV$ on $[0,1]\times[0,2]\times[0,1]$.",
        integrand="x*y*z",
        x_min=0,
        x_max=1,
        y_min=0,
        y_max=2,
        z_min=0,
        z_max=1,
    )
    assert plan["answer"] == "0.5"


def test_plan_trig_substitution_sec() -> None:
    plan = plan_trig_substitution(
        r"Evaluate $\int \sqrt{49t^{2} - 5} \, dt$.",
        expression="sqrt(49*t**2-5)",
        variable="t",
    )
    titles = [s["title"] for s in plan["steps"]]
    assert "Use trigonometric substitution" in titles
    assert "Substitute back" in titles
    assert "sec" in plan["steps"][1]["math"][0]
    assert "+ C" in plan["answer"]
    assert r"\sqrt{49 t^{2} - 5}" in plan["answer"]


def test_plan_trig_substitution_tan() -> None:
    plan = plan_trig_substitution(
        r"Evaluate $\int \sqrt{25t^{2} + 13} \, dt$.",
        expression="sqrt(25*t**2+13)",
        variable="t",
    )
    titles = [s["title"] for s in plan["steps"]]
    assert "Use trigonometric substitution" in titles
    assert "tan" in plan["steps"][titles.index("Use trigonometric substitution")]["math"][0]


def test_run_catalog_definite_integral() -> None:
    plan = run_catalog(
        "plan_definite_integral",
        {
            "problem_statement": "Integrate.",
            "expression": "x**2",
            "variable": "x",
            "lower": 0,
            "upper": 2,
        },
    )
    assert plan is not None
    assert "frac{8}{3}" in plan["answer"] or plan["answer"] == "8/3"


def test_run_catalog_trig_substitution() -> None:
    plan = run_catalog(
        "plan_trig_substitution",
        {
            "problem_statement": "Integrate.",
            "expression": "sqrt(49*t**2-5)",
            "variable": "t",
        },
    )
    assert plan is not None
    assert "Use trigonometric substitution" in [s["title"] for s in plan["steps"]]


def test_run_catalog_unwalkable_integral_falls_back_to_freeform() -> None:
    plan = run_catalog(
        "plan_u_substitution",
        {
            "problem_statement": r"Evaluate $\int \sqrt{\tan x}\,dx$.",
            "expression": "sqrt(tan(x))",
            "variable": "x",
        },
    )
    assert plan is None
