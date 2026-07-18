# plan_long_subtract

Batch test with the `plan_long_subtract` catalog solver:

```bash
find problems/by-type/plan_long_subtract -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
