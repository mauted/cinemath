"""Fetch practice problems from Paul's Online Math Notes (Lamar University)."""

from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from cinemath.problems.latex_normalize import normalize_lamar_latex
from cinemath.problems.layout import pack_dir, write_pack_meta, write_problem_file
from cinemath.problems.topic_map import lamar_pack_id, resolve_lamar_planner

LAMAR_BASE = "https://tutorial.math.lamar.edu"
INTRO_SLUGS = frozenset({"inttechintro", "intappsintro", "parametricintro", "seriesintro", "vectorsintro", "3dspace", "partialderivsintro", "partialderivappsintro", "multipleintegralsintro", "surfaceintegralsintro", "lineintegralsintro"})


def camel_to_kebab(name: str) -> str:
    stem = name.replace(".aspx", "")
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", stem).lower()


@dataclass(frozen=True)
class LamarProblem:
    number: int
    latex: str
    solution_url: str | None


@dataclass(frozen=True)
class LamarSection:
    course: str
    slug: str
    title: str
    source_url: str
    problems: list[LamarProblem]


class _PracticeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._capture_problems = False
        self._in_li = False
        self._li_parts: list[str] = []
        self.problems: list[tuple[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "h3" and attr.get("class") == "practice-title":
            self._in_title = True
            self._capture_problems = True
        elif tag == "li" and self._capture_problems:
            self._in_li = True
            self._li_parts = []
        elif tag == "a" and self._in_li and attr.get("class") == "practice-soln-link":
            href = attr.get("href") or ""
            self._li_parts.append(f"__SOLN__{href}")

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self._in_title:
            self._in_title = False
        elif tag == "li" and self._in_li:
            self._in_li = False
            raw = "".join(self._li_parts)
            soln = None
            m = re.search(r"__SOLN__(/[^<]+)", raw)
            if m:
                soln = m.group(1)
                raw = raw[: m.start()]
            raw = re.sub(r"\\?\(|\\?\)", "", raw).strip()
            if raw:
                self.problems.append((raw, soln))

    def handle_data(self, data: str) -> None:
        if self._in_title and not self._in_li:
            self.title += data
        elif self._in_li:
            self._li_parts.append(data)


def fetch_section_slugs(course: str) -> list[str]:
    """Return practice section filenames for calc-ii or calc-iii."""
    index_url = f"{LAMAR_BASE}/problems/{course}/{course}.aspx"
    html = urllib.request.urlopen(index_url, timeout=60).read().decode("utf-8", errors="replace")
    slugs = sorted(
        {
            m.group(1)
            for m in re.finditer(r'href="([A-Za-z0-9]+\.aspx)"', html)
            if m.group(1).lower() not in {f"{course}.aspx"}
        }
    )
    return [s for s in slugs if camel_to_kebab(s).replace("-", "") not in INTRO_SLUGS]


def fetch_section(course: str, slug: str) -> LamarSection:
    url = f"{LAMAR_BASE}/problems/{course}/{slug}"
    html = urllib.request.urlopen(url, timeout=60).read().decode("utf-8", errors="replace")
    parser = _PracticeParser()
    parser.feed(html)
    title = parser.title.strip() or slug
    problems = [
        LamarProblem(
            number=i,
            latex=normalize_lamar_latex(latex),
            solution_url=f"{LAMAR_BASE}{soln}" if soln else None,
        )
        for i, (latex, soln) in enumerate(parser.problems, start=1)
    ]
    return LamarSection(
        course=course,
        slug=camel_to_kebab(slug),
        title=title,
        source_url=url,
        problems=problems,
    )


def problem_statement_tex(problem: LamarProblem) -> str:
    if problem.latex.strip().startswith("\\int"):
        return f"Evaluate\n\n${problem.latex}$"
    return f"Evaluate\n\n${problem.latex}$"


def write_section(section: LamarSection, problems_dir: Path) -> int:
    course = section.course.replace("calc", "calc-")
    planner = resolve_lamar_planner(course, section.slug)
    pack_id = lamar_pack_id(course, section.slug)
    out_dir = pack_dir(problems_dir, planner, pack_id)
    meta = {
        "planner": planner,
        "pack_id": pack_id,
        "source": "lamar",
        "course": course,
        "section": section.slug,
        "title": section.title,
        "url": section.source_url,
        "problem_count": len(section.problems),
    }
    write_pack_meta(out_dir, meta)
    written = 0
    for problem in section.problems:
        path = out_dir / f"prob-{problem.number:02d}.txt"
        header = (
            f"# {section.title} (problem {problem.number})\n"
            f"# Planner: {planner}\n"
            f"# Pack: {pack_id}\n"
            f"# Source: {section.source_url}\n"
        )
        if problem.solution_url:
            header += f"# Solution: {problem.solution_url}\n"
        write_problem_file(path, header=header, body=problem_statement_tex(problem))
        written += 1
    return written


def sync_lamar(problems_dir: Path, *, courses: tuple[str, ...] = ("calcii", "calciii")) -> dict[str, int]:
    """Download Lamar practice problems into problems/by-type/<planner>/<pack>/."""
    stats: dict[str, int] = {"sections": 0, "problems": 0}
    for course in courses:
        slugs = fetch_section_slugs(course)
        for slug in slugs:
            section = fetch_section(course, slug)
            if not section.problems:
                continue
            count = write_section(section, problems_dir)
            stats["sections"] += 1
            stats["problems"] += count
    return stats
