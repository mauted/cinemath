"""Render progress helpers."""

from __future__ import annotations

from pathlib import Path

_PARTIAL_CLIP_GLOB = "**/partial_movie_files/**/*.mp4"


def test_count_partial_clips(tmp_path: Path) -> None:
    clips = tmp_path / "videos/scene/480p15/partial_movie_files/MathSolution"
    clips.mkdir(parents=True)
    (clips / "a.mp4").write_bytes(b"x")
    (clips / "b.mp4").write_bytes(b"x")
    assert len(list(tmp_path.glob(_PARTIAL_CLIP_GLOB))) == 2
