"""Validate teacher plans from the LLM."""

from __future__ import annotations

from typing import Any

from mathanim.arithmetic import normalize_numeric_literal
from mathanim.plan import PLAN_VERSION, VISUAL_TOOLS


class PlanValidationError(ValueError):
    pass


def validate_plan(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise PlanValidationError("Plan root must be a JSON object")
    for key in ("problem", "answer", "steps", "visuals"):
        if key not in data:
            raise PlanValidationError(f"Plan missing key: {key}")

    version = data.get("version", PLAN_VERSION)
    if version != PLAN_VERSION:
        raise PlanValidationError(f"Unsupported plan version {version}")

    problem = _string_field(data, "problem", message="'problem' must be a non-empty string")
    answer = _string_field(data, "answer", message="'answer' must be a non-empty string")
    steps = _validate_steps(data["steps"])

    visuals_raw = data.get("visuals")
    if not isinstance(visuals_raw, list):
        raise PlanValidationError("'visuals' must be a list")
    if not visuals_raw:
        raise PlanValidationError("'visuals' must be a non-empty list")
    visuals = [_validate_visual_call(i, item) for i, item in enumerate(visuals_raw)]

    if any(v["tool"] == "equation_board" for v in visuals) and not _steps_have_math(steps):
        raise PlanValidationError("equation_board requires at least one non-empty math line in steps")

    return {
        "version": PLAN_VERSION,
        "problem": problem,
        "answer": answer,
        "steps": steps,
        "visuals": visuals,
    }


def _validate_steps(steps_raw: Any) -> list[dict[str, Any]]:
    if not isinstance(steps_raw, list) or not steps_raw:
        raise PlanValidationError("'steps' must be a non-empty list")

    steps: list[dict[str, Any]] = []
    for i, step in enumerate(steps_raw):
        if not isinstance(step, dict):
            raise PlanValidationError(f"steps[{i}] must be an object")
        title = step.get("title")
        explanation = step.get("explanation", "")
        math = step.get("math", [])
        if not isinstance(title, str) or not title.strip():
            raise PlanValidationError(f"steps[{i}].title must be a non-empty string")
        if not isinstance(explanation, str):
            raise PlanValidationError(f"steps[{i}].explanation must be a string")
        if not isinstance(math, list) or not all(isinstance(m, str) for m in math):
            raise PlanValidationError(f"steps[{i}].math must be a list of strings")
        steps.append(
            {
                "title": title.strip(),
                "explanation": explanation.strip(),
                "math": [m.strip() for m in math if m.strip()],
            }
        )
    return steps


def _validate_visual_call(index: int, raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise PlanValidationError(f"visuals[{index}] must be an object")
    tool = raw.get("tool")
    if not isinstance(tool, str) or tool not in VISUAL_TOOLS:
        raise PlanValidationError(
            f"visuals[{index}].tool must be one of {sorted(VISUAL_TOOLS)}"
        )

    if tool == "equation_board":
        return {"tool": tool}

    if tool == "state_claim":
        claim = _require_string(raw, "claim", f"visuals[{index}].claim")
        given = raw.get("given") or []
        if not isinstance(given, list) or not all(isinstance(g, str) for g in given):
            raise PlanValidationError(f"visuals[{index}].given must be a list of strings")
        return {"tool": tool, "claim": claim, "given": [g.strip() for g in given if g.strip()]}

    if tool == "show_qed":
        return {"tool": tool, "tex": _require_string(raw, "tex", f"visuals[{index}].tex")}

    if tool == "plot_2d":
        return {
            "tool": tool,
            "equation": str(raw.get("equation") or "").strip(),
            "coefficients": _validate_coefficients(raw, index=index),
            "roots": _validate_number_list(raw.get("roots"), f"visuals[{index}].roots"),
        }

    if tool == "show_region_rectangle":
        out = _validate_rect_visual(raw, index=index)
        out["tool"] = tool
        out["value"] = _number_field(raw, "value", f"visuals[{index}].value")
        return out

    if tool == "plot_surface_3d":
        out = _validate_rect_visual(raw, index=index)
        out["tool"] = tool
        return out

    if tool == "paper_long_multiply":
        return {
            "tool": tool,
            "multiplicand": _numeric_field(raw, "multiplicand", allow_decimal=True),
            "multiplier": _numeric_field(raw, "multiplier", allow_decimal=True),
            "product": _numeric_field(raw, "product", allow_decimal=True),
        }

    if tool == "paper_long_divide":
        return {
            "tool": tool,
            "dividend": _numeric_field(raw, "dividend", allow_decimal=False),
            "divisor": _numeric_field(raw, "divisor", allow_decimal=False),
            "quotient": _numeric_field(raw, "quotient", allow_decimal=True),
        }

    if tool == "paper_long_add":
        addends = raw.get("addends")
        if not isinstance(addends, list) or len(addends) < 2:
            raise PlanValidationError(f"visuals[{index}].addends must be a list of at least 2 strings")
        out_addends: list[str] = []
        for i, value in enumerate(addends):
            if not isinstance(value, str) or not value.strip():
                raise PlanValidationError(
                    f"visuals[{index}].addends[{i}] must be a non-empty string"
                )
            try:
                out_addends.append(
                    normalize_numeric_literal(
                        value,
                        allow_decimal=True,
                        trim_trailing_zeros=False,
                    )
                )
            except ValueError as exc:
                raise PlanValidationError(str(exc)) from exc
        return {
            "tool": tool,
            "addends": out_addends,
            "sum": _numeric_field(raw, "sum", allow_decimal=True),
        }

    if tool == "paper_long_subtract":
        return {
            "tool": tool,
            "minuend": _numeric_field(raw, "minuend", allow_decimal=True),
            "subtrahend": _numeric_field(raw, "subtrahend", allow_decimal=True),
            "difference": _numeric_field(raw, "difference", allow_decimal=True),
        }

    if tool == "show_lagrangian":
        return {
            "tool": tool,
            "interaction": _require_string(raw, "interaction", f"visuals[{index}].interaction"),
            "condition": str(raw.get("condition") or "").strip(),
            "caption": str(raw.get("caption") or "").strip(),
        }

    if tool == "feynman_1to2":
        daughters = raw.get("daughters")
        if not isinstance(daughters, list) or not daughters:
            raise PlanValidationError(f"visuals[{index}].daughters must be a non-empty list")
        if not all(isinstance(d, str) and d.strip() for d in daughters):
            raise PlanValidationError(f"visuals[{index}].daughters must be strings")
        return {
            "tool": tool,
            "parent": _require_string(raw, "parent", f"visuals[{index}].parent"),
            "daughters": [d.strip() for d in daughters],
            "coupling": _require_string(raw, "coupling", f"visuals[{index}].coupling"),
        }

    if tool == "feynman_loop":
        from mathanim.render_engine.feynman import PROCESSES

        process = str(raw.get("process") or "").strip()
        allowed = PROCESSES - {"1_to_2"}
        if process not in allowed:
            raise PlanValidationError(
                f"visuals[{index}].process must be one of {sorted(allowed)}"
            )
        labels = raw.get("labels") or {}
        if not isinstance(labels, dict):
            raise PlanValidationError(f"visuals[{index}].labels must be an object")
        return {
            "tool": tool,
            "process": process,
            "labels": {str(k): str(v).strip() for k, v in labels.items() if str(v).strip()},
            "caption": str(raw.get("caption") or "").strip(),
            "scale": float(raw.get("scale", 1.0)),
        }

    if tool == "rg_flow_2d":
        from mathanim.render_engine.validate import _safe_expr

        beta_x = _require_string(raw, "beta_x", f"visuals[{index}].beta_x")
        beta_y = _require_string(raw, "beta_y", f"visuals[{index}].beta_y")
        try:
            _safe_expr(beta_x, {"x", "y"})
            _safe_expr(beta_y, {"x", "y"})
        except Exception as exc:
            raise PlanValidationError(f"visuals[{index}] bad beta expression: {exc}") from exc
        x_range = raw.get("x_range") or [0, 3, 0.5]
        y_range = raw.get("y_range") or [0, 2, 0.5]
        if not isinstance(x_range, list) or len(x_range) < 2:
            raise PlanValidationError(f"visuals[{index}].x_range must be [xmin, xmax, step?]")
        if not isinstance(y_range, list) or len(y_range) < 2:
            raise PlanValidationError(f"visuals[{index}].y_range must be [ymin, ymax, step?]")
        grid = raw.get("grid") or [7, 6]
        if not isinstance(grid, list) or len(grid) < 2:
            raise PlanValidationError(f"visuals[{index}].grid must be [nx, ny]")
        return {
            "tool": tool,
            "beta_x": beta_x,
            "beta_y": beta_y,
            "x_range": [float(x_range[0]), float(x_range[1]), float(x_range[2] if len(x_range) > 2 else 0.5)],
            "y_range": [float(y_range[0]), float(y_range[1]), float(y_range[2] if len(y_range) > 2 else 0.5)],
            "x_label": str(raw.get("x_label") or r"\lambda").strip() or r"\lambda",
            "y_label": str(raw.get("y_label") or "g").strip() or "g",
            "grid": [int(grid[0]), int(grid[1])],
            "caption": str(raw.get("caption") or "RG flow").strip() or "RG flow",
        }

    if tool == "show_answer":
        return {
            "tool": tool,
            "tex": _require_string(raw, "tex", f"visuals[{index}].tex"),
            "caption": str(raw.get("caption") or "Answer").strip() or "Answer",
        }

    raise PlanValidationError(f"Unsupported visual tool '{tool}'")


def _validate_coefficients(data: dict[str, Any], *, index: int) -> dict[str, float]:
    coef = data.get("coefficients") or {}
    if not isinstance(coef, dict):
        raise PlanValidationError(f"visuals[{index}].coefficients must be an object")
    for key in ("a", "b", "c"):
        if key not in coef or not isinstance(coef[key], (int, float)):
            raise PlanValidationError(f"visuals[{index}].coefficients.{key} must be a number")
    return {
        "a": float(coef["a"]),
        "b": float(coef["b"]),
        "c": float(coef["c"]),
    }


def _validate_number_list(value: Any, label: str) -> list[float]:
    if not isinstance(value, list) or not value:
        raise PlanValidationError(f"{label} must be a non-empty list")
    if not all(isinstance(item, (int, float)) for item in value):
        raise PlanValidationError(f"{label} must contain only numbers")
    return [float(item) for item in value]


def _validate_rect_visual(data: dict[str, Any], *, index: int) -> dict[str, Any]:
    integrand = _require_string(data, "integrand", f"visuals[{index}].integrand")
    order = str(data.get("order") or "dy_dx")
    if order not in {"dy_dx", "dx_dy"}:
        raise PlanValidationError(f"visuals[{index}].order must be dy_dx or dx_dy")
    return {
        "integrand": integrand,
        "x_min": _number_field(data, "x_min", f"visuals[{index}].x_min"),
        "x_max": _number_field(data, "x_max", f"visuals[{index}].x_max"),
        "y_min": _number_field(data, "y_min", f"visuals[{index}].y_min"),
        "y_max": _number_field(data, "y_max", f"visuals[{index}].y_max"),
        "order": order,
    }


def _steps_have_math(steps: list[dict[str, Any]]) -> bool:
    return any(step["math"] for step in steps)


def _string_field(data: dict[str, Any], key: str, *, message: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(message)
    return value.strip()


def _require_string(data: dict[str, Any], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(f"{label} must be a non-empty string")
    return value.strip()


def _number_field(data: dict[str, Any], key: str, label: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise PlanValidationError(f"{label} must be a number")
    return float(value)


def _numeric_field(data: dict[str, Any], key: str, *, allow_decimal: bool) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PlanValidationError(f"{key} must be a non-empty string")
    try:
        return normalize_numeric_literal(
            value,
            allow_decimal=allow_decimal,
            trim_trailing_zeros=False,
        )
    except ValueError as exc:
        raise PlanValidationError(str(exc)) from exc
