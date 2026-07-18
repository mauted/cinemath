"""Calculus catalog planners (single- and multivariable)."""

from cinemath.planners.calculus.definite_integral import (
    DEFINITE_INTEGRAL_ENTRY,
    plan_definite_integral,
)
from cinemath.planners.calculus.derivative import plan_derivative
from cinemath.planners.calculus.double_integral import Order, plan_double_integral
from cinemath.planners.calculus.integration_by_parts import (
    INTEGRATION_BY_PARTS_ENTRY,
    plan_integration_by_parts,
)
from cinemath.planners.calculus.partial_derivative import (
    PARTIAL_DERIVATIVE_ENTRY,
    plan_partial_derivative,
)
from cinemath.planners.calculus.partial_fractions import (
    PARTIAL_FRACTIONS_ENTRY,
    plan_partial_fractions,
)
from cinemath.planners.calculus.trig_substitution import (
    TRIG_SUBSTITUTION_ENTRY,
    plan_trig_substitution,
)
from cinemath.planners.calculus.triple_integral import (
    TRIPLE_INTEGRAL_ENTRY,
    plan_triple_integral,
)
from cinemath.planners.calculus.u_substitution import (
    U_SUBSTITUTION_ENTRY,
    plan_u_substitution,
)

CALCULUS_ENTRIES: list = [
    DEFINITE_INTEGRAL_ENTRY,
    PARTIAL_FRACTIONS_ENTRY,
    TRIG_SUBSTITUTION_ENTRY,
    U_SUBSTITUTION_ENTRY,
    INTEGRATION_BY_PARTS_ENTRY,
    PARTIAL_DERIVATIVE_ENTRY,
    TRIPLE_INTEGRAL_ENTRY,
]

__all__ = [
    "CALCULUS_ENTRIES",
    "Order",
    "plan_definite_integral",
    "plan_derivative",
    "plan_double_integral",
    "plan_integration_by_parts",
    "plan_partial_derivative",
    "plan_partial_fractions",
    "plan_trig_substitution",
    "plan_triple_integral",
    "plan_u_substitution",
]
