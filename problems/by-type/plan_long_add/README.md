# plan_long_add

Batch test with the `plan_long_add` catalog solver:

```bash
find problems/by-type/plan_long_add -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
