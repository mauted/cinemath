"""Backward-compatible re-exports. Prefer ``cinemath.planners.calculus``."""

from cinemath.planners.calculus import CALCULUS_ENTRIES
from cinemath.planners.integration_by_parts import plan_integration_by_parts
from cinemath.planners.calculus import (
    plan_definite_integral,
    plan_partial_derivative,
    plan_triple_integral,
)

__all__ = [
    "CALCULUS_ENTRIES",
    "plan_definite_integral",
    "plan_integration_by_parts",
    "plan_partial_derivative",
    "plan_triple_integral",
]
