# plan_linear_system_3d

Batch test with the `plan_linear_system_3d` catalog solver:

```bash
find problems/by-type/plan_linear_system_3d -name "prob-*.txt" -print0 | xargs -0 -I{} uv run cinemath solve {} -q l --skip-render
```
