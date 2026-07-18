"""Manim renderer for template-produced animation scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manim import (
    DEGREES,
    DOWN,
    LEFT,
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

from cinemath.render_engine import COLORS
from cinemath.render_engine import feynman as feynman_mod
from cinemath.render_engine import graph_2d, graph_3d
from cinemath.render_engine import instructions as instr
from cinemath.render_engine import problem_statement as stmt
from cinemath.render_engine.equation_chain import EquationBoard
from cinemath.render_engine.sanitize import to_math_tex
from cinemath.render_engine.stage import StageConductor
from cinemath.render_engine.texutil import plain_tex
from cinemath.render_engine.validate import validate_animation

_DIRECTION = {"up": UP, "down": DOWN, "left": LEFT, "right": RIGHT}
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

_ANIMATION_JSON_ENV = "CINEMATH_ANIMATION_JSON"


class ScriptedScene(ThreeDScene):
    def construct(self) -> None:
        import os

        animation_json = os.environ.get(_ANIMATION_JSON_ENV)
        if not animation_json:
            raise RuntimeError(f"{_ANIMATION_JSON_ENV} is not set")
        animation_path = Path(animation_json).resolve()
        script = validate_animation(json.loads(animation_path.read_text(encoding="utf-8")))
        ScriptRunner(self, script).run()


class ScriptRunner:
    def __init__(self, scene: ThreeDScene, script: dict[str, Any]) -> None:
        self.scene = scene
        self.script = script
        self.mobjects: dict[str, VMobject] = {}
        self._obj_type: dict[str, str] = {}
        self.on_screen: set[str] = set()
        self.stage = StageConductor(scene)
        self._board_scene = False
        self.board = EquationBoard(
            scene,
            mobjects=self.mobjects,
            on_screen=self.on_screen,
            content_region=self.stage.board_region,
            accent_color=lambda: self._color("yellow"),
        )

    @property
    def caption_mob(self) -> VMobject | None:
        return self.stage.caption_mob

    @property
    def left_panel(self) -> VMobject | None:
        return self.stage.left_panel

    def run(self) -> None:
        self._set_flat_camera(animate=False)
        scenes = self.script["scenes"]
        for scene_data in scenes:
            self._run_scene(scene_data)

        # Closing beat: clear the split stage, show the answer centered.
        outro = self.stage.clear_left_panel()
        leftovers = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
        if self.stage.caption_mob is not None:
            leftovers.append(self.stage.caption_mob)
        if leftovers:
            outro.extend(FadeOut(m) for m in leftovers)
        if outro:
            self.scene.play(*outro, run_time=0.45)
        self.on_screen.clear()
        self.stage.caption_mob = None
        self.mobjects.clear()

        answer = self._answer_mob(self.script["answer"])
        self.stage.place(answer, at="center")
        self.scene.play(FadeIn(answer))
        self.scene.wait(1.3)

    def _run_scene(self, scene_data: dict[str, Any]) -> None:
        self.mobjects.clear()
        self._obj_type.clear()
        self.on_screen.clear()
        self.board.clear()
        pin_caption_top = self._will_be_board_scene(scene_data)
        self._board_scene = pin_caption_top
        self.stage.begin_scene(pin_caption_top=pin_caption_top)
        self._ensure_mode(scene_data.get("mode", "2d"))

        for obj in scene_data["objects"]:
            self._obj_type[obj["id"]] = obj["type"]
            self.mobjects[obj["id"]] = self._build_object(obj)
        for obj in scene_data["objects"]:
            if "next_to" in obj:
                kwargs: dict[str, Any] = {}
                if "buff" in obj:
                    kwargs["buff"] = float(obj["buff"])
                self.mobjects[obj["id"]].next_to(
                    self.mobjects[obj["next_to"]],
                    _DIRECTION[obj.get("direction", "down")],
                    **kwargs,
                )

        if scene_data.get("separate_labels", True):
            self._separate_labels_from_geometry(scene_data)

        is_3d = scene_data.get("mode") == "3d"
        if is_3d and self.stage.left_panel is not None:
            self.stage.release_left_for_3d()

        if self.stage.use_right_stage and self.mobjects and not is_3d and not self._board_scene:
            content = VGroup(*self.mobjects.values())
            self.stage.fit_active_if_split(content)

        if scene_data.get("caption"):
            self.stage.show_caption(
                scene_data["caption"],
                color=self._color("gray"),
                content=list(self.mobjects.values()),
            )
            if is_3d:
                graph_3d.fix_caption_in_frame(self.scene, self.stage.caption_mob)

        for action in scene_data["actions"]:
            self._run_action(action)

        if is_3d:
            graph_3d.unfix_caption(self.scene, self.stage.caption_mob)

        if scene_data.get("pin", True):
            pieces = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
            self.stage.pin_active_to_left(pieces)
            self.on_screen.clear()
            self.mobjects.clear()
            self.board.clear()
        else:
            pieces = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
            self.stage.clear_active(pieces)
            self.on_screen.clear()
            self.mobjects.clear()
            self.board.clear()
            if is_3d and self.stage.mode == "3d":
                graph_3d.exit_3d(self.scene)
                self.stage.mode = "2d"

    def _will_be_board_scene(self, scene_data: dict[str, Any]) -> bool:
        types = [o.get("type") for o in scene_data.get("objects") or []]
        return bool(types) and all(t == "math" for t in types)

    def _separate_labels_from_geometry(self, scene_data: dict[str, Any]) -> None:
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
        self.stage.separate_labels_from_chrome(labels, chrome)

    def _answer_mob(self, answer: str) -> VMobject:
        """Render the closing answer with real math (not escaped plain text)."""
        ans = to_math_tex(answer.strip())
        color = self._color("yellow")
        try:
            return MathTex(rf"\text{{Answer: }}{ans}", font_size=40, color=color)
        except Exception:
            return plain_tex(f"Answer: {answer}", font_size=40, color=color)

    def _ensure_mode(self, mode: str) -> None:
        if mode == self.stage.mode:
            return
        if mode == "3d":
            graph_3d.enter_3d(self.scene, phi=70, theta=-45, run_time=0.55)
        else:
            graph_3d.exit_3d(self.scene, run_time=0.45)
        self.stage.mode = mode

    def _set_flat_camera(self, *, animate: bool) -> None:
        if animate:
            graph_3d.exit_3d(self.scene, run_time=0.45)
        else:
            self.scene.set_camera_orientation(phi=0, theta=-90 * DEGREES)

    def _run_action(self, action: dict[str, Any]) -> None:
        op = action["op"]
        if op == "wait":
            self.scene.wait(float(action["seconds"]))
            return
        if op == "set_caption":
            self.stage.set_caption(
                action["text"],
                color=self._color("gray"),
                content=self._instruction_content(),
            )
            return
        if op == "derive":
            self.board.derive(action["from"], action["to"], buff=float(action.get("buff", 0.55)))
            return
        if op == "fork":
            self.board.fork(action["from"], list(action["to"]), buff=float(action.get("buff", 0.75)))
            return
        if op == "clear":
            fade = [self.mobjects[i] for i in list(self.on_screen) if i in self.mobjects]
            self.stage.clear_active(fade)
            self.on_screen.clear()
            self.board.clear()
            return
        if op == "move_camera":
            graph_3d.enter_3d(
                self.scene,
                phi=float(action["phi"]),
                theta=float(action["theta"]),
                run_time=float(action.get("run_time", 1)),
            )
            self.stage.mode = "3d"
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
                    stmt.play_write_statement(self.scene, self.mobjects[tid], place=False)
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

    def _instruction_content(self) -> list[VMobject]:
        return [self.mobjects[i] for i in self.on_screen if i in self.mobjects]

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
        elif otype == "plane":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, ThreeDAxes)
            mob = graph_3d.build_plane(obj, axes, color=color)
        elif otype == "polygon":
            axes = self.mobjects[obj["axes"]]
            assert isinstance(axes, Axes)
            mob = graph_2d.build_polygon(obj, axes, color=color)
        elif otype == "dot":
            if "axes" in obj:
                axes = self.mobjects[obj["axes"]]
                if isinstance(axes, ThreeDAxes):
                    mob = graph_3d.build_axes3d_dot(obj, axes, color=color)
                else:
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
            self.stage.fit(mob, self.stage.content())
            return mob
        else:
            raise RuntimeError(otype)

        if "next_to" not in obj:
            self._place(mob, obj)
        return mob

    def _endpoints(self, obj: dict[str, Any]):
        if "axes" in obj:
            axes = self.mobjects[obj["axes"]]
            start = list(obj["start"])
            end = list(obj["end"])
            if isinstance(axes, ThreeDAxes):
                while len(start) < 3:
                    start.append(0.0)
                while len(end) < 3:
                    end.append(0.0)
                return axes.c2p(*start[:3]), axes.c2p(*end[:3])
            assert isinstance(axes, Axes)
            return axes.c2p(*start[:2]), axes.c2p(*end[:2])
        return (
            float(obj["start"][0]) * RIGHT + float(obj["start"][1]) * UP,
            float(obj["end"][0]) * RIGHT + float(obj["end"][1]) * UP,
        )

    def _place(self, mob: VMobject, obj: dict[str, Any]) -> None:
        if obj["type"] == "math" and self._board_scene:
            # Board playback owns absolute placement (anchor + derive/fork).
            return
        if obj["type"] in {"plot", "surface", "plane", "polygon", "flow_field"}:
            return
        if obj["type"] == "dot" and ("axes" in obj or "number_line" in obj):
            return
        if obj["type"] in {"line", "arrow"}:
            return
        if obj["type"] == "axes3d":
            # Built at origin; conductor fits the whole scene into content().
            return
        if obj["type"] == "axes":
            at = obj.get("at", "center")
            if isinstance(at, str):
                self.stage.place(mob, at=at)
            else:
                # Explicit coords still honored for rare overrides.
                mob.move_to(float(at[0]) * RIGHT + float(at[1]) * UP)
            return
        at = obj.get("at", "center")
        self.stage.place(mob, at=at if isinstance(at, (str, list, tuple)) else "center")

    def _color(self, name: str):
        if isinstance(name, str) and name.startswith("#"):
            return name
        return COLORS.get(str(name).lower(), COLORS["white"])
