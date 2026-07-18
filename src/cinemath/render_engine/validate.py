"""Validate internal animation scripts emitted by templates."""

from __future__ import annotations

import ast
import operator
from typing import Any

from cinemath.render_engine import COLORS

OBJECT_TYPES = frozenset(
    {
        "text",
        "math",
        "prose",
        "axes",
        "plot",
        "dot",
        "line",
        "arrow",
        "number_line",
        "axes3d",
        "surface",
        "plane",
        "polygon",
        "feynman",
        "flow_field",
        "statement",
    }
)
ACTION_OPS = frozenset(
    {
        "create",
        "write",
        "fade_in",
        "fade_out",
        "transform",
        "indicate",
        "wait",
        "clear",
        "move_camera",
        "derive",
        "fork",
        "set_caption",
    }
)
SLOTS = frozenset({"title", "center", "upper", "lower", "left", "right", "ul", "ur", "ll", "lr"})
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCS = {"sin", "cos", "tan", "exp", "log", "sqrt", "abs"}


class AnimValidationError(ValueError):
    pass


def validate_animation(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise AnimValidationError("animation root must be object")
    for key in ("problem", "answer", "steps", "scenes"):
        if key not in data:
            raise AnimValidationError(f"animation missing {key}")
    scenes = [_scene(s, i) for i, s in enumerate(data["scenes"])]
    if not scenes:
        raise AnimValidationError("animation needs scenes")
    return {
        "version": 1,
        "problem": str(data["problem"]).strip(),
        "answer": str(data["answer"]).strip(),
        "steps": list(data["steps"]),
        "scenes": scenes,
    }


def _scene(scene: Any, index: int) -> dict[str, Any]:
    if not isinstance(scene, dict):
        raise AnimValidationError(f"scenes[{index}] invalid")
    sid = scene.get("id") or f"scene_{index+1}"
    mode = scene.get("mode", "2d")
    objects = [_object(o, sid, j) for j, o in enumerate(scene.get("objects") or [])]
    ids = {o["id"] for o in objects}
    if not objects:
        raise AnimValidationError(f"scene {sid} has no objects")
    for o in objects:
        if "axes" in o and o["axes"] not in ids:
            raise AnimValidationError(f"{sid}/{o['id']} bad axes ref")
        if o["type"] == "plot":
            _safe_expr(o["expr"], {"x"})
            if next(x for x in objects if x["id"] == o["axes"])["type"] != "axes":
                raise AnimValidationError(f"{sid}/{o['id']} plot needs axes")
        if o["type"] == "surface":
            _safe_expr(o["expr"], {"x", "y"})
            if next(x for x in objects if x["id"] == o["axes"])["type"] != "axes3d":
                raise AnimValidationError(f"{sid}/{o['id']} surface needs axes3d")
        if o["type"] == "polygon":
            if next(x for x in objects if x["id"] == o["axes"])["type"] != "axes":
                raise AnimValidationError(f"{sid}/{o['id']} polygon needs axes")
        if o["type"] == "plane":
            if next(x for x in objects if x["id"] == o["axes"])["type"] != "axes3d":
                raise AnimValidationError(f"{sid}/{o['id']} plane needs axes3d")
        if o["type"] == "flow_field":
            if next(x for x in objects if x["id"] == o["axes"])["type"] != "axes":
                raise AnimValidationError(f"{sid}/{o['id']} flow_field needs axes")
        if o["type"] == "dot" and "axes" in o:
            axes_type = next(x for x in objects if x["id"] == o["axes"])["type"]
            if axes_type not in {"axes", "axes3d"}:
                raise AnimValidationError(f"{sid}/{o['id']} dot needs axes or axes3d")
            if axes_type == "axes3d" and len(o["at"]) < 3:
                raise AnimValidationError(f"{sid}/{o['id']} 3d dot needs [x,y,z]")
    if any(o["type"] in {"axes3d", "surface", "plane"} for o in objects):
        mode = "3d"
    actions = [_action(a, sid, k, ids) for k, a in enumerate(scene.get("actions") or [])]
    if not actions:
        raise AnimValidationError(f"scene {sid} has no actions")
    out = {
        "id": sid,
        "mode": mode,
        "pin": bool(scene.get("pin", True)),
        "separate_labels": bool(scene.get("separate_labels", True)),
        "objects": objects,
        "actions": actions,
    }
    if scene.get("caption"):
        out["caption"] = str(scene["caption"]).strip()
    return out


def _object(obj: Any, sid: str, index: int) -> dict[str, Any]:
    if not isinstance(obj, dict) or obj.get("type") not in OBJECT_TYPES:
        raise AnimValidationError(f"{sid} objects[{index}] bad type")
    oid = str(obj["id"])
    otype = obj["type"]
    out: dict[str, Any] = {"id": oid, "type": otype}
    if "color" in obj:
        out["color"] = _color(obj["color"])
    if "font_size" in obj:
        out["font_size"] = float(obj["font_size"])
    if "at" in obj:
        out["at"] = _pos(obj["at"])
    if "next_to" in obj:
        out["next_to"] = str(obj["next_to"])
        out["direction"] = obj.get("direction", "down")
        if "buff" in obj:
            out["buff"] = float(obj["buff"])

    if otype == "text":
        out["content"] = str(obj["content"])
    elif otype == "math":
        out["tex"] = str(obj["tex"])
    elif otype == "axes":
        out["x_range"] = _range3(obj.get("x_range", [-4, 4, 1]))
        out["y_range"] = _range3(obj.get("y_range", [-3, 3, 1]))
        out["x_length"] = float(obj.get("x_length", 6))
        out["y_length"] = float(obj.get("y_length", 3.5))
    elif otype == "axes3d":
        out["x_range"] = _range3(obj.get("x_range", [-3, 3, 1]))
        out["y_range"] = _range3(obj.get("y_range", [-3, 3, 1]))
        out["z_range"] = _range3(obj.get("z_range", [-3, 3, 1]))
        out["x_length"] = float(obj.get("x_length", 5))
        out["y_length"] = float(obj.get("y_length", 5))
        out["z_length"] = float(obj.get("z_length", 3.5))
    elif otype == "plot":
        out["axes"] = str(obj["axes"])
        out["expr"] = str(obj["expr"]).strip()
        if "x_range" in obj:
            out["x_range"] = _range2(obj["x_range"])
        shade = obj.get("shade", "none")
        if isinstance(shade, bool):
            out["shade"] = "x_axis" if shade else "none"
        else:
            key = str(shade).strip().lower()
            if key in {"none", "off", "false"}:
                out["shade"] = "none"
            elif key in {"x_axis", "axis", "under", "true"}:
                out["shade"] = "x_axis"
            else:
                raise AnimValidationError(f"plot shade must be 'none' or 'x_axis', got {shade!r}")
        if "fill_opacity" in obj:
            out["fill_opacity"] = float(obj["fill_opacity"])
        if "stroke_width" in obj:
            out["stroke_width"] = float(obj["stroke_width"])
    elif otype == "surface":
        out["axes"] = str(obj["axes"])
        out["expr"] = str(obj["expr"]).strip()
        out["x_range"] = _range2(obj.get("x_range", [-2, 2]))
        out["y_range"] = _range2(obj.get("y_range", [-2, 2]))
        out["opacity"] = float(obj.get("opacity", 0.75))
        out["resolution"] = int(obj.get("resolution", 24))
    elif otype == "plane":
        out["axes"] = str(obj["axes"])
        for key in ("a", "b", "c", "d"):
            if key not in obj or not isinstance(obj[key], (int, float)):
                raise AnimValidationError(f"plane needs numeric {key}")
            out[key] = float(obj[key])
        out["opacity"] = float(obj.get("opacity", 0.35))
    elif otype == "polygon":
        out["axes"] = str(obj["axes"])
        pts = obj.get("points")
        if not isinstance(pts, list) or len(pts) < 3:
            raise AnimValidationError("polygon needs >= 3 points")
        out["points"] = [_point(p) for p in pts]
        out["opacity"] = float(obj.get("opacity", 0.25))
    elif otype == "dot":
        if "axes" in obj:
            out["axes"] = str(obj["axes"])
            out["at"] = _point(obj["at"])
        elif "number_line" in obj:
            out["number_line"] = str(obj["number_line"])
            out["value"] = float(obj["value"])
        else:
            out["at"] = _pos(obj.get("at", "center"))
    elif otype in {"line", "arrow"}:
        if "axes" in obj:
            out["axes"] = str(obj["axes"])
        out["start"] = _point(obj["start"])
        out["end"] = _point(obj["end"])
        if otype == "line":
            out["dashed"] = bool(obj.get("dashed", False))
        if "stroke_width" in obj:
            out["stroke_width"] = float(obj["stroke_width"])
        if otype == "arrow" and "tip_length" in obj:
            out["tip_length"] = float(obj["tip_length"])
    elif otype == "number_line":
        out["x_range"] = _range3(obj.get("x_range", [-5, 5, 1]))
        out["length"] = float(obj.get("length", 8))
    elif otype == "feynman":
        from cinemath.render_engine.feynman import PROCESSES

        process = obj.get("process", "1_to_2")
        if process not in PROCESSES:
            raise AnimValidationError(
                f"feynman process '{process}' not supported; use {sorted(PROCESSES)}"
            )
        labels = obj.get("labels") or {}
        if not isinstance(labels, dict):
            raise AnimValidationError("feynman labels must be an object")
        out["process"] = process
        out["labels"] = {str(k): str(v) for k, v in labels.items()}
        out["scale"] = float(obj.get("scale", 1.0))
    elif otype == "flow_field":
        out["axes"] = str(obj["axes"])
        out["beta_x"] = str(obj["beta_x"]).strip()
        out["beta_y"] = str(obj["beta_y"]).strip()
        _safe_expr(out["beta_x"], {"x", "y"})
        _safe_expr(out["beta_y"], {"x", "y"})
        grid = obj.get("grid", [7, 6])
        if not isinstance(grid, list) or len(grid) < 2:
            raise AnimValidationError("flow_field.grid must be [nx, ny]")
        out["grid"] = [int(grid[0]), int(grid[1])]
    elif otype == "statement":
        content = obj.get("content")
        if not isinstance(content, str) or not content.strip():
            raise AnimValidationError("statement needs content")
        out["content"] = content.strip()
        out["at"] = _pos(obj.get("at", "center"))
    elif otype == "prose":
        content = obj.get("content")
        if not isinstance(content, str) or not content.strip():
            raise AnimValidationError("prose needs content")
        out["content"] = content.strip()
        out["at"] = _pos(obj.get("at", "center"))
    return out


def _action(action: Any, sid: str, index: int, ids: set[str]) -> dict[str, Any]:
    if not isinstance(action, dict) or action.get("op") not in ACTION_OPS:
        raise AnimValidationError(f"{sid} actions[{index}] bad op")
    op = action["op"]
    out: dict[str, Any] = {"op": op}
    if op == "wait":
        out["seconds"] = float(action.get("seconds", 1))
        return out
    if op == "clear":
        return out
    if op == "set_caption":
        text = action.get("text")
        if not isinstance(text, str) or not text.strip():
            raise AnimValidationError(f"{sid} set_caption needs text")
        out["text"] = text.strip()
        return out
    if op == "derive":
        frm = action.get("from")
        to = action.get("to")
        if not isinstance(frm, str) or not isinstance(to, str):
            raise AnimValidationError(f"{sid} derive needs from/to")
        if frm not in ids or to not in ids:
            raise AnimValidationError(f"{sid} derive unknown ids")
        out["from"] = frm
        out["to"] = to
        out["buff"] = float(action.get("buff", 0.55))
        return out
    if op == "fork":
        frm = action.get("from")
        to = action.get("to")
        if not isinstance(frm, str) or not isinstance(to, list) or len(to) < 2:
            raise AnimValidationError(f"{sid} fork needs from/to[]")
        if not all(isinstance(item, str) for item in to):
            raise AnimValidationError(f"{sid} fork targets must be ids")
        if frm not in ids or any(item not in ids for item in to):
            raise AnimValidationError(f"{sid} fork unknown ids")
        out["from"] = frm
        out["to"] = list(to)
        out["buff"] = float(action.get("buff", 0.75))
        return out
    if op == "move_camera":
        out["phi"] = float(action.get("phi", 70))
        out["theta"] = float(action.get("theta", -45))
        out["run_time"] = float(action.get("run_time", 1))
        if "zoom" in action:
            out["zoom"] = float(action["zoom"])
        return out
    if op == "transform":
        out["from"] = str(action["from"])
        out["to"] = str(action["to"])
        return out
    targets = action.get("targets") or ([action["target"]] if "target" in action else None)
    if not targets:
        raise AnimValidationError(f"{sid} actions[{index}] needs targets")
    out["targets"] = list(targets)
    for t in out["targets"]:
        if t not in ids:
            raise AnimValidationError(f"{sid} unknown target {t}")
    return out


def _color(value: Any) -> str:
    key = str(value).lower()
    if key in COLORS or key.startswith("#"):
        return key
    raise AnimValidationError(f"bad color {value}")


def _pos(value: Any) -> Any:
    if isinstance(value, str) and value in SLOTS:
        return value
    return _point(value)


def _point(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) < 2:
        raise AnimValidationError("point needs [x, y] or [x, y, z]")
    pts = [float(value[0]), float(value[1])]
    if len(value) > 2:
        pts.append(float(value[2]))
    return pts


def _range3(value: Any) -> list[float]:
    vals = [float(v) for v in value]
    if len(vals) == 2:
        vals.append(1.0)
    return vals[:3]


def _range2(value: Any) -> list[float]:
    return [float(value[0]), float(value[1])]


def _safe_expr(expr: str, allowed: set[str]) -> None:
    tree = ast.parse(expr, mode="eval")

    def walk(node: ast.AST) -> None:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return
        if isinstance(node, ast.Name) and node.id in allowed:
            return
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            walk(node.left)
            walk(node.right)
            return
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
            walk(node.operand)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
            for a in node.args:
                walk(a)
            return
        raise AnimValidationError(f"unsafe expr: {expr}")

    walk(tree.body)


def compile_expr(expr: str):
    tree = ast.parse(expr, mode="eval")

    def ev(node: ast.AST, env: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return float(env[node.id])
        if isinstance(node, ast.BinOp):
            return float(_BIN[type(node.op)](ev(node.left, env), ev(node.right, env)))
        if isinstance(node, ast.UnaryOp):
            return float(_UNARY[type(node.op)](ev(node.operand, env)))
        if isinstance(node, ast.Call):
            import math

            return float(getattr(math, node.func.id)(*(ev(a, env) for a in node.args)))
        raise AnimValidationError("bad expr eval")

    return lambda x, _t=tree: ev(_t.body, {"x": float(x)})


def compile_expr2(expr: str):
    tree = ast.parse(expr, mode="eval")

    def ev(node: ast.AST, env: dict[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            return float(env[node.id])
        if isinstance(node, ast.BinOp):
            return float(_BIN[type(node.op)](ev(node.left, env), ev(node.right, env)))
        if isinstance(node, ast.UnaryOp):
            return float(_UNARY[type(node.op)](ev(node.operand, env)))
        if isinstance(node, ast.Call):
            import math

            return float(getattr(math, node.func.id)(*(ev(a, env) for a in node.args)))
        raise AnimValidationError("bad expr eval")

    return lambda x, y, _t=tree: ev(_t.body, {"x": float(x), "y": float(y)})
