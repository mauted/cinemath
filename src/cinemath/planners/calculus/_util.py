"""Shared helpers for calculus catalog entries."""

from __future__ import annotations

from typing import Any


def _problem(tool_input: dict[str, Any], *, name: str) -> str:
    problem = str(tool_input.get("problem_statement") or "").strip()
    if not problem:
        raise ValueError(f"{name} requires problem_statement")
    return problem
