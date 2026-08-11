"""Backward obligation expansion and structured multi-seed bridge search (issue #141).

Status: ``FRAMEWORK_EXTENSION_HYPOTHESIS / RAKL_CORE_PRESERVED /
PROSPECTIVE_BENCHMARK_REQUIRED / NO_SCIENTIFIC_AUTHORITY``.

Research-only objects.  Wired into no gate and promoted nowhere.  The frozen
evaluator for these objects is :mod:`rakl.backward_multiseed_benchmark`, which
was committed first.

The logical boundary this module exists to hold
-----------------------------------------------

``L -> G`` does not make ``L`` necessary.  Backward expansion produces *sufficient
predecessor obligations*, i.e. candidate proof architectures.  That boundary is
enforced structurally rather than documented:

* :attr:`BackwardObligation.candidate_only` is a property with no backing field,
  so no constructor path can clear it;
* :attr:`BackwardObligation.establishes_necessity` is a property returning
  ``False``, and the type has no field, method or verdict able to express
  necessity -- ``sufficient_for`` is directional with no inverse accessor;
* an obligation that asserts itself as the *sole* predecessor is the necessity
  error under another name, so :class:`AlternativePredecessorSearch` offers no
  "no alternatives exist" value.  A bounded search that found none records its
  search boundary instead, exactly as RAKL records ``NO_SAFE_BRIDGE_FOUND``.

Reuse rather than duplication
-----------------------------

``VERIFIED_TRANSITION`` is decided by the existing
:func:`~rakl.problem_solving_algebra.operator_applicable` precondition check and
mirrors :class:`~rakl.problem_solving_algebra.TerminalCertificate`'s rule that
verified closure requires a named checker.  ``CANDIDATE_BRIDGE`` and
``ANALOGY_ONLY`` are mapped from the existing
:func:`~rakl.bridge_composition.evaluate_bridge_path` and
:func:`~rakl.similarity.validate_similarity_witness` verdicts rather than
re-derived.  Chronology uses the house ``Optional[bool]`` tri-state.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
from typing import Iterable, Optional, Tuple

from .bridge_composition import BridgePath, BridgePathVerdict, evaluate_bridge_path
from .problem_solving_algebra import (
    OperatorFamily,
    ProblemState,
    ResearchOperator,
    apply_operator_symbolic,
    operator_applicable,
)
from .similarity import (
    DistinguishingProbeCertificate,
    SimilarityWitness,
    WitnessVerdict,
    validate_similarity_witness,
)


class BackwardSeedFailureMode(str, Enum):
    """The ten named failure modes of issue #141, as typed states."""

    BACKWARD_SUFFICIENCY_AS_NECESSITY = "BACKWARD_SUFFICIENCY_AS_NECESSITY"
    GOLD_PATH_LEAK = "GOLD_PATH_LEAK"
    RANDOM_SEED_NOISE = "RANDOM_SEED_NOISE"
    WAYPOINT_INTERESTINGNESS_OVERREACH = "WAYPOINT_INTERESTINGNESS_OVERREACH"
    UNVERIFIED_CONNECTION_AS_ROAD = "UNVERIFIED_CONNECTION_AS_ROAD"
    LOCAL_WAYPOINT_AS_ROOT_PROGRESS = "LOCAL_WAYPOINT_AS_ROOT_PROGRESS"
    SEED_FAMILY_COLLAPSE = "SEED_FAMILY_COLLAPSE"
    FRONTIER_REPRESENTATION_MISMATCH = "FRONTIER_REPRESENTATION_MISMATCH"
    MEET_IN_MIDDLE_FALSE_GLUE = "MEET_IN_MIDDLE_FALSE_GLUE"
    CONNECTION_AUTHORITY_LEAK = "CONNECTION_AUTHORITY_LEAK"


# --------------------------------------------------------------------------
# Extension A -- backward obligation expansion
# --------------------------------------------------------------------------


class ImplicationStatus(str, Enum):
    """Whether ``obligation -> target`` has been separately verified.

    ``IMPLICATION_VERIFIED`` says the implication holds.  It never says the
    obligation is required: a verified sufficient predecessor is still one
    candidate proof architecture among unknown others.
    """

    CANDIDATE_UNVERIFIED = "CANDIDATE_UNVERIFIED"
    IMPLICATION_VERIFIED = "IMPLICATION_VERIFIED"
    IMPLICATION_REFUTED = "IMPLICATION_REFUTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class AlternativePredecessorSearch(str, Enum):
    """How hard the alternatives to this predecessor were looked for.

    There is deliberately no ``NO_ALTERNATIVES_EXIST`` member.  Asserting that a
    predecessor is the only one is a necessity claim, which backward expansion
    cannot make.  A bounded search that found nothing records its boundary.
    """

    ALTERNATIVES_RECORDED = "ALTERNATIVES_RECORDED"
    ALTERNATIVES_NOT_SEARCHED = "ALTERNATIVES_NOT_SEARCHED"
    BOUNDED_SEARCH_NONE_FOUND = "BOUNDED_SEARCH_NONE_FOUND"


def _hash(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BackwardObligation:
    """A sufficient predecessor obligation for a goal or another obligation.

    Never a necessity claim, and never evidence.
    """

    obligation_id: str
    root_goal_id: str
    statement: str
    structural_signature: Tuple[str, ...]
    sufficient_for: Tuple[str, ...]
    supporting_family: OperatorFamily
    supporting_theorem_ids: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    representation: str
    scope: str
    source_evidence_ids: Tuple[str, ...]
    implication_status: ImplicationStatus
    alternative_search: AlternativePredecessorSearch
    implication_checker: str = ""
    known_alternative_predecessor_families: Tuple[str, ...] = ()
    alternative_search_boundary: Tuple[str, ...] = ()
    expansion_depth: int = 1

    def __post_init__(self) -> None:
        if not self.obligation_id or not self.root_goal_id or not self.statement:
            raise ValueError("obligations require id, root goal and statement")
        if not self.sufficient_for:
            raise ValueError("an obligation must declare what it is sufficient for")
        if not self.structural_signature:
            raise ValueError("obligations require a structural signature")
        if not self.scope or not self.representation:
            raise ValueError("obligations require scope and representation")
        if self.expansion_depth < 1:
            raise ValueError("expansion depth must be positive")
        if (
            self.implication_status is ImplicationStatus.IMPLICATION_VERIFIED
            and not self.implication_checker
        ):
            raise ValueError(
                "a verified implication requires a checker identity, "
                "mirroring TerminalCertificate"
            )
        if (
            self.alternative_search is AlternativePredecessorSearch.ALTERNATIVES_RECORDED
            and not self.known_alternative_predecessor_families
        ):
            raise ValueError(
                "ALTERNATIVES_RECORDED requires at least one recorded alternative family"
            )
        if (
            self.alternative_search is AlternativePredecessorSearch.BOUNDED_SEARCH_NONE_FOUND
            and not self.alternative_search_boundary
        ):
            raise ValueError(
                "a bounded alternative search that found none must record its search "
                "boundary; finding none is not evidence that none exist"
            )

    @property
    def candidate_only(self) -> bool:
        """Always true.  There is no field backing this and no way to clear it."""

        return True

    @property
    def establishes_necessity(self) -> bool:
        """Always false.  ``L -> G`` never yields ``G -> L``."""

        return False

    @property
    def grants_root_progress(self) -> bool:
        return False

    @property
    def artifact_hash(self) -> str:
        return _hash(
            self.obligation_id,
            self.root_goal_id,
            self.statement,
            ",".join(self.structural_signature),
            ",".join(self.sufficient_for),
            self.supporting_family.value,
            self.representation,
            self.scope,
            self.implication_status.value,
            self.alternative_search.value,
        )


@dataclass(frozen=True)
class BackwardObligationProposal:
    """Untyped generator output entering the typed boundary.

    ``claims_necessity`` exists only so that a generator asserting necessity can
    be caught and rejected with its claim preserved as negative history.
    """

    proposal_id: str
    statement: str
    structural_signature: Tuple[str, ...]
    supporting_family: OperatorFamily
    representation: str
    scope: str
    implication_status: ImplicationStatus
    alternative_search: AlternativePredecessorSearch
    supporting_theorem_ids: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    source_evidence_ids: Tuple[str, ...] = ()
    implication_checker: str = ""
    known_alternative_predecessor_families: Tuple[str, ...] = ()
    alternative_search_boundary: Tuple[str, ...] = ()
    claims_necessity: bool = False


@dataclass(frozen=True)
class RejectedProposal:
    """Preserved negative history for a proposal that did not survive typing."""

    proposal_id: str
    reasons: Tuple[str, ...]
    failure_modes: Tuple[BackwardSeedFailureMode, ...] = ()


@dataclass(frozen=True)
class BackwardExpansion:
    """Result of ``EXPAND_BACKWARD(goal_or_obligation)``."""

    target_id: str
    root_goal_id: str
    generator_id: str
    obligations: Tuple[BackwardObligation, ...]
    rejected: Tuple[RejectedProposal, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_necessity_authority(self) -> bool:
        return False

    @property
    def sufficient_frontier_signature(self) -> Tuple[str, ...]:
        return tuple(
            sorted({coord for item in self.obligations for coord in item.structural_signature})
        )


def expand_backward(
    *,
    target_id: str,
    root_goal_id: str,
    proposals: Iterable[BackwardObligationProposal],
    generator_id: str,
    expansion_depth: int = 1,
) -> BackwardExpansion:
    """``EXPAND_BACKWARD``: type candidate sufficient predecessors for a target.

    This function is a typing boundary, not a generator.  It does not invent
    predecessors; it accepts proposals and refuses the ones that would smuggle a
    necessity claim or an unverifiable implication into the obligation type.
    Rejected proposals are retained.
    """

    if not target_id or not root_goal_id or not generator_id:
        raise ValueError("backward expansion requires target, root goal and generator ids")
    accepted: list[BackwardObligation] = []
    rejected: list[RejectedProposal] = []
    for proposal in proposals:
        reasons: list[str] = []
        modes: list[BackwardSeedFailureMode] = []
        if proposal.claims_necessity:
            reasons.append("proposal_asserts_predecessor_is_necessary")
            modes.append(BackwardSeedFailureMode.BACKWARD_SUFFICIENCY_AS_NECESSITY)
        if not proposal.statement or not proposal.structural_signature:
            reasons.append("proposal_missing_statement_or_structural_signature")
        if reasons:
            rejected.append(RejectedProposal(proposal.proposal_id, tuple(reasons), tuple(modes)))
            continue
        try:
            accepted.append(
                BackwardObligation(
                    obligation_id=proposal.proposal_id,
                    root_goal_id=root_goal_id,
                    statement=proposal.statement,
                    structural_signature=proposal.structural_signature,
                    sufficient_for=(target_id,),
                    supporting_family=proposal.supporting_family,
                    supporting_theorem_ids=proposal.supporting_theorem_ids,
                    assumptions=proposal.assumptions,
                    representation=proposal.representation,
                    scope=proposal.scope,
                    source_evidence_ids=proposal.source_evidence_ids,
                    implication_status=proposal.implication_status,
                    implication_checker=proposal.implication_checker,
                    alternative_search=proposal.alternative_search,
                    known_alternative_predecessor_families=(
                        proposal.known_alternative_predecessor_families
                    ),
                    alternative_search_boundary=proposal.alternative_search_boundary,
                    expansion_depth=expansion_depth,
                )
            )
        except ValueError as error:
            rejected.append(RejectedProposal(proposal.proposal_id, (str(error),)))
    return BackwardExpansion(
        target_id=target_id,
        root_goal_id=root_goal_id,
        generator_id=generator_id,
        obligations=tuple(accepted),
        rejected=tuple(rejected),
        reasons=(
            "generated_predecessors_are_sufficient_candidates_only",
            "no_generated_predecessor_is_claimed_necessary",
            "rejected_proposals_retained_as_negative_history",
        ),
    )


# --------------------------------------------------------------------------
# Extension B -- structured multi-seed intermediate exploration
# --------------------------------------------------------------------------


class SeedFamily(str, Enum):
    """The thirteen structured seed families of issue #141.

    A closed enum is what makes ``RANDOM_SEED_NOISE`` unconstructible: there is
    no free-text family, so an unconstrained generated sentence has nowhere to go.
    """

    CANDIDATE_LEMMA = "CANDIDATE_LEMMA"
    CANDIDATE_INVARIANT = "CANDIDATE_INVARIANT"
    ALTERNATIVE_REPRESENTATION = "ALTERNATIVE_REPRESENTATION"
    AUXILIARY_OBJECT = "AUXILIARY_OBJECT"
    INTERMEDIATE_BOUND = "INTERMEDIATE_BOUND"
    EXTREME_OR_BOUNDARY_CASE = "EXTREME_OR_BOUNDARY_CASE"
    NORMAL_FORM = "NORMAL_FORM"
    REDUCTION_TARGET = "REDUCTION_TARGET"
    KNOWN_THEOREM_INTERFACE = "KNOWN_THEOREM_INTERFACE"
    ANALOGY_OR_JUMP_DERIVED = "ANALOGY_OR_JUMP_DERIVED"
    COUNTEREXAMPLE_BOUNDARY = "COUNTEREXAMPLE_BOUNDARY"
    SYMMETRY_OR_DUALITY_COORDINATE = "SYMMETRY_OR_DUALITY_COORDINATE"
    LOCAL_TO_GLOBAL_BRIDGE_CANDIDATE = "LOCAL_TO_GLOBAL_BRIDGE_CANDIDATE"


class SeedOrigin(str, Enum):
    OPERATOR_APPLICATION = "OPERATOR_APPLICATION"
    RETRIEVAL = "RETRIEVAL"
    JUMP = "JUMP"
    FIBRE_EXPANSION = "FIBRE_EXPANSION"
    FAILURE_HISTORY = "FAILURE_HISTORY"


@dataclass(frozen=True)
class WaypointSeed:
    """An independently generated intermediate candidate.

    Not evidence, and not progress merely because it is novel or interesting.
    """

    seed_id: str
    root_goal_id: str
    atom_ids: Tuple[str, ...]
    family: SeedFamily
    statement_or_object: str
    representation: str
    structural_signature: Tuple[str, ...]
    origin: SeedOrigin
    origin_operator_id: str
    expected_useful_connection: str
    falsifier_or_cheapest_connection_test: str
    assumptions: Tuple[str, ...] = ()
    scope: str = ""

    def __post_init__(self) -> None:
        if not self.seed_id or not self.root_goal_id:
            raise ValueError("waypoint seeds require seed_id and root_goal_id")
        if not self.statement_or_object or not self.structural_signature:
            raise ValueError("waypoint seeds require a statement/object and structural signature")
        if not self.expected_useful_connection:
            raise ValueError(
                "a seed must declare the connection it is expected to expose; "
                "interestingness is not a reason to keep it"
            )
        if not self.falsifier_or_cheapest_connection_test:
            raise ValueError(
                "a seed must carry its cheapest connection test, otherwise it can "
                "never be shown irrelevant"
            )

    @property
    def candidate_only(self) -> bool:
        return True

    @property
    def is_evidence(self) -> bool:
        return False

    @property
    def grants_root_progress(self) -> bool:
        return False

    @property
    def artifact_hash(self) -> str:
        return _hash(
            self.seed_id,
            self.root_goal_id,
            self.family.value,
            self.statement_or_object,
            self.representation,
            ",".join(self.structural_signature),
            self.origin.value,
        )


@dataclass(frozen=True)
class SeedDiversityReport:
    families_present: Tuple[SeedFamily, ...]
    seeds_per_family: Tuple[Tuple[SeedFamily, int], ...]
    distinct_family_count: int
    total_seeds: int
    collapsed: bool
    reasons: Tuple[str, ...]

    @property
    def grants_progress_credit(self) -> bool:
        """Diversity is a search-control diagnostic, never progress."""

        return False


def assess_seed_diversity(
    seeds: Iterable[WaypointSeed], *, min_distinct_families: int = 3
) -> SeedDiversityReport:
    """Measure ``SEED_FAMILY_COLLAPSE`` over the closed family set."""

    if min_distinct_families < 1:
        raise ValueError("min_distinct_families must be positive")
    seed_tuple = tuple(seeds)
    counts: dict[SeedFamily, int] = {}
    for seed in seed_tuple:
        counts[seed.family] = counts.get(seed.family, 0) + 1
    present = tuple(sorted(counts, key=lambda family: family.value))
    collapsed = bool(seed_tuple) and len(present) < min_distinct_families
    reasons: list[str] = []
    if not seed_tuple:
        reasons.append("no_seeds_supplied")
    if collapsed:
        reasons.append(
            f"{BackwardSeedFailureMode.SEED_FAMILY_COLLAPSE.value}:"
            f"distinct_families:{len(present)}:required:{min_distinct_families}"
        )
    reasons.append("seed_count_is_not_a_success_metric")
    return SeedDiversityReport(
        families_present=present,
        seeds_per_family=tuple((family, counts[family]) for family in present),
        distinct_family_count=len(present),
        total_seeds=len(seed_tuple),
        collapsed=collapsed,
        reasons=tuple(reasons),
    )


# --------------------------------------------------------------------------
# Extension C -- connection / bridge testing
# --------------------------------------------------------------------------


class ConnectionVerdict(str, Enum):
    VERIFIED_TRANSITION = "VERIFIED_TRANSITION"
    CANDIDATE_BRIDGE = "CANDIDATE_BRIDGE"
    ANALOGY_ONLY = "ANALOGY_ONLY"
    REFUTED = "REFUTED"
    BLOCKED = "BLOCKED"
    CANNOT_CHECK = "CANNOT_CHECK"


class ConnectionNodeKind(str, Enum):
    FORWARD_FRONTIER_STATE = "FORWARD_FRONTIER_STATE"
    BACKWARD_OBLIGATION = "BACKWARD_OBLIGATION"
    WAYPOINT_SEED = "WAYPOINT_SEED"
    ROOT_GOAL = "ROOT_GOAL"


@dataclass(frozen=True)
class ConnectionNode:
    node_id: str
    kind: ConnectionNodeKind
    representation: str
    structural_signature: Tuple[str, ...]
    required_facts: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("connection nodes require a node_id")


@dataclass(frozen=True)
class TransitionEvidence:
    """Operator-level evidence that source actually transforms into target."""

    operator: ResearchOperator
    source_state: ProblemState
    checker_id: str = ""
    verification_artifact_id: str = ""


@dataclass(frozen=True)
class ConnectionTrial:
    trial_id: str
    source: ConnectionNode
    target: ConnectionNode
    declared_before_outcomes: Optional[bool]
    blocked_dependency: str = ""
    transition: Optional[TransitionEvidence] = None
    bridge_path: Optional[BridgePath] = None
    witness: Optional[SimilarityWitness] = None
    refutation: Optional[DistinguishingProbeCertificate] = None


@dataclass(frozen=True)
class ConnectionReport:
    verdict: ConnectionVerdict
    trial_id: str
    source_id: str
    target_id: str
    reasons: Tuple[str, ...]
    failure_modes: Tuple[BackwardSeedFailureMode, ...] = ()

    @property
    def grants_route_authority(self) -> bool:
        """Only a VERIFIED_TRANSITION is a road, and even then not an authority."""

        return False

    @property
    def is_road(self) -> bool:
        return self.verdict is ConnectionVerdict.VERIFIED_TRANSITION

    @property
    def is_negative_history(self) -> bool:
        return self.verdict in {ConnectionVerdict.REFUTED, ConnectionVerdict.BLOCKED}


def _report(
    verdict: ConnectionVerdict,
    trial: ConnectionTrial,
    reasons: Tuple[str, ...],
    modes: Tuple[BackwardSeedFailureMode, ...] = (),
) -> ConnectionReport:
    return ConnectionReport(
        verdict=verdict,
        trial_id=trial.trial_id,
        source_id=trial.source.node_id,
        target_id=trial.target.node_id,
        reasons=reasons,
        failure_modes=modes,
    )


def evaluate_connection(trial: ConnectionTrial) -> ConnectionReport:
    """``TEST_CONNECTION(X, Y)``.

    Distinguishes a verified transition from a candidate bridge, a bare analogy,
    a refutation, an external block and an unresolvable check.  A trial with no
    operator, bridge path or witness is ``CANNOT_CHECK``: silence is never a road.
    """

    if not trial.trial_id or not trial.source.node_id or not trial.target.node_id:
        return _report(
            ConnectionVerdict.CANNOT_CHECK, trial, ("trial_or_node_identity_missing",)
        )
    if trial.blocked_dependency:
        return _report(
            ConnectionVerdict.BLOCKED,
            trial,
            (f"named_unavailable_dependency:{trial.blocked_dependency}",),
        )
    if trial.declared_before_outcomes is None:
        return _report(
            ConnectionVerdict.CANNOT_CHECK, trial, ("connection_freeze_chronology_unknown",)
        )
    if trial.declared_before_outcomes is False:
        return _report(
            ConnectionVerdict.CANNOT_CHECK,
            trial,
            ("posthoc_connection_selection_is_not_an_admissible_check",),
        )
    if trial.refutation is not None:
        return _report(
            ConnectionVerdict.REFUTED,
            trial,
            (
                f"distinguishing_probe:{trial.refutation.probe_id}",
                f"discrepancy:{trial.refutation.discrepancy}",
                "refutation_retained_as_negative_history",
            ),
        )

    if trial.transition is not None:
        evidence = trial.transition
        if not operator_applicable(evidence.operator, evidence.source_state):
            return _report(
                ConnectionVerdict.REFUTED,
                trial,
                (
                    f"operator_preconditions_unmet:{evidence.operator.operator_id}",
                    "source_state_cannot_reach_target_by_this_operator",
                ),
            )
        reached = apply_operator_symbolic(evidence.operator, evidence.source_state)
        if not trial.target.required_facts.issubset(reached.facts):
            missing = tuple(sorted(trial.target.required_facts - reached.facts))
            return _report(
                ConnectionVerdict.REFUTED,
                trial,
                ("target_facts_not_reached:" + ",".join(missing),),
            )
        if not evidence.checker_id or not evidence.verification_artifact_id:
            return _report(
                ConnectionVerdict.CANDIDATE_BRIDGE,
                trial,
                (
                    "operator_transition_is_symbolically_applicable",
                    "no_checker_identity_or_verification_artifact",
                    "unverified_transition_is_not_a_road",
                ),
                (BackwardSeedFailureMode.UNVERIFIED_CONNECTION_AS_ROAD,),
            )
        return _report(
            ConnectionVerdict.VERIFIED_TRANSITION,
            trial,
            (
                f"operator:{evidence.operator.operator_id}",
                f"checker:{evidence.checker_id}",
                f"verification_artifact:{evidence.verification_artifact_id}",
                "transition_verified_but_grants_no_theorem_authority",
            ),
        )

    if trial.bridge_path is not None:
        path_report = evaluate_bridge_path(trial.bridge_path)
        mapped = {
            BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY: ConnectionVerdict.CANDIDATE_BRIDGE,
            BridgePathVerdict.NAVIGABLE_ONLY: ConnectionVerdict.ANALOGY_ONLY,
            BridgePathVerdict.REJECT: ConnectionVerdict.REFUTED,
            BridgePathVerdict.TRIAL_INVALID: ConnectionVerdict.CANNOT_CHECK,
            BridgePathVerdict.CANNOT_CHECK: ConnectionVerdict.CANNOT_CHECK,
        }
        return _report(
            mapped[path_report.verdict],
            trial,
            (f"bridge_path_verdict:{path_report.verdict.value}",) + path_report.reasons,
        )

    if trial.witness is not None:
        witness_report = validate_similarity_witness(trial.witness)
        if witness_report.verdict is WitnessVerdict.REJECT:
            return _report(
                ConnectionVerdict.REFUTED,
                trial,
                ("similarity_witness_rejected",) + witness_report.reasons,
            )
        if witness_report.verdict is WitnessVerdict.CANNOT_CHECK:
            return _report(
                ConnectionVerdict.CANNOT_CHECK,
                trial,
                ("similarity_witness_incomplete",) + witness_report.reasons,
            )
        return _report(
            ConnectionVerdict.ANALOGY_ONLY,
            trial,
            (
                f"similarity_relation:{trial.witness.relation.value}",
                "structural_resemblance_is_not_a_transition",
            ),
        )

    return _report(
        ConnectionVerdict.CANNOT_CHECK,
        trial,
        ("no_operator_bridge_path_or_witness_supplied",),
    )


@dataclass(frozen=True)
class ConnectionHistory:
    """Immutable ledger of connection attempts, successes and failures alike."""

    entries: Tuple[ConnectionReport, ...] = ()

    def record(self, report: ConnectionReport) -> "ConnectionHistory":
        return replace(self, entries=self.entries + (report,))

    def attempts_for(self, source_id: str, target_id: str) -> Tuple[ConnectionReport, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.source_id == source_id and entry.target_id == target_id
        )

    def is_known_failure(self, source_id: str, target_id: str) -> bool:
        return any(
            entry.verdict is ConnectionVerdict.REFUTED
            for entry in self.attempts_for(source_id, target_id)
        )

    def repeated_known_failure_count(self) -> int:
        """Attempts made against a pair already refuted earlier in the ledger."""

        refuted: set[Tuple[str, str]] = set()
        repeats = 0
        for entry in self.entries:
            pair = (entry.source_id, entry.target_id)
            if pair in refuted:
                repeats += 1
            if entry.verdict is ConnectionVerdict.REFUTED:
                refuted.add(pair)
        return repeats

    @property
    def failed_bridge_ids(self) -> Tuple[str, ...]:
        return tuple(
            entry.trial_id
            for entry in self.entries
            if entry.verdict is ConnectionVerdict.REFUTED
        )

    @property
    def verified_roads(self) -> Tuple[ConnectionReport, ...]:
        return tuple(entry for entry in self.entries if entry.is_road)


# --------------------------------------------------------------------------
# Extension D -- meet-in-the-middle atom discovery
# --------------------------------------------------------------------------


class MeetInMiddleVerdict(str, Enum):
    VERIFIED_GLUE = "VERIFIED_GLUE"
    CANDIDATE_GLUE_UNVERIFIED = "CANDIDATE_GLUE_UNVERIFIED"
    DISCONNECTED = "DISCONNECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MeetInMiddleReport:
    verdict: MeetInMiddleVerdict
    chain_trial_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]
    failure_modes: Tuple[BackwardSeedFailureMode, ...] = ()

    @property
    def grants_solution_authority(self) -> bool:
        return False


def assess_meet_in_middle(
    chain: Iterable[ConnectionReport],
    *,
    forward_frontier_ids: Tuple[str, ...],
    backward_obligation_ids: Tuple[str, ...],
) -> MeetInMiddleReport:
    """Refuse to call a forward/backward meeting glued without a verified chain.

    This is the ``MEET_IN_MIDDLE_FALSE_GLUE`` guard: a chain containing even one
    ``CANDIDATE_BRIDGE`` or ``ANALOGY_ONLY`` hop is a candidate, not a join.
    """

    links = tuple(chain)
    trial_ids = tuple(link.trial_id for link in links)
    if not links:
        return MeetInMiddleReport(
            MeetInMiddleVerdict.DISCONNECTED, (), ("no_connection_reports_supplied",)
        )
    if not forward_frontier_ids or not backward_obligation_ids:
        return MeetInMiddleReport(
            MeetInMiddleVerdict.CANNOT_CHECK, trial_ids, ("frontier_identities_missing",)
        )
    for index in range(len(links) - 1):
        if links[index].target_id != links[index + 1].source_id:
            return MeetInMiddleReport(
                MeetInMiddleVerdict.DISCONNECTED,
                trial_ids,
                (f"chain_break_between_links:{index}:{index + 1}",),
            )
    if links[0].source_id not in forward_frontier_ids:
        return MeetInMiddleReport(
            MeetInMiddleVerdict.DISCONNECTED,
            trial_ids,
            ("chain_does_not_start_at_a_forward_frontier_state",),
        )
    if links[-1].target_id not in backward_obligation_ids:
        return MeetInMiddleReport(
            MeetInMiddleVerdict.DISCONNECTED,
            trial_ids,
            ("chain_does_not_end_at_a_backward_obligation",),
        )
    if any(link.verdict is ConnectionVerdict.REFUTED for link in links):
        return MeetInMiddleReport(
            MeetInMiddleVerdict.DISCONNECTED, trial_ids, ("chain_contains_a_refuted_link",)
        )
    weak = tuple(
        f"{link.trial_id}:{link.verdict.value}" for link in links if not link.is_road
    )
    if weak:
        return MeetInMiddleReport(
            MeetInMiddleVerdict.CANDIDATE_GLUE_UNVERIFIED,
            trial_ids,
            ("unverified_links_present:" + ",".join(weak), "candidate_glue_is_not_a_join"),
            (BackwardSeedFailureMode.MEET_IN_MIDDLE_FALSE_GLUE,),
        )
    return MeetInMiddleReport(
        MeetInMiddleVerdict.VERIFIED_GLUE,
        trial_ids,
        (
            "every_link_is_a_verified_transition_with_a_checker",
            "verified_glue_still_requires_separate_solution_promotion",
        ),
    )


@dataclass(frozen=True)
class BridgeResidual:
    """The unresolved forward/backward cut, opened as the next atom."""

    residual_id: str
    root_goal_id: str
    forward_frontier_signature: Tuple[str, ...]
    backward_sufficient_frontier_signature: Tuple[str, ...]
    missing_coordinates: Tuple[str, ...]
    incompatible_coordinates: Tuple[str, ...]
    known_failed_bridge_ids: Tuple[str, ...]
    candidate_waypoint_seed_ids: Tuple[str, ...]
    cheapest_discriminating_action: str

    def __post_init__(self) -> None:
        if not self.residual_id or not self.root_goal_id:
            raise ValueError("bridge residuals require residual_id and root_goal_id")
        if not self.cheapest_discriminating_action:
            raise ValueError(
                "a residual must name the cheapest discriminating next action, "
                "otherwise it reopens the broad root question instead of the cut"
            )

    @property
    def opens_atom_only(self) -> bool:
        return True

    @property
    def grants_root_progress(self) -> bool:
        return False

    @property
    def frontier_overlap(self) -> float:
        forward = set(self.forward_frontier_signature)
        backward = set(self.backward_sufficient_frontier_signature)
        union = forward | backward
        return len(forward & backward) / len(union) if union else 0.0

    @property
    def artifact_hash(self) -> str:
        return _hash(
            self.residual_id,
            self.root_goal_id,
            ",".join(self.forward_frontier_signature),
            ",".join(self.backward_sufficient_frontier_signature),
            ",".join(self.missing_coordinates),
            ",".join(self.incompatible_coordinates),
            self.cheapest_discriminating_action,
        )


def compute_bridge_residual(
    *,
    residual_id: str,
    root_goal_id: str,
    forward_frontier_signature: Tuple[str, ...],
    expansion: BackwardExpansion,
    history: ConnectionHistory,
    seeds: Iterable[WaypointSeed] = (),
    incompatible_coordinates: Tuple[str, ...] = (),
    cheapest_discriminating_action: str,
) -> BridgeResidual:
    """Define the unresolved cut between the two frontiers as the next atom."""

    backward_signature = expansion.sufficient_frontier_signature
    missing = tuple(sorted(set(backward_signature) - set(forward_frontier_signature)))
    return BridgeResidual(
        residual_id=residual_id,
        root_goal_id=root_goal_id,
        forward_frontier_signature=tuple(sorted(set(forward_frontier_signature))),
        backward_sufficient_frontier_signature=backward_signature,
        missing_coordinates=missing,
        incompatible_coordinates=tuple(sorted(set(incompatible_coordinates))),
        known_failed_bridge_ids=history.failed_bridge_ids,
        candidate_waypoint_seed_ids=tuple(seed.seed_id for seed in seeds),
        cheapest_discriminating_action=cheapest_discriminating_action,
    )


# --------------------------------------------------------------------------
# Failure-mode audit
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BackwardSeedAuditReport:
    triggered: Tuple[BackwardSeedFailureMode, ...]
    reasons: Tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.triggered

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def audit_backward_seed_state(
    *,
    diversity: SeedDiversityReport,
    history: ConnectionHistory,
    residual: Optional[BridgeResidual] = None,
    meet_in_middle: Optional[MeetInMiddleReport] = None,
    necessity_claims: Tuple[str, ...] = (),
    connections_cited_as_roads: Tuple[str, ...] = (),
    root_progress_claimed_from_seed_ids: Tuple[str, ...] = (),
    root_obligations_verified_closed: int = 0,
    gold_path_exposed: Optional[bool] = None,
) -> BackwardSeedAuditReport:
    """Report which of the ten named failure modes the current state exhibits."""

    triggered: list[BackwardSeedFailureMode] = []
    reasons: list[str] = []

    if necessity_claims:
        triggered.append(BackwardSeedFailureMode.BACKWARD_SUFFICIENCY_AS_NECESSITY)
        reasons.append("necessity_claimed_for:" + ",".join(necessity_claims))
    if gold_path_exposed is True:
        triggered.append(BackwardSeedFailureMode.GOLD_PATH_LEAK)
        reasons.append("gold_path_exposed_to_solver")
    if gold_path_exposed is None:
        reasons.append("gold_path_exposure_unknown_cannot_check")
    if diversity.collapsed:
        triggered.append(BackwardSeedFailureMode.SEED_FAMILY_COLLAPSE)
        reasons.append(f"distinct_seed_families:{diversity.distinct_family_count}")

    roads = {report.trial_id for report in history.verified_roads}
    leaked = tuple(sorted(set(connections_cited_as_roads) - roads))
    if leaked:
        triggered.append(BackwardSeedFailureMode.UNVERIFIED_CONNECTION_AS_ROAD)
        reasons.append("unverified_connections_cited_as_roads:" + ",".join(leaked))

    if root_progress_claimed_from_seed_ids and root_obligations_verified_closed <= 0:
        triggered.append(BackwardSeedFailureMode.LOCAL_WAYPOINT_AS_ROOT_PROGRESS)
        reasons.append(
            "root_progress_claimed_from_seeds_without_verified_root_obligation_closure"
        )

    if meet_in_middle is not None and meet_in_middle.verdict is (
        MeetInMiddleVerdict.CANDIDATE_GLUE_UNVERIFIED
    ):
        triggered.append(BackwardSeedFailureMode.MEET_IN_MIDDLE_FALSE_GLUE)
        reasons.append("candidate_glue_present_but_not_verified")

    if residual is not None and residual.frontier_overlap == 0.0:
        triggered.append(BackwardSeedFailureMode.FRONTIER_REPRESENTATION_MISMATCH)
        reasons.append("forward_and_backward_frontiers_share_no_coordinate")

    if history.repeated_known_failure_count() > 0:
        reasons.append(
            f"repeated_known_failure_attempts:{history.repeated_known_failure_count()}"
        )

    reasons.append("audit_is_search_control_diagnostic_only")
    return BackwardSeedAuditReport(tuple(dict.fromkeys(triggered)), tuple(reasons))
