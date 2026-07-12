"""Paper-style long multiplication, division, addition, and subtraction layouts."""

from __future__ import annotations

from typing import Any, Callable

from cinemath.arithmetic import (
    analyze_long_addition,
    analyze_long_division,
    analyze_long_multiplication,
    analyze_long_subtraction,
    split_decimal_parts,
)
from cinemath.templates import dsl
from cinemath.templates.narration import read_wait, step_narration

DIGIT_W = 0.58
ROW_H = 0.58
MAIN_FONT = 38
QUOT_FONT = 34
SMALL_FONT = 24
BRACKET_FONT = 70
RIGHT_EDGE = 2.15
DIV_BASE_X = -0.1
# Half-height of MAIN_FONT digits; keep bars outside glyph boxes.
DIGIT_HALF_H = 0.30
# Side pad for a×b+c scratch work during long multiplication.
SIDE_X = -3.55
SIDE_Y = 0.35


def compile_long_multiplication(plan: dict[str, Any]) -> dict[str, Any]:
    steps = plan["steps"]
    data = analyze_long_multiplication(
        str(plan["data"]["multiplicand"]),
        str(plan["data"]["multiplier"]),
    )
    captions = _captions(steps)
    opening = _caption(captions, 0, "Set up the multiplication.")

    total_cols = int(data["columns"])
    x_of = _mul_x_fn(total_cols)

    carry_y = 1.92
    top_y = 1.35
    bottom_y = 0.72
    # Vinculum sits in the gap under the multiplier, not through partials.
    line1_y = bottom_y - DIGIT_HALF_H - 0.14
    partial_start_y = line1_y - DIGIT_HALF_H - 0.22
    partial_ys = [partial_start_y - i * ROW_H for i in range(len(data["rows"]))]
    line2_y = (partial_ys[-1] - DIGIT_HALF_H - 0.14) if partial_ys else (line1_y - 0.55)
    product_y = line2_y - DIGIT_HALF_H - 0.22

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    top_objs, top_ids, top_dot = _number_objects_explicit(
        "top",
        data["multiplicand"],
        int(data["top_start"]),
        x_of,
        top_y,
    )
    bottom_objs, bottom_ids, bottom_dot = _number_objects_explicit(
        "bottom",
        data["multiplier"],
        int(data["bottom_start"]),
        x_of,
        bottom_y,
    )
    objects.extend(top_objs)
    objects.extend(bottom_objs)

    left_bar_x = min(x_of(float(data["bottom_start"]) - 0.85), x_of(0) - 0.2)
    right_bar_x = x_of(total_cols - 1) + 0.28
    op_x = x_of(float(data["bottom_start"]) - 0.85)
    objects.append(_math_obj("mul_sign", r"\times", op_x, bottom_y))
    objects.append(
        _line_obj("mul_line_1", left_bar_x, line1_y, right_bar_x, line1_y, stroke_width=3.0)
    )

    setup_ids = [*top_ids, *bottom_ids, "mul_sign", "mul_line_1"]
    if top_dot is not None:
        setup_ids.append(top_dot)
    if bottom_dot is not None:
        setup_ids.append(bottom_dot)

    row_side_meta: list[list[dict[str, Any]]] = []
    active_bottom_ids: list[str] = []
    for row_idx, row in enumerate(data["rows"]):
        side_meta: list[dict[str, Any]] = []
        y = partial_ys[row_idx]
        for step_idx, step in enumerate(row["steps"]):
            digit_id = f"partial_{row_idx}_{step_idx}"
            objects.append(_math_obj(digit_id, step["write_digit"], x_of(step["write_col"]), y))

            carry_id: str | None = None
            lead_id: str | None = None
            carry_digit = step.get("carry_digit")
            carry_col = step.get("carry_col")
            lead_digit = step.get("lead_digit")
            lead_col = step.get("lead_col")
            tens_digit = carry_digit if carry_digit is not None else lead_digit
            if carry_digit is not None and carry_col is not None:
                carry_id = f"carry_{row_idx}_{step_idx}"
                objects.append(
                    _math_obj(
                        carry_id,
                        str(carry_digit),
                        x_of(carry_col),
                        carry_y,
                        font_size=SMALL_FONT,
                        color="yellow",
                    )
                )
            if lead_digit is not None and lead_col is not None:
                lead_id = f"partial_lead_{row_idx}_{step_idx}"
                objects.append(_math_obj(lead_id, str(lead_digit), x_of(lead_col), y))

            # Scratch work on the left: a×b[+c] = [tens]ones.
            lhs_id = f"side_{row_idx}_{step_idx}_lhs"
            eq_id = f"side_{row_idx}_{step_idx}_eq"
            objects.append(_math_obj(lhs_id, step["lhs_tex"], SIDE_X, SIDE_Y, font_size=34))
            objects.append(
                {
                    "id": eq_id,
                    "type": "math",
                    "tex": "=",
                    "next_to": lhs_id,
                    "direction": "right",
                    "font_size": 34,
                    "color": "white",
                }
            )
            side_ids = [lhs_id, eq_id]
            side_tens_id: str | None = None
            side_write_id = f"side_{row_idx}_{step_idx}_write"
            if tens_digit is not None:
                side_tens_id = f"side_{row_idx}_{step_idx}_tens"
                objects.append(
                    {
                        "id": side_tens_id,
                        "type": "math",
                        "tex": str(tens_digit),
                        "next_to": eq_id,
                        "direction": "right",
                        "font_size": 34,
                        "color": "yellow" if carry_id is not None else "white",
                    }
                )
                objects.append(
                    {
                        "id": side_write_id,
                        "type": "math",
                        "tex": step["write_digit"],
                        "next_to": side_tens_id,
                        "direction": "right",
                        "font_size": 34,
                        "color": "white",
                    }
                )
                side_ids.extend([side_tens_id, side_write_id])
            else:
                objects.append(
                    {
                        "id": side_write_id,
                        "type": "math",
                        "tex": step["write_digit"],
                        "next_to": eq_id,
                        "direction": "right",
                        "font_size": 34,
                        "color": "white",
                    }
                )
                side_ids.append(side_write_id)
            board_tens_id = carry_id if carry_id is not None else lead_id
            side_meta.append(
                {
                    "side_ids": side_ids,
                    "side_write_id": side_write_id,
                    "side_tens_id": side_tens_id,
                    "board_write_id": digit_id,
                    "board_tens_id": board_tens_id,
                    "board_carry_id": carry_id,
                    "incoming_carry": int(step.get("incoming_carry") or 0),
                }
            )
        row_side_meta.append(side_meta)
        active_bottom_ids.append(bottom_ids[len(bottom_ids) - 1 - row_idx])

    integer_product = str(data["integer_product"])
    product_start = total_cols - len(integer_product)
    product_objs, product_ids = _row_digit_objects_explicit("product", integer_product, product_start, x_of, product_y)
    objects.extend(product_objs)
    objects.append(
        _line_obj("mul_line_2", left_bar_x, line2_y, right_bar_x, line2_y, stroke_width=3.0)
    )

    product_dot: str | None = None
    if data["product_decimal_places"]:
        product_dot = "product_dot"
        objects.append(
            _math_obj(
                product_dot,
                ".",
                x_of(total_cols - data["product_decimal_places"] - 0.5),
                product_y,
            )
        )

    actions.append(dsl.fade_in(*setup_ids))
    actions.append(dsl.wait(read_wait(opening)))
    current_caption = opening

    multiply_steps = _matching_step_texts(steps, "multiply")
    add_step = _first_matching_step_text(steps, "add")
    count_step = _first_matching_step_text(steps, "count", "decimal")
    place_match = _first_matching_title_text(steps, "place", "decimal") or _first_matching_step_text(
        steps,
        "place",
        "decimal",
    )
    place_step = place_match[1] if place_match is not None else "Place the decimal point."
    simplify_match = _first_matching_step_text(steps, "simplify")
    simplify_step = simplify_match[1] if simplify_match is not None else _caption(
        captions,
        len(captions) - 1,
        "Write the final product.",
    )

    has_decimal = bool(data["multiplicand_places"] or data["multiplier_places"])
    count_before_work = False
    if count_step is not None:
        first_mul_idx = multiply_steps[0][0] if multiply_steps else 10**9
        count_before_work = count_step[0] < first_mul_idx

    if has_decimal and count_before_work:
        current_caption = _maybe_set_caption(actions, current_caption, count_step[1])
        dot_ids = [dot for dot in (top_dot, bottom_dot) if dot is not None]
        if dot_ids:
            actions.append(dsl.indicate(*dot_ids))
            actions.append(dsl.wait(0.25))

    for row_idx, row in enumerate(data["rows"]):
        current_caption = _maybe_set_caption(
            actions,
            current_caption,
            _caption_from_matches(multiply_steps, row_idx, "Multiply by the next digit."),
        )
        bottom_id = active_bottom_ids[row_idx]
        prev_carry_id: str | None = None
        for step_idx, step in enumerate(row["steps"]):
            meta = row_side_meta[row_idx][step_idx]
            pair = [bottom_id]
            consumed_carry: str | None = None
            if step["top_index"] >= 0:
                pair.append(top_ids[step["top_index"]])
            if meta["incoming_carry"] and prev_carry_id is not None:
                pair.append(prev_carry_id)
                consumed_carry = prev_carry_id
            actions.append(dsl.indicate(*pair))
            actions.append(dsl.fade_in(*meta["side_ids"]))
            actions.append(dsl.wait(0.35))
            # Swipe result digit(s) from the side pad into the paper tableau.
            actions.append(dsl.transform(meta["side_write_id"], meta["board_write_id"]))
            if meta["side_tens_id"] is not None and meta["board_tens_id"] is not None:
                actions.append(dsl.transform(meta["side_tens_id"], meta["board_tens_id"]))
            leftovers = [
                sid
                for sid in meta["side_ids"]
                if sid not in {meta["side_write_id"], meta["side_tens_id"]}
            ]
            if leftovers:
                actions.append(dsl.fade_out(*leftovers))
            if consumed_carry is not None:
                actions.append(dsl.fade_out(consumed_carry))
            actions.append(dsl.wait(0.12))
            prev_carry_id = meta["board_carry_id"]

    current_caption = _maybe_set_caption(
        actions,
        current_caption,
        add_step[1] if add_step is not None else "Add the partial products.",
    )
    actions.append(dsl.fade_in("mul_line_2", *product_ids))
    actions.append(dsl.wait(0.35))

    if has_decimal and count_step is not None and not count_before_work:
        current_caption = _maybe_set_caption(actions, current_caption, count_step[1])
        dot_ids = [dot for dot in (top_dot, bottom_dot) if dot is not None]
        if dot_ids:
            actions.append(dsl.indicate(*dot_ids))
            actions.append(dsl.wait(0.25))

    if has_decimal and product_dot is not None:
        current_caption = _maybe_set_caption(actions, current_caption, place_step)
        highlight = [dot for dot in (top_dot, bottom_dot, product_dot) if dot is not None]
        actions.append(dsl.fade_in(product_dot))
        actions.append(dsl.indicate(*highlight))
        actions.append(dsl.wait(0.35))

    trimmed = _trimmed_zero_ids(data["product_with_decimal"], data["product"], product_ids)
    if has_decimal and trimmed:
        current_caption = _maybe_set_caption(actions, current_caption, simplify_step)
        actions.append(dsl.fade_out(*trimmed))
    else:
        current_caption = _maybe_set_caption(
            actions,
            current_caption,
            _caption(captions, len(captions) - 1, "This is the final product."),
        )
    final_targets = [pid for pid in product_ids if pid not in trimmed]
    if product_dot is not None:
        final_targets.append(product_dot)
    actions.append(dsl.indicate(*final_targets))
    actions.append(dsl.wait(0.45))

    scene = dsl.scene(
        "paper_multiplication",
        caption=opening,
        objects=objects,
        actions=actions,
        pin=False,
        separate_labels=False,
    )
    return dsl.script(
        plan["problem"],
        plan["answer"],
        [s["title"] for s in steps],
        [scene],
    )


def compile_long_addition(plan: dict[str, Any]) -> dict[str, Any]:
    steps = plan["steps"]
    data = analyze_long_addition([str(a) for a in plan["data"]["addends"]])
    captions = _captions(steps)
    opening = _caption(captions, 0, "Set up the addition.")

    total_cols = int(data["columns"])
    x_of = _mul_x_fn(total_cols)
    n_addends = len(data["addends"])
    places = int(data["decimal_places"])
    start = int(data["start"])

    carry_y = 1.55 + 0.35 * max(0, n_addends - 2)
    addend_top_y = carry_y - 0.55
    addend_ys = [addend_top_y - i * ROW_H for i in range(n_addends)]
    line_y = addend_ys[-1] - DIGIT_HALF_H - 0.14
    sum_y = line_y - DIGIT_HALF_H - 0.22

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    addend_id_rows: list[dict[int, str]] = []
    addend_dot_ids: list[str | None] = []
    setup_ids: list[str] = []
    for row_idx, digits in enumerate(data["addend_digits"]):
        visible, lead = _visible_padded_span(digits, places)
        objs, ids = _row_digit_objects_explicit(
            f"addend{row_idx}",
            visible,
            start + lead,
            x_of,
            addend_ys[row_idx],
        )
        objects.extend(objs)
        col_map = {start + lead + i: oid for i, oid in enumerate(ids)}
        addend_id_rows.append(col_map)
        setup_ids.extend(ids)
        dot_id: str | None = None
        if places:
            dot_id = f"addend{row_idx}_dot"
            objects.append(
                _math_obj(
                    dot_id,
                    ".",
                    x_of(start + len(digits) - places - 0.5),
                    addend_ys[row_idx],
                )
            )
            setup_ids.append(dot_id)
        addend_dot_ids.append(dot_id)

    op_x = x_of(float(start) - 0.85)
    objects.append(_math_obj("add_sign", "+", op_x, addend_ys[-1]))
    left_bar_x = min(op_x - 0.15, x_of(0) - 0.2)
    right_bar_x = x_of(total_cols - 1) + 0.28
    objects.append(_line_obj("add_line", left_bar_x, line_y, right_bar_x, line_y, stroke_width=3.0))
    setup_ids.extend(["add_sign", "add_line"])

    side_meta: list[dict[str, Any]] = []
    for step_idx, step in enumerate(data["steps"]):
        write_id = f"sum_{step_idx}"
        objects.append(_math_obj(write_id, step["write_digit"], x_of(step["write_col"]), sum_y))

        carry_id: str | None = None
        lead_id: str | None = None
        carry_digit = step.get("carry_digit")
        carry_col = step.get("carry_col")
        lead_digit = step.get("lead_digit")
        lead_col = step.get("lead_col")
        tens_digit = carry_digit if carry_digit is not None else lead_digit
        if carry_digit is not None and carry_col is not None:
            carry_id = f"add_carry_{step_idx}"
            objects.append(
                _math_obj(
                    carry_id,
                    str(carry_digit),
                    x_of(carry_col),
                    carry_y,
                    font_size=SMALL_FONT,
                    color="yellow",
                )
            )
        if lead_digit is not None and lead_col is not None:
            lead_id = f"sum_lead_{step_idx}"
            objects.append(_math_obj(lead_id, str(lead_digit), x_of(lead_col), sum_y))

        lhs_id = f"side_add_{step_idx}_lhs"
        eq_id = f"side_add_{step_idx}_eq"
        objects.append(_math_obj(lhs_id, step["lhs_tex"], SIDE_X, SIDE_Y, font_size=34))
        objects.append(
            {
                "id": eq_id,
                "type": "math",
                "tex": "=",
                "next_to": lhs_id,
                "direction": "right",
                "font_size": 34,
                "color": "white",
            }
        )
        side_ids = [lhs_id, eq_id]
        side_tens_id: str | None = None
        side_write_id = f"side_add_{step_idx}_write"
        if tens_digit is not None:
            side_tens_id = f"side_add_{step_idx}_tens"
            objects.append(
                {
                    "id": side_tens_id,
                    "type": "math",
                    "tex": str(tens_digit),
                    "next_to": eq_id,
                    "direction": "right",
                    "font_size": 34,
                    "color": "yellow" if carry_id is not None else "white",
                }
            )
            objects.append(
                {
                    "id": side_write_id,
                    "type": "math",
                    "tex": step["write_digit"],
                    "next_to": side_tens_id,
                    "direction": "right",
                    "font_size": 34,
                    "color": "white",
                }
            )
            side_ids.extend([side_tens_id, side_write_id])
        else:
            objects.append(
                {
                    "id": side_write_id,
                    "type": "math",
                    "tex": step["write_digit"],
                    "next_to": eq_id,
                    "direction": "right",
                    "font_size": 34,
                    "color": "white",
                }
            )
            side_ids.append(side_write_id)

        digit_index = len(data["addend_digits"][0]) - 1 - step_idx
        col = start + digit_index
        column_ids = [row[col] for row in addend_id_rows if col in row]
        # Side scratch still uses the algorithmic digit (including pad zeros).
        side_meta.append(
            {
                "column_ids": column_ids,
                "side_ids": side_ids,
                "side_write_id": side_write_id,
                "side_tens_id": side_tens_id,
                "board_write_id": write_id,
                "board_tens_id": carry_id if carry_id is not None else lead_id,
                "board_carry_id": carry_id,
                "incoming_carry": int(step.get("incoming_carry") or 0),
            }
        )

    # Result digits already animated; optional decimal point + trim trailing zeros.
    sum_dot: str | None = None
    if places:
        sum_dot = "sum_dot"
        objects.append(
            _math_obj(
                sum_dot,
                ".",
                x_of(start + len(data["addend_digits"][0]) - places - 0.5),
                sum_y,
            )
        )

    actions.append(dsl.fade_in(*setup_ids))
    actions.append(dsl.wait(read_wait(opening)))
    current_caption = opening

    column_steps = _matching_step_texts(steps, "column") or _matching_step_texts(steps, "add")

    prev_carry_id: str | None = None
    for step_idx, meta in enumerate(side_meta):
        current_caption = _maybe_set_caption(
            actions,
            current_caption,
            _caption_from_matches(column_steps, step_idx, "Add the next column."),
        )
        pair = list(meta["column_ids"])
        consumed_carry: str | None = None
        if meta["incoming_carry"] and prev_carry_id is not None:
            pair.append(prev_carry_id)
            consumed_carry = prev_carry_id
        if pair:
            actions.append(dsl.indicate(*pair))
        actions.append(dsl.fade_in(*meta["side_ids"]))
        actions.append(dsl.wait(0.35))
        actions.append(dsl.transform(meta["side_write_id"], meta["board_write_id"]))
        if meta["side_tens_id"] is not None and meta["board_tens_id"] is not None:
            actions.append(dsl.transform(meta["side_tens_id"], meta["board_tens_id"]))
        leftovers = [
            sid
            for sid in meta["side_ids"]
            if sid not in {meta["side_write_id"], meta["side_tens_id"]}
        ]
        if leftovers:
            actions.append(dsl.fade_out(*leftovers))
        if consumed_carry is not None:
            actions.append(dsl.fade_out(consumed_carry))
        actions.append(dsl.wait(0.12))
        prev_carry_id = meta["board_carry_id"]

    if places and sum_dot is not None:
        place_match = _first_matching_title_text(steps, "decimal") or _first_matching_step_text(
            steps, "decimal"
        )
        place_step = place_match[1] if place_match is not None else "Place the decimal point."
        current_caption = _maybe_set_caption(actions, current_caption, place_step)
        actions.append(dsl.fade_in(sum_dot))
        highlight = [d for d in (*addend_dot_ids, sum_dot) if d is not None]
        actions.append(dsl.indicate(*highlight))
        actions.append(dsl.wait(0.3))

    write_ids_rtl = [m["board_write_id"] for m in side_meta]
    lead_ids = [oid for oid in (o["id"] for o in objects) if oid.startswith("sum_lead_")]
    sum_ids_ltr = [*lead_ids, *reversed(write_ids_rtl)]
    trimmed = _trimmed_zero_ids(data["sum_with_decimal"], data["sum"], sum_ids_ltr)
    final_targets = [oid for oid in sum_ids_ltr if oid not in trimmed]
    if sum_dot is not None:
        final_targets.append(sum_dot)
    current_caption = _maybe_set_caption(
        actions,
        current_caption,
        _caption(captions, len(captions) - 1, "This is the final sum."),
    )
    if trimmed:
        actions.append(dsl.fade_out(*trimmed))
    actions.append(dsl.indicate(*final_targets))
    actions.append(dsl.wait(0.45))

    scene = dsl.scene(
        "paper_addition",
        caption=opening,
        objects=objects,
        actions=actions,
        pin=False,
        separate_labels=False,
    )
    return dsl.script(
        plan["problem"],
        plan["answer"],
        [s["title"] for s in steps],
        [scene],
    )


def compile_long_subtraction(plan: dict[str, Any]) -> dict[str, Any]:
    steps = plan["steps"]
    data = analyze_long_subtraction(str(plan["data"]["minuend"]), str(plan["data"]["subtrahend"]))
    captions = _captions(steps)
    opening = _caption(captions, 0, "Set up the subtraction.")

    total_cols = int(data["columns"])
    x_of = _mul_x_fn(total_cols)
    places = int(data["decimal_places"])
    start = int(data["start"])

    borrow_y = 1.85
    top_y = 1.25
    bottom_y = 0.62
    line_y = bottom_y - DIGIT_HALF_H - 0.14
    diff_y = line_y - DIGIT_HALF_H - 0.22

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    top_visible, top_lead = _visible_padded_span(data["minuend_digits"], places)
    bottom_visible, bottom_lead = _visible_padded_span(data["subtrahend_digits"], places)
    top_objs, top_ids = _row_digit_objects_explicit(
        "minuend",
        top_visible,
        start + top_lead,
        x_of,
        top_y,
    )
    bottom_objs, bottom_ids = _row_digit_objects_explicit(
        "subtrahend",
        bottom_visible,
        start + bottom_lead,
        x_of,
        bottom_y,
    )
    objects.extend(top_objs)
    objects.extend(bottom_objs)
    top_map = {start + top_lead + i: oid for i, oid in enumerate(top_ids)}
    bottom_map = {start + bottom_lead + i: oid for i, oid in enumerate(bottom_ids)}
    setup_ids = [*top_ids, *bottom_ids]

    top_dot: str | None = None
    bottom_dot: str | None = None
    if places:
        top_dot = "minuend_dot"
        bottom_dot = "subtrahend_dot"
        dot_x = x_of(start + len(data["minuend_digits"]) - places - 0.5)
        objects.append(_math_obj(top_dot, ".", dot_x, top_y))
        objects.append(_math_obj(bottom_dot, ".", dot_x, bottom_y))
        setup_ids.extend([top_dot, bottom_dot])

    op_x = x_of(float(start) - 0.85)
    objects.append(_math_obj("sub_sign", "-", op_x, bottom_y))
    left_bar_x = min(op_x - 0.15, x_of(0) - 0.2)
    right_bar_x = x_of(total_cols - 1) + 0.28
    objects.append(_line_obj("sub_line", left_bar_x, line_y, right_bar_x, line_y, stroke_width=3.0))
    setup_ids.extend(["sub_sign", "sub_line"])

    side_meta: list[dict[str, Any]] = []
    for step_idx, step in enumerate(data["steps"]):
        write_id = f"diff_{step_idx}"
        objects.append(_math_obj(write_id, step["write_digit"], x_of(step["write_col"]), diff_y))

        borrow_id: str | None = None
        borrow_col = step.get("borrow_mark_col")
        if borrow_col is not None:
            borrow_id = f"borrow_{step_idx}"
            objects.append(
                _math_obj(
                    borrow_id,
                    "1",
                    x_of(borrow_col),
                    borrow_y,
                    font_size=SMALL_FONT,
                    color="yellow",
                )
            )

        lhs_id = f"side_sub_{step_idx}_lhs"
        eq_id = f"side_sub_{step_idx}_eq"
        side_write_id = f"side_sub_{step_idx}_write"
        objects.append(_math_obj(lhs_id, step["lhs_tex"], SIDE_X, SIDE_Y, font_size=30))
        objects.append(
            {
                "id": eq_id,
                "type": "math",
                "tex": "=",
                "next_to": lhs_id,
                "direction": "right",
                "font_size": 30,
                "color": "white",
            }
        )
        objects.append(
            {
                "id": side_write_id,
                "type": "math",
                "tex": step["write_digit"],
                "next_to": eq_id,
                "direction": "right",
                "font_size": 30,
                "color": "white",
            }
        )
        digit_index = len(data["minuend_digits"]) - 1 - step_idx
        col = start + digit_index
        top_id = top_map.get(col)
        bottom_id = bottom_map.get(col)
        pair_ids = [oid for oid in (top_id, bottom_id) if oid is not None]
        side_meta.append(
            {
                "pair_ids": pair_ids,
                "side_ids": [lhs_id, eq_id, side_write_id],
                "side_write_id": side_write_id,
                "board_write_id": write_id,
                "board_borrow_id": borrow_id,
                "incoming_borrow": int(step.get("incoming_borrow") or 0),
            }
        )

    diff_dot: str | None = None
    if places:
        diff_dot = "diff_dot"
        objects.append(
            _math_obj(
                diff_dot,
                ".",
                x_of(start + len(data["minuend_digits"]) - places - 0.5),
                diff_y,
            )
        )

    actions.append(dsl.fade_in(*setup_ids))
    actions.append(dsl.wait(read_wait(opening)))
    current_caption = opening

    column_steps = _matching_step_texts(steps, "column") or _matching_step_texts(
        steps, "borrow"
    ) or _matching_step_texts(steps, "subtract")

    prev_borrow_id: str | None = None
    for step_idx, meta in enumerate(side_meta):
        current_caption = _maybe_set_caption(
            actions,
            current_caption,
            _caption_from_matches(column_steps, step_idx, "Subtract the next column."),
        )
        pair = list(meta["pair_ids"])
        consumed_borrow: str | None = None
        if meta["incoming_borrow"] and prev_borrow_id is not None:
            pair.append(prev_borrow_id)
            consumed_borrow = prev_borrow_id
        if pair:
            actions.append(dsl.indicate(*pair))
        actions.append(dsl.fade_in(*meta["side_ids"]))
        actions.append(dsl.wait(0.35))
        actions.append(dsl.transform(meta["side_write_id"], meta["board_write_id"]))
        if meta["board_borrow_id"] is not None:
            # Borrow mark appears above the left neighbor as we create it.
            actions.append(dsl.fade_in(meta["board_borrow_id"]))
        leftovers = [sid for sid in meta["side_ids"] if sid != meta["side_write_id"]]
        if leftovers:
            actions.append(dsl.fade_out(*leftovers))
        if consumed_borrow is not None:
            actions.append(dsl.fade_out(consumed_borrow))
        actions.append(dsl.wait(0.12))
        prev_borrow_id = meta["board_borrow_id"]

    if places and diff_dot is not None:
        place_match = _first_matching_title_text(steps, "decimal") or _first_matching_step_text(
            steps, "decimal"
        )
        place_step = place_match[1] if place_match is not None else "Place the decimal point."
        current_caption = _maybe_set_caption(actions, current_caption, place_step)
        actions.append(dsl.fade_in(diff_dot))
        highlight = [d for d in (top_dot, bottom_dot, diff_dot) if d is not None]
        actions.append(dsl.indicate(*highlight))
        actions.append(dsl.wait(0.3))

    write_ids_rtl = [m["board_write_id"] for m in side_meta]
    write_ids_ltr = list(reversed(write_ids_rtl))
    trimmed = _trimmed_zero_ids(data["difference_with_decimal"], data["difference"], write_ids_ltr)
    leading_trim = _leading_zero_ids(write_ids_rtl, places, data["difference"])
    fade_ids = list(dict.fromkeys([*trimmed, *leading_trim]))
    final_targets = [wid for wid in write_ids_ltr if wid not in fade_ids]
    if diff_dot is not None:
        final_targets.append(diff_dot)
    current_caption = _maybe_set_caption(
        actions,
        current_caption,
        _caption(captions, len(captions) - 1, "This is the final difference."),
    )
    if fade_ids:
        actions.append(dsl.fade_out(*fade_ids))
    if final_targets:
        actions.append(dsl.indicate(*final_targets))
    actions.append(dsl.wait(0.45))

    scene = dsl.scene(
        "paper_subtraction",
        caption=opening,
        objects=objects,
        actions=actions,
        pin=False,
        separate_labels=False,
    )
    return dsl.script(
        plan["problem"],
        plan["answer"],
        [s["title"] for s in steps],
        [scene],
    )


def compile_long_division(plan: dict[str, Any]) -> dict[str, Any]:
    steps = plan["steps"]
    data = analyze_long_division(
        str(plan["data"]["dividend"]),
        str(plan["data"]["divisor"]),
    )
    captions = _captions(steps)
    opening = _caption(captions, 0, "Set up the long division.")

    dividend_cols = len(data["dividend_digits"]) + int(data["extra_decimal_digits"])
    x_of = _div_x_fn()

    # Compact textbook rhythm: quotient just above the bar, work stacked tightly.
    dividend_y = 1.15
    bar_y = dividend_y + 0.34
    quotient_y = bar_y + 0.38
    wall_x = DIV_BASE_X - 0.42
    divisor_right_x = wall_x - 0.42

    stage_gap = 0.92
    product_offset = 0.55
    line_gap = 0.26
    rem_gap = 0.26

    objects: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    divisor_objs, divisor_ids = _right_edge_digit_objects(
        "divisor",
        data["divisor_digits"],
        divisor_right_x,
        dividend_y,
    )
    objects.extend(divisor_objs)

    # Classic long-division house: top vinculum + short left wall ending under the dividend.
    bar_right = x_of(max(dividend_cols - 1, 0)) + 0.34
    wall_top = bar_y
    wall_bottom = dividend_y - DIGIT_HALF_H - 0.08
    objects.append(_line_obj("div_bar_h", wall_x, bar_y, bar_right, bar_y, stroke_width=3.5))
    objects.append(_line_obj("div_bar_v", wall_x, wall_top, wall_x, wall_bottom, stroke_width=3.5))

    dividend_objs, dividend_ids = _row_digit_objects_explicit("dividend", data["dividend_digits"], 0, x_of, dividend_y)
    objects.extend(dividend_objs)

    dividend_dot: str | None = None
    if data["extra_decimal_digits"]:
        dividend_dot = "dividend_dot"
        objects.append(_math_obj(dividend_dot, ".", x_of(len(data["dividend_digits"]) - 0.5), dividend_y))

    dividend_zero_ids: list[str] = []
    for idx in range(int(data["extra_decimal_digits"])):
        zero_id = f"dividend_zero_{idx}"
        dividend_zero_ids.append(zero_id)
        objects.append(_math_obj(zero_id, "0", x_of(len(data["dividend_digits"]) + idx), dividend_y))

    quotient_ids: list[str] = []
    quotient_id_by_col: dict[int, str] = {}
    for idx, (digit, col) in enumerate(zip(data["quotient_digits"], data["quotient_columns"], strict=False)):
        oid = f"quot_{idx}"
        quotient_ids.append(oid)
        quotient_id_by_col[int(col)] = oid
        objects.append(_math_obj(oid, digit, x_of(col), quotient_y, font_size=QUOT_FONT, color="blue"))

    quotient_dot: str | None = None
    if data["extra_decimal_digits"]:
        quotient_dot = "quot_dot"
        objects.append(
            _math_obj(
                quotient_dot,
                ".",
                x_of(len(data["dividend_digits"]) - 0.5),
                quotient_y,
                font_size=QUOT_FONT,
                color="blue",
            )
        )

    stage_product_ids: list[list[str]] = []
    stage_remainder_ids: list[list[str]] = []
    stage_line_ids: list[str] = []
    stage_minus_ids: list[str] = []
    stage_bring_digit_ids: list[str | None] = []
    stage_bring_arrow_ids: list[str | None] = []
    stage_bring_source_ids: list[str | None] = []
    stage_quot_ids: list[str] = []
    stage_header_ids: list[list[str]] = []

    for idx, stage in enumerate(data["stages"]):
        product_y = dividend_y - product_offset - idx * stage_gap
        line_y = product_y - line_gap
        remainder_y = line_y - rem_gap

        stage_quot_ids.append(quotient_id_by_col[int(stage["q_column"])])

        product_objs, product_ids = _row_digit_objects_explicit(
            f"stage_{idx}_prod",
            stage["product_text"],
            int(stage["product_start"]),
            x_of,
            product_y,
        )
        objects.extend(product_objs)
        stage_product_ids.append(product_ids)

        minus_id = f"stage_{idx}_minus"
        stage_minus_ids.append(minus_id)
        objects.append(
            _math_obj(
                minus_id,
                "-",
                x_of(stage["product_start"]) - 0.36,
                product_y,
                color="red",
            )
        )

        line_id = f"stage_{idx}_line"
        stage_line_ids.append(line_id)
        objects.append(
            _line_obj(
                line_id,
                x_of(stage["current_start"]) - 0.16,
                line_y,
                x_of(stage["current_end"]) + 0.16,
                line_y,
                stroke_width=2.5,
            )
        )

        remainder_objs, remainder_ids = _row_digit_objects_explicit(
            f"stage_{idx}_rem",
            stage["remainder_text"],
            int(stage["remainder_start"]),
            x_of,
            remainder_y,
        )
        objects.extend(remainder_objs)
        stage_remainder_ids.append(remainder_ids)

        header_ids: list[str] = []
        if stage.get("show_decimal"):
            if quotient_dot is not None:
                header_ids.append(quotient_dot)
            if dividend_dot is not None:
                header_ids.append(dividend_dot)
            zero_index = int(stage["q_column"]) - len(data["dividend_digits"])
            if 0 <= zero_index < len(dividend_zero_ids):
                header_ids.append(dividend_zero_ids[zero_index])
        stage_header_ids.append(header_ids)

        bring_digit_id: str | None = None
        bring_arrow_id: str | None = None
        bring_source_id: str | None = None
        bring_down = stage.get("bring_down")
        bring_col = stage.get("bring_down_column")
        if bring_down is not None and bring_col is not None:
            bring_digit_id = f"stage_{idx}_bring_digit"
            bring_arrow_id = f"stage_{idx}_bring_arrow"
            objects.append(_math_obj(bring_digit_id, str(bring_down), x_of(bring_col), remainder_y))
            if int(bring_col) < len(data["dividend_digits"]):
                bring_source_id = dividend_ids[int(bring_col)]
            elif dividend_zero_ids:
                zero_i = int(bring_col) - len(data["dividend_digits"])
                if 0 <= zero_i < len(dividend_zero_ids):
                    bring_source_id = dividend_zero_ids[zero_i]
            # Solid arrow from the first-row source digit down to the working row.
            objects.append(
                _arrow_obj(
                    bring_arrow_id,
                    x_of(bring_col),
                    dividend_y - DIGIT_HALF_H - 0.02,
                    x_of(bring_col),
                    remainder_y + DIGIT_HALF_H + 0.06,
                    color="gray",
                    stroke_width=2.0,
                    tip_length=0.14,
                )
            )
        stage_bring_digit_ids.append(bring_digit_id)
        stage_bring_arrow_ids.append(bring_arrow_id)
        stage_bring_source_ids.append(bring_source_id)

    setup_ids = [*divisor_ids, "div_bar_h", "div_bar_v", *dividend_ids]
    actions.append(dsl.fade_in(*setup_ids))
    actions.append(dsl.wait(read_wait(opening)))
    current_caption = opening

    stage_caps = captions[1:-1] if len(captions) > 2 else captions[1:]
    active_bring_arrows: list[str] = []
    for idx, stage in enumerate(data["stages"]):
        current_caption = _maybe_set_caption(
            actions,
            current_caption,
            _caption(stage_caps, idx, f"Division step {idx + 1}."),
        )
        if stage_header_ids[idx]:
            actions.append(dsl.fade_in(*stage_header_ids[idx]))
        actions.append(dsl.fade_in(stage_quot_ids[idx]))
        actions.append(dsl.indicate(stage_quot_ids[idx]))
        actions.append(dsl.fade_in(stage_minus_ids[idx], *stage_product_ids[idx]))
        actions.append(dsl.wait(0.15))
        actions.append(dsl.fade_in(stage_line_ids[idx]))
        actions.append(dsl.fade_in(*stage_remainder_ids[idx]))
        if stage_bring_arrow_ids[idx] is not None and stage_bring_digit_ids[idx] is not None:
            if stage_bring_source_ids[idx] is not None:
                actions.append(dsl.indicate(stage_bring_source_ids[idx]))
            actions.append(dsl.fade_in(stage_bring_arrow_ids[idx], stage_bring_digit_ids[idx]))
            active_bring_arrows.append(stage_bring_arrow_ids[idx])
            # Keep only the latest bring-down arrow on screen.
            if len(active_bring_arrows) > 1:
                old = active_bring_arrows.pop(0)
                actions.append({"op": "fade_out", "targets": [old]})
        actions.append(dsl.wait(0.28))

    if active_bring_arrows:
        actions.append({"op": "fade_out", "targets": list(active_bring_arrows)})

    final_caption = captions[-1] if len(captions) > len(stage_caps) + 1 else "Read the final quotient."
    current_caption = _maybe_set_caption(actions, current_caption, final_caption)
    final_ids = list(quotient_ids)
    if quotient_dot is not None:
        final_ids.append(quotient_dot)
    actions.append(dsl.indicate(*final_ids))
    actions.append(dsl.wait(0.45))

    scene = dsl.scene(
        "paper_division",
        caption=opening,
        objects=objects,
        actions=actions,
        pin=False,
        separate_labels=False,
    )
    return dsl.script(
        plan["problem"],
        plan["answer"],
        [s["title"] for s in steps],
        [scene],
    )


def _captions(steps: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for step in steps:
        text = step_narration(step) or str(step.get("title") or "").strip()
        if text:
            out.append(text)
    return out


def _caption(captions: list[str], index: int, default: str) -> str:
    if 0 <= index < len(captions) and captions[index]:
        return captions[index]
    return default


def _maybe_set_caption(actions: list[dict[str, Any]], current: str, new: str) -> str:
    if not new or new == current:
        return current
    actions.append(dsl.set_caption(new))
    actions.append(dsl.wait(read_wait(new)))
    return new


def _matching_step_texts(steps: list[dict[str, Any]], *needles: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    lowered_needles = tuple(n.lower() for n in needles)
    for idx, step in enumerate(steps):
        text = step_narration(step) or str(step.get("title") or "").strip()
        if not text:
            continue
        blob = f"{step.get('title', '')} {step.get('explanation', '')}".lower()
        if all(needle in blob for needle in lowered_needles):
            out.append((idx, text))
    return out


def _first_matching_step_text(steps: list[dict[str, Any]], *needles: str) -> tuple[int, str] | None:
    matches = _matching_step_texts(steps, *needles)
    return matches[0] if matches else None


def _first_matching_title_text(steps: list[dict[str, Any]], *needles: str) -> tuple[int, str] | None:
    lowered_needles = tuple(n.lower() for n in needles)
    for idx, step in enumerate(steps):
        text = step_narration(step) or str(step.get("title") or "").strip()
        if not text:
            continue
        title = str(step.get("title") or "").lower()
        if all(needle in title for needle in lowered_needles):
            return idx, text
    return None


def _caption_from_matches(matches: list[tuple[int, str]], index: int, default: str) -> str:
    if 0 <= index < len(matches):
        return matches[index][1]
    return default


def _trimmed_zero_ids(full_value: str, trimmed_value: str, digit_ids: list[str]) -> list[str]:
    if "." not in full_value:
        return []
    full_frac = full_value.split(".", 1)[1]
    trimmed_frac = trimmed_value.split(".", 1)[1] if "." in trimmed_value else ""
    count = max(0, len(full_frac) - len(trimmed_frac))
    return digit_ids[-count:] if count else []


def _leading_zero_ids(write_ids_rtl: list[str], decimal_places: int, answer: str) -> list[str]:
    """Fade leading whole-number zeros written during subtraction."""
    whole_written = max(0, len(write_ids_rtl) - decimal_places)
    whole_answer = answer.split(".", 1)[0] if answer else "0"
    whole_answer_len = max(1, len(whole_answer))
    extra = max(0, whole_written - whole_answer_len)
    return write_ids_rtl[-extra:] if extra else []


def _visible_padded_span(digits: str, decimal_places: int) -> tuple[str, int]:
    """Drop leading whole-number zeros from a padded digit string; keep column offset."""
    whole_len = len(digits) - decimal_places
    if whole_len <= 0:
        return digits, 0
    lead = 0
    for ch in digits[:whole_len]:
        if ch == "0":
            lead += 1
        else:
            break
    if lead == whole_len:
        lead = max(0, whole_len - 1)
    return digits[lead:], lead


def _mul_x_fn(total_cols: int) -> Callable[[float], float]:
    left_x = RIGHT_EDGE - (total_cols - 1) * DIGIT_W
    return lambda col: left_x + float(col) * DIGIT_W


def _div_x_fn() -> Callable[[float], float]:
    return lambda col: DIV_BASE_X + float(col) * DIGIT_W


def _number_objects_explicit(
    prefix: str,
    value: str,
    start_col: int,
    x_of: Callable[[float], float],
    y: float,
) -> tuple[list[dict[str, Any]], list[str], str | None]:
    digits, decimal_places = split_decimal_parts(value)
    objs, ids = _row_digit_objects_explicit(prefix, digits, start_col, x_of, y)
    dot_id: str | None = None
    if decimal_places:
        dot_id = f"{prefix}_dot"
        objs.append(_math_obj(dot_id, ".", x_of(start_col + len(digits) - decimal_places - 0.5), y))
    return objs, ids, dot_id


def _row_digit_objects_explicit(
    prefix: str,
    digits: str,
    start_col: int,
    x_of: Callable[[float], float],
    y: float,
) -> tuple[list[dict[str, Any]], list[str]]:
    objs: list[dict[str, Any]] = []
    ids: list[str] = []
    for idx, digit in enumerate(digits):
        oid = f"{prefix}_{idx}"
        ids.append(oid)
        objs.append(_math_obj(oid, digit, x_of(start_col + idx), y))
    return objs, ids


def _right_edge_digit_objects(prefix: str, digits: str, right_x: float, y: float) -> tuple[list[dict[str, Any]], list[str]]:
    objs: list[dict[str, Any]] = []
    ids: list[str] = []
    left_x = right_x - (len(digits) - 1) * DIGIT_W
    for idx, digit in enumerate(digits):
        oid = f"{prefix}_{idx}"
        ids.append(oid)
        objs.append(_math_obj(oid, digit, left_x + idx * DIGIT_W, y))
    return objs, ids


def _math_obj(
    oid: str,
    tex: str,
    x: float,
    y: float,
    *,
    font_size: int = MAIN_FONT,
    color: str = "white",
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "math",
        "tex": tex,
        "at": [x, y],
        "font_size": font_size,
        "color": color,
    }


def _line_obj(
    oid: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    color: str = "white",
    dashed: bool = False,
    stroke_width: float = 2.0,
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "line",
        "start": [x0, y0],
        "end": [x1, y1],
        "color": color,
        "dashed": dashed,
        "stroke_width": stroke_width,
    }


def _arrow_obj(
    oid: str,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    color: str = "white",
    stroke_width: float = 2.0,
    tip_length: float = 0.18,
) -> dict[str, Any]:
    return {
        "id": oid,
        "type": "arrow",
        "start": [x0, y0],
        "end": [x1, y1],
        "color": color,
        "stroke_width": stroke_width,
        "tip_length": tip_length,
    }
