"""Run Manim to render MathSolution."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

QUALITY_FLAGS = {"l": "-ql", "m": "-qm", "h": "-qh"}


def render_scene(scene_path: Path, media_dir: Path, *, quality: str = "l") -> Path:
    flag = QUALITY_FLAGS.get(quality)
    if flag is None:
        raise ValueError(f"Unknown quality '{quality}'")
    media_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "manim",
        flag,
        str(scene_path),
        "MathSolution",
        "--media_dir",
        str(media_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Manim failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    videos = sorted(media_dir.rglob("MathSolution.mp4"))
    if not videos:
        raise RuntimeError(f"No MathSolution.mp4 under {media_dir}")
    return videos[-1]


def copy_animation(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest
