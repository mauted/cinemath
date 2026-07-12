"""CLI: `mathanim solve <input>`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from mathanim import __version__
from mathanim.pipeline import run_pipeline

app = typer.Typer(
    name="mathanim",
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
) -> None:
    load_dotenv()


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
    quality: str = typer.Option("l", "--quality", "-q", help="Manim quality: l|m|h."),
    skip_render: bool = typer.Option(False, "--skip-render", help="Write plan/animation JSON only."),
) -> None:
    """Teach a problem with the LLM, then animate it with local templates."""
    typer.echo(f"Loading {input_path} …")
    try:
        result = run_pipeline(
            input_path,
            output_root=out.resolve() if out else None,
            quality=quality,
            skip_render=skip_render,
        )
    except Exception as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Run directory: {result.run_dir}", fg=typer.colors.GREEN)
    typer.echo(f"  plan:       {result.plan_path}")
    typer.echo(f"  verify:     {result.verify_path}")
    typer.echo(f"  animation:  {result.animation_path}")
    if skip_render:
        typer.echo("  video:      (skipped)")
    else:
        typer.echo(f"  video:      {result.video_path}")


if __name__ == "__main__":
    app()
