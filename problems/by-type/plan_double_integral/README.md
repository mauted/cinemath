# plan_double_integral

Batch test with the `plan_double_integral` catalog solver:

```bash
find problems/by-type/plan_double_integral -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
