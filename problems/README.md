# Problem banks

Curated cinemath examples and scraped problems from standard calculus sources.

## Layout

```
problems/
  curated/              # Cinemath difficulty ladder (symlinked as ../examples)
  lamar/
    calc-ii/<section>/  # Paul's Online Math Notes Calc II practice problems
    calc-iii/<section>/
  mit/
    18.01-single-variable/<topic>/
    18.02-multivariable/<topic>/
  arizona/math-129/<worksheet>/
  openstax/volume-2/<chapter>/
  openstax/volume-3/<chapter>/
```

Each topic folder contains:

- `meta.json` -- source URL, title, problem count
- `prob-NN.txt` -- cinemath-ready problem statement (ASCII LaTeX in `$...$`)

## Sync

```bash
# Full sync (Lamar scrape + MIT/Arizona/OpenStax folder manifests)
uv run python scripts/sync_problem_banks.py

# Lamar only
uv run python scripts/sync_problem_banks.py --lamar-only
```

## Solve

```bash
uv run cinemath solve problems/curated/04_quadratic.txt
uv run cinemath solve problems/lamar/calc-ii/integration-by-parts/prob-01.txt
uv run cinemath solve problems/mit/18.01-single-variable/definite-integrals/prob-01.txt
```

See [docs/calculus_problem_sources.md](../docs/calculus_problem_sources.md) for source links and catalog planner coverage.
