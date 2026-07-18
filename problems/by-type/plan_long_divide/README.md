# plan_long_divide

Batch test with the `plan_long_divide` catalog solver:

```bash
find problems/by-type/plan_long_divide -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
