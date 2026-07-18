"""Central logging for cinemath — configure once, import get_logger elsewhere."""

from __future__ import annotations

import logging
import os
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_ROOT_NAME = "cinemath"
_CONFIGURED = False
_USE_COLOR = False
_LINK_PATHS = False
_DATEFMT = "%H:%M:%S"
_QUIET_LOGGERS = ("httpx", "httpcore", "anthropic", "manim")

_RESET = "\033[0m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_COLORS = {
    "DEBUG": "\033[36m",  # cyan
    "INFO": "\033[32m",  # green
    "WARNING": "\033[33m",  # yellow
    "ERROR": "\033[31m",  # red
    "CRITICAL": "\033[1;31m",  # bold red
    "TIME": "\033[90m",  # gray
    "NAME": "\033[35m",  # magenta
    "PATH": "\033[36m",  # cyan
    "MSG": "\033[0m",
    "STEP_START": "\033[34m",  # blue
    "STEP_OK": "\033[32m",
    "STEP_FAIL": "\033[31m",
}


def configure(
    *,
    level: str | int | None = None,
    color: bool | None = None,
    links: bool | None = None,
) -> None:
    """Attach a console handler to the cinemath logger tree."""
    global _CONFIGURED, _USE_COLOR, _LINK_PATHS
    resolved = _resolve_level(level)
    _USE_COLOR = _use_color(color)
    _LINK_PATHS = _use_path_links() if links is None else links
    root = logging.getLogger(_ROOT_NAME)
    if not _CONFIGURED:
        root.handlers.clear()
        root.propagate = False
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(_ColorFormatter(use_color=_USE_COLOR))
        root.addHandler(handler)
        for name in _QUIET_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)
        _CONFIGURED = True
    root.setLevel(resolved)


def get_logger(name: str) -> logging.Logger:
    """Return ``cinemath.<name>`` logger, configuring defaults on first use."""
    if not _CONFIGURED:
        configure()
    return logging.getLogger(f"{_ROOT_NAME}.{name}")


def fmt_path(path: Path | str) -> str:
    """Short, terminal-clickable path (OSC-8 hyperlink when supported)."""
    resolved = _resolve_path(path)
    display = _short_display(resolved)
    if _LINK_PATHS:
        return _osc8_link(resolved.as_uri(), display, colored=_USE_COLOR)
    return display


def _resolve_path(path: Path | str) -> Path:
    p = Path(path).expanduser()
    try:
        return p.resolve()
    except OSError:
        return p.absolute()


def _short_display(path: Path) -> str:
    cwd = Path.cwd()
    try:
        rel = path.relative_to(cwd)
        parts = rel.parts
        if len(parts) >= 3 and parts[0] == "outputs":
            return f"outputs/…/{'/'.join(parts[2:])}"
        return rel.as_posix()
    except ValueError:
        pass
    home = Path.home()
    try:
        rel = path.relative_to(home)
        return f"~/{rel.as_posix()}"
    except ValueError:
        pass
    parts = path.parts
    if len(parts) >= 2:
        return f"…/{path.name}"
    return path.name


def _osc8_link(uri: str, label: str, *, colored: bool) -> str:
    text = f"{_COLORS['PATH']}{label}{_RESET}" if colored else label
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


def _use_path_links() -> bool:
    env = os.environ.get("CINEMATH_LOG_LINKS", "").strip().lower()
    if env in {"0", "false", "no", "off"}:
        return False
    if env in {"1", "true", "yes", "on"}:
        return True
    return hasattr(sys.stderr, "isatty") and bool(sys.stderr.isatty())


def _resolve_level(level: str | int | None) -> int:
    if level is None:
        level = os.environ.get("CINEMATH_LOG_LEVEL", "INFO")
    if isinstance(level, int):
        return level
    normalized = str(level).strip().upper()
    value = logging.getLevelNamesMapping().get(normalized)
    if value is None:
        raise ValueError(f"Unknown log level: {level!r}")
    return value


def _use_color(override: bool | None) -> bool:
    if override is not None:
        return override
    env = os.environ.get("CINEMATH_LOG_COLOR", "").strip().lower()
    if env in {"0", "false", "no", "off"}:
        return False
    if env in {"1", "true", "yes", "on"}:
        return True
    if os.environ.get("NO_COLOR"):
        return False
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


class _ColorFormatter(logging.Formatter):
    def __init__(self, *, use_color: bool) -> None:
        super().__init__(datefmt=_DATEFMT)
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, self.datefmt)
        level = record.levelname
        name = record.name.removeprefix(f"{_ROOT_NAME}.")
        message = record.getMessage()

        if self._use_color:
            message = _colorize_message(message)
            return (
                f"{_DIM}{ts}{_RESET} "
                f"{_COLORS.get(level, '')}{level:<5}{_RESET} "
                f"{_COLORS['NAME']}[{name}]{_RESET} "
                f"{message}"
            )
        return f"{ts} {level:<5} [{name}] {message}"


def _colorize_message(message: str) -> str:
    if message.startswith("→ "):
        return f"{_COLORS['STEP_START']}{message}{_RESET}"
    if message.startswith("✓ "):
        return f"{_COLORS['STEP_OK']}{message}{_RESET}"
    if message.startswith("✗ "):
        return f"{_COLORS['STEP_FAIL']}{message}{_RESET}"
    return message


@contextmanager
def log_step(logger: logging.Logger, label: str) -> Iterator[None]:
    """Log start/finish of a pipeline step with elapsed seconds."""
    logger.info("→ %s", label)
    started = time.perf_counter()
    try:
        yield
    except Exception:
        logger.exception("✗ %s failed after %.1fs", label, time.perf_counter() - started)
        raise
    else:
        logger.info("✓ %s (%.1fs)", label, time.perf_counter() - started)
