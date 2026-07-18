from pathlib import Path

import pytest

from cinemath.api.errors import CinemathError, ErrorCode
from cinemath.api.models import (
    GenerationOptions,
    JobContext,
    ProblemInput,
    ProblemSourceKind,
)


def test_problem_input_requires_text_or_path() -> None:
    with pytest.raises(ValueError, match="requires text or source_path"):
        ProblemInput()


def test_problem_input_accepts_text() -> None:
    problem = ProblemInput(text="integrate sin(x) dx")
    assert problem.text == "integrate sin(x) dx"


def test_cinemath_error_retry_classification() -> None:
    retryable = CinemathError.from_code(ErrorCode.RENDER_FAILED, "render failed")
    permanent = CinemathError.from_code(ErrorCode.INVALID_INPUT, "bad input")
    assert retryable.retryable is True
    assert permanent.retryable is False


def test_artifact_entry_checksum_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "plan.json"
    path.write_text("{}", encoding="utf-8")
    from cinemath.api.generate import _artifact_entry

    entry = _artifact_entry(path)
    assert entry.name == "plan.json"
    assert entry.size_bytes == 2
    assert entry.checksum_sha256 is not None


def test_job_context_is_immutable() -> None:
    context = JobContext(job_id="job-1", attempt_id="attempt-1")
    assert context.job_id == "job-1"


def test_generation_options_defaults() -> None:
    opts = GenerationOptions()
    assert opts.quality == "m"
    assert opts.skip_render is False


def test_problem_source_kind_values() -> None:
    assert ProblemSourceKind.MARKDOWN.value == "markdown"
