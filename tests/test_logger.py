"""Unit tests for cinemath logging."""

from __future__ import annotations

import logging
from pathlib import Path

from cinemath.logger import (
    _ColorFormatter,
    _short_display,
    configure,
    fmt_path,
    get_logger,
    log_step,
)


def test_get_logger_uses_cinemath_namespace() -> None:
    configure(level="INFO", color=False, links=False)
    assert get_logger("test").name == "cinemath.test"


def test_log_step_emits_start_and_finish(caplog) -> None:
    configure(level="INFO", color=False, links=False)
    logger = get_logger("test.step")
    with caplog.at_level(logging.INFO, logger="cinemath"):
        with log_step(logger, "demo step"):
            pass
    messages = [r.message for r in caplog.records if r.name.startswith("cinemath")]
    assert any("→ demo step" in m for m in messages)
    assert any("✓ demo step" in m for m in messages)


def test_color_formatter_includes_ansi_when_enabled() -> None:
    record = logging.LogRecord(
        name="cinemath.pipeline",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="→ compile animation",
        args=(),
        exc_info=None,
    )
    line = _ColorFormatter(use_color=True).format(record)
    assert "\033[" in line
    assert "pipeline" in line


def test_color_formatter_plain_when_disabled() -> None:
    record = logging.LogRecord(
        name="cinemath.pipeline",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    line = _ColorFormatter(use_color=False).format(record)
    assert "\033[" not in line
    assert "INFO" in line


def test_configure_color_false(monkeypatch) -> None:
    monkeypatch.setenv("CINEMATH_LOG_COLOR", "0")
    configure(level="INFO", color=False, links=False)
    handler = logging.getLogger("cinemath").handlers[0]
    assert isinstance(handler.formatter, _ColorFormatter)
    assert handler.formatter._use_color is False


def test_short_display_collapses_output_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run = tmp_path / "outputs" / "2026-07-18_023557_solve-for-x" / "plan.json"
    run.parent.mkdir(parents=True)
    run.touch()
    assert _short_display(run.resolve()) == "outputs/…/plan.json"


def test_fmt_path_plain_without_links(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configure(links=False, color=False)
    p = tmp_path / "examples" / "04.txt"
    p.parent.mkdir()
    p.touch()
    assert fmt_path(p) == "examples/04.txt"
    assert "\033]" not in fmt_path(p)


def test_fmt_path_osc8_when_links_enabled(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    configure(links=True, color=False)
    p = (tmp_path / "plan.json").resolve()
    p.touch()
    linked = fmt_path(p)
    assert "\033]8;;file://" in linked
    assert "plan.json" in linked
