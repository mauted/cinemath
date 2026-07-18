"""Map external problem-bank topics to cinemath catalog planners."""

from __future__ import annotations

from typing import Final

UNCLASSIFIED: Final = "unclassified"

# All shipped catalog planners that have (or will have) problem batches.
CATALOG_PLANNERS: Final[tuple[str, ...]] = (
    "plan_quadratic",
    "plan_linear",
    "plan_linear_system_2d",
    "plan_linear_system_3d",
    "plan_percent_off",
    "plan_derivative",
    "plan_definite_integral",
    "plan_integration_by_parts",
    "plan_partial_fractions",
    "plan_trig_substitution",
    "plan_u_substitution",
    "plan_partial_derivative",
    "plan_double_integral",
    "plan_triple_integral",
    "plan_long_multiply",
    "plan_long_divide",
    "plan_long_add",
    "plan_long_subtract",
)

# Lamar practice sections: (course slug, section slug) -> planner or unclassified.
LAMAR_SECTION_PLANNERS: Final[dict[tuple[str, str], str]] = {
    # Calc II — integration techniques
    ("calc-ii", "integration-by-parts"): "plan_integration_by_parts",
    ("calc-ii", "partial-fractions"): "plan_partial_fractions",
    ("calc-ii", "trig-substitutions"): "plan_trig_substitution",
    ("calc-ii", "integrals-with-trig"): "plan_u_substitution",
    ("calc-ii", "integrals-with-roots"): "plan_u_substitution",
    ("calc-ii", "integrals-with-quadratics"): "plan_trig_substitution",
    ("calc-ii", "improper-integrals"): "plan_definite_integral",
    ("calc-ii", "improper-integrals-comp-test"): "plan_definite_integral",
    ("calc-ii", "approximating-def-integrals"): "plan_definite_integral",
    # Calc III — partials
    ("calc-iii", "partial-derivatives"): "plan_partial_derivative",
    ("calc-iii", "high-order-partial-derivs"): "plan_partial_derivative",
    ("calc-iii", "partial-deriv-interp"): "plan_partial_derivative",
    ("calc-iii", "chain-rule"): "plan_partial_derivative",
    ("calc-iii", "directional-deriv"): "plan_partial_derivative",
    ("calc-iii", "gradient-vector-tangent-plane"): "plan_partial_derivative",
    ("calc-iii", "tangent-planes"): "plan_partial_derivative",
    # Calc III — multiple integrals
    ("calc-iii", "double-integrals"): "plan_double_integral",
    ("calc-iii", "iterated-integrals"): "plan_double_integral",
    ("calc-iii", "digeneral-region"): "plan_double_integral",
    ("calc-iii", "dipolar-coords"): "plan_double_integral",
    ("calc-iii", "change-of-variables"): "plan_double_integral",
    ("calc-iii", "triple-integrals"): "plan_triple_integral",
    ("calc-iii", "ticylindrical-coords"): "plan_triple_integral",
    ("calc-iii", "tispherical-coords"): "plan_triple_integral",
    ("calc-iii", "cylindrical-coords"): "plan_triple_integral",
    ("calc-iii", "spherical-coords"): "plan_triple_integral",
}

# MIT manifest topic slugs -> planner.
MIT_TOPIC_PLANNERS: Final[dict[str, str]] = {
    "derivatives": "plan_derivative",
    "definite-integrals": "plan_definite_integral",
    "integration-techniques": "plan_definite_integral",
    "improper-integrals": "plan_definite_integral",
    "partial-derivatives": "plan_partial_derivative",
    "double-integrals": "plan_double_integral",
    "triple-integrals": "plan_triple_integral",
}

# Curated ladder filenames -> planner (for cross-linking into by-type batches).
CURATED_PLANNERS: Final[dict[str, str]] = {
    "02_linear_equation.txt": "plan_linear",
    "03_percent_off.txt": "plan_percent_off",
    "04_quadratic.txt": "plan_quadratic",
    "06_derivative.txt": "plan_derivative",
    "07_double_integral.md": "plan_double_integral",
    "09_improper_integral.md": "plan_definite_integral",
    "11_long_multiplication.txt": "plan_long_multiply",
    "12_long_division.txt": "plan_long_divide",
    "13_decimal_multiplication.txt": "plan_long_multiply",
    "14_long_addition.txt": "plan_long_add",
    "15_long_subtraction.txt": "plan_long_subtract",
    "16_linear_system_2d.txt": "plan_linear_system_2d",
    "17_linear_system_3d.txt": "plan_linear_system_3d",
    "18_lamar_integration_by_parts.txt": "plan_integration_by_parts",
    "19_mit_sine_integral.txt": "plan_definite_integral",
    "20_partial_derivative.txt": "plan_partial_derivative",
    "21_triple_integral.md": "plan_triple_integral",
}


def lamar_pack_id(course: str, section: str) -> str:
    return f"lamar-{course}-{section}"


def mit_pack_id(course: str, topic: str) -> str:
    return f"mit-{course}-{topic}"


def resolve_lamar_planner(course: str, section: str) -> str:
    return LAMAR_SECTION_PLANNERS.get((course, section), UNCLASSIFIED)


def resolve_mit_planner(topic: str) -> str:
    return MIT_TOPIC_PLANNERS.get(topic, UNCLASSIFIED)


def resolve_curated_planner(filename: str) -> str | None:
    return CURATED_PLANNERS.get(filename)
