# plan_percent_off

Batch test with the `plan_percent_off` catalog solver:

```bash
find problems/by-type/plan_percent_off -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
