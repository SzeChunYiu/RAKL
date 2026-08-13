from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping

from .evolution import EvolutionVerdict
from .mechanic_diagnosis import MechanicCause


class EvolutionLayer(str, Enum):
    """Mutable layers of the RAKL/ORION method stack.

    The ordering is conceptual rather than an authority hierarchy.  In
    particular, representation, ontology, topology, evaluator policy, the
    meta-policy that chooses mutations, and the mutation language itself are
    first-class research objects rather than fixed assumptions.
    """

    IMPLEMENTATION = "IMPLEMENTATION"
    WORKFLOW = "WORKFLOW"
    SEARCH_OPERATOR = "SEARCH_OPERATOR"
    REPRESENTATION = "REPRESENTATION"
    ONTOLOGY = "ONTOLOGY"
    TOPOLOGY = "TOPOLOGY"
    EVALUATOR = "EVALUATOR"
    META_POLICY = "META_POLICY"
    MUTATION_LANGUAGE = "MUTATION_LANGUAGE"
    CONSTITUTION = "CONSTITUTION"


class SelfEvolutionAction(str, Enum):
    KEEP_INCUMBENT = "KEEP_INCUMBENT"
    RUN_DISCRIMINATOR = "RUN_DISCRIMINATOR"
    PROPOSE_MUTATION = "PROPOSE_MUTATION"


@dataclass(frozen=True)
class MethodGenome:
    """Versioned identifiers for the method surfaces that may be challenged.

    Surface identifiers are deliberately open strings.  The engine therefore
    does not assume that a recursive/fractal topology, a particular ontology,
    or a particular representation language is the final substrate.
    """

    version_id: str
    implementation_id: str = "incumbent_implementation"
    workflow_id: str = "incumbent_workflow"
    search_operator_basis_id: str = "incumbent_operator_basis"
    representation_id: str = "incumbent_representation"
    ontology_id: str = "incumbent_ontology"
    topology_id: str = "incumbent_topology"
    evaluator_id: str = "incumbent_evaluator"
    meta_policy_id: str = "incumbent_meta_policy"
    mutation_language_id: str = "incumbent_mutation_language"

    def __post_init__(self) -> None:
        values = (
            self.version_id,
            self.implementation_id,
            self.workflow_id,
            self.search_operator_basis_id,
            self.representation_id,
            self.ontology_id,
            self.topology_id,
            self.evaluator_id,
            self.meta_policy_id,
            self.mutation_language_id,
        )
        if any(not value for value in values):
            raise ValueError("method genome identifiers cannot be empty")


@dataclass(frozen=True)
class GenomeMutation:
    mutation_id: str
    operator_id: str
    target_layer: EvolutionLayer
    replacement_id: str
    rationale: str
    predicted_qoi_deltas: tuple[tuple[str, float], ...] = ()
    falsifier_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.mutation_id or not self.operator_id or not self.replacement_id:
            raise ValueError("mutation requires id, operator id, and replacement id")
        if self.target_layer is EvolutionLayer.CONSTITUTION:
            raise ValueError("constitutional amendments are not materialized as ordinary genome mutations")
        if len({name for name, _ in self.predicted_qoi_deltas}) != len(self.predicted_qoi_deltas):
            raise ValueError("predicted QoI names must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


_GENOME_FIELD_BY_LAYER: Mapping[EvolutionLayer, str] = {
    EvolutionLayer.IMPLEMENTATION: "implementation_id",
    EvolutionLayer.WORKFLOW: "workflow_id",
    EvolutionLayer.SEARCH_OPERATOR: "search_operator_basis_id",
    EvolutionLayer.REPRESENTATION: "representation_id",
    EvolutionLayer.ONTOLOGY: "ontology_id",
    EvolutionLayer.TOPOLOGY: "topology_id",
    EvolutionLayer.EVALUATOR: "evaluator_id",
    EvolutionLayer.META_POLICY: "meta_policy_id",
    EvolutionLayer.MUTATION_LANGUAGE: "mutation_language_id",
}


def materialize_challenger_genome(
    parent: MethodGenome,
    mutation: GenomeMutation,
    *,
    child_version_id: str,
) -> MethodGenome:
    """Create an immutable challenger genome; never promote it implicitly."""

    if not child_version_id or child_version_id == parent.version_id:
        raise ValueError("child version id must be new and non-empty")
    field_name = _GENOME_FIELD_BY_LAYER.get(mutation.target_layer)
    if field_name is None:
        raise ValueError("target layer is not an ordinary mutable genome surface")
    return replace(parent, version_id=child_version_id, **{field_name: mutation.replacement_id})


@dataclass(frozen=True)
class EvolutionPortrait:
    causes: tuple[MechanicCause, ...]
    stagnant: bool
    knowledge_gain_positive: bool = False
    same_layer_failed_generations: int = 0
    current_topology: str | None = None
    registered_topology_challengers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.same_layer_failed_generations < 0:
            raise ValueError("failed generation count cannot be negative")
        if len(set(self.causes)) != len(self.causes):
            raise ValueError("mechanic causes must be unique")
        if len(set(self.registered_topology_challengers)) != len(self.registered_topology_challengers):
            raise ValueError("topology challenger identifiers must be unique")


@dataclass(frozen=True)
class SelfEvolutionPlan:
    action: SelfEvolutionAction
    target_layers: tuple[EvolutionLayer, ...]
    primary_layer: EvolutionLayer | None
    reasons: tuple[str, ...]
    requires_outer_assurance: bool = False
    incumbent_topology_protected: bool = False

    def __post_init__(self) -> None:
        if len(set(self.target_layers)) != len(self.target_layers):
            raise ValueError("target layers must be unique")
        if self.action is SelfEvolutionAction.PROPOSE_MUTATION and not self.target_layers:
            raise ValueError("mutation plan requires at least one target layer")
        if self.action is not SelfEvolutionAction.PROPOSE_MUTATION and self.target_layers:
            raise ValueError("non-mutation plan cannot carry target layers")
        if self.primary_layer is not None and self.primary_layer not in self.target_layers:
            raise ValueError("primary layer must be one of the target layers")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


_CAUSE_LAYER: Mapping[MechanicCause, tuple[EvolutionLayer, ...]] = {
    MechanicCause.SPECIFICATION_GAP: (EvolutionLayer.WORKFLOW,),
    MechanicCause.EVIDENCE_GAP: (EvolutionLayer.WORKFLOW,),
    MechanicCause.MAP_COVERAGE_GAP: (EvolutionLayer.WORKFLOW,),
    MechanicCause.REPRESENTATION_GAP: (EvolutionLayer.REPRESENTATION,),
    MechanicCause.PORTAL_GAP: (EvolutionLayer.REPRESENTATION,),
    MechanicCause.DECOMPOSITION_GAP: (EvolutionLayer.TOPOLOGY,),
    MechanicCause.SCALE_GAP: (EvolutionLayer.TOPOLOGY,),
    MechanicCause.METRIC_FALSEHOOD: (EvolutionLayer.EVALUATOR,),
    MechanicCause.LOCAL_MINIMUM_OR_DYNAMICS_GAP: (EvolutionLayer.SEARCH_OPERATOR,),
    MechanicCause.METHOD_OPERATOR_GAP: (EvolutionLayer.SEARCH_OPERATOR,),
    MechanicCause.AUXILIARY_OBJECT_GAP: (EvolutionLayer.SEARCH_OPERATOR,),
    MechanicCause.EXPERIMENT_SELECTION_GAP: (EvolutionLayer.EVALUATOR,),
    MechanicCause.VERIFIER_GAP: (EvolutionLayer.EVALUATOR,),
    MechanicCause.COMPOSITION_INTERFACE_GAP: (EvolutionLayer.TOPOLOGY,),
    MechanicCause.MEMORY_VIEW_GAP: (EvolutionLayer.WORKFLOW,),
    MechanicCause.MODEL_TOOL_FLOOR: (EvolutionLayer.WORKFLOW,),
    MechanicCause.COMPUTE_ALLOCATION_GAP: (EvolutionLayer.META_POLICY,),
    MechanicCause.STOPPING_GAP: (EvolutionLayer.META_POLICY,),
    MechanicCause.ONTOLOGY_GAP: (EvolutionLayer.ONTOLOGY, EvolutionLayer.REPRESENTATION),
    MechanicCause.COMPILATION_BARRIER: (EvolutionLayer.WORKFLOW,),
    MechanicCause.IMPLEMENTATION_DEFECT: (EvolutionLayer.IMPLEMENTATION,),
    MechanicCause.NO_LOCAL_GEOMETRY_IN_SCOPE: (EvolutionLayer.REPRESENTATION, EvolutionLayer.TOPOLOGY),
}


def _dedupe(items: Iterable[EvolutionLayer]) -> tuple[EvolutionLayer, ...]:
    return tuple(dict.fromkeys(items))


def plan_self_evolution(portrait: EvolutionPortrait) -> SelfEvolutionPlan:
    """Route a diagnosed weakness to the smallest justified mutable layer set.

    Repeated failure at one layer broadens the search space rather than blindly
    retrying the same basis.  The escalation is itself explicit and testable:
    representation -> topology -> meta-policy -> mutation language.
    """

    if not portrait.causes or set(portrait.causes) == {MechanicCause.UNKNOWN}:
        return SelfEvolutionPlan(
            action=SelfEvolutionAction.RUN_DISCRIMINATOR,
            target_layers=(),
            primary_layer=None,
            reasons=("failure_cause_not_identified",),
        )

    if not portrait.stagnant and portrait.knowledge_gain_positive:
        return SelfEvolutionPlan(
            action=SelfEvolutionAction.KEEP_INCUMBENT,
            target_layers=(),
            primary_layer=None,
            reasons=("incumbent_route_still_producing_registered_gain",),
        )

    layers: list[EvolutionLayer] = []
    for cause in portrait.causes:
        if cause is MechanicCause.UNKNOWN:
            continue
        layers.extend(_CAUSE_LAYER.get(cause, (EvolutionLayer.WORKFLOW,)))
    targets = list(_dedupe(layers))
    reasons = ["diagnosed_mechanic_gap_routes_to_mutable_surface"]

    failed = portrait.same_layer_failed_generations
    if EvolutionLayer.SEARCH_OPERATOR in targets and failed >= 3:
        if EvolutionLayer.REPRESENTATION not in targets:
            targets.append(EvolutionLayer.REPRESENTATION)
        reasons.append("operator_plateau_opens_representation_search")
    if EvolutionLayer.REPRESENTATION in targets and failed >= 3:
        if EvolutionLayer.TOPOLOGY not in targets:
            targets.append(EvolutionLayer.TOPOLOGY)
        reasons.append("representation_plateau_opens_topology_search")
    if EvolutionLayer.TOPOLOGY in targets and failed >= 3:
        if EvolutionLayer.META_POLICY not in targets:
            targets.append(EvolutionLayer.META_POLICY)
        reasons.append("topology_plateau_opens_meta_policy_search")
    if EvolutionLayer.META_POLICY in targets and failed >= 4:
        if EvolutionLayer.MUTATION_LANGUAGE not in targets:
            targets.append(EvolutionLayer.MUTATION_LANGUAGE)
        reasons.append("meta_policy_plateau_opens_mutation_language_search")

    target_tuple = tuple(targets)
    requires_outer = any(
        layer in {
            EvolutionLayer.EVALUATOR,
            EvolutionLayer.META_POLICY,
            EvolutionLayer.MUTATION_LANGUAGE,
        }
        for layer in target_tuple
    )
    return SelfEvolutionPlan(
        action=SelfEvolutionAction.PROPOSE_MUTATION,
        target_layers=target_tuple,
        primary_layer=target_tuple[0] if target_tuple else None,
        reasons=tuple(reasons),
        requires_outer_assurance=requires_outer,
        incumbent_topology_protected=False,
    )


@dataclass(frozen=True)
class CandidateDelta:
    candidate_id: str
    quality: float
    cost: float
    latency: float
    robustness: float
    complexity: float

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError("candidate id cannot be empty")

    @property
    def vector(self) -> tuple[float, ...]:
        # Every coordinate is expressed as an improvement delta: larger is better.
        return (self.quality, self.cost, self.latency, self.robustness, self.complexity)


def _dominates(left: CandidateDelta, right: CandidateDelta) -> bool:
    return all(a >= b for a, b in zip(left.vector, right.vector)) and any(
        a > b for a, b in zip(left.vector, right.vector)
    )


def pareto_frontier(candidates: Iterable[CandidateDelta]) -> tuple[CandidateDelta, ...]:
    """Retain non-dominated challengers without inventing a universal scalar utility."""

    items = tuple(candidates)
    ids = [item.candidate_id for item in items]
    if len(set(ids)) != len(ids):
        raise ValueError("candidate ids must be unique")
    survivors = [
        item
        for item in items
        if not any(_dominates(other, item) for other in items if other is not item)
    ]
    return tuple(sorted(survivors, key=lambda item: item.candidate_id))


@dataclass(frozen=True)
class MutationPolicy:
    """Scoped priors over mutation operators; not probabilities or authority."""

    weights: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not self.weights:
            raise ValueError("mutation policy requires at least one operator")
        names = [name for name, _ in self.weights]
        if len(set(names)) != len(names):
            raise ValueError("mutation operator ids must be unique")
        if any(not name or weight <= 0 for name, weight in self.weights):
            raise ValueError("mutation operator weights must be positive")

    @classmethod
    def from_mapping(cls, weights: Mapping[str, float]) -> "MutationPolicy":
        return cls(tuple(sorted((str(name), float(weight)) for name, weight in weights.items())))

    def as_dict(self) -> dict[str, float]:
        return dict(self.weights)


def update_mutation_policy(
    policy: MutationPolicy,
    *,
    operator_id: str,
    outcome: EvolutionVerdict,
) -> MutationPolicy:
    """Credit assignment to the method that generated a method change.

    This is the first recursive step: the operator-selection policy changes in
    response to evidence about the mutations it generated.  It never deletes a
    failed operator; negative history remains available to the surrounding
    research ledger.
    """

    weights = policy.as_dict()
    if operator_id not in weights:
        raise ValueError("operator must already be registered before policy credit assignment")
    delta = {
        EvolutionVerdict.SCOPED_EVOLUTION_EVIDENCE: 0.25,
        EvolutionVerdict.TRANSFER_OBSERVED_NOT_ASSURANCE_VALIDATED: 0.10,
        EvolutionVerdict.LOCAL_IMPROVEMENT_ONLY: 0.05,
        EvolutionVerdict.META_OVERFIT: -0.25,
        EvolutionVerdict.NO_IMPROVEMENT: -0.10,
        EvolutionVerdict.BLOCKED: -0.05,
        EvolutionVerdict.CANNOT_CHECK: 0.0,
    }[outcome]
    weights[operator_id] = max(0.05, weights[operator_id] + delta)
    return MutationPolicy.from_mapping(weights)


@dataclass(frozen=True)
class MutationGovernance:
    proposal_allowed: bool
    eligible_for_auto_promotion: bool
    requires_outer_assurance: bool
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_mutation_governance(
    *,
    target_layer: EvolutionLayer,
    outer_assurance_frozen: bool,
) -> MutationGovernance:
    """Separate broad mutability from self-authorization.

    Everything may be challenged, including evaluators and the mutation
    language.  Constitutional changes remain proposals for external amendment
    review, while higher-order method changes require a frozen outer evaluator.
    """

    if target_layer is EvolutionLayer.CONSTITUTION:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("constitutional_change_requires_external_amendment_review",),
        )

    higher_order = target_layer in {
        EvolutionLayer.EVALUATOR,
        EvolutionLayer.META_POLICY,
        EvolutionLayer.MUTATION_LANGUAGE,
    }
    if higher_order and not outer_assurance_frozen:
        return MutationGovernance(
            proposal_allowed=True,
            eligible_for_auto_promotion=False,
            requires_outer_assurance=True,
            reasons=("higher_order_mutation_requires_frozen_outer_assurance",),
        )

    return MutationGovernance(
        proposal_allowed=True,
        eligible_for_auto_promotion=True,
        requires_outer_assurance=higher_order,
        reasons=("proposal_may_enter_existing_protected_method_promotion_gate",),
    )
