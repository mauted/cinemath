"""Run Manim to render MathSolution."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from cinemath.render_engine.builder import _ANIMATION_JSON_ENV
from cinemath.logger import fmt_path, get_logger

QUALITY_ARGS: dict[str, list[str]] = {
    "l": ["-ql"],  # 854×480 @ 15fps
    "m": ["-qm", "--frame_rate", "60"],  # 1280×720 @ 60fps
    "h": ["-qh"],  # 1920×1080 @ 60fps
}
_SCENE_MODULE = Path(__file__).resolve().with_name("math_solution_scene.py")
log = get_logger("render")


def _quality_args(quality: str) -> list[str]:
    args = QUALITY_ARGS.get(quality)
    if args is None:
        raise ValueError(f"Unknown quality '{quality}'")
    return args


def render_animation(
    animation_path: Path,
    *,
    media_dir: Path | None = None,
    output_path: Path | None = None,
    quality: str = "m",
    cleanup_media: bool = True,
) -> Path:
    """Render animation.json to MathSolution.mp4."""
    quality_args = _quality_args(quality)
    animation_path = animation_path.resolve()
    if not animation_path.is_file():
        raise FileNotFoundError(animation_path)

    owns_media = media_dir is None
    if owns_media:
        media_dir = Path(tempfile.mkdtemp(prefix="cinemath-manim-"))
    else:
        media_dir = media_dir.resolve()
    media_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env[_ANIMATION_JSON_ENV] = str(animation_path)
    cmd = [
        sys.executable,
        "-m",
        "manim",
        *quality_args,
        str(_SCENE_MODULE),
        "MathSolution",
        "--media_dir",
        str(media_dir),
    ]
    log.info("manim render quality=%s → %s", quality, fmt_path(output_path or animation_path))
    log.debug("manim command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        if owns_media and cleanup_media and media_dir.exists():
            shutil.rmtree(media_dir, ignore_errors=True)
        raise RuntimeError(
            f"Manim failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    videos = sorted(media_dir.rglob("MathSolution.mp4"))
    if not videos:
        if owns_media and cleanup_media and media_dir.exists():
            shutil.rmtree(media_dir, ignore_errors=True)
        raise RuntimeError(f"No MathSolution.mp4 under {media_dir}")
    rendered = videos[-1]
    dest = copy_animation(rendered, output_path) if output_path is not None else rendered
    if owns_media and cleanup_media and media_dir.exists():
        shutil.rmtree(media_dir, ignore_errors=True)
    size_mb = dest.stat().st_size / (1024 * 1024)
    log.info("video ready: %s (%.1f MB)", fmt_path(dest), size_mb)
    return dest


def copy_animation(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest
