"""Shared helpers for single-variable integral catalog planners."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp
from sympy.integrals.manualintegrate import (
    AddRule,
    AlternativeRule,
    AtomicRule,
    ConstantTimesRule,
    CyclicPartsRule,
    DontKnowRule,
    PartsRule,
    RewriteRule,
    URule,
    integral_steps,
)

from cinemath.planners.calculus.bounds import _bound_tex, bound_as_float, bound_is_finite
from cinemath.planners.common import CatalogFreeform
from cinemath.render_engine.graph_2d import integral_plot_window

_SUB_VAR_NAMES = ("u", "v", "w", "t", "s", "p", "q", "r")


@dataclass(frozen=True)
class _SubContext:
    depth: int
    int_var: sp.Symbol
    int_var_name: str


def _sub_var_name(depth: int) -> str:
    if depth >= len(_SUB_VAR_NAMES):
        return f"u_{{{depth + 1}}}"
    return _SUB_VAR_NAMES[depth]


def _integration_d(ctx: _SubContext) -> str:
    return rf"\,d{ctx.int_var_name}"


def _display_expr(expr: sp.Expr, ctx: _SubContext) -> sp.Expr:
    if str(ctx.int_var) != ctx.int_var_name:
        return expr.xreplace({ctx.int_var: sp.Symbol(ctx.int_var_name)})
    return expr


def _expr_tex(expr: sp.Expr, ctx: _SubContext) -> str:
    return sp.latex(_display_expr(expr, ctx))


def integral_tex(
    integrand: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
) -> str:
    body = sp.latex(integrand)
    var = sp.latex(variable)
    if lower is None or upper is None:
        return rf"\int {body}\,d{var}"
    lo = _bound_tex(lower, str(variable))
    hi = _bound_tex(upper, str(variable))
    return rf"\int_{{{lo}}}^{{{hi}}} {body}\,d{var}"


def _is_display_ibp(rule: PartsRule | CyclicPartsRule) -> bool:
    """Skip SymPy's internal substitution PartsRule nodes (e.g. u = _u)."""
    if isinstance(rule, CyclicPartsRule):
        return all(_is_display_parts(parts) for parts in rule.parts_rules)
    return _is_display_parts(rule)


def _is_display_parts(parts: PartsRule) -> bool:
    u = parts.u
    if isinstance(u, sp.Symbol) and str(u).startswith("_"):
        return False
    return True


def find_ibp_step(step: Any) -> PartsRule | CyclicPartsRule | None:
    if isinstance(step, (PartsRule, CyclicPartsRule)):
        return step if _is_display_ibp(step) else None
    if isinstance(step, AlternativeRule):
        for alt in step.alternatives:
            if isinstance(alt, (PartsRule, CyclicPartsRule)) and _is_display_ibp(alt):
                return alt
        for alt in step.alternatives:
            found = find_ibp_step(alt)
            if found is not None:
                return found
    if isinstance(step, ConstantTimesRule):
        return find_ibp_step(step.substep)
    if isinstance(step, RewriteRule):
        return find_ibp_step(step.substep)
    if isinstance(step, URule):
        return find_ibp_step(step.substep)
    if isinstance(step, AddRule):
        for sub in step.substeps:
            found = find_ibp_step(sub)
            if found is not None:
                return found
    return None


def find_u_step(step: Any) -> URule | None:
    """Return a displayable u-substitution rule if one appears in the step tree."""
    if isinstance(step, URule):
        return step
    if isinstance(step, AlternativeRule):
        for alt in step.alternatives:
            found = find_u_step(alt)
            if found is not None:
                return found
    if isinstance(step, ConstantTimesRule):
        return find_u_step(step.substep)
    if isinstance(step, RewriteRule):
        return find_u_step(step.substep)
    if isinstance(step, AddRule):
        for sub in step.substeps:
            found = find_u_step(sub)
            if found is not None:
                return found
    return None


def _needs_partial_fractions(expr: sp.Expr, variable: sp.Symbol) -> bool:
    """True when the integrand needs nontrivial partial-fraction decomposition."""
    together = sp.together(expr)
    numer, denom = sp.fraction(together)
    if not denom.has(variable):
        return False
    if numer.as_poly(variable) is None or denom.as_poly(variable) is None:
        return False
    # Monomial denominators 1/x^n are power-rule integrals, not PFD exercises.
    if sp.simplify(numer - 1) == 0 and (
        denom == variable
        or (denom.is_Pow and denom.base == variable and denom.exp.is_Integer)
    ):
        return False
    return try_partial_fraction_steps(expr, variable) is not None


def requires_specialized_technique(expr: sp.Expr, variable: sp.Symbol) -> str | None:
    """Return the catalog planner name if expr needs a specialized technique."""
    root = integral_steps(expr, variable)
    if find_ibp_step(root) is not None:
        return "plan_integration_by_parts"
    if _needs_partial_fractions(expr, variable):
        return "plan_partial_fractions"
    from cinemath.planners.calculus.trig_substitution import try_trig_substitution_steps

    if try_trig_substitution_steps(expr, variable) is not None:
        return "plan_trig_substitution"
    if find_u_step(root) is not None:
        return "plan_u_substitution"
    return None


def reject_unwalkable_integral(expr: sp.Expr, variable: sp.Symbol) -> None:
    """Raise CatalogFreeform when SymPy has no manual-integration recipe."""
    root = integral_steps(expr, variable)
    if isinstance(root, DontKnowRule):
        raise CatalogFreeform(
            "This integral needs a custom multi-step approach; use teach_freeform."
        )


def verify_catalog_antideriv(
    antideriv: sp.Expr,
    expr: sp.Expr,
    variable: sp.Symbol,
) -> sp.Expr:
    """Ensure the planner produced a closed antiderivative, not an unevaluated integral."""
    if antideriv.has(sp.Integral):
        raise CatalogFreeform(
            "Catalog planners cannot finish this integral; use teach_freeform."
        )
    return antideriv


def pick_alternative(rule: AlternativeRule) -> Any:
    for alt in rule.alternatives:
        if not alt.contains_dont_know():
            return alt
    return rule.alternatives[0]


def _eval_at_bound(antideriv: sp.Expr, variable: sp.Symbol, bound: sp.Expr) -> sp.Expr:
    if bound is sp.oo:
        return sp.limit(antideriv, variable, sp.oo)
    if bound is -sp.oo:
        return sp.limit(antideriv, variable, -sp.oo)
    return sp.simplify(antideriv.subs(variable, bound))


def _at_bound_tex(antideriv: sp.Expr, variable: sp.Symbol, bound: sp.Expr) -> str:
    if bound is sp.oo:
        return rf"\lim_{{{sp.latex(variable)}\to \infty}} {sp.latex(antideriv)}"
    if bound is -sp.oo:
        return rf"\lim_{{{sp.latex(variable)}\to -\infty}} {sp.latex(antideriv)}"
    if bound.is_Integer or bound.is_Rational:
        return sp.latex(sp.simplify(antideriv.subs(variable, bound)))
    return sp.latex(antideriv.xreplace({variable: sp.UnevaluatedExpr(bound)}))


def _format_bound_difference(
    upper_tex: str,
    lower_tex: str,
    *,
    upper_val: sp.Expr | None = None,
    lower_val: sp.Expr | None = None,
) -> str:
    if lower_val is not None and lower_val == 0:
        return upper_tex
    if lower_val is not None and lower_val.is_Add:
        return rf"{upper_tex} - \left({lower_tex}\right)"
    if lower_tex.startswith("-") or lower_tex.startswith(r"\left(-"):
        return rf"{upper_tex} - \left({lower_tex}\right)"
    return rf"{upper_tex} - {lower_tex}"


def build_bound_evaluation_math(
    antideriv: sp.Expr,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
) -> list[str]:
    """Build FTC evaluation lines: bracket form, substitution, simplification, result."""
    antideriv_tex = sp.latex(antideriv)
    lo_tex, hi_tex = _bound_tex(lower, str(variable)), _bound_tex(upper, str(variable))
    lines = [rf"\left[{antideriv_tex}\right]_{{{lo_tex}}}^{{{hi_tex}}}"]

    sub_hi = _at_bound_tex(antideriv, variable, upper)
    sub_lo = _at_bound_tex(antideriv, variable, lower)
    at_hi = sp.simplify(_eval_at_bound(antideriv, variable, upper))
    at_lo = sp.simplify(_eval_at_bound(antideriv, variable, lower))

    substitution = _format_bound_difference(
        sub_hi,
        sub_lo,
        upper_val=at_hi,
        lower_val=at_lo,
    )
    lines.append(f"= {substitution}")

    eval_hi = sp.latex(at_hi)
    eval_lo = sp.latex(at_lo)
    if sub_hi != eval_hi or sub_lo != eval_lo:
        simplified = _format_bound_difference(
            eval_hi,
            eval_lo,
            upper_val=at_hi,
            lower_val=at_lo,
        )
        if simplified != substitution:
            lines.append(f"= {simplified}")

    value_tex = sp.latex(sp.simplify(at_hi - at_lo))
    if not lines[-1].endswith(value_tex):
        lines.append(f"= {value_tex}")

    return lines


def finalize_answer(
    expr: sp.Expr,
    variable: sp.Symbol,
    antideriv: sp.Expr,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
    steps: list[dict[str, Any]],
) -> tuple[str, str]:
    antideriv = sp.simplify(antideriv)
    if lower is not None and upper is not None:
        value = sp.integrate(expr, (variable, lower, upper))
        value_tex = sp.latex(value)
        improper = lower in (sp.oo, -sp.oo) or upper in (sp.oo, -sp.oo)
        steps.append(
            {
                "title": "Evaluate at the bounds",
                "explanation": (
                    "Take the limit of the antiderivative as the bound approaches infinity."
                    if improper
                    else "Apply the Fundamental Theorem of Calculus."
                ),
                "math": build_bound_evaluation_math(antideriv, variable, lower, upper),
            }
        )
        setup = integral_tex(expr, variable, lower=lower, upper=upper)
        return value_tex, rf"{setup} = {value_tex}"

    antideriv_tex = sp.latex(antideriv)
    return f"{antideriv_tex} + C", f"{antideriv_tex} + C"


def _append_step(
    steps: list[dict[str, Any]],
    *,
    title: str,
    explanation: str,
    math: list[str] | None = None,
    side_math: list[str] | None = None,
    side_begin: bool = False,
    side_hold: str | None = None,
    close_side: bool = False,
    break_spine: bool = False,
) -> None:
    payload: dict[str, Any] = {
        "title": title,
        "explanation": explanation,
    }
    if math:
        payload["math"] = math
    if side_math:
        payload["side_math"] = side_math
    if side_begin:
        payload["side_begin"] = True
    if side_hold:
        payload["side_hold"] = side_hold
    if close_side:
        payload["close_side"] = True
    if break_spine:
        payload["break_spine"] = True
    steps.append(payload)


def _atomic_title(rule: Any) -> str:
    name = type(rule).__name__
    mapping = {
        "SinRule": "Integrate $\\sin(x)$",
        "CosRule": "Integrate $\\cos(x)$",
        "ExpRule": "Integrate an exponential",
        "PowerRule": "Apply the power rule",
        "ReciprocalRule": "Integrate a reciprocal",
        "ArcsinRule": "Integrate to $\\arcsin$",
        "ArctanRule": "Integrate to $\\arctan$",
        "Sec2Rule": "Integrate $\\sec^2(x)$",
        "Csc2Rule": "Integrate $\\csc^2(x)$",
    }
    return mapping.get(name, "Integrate")


def _walk_rule(
    rule: Any,
    steps: list[dict[str, Any]],
    ctx: _SubContext,
) -> sp.Expr:
    if isinstance(rule, AlternativeRule):
        return _walk_rule(pick_alternative(rule), steps, ctx)

    if isinstance(rule, RewriteRule):
        _append_step(
            steps,
            title="Rewrite the integrand",
            explanation="Use an algebra or trig identity so the integral is easier.",
            math=[
                rf"\int {_expr_tex(rule.integrand, ctx)}{_integration_d(ctx)} "
                rf"= \int {_expr_tex(rule.rewritten, ctx)}{_integration_d(ctx)}",
            ],
        )
        return _walk_rule(rule.substep, steps, ctx)

    if isinstance(rule, ConstantTimesRule):
        _append_step(
            steps,
            title="Pull out the constant",
            explanation="Move a constant factor outside the integral.",
            math=[
                rf"\int {_expr_tex(rule.integrand, ctx)}{_integration_d(ctx)} "
                rf"= {_expr_tex(rule.constant, ctx)} \int {_expr_tex(rule.other, ctx)}{_integration_d(ctx)}",
            ],
        )
        return sp.simplify(rule.constant * _walk_rule(rule.substep, steps, ctx))

    if isinstance(rule, URule):
        new_name = _sub_var_name(ctx.depth)
        du = sp.diff(rule.u_func, ctx.int_var)
        _append_step(
            steps,
            title="Use substitution",
            explanation=(
                f"Choose ${new_name}$ so the integral becomes a simpler form in ${new_name}$."
            ),
            math=[
                rf"{new_name} = {_expr_tex(rule.u_func, ctx)}",
                rf"d{new_name} = {_expr_tex(du, ctx)}{_integration_d(ctx)}",
            ],
        )
        child_ctx = _SubContext(
            depth=ctx.depth + 1,
            int_var=rule.u_var,
            int_var_name=new_name,
        )
        sub_result = _walk_rule(rule.substep, steps, child_ctx)
        result = sp.simplify(sub_result.subs(rule.u_var, rule.u_func))
        _append_step(
            steps,
            title="Substitute back",
            explanation=f"Replace ${new_name}$ with ${_expr_tex(rule.u_func, ctx)}$.",
            math=[rf"= {_expr_tex(result, ctx)}"],
        )
        return result

    if isinstance(rule, AddRule):
        terms = [sub.integrand for sub in rule.substeps]
        _append_step(
            steps,
            title="Split the integral",
            explanation="Integrate term by term.",
            math=[
                rf"\int {_expr_tex(rule.integrand, ctx)}{_integration_d(ctx)} = "
                + " + ".join(
                    rf"\int {_expr_tex(term, ctx)}{_integration_d(ctx)}" for term in terms
                ),
            ],
        )
        parts = [_walk_rule(sub, steps, ctx) for sub in rule.substeps]
        return sp.simplify(sum(parts))

    if isinstance(rule, AtomicRule):
        result = sp.simplify(rule.eval())
        _append_step(
            steps,
            title=_atomic_title(rule),
            explanation="Apply a standard antiderivative rule.",
            math=[
                rf"\int {_expr_tex(rule.integrand, ctx)}{_integration_d(ctx)} = {_expr_tex(result, ctx)}",
            ],
        )
        return result

    if isinstance(rule, DontKnowRule):
        result = sp.simplify(sp.integrate(rule.integrand, ctx.int_var))
        if result.has(sp.Integral):
            raise CatalogFreeform(
                "Catalog planners cannot walk this sub-integral; use teach_freeform."
            )
        _append_step(
            steps,
            title="Integrate",
            explanation="Apply a standard antiderivative rule.",
            math=[
                rf"\int {_expr_tex(rule.integrand, ctx)}{_integration_d(ctx)} = {_expr_tex(result, ctx)}",
            ],
        )
        return result

    result = sp.simplify(rule.eval())
    _append_step(
        steps,
        title="Integrate",
        explanation="Combine the previous substitution or rewrite with a standard rule.",
        math=[rf"= {_expr_tex(result, ctx)}"],
    )
    return result


def _pfd_power_label(variable: sp.Symbol, power: int) -> str:
    if power == 0:
        return r"\text{constant}"
    if power == 1:
        return sp.latex(variable)
    return sp.latex(variable**power)


def _build_pfd_template(
    factor_list: list[tuple[sp.Expr, int]],
    variable: sp.Symbol,
) -> tuple[sp.Expr, list[sp.Symbol]] | None:
    """Undetermined-coefficient template from a factored denominator."""
    terms: list[sp.Expr] = []
    symbols: list[sp.Symbol] = []
    index = 0

    for factor, multiplicity in factor_list:
        degree = sp.degree(factor, variable)
        if degree == 1:
            for power in range(1, multiplicity + 1):
                coeff = sp.Symbol(f"a_{{{index}}}")
                index += 1
                symbols.append(coeff)
                terms.append(coeff / factor**power)
            continue
        if degree == 2 and multiplicity == 1:
            a = sp.Symbol(f"a_{{{index}}}")
            b = sp.Symbol(f"b_{{{index}}}")
            index += 1
            symbols.extend([a, b])
            terms.append((a * variable + b) / factor)
            continue
        return None

    if not terms:
        return None
    return sp.simplify(sum(terms)), symbols


def _template_cleared_polynomial(
    numer: sp.Expr,
    denom: sp.Expr,
    template: sp.Expr,
    variable: sp.Symbol,
) -> sp.Expr:
    """Polynomial obtained by clearing denominators in a PFD template."""
    factored_denom = sp.factor(denom, variable)
    return sp.expand(numer - sp.together(template * factored_denom, variable), variable)


def _template_cleared_rhs(
    denom: sp.Expr,
    template: sp.Expr,
    variable: sp.Symbol,
) -> sp.Expr:
    factored_denom = sp.factor(denom, variable)
    return sp.expand(sp.together(template * factored_denom, variable), variable)


def _solve_pfd_coefficients(
    numer: sp.Expr,
    denom: sp.Expr,
    template: sp.Expr,
    symbols: list[sp.Symbol],
    variable: sp.Symbol,
) -> dict[sp.Symbol, sp.Expr] | None:
    """Solve for template coefficients by equating powers of the variable."""
    cleared = _template_cleared_polynomial(numer, denom, template, variable)
    if cleared == 0:
        return {symbol: sp.Integer(0) for symbol in symbols}

    degree = sp.Poly(cleared, variable).degree()
    equations: list[sp.Eq] = []
    for power in range(degree + 1):
        coefficient = sp.expand(cleared.coeff(variable, power))
        if coefficient != 0:
            equations.append(sp.Eq(coefficient, 0))

    if not equations:
        return None

    solutions = sp.solve(equations, symbols, dict=True)
    if not solutions:
        return None
    return solutions[0]


def _format_pfd_solution(solution: dict[sp.Symbol, sp.Expr]) -> list[str]:
    parts = [
        rf"{sp.latex(symbol)} = {sp.latex(sp.simplify(value))}"
        for symbol, value in solution.items()
    ]
    return [r",\quad ".join(parts)]


def _append_pfd_algebra_steps(
    steps: list[dict[str, Any]],
    *,
    together: sp.Expr,
    numer: sp.Expr,
    denom: sp.Expr,
    variable: sp.Symbol,
    factor_list: list[tuple[sp.Expr, int]],
    factored_denom: sp.Expr | None = None,
) -> sp.Expr | None:
    """Show template, cleared denominators, coefficient system on a side column."""
    built = _build_pfd_template(factor_list, variable)
    if built is None:
        return None
    template, symbols = built

    side_hold = rf"\frac{{{sp.latex(numer)}}}{{{sp.latex(denom)}}}"
    side_lines: list[str] = []
    if factored_denom is not None and factored_denom != denom:
        side_lines.append(f"{sp.latex(denom)} = {sp.latex(factored_denom)}")
    side_lines.append(rf"{side_hold} = {sp.latex(template)}")

    _append_step(
        steps,
        title="Write the decomposition form",
        explanation=(
            "For each linear factor $x-a$, include terms $A/(x-a)^k$. "
            "For each irreducible quadratic, use $(Ax+B)/Q(x)$."
        ),
        side_begin=True,
        side_hold=side_hold,
        side_math=side_lines,
    )

    cleared_rhs = _template_cleared_rhs(denom, template, variable)
    _append_step(
        steps,
        title="Clear denominators",
        explanation="Multiply both sides by the factored denominator so we can compare polynomials.",
        side_math=[rf"{sp.latex(numer)} = {sp.latex(cleared_rhs)}"],
    )

    solution = _solve_pfd_coefficients(numer, denom, template, symbols, variable)
    if solution is None:
        return None

    cleared = _template_cleared_polynomial(numer, denom, template, variable)
    degree = sp.Poly(cleared, variable).degree()
    coefficient_lines = [
        rf"\text{{coeff of }}{_pfd_power_label(variable, power)}:\ "
        rf"{sp.latex(sp.expand(cleared.coeff(variable, power)))} = 0"
        for power in range(degree + 1)
        if sp.expand(cleared.coeff(variable, power)) != 0
    ]
    _append_step(
        steps,
        title="Equate coefficients",
        explanation="Match coefficients of each power of the variable to solve for the unknowns.",
        side_math=coefficient_lines + _format_pfd_solution(solution),
    )

    decomposed = sp.simplify(template.subs(solution))
    verified = sp.apart(together, variable)
    if sp.simplify(sp.together(decomposed - verified)) != 0:
        return None
    return verified


def _integrate_with_walk_steps(
    steps: list[dict[str, Any]],
    integrand: sp.Expr,
    variable: sp.Symbol,
    *,
    label: str,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> sp.Expr:
    """Integrate one addend with SymPy's manual-integration walk."""
    sub_steps, antideriv = walk_integral_steps(
        integrand,
        variable,
        lower=lower,
        upper=upper,
        include_setup=False,
    )
    if label:
        sub_steps = [{**step, "title": f"{label}: {step['title']}"} for step in sub_steps]
    steps.extend(sub_steps)
    return verify_catalog_antideriv(antideriv, integrand, variable)


def _integrate_decomposed_terms(
    steps: list[dict[str, Any]],
    terms: list[sp.Expr],
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> sp.Expr:
    """Integrate each partial-fraction addend and collect the antiderivative."""
    results: list[sp.Expr] = []
    for index, term in enumerate(terms, start=1):
        results.append(
            _integrate_with_walk_steps(
                steps,
                term,
                variable,
                label=f"Term {index}",
                lower=lower,
                upper=upper,
            )
        )
    return sp.simplify(sum(results))


def try_partial_fraction_steps(
    expr: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
) -> tuple[list[dict[str, Any]], sp.Expr] | None:
    """Deterministic partial-fraction steps for rational integrands."""
    together = sp.together(expr)
    numer, denom = sp.fraction(together)
    if not denom.has(variable):
        return None

    setup = integral_tex(together, variable, lower=lower, upper=upper)
    steps: list[dict[str, Any]] = [
        {
            "title": "Set up the integral",
            "explanation": "Identify a rational integrand.",
            "math": [setup],
        }
    ]

    quotient, remainder = sp.div(numer, denom, variable)
    proper: sp.Expr
    if sp.simplify(quotient) != 0:
        proper = sp.together(remainder / denom)
        _append_step(
            steps,
            title="Polynomial long division",
            explanation=(
                "The numerator degree is at least the denominator degree, "
                "so divide first to get a polynomial plus a proper fraction."
            ),
            math=[
                rf"\frac{{{sp.latex(numer)}}}{{{sp.latex(denom)}}} = "
                rf"{sp.latex(quotient)} + {sp.latex(proper)}",
            ],
        )
    else:
        proper = together

    factored_denom = sp.factor(denom)
    factor_list = sp.factor_list(denom, variable)[1]

    decomposed = _append_pfd_algebra_steps(
        steps,
        together=proper,
        numer=sp.fraction(proper)[0],
        denom=sp.fraction(proper)[1],
        variable=variable,
        factor_list=factor_list,
        factored_denom=factored_denom,
    )
    if decomposed is None:
        return None

    integration_terms: list[sp.Expr] = []
    if sp.simplify(quotient) != 0:
        integration_terms.append(quotient)
    integration_terms.extend(decomposed.args if decomposed.is_Add else [decomposed])

    split_rhs_parts = [
        integral_tex(term, variable, lower=lower, upper=upper)
        for term in integration_terms
    ]
    _append_step(
        steps,
        title="Split the integral",
        explanation="Integrate the polynomial part (if any) and each partial fraction separately.",
        close_side=True,
        break_spine=True,
        math=[setup, "= " + " + ".join(split_rhs_parts)],
    )

    antideriv_parts: list[sp.Expr] = []
    if sp.simplify(quotient) != 0:
        antideriv_parts.append(
            _integrate_with_walk_steps(
                steps,
                quotient,
                variable,
                label="Polynomial part",
                lower=lower,
                upper=upper,
            )
        )

    fraction_terms = list(decomposed.args) if decomposed.is_Add else [decomposed]
    antideriv_parts.append(
        _integrate_decomposed_terms(
            steps,
            fraction_terms,
            variable,
            lower=lower,
            upper=upper,
        )
    )
    antideriv = sp.simplify(sum(antideriv_parts))

    combined = sp.simplify(antideriv)
    _append_step(
        steps,
        title="Combine",
        explanation="Collect logarithms using log rules when possible.",
        math=[rf"= {sp.latex(combined)}"],
    )
    return steps, combined


def walk_integral_steps(
    expr: sp.Expr,
    variable: sp.Symbol,
    *,
    lower: sp.Expr | None = None,
    upper: sp.Expr | None = None,
    include_setup: bool = True,
) -> tuple[list[dict[str, Any]], sp.Expr]:
    """Build teaching steps from SymPy manual integration rules."""
    setup = integral_tex(expr, variable, lower=lower, upper=upper)
    improper = (
        lower is not None
        and upper is not None
        and (lower in (sp.oo, -sp.oo) or upper in (sp.oo, -sp.oo))
    )
    steps: list[dict[str, Any]] = []
    if include_setup:
        steps.append(
            {
                "title": "Set up the integral",
                "explanation": (
                    "This is an improper integral — evaluate it as a limit."
                    if improper
                    else "Identify the integrand and variable of integration."
                ),
                "math": [setup],
            }
        )
    root = integral_steps(expr, variable)
    sub_ctx = _SubContext(
        depth=0,
        int_var=variable,
        int_var_name=str(variable),
    )
    antideriv = _walk_rule(root, steps, sub_ctx)
    antideriv = verify_catalog_antideriv(antideriv, expr, variable)
    simplified = sp.simplify(antideriv)
    if simplified != antideriv:
        antideriv = simplified
        _append_step(
            steps,
            title="Simplify the antiderivative",
            explanation="Combine terms to reach the final form.",
            math=[rf"= {sp.latex(antideriv)}"],
        )
    return steps, antideriv


def integral_1d_visual(
    expression: str,
    variable: str,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
) -> dict[str, Any] | None:
    """Build a shaded 1D integral plot visual when both bounds are present."""
    if lower is None or upper is None or variable != "x":
        return None

    lo_f = bound_as_float(lower) if bound_is_finite(lower) else None
    hi_f = bound_as_float(upper) if bound_is_finite(upper) else None
    x_lo, x_hi, shade_lo, shade_hi = integral_plot_window(lo_f, hi_f)

    return {
        "tool": "plot_integral_1d",
        "expr": expression,
        "x_min": x_lo,
        "x_max": x_hi,
        "shade_min": shade_lo,
        "shade_max": shade_hi,
        "lower": lo_f,
        "upper": hi_f,
        "lower_infinite": not bound_is_finite(lower),
        "upper_infinite": not bound_is_finite(upper),
    }


def definite_integral_visuals(
    *,
    expression: str,
    variable: str,
    lower: sp.Expr | None,
    upper: sp.Expr | None,
    answer_tex: str,
    caption: str,
) -> list[dict[str, Any]]:
    visuals: list[dict[str, Any]] = []
    plot = integral_1d_visual(expression, variable, lower, upper)
    if plot is not None:
        visuals.append(plot)
    visuals.append({"tool": "equation_board"})
    visuals.append({"tool": "show_answer", "tex": answer_tex, "caption": caption})
    return visuals
