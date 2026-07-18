"""Stable public generation contract for workers and integrations."""

from cinemath.api.errors import CinemathError, ErrorCode
from cinemath.api.generate import generate_lesson
from cinemath.api.models import (
    ArtifactEntry,
    ArtifactManifest,
    GenerationOptions,
    GenerationResult,
    JobContext,
    ProblemInput,
    VerificationResult,
)

__all__ = [
    "ArtifactEntry",
    "ArtifactManifest",
    "CinemathError",
    "ErrorCode",
    "GenerationOptions",
    "GenerationResult",
    "JobContext",
    "ProblemInput",
    "VerificationResult",
    "generate_lesson",
]
