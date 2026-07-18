"""Problem-bank layout: organize batches by catalog planner."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterator

from cinemath.problems.topic_map import CATALOG_PLANNERS, UNCLASSIFIED

BY_TYPE_DIRNAME = "by-type"
LEGACY_SOURCE_DIRS = ("lamar", "mit", "arizona", "openstax")


def by_type_dir(problems_dir: Path) -> Path:
    return problems_dir / BY_TYPE_DIRNAME


def planner_dir(problems_dir: Path, planner: str) -> Path:
    return by_type_dir(problems_dir) / planner


def pack_dir(problems_dir: Path, planner: str, pack_id: str) -> Path:
    return planner_dir(problems_dir, planner) / pack_id


def iter_planner_batches(
    problems_dir: Path,
    planner: str,
    *,
    include_unclassified: bool = False,
) -> Iterator[Path]:
    """Yield pack directories for a catalog planner."""
    root = planner_dir(problems_dir, planner)
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir() and (include_unclassified or child.name != UNCLASSIFIED):
            yield child


def iter_problems_in_batch(pack_path: Path) -> Iterator[Path]:
    """Yield problem files in a pack directory."""
    yield from sorted(pack_path.glob("prob-*.txt"))


def iter_problems_for_planner(problems_dir: Path, planner: str) -> Iterator[Path]:
    """Yield all problem files assigned to a catalog planner."""
    for batch in iter_planner_batches(problems_dir, planner):
        yield from iter_problems_in_batch(batch)


def write_pack_meta(pack_path: Path, meta: dict[str, Any]) -> None:
    pack_path.mkdir(parents=True, exist_ok=True)
    (pack_path / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def write_problem_file(path: Path, *, header: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header.rstrip() + "\n\n" + body.rstrip() + "\n", encoding="utf-8")


def ensure_planner_readmes(problems_dir: Path) -> None:
    root = by_type_dir(problems_dir)
    root.mkdir(parents=True, exist_ok=True)
    planners = (*CATALOG_PLANNERS, UNCLASSIFIED)
    for planner in planners:
        planner_path = root / planner
        planner_path.mkdir(parents=True, exist_ok=True)
        readme = planner_path / "README.md"
        if readme.exists():
            continue
        if planner == UNCLASSIFIED:
            body = (
                "Problem packs without a shipped catalog planner yet "
                "(series, vector calculus, geometry, etc.).\n"
            )
        else:
            body = (
                f"Batch test with the `{planner}` catalog solver:\n\n"
                f"```bash\n"
                f'find problems/by-type/{planner} -name "prob-*.txt" '
                f'-print0 | xargs -0 -I{{}} uv run cinemath solve {{}} -q l --skip-render\n'
                f"```\n"
            )
        readme.write_text(f"# {planner}\n\n{body}", encoding="utf-8")

    top_readme = root / "README.md"
    if not top_readme.exists():
        top_readme.write_text(
            "# Problem batches by catalog planner\n\n"
            "Each subfolder is a catalog `plan_*` solver. Inside, `pack_id` folders "
            "group problems from a single source topic (Lamar section, MIT topic, etc.).\n\n"
            "Run `uv run python scripts/sync_problem_banks.py` to refresh Lamar scrapes.\n",
            encoding="utf-8",
        )


def remove_legacy_source_trees(problems_dir: Path) -> list[str]:
    """Remove old source-first layout directories. Returns removed paths."""
    removed: list[str] = []
    for name in LEGACY_SOURCE_DIRS:
        path = problems_dir / name
        if path.is_dir():
            shutil.rmtree(path)
            removed.append(str(path))
    return removed
