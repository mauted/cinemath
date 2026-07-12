"""Normalize unicode math characters into TeX-safe strings."""

from __future__ import annotations

import re

# Common physics/math unicode → LaTeX (math mode) or ASCII (text mode).
_UNICODE_TO_LATEX = {
    "Γ": r"\Gamma",
    "γ": r"\gamma",
    "Δ": r"\Delta",
    "δ": r"\delta",
    "Θ": r"\Theta",
    "θ": r"\theta",
    "Λ": r"\Lambda",
    "λ": r"\lambda",
    "Μ": r"M",
    "μ": r"\mu",
    "Ξ": r"\Xi",
    "ξ": r"\xi",
    "Π": r"\Pi",
    "π": r"\pi",
    "Σ": r"\Sigma",
    "σ": r"\sigma",
    "Φ": r"\Phi",
    "φ": r"\phi",
    "ϕ": r"\varphi",
    "Ψ": r"\Psi",
    "ψ": r"\psi",
    "Ω": r"\Omega",
    "ω": r"\omega",
    "α": r"\alpha",
    "β": r"\beta",
    "ε": r"\varepsilon",
    "η": r"\eta",
    "ρ": r"\rho",
    "τ": r"\tau",
    "χ": r"\chi",
    "∂": r"\partial",
    "∞": r"\infty",
    "±": r"\pm",
    "·": r"\cdot",
    "×": r"\times",
    "→": r"\to",
    "←": r"\leftarrow",
    "⇒": r"\Rightarrow",
    "≈": r"\approx",
    "≠": r"\neq",
    "≤": r"\leq",
    "≥": r"\geq",
    "⊃": r"\supset",
    "∈": r"\in",
    "ℏ": r"\hbar",
    "−": r"-",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∬": r"\iint",
    "∮": r"\oint",
    "√": r"\sqrt",
    "²": r"^{2}",
    "³": r"^{3}",
    "⁴": r"^{4}",
    "₁": r"_{1}",
    "₂": r"_{2}",
}

_UNICODE_TO_ASCII = {
    "Γ": "Gamma",
    "γ": "gamma",
    "Δ": "Delta",
    "δ": "delta",
    "Θ": "Theta",
    "θ": "theta",
    "Λ": "Lambda",
    "λ": "lambda",
    "μ": "mu",
    "π": "pi",
    "Σ": "Sigma",
    "σ": "sigma",
    "Φ": "Phi",
    "φ": "phi",
    "ϕ": "varphi",
    "Ψ": "Psi",
    "ψ": "psi",
    "Ω": "Omega",
    "ω": "omega",
    "α": "alpha",
    "β": "beta",
    "τ": "tau",
    "∂": "d",
    "∞": "inf",
    "±": "+/-",
    "·": "*",
    "×": "x",
    "→": "->",
    "←": "<-",
    "⇒": "=>",
    "≈": "~",
    "≠": "!=",
    "≤": "<=",
    "≥": ">=",
    "⊃": "supset",
    "∈": "in",
    "ℏ": "hbar",
    "−": "-",
    "–": "-",
    "—": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "…": "...",
    "∑": "sum",
    "∏": "prod",
    "∫": "int",
    "∬": "iint",
    "√": "sqrt",
    "²": "^2",
    "³": "^3",
    "⁴": "^4",
}


# Commands that need extra packages Manim's default template may lack.
_SLASHED_RE = re.compile(r"\\slashed\s*\{([^{}]+)\}")


def to_math_tex(s: str) -> str:
    """Replace unicode math glyphs with LaTeX commands for MathTex."""
    out = []
    for ch in s:
        out.append(_UNICODE_TO_LATEX.get(ch, ch))
    tex = "".join(out)
    # `\slashed` needs the slashed package; `\not` is available via amsmath.
    return _SLASHED_RE.sub(r"\\not{\1}", tex)


def unicode_math_char(ch: str) -> str | None:
    """Return a math-mode TeX command for a unicode glyph, or None."""
    return _UNICODE_TO_LATEX.get(ch)


def to_plain_tex_text(s: str) -> str:
    """Replace unicode math glyphs with ASCII for text-mode TeX."""
    out = []
    for ch in s:
        out.append(_UNICODE_TO_ASCII.get(ch, ch))
    return "".join(out)
