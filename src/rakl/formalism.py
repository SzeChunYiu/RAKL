from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterable, Mapping, Optional, Tuple


class SymbolRole(str, Enum):
    STATE = "STATE"
    LATENT_STATE = "LATENT_STATE"
    OBSERVABLE = "OBSERVABLE"
    PARAMETER = "PARAMETER"
    CONTROL = "CONTROL"
    NOISE = "NOISE"
    CLOCK = "CLOCK"
    REGIME = "REGIME"
    AUXILIARY = "AUXILIARY"


class ExprOp(str, Enum):
    SYMBOL = "SYMBOL"
    CONSTANT = "CONSTANT"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    POW = "POW"
    NEG = "NEG"
    FUNCTION = "FUNCTION"
    DERIVATIVE = "DERIVATIVE"
    EXPECTATION = "EXPECTATION"
    SUM = "SUM"
    INTEGRAL = "INTEGRAL"
    PIECEWISE = "PIECEWISE"


@dataclass(frozen=True)
class FormalExpression:
    """Small typed mathematical AST used by RAKL candidate theories.

    RAKL deliberately stores mathematical structure rather than only display text.
    More sophisticated CAS/proof backends can translate this tree into native forms.
    """

    op: ExprOp
    args: Tuple["FormalExpression", ...] = ()
    symbol: Optional[str] = None
    value: Optional[float] = None
    function_name: Optional[str] = None
    variable: Optional[str] = None
    order: int = 1
    metadata: Mapping[str, str] = field(default_factory=dict)

    @staticmethod
    def sym(name: str) -> "FormalExpression":
        return FormalExpression(ExprOp.SYMBOL, symbol=name)

    @staticmethod
    def const(value: float) -> "FormalExpression":
        return FormalExpression(ExprOp.CONSTANT, value=float(value))

    def referenced_symbols(self) -> frozenset[str]:
        refs: set[str] = set()
        if self.op is ExprOp.SYMBOL and self.symbol:
            refs.add(self.symbol)
        if self.variable:
            refs.add(self.variable)
        for arg in self.args:
            refs.update(arg.referenced_symbols())
        return frozenset(refs)


class EquationKind(str, Enum):
    DEFINITION = "DEFINITION"
    ALGEBRAIC = "ALGEBRAIC"
    DIFFERENTIAL = "DIFFERENTIAL"
    STOCHASTIC = "STOCHASTIC"
    STRUCTURAL = "STRUCTURAL"
    OBSERVATION = "OBSERVATION"
    CONSTRAINT = "CONSTRAINT"
    OBJECTIVE = "OBJECTIVE"


@dataclass(frozen=True)
class FormalSymbol:
    name: str
    role: SymbolRole
    domain: str
    units: Optional[str] = None
    description: str = ""
    observable_at_decision_time: Optional[bool] = None


@dataclass(frozen=True)
class FormalEquation:
    equation_id: str
    lhs: FormalExpression
    rhs: FormalExpression
    kind: EquationKind
    regime: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    unit_balance_passed: Optional[bool] = None
    derivation_ids: Tuple[str, ...] = ()

    def referenced_symbols(self) -> frozenset[str]:
        return self.lhs.referenced_symbols() | self.rhs.referenced_symbols()


@dataclass(frozen=True)
class LimitCase:
    case_id: str
    description: str
    expected_behavior: str
    verified: Optional[bool] = None


@dataclass(frozen=True)
class Invariant:
    invariant_id: str
    statement: str
    regime: Tuple[str, ...] = ()
    verified: Optional[bool] = None


@dataclass(frozen=True)
class ObservationMap:
    map_id: str
    latent_symbols: Tuple[str, ...]
    observed_symbols: Tuple[str, ...]
    operator: FormalExpression
    assumptions: Tuple[str, ...] = ()


class MechanismNodeKind(str, Enum):
    ENTITY = "ENTITY"
    STATE = "STATE"
    LATENT_STATE = "LATENT_STATE"
    OBSERVABLE = "OBSERVABLE"
    SHOCK = "SHOCK"
    CLOCK = "CLOCK"
    REGIME = "REGIME"


class MechanismRelation(str, Enum):
    CAUSES = "CAUSES"
    MEDIATES = "MEDIATES"
    MODULATES = "MODULATES"
    CONSTRAINS = "CONSTRAINS"
    OBSERVES = "OBSERVES"
    FEEDBACK = "FEEDBACK"
    COUPLES = "COUPLES"
    SWITCHES = "SWITCHES"


@dataclass(frozen=True)
class MechanismNode:
    node_id: str
    kind: MechanismNodeKind
    label: str
    symbol: Optional[str] = None
    evidence_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MechanismEdge:
    edge_id: str
    source: str
    target: str
    relation: MechanismRelation
    sign: Optional[int] = None
    lag: Optional[str] = None
    regime: Tuple[str, ...] = ()
    mediator: Optional[str] = None
    evidence_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sign not in (None, -1, 0, 1):
            raise ValueError("sign must be one of None, -1, 0, 1")


@dataclass(frozen=True)
class MechanismGraph:
    mechanism_id: str
    nodes: Tuple[MechanismNode, ...]
    edges: Tuple[MechanismEdge, ...]
    regime: Tuple[str, ...] = ()
    falsifiers: Tuple[str, ...] = ()
    source_fiber_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Formalism:
    formalism_id: str
    object_id: str
    symbols: Tuple[FormalSymbol, ...]
    equations: Tuple[FormalEquation, ...]
    mechanism: MechanismGraph
    assumptions: Tuple[str, ...] = ()
    regimes: Tuple[str, ...] = ()
    invariants: Tuple[Invariant, ...] = ()
    limit_cases: Tuple[LimitCase, ...] = ()
    observation_maps: Tuple[ObservationMap, ...] = ()
    symmetries: Tuple[str, ...] = ()
    boundary_conditions: Tuple[str, ...] = ()
    parent_formalism_ids: Tuple[str, ...] = ()
    invention_move_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()

    def symbol_map(self) -> dict[str, FormalSymbol]:
        return {symbol.name: symbol for symbol in self.symbols}

    def with_symbol(self, symbol: FormalSymbol) -> "Formalism":
        if symbol.name in self.symbol_map():
            raise ValueError(f"symbol already exists: {symbol.name}")
        return replace(self, symbols=self.symbols + (symbol,))

    def with_equation(self, equation: FormalEquation) -> "Formalism":
        if any(item.equation_id == equation.equation_id for item in self.equations):
            raise ValueError(f"equation already exists: {equation.equation_id}")
        return replace(self, equations=self.equations + (equation,))


class FormalismStructureVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class FormalismStructureReport:
    verdict: FormalismStructureVerdict
    reasons: Tuple[str, ...]
    unknown_symbols: Tuple[str, ...] = ()


def validate_formalism_structure(formalism: Formalism) -> FormalismStructureReport:
    reasons: list[str] = []
    symbol_names = [symbol.name for symbol in formalism.symbols]
    if not formalism.formalism_id or not formalism.object_id:
        reasons.append("formalism_or_object_identity_missing")
    if not formalism.mechanism.mechanism_id:
        reasons.append("mechanism_identity_missing")
    if len(symbol_names) != len(set(symbol_names)):
        reasons.append("duplicate_symbol_name")

    equation_ids = [equation.equation_id for equation in formalism.equations]
    if len(equation_ids) != len(set(equation_ids)):
        reasons.append("duplicate_equation_id")

    known = set(symbol_names)
    referenced: set[str] = set()
    for equation in formalism.equations:
        referenced.update(equation.referenced_symbols())
    for observation_map in formalism.observation_maps:
        referenced.update(observation_map.latent_symbols)
        referenced.update(observation_map.observed_symbols)
        referenced.update(observation_map.operator.referenced_symbols())
    unknown = tuple(sorted(referenced - known))
    if unknown:
        reasons.append("formal_expression_references_unknown_symbols")

    node_ids = [node.node_id for node in formalism.mechanism.nodes]
    if len(node_ids) != len(set(node_ids)):
        reasons.append("duplicate_mechanism_node_id")
    node_set = set(node_ids)
    for edge in formalism.mechanism.edges:
        if edge.source not in node_set or edge.target not in node_set:
            reasons.append(f"mechanism_edge_has_unknown_endpoint:{edge.edge_id}")
        if edge.mediator is not None and edge.mediator not in node_set:
            reasons.append(f"mechanism_edge_has_unknown_mediator:{edge.edge_id}")

    if reasons:
        return FormalismStructureReport(
            FormalismStructureVerdict.REJECT,
            tuple(reasons),
            unknown,
        )

    if not formalism.equations:
        return FormalismStructureReport(
            FormalismStructureVerdict.CANNOT_CHECK,
            ("no_formal_equations_registered",),
        )

    return FormalismStructureReport(
        FormalismStructureVerdict.VALID,
        (
            "typed_symbols_unique",
            "formal_expression_references_resolve",
            "mechanism_graph_endpoints_resolve",
            "equation_identity_unique",
        ),
    )


class VerificationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class VerificationPacket:
    """External-oracle results bound to one exact candidate formalism."""

    formalism_id: str
    dimensional_analysis_passed: Optional[bool] = None
    limiting_cases_passed: Optional[bool] = None
    invariants_passed: Optional[bool] = None
    stability_passed: Optional[bool] = None
    identifiability_passed: Optional[bool] = None
    simulation_sanity_passed: Optional[bool] = None
    leakage_checks_passed: Optional[bool] = None
    falsifier_execution_passed: Optional[bool] = None
    evidence_lineage_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class VerificationReport:
    verdict: VerificationVerdict
    reasons: Tuple[str, ...]
    failed_checks: Tuple[str, ...] = ()
    unresolved_checks: Tuple[str, ...] = ()


_REQUIRED_ORACLE_FIELDS = (
    "dimensional_analysis_passed",
    "limiting_cases_passed",
    "invariants_passed",
    "stability_passed",
    "identifiability_passed",
    "simulation_sanity_passed",
    "leakage_checks_passed",
    "falsifier_execution_passed",
)


def verify_formalism(
    formalism: Formalism,
    packet: VerificationPacket,
    *,
    required_checks: Iterable[str] = _REQUIRED_ORACLE_FIELDS,
) -> VerificationReport:
    structure = validate_formalism_structure(formalism)
    if structure.verdict is FormalismStructureVerdict.REJECT:
        return VerificationReport(
            VerificationVerdict.FAIL,
            ("formalism_structure_rejected",) + structure.reasons,
            ("structure",),
        )
    if structure.verdict is FormalismStructureVerdict.CANNOT_CHECK:
        return VerificationReport(
            VerificationVerdict.CANNOT_CHECK,
            ("formalism_structure_incomplete",) + structure.reasons,
            unresolved_checks=("structure",),
        )
    if packet.formalism_id != formalism.formalism_id:
        return VerificationReport(
            VerificationVerdict.FAIL,
            ("verification_packet_bound_to_wrong_formalism",),
            ("candidate_identity",),
        )
    if not packet.evidence_lineage_ids:
        return VerificationReport(
            VerificationVerdict.CANNOT_CHECK,
            ("verification_evidence_lineage_missing",),
            unresolved_checks=("evidence_lineage",),
        )

    failed: list[str] = []
    unresolved: list[str] = []
    for name in required_checks:
        if not hasattr(packet, name):
            raise ValueError(f"unknown verification check: {name}")
        value = getattr(packet, name)
        if value is False:
            failed.append(name)
        elif value is None:
            unresolved.append(name)

    unit_failures = [
        equation.equation_id
        for equation in formalism.equations
        if equation.unit_balance_passed is False
    ]
    if unit_failures:
        failed.extend(f"equation_unit_balance:{item}" for item in unit_failures)

    if failed:
        return VerificationReport(
            VerificationVerdict.FAIL,
            tuple(f"verification_failed:{item}" for item in failed),
            tuple(failed),
            tuple(unresolved),
        )
    if unresolved:
        return VerificationReport(
            VerificationVerdict.CANNOT_CHECK,
            tuple(f"verification_unresolved:{item}" for item in unresolved),
            unresolved_checks=tuple(unresolved),
        )

    return VerificationReport(
        VerificationVerdict.PASS,
        (
            "formalism_structure_valid",
            "required_formal_and_empirical_oracles_passed",
            "verification_bound_to_exact_candidate",
            "evidence_lineage_present",
        ),
    )
