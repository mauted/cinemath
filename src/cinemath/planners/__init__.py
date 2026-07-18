"""Catalog planners: classify -> plan_* -> plan.json."""

from cinemath.planners.algebra import (
    plan_linear,
    plan_linear_system_2d,
    plan_linear_system_3d,
    plan_percent_off,
    plan_quadratic,
)
from cinemath.planners.arithmetic import (
    plan_long_add,
    plan_long_divide,
    plan_long_multiply,
    plan_long_subtract,
)
from cinemath.planners.calculus import (
    Order,
    plan_definite_integral,
    plan_derivative,
    plan_double_integral,
    plan_integration_by_parts,
    plan_partial_derivative,
    plan_triple_integral,
)
from cinemath.planners.registry import CLASSIFY_SYSTEM, CLASSIFY_TOOLS, run_catalog

__all__ = [
    "CLASSIFY_SYSTEM",
    "CLASSIFY_TOOLS",
    "Order",
    "plan_definite_integral",
    "plan_derivative",
    "plan_double_integral",
    "plan_linear",
    "plan_linear_system_2d",
    "plan_linear_system_3d",
    "plan_long_add",
    "plan_long_divide",
    "plan_long_multiply",
    "plan_long_subtract",
    "plan_integration_by_parts",
    "plan_partial_derivative",
    "plan_percent_off",
    "plan_quadratic",
    "plan_triple_integral",
    "run_catalog",
]
