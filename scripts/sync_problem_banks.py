#!/usr/bin/env python3
"""Sync external problem banks into problems/.

Usage:
  uv run python scripts/sync_problem_banks.py
  uv run python scripts/sync_problem_banks.py --lamar-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cinemath.problems import PROBLEMS_DIR  # noqa: E402
from cinemath.problems.sources.lamar import sync_lamar  # noqa: E402
from cinemath.problems.sources.manifests import (  # noqa: E402
    ARIZONA_MATH_129_WORKSHEETS,
    MIT_18_01_TOPICS,
    MIT_18_02_TOPICS,
    OPENSTAX_VOL2_CHAPTERS,
    OPENSTAX_VOL3_CHAPTERS,
)


def _write_readme(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")


def _seed_manifest_tree(
    base: Path,
    *,
    source: str,
    readme_title: str,
    readme_url: str,
    topics: list[dict[str, str]],
) -> None:
    _write_readme(
        base / "README.md",
        readme_title,
        f"Source: {readme_url}\n\n"
        "Topic folders hold cinemath-ready `.txt` problems. "
        "Run `uv run python scripts/sync_problem_banks.py` to refresh Lamar; "
        "MIT/Arizona/OpenStax folders are seeded from manifests until PDF scraping is added.\n",
    )
    for topic in topics:
        topic_dir = base / topic["slug"]
        topic_dir.mkdir(parents=True, exist_ok=True)
        meta = {
            "source": source,
            "slug": topic["slug"],
            "title": topic["title"],
            "url": topic["url"],
            "problem_count": len(list(topic_dir.glob("prob-*.txt"))),
        }
        (topic_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _seed_mit_starters(problems_dir: Path) -> None:
    starters = {
        "18.01-single-variable/definite-integrals/prob-01.txt": (
            "# MIT 18.01 style - sine integral\n"
            "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
            "Evaluate\n\n"
            r"$\int_0^{\pi/2} \sin(x)\, dx$"
            "\n"
        ),
        "18.01-single-variable/derivatives/prob-01.txt": (
            "# MIT 18.01 style - polynomial derivative\n"
            "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
            "Differentiate with respect to $x$:\n\n"
            r"$f(x) = 3x^4 - 2x^2 + 7$"
            "\n"
        ),
        "18.01-single-variable/improper-integrals/prob-01.txt": (
            "# MIT 18.01 / Lamar style - improper integral\n"
            "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
            "Evaluate the improper integral\n\n"
            r"$\int_1^\infty \frac{1}{x^2}\, dx$"
            "\n"
            "and explain why it converges.\n"
        ),
        "18.02-multivariable/double-integrals/prob-01.txt": (
            "# MIT 18.02 style - rectangle double integral\n"
            "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
            "Evaluate\n\n"
            r"$\iint_R 6xy^2 \, dA$"
            "\n\n"
            "where $R = [2, 4] \\times [1, 2]$, by writing it as the iterated integral\n\n"
            r"$\int_1^2 \int_2^4 6xy^2 \, dx \, dy$."
            "\n"
        ),
        "18.02-multivariable/partial-derivatives/prob-01.txt": (
            "# MIT 18.02 / Lamar Calc III - partial derivative\n"
            "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
            r"Let $f(x, y) = x^2 y + \sin(xy)$. Find $\frac{\partial f}{\partial x}$."
            "\n"
        ),
        "18.02-multivariable/triple-integrals/prob-01.txt": (
            "# MIT 18.02 / Lamar Calc III - triple integral\n"
            "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
            "Evaluate\n\n"
            r"$\iiint_E x y z \, dV$"
            "\n\n"
            "where $E$ is the box $0 \\le x \\le 1$, $0 \\le y \\le 2$, $0 \\le z \\le 1$.\n"
        ),
    }
    for rel, content in starters.items():
        path = problems_dir / "mit" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def _seed_lamar_curated_crossrefs(problems_dir: Path) -> None:
    """Add the IBP definite integral used in cinemath curated ladder."""
    path = (
        problems_dir
        / "lamar"
        / "calc-ii"
        / "integration-by-parts"
        / "prob-00-curated-ibp.txt"
    )
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Lamar Calc II - integration by parts (cinemath curated)\n"
        "# Source: https://tutorial.math.lamar.edu/problems/calcii/integrationbyparts.aspx\n\n"
        "Evaluate the definite integral\n\n"
        r"$\int_0^1 x e^x\, dx$"
        "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync problem banks into problems/")
    parser.add_argument("--lamar-only", action="store_true", help="Only refresh Lamar")
    parser.add_argument("--skip-lamar", action="store_true", help="Skip Lamar network fetch")
    args = parser.parse_args()

    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    (PROBLEMS_DIR / "curated").mkdir(parents=True, exist_ok=True)

    if not args.lamar_only:
        _seed_manifest_tree(
            PROBLEMS_DIR / "mit" / "18.01-single-variable",
            source="mit",
            readme_title="MIT 18.01 Single Variable Calculus",
            readme_url="https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/",
            topics=MIT_18_01_TOPICS,
        )
        _seed_manifest_tree(
            PROBLEMS_DIR / "mit" / "18.02-multivariable",
            source="mit",
            readme_title="MIT 18.02 Multivariable Calculus",
            readme_url="https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/",
            topics=MIT_18_02_TOPICS,
        )
        _seed_manifest_tree(
            PROBLEMS_DIR / "arizona" / "math-129",
            source="arizona",
            readme_title="University of Arizona Math 129",
            readme_url="https://math.arizona.edu/~calc/m129Worksheets.html",
            topics=ARIZONA_MATH_129_WORKSHEETS,
        )
        _seed_manifest_tree(
            PROBLEMS_DIR / "openstax" / "volume-2",
            source="openstax",
            readme_title="OpenStax Calculus Volume 2",
            readme_url="https://openstax.org/details/books/calculus-volume-2",
            topics=OPENSTAX_VOL2_CHAPTERS,
        )
        _seed_manifest_tree(
            PROBLEMS_DIR / "openstax" / "volume-3",
            source="openstax",
            readme_title="OpenStax Calculus Volume 3",
            readme_url="https://openstax.org/details/books/calculus-volume-3",
            topics=OPENSTAX_VOL3_CHAPTERS,
        )
        _seed_mit_starters(PROBLEMS_DIR)
        _seed_lamar_curated_crossrefs(PROBLEMS_DIR)

    if not args.skip_lamar:
        print("Syncing Lamar practice problems...")
        stats = sync_lamar(PROBLEMS_DIR)
        print(f"Lamar: {stats['sections']} sections, {stats['problems']} problems")

    _write_readme(
        PROBLEMS_DIR / "lamar" / "README.md",
        "Paul's Online Math Notes (Lamar)",
        "Source: https://tutorial.math.lamar.edu/\n\n"
        "Practice problems are scraped from `/problems/calcii/` and `/problems/calciii/`.\n"
        "Each section folder has `meta.json` plus `prob-NN.txt` files.\n",
    )

    print(f"Done. Problem bank root: {PROBLEMS_DIR}")


if __name__ == "__main__":
    main()
