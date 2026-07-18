"""Unit tests for Manim render settings."""

from __future__ import annotations

import pytest

from cinemath.render_engine.render import QUALITY_ARGS, _quality_args


def test_default_quality_is_720p60() -> None:
    assert _quality_args("m") == ["-qm", "--frame_rate", "60"]


def test_unknown_quality_raises() -> None:
    with pytest.raises(ValueError, match="Unknown quality"):
        _quality_args("x")


def test_all_quality_presets_defined() -> None:
    assert set(QUALITY_ARGS) == {"l", "m", "h"}
