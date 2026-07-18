"""Problem bank paths and layout for cinemath."""

from __future__ import annotations

from pathlib import Path

from cinemath.problems.layout import (
    BY_TYPE_DIRNAME,
    by_type_dir,
    iter_problems_for_planner,
    iter_planner_batches,
    planner_dir,
)

# cinemath/src/cinemath/problems/__init__.py -> repo root cinemath/
REPO_ROOT = Path(__file__).resolve().parents[3]
PROBLEMS_DIR = REPO_ROOT / "problems"
CURATED_DIR = PROBLEMS_DIR / "curated"
BY_TYPE_DIR = by_type_dir(PROBLEMS_DIR)

__all__ = [
    "BY_TYPE_DIR",
    "BY_TYPE_DIRNAME",
    "CURATED_DIR",
    "PROBLEMS_DIR",
    "by_type_dir",
    "iter_planner_batches",
    "iter_problems_for_planner",
    "planner_dir",
]
