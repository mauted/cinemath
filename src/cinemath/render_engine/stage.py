"""Stage geometry and StageConductor — the one place that owns absolute layout."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

from manim import DOWN, LEFT, RIGHT, UP, FadeIn, FadeOut, ThreeDScene, VGroup, VMobject

# ---------------------------------------------------------------------------
# Shared frame geometry (single source of truth)
# ---------------------------------------------------------------------------

FRAME_LEFT = -6.95
FRAME_RIGHT = 6.95
FRAME_BOTTOM = -3.55
FRAME_TOP = 3.85

HALF_CENTER_X = 3.35
HALF_SPLIT_X = 0.25
HALF_MAX_W = 5.7
HALF_MAX_H = 6.2
FULL_MAX_W = 12.8
FULL_MAX_H = 6.2

CAPTION_CEILING = 2.7
CAPTION_GAP = 0.78
CAPTION_TOP_BUFF = 0.2
LEFT_PANEL_OPACITY = 0.55

# Equation-board scroll bands (content region, before caption clamp).
BOARD_FULL_BOTTOM = -2.35
BOARD_FULL_TOP = 1.35
BOARD_RIGHT_BOTTOM = -2.2
BOARD_RIGHT_TOP = 1.15

SLOT_COORDS: dict[str, tuple[float, float]] = {
    "title": (0.0, 2.15),
    "center": (0.0, -0.15),
    "upper": (0.0, 1.15),
    "lower": (0.0, -2.15),
    "left": (-3.2, -0.1),
    "right": (3.2, -0.1),
    "ul": (-3.4, 1.6),
    "ur": (3.4, 1.6),
    "ll": (-3.4, -2.3),
    "lr": (3.4, -2.3),
}

PlacePolicy = Literal["center", "slot", "keep"]


@dataclass(frozen=True)
class Region:
    """Axis-aligned stage rectangle in Manim scene units."""

    center: tuple[float, float]
    max_w: float
    max_h: float
    left: float
    right: float
    bottom: float
    top: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom


def full_frame() -> Region:
    return Region(
        center=(0.0, 0.0),
        max_w=FULL_MAX_W,
        max_h=FULL_MAX_H,
        left=FRAME_LEFT,
        right=FRAME_RIGHT,
        bottom=FRAME_BOTTOM,
        top=FRAME_TOP,
    )


def right_active() -> Region:
    return Region(
        center=(HALF_CENTER_X, 0.0),
        max_w=HALF_MAX_W,
        max_h=HALF_MAX_H,
        left=HALF_SPLIT_X,
        right=FRAME_RIGHT,
        bottom=FRAME_BOTTOM,
        top=FRAME_TOP,
    )


def left_archive() -> Region:
    return Region(
        center=(-HALF_CENTER_X, 0.0),
        max_w=HALF_MAX_W,
        max_h=HALF_MAX_H,
        left=FRAME_LEFT,
        right=-HALF_SPLIT_X,
        bottom=FRAME_BOTTOM,
        top=FRAME_TOP,
    )


def board_band(*, right_stage: bool) -> Region:
    """Vertical band used by the equation board for scroll clamps."""
    if right_stage:
        return Region(
            center=(HALF_CENTER_X, (BOARD_RIGHT_BOTTOM + BOARD_RIGHT_TOP) / 2),
            max_w=HALF_MAX_W,
            max_h=BOARD_RIGHT_TOP - BOARD_RIGHT_BOTTOM,
            left=HALF_SPLIT_X,
            right=FRAME_RIGHT,
            bottom=BOARD_RIGHT_BOTTOM,
            top=BOARD_RIGHT_TOP,
        )
    return Region(
        center=(0.0, (BOARD_FULL_BOTTOM + BOARD_FULL_TOP) / 2),
        max_w=FULL_MAX_W,
        max_h=BOARD_FULL_TOP - BOARD_FULL_BOTTOM,
        left=FRAME_LEFT,
        right=FRAME_RIGHT,
        bottom=BOARD_FULL_BOTTOM,
        top=BOARD_FULL_TOP,
    )


class StageConductor:
    """Owns absolute placement, half-stage pin/swipe, and caption lifecycle."""

    def __init__(self, scene: ThreeDScene) -> None:
        self.scene = scene
        self.caption_mob: VMobject | None = None
        self.left_panel: VMobject | None = None
        self.use_right_stage = False
        self.mode = "2d"
        self._pin_caption_top = False

    # --- regions ---------------------------------------------------------

    def content(self) -> Region:
        if self.use_right_stage and self.mode != "3d":
            return right_active()
        return full_frame()

    def archive_left(self) -> Region:
        return left_archive()

    def caption_band(self) -> Region:
        region = self.content()
        return Region(
            center=(region.center[0], (CAPTION_CEILING + FRAME_TOP) / 2),
            max_w=region.max_w,
            max_h=FRAME_TOP - CAPTION_CEILING,
            left=region.left,
            right=region.right,
            bottom=CAPTION_CEILING,
            top=FRAME_TOP,
        )

    def board_region(self) -> Region:
        """Content band for equation-board scroll; shrinks under a pinned caption."""
        base = board_band(right_stage=self.use_right_stage and self.mode != "3d")
        top = base.top
        if self._pin_caption_top and self.caption_mob is not None:
            top = min(top, float(self.caption_mob.get_bottom()[1]) - CAPTION_GAP)
        return Region(
            center=(base.center[0], (base.bottom + top) / 2),
            max_w=base.max_w,
            max_h=max(0.5, top - base.bottom),
            left=base.left,
            right=base.right,
            bottom=base.bottom,
            top=top,
        )

    # --- scene lifecycle -------------------------------------------------

    def begin_scene(self, *, pin_caption_top: bool = False) -> None:
        self.caption_mob = None
        self.use_right_stage = self.left_panel is not None
        self._pin_caption_top = pin_caption_top

    def release_left_for_3d(self) -> None:
        if self.left_panel is None:
            return
        self.scene.play(FadeOut(self.left_panel, shift=LEFT * 0.4), run_time=0.4)
        self.left_panel = None
        self.use_right_stage = False

    # --- placement -------------------------------------------------------

    def place(
        self,
        mob: VMobject,
        *,
        at: str | list[float] | tuple[float, float] | None = "center",
        region: Region | None = None,
        policy: PlacePolicy = "slot",
    ) -> None:
        if policy == "keep":
            return
        target = region or self.content()
        if policy == "center" or at is None:
            mob.move_to(float(target.center[0]) * RIGHT + float(target.center[1]) * UP)
            return
        if isinstance(at, str):
            if self.use_right_stage and self.mode != "3d" and at in {"center", "title", "upper", "lower"}:
                # Soft hints in half-stage: keep X on the active column.
                y = SLOT_COORDS.get(at, (0.0, 0.0))[1]
                mob.move_to(HALF_CENTER_X * RIGHT + y * UP)
            else:
                x, y = SLOT_COORDS.get(at, SLOT_COORDS["center"])
                mob.move_to(x * RIGHT + y * UP)
            return
        mob.move_to(float(at[0]) * RIGHT + float(at[1]) * UP)

    def fit(self, group: VMobject, region: Region | None = None, *, max_scale: float = 1.0) -> None:
        region = region or self.content()
        w = max(float(group.width), 1e-3)
        h = max(float(group.height), 1e-3)
        scale = min(region.max_w / w, region.max_h / h, max_scale)
        if scale < 0.999:
            group.scale(scale)
        group.move_to(float(region.center[0]) * RIGHT + float(region.center[1]) * UP)

    def fit_active_if_split(self, group: VMobject) -> None:
        if self.use_right_stage and self.mode != "3d" and group.submobjects:
            self.fit(group, self.content())

    def separate_labels_from_chrome(
        self,
        labels: Sequence[VMobject],
        chrome: Sequence[VMobject],
        *,
        buff: float = 0.45,
    ) -> None:
        if not labels or not chrome:
            return
        chrome_group = VGroup(*chrome)

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

        highest_label = max(float(lab.get_top()[1]) for lab in labels)
        if highest_label > CAPTION_CEILING:
            drop = highest_label - CAPTION_CEILING + 0.15
            chrome_group.shift(DOWN * drop)
            for lab in labels:
                if any(_overlaps(lab, c, pad=0.05) for c in chrome):
                    lab.next_to(chrome_group, UP, buff=buff)

    # --- captions --------------------------------------------------------

    def show_caption(self, text: str, *, color: Any, content: Sequence[VMobject] | None = None) -> None:
        from cinemath.render_engine import instructions as instr

        region = self.content()
        half = self.use_right_stage and self.mode != "3d"
        self.caption_mob = instr.build_instruction(
            text,
            color=color,
            max_width_cm=6.6 if half else 11.8,
        )
        instr.place_instruction(
            self.caption_mob,
            region=region,
            content=None if self._pin_caption_top else content,
            pin_top=self._pin_caption_top,
        )
        self.scene.play(FadeIn(self.caption_mob), run_time=0.35)

    def set_caption(self, text: str, *, color: Any, content: Sequence[VMobject] | None = None) -> None:
        from cinemath.render_engine import instructions as instr

        self.caption_mob = instr.play_set_instruction(
            self.scene,
            self.caption_mob,
            text,
            color=color,
            region=self.content(),
            content=None if self._pin_caption_top else content,
            pin_top=self._pin_caption_top,
        )

    def fade_caption(self) -> list[Any]:
        if self.caption_mob is None:
            return []
        anim = FadeOut(self.caption_mob, shift=UP * 0.15)
        self.caption_mob = None
        return [anim]

    # --- half-stage pin / clear ------------------------------------------

    def pin_active_to_left(self, pieces: Sequence[VMobject]) -> None:
        anims = self.fade_caption()
        if not pieces:
            if anims:
                self.scene.play(*anims, run_time=0.35)
            return

        group = VGroup(*pieces)
        region = self.archive_left()
        w = max(float(group.width), 1e-3)
        h = max(float(group.height), 1e-3)
        scale = min(region.max_w / w, region.max_h / h, 1.0)

        if self.left_panel is not None:
            anims.append(FadeOut(self.left_panel, shift=LEFT * 0.6))
        anims.append(
            group.animate.scale(scale).move_to(
                float(region.center[0]) * RIGHT + float(region.center[1]) * UP
            )
        )
        self.scene.play(*anims, run_time=0.75)
        self._apply_panel_dim(group, LEFT_PANEL_OPACITY)
        self.left_panel = group
        self.scene.wait(0.12)

    def clear_active(self, pieces: Sequence[VMobject]) -> None:
        fade = list(pieces)
        if self.caption_mob is not None:
            fade.append(self.caption_mob)
        if fade:
            self.scene.play(*[FadeOut(m) for m in fade], run_time=0.45)
        self.caption_mob = None

    def clear_left_panel(self) -> list[Any]:
        if self.left_panel is None:
            return []
        anim = FadeOut(self.left_panel)
        self.left_panel = None
        return [anim]

    def _apply_panel_dim(self, mob: VMobject, opacity: float) -> None:
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
