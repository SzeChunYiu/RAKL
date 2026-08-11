"""Frozen hidden-path benchmark harness for backward/multi-seed search (issue #141).

Status: ``FRAMEWORK_EXTENSION_HYPOTHESIS / PROSPECTIVE_BENCHMARK_REQUIRED /
NO_SCIENTIFIC_AUTHORITY``.

This module freezes *how* arms A-F would be compared.  It is deliberately
committed before any generation or ranking heuristic so that the repository
chronology shows the evaluator was fixed before the thing it evaluates.

The harness never generates an outcome.  Every number it reports is derived from
:class:`TaskArmObservation` values supplied by a caller that actually ran a solver.
With no observations supplied the harness returns ``INSUFFICIENT_HISTORY``; there
is no code path that manufactures an arm result.

Two contamination ceilings are treated as *admissibility*, not quality:

* ``false_root_progress_rate`` above its ceiling means the arm's reported root
  progress cannot be trusted, so its solve count is not comparable evidence;
* ``connection_test_precision`` below its floor means the arm calls unverified
  connections roads (``UNVERIFIED_CONNECTION_AS_ROAD``).

An inadmissible arm ranks after every admissible arm regardless of solve rate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable, Optional, Tuple


class SearchArm(str, Enum):
    """The six matched-budget arms frozen by issue #141."""

    A_FORWARD_ONLY = "A_FORWARD_ONLY"
    B_BACKWARD_ONLY = "B_BACKWARD_ONLY"
    C_FORWARD_BACKWARD = "C_FORWARD_BACKWARD"
    D_FORWARD_SEEDS = "D_FORWARD_SEEDS"
    E_FORWARD_BACKWARD_SEEDS = "E_FORWARD_BACKWARD_SEEDS"
    F_FORWARD_BACKWARD_SEEDS_EXPERIENCE = "F_FORWARD_BACKWARD_SEEDS_EXPERIENCE"


class HiddenPathTaskFamily(str, Enum):
    """The nine task families frozen by issue #141."""

    SHORT_DIRECT_FORWARD = "SHORT_DIRECT_FORWARD"
    BACKWARD_EASIER_KEY_LEMMA = "BACKWARD_EASIER_KEY_LEMMA"
    NONOBVIOUS_INTERMEDIATE_INVARIANT = "NONOBVIOUS_INTERMEDIATE_INVARIANT"
    REPRESENTATION_TRAP = "REPRESENTATION_TRAP"
    MULTIPLE_PROOF_ARCHITECTURES = "MULTIPLE_PROOF_ARCHITECTURES"
    TEMPTING_IRRELEVANT_LEMMAS = "TEMPTING_IRRELEVANT_LEMMAS"
    LOCAL_TO_GLOBAL_BRIDGE = "LOCAL_TO_GLOBAL_BRIDGE"
    FORMAL_KNOWN_PROOF_DAG = "FORMAL_KNOWN_PROOF_DAG"
    SOURCE_BOUND_INFORMAL = "SOURCE_BOUND_INFORMAL"


class ArmVerdict(str, Enum):
    ARM_ADMISSIBLE = "ARM_ADMISSIBLE"
    ARM_CONTAMINATED = "ARM_CONTAMINATED"
    TRIAL_INVALID = "TRIAL_INVALID"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MatchedBudget:
    """Per-case budget every arm must respect for the comparison to be matched."""

    max_expansions: int
    max_connection_tests: int
    max_tool_calls: int
    max_tokens: int
    max_wall_clock_seconds: float

    def __post_init__(self) -> None:
        values = (
            self.max_expansions,
            self.max_connection_tests,
            self.max_tool_calls,
            self.max_tokens,
        )
        if any(value < 1 for value in values) or self.max_wall_clock_seconds <= 0:
            raise ValueError("matched budget limits must be positive")


@dataclass(frozen=True)
class ContaminationCeilings:
    """Frozen integrity ceilings; breaching one makes an arm's evidence untrusted."""

    max_false_root_progress_rate: float
    min_connection_test_precision: float
    max_repeated_known_failure_rate: float

    def __post_init__(self) -> None:
        for value in (
            self.max_false_root_progress_rate,
            self.min_connection_test_precision,
            self.max_repeated_known_failure_rate,
        ):
            if value < 0.0 or value > 1.0:
                raise ValueError("contamination ceilings must lie in [0, 1]")


@dataclass(frozen=True)
class HiddenPathCase:
    """One frozen task whose solution the evaluator knows and the solver does not."""

    case_id: str
    family: HiddenPathTaskFamily
    root_goal_id: str
    frozen_evidence_ids: Tuple[str, ...]
    evaluator_knows_solution: Optional[bool]
    gold_path_hidden_from_solver: Optional[bool]
    evaluator_separate_from_solver: Optional[bool]

    def __post_init__(self) -> None:
        if not self.case_id or not self.root_goal_id:
            raise ValueError("hidden-path cases require case_id and root_goal_id")
        if not self.frozen_evidence_ids:
            raise ValueError("hidden-path cases require a frozen evidence packet")


@dataclass(frozen=True)
class TaskArmObservation:
    """Externally observed result of running one arm on one case.

    Every field is an observation.  Nothing here is derived, defaulted to a
    favourable value, or inferred by the harness.
    """

    benchmark_id: str
    case_id: str
    arm: SearchArm
    verified_solved: Optional[bool]
    root_obligations_declared: int
    root_obligations_verified_closed: int
    waypoints_emitted: int
    waypoints_used_in_verified_connection: int
    waypoints_judged_irrelevant_by_evaluator: int
    connection_tests_run: int
    connection_tests_claimed_verified: int
    connection_tests_confirmed_by_checker: int
    root_progress_claims: int
    root_progress_claims_upheld: int
    repeated_known_failure_retries: int
    distinct_representations_used: int
    forward_frontier_signature: Tuple[str, ...]
    backward_frontier_signature: Tuple[str, ...]
    expansions_used: int
    tool_calls_used: int
    tokens_used: int
    wall_clock_seconds: float
    verification_debt: float
    gold_path_exposed: Optional[bool]
    budget_frozen_before_run: Optional[bool]

    def __post_init__(self) -> None:
        counts = (
            self.root_obligations_declared,
            self.root_obligations_verified_closed,
            self.waypoints_emitted,
            self.waypoints_used_in_verified_connection,
            self.waypoints_judged_irrelevant_by_evaluator,
            self.connection_tests_run,
            self.connection_tests_claimed_verified,
            self.connection_tests_confirmed_by_checker,
            self.root_progress_claims,
            self.root_progress_claims_upheld,
            self.repeated_known_failure_retries,
            self.distinct_representations_used,
            self.expansions_used,
            self.tool_calls_used,
            self.tokens_used,
        )
        if any(value < 0 for value in counts):
            raise ValueError("observation counts cannot be negative")
        if self.wall_clock_seconds < 0 or self.verification_debt < 0:
            raise ValueError("observed cost and debt cannot be negative")
        if self.root_obligations_verified_closed > self.root_obligations_declared:
            raise ValueError("cannot close more root obligations than were declared")
        if self.root_progress_claims_upheld > self.root_progress_claims:
            raise ValueError("cannot uphold more root-progress claims than were made")
        if self.connection_tests_confirmed_by_checker > self.connection_tests_claimed_verified:
            raise ValueError("cannot confirm more connections than were claimed verified")
        if (
            self.waypoints_used_in_verified_connection
            + self.waypoints_judged_irrelevant_by_evaluator
            > self.waypoints_emitted
        ):
            raise ValueError("useful plus irrelevant waypoints cannot exceed those emitted")


@dataclass(frozen=True)
class FrozenBenchmarkSpec:
    """The evaluator, frozen before any arm runs.

    ``spec_hash`` covers the arms, cases, budget and ceilings, so changing a
    threshold after the fact produces a different identity.
    """

    benchmark_id: str
    cases: Tuple[HiddenPathCase, ...]
    arms: Tuple[SearchArm, ...]
    budget: MatchedBudget
    ceilings: ContaminationCeilings
    minimum_cases_per_arm: int
    frozen_before_any_arm_execution: Optional[bool]

    def __post_init__(self) -> None:
        if not self.benchmark_id:
            raise ValueError("benchmark_id is required")
        if not self.cases:
            raise ValueError("a frozen benchmark requires at least one case")
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("case ids must be unique")
        if len(self.arms) < 2:
            raise ValueError("an arm comparison requires at least two arms")
        if len(set(self.arms)) != len(self.arms):
            raise ValueError("arms must be unique")
        if self.minimum_cases_per_arm < 1:
            raise ValueError("minimum_cases_per_arm must be positive")

    @property
    def spec_hash(self) -> str:
        payload = "|".join(
            (
                self.benchmark_id,
                ",".join(arm.value for arm in self.arms),
                ",".join(f"{case.case_id}:{case.family.value}" for case in self.cases),
                f"{self.budget.max_expansions}:{self.budget.max_connection_tests}:"
                f"{self.budget.max_tool_calls}:{self.budget.max_tokens}:"
                f"{self.budget.max_wall_clock_seconds}",
                f"{self.ceilings.max_false_root_progress_rate}:"
                f"{self.ceilings.min_connection_test_precision}:"
                f"{self.ceilings.max_repeated_known_failure_rate}",
                str(self.minimum_cases_per_arm),
            )
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    @property
    def covers_all_task_families(self) -> bool:
        return {case.family for case in self.cases} == set(HiddenPathTaskFamily)

    @property
    def covers_all_arms(self) -> bool:
        return set(self.arms) == set(SearchArm)


@dataclass(frozen=True)
class ArmMetrics:
    """Issue #141's primary metric list, all derived from observations."""

    arm: SearchArm
    cases_observed: int
    verified_solve_rate: float
    verified_root_obligation_closure: Optional[float]
    useful_waypoint_rate: Optional[float]
    irrelevant_waypoint_rate: Optional[float]
    connection_test_precision: Optional[float]
    forward_backward_frontier_overlap: Optional[float]
    false_root_progress_rate: Optional[float]
    repeated_known_failure_rate: Optional[float]
    representation_diversity: float
    expansions: int
    tool_calls: int
    tokens: int
    wall_clock_seconds: float
    verification_debt: float
    cost_per_verified_solve: float

    @property
    def grants_capability_claim(self) -> bool:
        return False


@dataclass(frozen=True)
class ArmReport:
    verdict: ArmVerdict
    metrics: Optional[ArmMetrics]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def admissible(self) -> bool:
        return self.verdict is ArmVerdict.ARM_ADMISSIBLE


def _rate(numerator: int, denominator: int) -> Optional[float]:
    if denominator <= 0:
        return None
    return numerator / denominator


def _overlap(left: Tuple[str, ...], right: Tuple[str, ...]) -> Optional[float]:
    union = set(left) | set(right)
    if not union:
        return None
    return len(set(left) & set(right)) / len(union)


def evaluate_arm(
    spec: FrozenBenchmarkSpec,
    observations: Iterable[TaskArmObservation],
    arm: SearchArm,
) -> ArmReport:
    """Score one arm against the frozen spec from supplied observations only."""

    if arm not in spec.arms:
        return ArmReport(ArmVerdict.TRIAL_INVALID, None, ("arm_not_registered_in_frozen_spec",))
    if spec.frozen_before_any_arm_execution is None:
        return ArmReport(ArmVerdict.CANNOT_CHECK, None, ("benchmark_freeze_chronology_unknown",))
    if spec.frozen_before_any_arm_execution is False:
        return ArmReport(ArmVerdict.TRIAL_INVALID, None, ("benchmark_frozen_after_arm_execution",))

    case_ids = {case.case_id for case in spec.cases}
    by_case = {case.case_id: case for case in spec.cases}
    rows = tuple(
        row
        for row in observations
        if row.arm is arm and row.benchmark_id == spec.benchmark_id
    )
    if not rows:
        return ArmReport(
            ArmVerdict.INSUFFICIENT_HISTORY,
            None,
            ("no_observations_supplied_for_arm", "harness_does_not_generate_arm_results"),
        )
    if len(rows) < spec.minimum_cases_per_arm:
        return ArmReport(
            ArmVerdict.INSUFFICIENT_HISTORY,
            None,
            (f"observed_cases:{len(rows)}", f"required_cases:{spec.minimum_cases_per_arm}"),
        )
    if len({row.case_id for row in rows}) != len(rows):
        return ArmReport(ArmVerdict.TRIAL_INVALID, None, ("duplicate_case_observations_for_arm",))

    unknown = tuple(sorted({row.case_id for row in rows} - case_ids))
    if unknown:
        return ArmReport(
            ArmVerdict.TRIAL_INVALID, None, ("observation_case_not_in_frozen_spec:" + ",".join(unknown),)
        )

    integrity_unknown: list[str] = []
    for row in rows:
        case = by_case[row.case_id]
        if case.evaluator_knows_solution is None:
            integrity_unknown.append(f"evaluator_solution_status_unknown:{row.case_id}")
        if case.gold_path_hidden_from_solver is None:
            integrity_unknown.append(f"gold_path_hidden_status_unknown:{row.case_id}")
        if case.evaluator_separate_from_solver is None:
            integrity_unknown.append(f"evaluator_separation_unknown:{row.case_id}")
        if row.gold_path_exposed is None:
            integrity_unknown.append(f"gold_path_exposure_unknown:{row.case_id}")
        if row.budget_frozen_before_run is None:
            integrity_unknown.append(f"budget_freeze_chronology_unknown:{row.case_id}")
        if row.verified_solved is None:
            integrity_unknown.append(f"solve_outcome_unknown:{row.case_id}")
    if integrity_unknown:
        return ArmReport(ArmVerdict.CANNOT_CHECK, None, tuple(sorted(set(integrity_unknown))))

    invalid: list[str] = []
    for row in rows:
        case = by_case[row.case_id]
        if case.gold_path_hidden_from_solver is not True or row.gold_path_exposed is True:
            invalid.append(f"GOLD_PATH_LEAK:{row.case_id}")
        if case.evaluator_separate_from_solver is not True:
            invalid.append(f"evaluator_not_separate:{row.case_id}")
        if row.budget_frozen_before_run is not True:
            invalid.append(f"budget_not_frozen_before_run:{row.case_id}")
        if row.expansions_used > spec.budget.max_expansions:
            invalid.append(f"budget_violation_expansions:{row.case_id}")
        if row.connection_tests_run > spec.budget.max_connection_tests:
            invalid.append(f"budget_violation_connection_tests:{row.case_id}")
        if row.tool_calls_used > spec.budget.max_tool_calls:
            invalid.append(f"budget_violation_tool_calls:{row.case_id}")
        if row.tokens_used > spec.budget.max_tokens:
            invalid.append(f"budget_violation_tokens:{row.case_id}")
        if row.wall_clock_seconds > spec.budget.max_wall_clock_seconds:
            invalid.append(f"budget_violation_wall_clock:{row.case_id}")
    if invalid:
        return ArmReport(ArmVerdict.TRIAL_INVALID, None, tuple(sorted(set(invalid))))

    solved = sum(1 for row in rows if row.verified_solved is True)
    declared = sum(row.root_obligations_declared for row in rows)
    closed = sum(row.root_obligations_verified_closed for row in rows)
    emitted = sum(row.waypoints_emitted for row in rows)
    useful = sum(row.waypoints_used_in_verified_connection for row in rows)
    irrelevant = sum(row.waypoints_judged_irrelevant_by_evaluator for row in rows)
    claimed = sum(row.connection_tests_claimed_verified for row in rows)
    confirmed = sum(row.connection_tests_confirmed_by_checker for row in rows)
    tests = sum(row.connection_tests_run for row in rows)
    claims = sum(row.root_progress_claims for row in rows)
    upheld = sum(row.root_progress_claims_upheld for row in rows)
    retries = sum(row.repeated_known_failure_retries for row in rows)
    expansions = sum(row.expansions_used for row in rows)
    tool_calls = sum(row.tool_calls_used for row in rows)
    tokens = sum(row.tokens_used for row in rows)
    seconds = sum(row.wall_clock_seconds for row in rows)
    debt = sum(row.verification_debt for row in rows)

    overlaps = tuple(
        value
        for value in (
            _overlap(row.forward_frontier_signature, row.backward_frontier_signature)
            for row in rows
        )
        if value is not None
    )
    metrics = ArmMetrics(
        arm=arm,
        cases_observed=len(rows),
        verified_solve_rate=solved / len(rows),
        verified_root_obligation_closure=_rate(closed, declared),
        useful_waypoint_rate=_rate(useful, emitted),
        irrelevant_waypoint_rate=_rate(irrelevant, emitted),
        connection_test_precision=_rate(confirmed, claimed),
        forward_backward_frontier_overlap=(
            sum(overlaps) / len(overlaps) if overlaps else None
        ),
        false_root_progress_rate=_rate(claims - upheld, claims),
        repeated_known_failure_rate=_rate(retries, tests),
        representation_diversity=(
            sum(row.distinct_representations_used for row in rows) / len(rows)
        ),
        expansions=expansions,
        tool_calls=tool_calls,
        tokens=tokens,
        wall_clock_seconds=seconds,
        verification_debt=debt,
        cost_per_verified_solve=(tool_calls / solved if solved else float("inf")),
    )

    contaminated: list[str] = []
    if (
        metrics.false_root_progress_rate is not None
        and metrics.false_root_progress_rate > spec.ceilings.max_false_root_progress_rate
    ):
        contaminated.append("LOCAL_WAYPOINT_AS_ROOT_PROGRESS:false_root_progress_above_ceiling")
    if (
        metrics.connection_test_precision is not None
        and metrics.connection_test_precision < spec.ceilings.min_connection_test_precision
    ):
        contaminated.append("UNVERIFIED_CONNECTION_AS_ROAD:connection_precision_below_floor")
    if (
        metrics.repeated_known_failure_rate is not None
        and metrics.repeated_known_failure_rate > spec.ceilings.max_repeated_known_failure_rate
    ):
        contaminated.append("repeated_known_failure_rate_above_ceiling")
    if contaminated:
        return ArmReport(ArmVerdict.ARM_CONTAMINATED, metrics, tuple(contaminated))

    return ArmReport(
        ArmVerdict.ARM_ADMISSIBLE,
        metrics,
        (
            "matched_budget_respected",
            "gold_path_hidden_and_unexposed",
            "contamination_ceilings_respected",
            "arm_metrics_are_observations_not_capability_claims",
        ),
    )


def _ranking_key(report: ArmReport) -> Tuple[int, float, float, float, float, str]:
    """Lexicographic, deliberately non-compensatory in its first coordinate.

    Admissibility dominates: a contaminated or invalid arm can never sort above an
    admissible one, no matter how high its solve rate.  Among admissible arms,
    solve rate leads, then contamination pressure, then cost, then waypoint noise.
    Waypoint *volume* appears nowhere: emitting more ideas cannot improve rank.
    """

    if report.metrics is None:
        return (2, 0.0, 1.0, float("inf"), 1.0, "")
    admissibility = 0 if report.admissible else 1
    false_root = (
        report.metrics.false_root_progress_rate
        if report.metrics.false_root_progress_rate is not None
        else 0.0
    )
    irrelevant = (
        report.metrics.irrelevant_waypoint_rate
        if report.metrics.irrelevant_waypoint_rate is not None
        else 0.0
    )
    return (
        admissibility,
        -report.metrics.verified_solve_rate,
        false_root,
        report.metrics.cost_per_verified_solve,
        irrelevant,
        report.metrics.arm.value,
    )


@dataclass(frozen=True)
class ArmComparisonReport:
    benchmark_id: str
    spec_hash: str
    ranked: Tuple[ArmReport, ...]
    baseline_arm: SearchArm
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def establishes_extension_benefit(self) -> bool:
        """A ranking is never by itself evidence that the extension works."""

        return False

    def rank_of(self, arm: SearchArm) -> Optional[int]:
        for index, report in enumerate(self.ranked):
            if report.metrics is not None and report.metrics.arm is arm:
                return index
        return None


def compare_arms(
    spec: FrozenBenchmarkSpec,
    observations: Iterable[TaskArmObservation],
    *,
    baseline_arm: SearchArm = SearchArm.A_FORWARD_ONLY,
) -> ArmComparisonReport:
    """Rank the frozen arms from supplied observations.

    The incumbent forward-only baseline is named explicitly so that any claimed
    benefit is always stated relative to it.
    """

    rows = tuple(observations)
    reports = tuple(evaluate_arm(spec, rows, arm) for arm in spec.arms)
    ranked = tuple(sorted(reports, key=_ranking_key))
    reasons: list[str] = []
    if not rows:
        reasons.append("no_observations_supplied")
    if not spec.covers_all_task_families:
        reasons.append("frozen_spec_does_not_cover_all_nine_task_families")
    if not spec.covers_all_arms:
        reasons.append("frozen_spec_does_not_cover_all_six_arms")
    if baseline_arm not in spec.arms:
        reasons.append("baseline_arm_not_registered")
    if any(report.verdict is ArmVerdict.ARM_CONTAMINATED for report in reports):
        reasons.append("one_or_more_arms_contaminated_and_ranked_last")
    reasons.append("ranking_is_search_control_evidence_only")
    return ArmComparisonReport(
        benchmark_id=spec.benchmark_id,
        spec_hash=spec.spec_hash,
        ranked=ranked,
        baseline_arm=baseline_arm,
        reasons=tuple(reasons),
    )
