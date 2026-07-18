# Curated difficulty ladder

Located at `problems/curated/` (symlinked as `examples/` at repo root).

These examples still span arithmetic -> QFT, but they now route through a `visuals[]`
tool list instead of one hard-coded problem type. In practice that means:

- generic algebra / calculus -> `equation_board`
- quadratic equations -> `plot_2d` + `equation_board`
- rectangle double integrals -> region + board + 3D surface
- proofs / identities -> claim + board + QED
- long arithmetic -> one matching `paper_long_*`
- scalar decay -> interaction + Feynman diagram + board + answer

| Level | File | Idea |
|------:|------|------|
| 1 | `01_watermelons.txt` | Word-problem arithmetic |
| 2 | `02_linear_equation.txt` | One-step linear equation |
| 3 | `03_percent_off.txt` | Percentages |
| 4 | `04_quadratic.txt` | Factor / solve a quadratic |
| 5 | `05_pythagoras.txt` | Right-triangle geometry |
| 6 | `06_derivative.txt` | Polynomial derivative |
| 7 | `07_double_integral.md` | Iterated double integral + region |
| 8 | `08_euler_totient.md` | Formal number-theory proof |
| 9 | `09_improper_integral.md` | Improper integral / convergence |
| 10 | `10_scalar_decay.md` | Tree-level QFT decay width |
| 11 | `11_long_multiplication.txt` | Long multiplication ($384 \times 67$) |
| 12 | `12_long_division.txt` | Long division |
| 13 | `13_decimal_multiplication.txt` | Decimal multiplication |
| 14 | `14_long_addition.txt` | Long addition (decimals) |
| 15 | `15_long_subtraction.txt` | Long subtraction (with borrowing) |
| 16 | `16_linear_system_2d.txt` | 2x2 linear system (line intersection) |
| 17 | `17_linear_system_3d.txt` | 3x3 linear system (plane intersection) |
| 18 | `18_lamar_integration_by_parts.txt` | Lamar Calc II - $\int_0^1 x e^x\,dx$ |
| 19 | `19_mit_sine_integral.txt` | MIT 18.01 style - $\int_0^{\pi/2} \sin x\,dx$ |
| 20 | `20_partial_derivative.txt` | Lamar Calc III - $\partial f/\partial x$ |
| 21 | `21_triple_integral.md` | Lamar Calc III - triple integral on a box |

See also [docs/calculus_problem_sources.md](../docs/calculus_problem_sources.md) for full Calc 2/3 problem banks (`problems/by-type/<planner>/`).

```bash
uv run cinemath solve examples/01_watermelons.txt
# ...
uv run cinemath solve examples/10_scalar_decay.md
uv run cinemath solve examples/11_long_multiplication.txt
uv run cinemath solve examples/12_long_division.txt
uv run cinemath solve examples/13_decimal_multiplication.txt
uv run cinemath solve examples/14_long_addition.txt
uv run cinemath solve examples/15_long_subtraction.txt
uv run cinemath solve examples/16_linear_system_2d.txt
uv run cinemath solve examples/17_linear_system_3d.txt
uv run cinemath solve examples/18_lamar_integration_by_parts.txt
uv run cinemath solve examples/20_partial_derivative.txt
```
