"""Manim renderer for template-produced animation scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manim import (
    DEGREES,
    DOWN,
    LEFT,
    ORIGIN,
    RIGHT,
    UP,
    Arrow,
    Axes,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    MathTex,
    NumberLine,
    ReplacementTransform,
    ThreeDAxes,
    ThreeDScene,
    VGroup,
    VMobject,
)

from mathanim.render_engine import COLORS
from mathanim.render_engine import feynman as feynman_mod
from mathanim.render_engine import graph_2d, graph_3d
from mathanim.render_engine import instructions as instr
from mathanim.render_engine import problem_statement as stmt
from mathanim.render_engine.equation_chain import EquationChain
from mathanim.render_engine.sanitize import to_math_tex
from mathanim.render_engine.texutil import plain_tex
from mathanim.render_engine.validate import validate_animation

_DIRECTION = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}
_SLOT = {
    "title": UP * 2.15,
    "center": DOWN * 0.15,
    "upper": UP * 1.15,
    "lower": DOWN * 2.15,
    "left": LEFT * 3.2 + DOWN * 0.1,
    "right": RIGHT * 3.2 + DOWN * 0.1,
    "ul": UP * 1.6 + LEFT * 3.4,
    "ur": UP * 1.6 + RIGHT * 3.4,
    "ll": DOWN * 2.3 + LEFT * 3.4,
    "lr": DOWN * 2.3 + RIGHT * 3.4,
}
# Split-stage transition: previous step → left half, new step → right half.
_LEFT_CENTER = LEFT * 3.35
_RIGHT_CENTER = RIGHT * 3.35
_HALF_MAX_W = 5.7
_HALF_MAX_H = 6.2
_LEFT_PANEL_OPACITY = 0.55
_CAPTION_CEILING = 2.7
_CHROME_TYPES = frozenset(
    {
        "axes",
        "axes3d",
        "plot",
        "surface",
        "polygon",
        "line",
        "arrow",
        "number_line",
        "dot",
        "feynman",
        "flow_field",
    }
)
_LABEL_TYPES = frozenset({"math", "text", "prose"})

SCENE_WRAPPER = '''\
"""Auto-generated. Source of truth: animation.json"""
from mathanim.render_engine.builder import ScriptedScene

class MathSolution(ScriptedScene):
    pass
'''


def write_scene_module(path: Path) -> Path:
    path.write_text(SCENE_WRAPPER, encoding="utf-8")
    return path


class ScriptedScene(ThreeDScene):
    def construct(self) -> None:
        import sys

        module = sys.modules[type(self).__module__]
        animation_path = Path(module.__file__).resolve().with_name("animation.json")
        script = validate_animation(json.loads(animation_path.read_text(encoding="utf-8")))
        ScriptRunner(self, script).run()


class ScriptRunner:
    def __init__(self, scene: ThreeDScene, script: dict[str, Any]) -> None:
        self.scene = scene
        self.script = script
        self.mobjects: dict[str, VMobject] = {}
        self._obj_type: dict[str, str] = {}
        self.on_screen: set[str] = set()
        self.caption_mob: VMobject | None = None
        self.left_panel: VMobject | None = None
        self._use_right_stage = False
        self._mode = "2d"
        self.board = EquationChain(
            scene,
            mobjects=self.mobjects,
            on_screen=self.on_screen,
            use_right_stage=lambda: self._use_right_stage,
            accent_color=lambda: self._color("yellow"),
        )

    def run(self) -> None:
        self._set_flat_camera(animate=False)
        scenes = self.script["scenes"]
        for scene_data in scenes:
            self._run_scene(scene_data)

        # Closing beat: clear the split stage, show the answer centered.
        outro = []
        if self.left_panel is not None:
            outro.append(FadeOut(self.left_panel))
            self.left_panel = None
        leftovers = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
        if self.caption_mob is not None:
            leftovers.append(self.caption_mob)
        if leftovers:
            outro.extend(FadeOut(m) for m in leftovers)
        if outro:
            self.scene.play(*outro, run_time=0.45)
        self.on_screen.clear()
        self.caption_mob = None
        self.mobjects.clear()

        answer = self._answer_mob(self.script["answer"])
        answer.move_to(_SLOT["center"])
        self.scene.play(FadeIn(answer))
        self.scene.wait(1.3)

    def _run_scene(self, scene_data: dict[str, Any]) -> None:
        self.mobjects.clear()
        self._obj_type.clear()
        self.on_screen.clear()
        self.caption_mob = None
        self.board.clear()
        # After the first scene parks left, new work happens on the right half.
        self._use_right_stage = self.left_panel is not None
        self._ensure_mode(scene_data.get("mode", "2d"))

        for obj in scene_data["objects"]:
            self._obj_type[obj["id"]] = obj["type"]
            self.mobjects[obj["id"]] = self._build_object(obj)
        for obj in scene_data["objects"]:
            if "next_to" in obj:
                self.mobjects[obj["id"]].next_to(
                    self.mobjects[obj["next_to"]],
                    _DIRECTION[obj.get("direction", "down")],
                )

        # Before playing: keep formulas clear of axes / plots / regions.
        if scene_data.get("separate_labels", True):
            self._separate_labels_from_geometry(scene_data)

        # 3D surfaces need the full frame; half-stage AABB fit fights the camera.
        is_3d = scene_data.get("mode") == "3d"
        if is_3d and self.left_panel is not None:
            self.scene.play(FadeOut(self.left_panel, shift=LEFT * 0.4), run_time=0.4)
            self.left_panel = None
            self._use_right_stage = False

        if self._use_right_stage and self.mobjects and not is_3d:
            content = VGroup(*self.mobjects.values())
            self._fit_group_to_region(
                content,
                center=_RIGHT_CENTER,
                max_w=_HALF_MAX_W,
                max_h=_HALF_MAX_H,
            )

        if scene_data.get("caption"):
            self.caption_mob = instr.build_instruction(
                scene_data["caption"],
                color=self._color("gray"),
                right_stage=self._use_right_stage and not is_3d,
            )
            instr.place_instruction(
                self.caption_mob,
                right_stage=self._use_right_stage and not is_3d,
            )
            self.scene.play(FadeIn(self.caption_mob), run_time=0.35)
            if is_3d:
                graph_3d.fix_caption_in_frame(self.scene, self.caption_mob)

        for action in scene_data["actions"]:
            self._run_action(action)

        if is_3d:
            graph_3d.unfix_caption(self.scene, self.caption_mob)

        if scene_data.get("pin", True):
            self._swipe_to_left_half()
        else:
            self._fade_scene_out()
            if is_3d and self._mode == "3d":
                graph_3d.exit_3d(self.scene)
                self._mode = "2d"

    def _separate_labels_from_geometry(self, scene_data: dict[str, Any]) -> None:
        """Push math/text above axes/plots/regions when their bounding boxes collide."""
        meta = {o["id"]: o for o in scene_data.get("objects") or []}
        chrome = [
            self.mobjects[oid]
            for oid, obj in meta.items()
            if obj.get("type") in _CHROME_TYPES and oid in self.mobjects
        ]
        labels = [
            self.mobjects[oid]
            for oid, obj in meta.items()
            if obj.get("type") in _LABEL_TYPES and oid in self.mobjects
        ]
        if not chrome or not labels:
            return

        chrome_group = VGroup(*chrome)
        buff = 0.45

        def _overlaps(a: VMobject, b: VMobject, pad: float = 0.1) -> bool:
            return not (
                a.get_right()[0] + pad < b.get_left()[0]
                or b.get_right()[0] + pad < a.get_left()[0]
                or a.get_top()[1] + pad < b.get_bottom()[1]
                or b.get_top()[1] + pad < a.get_bottom()[1]
            )

        for lab in labels:
            if not any(_overlaps(lab, c) for c in chrome):
                continue
            lab.next_to(chrome_group, UP, buff=buff)

        # If labels now hit the caption band, drop the geometry instead.
        highest_label = max(float(lab.get_top()[1]) for lab in labels)
        if highest_label > _CAPTION_CEILING:
            drop = highest_label - _CAPTION_CEILING + 0.15
            chrome_group.shift(DOWN * drop)
            for lab in labels:
                if any(_overlaps(lab, c, pad=0.05) for c in chrome):
                    lab.next_to(chrome_group, UP, buff=buff)

    def _answer_mob(self, answer: str) -> VMobject:
        """Render the closing answer with real math (not escaped plain text)."""
        ans = to_math_tex(answer.strip())
        color = self._color("yellow")
        try:
            return MathTex(rf"\text{{Answer: }}{ans}", font_size=40, color=color)
        except Exception:
            return plain_tex(f"Answer: {answer}", font_size=40, color=color)

    def _ensure_mode(self, mode: str) -> None:
        if mode == self._mode:
            return
        if mode == "3d":
            graph_3d.enter_3d(self.scene, phi=70, theta=-45, run_time=0.55)
        else:
            graph_3d.exit_3d(self.scene, run_time=0.45)
        self._mode = mode

    def _set_flat_camera(self, *, animate: bool) -> None:
        if animate:
            graph_3d.exit_3d(self.scene, run_time=0.45)
        else:
            self.scene.set_camera_orientation(phi=0, theta=-90 * DEGREES)

    def _fit_group_to_region(
        self,
        group: VMobject,
        *,
        center,
        max_w: float,
        max_h: float,
        max_scale: float = 1.0,
    ) -> None:
        """Scale + move a group so it fits inside a half-frame region."""
        w = max(float(group.width), 1e-3)
        h = max(float(group.height), 1e-3)
        scale = min(max_w / w, max_h / h, max_scale)
        if scale < 0.999:
            group.scale(scale)
        group.move_to(center)

    def _swipe_to_left_half(self) -> None:
        """Park the finished step on the left half; next step will use the right."""
        pieces = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
        # Fade the caption out — keeping it in the left pin overlaps the next
        # scene's instruction banner across the top of the frame.
        anims = []
        if self.caption_mob is not None:
            anims.append(FadeOut(self.caption_mob, shift=UP * 0.15))
            self.caption_mob = None
        if not pieces:
            if anims:
                self.scene.play(*anims, run_time=0.35)
            return

        group = VGroup(*pieces)
        w = max(float(group.width), 1e-3)
        h = max(float(group.height), 1e-3)
        scale = min(_HALF_MAX_W / w, _HALF_MAX_H / h, 1.0)

        if self.left_panel is not None:
            anims.append(FadeOut(self.left_panel, shift=LEFT * 0.6))
        # ONE transform on the whole group. Do NOT also .animate children here —
        # concurrent child animations steal them from the parent move (axes move,
        # plots/ticks/tips/points get left behind).
        anims.append(group.animate.scale(scale).move_to(_LEFT_CENTER))
        self.scene.play(*anims, run_time=0.75)
        self._apply_panel_dim(group, _LEFT_PANEL_OPACITY)
        self.left_panel = group
        self.on_screen.clear()
        self.mobjects.clear()
        self.board.clear()
        self.scene.wait(0.12)

    def _apply_panel_dim(self, mob: VMobject, opacity: float) -> None:
        """Dim a parked left panel without enabling stroke-only plot fills."""
        name = type(mob).__name__
        if name == "ParametricFunction":
            mob.set_fill(opacity=0)
            mob.set_stroke(opacity=opacity)
            return
        if name not in {"MathTex", "Tex", "SingleStringMathTex", "DecimalNumber"} and getattr(
            mob, "submobjects", None
        ):
            for sub in list(mob.submobjects):
                self._apply_panel_dim(sub, opacity)
            if mob.submobjects:
                return
        mob.set_opacity(opacity)
        if name == "ParametricFunction":
            mob.set_fill(opacity=0)

    def _force_stroke_curves_unfilled(self, mob: VMobject) -> None:
        """Safety net: plots must stay fill-free after panel dimming."""
        if type(mob).__name__ == "ParametricFunction":
            mob.set_fill(opacity=0)
            return
        for sub in getattr(mob, "submobjects", []) or []:
            self._force_stroke_curves_unfilled(sub)

    def _fade_scene_out(self) -> None:
        pieces = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
        if self.caption_mob is not None:
            pieces.append(self.caption_mob)
        if pieces:
            self.scene.play(*[FadeOut(m) for m in pieces], run_time=0.45)
        self.on_screen.clear()
        self.caption_mob = None
        self.mobjects.clear()
        self.board.clear()

    def _run_action(self, action: dict[str, Any]) -> None:
        op = action["op"]
        if op == "wait":
            self.scene.wait(float(action["seconds"]))
            return
        if op == "set_caption":
            self._set_caption(action["text"])
            return
        if op == "derive":
            self.board.derive(action["from"], action["to"], buff=float(action.get("buff", 0.55)))
            return
        if op == "clear":
            fade = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
            if self.caption_mob is not None:
                fade.append(self.caption_mob)
            if fade:
                self.scene.play(*[FadeOut(m) for m in fade])
            self.on_screen.clear()
            self.caption_mob = None
            self.board.clear()
            return
        if op == "move_camera":
            graph_3d.enter_3d(
                self.scene,
                phi=float(action["phi"]),
                theta=float(action["theta"]),
                run_time=float(action.get("run_time", 1)),
            )
            self._mode = "3d"
            return
        if op == "transform":
            src, dst = action["from"], action["to"]
            self.scene.play(ReplacementTransform(self.mobjects[src], self.mobjects[dst]))
            self.mobjects[src] = self.mobjects[dst]
            self.on_screen.discard(src)
            self.on_screen.add(dst)
            return
        targets = action["targets"]
        mobs = [self.mobjects[t] for t in targets]
        if op == "create":
            # Prefer axes→surface reveal for 3D volume beats.
            surf_ids = [t for t in targets if self._obj_type.get(t) == "surface"]
            axes_ids = [t for t in targets if self._obj_type.get(t) == "axes3d"]
            if (
                len(axes_ids) == 1
                and len(surf_ids) == 1
                and set(targets) == {axes_ids[0], surf_ids[0]}
            ):
                graph_3d.reveal_surface(
                    self.scene, self.mobjects[axes_ids[0]], self.mobjects[surf_ids[0]]
                )
                self.on_screen.update(targets)
            else:
                # Stroke-only plots: FadeIn (Create can flash a closed-path fill
                # between equal-height endpoints of a parabola).
                plot_ids = [t for t in targets if self._obj_type.get(t) == "plot"]
                other_ids = [t for t in targets if t not in plot_ids]
                anims = []
                if other_ids:
                    anims.extend(Create(self.mobjects[t]) for t in other_ids)
                if plot_ids:
                    anims.extend(FadeIn(self.mobjects[t]) for t in plot_ids)
                self.scene.play(*anims)
                self.on_screen.update(targets)
        elif op == "write":
            stmt_ids = [t for t in targets if self._obj_type.get(t) == "statement"]
            if stmt_ids and set(stmt_ids) == set(targets):
                for tid in stmt_ids:
                    stmt.play_write_statement(self.scene, self.mobjects[tid])
                self.on_screen.update(targets)
            else:
                self.board.write(targets)
        elif op == "fade_in":
            self.scene.play(*[FadeIn(m) for m in mobs])
            self.on_screen.update(targets)
        elif op == "fade_out":
            self.scene.play(*[FadeOut(m) for m in mobs])
            self.on_screen.difference_update(targets)
            self.board.discard(targets)
        elif op == "indicate":
            self.scene.play(*[Indicate(m) for m in mobs])

    def _set_caption(self, text: str) -> None:
        self.caption_mob = instr.play_set_instruction(
            self.scene,
            self.caption_mob,
            text,
            color=self._color("gray"),
            right_stage=self._use_right_stage and self._mode != "3d",
        )

    def _build_object(self, obj: dict[str, Any]) -> VMobject:
        otype = obj["type"]
        color = self._color(obj.get("color", "white"))
        font_size = int(obj.get("font_size", 36))
        if otype == "text":
            mob: VMobject = plain_tex(obj["content"], font_size=font_size, color=color)
        elif otype == "math":
            mob = MathTex(to_math_tex(obj["tex"]), font_size=font_size, color=color)
        elif otype == "prose":
            mob = instr.build_instruction(
                obj["content"],
                color=color,
                font_size=font_size,
                right_stage=False,
            )
            # build_instruction pins to the top; relocate to the requested slot.
            self._place(mob, obj)
            return mob
        elif otype == "axes":
            mob = graph_2d.build_axes(obj, color=color)
        elif otype == "axes3d":
            mob = graph_3d.build_axes3d(obj)
        elif otype == "number_line":
            mob = NumberLine(
                x_range=obj["x_range"],
                length=obj["length"],
                include_numbers=True,
                font_size=24,
                color=color,
            )
        elif otype == "plot":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, Axes)
            mob = graph_2d.build_plot(obj, axes, color=color)
        elif otype == "surface":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, ThreeDAxes)
            mob = graph_3d.build_surface(obj, axes, color=color)
        elif otype == "polygon":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, Axes)
            mob = graph_2d.build_polygon(obj, axes, color=color)
        elif otype == "dot":
            if "axes" in obj:
                axes = self.mobjects[obj["axes"]]
                assert isinstance(axes, Axes)
                mob = graph_2d.build_axes_dot(obj, axes, color=color)
            elif "number_line" in obj:
                nl = self.mobjects[obj["number_line"]]
                assert isinstance(nl, NumberLine)
                mob = Dot(nl.n2p(obj["value"]), color=color)
            else:
                mob = Dot(color=color)
        elif otype == "line":
            start, end = self._endpoints(obj)
            stroke = float(obj.get("stroke_width", 2))
            if obj.get("dashed"):
                mob = DashedLine(start, end, color=color, stroke_width=stroke)
            else:
                mob = Line(start, end, color=color, stroke_width=stroke)
        elif otype == "arrow":
            start, end = self._endpoints(obj)
            stroke = float(obj.get("stroke_width", 2))
            tip = float(obj.get("tip_length", 0.18))
            mob = Arrow(
                start,
                end,
                color=color,
                buff=0,
                stroke_width=stroke,
                tip_length=tip,
                max_tip_length_to_length_ratio=0.35,
            )
        elif otype == "feynman":
            mob = feynman_mod.build_feynman(
                obj, color=color, accent=self._color("yellow")
            )
        elif otype == "flow_field":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, Axes)
            mob = graph_2d.build_flow_field(obj, axes, color=color)
        elif otype == "statement":
            mob = stmt.build_statement(
                obj["content"],
                color=color,
                font_size=int(obj.get("font_size", 30)),
            )
            stmt.place_statement(mob)
            return mob
        else:
            raise RuntimeError(otype)

        if "next_to" not in obj:
            self._place(mob, obj)
        return mob

    def _endpoints(self, obj: dict[str, Any]):
        if "axes" in obj:
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, Axes)
            return axes.c2p(*obj["start"]), axes.c2p(*obj["end"])
        return (
            float(obj["start"][0]) * RIGHT + float(obj["start"][1]) * UP,
            float(obj["end"][0]) * RIGHT + float(obj["end"][1]) * UP,
        )

    def _place(self, mob: VMobject, obj: dict[str, Any]) -> None:
        if obj["type"] in {"plot", "surface", "polygon", "flow_field"}:
            return
        if obj["type"] == "dot" and ("axes" in obj or "number_line" in obj):
            return
        # Absolute start/end already place the segment; do not re-center it.
        if obj["type"] in {"line", "arrow"}:
            return
        if obj["type"] == "axes3d":
            graph_3d.place_axes3d(mob, obj)
            return
        if obj["type"] == "axes" and not isinstance(obj.get("at"), str):
            graph_2d.place_axes(mob, obj)
            return
        at = obj.get("at", "center")
        if isinstance(at, str):
            mob.move_to(_SLOT["title"] if at == "title" else _SLOT[at])
        else:
            mob.move_to(float(at[0]) * RIGHT + float(at[1]) * UP)

    def _color(self, name: str):
        if isinstance(name, str) and name.startswith("#"):
            return name
        return COLORS.get(str(name).lower(), COLORS["white"])
