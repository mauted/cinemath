"""Local arithmetic engine + Anthropic tool schemas for paper algorithms."""

from __future__ import annotations

import json
import re
from typing import Any

_DECIMAL_RE = re.compile(r"^\d+(?:\.\d+)?$")

ARITHMETIC_TOOLS: list[dict[str, Any]] = [
    {
        "name": "long_multiply",
        "description": (
            "Compute a multi-digit / decimal product with the standard long-multiplication "
            "algorithm. Call this for long_multiplication problems instead of doing the "
            "arithmetic yourself. Use the returned product as answer and data.product."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "multiplicand": {
                    "type": "string",
                    "description": "Top factor, e.g. '384' or '12.75'.",
                },
                "multiplier": {
                    "type": "string",
                    "description": "Bottom factor, e.g. '67' or '3.4'.",
                },
            },
            "required": ["multiplicand", "multiplier"],
        },
    },
    {
        "name": "long_divide",
        "description": (
            "Compute a whole-number long division (decimal continuation allowed in the "
            "quotient). Call this for long_division problems instead of doing the "
            "arithmetic yourself. Use the returned quotient as answer and data.quotient."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dividend": {
                    "type": "string",
                    "description": "Whole-number dividend, e.g. '9876'.",
                },
                "divisor": {
                    "type": "string",
                    "description": "Whole-number divisor, e.g. '24'.",
                },
            },
            "required": ["dividend", "divisor"],
        },
    },
    {
        "name": "long_add",
        "description": (
            "Compute a multi-digit / decimal sum with the standard stacked long-addition "
            "algorithm. Call this for long_addition problems instead of doing the "
            "arithmetic yourself. Use the returned sum as answer and data.sum."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "addends": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "description": "Addends top-to-bottom, e.g. ['456.7', '89.25'].",
                },
            },
            "required": ["addends"],
        },
    },
    {
        "name": "long_subtract",
        "description": (
            "Compute a multi-digit / decimal difference with the standard stacked "
            "long-subtraction algorithm (minuend >= subtrahend). Call this for "
            "long_subtraction problems instead of doing the arithmetic yourself. Use "
            "the returned difference as answer and data.difference."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "minuend": {
                    "type": "string",
                    "description": "Top number, e.g. '1000' or '45.6'.",
                },
                "subtrahend": {
                    "type": "string",
                    "description": "Bottom number, e.g. '378' or '12.85'.",
                },
            },
            "required": ["minuend", "subtrahend"],
        },
    },
]


def normalize_numeric_literal(
    value: str,
    *,
    allow_decimal: bool = True,
    trim_trailing_zeros: bool = False,
) -> str:
    raw = str(value).strip()
    if not raw:
        raise ValueError("numeric literal must be non-empty")
    if not _DECIMAL_RE.fullmatch(raw):
        raise ValueError(f"invalid numeric literal: {value!r}")
    if not allow_decimal and "." in raw:
        raise ValueError(f"decimals not allowed here: {value!r}")

    if "." not in raw:
        return str(int(raw))

    whole, frac = raw.split(".", 1)
    whole = str(int(whole))
    if trim_trailing_zeros:
        frac = frac.rstrip("0")
    return whole if not frac else f"{whole}.{frac}"


def split_decimal_parts(value: str) -> tuple[str, int]:
    norm = normalize_numeric_literal(value, allow_decimal=True, trim_trailing_zeros=False)
    if "." not in norm:
        return norm, 0
    whole, frac = norm.split(".", 1)
    return whole + frac, len(frac)


def format_scaled_integer(value: int, decimal_places: int, *, trim_trailing_zeros: bool) -> str:
    if decimal_places <= 0:
        return str(value)

    digits = str(abs(int(value)))
    if len(digits) <= decimal_places:
        digits = "0" * (decimal_places - len(digits) + 1) + digits
    cut = len(digits) - decimal_places
    text = f"{digits[:cut]}.{digits[cut:]}"
    out = normalize_numeric_literal(text, allow_decimal=True, trim_trailing_zeros=trim_trailing_zeros)
    return f"-{out}" if value < 0 else out


def _align_decimal_digit_strings(values: list[str]) -> tuple[list[str], int, list[str]]:
    """Pad whole/fractional digits so every value shares the same decimal places and width."""
    norms = [
        normalize_numeric_literal(v, allow_decimal=True, trim_trailing_zeros=False) for v in values
    ]
    places = max((split_decimal_parts(n)[1] for n in norms), default=0)
    digit_strs: list[str] = []
    for n in norms:
        digits, p = split_decimal_parts(n)
        if p < places:
            digits = digits + ("0" * (places - p))
        digit_strs.append(digits)
    max_len = max((len(d) for d in digit_strs), default=1)
    padded = [d.zfill(max_len) for d in digit_strs]
    return padded, places, norms


def analyze_long_addition(addends: list[str]) -> dict[str, Any]:
    if len(addends) < 2:
        raise ValueError("long addition needs at least two addends")
    padded, places, norms = _align_decimal_digit_strings([str(a) for a in addends])
    max_len = len(padded[0])
    # Extra leading column for a possible final carry.
    width = max_len + 1
    start = 1
    carry = 0
    steps: list[dict[str, Any]] = []
    result_digits: list[str] = []
    for offset in range(max_len):
        col = width - 1 - offset
        digits = [int(row[max_len - 1 - offset]) for row in padded]
        incoming = carry
        total = sum(digits) + incoming
        write_digit = total % 10
        carry = total // 10
        parts = [str(d) for d in digits]
        if incoming:
            parts.append(str(incoming))
        lhs_tex = "+".join(parts)
        step: dict[str, Any] = {
            "column": col,
            "digits": [str(d) for d in digits],
            "incoming_carry": incoming,
            "total": total,
            "lhs_tex": lhs_tex,
            "write_digit": str(write_digit),
            "write_col": col,
        }
        if carry:
            if offset == max_len - 1:
                step["lead_digit"] = str(carry)
                step["lead_col"] = col - 1
            else:
                step["carry_digit"] = str(carry)
                step["carry_col"] = col - 1
        steps.append(step)
        result_digits.append(str(write_digit))
    if carry:
        result_digits.append(str(carry))
    result_digits.reverse()
    integer_sum = int("".join(result_digits) or "0")
    total_sum = format_scaled_integer(integer_sum, places, trim_trailing_zeros=True)
    sum_with_decimal = format_scaled_integer(integer_sum, places, trim_trailing_zeros=False)
    return {
        "addends": norms,
        "addend_digits": padded,
        "decimal_places": places,
        "columns": width,
        "start": start,
        "steps": steps,
        "integer_sum": str(integer_sum),
        "sum": total_sum,
        "sum_with_decimal": sum_with_decimal,
    }


def analyze_long_subtraction(minuend: str, subtrahend: str) -> dict[str, Any]:
    padded, places, norms = _align_decimal_digit_strings([minuend, subtrahend])
    top_digits, bottom_digits = padded
    top_value = int(top_digits)
    bottom_value = int(bottom_digits)
    if top_value < bottom_value:
        raise ValueError("long subtraction requires minuend >= subtrahend")
    max_len = len(top_digits)
    width = max_len
    start = 0
    borrow = 0
    steps: list[dict[str, Any]] = []
    result_digits: list[str] = []
    for offset in range(max_len):
        col = width - 1 - offset
        top_digit = int(top_digits[max_len - 1 - offset])
        bottom_digit = int(bottom_digits[max_len - 1 - offset])
        incoming = borrow
        after_borrow = top_digit - incoming
        did_borrow = after_borrow < bottom_digit
        effective = after_borrow + (10 if did_borrow else 0)
        write_digit = effective - bottom_digit
        borrow = 1 if did_borrow else 0
        if did_borrow and incoming:
            lhs_tex = rf"(10+{top_digit}-1)-{bottom_digit}"
        elif did_borrow:
            lhs_tex = rf"(10+{top_digit})-{bottom_digit}"
        elif incoming:
            lhs_tex = rf"({top_digit}-1)-{bottom_digit}"
        else:
            lhs_tex = rf"{top_digit}-{bottom_digit}"
        step: dict[str, Any] = {
            "column": col,
            "top_digit": str(top_digit),
            "bottom_digit": str(bottom_digit),
            "incoming_borrow": incoming,
            "borrowed": did_borrow,
            "effective_top": effective,
            "total": write_digit,
            "lhs_tex": lhs_tex,
            "write_digit": str(write_digit),
            "write_col": col,
        }
        if did_borrow and col > 0:
            # Mark the next column to the left as owing one.
            step["borrow_mark_col"] = col - 1
        steps.append(step)
        result_digits.append(str(write_digit))
    if borrow:
        raise ValueError("internal borrow error in long subtraction")
    result_digits.reverse()
    integer_diff = int("".join(result_digits) or "0")
    difference = format_scaled_integer(integer_diff, places, trim_trailing_zeros=True)
    difference_with_decimal = format_scaled_integer(
        integer_diff,
        places,
        trim_trailing_zeros=False,
    )
    return {
        "minuend": norms[0],
        "subtrahend": norms[1],
        "minuend_digits": top_digits,
        "subtrahend_digits": bottom_digits,
        "decimal_places": places,
        "columns": width,
        "start": start,
        "steps": steps,
        "integer_difference": str(integer_diff),
        "difference": difference,
        "difference_with_decimal": difference_with_decimal,
    }


def analyze_long_multiplication(multiplicand: str, multiplier: str) -> dict[str, Any]:
    top = normalize_numeric_literal(multiplicand, allow_decimal=True, trim_trailing_zeros=False)
    bottom = normalize_numeric_literal(multiplier, allow_decimal=True, trim_trailing_zeros=False)
    top_digits, top_places = split_decimal_parts(top)
    bottom_digits, bottom_places = split_decimal_parts(bottom)

    top_value = int(top_digits)
    bottom_value = int(bottom_digits)
    product_value = top_value * bottom_value
    total_places = top_places + bottom_places

    partials: list[dict[str, Any]] = []
    for shift, digit_char in enumerate(reversed(bottom_digits)):
        partial_value = top_value * int(digit_char)
        partials.append(
            {
                "digit": digit_char,
                "shift": shift,
                "digits": str(partial_value),
                "value": partial_value,
            }
        )

    width = max(
        len(top_digits),
        len(bottom_digits),
        len(str(product_value)),
        max((len(row["digits"]) + row["shift"] for row in partials), default=1),
    )

    top_start = width - len(top_digits)
    bottom_start = width - len(bottom_digits)
    detailed_rows: list[dict[str, Any]] = []
    for shift, row in enumerate(partials):
        carry = 0
        row_steps: list[dict[str, Any]] = []
        output_col = width - 1 - shift
        for top_idx in range(len(top_digits) - 1, -1, -1):
            top_digit = int(top_digits[top_idx])
            bottom_digit = int(row["digit"])
            incoming = carry
            total = top_digit * bottom_digit + incoming
            write_digit = total % 10
            carry = total // 10
            if incoming:
                lhs_tex = rf"{top_digit}\times {bottom_digit}+{incoming}"
            else:
                lhs_tex = rf"{top_digit}\times {bottom_digit}"
            step: dict[str, Any] = {
                "top_index": top_idx,
                "top_digit": str(top_digit),
                "bottom_digit": str(bottom_digit),
                "incoming_carry": incoming,
                "total": total,
                "lhs_tex": lhs_tex,
                "top_col": top_start + top_idx,
                "write_digit": str(write_digit),
                "write_col": output_col,
            }
            if carry:
                if top_idx == 0:
                    # Leftmost multiplicand digit: leftover tens stay in the
                    # partial-product row as a permanent leading digit.
                    step["lead_digit"] = str(carry)
                    step["lead_col"] = output_col - 1
                else:
                    # Intermediate: tens sit above the multiplicand until used.
                    step["carry_digit"] = str(carry)
                    step["carry_col"] = output_col - 1
            row_steps.append(step)
            output_col -= 1
        detailed_rows.append(
            {
                "digit": row["digit"],
                "shift": shift,
                "digits": row["digits"],
                "value": row["value"],
                "steps": row_steps,
            }
        )

    product = format_scaled_integer(product_value, total_places, trim_trailing_zeros=True)
    product_with_decimal = format_scaled_integer(
        product_value,
        total_places,
        trim_trailing_zeros=False,
    )
    return {
        "multiplicand": top,
        "multiplier": bottom,
        "multiplicand_digits": top_digits,
        "multiplier_digits": bottom_digits,
        "multiplicand_places": top_places,
        "multiplier_places": bottom_places,
        "partial_products": partials,
        "rows": detailed_rows,
        "integer_product": str(product_value),
        "product": product,
        "product_with_decimal": product_with_decimal,
        "product_decimal_places": total_places,
        "columns": width,
        "top_start": top_start,
        "bottom_start": bottom_start,
    }


def analyze_long_division(
    dividend: str,
    divisor: str,
    *,
    max_decimal_places: int = 6,
) -> dict[str, Any]:
    dividend_text = normalize_numeric_literal(dividend, allow_decimal=False)
    divisor_text = normalize_numeric_literal(divisor, allow_decimal=False)
    dividend_digits = dividend_text
    divisor_value = int(divisor_text)
    if divisor_value == 0:
        raise ValueError("division by zero")

    stages: list[dict[str, Any]] = []
    quotient_columns: list[int] = []
    quotient_digits: list[str] = []
    current = 0
    started = False

    for idx, digit_char in enumerate(dividend_digits):
        current = current * 10 + int(digit_char)
        if not started and current < divisor_value:
            continue
        started = True
        q_digit = current // divisor_value
        product = q_digit * divisor_value
        remainder = current - product
        current_text = str(current)
        current_end = idx
        stages.append(
            {
                "kind": "integer",
                "q_digit": str(q_digit),
                "q_column": idx,
                "current_text": current_text,
                "current_start": idx - len(current_text) + 1,
                "current_end": current_end,
                "product_text": str(product),
                "product_start": current_end - len(str(product)) + 1,
                "remainder_text": str(remainder),
                "remainder_start": current_end - len(str(remainder)) + 1,
                "bring_down": dividend_digits[idx + 1] if idx + 1 < len(dividend_digits) else None,
                "bring_down_column": idx + 1 if idx + 1 < len(dividend_digits) else None,
            }
        )
        quotient_digits.append(str(q_digit))
        quotient_columns.append(idx)
        current = remainder

    if not started:
        quotient_digits.append("0")
        quotient_columns.append(0)

    decimal_places_used = 0
    remainder = current
    if remainder and stages:
        stages[-1]["bring_down"] = "0"
        stages[-1]["bring_down_column"] = len(dividend_digits)
    while remainder and decimal_places_used < max_decimal_places:
        remainder *= 10
        q_digit = remainder // divisor_value
        product = q_digit * divisor_value
        next_remainder = remainder - product
        current_end = len(dividend_digits) + decimal_places_used
        current_text = str(remainder)
        stages.append(
            {
                "kind": "decimal",
                "q_digit": str(q_digit),
                "q_column": current_end,
                "current_text": current_text,
                "current_start": current_end - len(current_text) + 1,
                "current_end": current_end,
                "product_text": str(product),
                "product_start": current_end - len(str(product)) + 1,
                "remainder_text": str(next_remainder),
                "remainder_start": current_end - len(str(next_remainder)) + 1,
                "bring_down": "0" if next_remainder and decimal_places_used + 1 < max_decimal_places else None,
                "bring_down_column": (
                    current_end if next_remainder and decimal_places_used + 1 < max_decimal_places else None
                ),
                "show_decimal": decimal_places_used == 0,
            }
        )
        quotient_digits.append(str(q_digit))
        quotient_columns.append(current_end)
        remainder = next_remainder
        decimal_places_used += 1

    integer_part = "".join(
        digit for digit, col in zip(quotient_digits, quotient_columns, strict=False) if col < len(dividend_digits)
    )
    decimal_part = "".join(
        digit for digit, col in zip(quotient_digits, quotient_columns, strict=False) if col >= len(dividend_digits)
    )
    quotient = integer_part or "0"
    if decimal_part:
        quotient = f"{quotient}.{decimal_part}"
    quotient = normalize_numeric_literal(quotient, allow_decimal=True, trim_trailing_zeros=True)

    return {
        "dividend": dividend_text,
        "divisor": divisor_text,
        "dividend_digits": dividend_digits,
        "divisor_digits": divisor_text,
        "quotient": quotient,
        "quotient_digits": quotient_digits,
        "quotient_columns": quotient_columns,
        "stages": stages,
        "extra_decimal_digits": decimal_places_used,
        "terminated": remainder == 0,
    }


def run_arithmetic_tool(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Dispatch an Anthropic tool_use block to local arithmetic."""
    if name == "long_multiply":
        analysis = analyze_long_multiplication(
            str(tool_input.get("multiplicand", "")),
            str(tool_input.get("multiplier", "")),
        )
        return {
            "multiplicand": analysis["multiplicand"],
            "multiplier": analysis["multiplier"],
            "product": analysis["product"],
            "integer_product": analysis["integer_product"],
            "product_decimal_places": analysis["product_decimal_places"],
        }
    if name == "long_divide":
        analysis = analyze_long_division(
            str(tool_input.get("dividend", "")),
            str(tool_input.get("divisor", "")),
        )
        return {
            "dividend": analysis["dividend"],
            "divisor": analysis["divisor"],
            "quotient": analysis["quotient"],
            "terminated": analysis["terminated"],
            "extra_decimal_digits": analysis["extra_decimal_digits"],
        }
    if name == "long_add":
        raw_addends = tool_input.get("addends") or []
        if not isinstance(raw_addends, list):
            raise ValueError("long_add requires addends: list[str]")
        analysis = analyze_long_addition([str(a) for a in raw_addends])
        return {
            "addends": analysis["addends"],
            "sum": analysis["sum"],
            "integer_sum": analysis["integer_sum"],
            "decimal_places": analysis["decimal_places"],
        }
    if name == "long_subtract":
        analysis = analyze_long_subtraction(
            str(tool_input.get("minuend", "")),
            str(tool_input.get("subtrahend", "")),
        )
        return {
            "minuend": analysis["minuend"],
            "subtrahend": analysis["subtrahend"],
            "difference": analysis["difference"],
            "integer_difference": analysis["integer_difference"],
            "decimal_places": analysis["decimal_places"],
        }
    raise ValueError(f"Unknown arithmetic tool: {name}")


def tool_result_content(result: dict[str, Any] | Exception) -> str:
    if isinstance(result, Exception):
        return json.dumps({"error": str(result)})
    return json.dumps(result)
