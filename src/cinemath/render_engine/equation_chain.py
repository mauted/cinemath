"""Equation-board playback: chains plus simple forks for case splits."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from manim import (
    DOWN,
    FadeIn,
    FadeOut,
    MathTex,
    ReplacementTransform,
    RIGHT,
    ThreeDScene,
    TransformMatchingTex,
    UP,
    VMobject,
    Write,
    rate_functions,
)

from cinemath.render_engine.stage import Region

_LINE_BUFF = 0.62
_FORK_BUFF = 0.75
_FORK_GAP = 1.0
_FORK_MIN_GAP = 0.65
_FORK_SIDE_BUFF = 0.2
_SCROLL_RUN_TIME = 0.48
_FORK_FULL_MAX_W = 7.0
_ANCHOR_TOP_BUFF = 0.28


class EquationBoard:
    """Continuous algebra board with chain and fork layout.

    Absolute stage bounds come from ``content_region`` (StageConductor).
    This class only owns relative structure: next_to, fork fan, scroll.
    """

    def __init__(
        self,
        scene: ThreeDScene,
        *,
        mobjects: dict[str, VMobject],
        on_screen: set[str],
        content_region: Callable[[], Region],
        accent_color: Callable[[], Any],
    ) -> None:
        self.scene = scene
        self.mobjects = mobjects
        self.on_screen = on_screen
        self._content_region = content_region
        self._accent_color = accent_color
        self.stack: list[str] = []
        self._branch_id: dict[str, str] = {}

    def clear(self) -> None:
        self.stack.clear()
        self._branch_id.clear()

    def discard(self, ids: set[str] | list[str]) -> None:
        drop = set(ids)
        self.stack = [i for i in self.stack if i not in drop]

    def track_write(self, target_ids: list[str]) -> None:
        for tid in target_ids:
            mob = self.mobjects.get(tid)
            if tid not in self.stack and isinstance(mob, MathTex):
                self.stack.append(tid)
        self._fit_after_write()

    def write(self, target_ids: list[str]) -> None:
        mobs = [self.mobjects[t] for t in target_ids]
        for mob in mobs:
            if not self.stack:
                self._anchor_line(mob)
            self._scroll_if_below(mob, extra=[mob])
        self.scene.play(*[Write(m) for m in mobs], run_time=0.65)
        self.on_screen.update(target_ids)
        self.track_write(target_ids)

    def _anchor_line(self, mob: VMobject) -> None:
        """Place the first visible line at the top of the board band."""
        region = self._content_region()
        y = region.top - _ANCHOR_TOP_BUFF - float(mob.height) / 2
        mob.move_to([float(region.center[0]), y, 0.0])

    def derive(self, src_id: str, dst_id: str, *, buff: float = _LINE_BUFF) -> None:
        src = self.mobjects[src_id]
        dst = self.mobjects[dst_id]

        dst.set_opacity(0)
        branch = self._branch_id.get(src_id)
        self._make_room_for(src, dst, buff=buff)
        if branch:
            self._branch_id[dst_id] = branch
            self._repack_branch_columns(animate=False, pending={dst_id: dst})

        if not isinstance(src, MathTex) or not isinstance(dst, MathTex):
            dst.set_opacity(1)
            self.scene.play(FadeIn(dst), run_time=0.5)
        else:
            dst.set_opacity(1)
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
                    run_time=1.05,
                    rate_func=rate_functions.smooth,
                )
            except Exception:
                ghost.move_to(dst.get_center())
                dst.set_opacity(1)
                self.scene.play(
                    ReplacementTransform(ghost, dst),
                    run_time=0.85,
                    rate_func=rate_functions.smooth,
                )

        self.on_screen.add(dst_id)
        if dst_id not in self.stack:
            self.stack.append(dst_id)
        if src_id in self.on_screen:
            self.scene.play(src.animate.set_opacity(0.4), run_time=0.2)
        self._repack_branch_columns(animate=True)
        self._fit_after_write()

    def fork(self, src_id: str, dst_ids: list[str], *, buff: float = _FORK_BUFF) -> None:
        src = self.mobjects[src_id]
        dsts = [self.mobjects[dst_id] for dst_id in dst_ids]
        if not dsts:
            return

        for dst in dsts:
            dst.set_opacity(0)
        self._make_room_for_fork(src, dsts, buff=buff)
        pending = {dst_id: self.mobjects[dst_id] for dst_id in dst_ids}
        for dst_id in dst_ids:
            self._branch_id[dst_id] = dst_id
        self._repack_branch_columns(animate=False, pending=pending)

        ghosts: list[VMobject] = []
        anims = []
        for dst in dsts:
            if isinstance(src, MathTex) and isinstance(dst, MathTex):
                dst.set_opacity(1)
                ghost = src.copy().set_opacity(1.0)
                ghost.move_to(src.get_center())
                ghosts.append(ghost)
                self.scene.add(ghost)
                anims.append(ReplacementTransform(ghost, dst))
            else:
                dst.set_opacity(1)
                anims.append(FadeIn(dst))
        self.scene.play(*anims, run_time=0.9, rate_func=rate_functions.smooth)

        for dst_id in dst_ids:
            self.on_screen.add(dst_id)
            if dst_id not in self.stack:
                self.stack.append(dst_id)
        if src_id in self.on_screen:
            self.scene.play(src.animate.set_opacity(0.4), run_time=0.2)
        self._repack_branch_columns(animate=True)
        self._fit_after_write()

    def _bounds(self) -> tuple[float, float]:
        region = self._content_region()
        return region.bottom, region.top

    def _visible(self) -> list[str]:
        return [i for i in self.stack if i in self.mobjects and i in self.on_screen]

    def _shift_group(
        self,
        dy: float,
        *,
        extra: list[VMobject] | None = None,
        run_time: float = _SCROLL_RUN_TIME,
    ) -> None:
        if abs(dy) < 0.01:
            return
        on_screen_mobs = {self.mobjects[i] for i in self._visible()}
        animate: list[VMobject] = list(on_screen_mobs)
        if extra:
            for mob in extra:
                if mob is None:
                    continue
                if mob in on_screen_mobs:
                    if mob not in animate:
                        animate.append(mob)
                else:
                    # Layout-only targets must not flash on screen before reveal.
                    mob.shift(UP * dy)
        if not animate:
            return
        self.scene.play(
            *[m.animate.shift(UP * dy) for m in animate],
            run_time=run_time,
            rate_func=rate_functions.smooth,
        )

    def _make_room_for(self, src: VMobject, dst: VMobject, *, buff: float) -> None:
        safe_bottom, safe_top = self._bounds()
        for _ in range(8):
            dst.next_to(src, DOWN, buff=buff)
            overflow = safe_bottom - float(dst.get_bottom()[1])
            if overflow <= 0.01:
                return
            visible = self._visible()
            if not visible:
                self._shift_group(overflow, extra=[src, dst])
                dst.next_to(src, DOWN, buff=buff)
                return
            tops_after = [float(self.mobjects[i].get_top()[1]) + overflow for i in visible]
            if max(tops_after) > safe_top and len(visible) > 1:
                self._fade_oldest()
                continue
            self._shift_group(overflow, extra=[dst])
            dst.next_to(src, DOWN, buff=buff)
            return

    def _make_room_for_fork(self, src: VMobject, dsts: list[VMobject], *, buff: float) -> None:
        safe_bottom, safe_top = self._bounds()
        for _ in range(8):
            self._place_fork_children(src, dsts, buff=buff)
            overflow = max(safe_bottom - float(dst.get_bottom()[1]) for dst in dsts)
            if overflow <= 0.01:
                return
            visible = self._visible()
            if not visible:
                self._shift_group(overflow, extra=[src, *dsts])
                self._place_fork_children(src, dsts, buff=buff)
                return
            tops_after = [float(self.mobjects[i].get_top()[1]) + overflow for i in visible]
            if max(tops_after) > safe_top and len(visible) > 1:
                self._fade_oldest()
                continue
            self._shift_group(overflow, extra=dsts)
            self._place_fork_children(src, dsts, buff=buff)
            return

    def _place_fork_children(self, src: VMobject, dsts: list[VMobject], *, buff: float) -> None:
        region = self._content_region()
        max_width = self._fork_span(region)
        base_y = float(src.get_bottom()[1]) - buff
        for dst in dsts:
            dst.move_to([float(src.get_center()[0]), base_y - float(dst.height) / 2, 0.0])
        self._layout_branch_columns(
            [dst for dst in dsts],
            region=region,
            max_width=max_width,
            center_x=float(src.get_center()[0]),
        )

    def _fork_span(self, region: Region) -> float:
        if region.center[0] > 0.5:
            return region.max_w
        return min(region.max_w, _FORK_FULL_MAX_W)

    def _branch_columns(
        self,
        pending: dict[str, VMobject] | None = None,
    ) -> dict[str, list[VMobject]]:
        columns: dict[str, list[VMobject]] = {}
        seen: set[str] = set()
        for eid in self._visible():
            seen.add(eid)
            root = self._branch_id.get(eid)
            if not root:
                continue
            columns.setdefault(root, []).append(self.mobjects[eid])
        if pending:
            for eid, mob in pending.items():
                if eid in seen:
                    continue
                root = self._branch_id.get(eid)
                if not root:
                    continue
                columns.setdefault(root, []).append(mob)
        return columns

    def _layout_branch_columns(
        self,
        roots: list[VMobject],
        *,
        region: Region,
        max_width: float,
        center_x: float,
    ) -> None:
        """Pack parallel branch columns side-by-side with guaranteed gap."""
        if not roots:
            return
        if len(roots) == 1:
            roots[0].set_x(center_x)
            return

        widths = [max(float(mob.width), 0.5) for mob in roots]
        n = len(roots)
        gap = _FORK_GAP
        total = sum(widths) + gap * (n - 1)
        if total > max_width:
            gap = max(_FORK_MIN_GAP, (max_width - sum(widths)) / (n - 1))
            total = sum(widths) + gap * (n - 1)

        left_limit = region.left + _FORK_SIDE_BUFF
        right_limit = region.right - _FORK_SIDE_BUFF
        span = min(max_width, right_limit - left_limit)
        if total > span:
            gap = max(_FORK_MIN_GAP, (span - sum(widths)) / (n - 1))
            total = sum(widths) + gap * (n - 1)

        cursor = center_x - total / 2
        for width, mob in zip(widths, roots, strict=False):
            mob.set_x(cursor + width / 2)
            cursor += width + gap

    def _repack_branch_columns(
        self,
        *,
        animate: bool = False,
        pending: dict[str, VMobject] | None = None,
    ) -> None:
        """Re-space whole branch columns after a leaf grows wider or taller."""
        columns = self._branch_columns(pending)
        if len(columns) < 2:
            return

        region = self._content_region()
        max_width = self._fork_span(region)
        roots = [self.mobjects[root_id] for root_id in columns if root_id in self.mobjects]
        if len(roots) < 2:
            return

        # Snapshot column boxes before shifting.
        col_data: list[tuple[str, list[VMobject], float, float]] = []
        for root_id, mobs in columns.items():
            left = min(float(m.get_left()[0]) for m in mobs)
            right = max(float(m.get_right()[0]) for m in mobs)
            cx = (left + right) / 2
            col_data.append((root_id, mobs, right - left, cx))
        col_data.sort(key=lambda item: item[3])

        widths = [max(w, 0.5) for _, _, w, _ in col_data]
        n = len(col_data)
        gap = _FORK_GAP
        total = sum(widths) + gap * (n - 1)
        if total > max_width:
            gap = max(_FORK_MIN_GAP, (max_width - sum(widths)) / (n - 1))
            total = sum(widths) + gap * (n - 1)

        center_x = float(region.center[0])
        cursor = center_x - total / 2
        shifts: list[tuple[VMobject, float]] = []
        for width, (_, mobs, _, old_cx) in zip(widths, col_data, strict=False):
            new_cx = cursor + width / 2
            dx = new_cx - old_cx
            if abs(dx) > 0.01:
                for mob in mobs:
                    shifts.append((mob, dx))
            cursor += width + gap

        if not shifts:
            return
        if animate:
            self.scene.play(
                *[mob.animate.shift(RIGHT * dx) for mob, dx in shifts],
                run_time=0.28,
                rate_func=rate_functions.smooth,
            )
        else:
            for mob, dx in shifts:
                mob.shift(RIGHT * dx)

    def _scroll_if_below(self, mob: VMobject, *, extra: list[VMobject] | None = None) -> None:
        safe_bottom, _ = self._bounds()
        overflow = safe_bottom - float(mob.get_bottom()[1])
        if overflow <= 0.01:
            return
        extras = list(extra or [])
        if mob not in extras:
            extras.append(mob)
        self._shift_group(overflow, extra=extras)

    def _fit_after_write(self) -> None:
        safe_bottom, safe_top = self._bounds()
        visible = self._visible()
        if not visible:
            return
        lowest = min(float(self.mobjects[i].get_bottom()[1]) for i in visible)
        if lowest < safe_bottom:
            self._shift_group(safe_bottom - lowest)
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
        self._branch_id.pop(old_id, None)
        if also_scroll_to is not None:
            visible = self._visible()
            if visible:
                lowest = min(float(self.mobjects[i].get_bottom()[1]) for i in visible)
                if lowest < also_scroll_to:
                    shift = also_scroll_to - lowest
                    anims.extend(self.mobjects[i].animate.shift(UP * shift) for i in visible)
        if anims:
            self.scene.play(*anims, run_time=0.35, rate_func=rate_functions.smooth)


EquationChain = EquationBoard
