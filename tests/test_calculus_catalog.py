"""Unit tests for Calc 2/3 catalog planners."""

from __future__ import annotations

from cinemath.calculus_catalog import (
    plan_definite_integral,
    plan_integration_by_parts,
    plan_partial_derivative,
    plan_triple_integral,
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


def test_plan_definite_integral_by_parts_style() -> None:
    plan = plan_definite_integral(
        "Evaluate $\\int_0^1 x e^x\\,dx$.",
        expression="x*exp(x)",
        variable="x",
        lower=0,
        upper=1,
    )
    assert plan["answer"] == "1"
    animation = validate_animation(compile_plan(plan))
    assert any(s["id"].startswith("board_") for s in animation["scenes"])


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
