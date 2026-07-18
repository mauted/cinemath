"""Public generation entrypoint."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import tempfile
from pathlib import Path

from cinemath import __version__
from cinemath.api.errors import CinemathError, ErrorCode
from cinemath.api.models import (
    SCHEMA_VERSION,
    ArtifactEntry,
    ArtifactManifest,
    GenerationOptions,
    GenerationResult,
    JobContext,
    ProblemInput,
    VerificationResult,
    VerificationStatus,
)
from cinemath.core.pipeline import run_pipeline


def _materialize_problem_input(problem: ProblemInput) -> Path:
    if problem.source_path is not None:
        return problem.source_path

    if not problem.text:
        raise CinemathError.permanent(
            ErrorCode.INVALID_INPUT,
            "Problem text is required when no source_path is provided.",
        )

    suffix = ".md" if problem.source_kind and problem.source_kind.value == "markdown" else ".txt"
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as handle:
        handle.write(problem.text.strip() + "\n")
        return Path(handle.name)


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_entry(path: Path) -> ArtifactEntry:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return ArtifactEntry(
        name=path.name,
        path=path,
        mime_type=mime_type,
        size_bytes=path.stat().st_size,
        checksum_sha256=_checksum(path),
    )


def _verification_from_file(path: Path | None) -> VerificationResult | None:
    if path is None or not path.exists():
        return VerificationResult(status=VerificationStatus.SKIPPED, method="catalog")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return VerificationResult(
            status=VerificationStatus.FAILED,
            method="sympy",
            notes="Could not parse verify.json",
            details={"error": str(exc)},
        )

    passed = bool(payload.get("passed"))
    return VerificationResult(
        status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
        method=str(payload.get("method") or "sympy"),
        notes=str(payload.get("summary") or "") or None,
        details=payload,
    )


def generate_lesson(
    problem: ProblemInput,
    *,
    context: JobContext,
    options: GenerationOptions | None = None,
) -> GenerationResult:
    """Generate a lesson from structured input and return a versioned manifest."""

    opts = options or GenerationOptions()
    input_path = _materialize_problem_input(problem)

    try:
        pipeline_result = run_pipeline(
            input_path,
            output_root=opts.output_root,
            quality=opts.quality,
            skip_render=opts.skip_render,
            keep_media=opts.keep_media,
        )
    except FileNotFoundError as exc:
        raise CinemathError.permanent(
            ErrorCode.INVALID_INPUT,
            "Problem input file was not found.",
            cause=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001 - mapped to typed API error
        raise CinemathError.from_code(
            ErrorCode.INTERNAL,
            "Lesson generation failed.",
            cause=str(exc),
        ) from exc
    finally:
        if problem.source_path is None and input_path.exists():
            input_path.unlink(missing_ok=True)

    artifact_paths = [
        pipeline_result.run_dir / "problem.txt",
        pipeline_result.plan_path,
        pipeline_result.animation_path,
        pipeline_result.run_dir / "lesson.md",
    ]
    if pipeline_result.verify_path is not None:
        artifact_paths.append(pipeline_result.verify_path)
    if not opts.skip_render:
        artifact_paths.append(pipeline_result.video_path)

    artifacts = tuple(_artifact_entry(path) for path in artifact_paths if path.exists())
    manifest = ArtifactManifest(
        engine_version=__version__,
        schema_version=SCHEMA_VERSION,
        job_id=context.job_id,
        attempt_id=context.attempt_id,
        artifacts=artifacts,
    )

    return GenerationResult(
        run_dir=pipeline_result.run_dir,
        manifest=manifest,
        verification=_verification_from_file(pipeline_result.verify_path),
        plan_path=pipeline_result.plan_path,
        animation_path=pipeline_result.animation_path,
        video_path=None if opts.skip_render else pipeline_result.video_path,
        lesson_path=pipeline_result.run_dir / "lesson.md",
    )
