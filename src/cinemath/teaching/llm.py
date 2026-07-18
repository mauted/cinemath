"""Anthropic helpers: OCR/normalize + teacher plan."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Literal

from anthropic import Anthropic

from cinemath.planners.arithmetic.tools import ARITHMETIC_TOOLS, run_arithmetic_tool, tool_result_content
from cinemath.core.ingest import ProblemInput
from cinemath.plan.schema import TEACH_SYSTEM
from cinemath.planners.registry import CLASSIFY_SYSTEM, CLASSIFY_TOOLS, run_catalog
from cinemath.plan.validate import PlanValidationError, validate_plan
from cinemath.teaching.verify import verify_feedback_message, verify_plan
from cinemath.core.logger import get_logger

DEFAULT_CLASSIFY_MODEL = "claude-haiku-4-5"
DEFAULT_TEACH_MODEL = "claude-sonnet-5"
_MAX_TOOL_ROUNDS = 6
_MAX_CLASSIFY_ROUNDS = 4
_MAX_VERIFY_RETRIES = 2

log = get_logger("llm")


@dataclass(frozen=True)
class TeacherPlan:
    plan: dict[str, Any]
    source: Literal["catalog", "freeform"]
    planner: str | None = None
    verify: dict[str, Any] | None = None


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


def _classify_model() -> str:
    return (
        os.environ.get("ANTHROPIC_CLASSIFY_MODEL")
        or os.environ.get("ANTHROPIC_MODEL")
        or DEFAULT_CLASSIFY_MODEL
    )


def _teach_model() -> str:
    return (
        os.environ.get("ANTHROPIC_TEACH_MODEL")
        or os.environ.get("ANTHROPIC_MODEL")
        or DEFAULT_TEACH_MODEL
    )


def _create_message(
    client: Anthropic,
    *,
    system: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    tools: list[dict[str, Any]] | None = None,
    model: str | None = None,
) -> Any:
    chosen = model or _teach_model()
    kwargs: dict[str, Any] = {
        "model": chosen,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        kwargs["tools"] = tools
    log.debug(
        "anthropic request model=%s max_tokens=%d tools=%d",
        chosen,
        max_tokens,
        len(tools or []),
    )
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


def _try_catalog_plan(client: Anthropic, problem_text: str) -> tuple[dict[str, Any], str] | None:
    """Classify → catalog planner plan.json, or None for freeform teacher."""
    model = _classify_model()
    log.info("classifying problem (model=%s)", model)
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Classify:\n\n{problem_text}"}
    ]
    for attempt in range(_MAX_CLASSIFY_ROUNDS):
        message = _create_message(
            client,
            system=CLASSIFY_SYSTEM,
            messages=messages,
            max_tokens=1024,
            tools=CLASSIFY_TOOLS,
            model=model,
        )
        uses = _tool_uses(message)
        if not uses:
            log.info("classifier returned no tool call → freeform")
            return None
        if len(uses) != 1:
            raise PlanValidationError("Classifier must call exactly one tool")

        block = uses[0]
        log.debug("classifier tool: %s", block.name)
        try:
            plan = run_catalog(str(block.name), dict(block.input or {}))
        except Exception as exc:  # noqa: BLE001
            log.warning("catalog planner %s failed: %s", block.name, exc)
            messages.append({"role": "assistant", "content": _assistant_content(message)})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": tool_result_content(exc),
                        }
                    ],
                }
            )
            continue

        if plan is not None:
            log.info("catalog hit: %s", block.name)
            return plan, str(block.name)
        log.info("classifier chose teach_freeform")
        return None  # teach_freeform

    log.warning("classifier exhausted %d rounds → freeform", _MAX_CLASSIFY_ROUNDS)
    return None


def extract_problem_text(problem: ProblemInput) -> str:
    client = _client()
    model = _classify_model()
    log.info("extracting problem (%s, model=%s)", problem.kind, model)
    if problem.kind == "text":
        assert problem.text is not None
        message = _create_message(
            client,
            system=EXTRACT_SYSTEM,
            messages=[{"role": "user", "content": problem.text}],
            max_tokens=1024,
            model=model,
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
        model=model,
    )
    return _text_content(message)


def generate_teacher_plan(
    problem_text: str,
    *,
    max_retries: int = 1,
    max_verify_retries: int = _MAX_VERIFY_RETRIES,
) -> TeacherPlan:
    """Classify → catalog plan.json, or freeform LLM teacher → plan.json."""
    client = _client()
    catalog_hit = _try_catalog_plan(client, problem_text)
    if catalog_hit is not None:
        plan, planner = catalog_hit
        return TeacherPlan(plan=plan, source="catalog", planner=planner)

    teach_model = _teach_model()
    log.info("freeform teach (model=%s)", teach_model)
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": f"Teach a clear solution for:\n\n{problem_text}"}
    ]
    last_error: Exception | None = None
    schema_attempts = 0
    verify_attempts = 0
    while True:
        try:
            raw = _teach_with_tools(client, messages)
            plan = validate_plan(_parse_json(raw))
        except (json.JSONDecodeError, PlanValidationError, ValueError) as exc:
            last_error = exc
            schema_attempts += 1
            log.warning("plan validation failed (attempt %d): %s", schema_attempts, exc)
            if schema_attempts > max_retries:
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
            continue

        verify_report = verify_plan(plan)
        if verify_report.get("checked") and not verify_report.get("ok"):
            verify_attempts += 1
            log.warning(
                "verify failed (attempt %d): %s",
                verify_attempts,
                verify_report.get("notes"),
            )
            if verify_attempts > max_verify_retries:
                last_error = PlanValidationError(
                    "Verification failed after "
                    f"{max_verify_retries + 1} attempt(s): {verify_report.get('notes')}"
                )
                break
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": verify_feedback_message(verify_report)})
            continue

        log.info("freeform plan ok (verified=%s)", verify_report.get("ok"))
        return TeacherPlan(plan=plan, source="freeform", verify=verify_report)

    assert last_error is not None
    raise PlanValidationError(
        f"Teacher plan invalid after retries: {last_error}"
    ) from last_error


def _teach_with_tools(client: Anthropic, messages: list[dict[str, Any]]) -> str:
    working = list(messages)
    for _ in range(_MAX_TOOL_ROUNDS):
        message = _create_message(
            client,
            system=TEACH_SYSTEM,
            messages=working,
            max_tokens=4096,
            tools=ARITHMETIC_TOOLS,
            model=_teach_model(),
        )
        uses = _tool_uses(message)
        if not uses:
            text = _text_content(message)
            if not text:
                raise PlanValidationError("Teacher returned empty response")
            log.debug("teacher returned plan JSON")
            return text

        tool_names = [str(block.name) for block in uses]
        log.debug("teacher arithmetic tools: %s", ", ".join(tool_names))

        working.append({"role": "assistant", "content": _assistant_content(message)})
        results: list[dict[str, Any]] = []
        for block in uses:
            try:
                payload = run_arithmetic_tool(block.name, dict(block.input or {}))
                body = tool_result_content(payload)
            except Exception as exc:  # noqa: BLE001
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
