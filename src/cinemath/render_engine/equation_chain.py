"""Equation-chain board playback: scroll to make room, then write/morph the next line."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from manim import (
    DOWN,
    UP,
    FadeIn,
    FadeOut,
    Indicate,
    MathTex,
    ReplacementTransform,
    ThreeDScene,
    TransformMatchingTex,
    VMobject,
    Write,
)

# Leave extra headroom for larger multi-line instruction banners.
_SAFE_BOTTOM = -3.2
_SAFE_TOP = 1.75
_RIGHT_SAFE_BOTTOM = -3.05
_RIGHT_SAFE_TOP = 1.55


class EquationChain:
    """
    Continuous algebra board: dim prior line, copy underneath, morph mismatches.

    Room is made *before* the next equation appears — scroll (and drop oldest
    lines if needed), then write/morph into the cleared space.
    """

    def __init__(
        self,
        scene: ThreeDScene,
        *,
        mobjects: dict[str, VMobject],
        on_screen: set[str],
        use_right_stage: Callable[[], bool],
        accent_color: Callable[[], Any],
    ) -> None:
        self.scene = scene
        self.mobjects = mobjects
        self.on_screen = on_screen
        self._use_right_stage = use_right_stage
        self._accent_color = accent_color
        self.stack: list[str] = []

    def clear(self) -> None:
        self.stack.clear()

    def discard(self, ids: set[str] | list[str]) -> None:
        drop = set(ids)
        self.stack = [i for i in self.stack if i not in drop]

    def track_write(self, target_ids: list[str]) -> None:
        """After a plain Write of math, register lines and keep the board in frame."""
        for tid in target_ids:
            mob = self.mobjects.get(tid)
            if tid not in self.stack and isinstance(mob, MathTex):
                self.stack.append(tid)
        self._fit_after_write()

    def derive(self, src_id: str, dst_id: str, *, buff: float = 0.55) -> None:
        """Make room below src, then morph a copy of src into dst."""
        src = self.mobjects[src_id]
        dst = self.mobjects[dst_id]

        self.scene.play(src.animate.set_opacity(0.4), run_time=0.3)
        self._make_room_for(src, dst, buff=buff)

        if not isinstance(src, MathTex) or not isinstance(dst, MathTex):
            self.scene.play(FadeIn(dst), run_time=0.5)
            self.on_screen.add(dst_id)
            if dst_id not in self.stack:
                self.stack.append(dst_id)
            return

        ghost = src.copy().set_opacity(1.0)
        self.scene.add(ghost)
        try:
            self.scene.play(
                TransformMatchingTex(
                    ghost,
                    dst,
                    transform_mismatches=True,
                    fade_transform_mismatches=True,
                ),
                run_time=1.15,
            )
        except Exception:
            ghost.move_to(dst.get_center())
            self.scene.play(ReplacementTransform(ghost, dst), run_time=0.9)

        self.on_screen.add(dst_id)
        if dst_id not in self.stack:
            self.stack.append(dst_id)
        self.scene.play(
            Indicate(dst, color=self._accent_color(), scale_factor=1.05),
            run_time=0.45,
        )

    def write(self, target_ids: list[str]) -> None:
        """Write math onto the board, scrolling first if the seed line would clip."""
        mobs = [self.mobjects[t] for t in target_ids]
        # If any target already sits below the floor, lift existing stack first.
        for mob in mobs:
            self._scroll_if_below(mob)
        self.scene.play(*[Write(m) for m in mobs])
        self.on_screen.update(target_ids)
        self.track_write(target_ids)

    # --- layout helpers -------------------------------------------------

    def _bounds(self) -> tuple[float, float]:
        if self._use_right_stage():
            return _RIGHT_SAFE_BOTTOM, _RIGHT_SAFE_TOP
        return _SAFE_BOTTOM, _SAFE_TOP

    def _visible(self) -> list[str]:
        return [i for i in self.stack if i in self.mobjects and i in self.on_screen]

    def _make_room_for(self, src: VMobject, dst: VMobject, *, buff: float) -> None:
        """Scroll / drop lines until dst fits below src, then place dst."""
        safe_bottom, safe_top = self._bounds()

        for _ in range(8):
            dst.next_to(src, DOWN, buff=buff)
            overflow = safe_bottom - float(dst.get_bottom()[1])
            if overflow <= 0.01:
                return

            visible = self._visible()
            if not visible:
                dst.shift(UP * overflow)
                return

            # Prefer dropping an old line over pushing the stack into the caption.
            tops_after = [float(self.mobjects[i].get_top()[1]) + overflow for i in visible]
            if max(tops_after) > safe_top and len(visible) > 1:
                self._fade_oldest()
                continue

            self.scene.play(
                *[self.mobjects[i].animate.shift(UP * overflow) for i in visible],
                run_time=0.4,
            )
            dst.next_to(src, DOWN, buff=buff)
            return

    def _scroll_if_below(self, mob: VMobject) -> None:
        safe_bottom, _ = self._bounds()
        overflow = safe_bottom - float(mob.get_bottom()[1])
        if overflow <= 0.01:
            return
        visible = self._visible()
        if visible:
            self.scene.play(
                *[self.mobjects[i].animate.shift(UP * overflow) for i in visible],
                run_time=0.35,
            )
        mob.shift(UP * overflow)

    def _fit_after_write(self) -> None:
        """Safety net if a write somehow still clips (should be rare)."""
        safe_bottom, safe_top = self._bounds()
        visible = self._visible()
        if not visible:
            return
        lowest = min(float(self.mobjects[i].get_bottom()[1]) for i in visible)
        if lowest < safe_bottom:
            shift = safe_bottom - lowest
            self.scene.play(
                *[self.mobjects[i].animate.shift(UP * shift) for i in visible],
                run_time=0.35,
            )
        while len(self._visible()) > 2:
            visible = self._visible()
            tops = [float(self.mobjects[i].get_top()[1]) for i in visible]
            bottoms = [float(self.mobjects[i].get_bottom()[1]) for i in visible]
            if max(tops) <= safe_top and min(bottoms) >= safe_bottom - 0.02:
                break
            self._fade_oldest(also_scroll_to=safe_bottom)

    def _fade_oldest(self, *, also_scroll_to: float | None = None) -> None:
        if not self.stack:
            return
        old_id = self.stack.pop(0)
        anims = []
        if old_id in self.mobjects and old_id in self.on_screen:
            anims.append(FadeOut(self.mobjects[old_id], shift=UP * 0.2))
            self.on_screen.discard(old_id)
        if also_scroll_to is not None:
            visible = self._visible()
            if visible:
                lowest = min(float(self.mobjects[i].get_bottom()[1]) for i in visible)
                if lowest < also_scroll_to:
                    shift = also_scroll_to - lowest
                    anims.extend(self.mobjects[i].animate.shift(UP * shift) for i in visible)
        if anims:
            self.scene.play(*anims, run_time=0.35)
