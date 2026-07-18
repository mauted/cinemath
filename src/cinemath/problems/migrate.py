"""Migrate legacy source-first problem trees into by-type layout."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from cinemath.problems.layout import (
    pack_dir,
    remove_legacy_source_trees,
    write_pack_meta,
    write_problem_file,
)
from cinemath.problems.topic_map import (
    lamar_pack_id,
    mit_pack_id,
    resolve_curated_planner,
    resolve_lamar_planner,
    resolve_mit_planner,
    UNCLASSIFIED,
)


def _read_meta(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _migrate_lamar_pack(problems_dir: Path, course_dir: Path, section_dir: Path) -> bool:
    meta_path = section_dir / "meta.json"
    if not meta_path.is_file():
        return False
    meta = _read_meta(meta_path)
    course = str(meta.get("course") or course_dir.name).replace("calc", "calc-")
    section = str(meta.get("section") or section_dir.name)
    planner = resolve_lamar_planner(course, section)
    pack_id = lamar_pack_id(course, section)
    dest = pack_dir(problems_dir, planner, pack_id)
    if dest.exists():
        return False
    dest.mkdir(parents=True, exist_ok=True)
    new_meta = {
        **meta,
        "planner": planner,
        "pack_id": pack_id,
        "course": course,
        "section": section,
    }
    write_pack_meta(dest, new_meta)
    for prob in sorted(section_dir.glob("prob-*.txt")):
        text = prob.read_text(encoding="utf-8")
        if "# Planner:" not in text:
            lines = text.splitlines()
            insert_at = 1
            for i, line in enumerate(lines):
                if line.startswith("# Source:"):
                    insert_at = i
                    break
            lines.insert(insert_at, f"# Planner: {planner}")
            lines.insert(insert_at, f"# Pack: {pack_id}")
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        shutil.copy2(prob, dest / prob.name)
        (dest / prob.name).write_text(text, encoding="utf-8")
    return True


def _migrate_mit_pack(problems_dir: Path, course_dir: Path, topic_dir: Path) -> bool:
    meta_path = topic_dir / "meta.json"
    topic = topic_dir.name
    planner = resolve_mit_planner(topic)
    pack_id = mit_pack_id(course_dir.name, topic)
    dest = pack_dir(problems_dir, planner, pack_id)
    if dest.exists():
        return False
    dest.mkdir(parents=True, exist_ok=True)
    meta: dict[str, Any]
    if meta_path.is_file():
        meta = _read_meta(meta_path)
    else:
        meta = {"source": "mit", "slug": topic}
    new_meta = {
        **meta,
        "planner": planner,
        "pack_id": pack_id,
        "course": course_dir.name,
        "topic": topic,
    }
    write_pack_meta(dest, new_meta)
    for prob in sorted(topic_dir.glob("prob-*.txt")):
        text = prob.read_text(encoding="utf-8")
        if "# Planner:" not in text:
            header = (
                f"# MIT {course_dir.name} / {topic}\n"
                f"# Planner: {planner}\n"
                f"# Pack: {pack_id}\n"
            )
            body = text.split("\n\n", 1)[-1] if text.startswith("#") else text
            write_problem_file(dest / prob.name, header=header, body=body)
        else:
            shutil.copy2(prob, dest / prob.name)
    return True


def _migrate_manifest_tree(
    problems_dir: Path,
    source_root: Path,
    *,
    source: str,
    course_key: str = "course",
) -> int:
    """Move empty manifest topic folders into unclassified packs."""
    if not source_root.is_dir():
        return 0
    moved = 0
    for course_dir in sorted(source_root.iterdir()):
        if not course_dir.is_dir():
            continue
        for topic_dir in sorted(course_dir.iterdir()):
            if not topic_dir.is_dir():
                continue
            pack_id = f"{source}-{course_dir.name}-{topic_dir.name}"
            dest = pack_dir(problems_dir, UNCLASSIFIED, pack_id)
            if dest.exists():
                continue
            meta_path = topic_dir / "meta.json"
            if not meta_path.is_file() and not any(topic_dir.glob("prob-*.txt")):
                continue
            dest.mkdir(parents=True, exist_ok=True)
            if meta_path.is_file():
                meta = _read_meta(meta_path)
                meta["planner"] = UNCLASSIFIED
                meta["pack_id"] = pack_id
                meta[course_key] = course_dir.name
                write_pack_meta(dest, meta)
            for prob in topic_dir.glob("prob-*.txt"):
                shutil.copy2(prob, dest / prob.name)
            moved += 1
    return moved


def migrate_curated_links(problems_dir: Path, curated_dir: Path) -> int:
    """Symlink curated ladder files into matching planner batches."""
    if not curated_dir.is_dir():
        return 0
    linked = 0
    for path in sorted(curated_dir.iterdir()):
        if path.suffix not in {".txt", ".md"} or path.name == "README.md":
            continue
        planner = resolve_curated_planner(path.name)
        if planner is None:
            continue
        dest_pack = pack_dir(problems_dir, planner, "curated-ladder")
        dest_pack.mkdir(parents=True, exist_ok=True)
        dest = dest_pack / path.name
        if dest.exists() or dest.is_symlink():
            continue
        dest.symlink_to(path.resolve())
        linked += 1
    return linked


def migrate_legacy_layout(problems_dir: Path, *, remove_legacy: bool = True) -> dict[str, int]:
    """Move problems/lamar|mit|... into problems/by-type/<planner>/<pack>/."""
    stats = {"lamar_packs": 0, "mit_packs": 0, "manifest_packs": 0, "curated_links": 0}
    lamar_root = problems_dir / "lamar"
    if lamar_root.is_dir():
        for course_dir in sorted(lamar_root.iterdir()):
            if not course_dir.is_dir() or course_dir.name == "README.md":
                continue
            for section_dir in sorted(course_dir.iterdir()):
                if section_dir.is_dir() and _migrate_lamar_pack(problems_dir, course_dir, section_dir):
                    stats["lamar_packs"] += 1

    mit_root = problems_dir / "mit"
    if mit_root.is_dir():
        for course_dir in sorted(mit_root.iterdir()):
            if not course_dir.is_dir():
                continue
            for topic_dir in sorted(course_dir.iterdir()):
                if topic_dir.is_dir() and _migrate_mit_pack(problems_dir, course_dir, topic_dir):
                    stats["mit_packs"] += 1

    for source, rel in (
        ("arizona", "arizona/math-129"),
        ("openstax", "openstax/volume-2"),
        ("openstax", "openstax/volume-3"),
    ):
        stats["manifest_packs"] += _migrate_manifest_tree(
            problems_dir, problems_dir / rel, source=source
        )

    stats["curated_links"] = migrate_curated_links(problems_dir, problems_dir / "curated")

    if remove_legacy:
        remove_legacy_source_trees(problems_dir)

    return stats
