#!/usr/bin/env python3
"""Print full catalog planner I/O. Usage: uv run python tests/show_catalog_io.py quadratic"""

from __future__ import annotations

import sys

from catalog_io import format_catalog_io, run_catalog_io

CASES = {
    "quadratic": (
        "plan_quadratic",
        {
            "problem_statement": "Solve for $x$: $x^2 - 5x + 6 = 0$.",
            "a": 1,
            "b": -5,
            "c": 6,
        },
    ),
}


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "quadratic"
    if name not in CASES:
        print(f"Unknown case {name!r}. Choose from: {', '.join(sorted(CASES))}", file=sys.stderr)
        raise SystemExit(1)
    planner, tool_input = CASES[name]
    io = run_catalog_io(planner, tool_input)
    print(format_catalog_io(io), end="")


if __name__ == "__main__":
    main()
