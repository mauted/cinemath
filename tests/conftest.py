"""Shared pytest fixtures."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = PROJECT_ROOT / "problems"
CURATED_DIR = PROBLEMS_DIR / "curated"
EXAMPLES_DIR = CURATED_DIR  # ../examples symlinks here
E2E_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "e2e"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: live LLM pipeline tests (requires ANTHROPIC_API_KEY)")


def _api_key_set() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


requires_api = pytest.mark.skipif(not _api_key_set(), reason="ANTHROPIC_API_KEY not set")


@pytest.fixture(autouse=True)
def _configure_output_dir(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if request.node.get_closest_marker("e2e"):
        monkeypatch.setenv("CINEMATH_OUTPUT_DIR", str(E2E_OUTPUT_DIR))
        return
    monkeypatch.setenv("CINEMATH_OUTPUT_DIR", str(tmp_path / "outputs"))
