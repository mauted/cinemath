# plan_integration_by_parts

Batch test with the `plan_integration_by_parts` catalog solver:

```bash
find problems/by-type/plan_integration_by_parts -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
