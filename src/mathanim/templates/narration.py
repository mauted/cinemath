"""Narration captions from teacher-plan explanations."""

from __future__ import annotations

import re
from typing import Any

# Inline math that must not be sliced mid-token by soft_trim.
_INLINE_MATH = re.compile(r"\$.+?\$|\\\(.+?\\\)")


def step_narration(step: dict[str, Any], *, max_chars: int = 220) -> str:
    """
    Prefer the spoken explanation; fall back to the board title.

    Soft-trims long prose so captions stay readable in-frame.
    """
    expl = (step.get("explanation") or "").strip()
    title = (step.get("title") or "").strip()
    text = expl or title
    if not text:
        return ""
    return soft_trim(text, max_chars=max_chars)


def soft_trim(text: str, *, max_chars: int = 220) -> str:
    """Keep up to ~max_chars, preferring sentence boundaries.

    Never cuts inside ``$...$`` / ``\\(...\\)`` — that breaks instruction TeX.
    """
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text

    # Prefer ending on a sentence within the budget.
    cut = text[: max_chars + 1]
    for sep in (". ", "! ", "? "):
        idx = cut.rfind(sep)
        if idx >= int(max_chars * 0.45):
            return _balance_math_trim(cut[: idx + 1].strip(), text)

    # Else break on a word.
    idx = cut.rfind(" ")
    if idx > 40:
        candidate = cut[:idx].rstrip(",;:") + "..."
    else:
        candidate = cut[:max_chars].rstrip() + "..."
    return _balance_math_trim(candidate, text)


def _balance_math_trim(candidate: str, full: str) -> str:
    """If a trim landed inside inline math, close the span or back up before it."""
    ellipsis = candidate.endswith("...")
    core = candidate[:-3] if ellipsis else candidate

    for match in _INLINE_MATH.finditer(full):
        start, end = match.start(), match.end()
        # Cut landed strictly inside this math span.
        if start < len(core) < end:
            # Prefer finishing the span when it isn't huge.
            if end - start <= 140:
                closed = full[:end].rstrip()
                if end < len(full):
                    return closed + "..."
                return closed
            before = full[:start].rstrip(",;: ")
            if len(before) > 40:
                return before + "..."
            closed = full[:end].rstrip()
            return closed + ("..." if end < len(full) else "")

    # Odd leftover `$` (e.g. malformed source) — drop the incomplete tail.
    if core.count("$") % 2 == 1:
        last = core.rfind("$")
        before = core[:last].rstrip(",;: ")
        if before:
            return before + ("..." if ellipsis or last < len(full) else "")
    return candidate

def read_wait(text: str, *, base: float = 0.55, per_char: float = 0.012, cap: float = 2.8) -> float:
    """Extra beat so the viewer can read the narration."""
    if not text:
        return 0.35
    return min(cap, base + per_char * len(text))
