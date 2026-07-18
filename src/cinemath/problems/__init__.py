"""Problem bank paths and layout for cinemath."""

from __future__ import annotations

from pathlib import Path

# cinemath/src/cinemath/problems/__init__.py -> repo root cinemath/
REPO_ROOT = Path(__file__).resolve().parents[3]
PROBLEMS_DIR = REPO_ROOT / "problems"
CURATED_DIR = PROBLEMS_DIR / "curated"

SOURCE_DIRS = {
    "lamar": PROBLEMS_DIR / "lamar",
    "mit": PROBLEMS_DIR / "mit",
    "arizona": PROBLEMS_DIR / "arizona",
    "openstax": PROBLEMS_DIR / "openstax",
}
