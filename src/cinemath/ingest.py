"""Load a math problem from .txt, .md, or image files."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".markdown"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

_MAGIC_TYPES = (
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
)


def _sniff_image_media_type(data: bytes, fallback: str) -> str:
    for magic, media_type in _MAGIC_TYPES:
        if data.startswith(magic):
            return media_type
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        return "image/webp"
    return fallback


@dataclass(frozen=True)
class ProblemInput:
    source_path: Path
    kind: str  # "text" | "image"
    text: str | None = None
    image_media_type: str | None = None
    image_base64: str | None = None


def load_problem(path: Path) -> ProblemInput:
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input not found: {path}")

    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Input file is empty: {path}")
        return ProblemInput(source_path=path, kind="text", text=text)

    if suffix in IMAGE_SUFFIXES:
        raw = path.read_bytes()
        guessed = mimetypes.guess_type(path.name)[0] or "image/png"
        media_type = _sniff_image_media_type(raw, guessed)
        data = base64.standard_b64encode(raw).decode("ascii")
        return ProblemInput(
            source_path=path,
            kind="image",
            image_media_type=media_type,
            image_base64=data,
        )

    raise ValueError(
        f"Unsupported input type '{suffix}'. Use .txt, .md, or an image "
        f"({', '.join(sorted(IMAGE_SUFFIXES))})."
    )
