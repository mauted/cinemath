"""Pipeline: problem → teacher plan → verify → template → render."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cinemath.ingest import load_problem
from cinemath.llm import extract_problem_text, generate_teacher_plan
from cinemath.render_engine.builder import write_scene_module
from cinemath.render_engine.render import copy_animation, render_scene
from cinemath.render_engine.validate import validate_animation
from cinemath.templates import compile_plan
from cinemath.verify import verify_plan


@dataclass(frozen=True)
class RunResult:
    run_dir: Path
    plan_path: Path
    animation_path: Path
    video_path: Path
    verify_path: Path


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
    quality: str = "l",
    skip_render: bool = False,
) -> RunResult:
    problem = load_problem(input_path)
    problem_text = extract_problem_text(problem)
    plan = generate_teacher_plan(problem_text)
    verify = verify_plan(plan)
    animation = validate_animation(compile_plan(plan))

    root = output_root or _output_root()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    slug = _slug(plan.get("problem") or input_path.stem)
    run_dir = root / f"{stamp}_{slug}"
    run_dir.mkdir(parents=True, exist_ok=False)

    problem_path = run_dir / "problem.txt"
    plan_path = run_dir / "plan.json"
    verify_path = run_dir / "verify.json"
    animation_path = run_dir / "animation.json"
    scene_path = run_dir / "scene.py"
    video_path = run_dir / "animation.mp4"
    teach_md = run_dir / "lesson.md"

    problem_path.write_text(problem_text.strip() + "\n", encoding="utf-8")
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    verify_path.write_text(json.dumps(verify, indent=2) + "\n", encoding="utf-8")
    animation_path.write_text(json.dumps(animation, indent=2) + "\n", encoding="utf-8")
    teach_md.write_text(_lesson_markdown(plan, verify), encoding="utf-8")
    write_scene_module(scene_path)

    if not skip_render:
        rendered = render_scene(scene_path, run_dir / "media", quality=quality)
        copy_animation(rendered, video_path)

    return RunResult(
        run_dir=run_dir,
        plan_path=plan_path,
        animation_path=animation_path,
        video_path=video_path,
        verify_path=verify_path,
    )


def _lesson_markdown(plan: dict, verify: dict) -> str:
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
    lines += ["## Verification", "", f"- checked: {verify.get('checked')}", f"- ok: {verify.get('ok')}"]
    for note in verify.get("notes") or []:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)
