"""DSL scene: introduce the problem before solving."""

from __future__ import annotations

from mathanim.templates import dsl
from mathanim.templates.narration import read_wait


def problem_statement_scene(problem: str) -> dict[str, object]:
    """
    Full-frame intro: write the problem statement, pause to read, then fade.

    ``pin=False`` so the statement clears before the solution begins.
    """
    text = problem.strip()

    return dsl.scene(
        "problem",
        caption="Problem",
        pin=False,
        objects=[
            {
                "id": "stmt",
                "type": "statement",
                "content": text,
                "at": "center",
                "font_size": 30,
                "color": "white",
            }
        ],
        actions=[
            dsl.write("stmt"),
            dsl.wait(read_wait(text, base=1.1, per_char=0.014, cap=3.8)),
        ],
    )
