"""Unit tests for instruction placement helpers."""

from __future__ import annotations

from cinemath.render_engine.instructions import (
    _content_profile,
    _overlap_area,
    _score_placement,
    _stage_bounds,
    format_instruction_body,
)


def test_format_instruction_body_mathifies_algebra() -> None:
    body = format_instruction_body("Find two numbers that multiply to 6 and add to -5.")
    assert "multiply" in body
    assert "$" in body or "6" in body


def test_content_profile_prefers_bottom_for_tall_upper_graphics() -> None:
    # Tall content centered high on the frame → bottom caption first.
    boxes = [(-2.0, 2.0, 0.0, 2.8), (-1.0, 3.0, -0.5, 2.5)]
    assert _content_profile(boxes)[0] == "bottom"


def test_content_profile_prefers_above_for_low_equations() -> None:
    boxes = [(-2.0, 2.0, -2.5, -1.0)]
    assert _content_profile(boxes)[0] == "above"


def test_score_penalizes_overlap() -> None:
    bounds = _stage_bounds(False)
    instr = (-5.0, 5.0, 2.5, 3.5)
    clear = _score_placement(instr, [], bounds)
    blocked = _score_placement(instr, [(-1.0, 1.0, 2.4, 3.6)], bounds)
    assert clear > blocked


def test_overlap_area_with_padding() -> None:
    a = (0.0, 2.0, 0.0, 1.0)
    b = (1.5, 3.0, 0.0, 1.0)
    assert _overlap_area(a, b) > 0
