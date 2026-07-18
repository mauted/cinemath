# cinemath

CLI that turns a math problem into a short educational Manim animation.

![Pseudoscalar Yukawa β-function lesson](preview.gif)

**Architecture (v0.4):**

1. **LLM classifies** → picks one catalog planner (`plan_*`) or `teach_freeform`
2. **Catalog planner** → local `plan_*` builds `plan.json` (SymPy / arithmetic)
3. **Freeform teacher** → LLM writes `plan.json` when no catalog entry fits
4. **Local verify** → SymPy checks freeform plans; failures are re-fed to the LLM until correct (`verify.json`)
5. **Local visual compilers** → `animation.json`
6. **Local renderer** → Manim video

Algebra steps use an **equation chain** (`render_engine/equation_chain.py`): dim the prior line, scroll up to make room, then morph a copy into the next equation with `TransformMatchingTex`. Step **explanations** become larger instruction banners (`render_engine/instructions.py`) placed above the active work, at the bottom under plots, or at the top when that is clearest.

Every animation opens with a **problem statement** beat (`problem_statement.py`): the statement is written onto the board, held to read, then cleared before the solution.

Graphs live in **`graph_2d.py`** / **`graph_3d.py`**: auto axis ranges, filled regions, full-frame surfaces with flat captions.

## Setup

```bash
cd cinemath
brew install cairo pkg-config   # once, for Manim
uv sync
cp .env.example .env            # set ANTHROPIC_API_KEY
```

Optional: `ANTHROPIC_CLASSIFY_MODEL` (default Haiku) for routing/OCR; `ANTHROPIC_TEACH_MODEL` (default Sonnet) for freeform plans. `ANTHROPIC_MODEL` overrides both when the specific vars are unset. Use `--verbose` / `CINEMATH_LOG_LEVEL=DEBUG` for full pipeline logs (color on in TTY; set `NO_COLOR=1` or `CINEMATH_LOG_COLOR=0` to disable).

## Usage

```bash
uv run cinemath solve examples/01_watermelons.txt
uv run cinemath solve examples/07_double_integral.md
uv run cinemath solve examples/10_scalar_decay.md
uv run cinemath solve path/to/photo.png
```

See [`problems/curated/README.md`](../problems/curated/README.md) for the full **difficulty ladder** (arithmetic → QFT).

**Problem banks:** [`problems/README.md`](problems/README.md) — Lamar (650+ scraped), MIT, Arizona, OpenStax, organized under `problems/by-type/<planner>/` for batch testing. Sync with `uv run python scripts/sync_problem_banks.py`.

**Source layout:** `src/cinemath/` is grouped by concern:

- `core/` — pipeline, ingest, logging
- `plan/` — teacher plan schema and validation
- `teaching/` — LLM teacher and SymPy verify
- `planners/` — catalog solvers by domain (`algebra/`, `arithmetic/`, `calculus/`)
- `render_engine/`, `templates/`, `problems/` — animation IR and problem banks

## Preprint

Architecture write-up with pipeline diagram:
[`docs/cinemath_showcase_report.pdf`](docs/cinemath_showcase_report.pdf)

## Output

```text
outputs/<timestamp>_<slug>/
  problem.txt
  plan.json         # catalog planner or freeform LLM teacher
  lesson.md
  verify.json       # freeform plans only (SymPy check + retry summary)
  animation.json    # intermediate representation (re-render with cinemath)
  animation.mp4
```

Manim renders into a temp directory by default; use `--keep-media` to retain `media/` for debugging.

## Visual tools

`plan.json` now chooses **local visual capabilities** with a `visuals[]` list instead of one
mutually exclusive problem type.

| Tool | Purpose |
|---|---|
| `equation_board` | Board: caption + stacked math per step |
| `state_claim` / `show_qed` | Proof-style opener / closer |
| `plot_2d` | 2D quadratic parabola + marked roots |
| `show_region_rectangle` | 2D rectangular integration region |
| `plot_surface_3d` | 3D surface over a rectangular domain |
| `paper_long_multiply` | Paper long multiplication + side digit calc |
| `paper_long_divide` | Paper long division |
| `paper_long_add` | Paper long addition + side column calc |
| `paper_long_subtract` | Paper long subtraction + borrow marks |
| `show_lagrangian` | QFT Lagrangian / interaction setup |
| `feynman_1to2` | Tree-level 1→2 decay diagram |
| `feynman_loop` | One-loop / 1PI layouts (`loop_bubble`, `four_point_loop`, `yukawa_triangle`) |
| `rg_flow_2d` | 2D RG flow arrow field from β(x,y) expressions |
| `show_answer` | Final highlighted answer beat |

Common recipes:

- Generic worked solution: `equation_board`
- Quadratic: `plot_2d` + `equation_board` + `show_answer`
- Rectangle double integral: `show_region_rectangle` + `equation_board` + `plot_surface_3d` + `show_answer`
- Proof / identity derivation: `state_claim` + `equation_board` + `show_qed`
- Paper arithmetic: one matching `paper_long_*`
- QFT decay: `show_lagrangian` + `feynman_1to2` + `equation_board` + `show_answer`
- QFT β / RG: `show_lagrangian` + `feynman_loop` + `equation_board` + `rg_flow_2d` + `show_answer`
