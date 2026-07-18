"""Normalize Lamar / MathJax LaTeX into cinemath ASCII $...$ fragments."""

from __future__ import annotations

import re

_UNICODE_REPLACEMENTS = {
    "\u2212": "-",
    "\u00b7": r"\cdot ",
    "\u03c0": r"\pi",
    "\u221e": r"\infty",
}


def normalize_lamar_latex(raw: str) -> str:
    """Convert a Lamar practice-problem LaTeX snippet to cinemath style."""
    tex = raw.strip()
    for src, dst in _UNICODE_REPLACEMENTS.items():
        tex = tex.replace(src, dst)

    tex = re.sub(r"\\displaystyle\s*", "", tex)
    tex = re.sub(r"\\left\s*", "", tex)
    tex = re.sub(r"\\right\s*", "", tex)
    tex = re.sub(r"\{\\bf\s*\{e\}\}", "e", tex)
    tex = re.sub(r"\{\\bf\{e\}\}", "e", tex)
    tex = tex.replace(r"{{\bf{e}}", "e^{")
    tex = tex.replace(r"{\bf{e}}", "e")
    tex = re.sub(r"\\left\s*([\(\[\{])", r"\1", tex)
    tex = re.sub(r"\\right\s*([\)\]\}])", r"\1", tex)
    tex = re.sub(r"\{\s*([^{}]+)\s*\}", r"\1", tex)
    tex = re.sub(r"\s+", " ", tex)
    tex = re.sub(r"\{\s*(\d+)\s*\}", r"\1", tex)
    tex = re.sub(r"\^(\d+)", r"^{\1}", tex)
    tex = re.sub(r"\^\{(\d+)\}", r"^{\1}", tex)
    tex = re.sub(r"\\tan\s*\^\s*\{\s*-\s*1\s*\}", r"\\arctan", tex)
    tex = re.sub(r"\\,\s*d([a-zA-Z])", r"\\,d\1", tex)
    return tex.strip()
