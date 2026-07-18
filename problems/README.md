# Problem banks

Curated cinemath examples and scraped problems from standard calculus sources.

## Layout

```
problems/
  curated/                          # Cinemath difficulty ladder (symlinked as ../examples)
  by-type/
    plan_definite_integral/         # Catalog solver batch
      lamar-calc-ii-improper-integrals/
        meta.json                   # planner, source, url, problem_count
        prob-01.txt
    plan_integration_by_parts/
    plan_partial_derivative/
    ...
    unclassified/                   # No shipped planner yet (series, vector calc, …)
```

Problems are grouped **by catalog planner** so you can batch-test one solver:

```bash
# All definite-integral problems (Lamar + MIT + curated symlinks)
find problems/by-type/plan_definite_integral -name 'prob-*.txt'

# Smoke-test a planner batch (plan only, no render)
find problems/by-type/plan_integration_by_parts -name 'prob-*.txt' -print0 \
  | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```

Each pack folder (`lamar-calc-ii-improper-integrals`, `mit-18.01-single-variable-definite-integrals`, …) keeps source metadata in `meta.json` and problem headers.

Topic → planner mapping lives in `src/cinemath/problems/topic_map.py`.

## Sync

```bash
# Full sync (migrate legacy layout + Lamar scrape + manifest seeds)
uv run python scripts/sync_problem_banks.py

# Lamar only (refresh scraped problems into by-type/)
uv run python scripts/sync_problem_banks.py --lamar-only

# One-time migrate from old source-first trees (lamar/, mit/, …)
uv run python scripts/sync_problem_banks.py --migrate-only
```

## Solve

```bash
uv run cinemath solve problems/curated/04_quadratic.txt
uv run cinemath solve problems/by-type/plan_integration_by_parts/lamar-calc-ii-integration-by-parts/prob-01.txt
uv run cinemath solve problems/by-type/plan_definite_integral/mit-18.01-single-variable-definite-integrals/prob-01.txt
```

See [docs/calculus_problem_sources.md](../docs/calculus_problem_sources.md) for source links and catalog planner coverage.
