# cinemath

CLI that turns a math problem into a short educational Manim animation.

![Pseudoscalar Yukawa β-function lesson](preview.gif)

**Architecture (v0.3):**

1. **LLM teaches only** → `plan.json` (`steps` + `visuals[]`)
2. **Local verify** → SymPy / arithmetic checks known visual tools (`verify.json`)
3. **Local visual compilers** → `animation.json` (never LLM-authored)
4. **Local renderer** → Manim video

Algebra steps use an **equation chain** (`render_engine/equation_chain.py`): dim the prior line, scroll up to make room, then morph a copy into the next equation with `TransformMatchingTex`. Step **explanations** become wrapped instruction banners (`render_engine/instructions.py`) fitted to the full frame or right half.

Every animation opens with a **problem statement** beat (`problem_statement.py`): the statement is written onto the board, held to read, then cleared before the solution.

Graphs live in **`graph_2d.py`** / **`graph_3d.py`**: auto axis ranges, filled regions, full-frame surfaces with flat captions.

## Setup

```bash
cd cinemath
brew install cairo pkg-config   # once, for Manim
uv sync
cp .env.example .env            # set ANTHROPIC_API_KEY
```

## Usage

```bash
uv run cinemath solve examples/01_watermelons.txt
uv run cinemath solve examples/07_double_integral.md
uv run cinemath solve examples/10_scalar_decay.md
uv run cinemath solve path/to/photo.png
```

See [`examples/README.md`](examples/README.md) for the full **10-level** difficulty ladder (arithmetic → QFT).

## Preprint

Architecture write-up with pipeline diagram:

- TeX: [`docs/cinemath_showcase_report.tex`](docs/cinemath_showcase_report.tex)
- PDF: [`docs/cinemath_showcase_report.pdf`](docs/cinemath_showcase_report.pdf)

```bash
latexmk -pdf -cd docs/cinemath_showcase_report.tex
```

## Output

```text
outputs/<timestamp>_<slug>/
  problem.txt
  plan.json         # teacher plan (LLM)
  lesson.md
  verify.json       # SymPy check / corrections
  animation.json    # built locally from templates
  scene.py
  animation.mp4
```

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
