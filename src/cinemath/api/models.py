"""Typed generation request and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"


class ProblemSourceKind(StrEnum):
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    FILE = "file"


@dataclass(frozen=True)
class ProblemInput:
    """Structured problem input for generation."""

    text: str | None = None
    source_path: Path | None = None
    source_kind: ProblemSourceKind | None = None
    mime_type: str | None = None
    course_hint: str | None = None
    topic_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.text and self.source_path is None:
            raise ValueError("ProblemInput requires text or source_path")


@dataclass(frozen=True)
class JobContext:
    """Immutable workspace identity for a generation attempt."""

    job_id: str
    attempt_id: str


@dataclass(frozen=True)
class GenerationOptions:
    quality: str = "m"
    skip_render: bool = False
    keep_media: bool = False
    output_root: Path | None = None
    timeout_seconds: int | None = None


@dataclass(frozen=True)
class ArtifactEntry:
    name: str
    path: Path
    mime_type: str
    size_bytes: int
    checksum_sha256: str | None = None


@dataclass(frozen=True)
class ArtifactManifest:
    engine_version: str
    schema_version: str
    job_id: str
    attempt_id: str
    artifacts: tuple[ArtifactEntry, ...] = field(default_factory=tuple)


class VerificationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    method: str | None = None
    notes: str | None = None
    details: dict[str, Any] | None = None


@dataclass(frozen=True)
class GenerationResult:
    run_dir: Path
    manifest: ArtifactManifest
    verification: VerificationResult | None
    plan_path: Path
    animation_path: Path
    video_path: Path | None
    lesson_path: Path | None
