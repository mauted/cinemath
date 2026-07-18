# plan_definite_integral

Batch test with the `plan_definite_integral` catalog solver:

```bash
find problems/by-type/plan_definite_integral -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
