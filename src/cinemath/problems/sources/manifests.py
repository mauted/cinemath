"""Static manifests for problem banks that are not fully scraped (MIT, Arizona, OpenStax)."""

from __future__ import annotations

MIT_18_01_TOPICS: list[dict[str, str]] = [
    {
        "slug": "derivatives",
        "title": "Derivatives and differentiation",
        "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/resources/problem-sets/",
    },
    {
        "slug": "definite-integrals",
        "title": "Definite integrals",
        "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/resources/problem-sets/",
    },
    {
        "slug": "integration-techniques",
        "title": "Integration techniques",
        "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/resources/problem-sets/",
    },
    {
        "slug": "improper-integrals",
        "title": "Improper integrals",
        "url": "https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/resources/problem-sets/",
    },
]

MIT_18_02_TOPICS: list[dict[str, str]] = [
    {
        "slug": "partial-derivatives",
        "title": "Partial derivatives",
        "url": "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/",
    },
    {
        "slug": "double-integrals",
        "title": "Double integrals",
        "url": "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/",
    },
    {
        "slug": "triple-integrals",
        "title": "Triple integrals",
        "url": "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/",
    },
    {
        "slug": "line-integrals",
        "title": "Line integrals",
        "url": "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/",
    },
    {
        "slug": "vector-calculus",
        "title": "Green, Stokes, divergence",
        "url": "https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/",
    },
]

ARIZONA_MATH_129_WORKSHEETS: list[dict[str, str]] = [
    {
        "slug": "integration",
        "title": "Integration worksheets",
        "url": "https://math.arizona.edu/~calc/m129Worksheets.html",
    },
    {
        "slug": "series",
        "title": "Series worksheets",
        "url": "https://math.arizona.edu/~calc/m129Worksheets.html",
    },
    {
        "slug": "parametric-polar",
        "title": "Parametric and polar",
        "url": "https://math.arizona.edu/~calc/m129Worksheets.html",
    },
]

OPENSTAX_VOL2_CHAPTERS: list[dict[str, str]] = [
    {"slug": "ch01-integration", "title": "Integration", "url": "https://openstax.org/books/calculus-volume-2/pages/1-introduction"},
    {"slug": "ch02-applications", "title": "Applications of integration", "url": "https://openstax.org/books/calculus-volume-2/pages/2-introduction"},
    {"slug": "ch03-techniques", "title": "Techniques of integration", "url": "https://openstax.org/books/calculus-volume-2/pages/3-introduction"},
    {"slug": "ch04-intro-de", "title": "Introduction to DEs", "url": "https://openstax.org/books/calculus-volume-2/pages/4-introduction"},
    {"slug": "ch05-sequences-series", "title": "Sequences and series", "url": "https://openstax.org/books/calculus-volume-2/pages/5-introduction"},
    {"slug": "ch06-power-series", "title": "Power series", "url": "https://openstax.org/books/calculus-volume-2/pages/6-introduction"},
    {"slug": "ch07-parametric-polar", "title": "Parametric and polar", "url": "https://openstax.org/books/calculus-volume-2/pages/7-introduction"},
]

OPENSTAX_VOL3_CHAPTERS: list[dict[str, str]] = [
    {"slug": "ch01-vectors", "title": "Vectors in space", "url": "https://openstax.org/books/calculus-volume-3/pages/1-introduction"},
    {"slug": "ch02-vectors-geometry", "title": "Vectors and geometry", "url": "https://openstax.org/books/calculus-volume-3/pages/2-introduction"},
    {"slug": "ch03-vector-functions", "title": "Vector-valued functions", "url": "https://openstax.org/books/calculus-volume-3/pages/3-introduction"},
    {"slug": "ch04-differentiation", "title": "Differentiation of functions of several variables", "url": "https://openstax.org/books/calculus-volume-3/pages/4-introduction"},
    {"slug": "ch05-multiple-integrals", "title": "Multiple integration", "url": "https://openstax.org/books/calculus-volume-3/pages/5-introduction"},
    {"slug": "ch06-vector-calculus", "title": "Vector calculus", "url": "https://openstax.org/books/calculus-volume-3/pages/6-introduction"},
    {"slug": "ch07-second-order", "title": "Second-order DEs", "url": "https://openstax.org/books/calculus-volume-3/pages/7-introduction"},
]
