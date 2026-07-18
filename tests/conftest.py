"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = PROJECT_ROOT / "problems"
CURATED_DIR = PROBLEMS_DIR / "curated"
EXAMPLES_DIR = CURATED_DIR  # ../examples symlinks here


@pytest.fixture(autouse=True)
def _configure_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CINEMATH_OUTPUT_DIR", str(tmp_path / "outputs"))
