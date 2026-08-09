from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from .formalism import (
    EquationKind,
    ExprOp,
    FormalEquation,
    FormalExpression,
    Formalism,
    MechanismEdge,
    MechanismRelation,
)


class InteractionAggregation(str, Enum):
    ADDITIVE = "ADDITIVE"
    MULTIPLICATIVE = "MULTIPLICATIVE"


@dataclass(frozen=True)
class InteractionLaw:
    """Formal contribution associated with one mechanism edge.

    `contribution` is expressed in the target symbol's update/rate units. The law may
    be supplied by literature, an LLM proposal, symbolic search, or a solver, but its
    provenance and applicability are explicit.
    """

    law_id: str
    edge_id: str
    contribution: FormalExpression
    target_symbol: str
    regime: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    declared_before_evaluation: Optional[bool] = None

    def __post_init__(self) -> None:
        if not self.law_id or not self.edge_id or not self.target_symbol:
            raise ValueError("law, edge and target identities are required")


@dataclass(frozen=True)
class StateEvolutionSpec:
    state_symbol: str
    clock_symbol: Optional[str]
    equation_kind: EquationKind = EquationKind.DIFFERENTIAL
    aggregation: InteractionAggregation = InteractionAggregation.ADDITIVE
    baseline: Optional[FormalExpression] = None
    regime: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()


class MechanismCompileVerdict(str, Enum):
    COMPILED = "COMPILED"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MechanismCompileReport:
    verdict: MechanismCompileVerdict
    reasons: Tuple[str, ...]
    equations: Tuple[FormalEquation, ...] = ()
    unused_law_ids: Tuple[str, ...] = ()
    missing_edge_ids: Tuple[str, ...] = ()


def _aggregate(expressions: Tuple[FormalExpression, ...], mode: InteractionAggregation) -> FormalExpression:
    if not expressions:
        return FormalExpression.const(0.0 if mode is InteractionAggregation.ADDITIVE else 1.0)
    if len(expressions) == 1:
        return expressions[0]
    return FormalExpression(
        ExprOp.ADD if mode is InteractionAggregation.ADDITIVE else ExprOp.MUL,
        args=expressions,
    )


def _lhs(spec: StateEvolutionSpec) -> FormalExpression:
    state = FormalExpression.sym(spec.state_symbol)
    if spec.equation_kind in {EquationKind.DIFFERENTIAL, EquationKind.STOCHASTIC}:
        if not spec.clock_symbol:
            raise ValueError("differential/stochastic evolution requires a clock symbol")
        return FormalExpression(
            ExprOp.DERIVATIVE,
            args=(state,),
            variable=spec.clock_symbol,
        )
    return state


def compile_mechanism_equations(
    formalism: Formalism,
    laws: Tuple[InteractionLaw, ...],
    specs: Tuple[StateEvolutionSpec, ...],
    *,
    equation_prefix: str = "compiled",
) -> MechanismCompileReport:
    """Compile graph interactions into explicit state equations.

    The compiler does not invent the edge laws. It makes the mapping from a proposed
    mechanism graph to mathematical dynamics explicit and checks that every supplied
    law points to a real graph edge and registered symbol. Missing influential edges
    are surfaced rather than silently ignored.
    """

    symbol_names = set(formalism.symbol_map())
    edges_by_id: Mapping[str, MechanismEdge] = {
        edge.edge_id: edge for edge in formalism.mechanism.edges
    }

    bad_laws: list[str] = []
    for law in laws:
        if law.edge_id not in edges_by_id:
            bad_laws.append(f"law_references_unknown_edge:{law.law_id}:{law.edge_id}")
        if law.target_symbol not in symbol_names:
            bad_laws.append(f"law_targets_unknown_symbol:{law.law_id}:{law.target_symbol}")
        if law.declared_before_evaluation is False:
            bad_laws.append(f"post_result_interaction_law:{law.law_id}")
        if not law.contribution.referenced_symbols().issubset(symbol_names):
            unknown = sorted(law.contribution.referenced_symbols() - symbol_names)
            bad_laws.append(f"law_references_unknown_symbols:{law.law_id}:{','.join(unknown)}")
    if bad_laws:
        return MechanismCompileReport(MechanismCompileVerdict.REJECT, tuple(bad_laws))

    if any(law.declared_before_evaluation is None for law in laws):
        return MechanismCompileReport(
            MechanismCompileVerdict.CANNOT_CHECK,
            ("one_or_more_interaction_law_chronologies_unknown",),
        )

    laws_by_target: dict[str, list[InteractionLaw]] = {}
    for law in laws:
        laws_by_target.setdefault(law.target_symbol, []).append(law)

    equations: list[FormalEquation] = []
    used_laws: set[str] = set()
    for index, spec in enumerate(specs):
        if spec.state_symbol not in symbol_names:
            return MechanismCompileReport(
                MechanismCompileVerdict.REJECT,
                (f"evolution_spec_unknown_state:{spec.state_symbol}",),
            )
        if spec.clock_symbol is not None and spec.clock_symbol not in symbol_names:
            return MechanismCompileReport(
                MechanismCompileVerdict.REJECT,
                (f"evolution_spec_unknown_clock:{spec.clock_symbol}",),
            )

        target_laws = tuple(laws_by_target.get(spec.state_symbol, ()))
        contributions = tuple(law.contribution for law in target_laws)
        used_laws.update(law.law_id for law in target_laws)
        rhs_terms = contributions
        if spec.baseline is not None:
            if not spec.baseline.referenced_symbols().issubset(symbol_names):
                return MechanismCompileReport(
                    MechanismCompileVerdict.REJECT,
                    (f"baseline_references_unknown_symbol:{spec.state_symbol}",),
                )
            rhs_terms = (spec.baseline,) + rhs_terms

        try:
            lhs = _lhs(spec)
        except ValueError as exc:
            return MechanismCompileReport(MechanismCompileVerdict.REJECT, (str(exc),))
        rhs = _aggregate(rhs_terms, spec.aggregation)
        equation = FormalEquation(
            equation_id=f"{equation_prefix}:{index}:{spec.state_symbol}",
            lhs=lhs,
            rhs=rhs,
            kind=spec.equation_kind,
            regime=tuple(dict.fromkeys(spec.regime + tuple(r for law in target_laws for r in law.regime))),
            assumptions=tuple(
                dict.fromkeys(spec.assumptions + tuple(a for law in target_laws for a in law.assumptions))
            ),
            derivation_ids=tuple(law.law_id for law in target_laws),
        )
        equations.append(equation)

    unused = tuple(sorted({law.law_id for law in laws} - used_laws))

    # Edges whose relation implies state influence should not disappear silently from
    # the compiled dynamics when they have a symbolic target state.
    target_symbol_by_node = {
        node.node_id: node.symbol for node in formalism.mechanism.nodes if node.symbol
    }
    influential = {
        MechanismRelation.CAUSES,
        MechanismRelation.MEDIATES,
        MechanismRelation.MODULATES,
        MechanismRelation.FEEDBACK,
        MechanismRelation.COUPLES,
        MechanismRelation.SWITCHES,
    }
    law_edge_ids = {law.edge_id for law in laws}
    missing_edges = []
    spec_states = {spec.state_symbol for spec in specs}
    for edge in formalism.mechanism.edges:
        target_symbol = target_symbol_by_node.get(edge.target)
        if edge.relation in influential and target_symbol in spec_states and edge.edge_id not in law_edge_ids:
            missing_edges.append(edge.edge_id)

    if missing_edges:
        return MechanismCompileReport(
            MechanismCompileVerdict.CANNOT_CHECK,
            ("mechanism_has_unformalized_influential_edges",),
            tuple(equations),
            unused,
            tuple(sorted(missing_edges)),
        )

    return MechanismCompileReport(
        MechanismCompileVerdict.COMPILED,
        (
            "mechanism_edges_bound_to_formal_interaction_laws",
            "state_evolution_equations_materialized",
            "interaction_law_lineage_preserved",
        ),
        tuple(equations),
        unused,
        (),
    )


def attach_compiled_equations(
    formalism: Formalism,
    report: MechanismCompileReport,
) -> Formalism:
    if report.verdict is not MechanismCompileVerdict.COMPILED:
        raise ValueError("only a fully compiled mechanism report can be attached")
    existing = {equation.equation_id for equation in formalism.equations}
    duplicate = existing.intersection(equation.equation_id for equation in report.equations)
    if duplicate:
        raise ValueError(f"compiled equation ids already exist: {sorted(duplicate)}")
    return Formalism(
        formalism_id=formalism.formalism_id,
        object_id=formalism.object_id,
        symbols=formalism.symbols,
        equations=formalism.equations + report.equations,
        mechanism=formalism.mechanism,
        assumptions=formalism.assumptions,
        regimes=formalism.regimes,
        invariants=formalism.invariants,
        limit_cases=formalism.limit_cases,
        observation_maps=formalism.observation_maps,
        symmetries=formalism.symmetries,
        boundary_conditions=formalism.boundary_conditions,
        parent_formalism_ids=formalism.parent_formalism_ids,
        invention_move_ids=formalism.invention_move_ids,
        evidence_ids=formalism.evidence_ids,
    )
