"""CLI: `cinemath solve <input>`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from cinemath import __version__
from cinemath.api import JobContext, generate_lesson
from cinemath.api.models import GenerationOptions, ProblemInput
from cinemath.core.logger import configure, fmt_path, get_logger

app = typer.Typer(
    name="cinemath",
    help="LLM teaches the math; local templates build the Manim animation.",
    add_completion=False,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", callback=_version_callback, is_eager=True
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging."),
) -> None:
    load_dotenv()
    configure(level="DEBUG" if verbose else None)


@app.command("solve")
def solve(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to .txt, .md, or image of the math problem.",
    ),
    out: Optional[Path] = typer.Option(None, "--out", "-o", help="Output root (default ./outputs)."),
    quality: str = typer.Option("m", "--quality", "-q", help="Manim quality: l (480p15), m (720p60), h (1080p60)."),
    skip_render: bool = typer.Option(False, "--skip-render", help="Write plan/animation JSON only."),
    keep_media: bool = typer.Option(
        False, "--keep-media", help="Keep Manim cache (media/) in the run directory."
    ),
) -> None:
    """Teach a problem with the LLM, then animate it with local templates."""
    log = get_logger("cli")
    log.info("solve %s", fmt_path(input_path))
    context = JobContext(job_id="cli", attempt_id=input_path.stem)
    try:
        result = generate_lesson(
            ProblemInput(source_path=input_path.resolve()),
            context=context,
            options=GenerationOptions(
                output_root=out.resolve() if out else None,
                quality=quality,
                skip_render=skip_render,
                keep_media=keep_media,
            ),
        )
    except Exception as exc:
        log.error("failed: %s", exc)
        raise typer.Exit(code=1) from exc

    log.info("done — %s", fmt_path(result.run_dir))
    log.info("  plan:       %s", fmt_path(result.plan_path))
    if result.verification is not None:
        log.info("  verify:     %s", result.verification.status.value)
    else:
        log.info("  verify:     (skipped)")
    log.info("  animation:  %s", fmt_path(result.animation_path))
    if skip_render:
        log.info("  video:      (skipped)")
    else:
        log.info("  video:      %s", fmt_path(result.video_path))
    log.info("  engine:     %s (schema %s)", result.manifest.engine_version, result.manifest.schema_version)


if __name__ == "__main__":
    app()
