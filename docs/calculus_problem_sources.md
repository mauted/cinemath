# Calculus problem sources & cinemath catalog roadmap

Reference list of free, standard problem banks for **Calculus 2** and **Calculus 3**, plus how we map topics to cinemath catalog planners.

---

## Calculus 2 (integration techniques, series, parametric/polar, applications)

### 1. Paul's Online Math Notes — Calculus II (top pick for self-study)

Hundreds of practice problems by topic, with full step-by-step solutions. Downloadable PDF problem/solution books.

- **Link:** [Calculus II practice problems](https://tutorial.math.lamar.edu/problems/calcii/calcii.aspx)
- **Topics:** Integration by parts; trig integrals/substitutions; partial fractions; improper integrals; arc length / surface area / center of mass; parametric & polar; sequences & series (convergence tests, power/Taylor series); etc.

### 2. MIT OpenCourseWare — 18.01 Single Variable Calculus

Official MIT problem sets (rigorous, university-standard).

- **Problem sets (Fall 2006):** [18.01 problem sets](https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/resources/problem-sets/)
- **With solutions:** search OCW for **18.01SC** problem set solutions.

### 3. University of Arizona — Math 129 Calculus II worksheets

Topic-specific PDF worksheets.

- **Link:** [Math 129 worksheets](https://math.arizona.edu/~calc/m129Worksheets.html)

### Bonus — OpenStax Calculus Volume 2

Free textbook; end-of-chapter exercises.

- **Link:** [OpenStax Calculus Vol. 2](https://openstax.org/details/books/calculus-volume-2)

---

## Calculus 3 / multivariable (vectors, partials, multiple integrals, vector calculus)

### 1. Paul's Online Math Notes — Calculus III

Same style as Calc II: web problems + full solutions + PDFs.

- **Link:** [Calculus III practice problems](https://tutorial.math.lamar.edu/Problems/CalcIII/CalcIII.aspx)
- **Topics:** 3D space & quadric surfaces; vector functions; partial derivatives (chain rule, directional derivatives); applications (tangent planes, extrema, Lagrange multipliers); double & triple integrals (polar, cylindrical, spherical); line/surface integrals; Green / Stokes / Divergence theorems; curl & divergence.

### 2. MIT OpenCourseWare — 18.02 Multivariable Calculus

- **SC solutions (Fall 2010):** [18.02SC problem set solutions](https://ocw.mit.edu/courses/18-02sc-multivariable-calculus-fall-2010/resources/problem-set-solutions/)
- Other semesters: search **18.02 assignments** on [ocw.mit.edu](https://ocw.mit.edu).

### Bonus — OpenStax Calculus Volume 3

- **Link:** [OpenStax Calculus Vol. 3](https://openstax.org/details/books/calculus-volume-3)

---

## Quick tips

- **Paul's Notes** — easiest starting point (web UI + instant solutions).
- **MIT OCW** — authentic university sets; often more proof-oriented.
- All sources above are free and legal to use.

---

## Cinemath catalog coverage (living map)

| Topic area | Example source | Catalog planner | Status |
|------------|----------------|-----------------|--------|
| Derivatives (single variable) | MIT 18.01, Lamar Calc I review | `plan_derivative` | **shipped** |
| Definite integrals | Lamar §7, MIT 18.01 PS | `plan_definite_integral` | **shipped** |
| Improper integrals | Lamar §7.8, example 09 | `plan_definite_integral` (`upper=oo`) | **shipped** |
| Integration by parts | Lamar §7.1, example 18 | `plan_integration_by_parts` | **shipped** |
| Integration by parts / trig / partial fractions (auto) | Lamar §7 | `plan_definite_integral` (SymPy) | **v1** — black-box evaluate |
| Double integrals (rectangle) | Lamar / MIT 18.02 | `plan_double_integral` | **shipped** |
| Triple integrals (box) | Lamar Calc III §14 | `plan_triple_integral` | **shipped** |
| Partial derivatives | Lamar Calc III §13 | `plan_partial_derivative` | **shipped** |
| Series / convergence tests | Lamar §10 | — | planned |
| Parametric / polar | Lamar §9 | — | planned |
| Vector calculus (line/surface integrals) | Lamar §16–17, MIT 18.02 | — | planned |
| Lagrange multipliers | Lamar §13.9 | — | planned |

**Classifier:** `CLASSIFY_SYSTEM` in `catalog.py` lists all `plan_*` tools; anything outside the table falls through to `teach_freeform`.

---

## Cinemath examples (curated from these banks)

Curated ladder lives in [`problems/curated/`](../problems/curated/) (also reachable as [`examples/`](../examples/) via symlink).

Full scraped banks: [`problems/README.md`](../problems/README.md). Refresh with `uv run python scripts/sync_problem_banks.py`.

| File | Style | Expected planner |
|------|-------|------------------|
| `problems/curated/06_derivative.txt` | MIT / standard | `plan_derivative` |
| `problems/curated/07_double_integral.md` | MIT 18.02 style | `plan_double_integral` |
| `problems/curated/09_improper_integral.md` | Lamar §7.8 | `plan_definite_integral` |
| `problems/curated/18_lamar_integration_by_parts.txt` | Lamar Calc II | `plan_integration_by_parts` |
| `problems/curated/19_mit_sine_integral.txt` | MIT 18.01 | `plan_definite_integral` |
| `problems/curated/20_partial_derivative.txt` | Lamar Calc III | `plan_partial_derivative` |
| `problems/curated/21_triple_integral.md` | Lamar Calc III §14 | `plan_triple_integral` |

Run locally:

```bash
uv run cinemath solve problems/lamar/calc-ii/integration-by-parts/prob-01.txt -q l
uv run cinemath solve problems/curated/20_partial_derivative.txt -q l
```

---

## Next steps toward “full calculus”

1. ~~Technique-aware boards (IBP, partial fractions, substitution)~~ **IBP shipped** (`plan_integration_by_parts`); partial fractions / substitution next.
2. `plan_series` — ratio/root/comparison tests with plot_2d partial sums where helpful.
3. `plan_line_integral` / `plan_surface_integral` — reuse `graph_2d` / `graph_3d` chrome.
4. Polar/cylindrical/spherical Jacobian helpers on top of `plan_double_integral` / `plan_triple_integral`.
5. Golden tests per planner + optional e2e over `problems/curated/18`–`21`.
