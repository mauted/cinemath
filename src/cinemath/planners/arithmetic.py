"""Paper arithmetic catalog planners."""

from __future__ import annotations

from typing import Any

from cinemath.arithmetic import run_arithmetic_tool
from cinemath.planners.common import _plan

def plan_long_multiply(problem: str, *, multiplicand: str, multiplier: str) -> dict[str, Any]:
    data = run_arithmetic_tool(
        "long_multiply", {"multiplicand": multiplicand, "multiplier": multiplier}
    )
    product = data["product"]
    return _plan(
        {
            "problem": problem,
            "answer": product,
            "steps": [
                {
                    "title": "Multiply",
                    "explanation": "Use the standard long-multiplication algorithm.",
                    "math": [rf"{data['multiplicand']} \times {data['multiplier']} = {product}"],
                },
            ],
            "visuals": [
                {
                    "tool": "paper_long_multiply",
                    "multiplicand": data["multiplicand"],
                    "multiplier": data["multiplier"],
                    "product": product,
                }
            ],
        }
    )


def plan_long_divide(problem: str, *, dividend: str, divisor: str) -> dict[str, Any]:
    data = run_arithmetic_tool("long_divide", {"dividend": dividend, "divisor": divisor})
    quotient = data["quotient"]
    return _plan(
        {
            "problem": problem,
            "answer": quotient,
            "steps": [
                {
                    "title": "Divide",
                    "explanation": "Use the standard long-division algorithm.",
                    "math": [rf"{data['dividend']} \div {data['divisor']} = {quotient}"],
                },
            ],
            "visuals": [
                {
                    "tool": "paper_long_divide",
                    "dividend": data["dividend"],
                    "divisor": data["divisor"],
                    "quotient": quotient,
                }
            ],
        }
    )


def plan_long_add(problem: str, *, addends: list[str]) -> dict[str, Any]:
    data = run_arithmetic_tool("long_add", {"addends": addends})
    total = data["sum"]
    return _plan(
        {
            "problem": problem,
            "answer": total,
            "steps": [
                {
                    "title": "Add",
                    "explanation": "Add column by column, carrying when needed.",
                    "math": [f"{' + '.join(data['addends'])} = {total}"],
                },
            ],
            "visuals": [{"tool": "paper_long_add", "addends": data["addends"], "sum": total}],
        }
    )


def plan_long_subtract(problem: str, *, minuend: str, subtrahend: str) -> dict[str, Any]:
    data = run_arithmetic_tool("long_subtract", {"minuend": minuend, "subtrahend": subtrahend})
    difference = data["difference"]
    return _plan(
        {
            "problem": problem,
            "answer": difference,
            "steps": [
                {
                    "title": "Subtract",
                    "explanation": "Subtract column by column, borrowing when needed.",
                    "math": [rf"{data['minuend']} - {data['subtrahend']} = {difference}"],
                },
            ],
            "visuals": [
                {
                    "tool": "paper_long_subtract",
                    "minuend": data["minuend"],
                    "subtrahend": data["subtrahend"],
                    "difference": difference,
                }
            ],
        }
    )


