# plan_linear

Batch test with the `plan_linear` catalog solver:

```bash
find problems/by-type/plan_linear -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
