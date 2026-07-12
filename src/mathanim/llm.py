"""Anthropic helpers: OCR/normalize + teacher plan (with local arithmetic tools)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from anthropic import Anthropic

from mathanim.arithmetic import ARITHMETIC_TOOLS, run_arithmetic_tool, tool_result_content
from mathanim.ingest import ProblemInput
from mathanim.plan import TEACH_SYSTEM
from mathanim.validate_plan import PlanValidationError, validate_plan

DEFAULT_MODEL = "claude-sonnet-5"
_MAX_TOOL_ROUNDS = 6

EXTRACT_SYSTEM = """You extract a single math problem from user input.
Return ONLY the problem statement.
Rules:
- Wrap EVERY math fragment in single-dollar inline LaTeX: $...$.
- Use ASCII LaTeX only (no unicode glyphs like μ Φ φ ∂ √ ∑ ² − →).
  Write $\\mu$, $\\Phi$, $\\phi$, $\\partial_\\mu$, $\\sqrt{...}$, $\\sum$, $x^{2}$, $-$, $\\to$.
- Keep the statement readable as one or two short paragraphs.
No solution. No preamble. No markdown fences."""


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Anthropic(api_key=api_key)


def _model() -> str:
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)


def _create_message(
    client: Anthropic,
    *,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    tools: list[dict[str, Any]] | None = None,
) -> Any:
    kwargs: dict[str, Any] = {
        "model": _model(),
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
    try:
        return client.messages.create(**kwargs, thinking={"type": "disabled"})
    except TypeError:
        return client.messages.create(**kwargs)
    except Exception as exc:
        if "thinking" in str(exc).lower():
            return client.messages.create(**kwargs)
        raise


def _text_content(message: Any) -> str:
    parts: list[str] = []
    for block in message.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "\n".join(parts).strip()


def _assistant_content(message: Any) -> list[dict[str, Any]]:
    """Serialize assistant content blocks for the next messages round-trip."""
    out: list[dict[str, Any]] = []
    for block in message.content:
        btype = getattr(block, "type", None)
        if btype == "text":
            out.append({"type": "text", "text": block.text})
        elif btype == "tool_use":
            out.append(
                {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": dict(block.input or {}),
                }
            )
    return out


def _tool_uses(message: Any) -> list[Any]:
    return [b for b in message.content if getattr(b, "type", None) == "tool_use"]


def _strip_fences(text: str) -> str:
    text = text.strip()
    fence = re.match(r"^```(?:\w+)?\s*([\s\S]*?)\s*```$", text)
    if fence:
        return fence.group(1).strip()
    return text


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def extract_problem_text(problem: ProblemInput) -> str:
    client = _client()
    if problem.kind == "text":
        assert problem.text is not None
        message = _create_message(
            client,
            system=EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": problem.text}],
            max_tokens=1024,
        )
        return _text_content(message)

    assert problem.image_base64 and problem.image_media_type
    message = _create_message(
        client,
        system=EXTRACT_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": problem.image_media_type,
                            "data": problem.image_base64,
                        },
                    },
                    {"type": "text", "text": "Extract the math problem shown in this image."},
                ],
            }
        ],
        max_tokens=1024,
    )
    return _text_content(message)


def generate_teacher_plan(problem_text: str, *, max_retries: int = 1) -> dict[str, Any]:
    """LLM teaches; local tools compute straightforward arithmetic."""
    client = _client()
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Teach a clear solution for:\n\n{problem_text}"}
    ]
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = _teach_with_tools(client, messages)
            return validate_plan(_parse_json(raw))
        except (json.JSONDecodeError, PlanValidationError, ValueError) as exc:
            last_error = exc
            if attempt >= max_retries:
                break
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous JSON failed validation. "
                        f"Fix it and return ONLY corrected JSON.\n\nError:\n{exc}"
                    ),
                }
            )
    assert last_error is not None
    raise PlanValidationError(
        f"Teacher plan invalid after {max_retries + 1} attempt(s): {last_error}"
    ) from last_error


def _teach_with_tools(client: Anthropic, messages: list[dict[str, Any]]) -> str:
    """Run a tool loop, then return the final assistant text (JSON plan)."""
    working = list(messages)
    for _ in range(_MAX_TOOL_ROUNDS):
        message = _create_message(
            client,
            system=TEACH_SYSTEM,
            messages=working,
            max_tokens=4096,
            tools=ARITHMETIC_TOOLS,
        )
        uses = _tool_uses(message)
        if not uses:
            text = _text_content(message)
            if not text:
                raise PlanValidationError("Teacher returned empty response")
            return text

        working.append({"role": "assistant", "content": _assistant_content(message)})
        results: list[dict[str, Any]] = []
        for block in uses:
            try:
                payload = run_arithmetic_tool(block.name, dict(block.input or {}))
                body = tool_result_content(payload)
            except Exception as exc:  # noqa: BLE001 — surface tool errors to the model
                body = tool_result_content(exc)
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": body,
                }
            )
        working.append({"role": "user", "content": results})

    raise PlanValidationError(f"Teacher exceeded {_MAX_TOOL_ROUNDS} arithmetic tool rounds")
