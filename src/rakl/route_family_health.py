"""Longitudinal route-family health diagnostics (issue #135).

Status: ``FRAMEWORK_RESEARCH_HYPOTHESIS / LONGITUDINAL_SEARCH_CONTROL /
PROSPECTIVE_BENCHMARK_REQUIRED / NO_AUTOMATIC_ABANDONMENT / NO_SCIENTIFIC_AUTHORITY``.

Research-only.  Wired into no gate, promoted nowhere, and it activates no
intervention.  The module is structurally incapable of emitting a truth or
rationality verdict: :class:`RouteHealthState` contains exactly eight cautious
search-control labels and no ``FALSE_PROGRAMME`` equivalent, and a frozen test
asserts that member set exactly so a later addition breaks CI.

Three properties carry the design
---------------------------------

**Non-compensation is structural.**  :class:`ProgrammeHealthVector` exposes no
``score``, ``total`` or arithmetic aggregation, and raises ``TypeError`` on
``iter()`` and ``float()``.  Its coordinates do not even point the same way --
``root_bridge_stability`` high means *stuck*, ``new_verified_local_results`` high
means *productive* -- so a weighted sum would be meaningless as well as wrong.
Coordinates declared non-compensatory at construction are evaluated as hard
predicates before anything else: ``PROGRESSIVE_SIGNAL`` is unreachable when any
of them shows no movement, no matter how many local lemmas accumulated.

**Root progress is bound to a preservation interface.**  Surrogate improvement is
classified as local progress unless a #124-style
:class:`RootCoordinatePreservationInterface` establishes preservation for the
relevant scope.  This is what stops route health from becoming another
false-progress score.

**Failures are not counted as degeneration.**  A route whose failures eliminate
search space, identify a stable obstruction, or force a productive
representation reset cannot be classified ``STAGNANT_SIGNAL``.  A route blocked
on a named unavailable dependency is ``EXTERNALLY_BLOCKED``, which pre-empts
stagnation entirely.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional, Protocol, Tuple


class RouteHealthState(str, Enum):
    """Cautious search-control labels.

    Deliberately absent: ``FALSE_PROGRAMME``, ``DEGENERATING``, ``PSEUDOSCIENCE``
    or any other truth/rationality verdict.  Telemetry cannot produce one.
    """

    PROGRESSIVE_SIGNAL = "PROGRESSIVE_SIGNAL"
    LOCALLY_PROGRESSIVE_ROOT_STALLED = "LOCALLY_PROGRESSIVE_ROOT_STALLED"
    STAGNANT_SIGNAL = "STAGNANT_SIGNAL"
    PATCH_ACCUMULATION_SIGNAL = "PATCH_ACCUMULATION_SIGNAL"
    RESTRUCTURING_SIGNAL = "RESTRUCTURING_SIGNAL"
    EXTERNALLY_BLOCKED = "EXTERNALLY_BLOCKED"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    CANNOT_CHECK = "CANNOT_CHECK"


class RouteHealthFailureMode(str, Enum):
    """The ten named failure modes of issue #135, as typed states."""

    FAILURE_COUNT_AS_DEGENERATION = "FAILURE_COUNT_AS_DEGENERATION"
    LOCAL_PROGRESS_AS_ROOT_PROGRESS = "LOCAL_PROGRESS_AS_ROOT_PROGRESS"
    COMPLEXITY_AS_BADNESS = "COMPLEXITY_AS_BADNESS"
    PREMATURE_PROGRAMME_ABANDONMENT = "PREMATURE_PROGRAMME_ABANDONMENT"
    SUCCESS_HINDSIGHT_LEAK = "SUCCESS_HINDSIGHT_LEAK"
    RETROSPECTIVE_PREDICTION_REWRITE = "RETROSPECTIVE_PREDICTION_REWRITE"
    ROUTE_FAMILY_MISCLUSTERING = "ROUTE_FAMILY_MISCLUSTERING"
    EXTERNAL_BLOCKER_MISCLASSIFICATION = "EXTERNAL_BLOCKER_MISCLASSIFICATION"
    PHILOSOPHICAL_LABEL_AUTHORITY_LEAK = "PHILOSOPHICAL_LABEL_AUTHORITY_LEAK"
    SHORT_HORIZON_BIAS = "SHORT_HORIZON_BIAS"


# --------------------------------------------------------------------------
# Root-coordinate preservation interface (composes with issue #124)
# --------------------------------------------------------------------------


class RootPreservationStatus(str, Enum):
    PRESERVATION_INTERFACE_ESTABLISHED = "PRESERVATION_INTERFACE_ESTABLISHED"
    PRESERVATION_INTERFACE_ABSENT = "PRESERVATION_INTERFACE_ABSENT"
    PRESERVATION_INTERFACE_REFUTED = "PRESERVATION_INTERFACE_REFUTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class RootCoordinatePreservationInterface(Protocol):
    """Narrow adapter boundary for issue #124's ``RootCoordinatePreservationReceipt``.

    #124 is not on ``main`` at the time of writing, so this module depends on the
    behaviour rather than the concrete type.  When #124 lands, an adapter
    implementing this single method is the whole integration.
    """

    def preservation_status(
        self, *, surrogate_id: str, root_goal_id: str, scope: str
    ) -> RootPreservationStatus:
        ...


class ProgressKind(str, Enum):
    ROOT_PROGRESS = "ROOT_PROGRESS"
    LOCAL_PROGRESS = "LOCAL_PROGRESS"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SurrogateImprovement:
    """A measured improvement on a surrogate the route optimises."""

    improvement_id: str
    surrogate_id: str
    root_goal_id: str
    scope: str

    def __post_init__(self) -> None:
        if not self.improvement_id or not self.surrogate_id or not self.scope:
            raise ValueError("surrogate improvements require id, surrogate and scope")


@dataclass(frozen=True)
class ProgressClassification:
    improvement_id: str
    kind: ProgressKind
    preservation_status: RootPreservationStatus
    reasons: Tuple[str, ...]


def classify_surrogate_improvement(
    improvement: SurrogateImprovement,
    interface: Optional[RootCoordinatePreservationInterface],
) -> ProgressClassification:
    """Surrogate gain counts as root progress only behind an established interface."""

    if interface is None:
        return ProgressClassification(
            improvement.improvement_id,
            ProgressKind.LOCAL_PROGRESS,
            RootPreservationStatus.PRESERVATION_INTERFACE_ABSENT,
            (
                "no_root_coordinate_preservation_interface_supplied",
                "surrogate_improvement_classified_as_local_progress",
            ),
        )
    status = interface.preservation_status(
        surrogate_id=improvement.surrogate_id,
        root_goal_id=improvement.root_goal_id,
        scope=improvement.scope,
    )
    if status is RootPreservationStatus.PRESERVATION_INTERFACE_ESTABLISHED:
        return ProgressClassification(
            improvement.improvement_id,
            ProgressKind.ROOT_PROGRESS,
            status,
            ("surrogate_to_root_preservation_established_for_scope",),
        )
    if status is RootPreservationStatus.CANNOT_CHECK:
        return ProgressClassification(
            improvement.improvement_id,
            ProgressKind.CANNOT_CHECK,
            status,
            ("preservation_status_unresolved",),
        )
    return ProgressClassification(
        improvement.improvement_id,
        ProgressKind.LOCAL_PROGRESS,
        status,
        (
            f"preservation_status:{status.value}",
            "surrogate_improvement_is_not_root_progress",
        ),
    )


# --------------------------------------------------------------------------
# Route-family continuity (itself a research problem)
# --------------------------------------------------------------------------


class ContinuityCoordinate(str, Enum):
    CORE_REPRESENTATION_OR_MECHANISM = "CORE_REPRESENTATION_OR_MECHANISM"
    ROOT_BRIDGE_HYPOTHESIS = "ROOT_BRIDGE_HYPOTHESIS"
    MECHANISM_FAMILY = "MECHANISM_FAMILY"
    SURROGATE_ROOT_COORDINATE_RELATION = "SURROGATE_ROOT_COORDINATE_RELATION"
    OPERATOR_MOTIF = "OPERATOR_MOTIF"
    FAILURE_INTERFACE = "FAILURE_INTERFACE"
    BACKWARD_OBLIGATION_LANDMARK = "BACKWARD_OBLIGATION_LANDMARK"
    ROOT_GOAL_ID = "ROOT_GOAL_ID"


class ContinuityVerdict(str, Enum):
    SAME_ROUTE_FAMILY = "SAME_ROUTE_FAMILY"
    DIFFERENT_ROUTE_FAMILY = "DIFFERENT_ROUTE_FAMILY"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class RouteEpisodeDescriptor:
    """The continuity coordinates of one attempt.

    Empty string means *unknown*, which yields ``CANNOT_CHECK`` rather than a
    silent match on a blank.
    """

    episode_id: str
    root_goal_id: str
    core_representation_or_mechanism: str = ""
    root_bridge_hypothesis: str = ""
    mechanism_family: str = ""
    surrogate_root_coordinate_relation: str = ""
    operator_motif: str = ""
    failure_interface: str = ""
    backward_obligation_landmark: str = ""

    def coordinate(self, coordinate: ContinuityCoordinate) -> str:
        return {
            ContinuityCoordinate.CORE_REPRESENTATION_OR_MECHANISM: (
                self.core_representation_or_mechanism
            ),
            ContinuityCoordinate.ROOT_BRIDGE_HYPOTHESIS: self.root_bridge_hypothesis,
            ContinuityCoordinate.MECHANISM_FAMILY: self.mechanism_family,
            ContinuityCoordinate.SURROGATE_ROOT_COORDINATE_RELATION: (
                self.surrogate_root_coordinate_relation
            ),
            ContinuityCoordinate.OPERATOR_MOTIF: self.operator_motif,
            ContinuityCoordinate.FAILURE_INTERFACE: self.failure_interface,
            ContinuityCoordinate.BACKWARD_OBLIGATION_LANDMARK: (
                self.backward_obligation_landmark
            ),
            ContinuityCoordinate.ROOT_GOAL_ID: self.root_goal_id,
        }[coordinate]


@dataclass(frozen=True)
class ContinuityPolicy:
    """Swappable definition of what makes two episodes one route family.

    Sharing a Millennium problem is not continuity, so a policy requiring only
    ``ROOT_GOAL_ID`` is rejected at construction: that is the
    ``ROUTE_FAMILY_MISCLUSTERING`` failure mode written as a policy.
    """

    policy_id: str
    required_coordinates: Tuple[ContinuityCoordinate, ...]

    def __post_init__(self) -> None:
        if not self.policy_id:
            raise ValueError("continuity policies require a policy_id")
        if not self.required_coordinates:
            raise ValueError("a continuity policy must require at least one coordinate")
        if len(set(self.required_coordinates)) != len(self.required_coordinates):
            raise ValueError("required coordinates must be unique")
        if set(self.required_coordinates) == {ContinuityCoordinate.ROOT_GOAL_ID}:
            raise ValueError(
                "root_goal_id alone is never route-family continuity: two episodes "
                "are not one lineage merely because they share a root problem"
            )


DEFAULT_CONTINUITY_POLICY = ContinuityPolicy(
    policy_id="default_core_and_root_bridge",
    required_coordinates=(
        ContinuityCoordinate.CORE_REPRESENTATION_OR_MECHANISM,
        ContinuityCoordinate.ROOT_BRIDGE_HYPOTHESIS,
    ),
)


@dataclass(frozen=True)
class ContinuityReport:
    verdict: ContinuityVerdict
    policy_id: str
    matched: Tuple[ContinuityCoordinate, ...]
    mismatched: Tuple[ContinuityCoordinate, ...]
    unknown: Tuple[ContinuityCoordinate, ...]
    reasons: Tuple[str, ...]


def same_route_family(
    left: RouteEpisodeDescriptor,
    right: RouteEpisodeDescriptor,
    policy: ContinuityPolicy = DEFAULT_CONTINUITY_POLICY,
) -> ContinuityReport:
    """Decide continuity under an explicit, swappable policy."""

    matched: list[ContinuityCoordinate] = []
    mismatched: list[ContinuityCoordinate] = []
    unknown: list[ContinuityCoordinate] = []
    for coordinate in policy.required_coordinates:
        left_value = left.coordinate(coordinate)
        right_value = right.coordinate(coordinate)
        if not left_value or not right_value:
            unknown.append(coordinate)
        elif left_value == right_value:
            matched.append(coordinate)
        else:
            mismatched.append(coordinate)
    if unknown:
        return ContinuityReport(
            ContinuityVerdict.CANNOT_CHECK,
            policy.policy_id,
            tuple(matched),
            tuple(mismatched),
            tuple(unknown),
            ("required_continuity_coordinate_unknown_on_one_or_both_episodes",),
        )
    if mismatched:
        return ContinuityReport(
            ContinuityVerdict.DIFFERENT_ROUTE_FAMILY,
            policy.policy_id,
            tuple(matched),
            tuple(mismatched),
            (),
            ("required_continuity_coordinates_differ",),
        )
    return ContinuityReport(
        ContinuityVerdict.SAME_ROUTE_FAMILY,
        policy.policy_id,
        tuple(matched),
        (),
        (),
        ("all_required_continuity_coordinates_agree",),
    )


# --------------------------------------------------------------------------
# Prospective vs post-hoc chronology
# --------------------------------------------------------------------------


class ChronologyKind(str, Enum):
    PROSPECTIVE_DISCRIMINATOR = "PROSPECTIVE_DISCRIMINATOR"
    POSTHOC_REPAIR = "POSTHOC_REPAIR"


@dataclass(frozen=True)
class ChronologyRecord:
    """One prediction or repair, with the chronology that makes it measurable.

    ``declared_before_outcome`` is the house tri-state: ``None`` means the
    chronology is unknown and the whole assessment falls to ``CANNOT_CHECK``
    rather than silently crediting the route.
    """

    record_id: str
    episode_id: str
    kind: ChronologyKind
    declared_before_outcome: Optional[bool]
    survived: Optional[bool] = None

    def __post_init__(self) -> None:
        if not self.record_id or not self.episode_id:
            raise ValueError("chronology records require record_id and episode_id")


@dataclass(frozen=True)
class ChronologyTally:
    prospective_successes: int
    prospective_attempts: int
    posthoc_repairs: int
    rewritten_predictions: Tuple[str, ...]
    unknown_chronology: Tuple[str, ...]


def tally_chronology(records: Iterable[ChronologyRecord]) -> ChronologyTally:
    """Count only predictions that were declared before the outcome they survived."""

    successes = 0
    attempts = 0
    repairs = 0
    rewritten: list[str] = []
    unknown: list[str] = []
    for record in records:
        if record.declared_before_outcome is None:
            unknown.append(record.record_id)
            continue
        if record.kind is ChronologyKind.POSTHOC_REPAIR:
            repairs += 1
            continue
        if record.declared_before_outcome is False:
            # Claimed prospective, actually written after the outcome.
            rewritten.append(record.record_id)
            continue
        attempts += 1
        if record.survived is True:
            successes += 1
    return ChronologyTally(
        prospective_successes=successes,
        prospective_attempts=attempts,
        posthoc_repairs=repairs,
        rewritten_predictions=tuple(rewritten),
        unknown_chronology=tuple(unknown),
    )


# --------------------------------------------------------------------------
# Programme-health vector -- a vector, structurally
# --------------------------------------------------------------------------


class CoordinateDirection(str, Enum):
    """Which way a coordinate has to move to count as movement.

    The coordinates do not share a direction, which is the concrete reason a
    single scalar would be meaningless: ``root_bridge_stability`` high means the
    named root bridge has not budged.
    """

    HIGHER_IS_MOVEMENT = "HIGHER_IS_MOVEMENT"
    LOWER_IS_MOVEMENT = "LOWER_IS_MOVEMENT"
    CONTEXT_ONLY = "CONTEXT_ONLY"


COORDINATE_DIRECTIONS: dict[str, CoordinateDirection] = {
    "root_critical_obligations_closed": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "new_root_reachable_states": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "residual_contraction": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "prospective_prediction_success": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "discriminating_falsifier_yield": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "representation_gain": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "retrieval_gain": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "new_verified_local_results": CoordinateDirection.HIGHER_IS_MOVEMENT,
    "auxiliary_complexity_growth": CoordinateDirection.CONTEXT_ONLY,
    "repeated_failure_redundancy": CoordinateDirection.CONTEXT_ONLY,
    "root_bridge_stability": CoordinateDirection.LOWER_IS_MOVEMENT,
    "verification_debt_growth": CoordinateDirection.CONTEXT_ONLY,
    "cost_per_epistemic_gain": CoordinateDirection.CONTEXT_ONLY,
    "exploration_diversity": CoordinateDirection.CONTEXT_ONLY,
    "external_blocker_fraction": CoordinateDirection.CONTEXT_ONLY,
}

COORDINATE_NAMES: Tuple[str, ...] = tuple(COORDINATE_DIRECTIONS)

DEFAULT_NON_COMPENSATORY: Tuple[str, ...] = (
    "root_critical_obligations_closed",
    "new_root_reachable_states",
    "root_bridge_stability",
)


@dataclass(frozen=True)
class ProgrammeHealthVector:
    """A vector, not a score.

    There is no ``score``, ``total``, ``__add__`` or comparison operator, and
    ``iter()``/``float()`` raise.  Thirty local lemmas cannot be summed against a
    motionless root bridge because there is nothing to sum them into.
    """

    coordinates: Tuple[Tuple[str, float], ...]
    non_compensatory_coordinates: Tuple[str, ...]
    window_episode_ids: Tuple[str, ...]

    def __post_init__(self) -> None:
        names = [name for name, _ in self.coordinates]
        if len(set(names)) != len(names):
            raise ValueError("health-vector coordinate names must be unique")
        unknown = set(names) - set(COORDINATE_NAMES)
        if unknown:
            raise ValueError(f"unknown health coordinates: {sorted(unknown)}")
        missing = set(COORDINATE_NAMES) - set(names)
        if missing:
            raise ValueError(f"health vector is missing coordinates: {sorted(missing)}")
        if not self.non_compensatory_coordinates:
            raise ValueError(
                "declare at least one non-compensatory coordinate; a vector where "
                "everything trades off is a score wearing a tuple"
            )
        undeclared = set(self.non_compensatory_coordinates) - set(names)
        if undeclared:
            raise ValueError(
                f"non-compensatory coordinates not in the vector: {sorted(undeclared)}"
            )
        context_only = [
            name
            for name in self.non_compensatory_coordinates
            if COORDINATE_DIRECTIONS[name] is CoordinateDirection.CONTEXT_ONLY
        ]
        if context_only:
            raise ValueError(
                "context-only coordinates have no movement direction and cannot be "
                f"non-compensatory: {sorted(context_only)}"
            )

    def __iter__(self) -> "ProgrammeHealthVector":
        raise TypeError(
            "ProgrammeHealthVector is deliberately not iterable: aggregating its "
            "coordinates would defeat the non-compensatory design. Read named "
            "coordinates with .value(name)."
        )

    def __float__(self) -> float:
        raise TypeError(
            "ProgrammeHealthVector has no scalar value by design; route health is "
            "a vector with non-compensatory coordinates."
        )

    def value(self, name: str) -> float:
        for coordinate, value in self.coordinates:
            if coordinate == name:
                return value
        raise KeyError(name)

    def shows_movement(self, name: str) -> bool:
        direction = COORDINATE_DIRECTIONS[name]
        value = self.value(name)
        if direction is CoordinateDirection.HIGHER_IS_MOVEMENT:
            return value > 0.0
        if direction is CoordinateDirection.LOWER_IS_MOVEMENT:
            return value < 1.0
        raise ValueError(f"{name} is context only and has no movement direction")

    @property
    def stalled_non_compensatory_coordinates(self) -> Tuple[str, ...]:
        return tuple(
            name
            for name in self.non_compensatory_coordinates
            if not self.shows_movement(name)
        )


# --------------------------------------------------------------------------
# Lineage and window observation
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class RouteFamilyLineage:
    """A coherent family of attempts sharing a declared core.

    Preferred over ``ResearchProgrammeLineage``: it names what is actually being
    tracked without importing a philosophy-of-science verdict.  Episodes are
    referenced by id in chronology; they are never copied or summarised away.
    """

    lineage_id: str
    root_goal_id: str
    route_family_id: str
    core_representation_or_mechanism: str
    root_bridge_hypothesis: str
    founding_episode_id: str
    episode_ids_in_chronology: Tuple[str, ...]
    continuity_policy_id: str
    child_atom_ids: Tuple[str, ...] = ()
    representation_revisions: Tuple[str, ...] = ()
    operator_families_used: Tuple[str, ...] = ()
    auxiliary_assumptions_introduced: Tuple[str, ...] = ()
    auxiliary_assumptions_removed: Tuple[str, ...] = ()
    prospectively_frozen_falsifiers: Tuple[str, ...] = ()
    local_result_ids: Tuple[str, ...] = ()
    root_critical_result_ids: Tuple[str, ...] = ()
    failure_ids: Tuple[str, ...] = ()
    diagnosis_revision_ids: Tuple[str, ...] = ()
    external_blocker_ids: Tuple[str, ...] = ()
    descends_from_lineage_id: str = ""
    responds_to_lineage_id: str = ""

    def __post_init__(self) -> None:
        if not self.lineage_id or not self.root_goal_id or not self.route_family_id:
            raise ValueError("lineages require lineage, root goal and route family ids")
        if not self.founding_episode_id:
            raise ValueError("lineages require a founding episode")
        if self.founding_episode_id not in self.episode_ids_in_chronology:
            raise ValueError("the founding episode must appear in the chronology")
        if len(set(self.episode_ids_in_chronology)) != len(self.episode_ids_in_chronology):
            raise ValueError("episode chronology must not repeat an episode id")

    @property
    def grants_theorem_authority(self) -> bool:
        return False

    @property
    def grants_method_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class RouteWindowObservation:
    """Observed telemetry for one route family over one registered window.

    Every field is supplied by a caller reading real episode history.  Nothing
    here is inferred, and the assessor never fabricates a coordinate.
    """

    lineage_id: str
    window_episode_ids: Tuple[str, ...]
    root_obligations_verified_closed: int
    root_reachable_states_from_verified_root_work: int
    residual_contraction: float
    discriminating_falsifiers_yielded: int
    representation_gain: float
    retrieval_gain: float
    verified_local_results: int
    auxiliary_assumptions_added_after_failure: int
    exception_classes_added: int
    route_specific_repair_lemmas: int
    interfaces_opened: int
    interfaces_closed: int
    repeated_failure_redundancy: float
    root_bridge_stability: float
    verification_debt_growth: float
    cost_per_epistemic_gain: float
    exploration_diversity: float
    actions_blocked_externally: int
    actions_attempted: int
    named_external_blockers: Tuple[str, ...]
    search_space_eliminated: float
    stable_obstruction_identified: Optional[bool]
    forced_productive_representation_reset: Optional[bool]
    representation_reset_declared: Optional[bool]
    chronology_records: Tuple[ChronologyRecord, ...] = ()
    surrogate_improvements: Tuple[SurrogateImprovement, ...] = ()

    def __post_init__(self) -> None:
        if not self.lineage_id:
            raise ValueError("window observations require a lineage_id")
        if self.actions_attempted < 0 or self.actions_blocked_externally < 0:
            raise ValueError("action counts cannot be negative")
        if self.actions_blocked_externally > self.actions_attempted:
            raise ValueError("cannot block more actions than were attempted")
        if not 0.0 <= self.root_bridge_stability <= 1.0:
            raise ValueError("root_bridge_stability is a fraction in [0, 1]")

    @property
    def patch_debt(self) -> int:
        return (
            self.auxiliary_assumptions_added_after_failure
            + self.exception_classes_added
            + self.route_specific_repair_lemmas
            + max(self.interfaces_opened - self.interfaces_closed, 0)
        )

    @property
    def external_blocker_fraction(self) -> float:
        if self.actions_attempted <= 0:
            return 0.0
        return self.actions_blocked_externally / self.actions_attempted


@dataclass(frozen=True)
class RouteFamilyHealthReport:
    state: RouteHealthState
    lineage_id: str
    vector: Optional[ProgrammeHealthVector]
    stalled_non_compensatory_coordinates: Tuple[str, ...]
    progress_classifications: Tuple[ProgressClassification, ...]
    chronology: Optional[ChronologyTally]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_abandonment_authority(self) -> bool:
        return False

    @property
    def recommends_abandonment(self) -> bool:
        """Never.  This diagnostic does not stop a route."""

        return False

    @property
    def is_truth_verdict(self) -> bool:
        return False


def assess_route_family_health(
    lineage: RouteFamilyLineage,
    observation: RouteWindowObservation,
    *,
    preservation_interface: Optional[RootCoordinatePreservationInterface] = None,
    non_compensatory_coordinates: Tuple[str, ...] = DEFAULT_NON_COMPENSATORY,
    minimum_window_episodes: int = 3,
    external_blocker_fraction_threshold: float = 0.5,
) -> RouteFamilyHealthReport:
    """Describe how a route family's problem shifts behaved over a window.

    The classifier order is load-bearing.  ``EXTERNALLY_BLOCKED`` pre-empts
    stagnation, and the non-compensatory gate is evaluated as a hard predicate
    before any compensatory coordinate is read.
    """

    if observation.lineage_id != lineage.lineage_id:
        return RouteFamilyHealthReport(
            RouteHealthState.CANNOT_CHECK,
            lineage.lineage_id,
            None,
            (),
            (),
            None,
            ("observation_bound_to_a_different_lineage",),
        )

    tally = tally_chronology(observation.chronology_records)
    if tally.unknown_chronology:
        return RouteFamilyHealthReport(
            RouteHealthState.CANNOT_CHECK,
            lineage.lineage_id,
            None,
            (),
            (),
            tally,
            ("chronology_unknown_for:" + ",".join(tally.unknown_chronology),),
        )

    unknown_tristates = [
        name
        for name, value in (
            ("stable_obstruction_identified", observation.stable_obstruction_identified),
            (
                "forced_productive_representation_reset",
                observation.forced_productive_representation_reset,
            ),
            ("representation_reset_declared", observation.representation_reset_declared),
        )
        if value is None
    ]
    if unknown_tristates:
        return RouteFamilyHealthReport(
            RouteHealthState.CANNOT_CHECK,
            lineage.lineage_id,
            None,
            (),
            (),
            tally,
            ("route_state_unknown_for:" + ",".join(unknown_tristates),),
        )

    classifications = tuple(
        classify_surrogate_improvement(improvement, preservation_interface)
        for improvement in observation.surrogate_improvements
    )
    if any(item.kind is ProgressKind.CANNOT_CHECK for item in classifications):
        return RouteFamilyHealthReport(
            RouteHealthState.CANNOT_CHECK,
            lineage.lineage_id,
            None,
            (),
            classifications,
            tally,
            ("surrogate_to_root_preservation_status_unresolved",),
        )

    surrogate_root = sum(
        1 for item in classifications if item.kind is ProgressKind.ROOT_PROGRESS
    )
    surrogate_local = sum(
        1 for item in classifications if item.kind is ProgressKind.LOCAL_PROGRESS
    )

    vector = ProgrammeHealthVector(
        coordinates=(
            ("root_critical_obligations_closed", float(observation.root_obligations_verified_closed)),
            (
                "new_root_reachable_states",
                float(
                    observation.root_reachable_states_from_verified_root_work + surrogate_root
                ),
            ),
            ("residual_contraction", observation.residual_contraction),
            ("prospective_prediction_success", float(tally.prospective_successes)),
            ("discriminating_falsifier_yield", float(observation.discriminating_falsifiers_yielded)),
            ("representation_gain", observation.representation_gain),
            ("retrieval_gain", observation.retrieval_gain),
            (
                "new_verified_local_results",
                float(observation.verified_local_results + surrogate_local),
            ),
            ("auxiliary_complexity_growth", float(observation.patch_debt)),
            ("repeated_failure_redundancy", observation.repeated_failure_redundancy),
            ("root_bridge_stability", observation.root_bridge_stability),
            ("verification_debt_growth", observation.verification_debt_growth),
            ("cost_per_epistemic_gain", observation.cost_per_epistemic_gain),
            ("exploration_diversity", observation.exploration_diversity),
            ("external_blocker_fraction", observation.external_blocker_fraction),
        ),
        non_compensatory_coordinates=non_compensatory_coordinates,
        window_episode_ids=observation.window_episode_ids,
    )

    base_reasons: list[str] = [
        "descriptive_search_control_signal_only",
        "no_truth_or_rationality_verdict_is_implied",
        f"surrogate_improvements_counted_as_root_progress:{surrogate_root}",
        f"surrogate_improvements_counted_as_local_progress:{surrogate_local}",
    ]
    if tally.rewritten_predictions:
        base_reasons.append(
            f"{RouteHealthFailureMode.RETROSPECTIVE_PREDICTION_REWRITE.value}:"
            + ",".join(tally.rewritten_predictions)
        )

    if len(observation.window_episode_ids) < minimum_window_episodes:
        return RouteFamilyHealthReport(
            RouteHealthState.INSUFFICIENT_HISTORY,
            lineage.lineage_id,
            vector,
            vector.stalled_non_compensatory_coordinates,
            classifications,
            tally,
            tuple(
                [
                    f"window_episodes:{len(observation.window_episode_ids)}",
                    f"required:{minimum_window_episodes}",
                    "short_windows_are_not_evidence_of_stagnation",
                ]
                + base_reasons
            ),
        )

    if observation.representation_reset_declared is True:
        return RouteFamilyHealthReport(
            RouteHealthState.RESTRUCTURING_SIGNAL,
            lineage.lineage_id,
            vector,
            vector.stalled_non_compensatory_coordinates,
            classifications,
            tally,
            tuple(
                [
                    "route_declared_a_representation_or_method_reset",
                    "compare_the_post_reset_window_as_a_new_lineage",
                ]
                + base_reasons
            ),
        )

    if (
        observation.named_external_blockers
        and observation.external_blocker_fraction >= external_blocker_fraction_threshold
    ):
        return RouteFamilyHealthReport(
            RouteHealthState.EXTERNALLY_BLOCKED,
            lineage.lineage_id,
            vector,
            vector.stalled_non_compensatory_coordinates,
            classifications,
            tally,
            tuple(
                [
                    "named_unavailable_dependencies:"
                    + ",".join(observation.named_external_blockers),
                    f"external_blocker_fraction:{observation.external_blocker_fraction:.3f}",
                    "an_externally_blocked_route_has_not_exhausted_its_internal_basis",
                ]
                + base_reasons
            ),
        )

    stalled = vector.stalled_non_compensatory_coordinates
    if not stalled:
        return RouteFamilyHealthReport(
            RouteHealthState.PROGRESSIVE_SIGNAL,
            lineage.lineage_id,
            vector,
            (),
            classifications,
            tally,
            tuple(
                [
                    "every_declared_non_compensatory_coordinate_moved",
                    "route_is_generating_new_verified_root_relevant_reachability",
                ]
                + base_reasons
            ),
        )

    stalled_reasons = [
        "non_compensatory_coordinates_without_movement:" + ",".join(stalled),
        "local_results_cannot_compensate_for_a_motionless_root_bridge",
    ]

    informative = (
        observation.search_space_eliminated > 0.0
        or observation.stable_obstruction_identified is True
        or observation.forced_productive_representation_reset is True
        or observation.discriminating_falsifiers_yielded > 0
    )

    if (
        observation.patch_debt > 0
        and tally.posthoc_repairs > 0
        and tally.prospective_successes == 0
    ):
        return RouteFamilyHealthReport(
            RouteHealthState.PATCH_ACCUMULATION_SIGNAL,
            lineage.lineage_id,
            vector,
            stalled,
            classifications,
            tally,
            tuple(
                stalled_reasons
                + [
                    f"posthoc_repairs:{tally.posthoc_repairs}",
                    "no_new_prospective_discriminating_success_in_window",
                    "complexity_growth_alone_would_not_have_been_sufficient",
                ]
                + base_reasons
            ),
        )

    local_progress = (
        observation.verified_local_results + surrogate_local > 0
        or observation.representation_gain > 0.0
        or observation.retrieval_gain > 0.0
        or observation.residual_contraction > 0.0
    )
    if not informative and not local_progress:
        return RouteFamilyHealthReport(
            RouteHealthState.STAGNANT_SIGNAL,
            lineage.lineage_id,
            vector,
            stalled,
            classifications,
            tally,
            tuple(
                stalled_reasons
                + [
                    "no_new_local_results_and_no_search_space_elimination",
                    "no_stable_obstruction_identified",
                    "stagnation_is_a_search_control_signal_not_a_reason_to_abandon",
                ]
                + base_reasons
            ),
        )

    return RouteFamilyHealthReport(
        RouteHealthState.LOCALLY_PROGRESSIVE_ROOT_STALLED,
        lineage.lineage_id,
        vector,
        stalled,
        classifications,
        tally,
        tuple(
            stalled_reasons
            + [
                f"informative_failures_or_local_progress_present:{informative or local_progress}",
                f"search_space_eliminated:{observation.search_space_eliminated:.3f}",
                "retain_local_results_and_negative_history",
            ]
            + base_reasons
        ),
    )
