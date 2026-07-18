"""Compile visual-tool calls into animation scenes."""

from __future__ import annotations

from typing import Any

from cinemath.render_engine import graph_2d, graph_3d

from . import dsl
from .board import equation_board_scene
from .paper_arithmetic import (
    compile_long_addition,
    compile_long_division,
    compile_long_multiplication,
    compile_long_subtraction,
)


def compile_visuals(plan: dict[str, Any]) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    for index, visual in enumerate(plan["visuals"]):
        scenes.extend(compile_visual(visual, plan, index=index))
    return scenes


def compile_visual(visual: dict[str, Any], plan: dict[str, Any], *, index: int) -> list[dict[str, Any]]:
    tool = visual["tool"]

    if tool == "equation_board":
        scene = equation_board_scene(f"board_{index}", plan["steps"], pin=True)
        if scene is None:
            raise ValueError("equation_board requires at least one math line")
        return [scene]
    if tool == "state_claim":
        return [_state_claim_scene(visual, index=index)]
    if tool == "show_qed":
        return [_show_qed_scene(visual, index=index)]
    if tool == "plot_2d":
        return [_plot_2d_scene(visual, index=index)]
    if tool == "plot_integral_1d":
        return [_plot_integral_1d_scene(visual, index=index)]
    if tool == "plot_lines_2d":
        return [_plot_lines_2d_scene(visual, index=index)]
    if tool == "plot_planes_3d":
        return [_plot_planes_3d_scene(visual, index=index)]
    if tool == "show_region_rectangle":
        return [_region_scene(visual, index=index)]
    if tool == "plot_surface_3d":
        return [_surface_scene(visual, index=index)]
    if tool == "paper_long_multiply":
        return list(_paper_script(plan, visual, kind="multiply")["scenes"])
    if tool == "paper_long_divide":
        return list(_paper_script(plan, visual, kind="divide")["scenes"])
    if tool == "paper_long_add":
        return list(_paper_script(plan, visual, kind="add")["scenes"])
    if tool == "paper_long_subtract":
        return list(_paper_script(plan, visual, kind="subtract")["scenes"])
    if tool == "show_lagrangian":
        return [_lagrangian_scene(visual, index=index)]
    if tool == "feynman_1to2":
        return [_feynman_scene(visual, index=index)]
    if tool == "feynman_loop":
        return [_feynman_loop_scene(visual, index=index)]
    if tool == "rg_flow_2d":
        return [_rg_flow_scene(visual, index=index)]
    if tool == "show_answer":
        return [_answer_scene(visual, index=index)]
    raise ValueError(f"Unsupported visual tool: {tool}")


def _state_claim_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    claim_id = f"claim_{index}"
    objects = [dsl.math(claim_id, visual["claim"], at="center", font_size=38, color="yellow")]
    actions = [dsl.write(claim_id), dsl.wait(0.7)]
    given = list(visual.get("given") or [])
    if given:
        given_id = f"given_{index}_0"
        # Givens are prose (possibly with $...$); never MathTex plain text.
        objects.append(
            {
                "id": given_id,
                "type": "prose",
                "content": given[0],
                "at": "lower",
                "font_size": 28,
                "color": "white",
            }
        )
        actions.extend([dsl.write(given_id), dsl.wait(0.5)])
    return dsl.scene(
        f"claim_{index}",
        caption="Claim",
        objects=objects,
        actions=actions,
    )


def _show_qed_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    obj_id = f"qed_{index}"
    return dsl.scene(
        f"qed_{index}",
        caption="QED",
        objects=[dsl.math(obj_id, visual["tex"], at="center", font_size=40, color="green")],
        actions=[dsl.write(obj_id), dsl.indicate(obj_id), dsl.wait(1.0)],
    )


def _plot_integral_1d_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    expr = visual["expr"]
    x0, x1 = visual["x_min"], visual["x_max"]
    x_range = graph_2d.integer_axis_range(x0, x1, step=1.0, pad=0.0)
    plot_x0, plot_x1 = x_range[0], x_range[1]
    y_range = graph_2d.auto_y_range(expr, plot_x0, plot_x1, include=[0.0], max_step=1.0)
    y_range = graph_2d.integer_axis_range(y_range[0], y_range[1], step=1.0)

    label_id = f"int_lab_{index}"
    axis_id = f"int_ax_{index}"
    curve_id = f"int_curve_{index}"

    shade_min = visual.get("shade_min")
    shade_max = visual.get("shade_max")
    plot_range = None
    shade = graph_2d.SHADE_NONE
    if shade_min is not None and shade_max is not None:
        plot_range = [float(shade_min), float(shade_max)]
        shade = graph_2d.SHADE_X_AXIS

    if visual.get("lower_infinite") and visual.get("upper_infinite"):
        lo_tex = r"-\infty"
        hi_tex = r"\infty"
    elif visual.get("lower_infinite"):
        lo_tex = r"-\infty"
        hi_tex = _fmt(visual["upper"])
    elif visual.get("upper_infinite"):
        lo_tex = _fmt(visual["lower"])
        hi_tex = r"\infty"
    else:
        lo_tex = _fmt(visual["lower"])
        hi_tex = _fmt(visual["upper"])

    import sympy as sp

    body = sp.latex(sp.sympify(expr))
    label_tex = rf"\int_{{{lo_tex}}}^{{{hi_tex}}} {body}\,dx"

    if visual.get("lower_infinite") and visual.get("upper_infinite"):
        caption = "Shape of the integrand near the origin"
    elif visual.get("upper_infinite"):
        caption = "Area under the curve from the finite bound"
    elif visual.get("lower_infinite"):
        caption = "Area under the curve up to the finite bound"
    else:
        caption = "Area under the curve on the interval"

    objects: list[dict[str, Any]] = [
        {
            "id": label_id,
            "type": "math",
            "tex": label_tex,
            "font_size": 32,
            "next_to": axis_id,
            "direction": "up",
            "buff": graph_2d.INTEGRAL_LABEL_BUFF,
        },
        graph_2d.axes_object(
            axis_id,
            x_range=x_range,
            y_range=y_range,
            at=graph_2d.INTEGRAL_PLOT_AT,
            x_length=graph_2d.PLOT_X_LENGTH,
            y_length=graph_2d.PLOT_Y_LENGTH,
        ),
        graph_2d.plot_object(
            curve_id,
            axes=axis_id,
            expr=expr,
            color="blue",
            x_range=plot_range,
            shade=shade,
        ),
    ]

    dot_ids: list[str] = []
    for side, bound in (("lo", visual.get("lower")), ("hi", visual.get("upper"))):
        if bound is None:
            continue
        dot_id = f"int_bound_{index}_{side}"
        dot_ids.append(dot_id)
        objects.append(
            {
                "id": dot_id,
                "type": "dot",
                "axes": axis_id,
                "at": [float(bound), 0],
                "color": "yellow",
            }
        )

    actions = [dsl.write(label_id), dsl.create(axis_id, curve_id)]
    if dot_ids:
        actions.extend([dsl.fade_in(*dot_ids), dsl.indicate(*dot_ids)])
    actions.append(dsl.wait(0.9))

    return dsl.scene(
        f"plot_integral_1d_{index}",
        caption=caption,
        objects=objects,
        actions=actions,
    )


def _plot_2d_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    coef = visual["coefficients"]
    a, b, c = coef["a"], coef["b"], coef["c"]
    roots = list(visual["roots"])
    x_range = graph_2d.integer_axis_range(min(roots), max(roots), step=1.0, pad=2.0)
    x0, x1 = x_range[0], x_range[1]
    expr = _quadratic_expr(a, b, c)
    y_range = graph_2d.auto_y_range(expr, x0, x1, include=[0.0], max_step=1.0)
    y_range = graph_2d.integer_axis_range(y_range[0], y_range[1], step=1.0)

    label_id = f"quad_lab_{index}"
    axis_id = f"quad_ax_{index}"
    curve_id = f"quad_curve_{index}"
    dot_ids = [f"quad_root_{index}_{i}" for i in range(len(roots))]

    objects: list[dict[str, Any]] = [
        dsl.math(label_id, f"y = {_quadratic_tex(a, b, c)}", at=graph_2d.LABEL_AT, font_size=34),
        graph_2d.axes_object(
            axis_id,
            x_range=x_range,
            y_range=y_range,
            x_length=graph_2d.PLOT_X_LENGTH,
            y_length=graph_2d.PLOT_Y_LENGTH,
        ),
        graph_2d.plot_object(
            curve_id,
            axes=axis_id,
            expr=expr,
            color="blue",
            x_range=[x0 + 0.05, x1 - 0.05],
            shade="none",
        ),
    ]
    objects.extend(
        {
            "id": dot_ids[i],
            "type": "dot",
            "axes": axis_id,
            "at": [float(root), 0],
            "color": "red",
        }
        for i, root in enumerate(roots)
    )

    return dsl.scene(
        f"plot_2d_{index}",
        caption="Where the parabola meets the x-axis",
        objects=objects,
        actions=[
            dsl.write(label_id),
            dsl.create(axis_id, curve_id),
            dsl.fade_in(*dot_ids),
            dsl.indicate(*dot_ids),
            dsl.wait(0.8),
        ],
    )


def _plot_lines_2d_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    eqs = list(visual["equations"])
    sol = visual["solution"]
    sx, sy = float(sol["x"]), float(sol["y"])
    pad = 3.0
    x_range = graph_2d.integer_axis_range(sx - pad, sx + pad, step=1.0)
    y_range = graph_2d.integer_axis_range(sy - pad, sy + pad, step=1.0)
    x0, x1 = x_range[0], x_range[1]
    y0, y1 = y_range[0], y_range[1]

    label_id = f"lines_lab_{index}"
    axis_id = f"lines_ax_{index}"
    colors = ("blue", "green")
    line_ids: list[str] = []
    objects: list[dict[str, Any]] = [
        dsl.math(
            label_id,
            r"\text{intersection of two lines}",
            at=graph_2d.LABEL_AT,
            font_size=32,
        ),
        graph_2d.axes_object(
            axis_id,
            x_range=x_range,
            y_range=y_range,
            x_length=graph_2d.PLOT_X_LENGTH,
            y_length=graph_2d.PLOT_Y_LENGTH,
        ),
    ]
    for i, eq in enumerate(eqs):
        clipped = graph_2d.clip_line_eq(eq["a"], eq["b"], eq["c"], x0, x1, y0, y1)
        if clipped is None:
            raise ValueError(f"line {i} does not intersect the plot window")
        start, end = clipped
        lid = f"line_{index}_{i}"
        line_ids.append(lid)
        objects.append(
            graph_2d.line_object(
                lid,
                axes=axis_id,
                start=start,
                end=end,
                color=colors[i % len(colors)],
                stroke_width=4.0,
            )
        )

    dot_id = f"lines_sol_{index}"
    objects.append(
        {
            "id": dot_id,
            "type": "dot",
            "axes": axis_id,
            "at": [sx, sy],
            "color": "red",
        }
    )
    return dsl.scene(
        f"plot_lines_2d_{index}",
        caption="Where the two lines meet",
        objects=objects,
        actions=[
            dsl.write(label_id),
            dsl.create(axis_id, *line_ids),
            dsl.fade_in(dot_id),
            dsl.indicate(dot_id),
            dsl.wait(0.9),
        ],
    )


def _plot_planes_3d_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    eqs = list(visual["equations"])
    sol = visual["solution"]
    sx, sy, sz = float(sol["x"]), float(sol["y"]), float(sol["z"])
    pad = 3.0
    x_range = graph_2d.integer_axis_range(sx - pad, sx + pad, step=1.0)
    y_range = graph_2d.integer_axis_range(sy - pad, sy + pad, step=1.0)
    z_range = graph_2d.integer_axis_range(sz - pad, sz + pad, step=1.0)

    axes_id = f"planes_ax_{index}"
    colors = ("blue", "green", "yellow")
    plane_ids: list[str] = []
    objects: list[dict[str, Any]] = [
        graph_3d.axes3d_object(
            axes_id,
            x_range=x_range,
            y_range=y_range,
            z_range=z_range,
        )
    ]
    for i, eq in enumerate(eqs):
        pid = f"plane_{index}_{i}"
        plane_ids.append(pid)
        objects.append(
            graph_3d.plane_object(
                pid,
                axes=axes_id,
                a=eq["a"],
                b=eq["b"],
                c=eq["c"],
                d=eq["d"],
                color=colors[i % len(colors)],
                opacity=0.32,
            )
        )
    dot_id = f"planes_sol_{index}"
    objects.append(
        {
            "id": dot_id,
            "type": "dot",
            "axes": axes_id,
            "at": [sx, sy, sz],
            "color": "red",
        }
    )
    return dsl.scene(
        f"plot_planes_3d_{index}",
        caption="Where the three planes meet",
        mode="3d",
        pin=False,
        objects=objects,
        actions=[
            dsl.move_camera(graph_3d.DEFAULT_PHI, graph_3d.DEFAULT_THETA),
            dsl.create(axes_id, *plane_ids),
            dsl.fade_in(dot_id),
            dsl.indicate(dot_id),
            dsl.wait(1.2),
        ],
    )


def _region_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    x0, x1 = visual["x_min"], visual["x_max"]
    y0, y1 = visual["y_min"], visual["y_max"]
    integrand_tex = _integrand_tex(visual["integrand"])
    pad_x = max(0.5, 0.25 * (x1 - x0))
    pad_y = max(0.5, 0.25 * (y1 - y0))
    ax_x = [x0 - pad_x, x1 + pad_x, 1]
    ax_y = [y0 - pad_y, y1 + pad_y, 1]

    integral_id = f"region_I_{index}"
    axis_id = f"region_ax_{index}"
    region_objects = graph_2d.region_outline(axis_id, x0, x1, y0, y1, color="yellow")
    rename = {
        "R": f"region_fill_{index}",
        "L1": f"region_l1_{index}",
        "L2": f"region_l2_{index}",
        "L3": f"region_l3_{index}",
        "L4": f"region_l4_{index}",
    }
    for obj in region_objects:
        obj["id"] = rename[obj["id"]]

    return dsl.scene(
        f"region_{index}",
        caption="Integrate over this rectangle",
        objects=[
            dsl.math(integral_id, rf"\iint_R {integrand_tex}\,dA", at=graph_2d.LABEL_AT, font_size=36),
            graph_2d.axes_object(
                axis_id,
                x_range=ax_x,
                y_range=ax_y,
                x_length=6.0,
                y_length=2.8,
            ),
            *region_objects,
        ],
        actions=[
            dsl.write(integral_id),
            dsl.create(axis_id),
            dsl.fade_in(rename["R"]),
            dsl.create(rename["L1"], rename["L2"], rename["L3"], rename["L4"]),
            dsl.wait(0.9),
        ],
    )


def _surface_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    x0, x1 = visual["x_min"], visual["x_max"]
    y0, y1 = visual["y_min"], visual["y_max"]
    pad_x = max(0.5, 0.25 * (x1 - x0))
    pad_y = max(0.5, 0.25 * (y1 - y0))
    ax_x = [x0 - pad_x, x1 + pad_x, 1]
    ax_y = [y0 - pad_y, y1 + pad_y, 1]
    z_range = graph_3d.sample_z_range(visual["integrand"], [x0, x1], [y0, y1])

    axes_id = f"surface_axes_{index}"
    surface_id = f"surface_plot_{index}"
    return dsl.scene(
        f"surface_{index}",
        caption="Volume under the surface",
        mode="3d",
        pin=False,
        objects=[
            graph_3d.axes3d_object(
                axes_id,
                x_range=ax_x,
                y_range=ax_y,
                z_range=z_range,
            ),
            graph_3d.surface_object(
                surface_id,
                axes=axes_id,
                expr=visual["integrand"],
                x_range=[x0, x1],
                y_range=[y0, y1],
                color="blue",
                opacity=0.75,
            ),
        ],
        actions=[
            dsl.move_camera(graph_3d.DEFAULT_PHI, graph_3d.DEFAULT_THETA),
            dsl.create(axes_id, surface_id),
            dsl.wait(1.2),
        ],
    )


def _lagrangian_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    lagrangian_id = f"lagrangian_{index}"
    condition_id = f"condition_{index}"
    objects = [
        dsl.math(lagrangian_id, rf"\mathcal{{L}}\supset {visual['interaction']}", at="upper", font_size=38)
    ]
    actions = [dsl.write(lagrangian_id)]
    condition = str(visual.get("condition") or "").strip()
    if condition:
        objects.append(dsl.math(condition_id, condition, at="lower", font_size=34, color="yellow"))
        actions.append(dsl.write(condition_id))
    actions.append(dsl.wait(0.9))
    caption = str(visual.get("caption") or "").strip() or "Interaction Lagrangian"
    return dsl.scene(
        f"lagrangian_{index}",
        caption=caption,
        objects=objects,
        actions=actions,
    )


def _feynman_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    daughters = visual["daughters"]
    out1 = daughters[0]
    out2 = daughters[1] if len(daughters) > 1 else daughters[0]
    diag_id = f"diag_{index}"
    return dsl.scene(
        f"diagram_{index}",
        caption="Tree-level decay",
        objects=[
            {
                "id": diag_id,
                "type": "feynman",
                "process": "1_to_2",
                "at": "center",
                "scale": 1.05,
                "labels": {
                    "in": visual["parent"],
                    "out1": out1,
                    "out2": out2,
                    "vertex": visual["coupling"],
                },
                "color": "white",
            }
        ],
        actions=[dsl.create(diag_id), dsl.wait(1.1)],
    )


def _feynman_loop_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    diag_id = f"loop_{index}"
    caption = str(visual.get("caption") or "").strip() or "One-loop diagram"
    return dsl.scene(
        f"feynman_loop_{index}",
        caption=caption,
        objects=[
            {
                "id": diag_id,
                "type": "feynman",
                "process": visual["process"],
                "at": "center",
                "scale": float(visual.get("scale", 1.0)),
                "labels": dict(visual.get("labels") or {}),
                "color": "white",
            }
        ],
        actions=[dsl.create(diag_id), dsl.wait(1.1)],
    )


def _rg_flow_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    label_id = f"rg_lab_{index}"
    axis_id = f"rg_ax_{index}"
    field_id = f"rg_field_{index}"
    x_lab = visual.get("x_label") or r"\lambda"
    y_lab = visual.get("y_label") or "g"
    title = rf"(\beta_{{{x_lab}}}, \beta_{{{y_lab}}})"
    return dsl.scene(
        f"rg_flow_{index}",
        caption=visual.get("caption") or "RG flow",
        objects=[
            dsl.math(label_id, title, at=graph_2d.LABEL_AT, font_size=32),
            graph_2d.axes_object(
                axis_id,
                x_range=visual["x_range"],
                y_range=visual["y_range"],
                x_length=graph_2d.PLOT_X_LENGTH,
                y_length=graph_2d.PLOT_Y_LENGTH,
            ),
            graph_2d.flow_field_object(
                field_id,
                axes=axis_id,
                beta_x=visual["beta_x"],
                beta_y=visual["beta_y"],
                grid=visual.get("grid") or [7, 6],
                color="yellow",
            ),
        ],
        actions=[
            dsl.write(label_id),
            dsl.create(axis_id, field_id),
            dsl.wait(1.2),
        ],
    )


def _answer_scene(visual: dict[str, Any], *, index: int) -> dict[str, Any]:
    obj_id = f"answer_{index}"
    return dsl.scene(
        f"answer_{index}",
        caption=visual.get("caption") or "Answer",
        objects=[dsl.math(obj_id, visual["tex"], at="center", font_size=40, color="yellow")],
        actions=[dsl.write(obj_id), dsl.indicate(obj_id), dsl.wait(1.0)],
    )


def _paper_script(plan: dict[str, Any], visual: dict[str, Any], *, kind: str) -> dict[str, Any]:
    typed_plan = {
        "problem": plan["problem"],
        "answer": plan["answer"],
        "steps": plan["steps"],
        "data": dict(visual),
    }
    if kind == "multiply":
        return compile_long_multiplication(typed_plan)
    if kind == "divide":
        return compile_long_division(typed_plan)
    if kind == "add":
        return compile_long_addition(typed_plan)
    if kind == "subtract":
        return compile_long_subtraction(typed_plan)
    raise ValueError(f"Unsupported paper kind: {kind}")


def _quadratic_expr(a: float, b: float, c: float) -> str:
    return f"{a}*x**2 + ({b})*x + ({c})"


def _quadratic_tex(a: float, b: float, c: float) -> str:
    if abs(a - 1) < 1e-9:
        lead = "x^2"
    elif abs(a + 1) < 1e-9:
        lead = "-x^2"
    else:
        lead = f"{_fmt(a)}x^2"
    return f"{lead} {_sign(b)} {_fmt(abs(b))}x {_sign(c)} {_fmt(abs(c))}"


def _integrand_tex(expr: str) -> str:
    return expr.replace("**", "^").replace("*", "").replace(" ", "")


def _sign(value: float) -> str:
    return "-" if value < 0 else "+"


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.4g}"
