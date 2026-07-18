"""Pipeline: problem → teacher plan → template → render."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cinemath.ingest import load_problem
from cinemath.llm import TeacherPlan, extract_problem_text, generate_teacher_plan
from cinemath.logger import fmt_path, get_logger, log_step
from cinemath.render_engine.render import render_animation
from cinemath.render_engine.validate import validate_animation
from cinemath.templates import compile_plan

log = get_logger("pipeline")


@dataclass(frozen=True)
class RunResult:
    run_dir: Path
    plan_path: Path
    animation_path: Path
    video_path: Path
    verify_path: Path | None
    teacher: TeacherPlan


def _slug(text: str, *, max_len: int = 40) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (cleaned or "problem")[:max_len].rstrip("-")


def _output_root() -> Path:
    override = os.environ.get("CINEMATH_OUTPUT_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.cwd() / "outputs"


def run_pipeline(
    input_path: Path,
    *,
    output_root: Path | None = None,
    quality: str = "m",
    skip_render: bool = False,
    keep_media: bool = False,
) -> RunResult:
    log.info("input: %s", fmt_path(input_path))
    with log_step(log, "load problem"):
        problem = load_problem(input_path)
    with log_step(log, "extract problem text"):
        problem_text = extract_problem_text(problem)
    with log_step(log, "generate teacher plan"):
        teacher = generate_teacher_plan(problem_text)
    plan = teacher.plan
    verify = teacher.verify
    log.info(
        "plan source: %s%s",
        teacher.source,
        f" ({teacher.planner})" if teacher.planner else "",
    )
    with log_step(log, "compile animation"):
        animation = validate_animation(compile_plan(plan))

    root = output_root or _output_root()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    slug = _slug(plan.get("problem") or input_path.stem)
    run_dir = root / f"{stamp}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=False)
    log.info("writing artifacts to %s", fmt_path(run_dir))

    problem_path = run_dir / "problem.txt"
    plan_path = run_dir / "plan.json"
    verify_path = run_dir / "verify.json"
    animation_path = run_dir / "animation.json"
    video_path = run_dir / "animation.mp4"
    teach_md = run_dir / "lesson.md"

    problem_path.write_text(problem_text.strip() + "\n", encoding="utf-8")
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if verify is not None:
        verify_path.write_text(json.dumps(verify, indent=2) + "\n", encoding="utf-8")
    animation_path.write_text(json.dumps(animation, indent=2) + "\n", encoding="utf-8")
    teach_md.write_text(_lesson_markdown(teacher), encoding="utf-8")

    if not skip_render:
        with log_step(log, f"render video (quality={quality})"):
            media_dir = run_dir / "media" if keep_media else None
            render_animation(
                animation_path,
                media_dir=media_dir,
                output_path=video_path,
                quality=quality,
                cleanup_media=not keep_media,
            )
    else:
        log.info("skip render")

    return RunResult(
        run_dir=run_dir,
        plan_path=plan_path,
        animation_path=animation_path,
        video_path=video_path,
        verify_path=verify_path if verify is not None else None,
        teacher=teacher,
    )


def _lesson_markdown(teacher: TeacherPlan) -> str:
    plan = teacher.plan
    verify = teacher.verify
    visual_tools = [v.get("tool", "?") for v in plan.get("visuals") or [] if isinstance(v, dict)]
    lines = [
        f"# {plan['problem']}",
        "",
        f"**Visuals:** `{', '.join(visual_tools) or 'equation_board'}`",
        f"**Answer:** {plan['answer']}",
        "",
        "## Lesson",
        "",
    ]
    for i, step in enumerate(plan["steps"], 1):
        lines.append(f"### {i}. {step['title']}")
        if step.get("explanation"):
            lines.append(step["explanation"])
            lines.append("")
        for tex in step.get("math") or []:
            lines.append(f"$${tex}$$")
        lines.append("")
    if teacher.source == "catalog":
        lines += [
            "## Source",
            "",
            f"- catalog planner: `{teacher.planner}`",
            "- verification: not needed (plan built deterministically)",
            "",
        ]
    else:
        lines += ["## Verification", "", f"- checked: {verify.get('checked')}", f"- ok: {verify.get('ok')}"]
        for note in (verify or {}).get("notes") or []:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)
