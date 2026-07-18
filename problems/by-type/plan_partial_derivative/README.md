# plan_partial_derivative

Batch test with the `plan_partial_derivative` catalog solver:

```bash
find problems/by-type/plan_partial_derivative -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
