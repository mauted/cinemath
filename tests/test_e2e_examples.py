"""Live end-to-end pipeline tests over examples/*."""

from __future__ import annotations

import json
import os

import pytest

from cinemath.pipeline import run_pipeline
from cinemath.render_engine.validate import validate_animation
from conftest import EXAMPLES_DIR, requires_api

EXAMPLE_CASES: list[tuple[str, str | None]] = [
    ("01_watermelons.txt", None),
    ("02_linear_equation.txt", "plan_linear"),
    ("03_percent_off.txt", "plan_percent_off"),
    ("04_quadratic.txt", "plan_quadratic"),
    ("05_pythagoras.txt", None),
    ("06_derivative.txt", "plan_derivative"),
    ("07_double_integral.md", "plan_double_integral"),
    ("08_euler_totient.md", None),
    ("09_improper_integral.md", None),
    ("10_scalar_decay.md", None),
    ("11_long_multiplication.txt", "plan_long_multiply"),
    ("12_long_division.txt", "plan_long_divide"),
    ("13_decimal_multiplication.txt", "plan_long_multiply"),
    ("14_long_addition.txt", "plan_long_add"),
    ("15_long_subtraction.txt", "plan_long_subtract"),
    ("16_linear_system_2d.txt", "plan_linear_system_2d"),
    ("17_linear_system_3d.txt", "plan_linear_system_3d"),
]


def _skip_render_e2e() -> bool:
    return os.environ.get("CINEMATH_E2E_SKIP_RENDER", "").strip().lower() in {"1", "true", "yes", "on"}


def _e2e_quality() -> str:
    return os.environ.get("CINEMATH_E2E_QUALITY", "l").strip().lower() or "l"


@pytest.mark.e2e
@requires_api
@pytest.mark.parametrize("filename,expected_planner", EXAMPLE_CASES, ids=[c[0] for c in EXAMPLE_CASES])
def test_example_pipeline(filename: str, expected_planner: str | None) -> None:
    path = EXAMPLES_DIR / filename
    assert path.is_file(), f"missing example: {path}"

    result = run_pipeline(
        path,
        quality=_e2e_quality(),
        skip_render=_skip_render_e2e(),
    )

    assert result.plan_path.is_file()
    assert result.animation_path.is_file()
    assert result.run_dir.is_dir()

    plan = json.loads(result.plan_path.read_text(encoding="utf-8"))
    assert plan.get("problem")
    assert plan.get("answer")
    assert isinstance(plan.get("steps"), list) and plan["steps"]
    assert isinstance(plan.get("visuals"), list) and plan["visuals"]

    animation = validate_animation(json.loads(result.animation_path.read_text(encoding="utf-8")))
    assert animation.get("scenes")

    if expected_planner is not None:
        assert result.teacher.source == "catalog"
        assert result.teacher.planner == expected_planner
        assert result.verify_path is None
    else:
        assert result.teacher.source == "freeform"
        if result.teacher.verify is not None:
            assert result.teacher.verify.get("ok") is True or not result.teacher.verify.get("checked")

    if _skip_render_e2e():
        assert not result.video_path.exists()
    else:
        assert result.video_path.is_file()
        assert result.video_path.stat().st_size > 0
