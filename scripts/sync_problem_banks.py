#!/usr/bin/env python3
"""Sync external problem banks into problems/by-type/<planner>/<pack>/.

Usage:
  uv run python scripts/sync_problem_banks.py
  uv run python scripts/sync_problem_banks.py --lamar-only
  uv run python scripts/sync_problem_banks.py --migrate-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cinemath.problems import BY_TYPE_DIR, CURATED_DIR, PROBLEMS_DIR  # noqa: E402
from cinemath.problems.layout import ensure_planner_readmes, pack_dir, write_pack_meta, write_problem_file  # noqa: E402
from cinemath.problems.migrate import migrate_legacy_layout  # noqa: E402
from cinemath.problems.sources.lamar import sync_lamar  # noqa: E402
from cinemath.problems.sources.manifests import (  # noqa: E402
    ARIZONA_MATH_129_WORKSHEETS,
    MIT_18_01_TOPICS,
    MIT_18_02_TOPICS,
    OPENSTAX_VOL2_CHAPTERS,
    OPENSTAX_VOL3_CHAPTERS,
)
from cinemath.problems.topic_map import (  # noqa: E402
    mit_pack_id,
    resolve_mit_planner,
    UNCLASSIFIED,
)


def _seed_manifest_packs(
    *,
    source: str,
    course: str,
    topics: list[dict[str, str]],
) -> None:
    for topic in topics:
        planner = resolve_mit_planner(topic["slug"]) if source == "mit" else UNCLASSIFIED
        pack_id = f"{source}-{course}-{topic['slug']}"
        pack_path = pack_dir(PROBLEMS_DIR, planner, pack_id)
        pack_path.mkdir(parents=True, exist_ok=True)
        meta = {
            "planner": planner,
            "pack_id": pack_id,
            "source": source,
            "course": course,
            "topic": topic["slug"],
            "title": topic["title"],
            "url": topic["url"],
            "problem_count": len(list(pack_path.glob("prob-*.txt"))),
        }
        write_pack_meta(pack_path, meta)


def _seed_mit_starters() -> None:
    starters: dict[tuple[str, str], tuple[str, str]] = {
        ("18.01-single-variable", "definite-integrals"): (
            "plan_definite_integral",
            (
                "# MIT 18.01 style - sine integral\n"
                "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
                "Evaluate\n\n"
                r"$\int_0^{\pi/2} \sin(x)\, dx$"
            ),
        ),
        ("18.01-single-variable", "derivatives"): (
            "plan_derivative",
            (
                "# MIT 18.01 style - polynomial derivative\n"
                "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
                "Differentiate with respect to $x$:\n\n"
                r"$f(x) = 3x^4 - 2x^2 + 7$"
            ),
        ),
        ("18.01-single-variable", "improper-integrals"): (
            "plan_definite_integral",
            (
                "# MIT 18.01 / Lamar style - improper integral\n"
                "# Source: https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/\n\n"
                "Evaluate the improper integral\n\n"
                r"$\int_1^\infty \frac{1}{x^2}\, dx$"
                "\n\n"
                "and explain why it converges.\n"
            ),
        ),
        ("18.02-multivariable", "double-integrals"): (
            "plan_double_integral",
            (
                "# MIT 18.02 style - rectangle double integral\n"
                "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
                "Evaluate\n\n"
                r"$\iint_R 6xy^2 \, dA$"
                "\n\n"
                "where $R = [2, 4] \\times [1, 2]$, by writing it as the iterated integral\n\n"
                r"$\int_1^2 \int_2^4 6xy^2 \, dx \, dy$."
            ),
        ),
        ("18.02-multivariable", "partial-derivatives"): (
            "plan_partial_derivative",
            (
                "# MIT 18.02 / Lamar Calc III - partial derivative\n"
                "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
                r"Let $f(x, y) = x^2 y + \sin(xy)$. Find $\frac{\partial f}{\partial x}$."
            ),
        ),
        ("18.02-multivariable", "triple-integrals"): (
            "plan_triple_integral",
            (
                "# MIT 18.02 / Lamar Calc III - triple integral\n"
                "# Source: https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/\n\n"
                "Evaluate\n\n"
                r"$\iiint_E x y z \, dV$"
                "\n\n"
                "where $E$ is the box $0 \\le x \\le 1$, $0 \\le y \\le 2$, $0 \\le z \\le 1$.\n"
            ),
        ),
    }
    for (course, topic), (planner, body) in starters.items():
        pack_id = mit_pack_id(course, topic)
        pack_path = pack_dir(PROBLEMS_DIR, planner, pack_id)
        prob_path = pack_path / "prob-01.txt"
        if prob_path.exists():
            continue
        pack_path.mkdir(parents=True, exist_ok=True)
        header = (
            f"# MIT {course} / {topic}\n"
            f"# Planner: {planner}\n"
            f"# Pack: {pack_id}\n"
        )
        write_problem_file(prob_path, header=header, body=body.split("\n\n", 1)[-1])


def _seed_lamar_curated_ibp() -> None:
    pack_id = "lamar-calc-ii-integration-by-parts"
    pack_path = pack_dir(PROBLEMS_DIR, "plan_integration_by_parts", pack_id)
    path = pack_path / "prob-00-curated-ibp.txt"
    if path.exists():
        return
    pack_path.mkdir(parents=True, exist_ok=True)
    write_problem_file(
        path,
        header=(
            "# Lamar Calc II - integration by parts (cinemath curated)\n"
            "# Planner: plan_integration_by_parts\n"
            f"# Pack: {pack_id}\n"
            "# Source: https://tutorial.math.lamar.edu/problems/calcii/integrationbyparts.aspx"
        ),
        body="Evaluate the definite integral\n\n" + r"$\int_0^1 x e^x\, dx$",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync problem banks into problems/by-type/")
    parser.add_argument("--lamar-only", action="store_true", help="Only refresh Lamar")
    parser.add_argument("--skip-lamar", action="store_true", help="Skip Lamar network fetch")
    parser.add_argument(
        "--migrate-only",
        action="store_true",
        help="Only migrate legacy source-first trees into by-type layout",
    )
    args = parser.parse_args()

    PROBLEMS_DIR.mkdir(parents=True, exist_ok=True)
    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    BY_TYPE_DIR.mkdir(parents=True, exist_ok=True)

    if args.migrate_only:
        stats = migrate_legacy_layout(PROBLEMS_DIR)
        print("Migration:", json.dumps(stats, indent=2))
        ensure_planner_readmes(PROBLEMS_DIR)
        print(f"Done. Problem batches: {BY_TYPE_DIR}")
        return

    if not args.lamar_only:
        _seed_manifest_packs(
            source="mit",
            course="18.01-single-variable",
            topics=MIT_18_01_TOPICS,
        )
        _seed_manifest_packs(
            source="mit",
            course="18.02-multivariable",
            topics=MIT_18_02_TOPICS,
        )
        for topic in ARIZONA_MATH_129_WORKSHEETS:
            pack_id = f"arizona-math-129-{topic['slug']}"
            pack_path = pack_dir(PROBLEMS_DIR, UNCLASSIFIED, pack_id)
            pack_path.mkdir(parents=True, exist_ok=True)
            write_pack_meta(
                pack_path,
                {
                    "planner": UNCLASSIFIED,
                    "pack_id": pack_id,
                    "source": "arizona",
                    "course": "math-129",
                    "topic": topic["slug"],
                    "title": topic["title"],
                    "url": topic["url"],
                    "problem_count": len(list(pack_path.glob("prob-*.txt"))),
                },
            )
        for vol, chapters in (
            ("volume-2", OPENSTAX_VOL2_CHAPTERS),
            ("volume-3", OPENSTAX_VOL3_CHAPTERS),
        ):
            for chapter in chapters:
                pack_id = f"openstax-{vol}-{chapter['slug']}"
                pack_path = pack_dir(PROBLEMS_DIR, UNCLASSIFIED, pack_id)
                pack_path.mkdir(parents=True, exist_ok=True)
                write_pack_meta(
                    pack_path,
                    {
                        "planner": UNCLASSIFIED,
                        "pack_id": pack_id,
                        "source": "openstax",
                        "course": vol,
                        "topic": chapter["slug"],
                        "title": chapter["title"],
                        "url": chapter["url"],
                        "problem_count": len(list(pack_path.glob("prob-*.txt"))),
                    },
                )
        _seed_mit_starters()
        _seed_lamar_curated_ibp()
        migrate_legacy_layout(PROBLEMS_DIR, remove_legacy=True)

    if not args.skip_lamar:
        print("Syncing Lamar practice problems...")
        stats = sync_lamar(PROBLEMS_DIR)
        print(f"Lamar: {stats['sections']} sections, {stats['problems']} problems")

    ensure_planner_readmes(PROBLEMS_DIR)
    print(f"Done. Problem batches: {BY_TYPE_DIR}")


if __name__ == "__main__":
    main()
