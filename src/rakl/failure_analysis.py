"""Proposal-only failure minimization and constraint conflict/correction analysis.

This module absorbs established debugging/diagnosis semantics into Orion without
claiming that delta debugging, minimal conflicts, or minimal correction sets are
new.  It is deliberately pure and caller-supplied-oracle based.  The only
certified statements it can make concern the exact registered oracle, condition
IDs, context and revision supplied to the call.

Authority boundary
------------------
* a minimized failure context is not a causal/mechanistic explanation;
* an inclusion-minimal result is not minimum-cardinality unless an exhaustive
  oracle proves that stronger statement;
* ``CANNOT_CHECK`` is never coerced into failure/inconsistency;
* no result grants scientific, theorem, solution, or method-promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from itertools import combinations
import json
from typing import Callable, Iterable, Sequence, Tuple


ConditionSet = Tuple[str, ...]
Oracle = Callable[[ConditionSet], "OracleVerdict"]


class OracleVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


class FailureAnalysisKind(str, Enum):
    FAILURE_CONDITION_MINIMIZATION = "FAILURE_CONDITION_MINIMIZATION"
    MINIMAL_CONFLICT = "MINIMAL_CONFLICT"
    MINIMAL_CORRECTION = "MINIMAL_CORRECTION"
    GLOBAL_MINIMUM_FAILURE_ORACLE = "GLOBAL_MINIMUM_FAILURE_ORACLE"
    ALL_MINIMAL_CONFLICTS_ORACLE = "ALL_MINIMAL_CONFLICTS_ORACLE"
    ALL_MINIMAL_CORRECTIONS_ORACLE = "ALL_MINIMAL_CORRECTIONS_ORACLE"


class FailureAnalysisVerdict(str, Enum):
    VERIFIED_RESULT = "VERIFIED_RESULT"
    NO_TARGET_PHENOMENON = "NO_TARGET_PHENOMENON"
    CANNOT_CHECK = "CANNOT_CHECK"
    INTERNAL_INVARIANT_FAILURE = "INTERNAL_INVARIANT_FAILURE"


class MinimalityKind(str, Enum):
    ONE_MINIMAL = "ONE_MINIMAL"
    INCLUSION_MINIMAL = "INCLUSION_MINIMAL"
    GLOBAL_MINIMUM_CARDINALITY = "GLOBAL_MINIMUM_CARDINALITY"
    COMPLETE_ENUMERATION_OF_INCLUSION_MINIMAL_SETS = "COMPLETE_ENUMERATION_OF_INCLUSION_MINIMAL_SETS"


def _canonical_hash(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(raw).hexdigest()


def _validated_conditions(values: Iterable[str]) -> ConditionSet:
    out = tuple(values)
    if any(not isinstance(item, str) or not item.strip() for item in out):
        raise ValueError("condition ids must be nonempty strings")
    if len(out) != len(set(out)):
        raise ValueError("condition ids must be unique")
    return out


def _without(values: ConditionSet, removed: Iterable[str]) -> ConditionSet:
    removed_set = set(removed)
    return tuple(item for item in values if item not in removed_set)


def _split(values: ConditionSet, n: int) -> tuple[ConditionSet, ...]:
    if not values:
        return ()
    n = max(1, min(n, len(values)))
    q, r = divmod(len(values), n)
    chunks: list[ConditionSet] = []
    start = 0
    for index in range(n):
        width = q + (1 if index < r else 0)
        chunk = values[start : start + width]
        start += width
        if chunk:
            chunks.append(chunk)
    return tuple(chunks)


@dataclass
class _TrackedOracle:
    oracle: Oracle
    calls: int = 0
    cannot_check_calls: int = 0

    def __call__(self, conditions: ConditionSet) -> OracleVerdict:
        self.calls += 1
        verdict = self.oracle(conditions)
        if not isinstance(verdict, OracleVerdict):
            raise TypeError("oracle must return OracleVerdict")
        if verdict is OracleVerdict.CANNOT_CHECK:
            self.cannot_check_calls += 1
        return verdict


@dataclass(frozen=True)
class FailureAnalysisReceipt:
    analysis_id: str
    kind: FailureAnalysisKind
    oracle_id: str
    context_hash: str
    revision_id: str
    target_id: str
    source_condition_ids: ConditionSet
    result_sets: Tuple[ConditionSet, ...]
    minimality_kind: MinimalityKind
    oracle_calls: int
    cannot_check_calls: int
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("analysis_id", self.analysis_id),
            ("oracle_id", self.oracle_id),
            ("context_hash", self.context_hash),
            ("revision_id", self.revision_id),
            ("target_id", self.target_id),
        ):
            if not value or not value.strip():
                raise ValueError(f"{name} is required")
        _validated_conditions(self.source_condition_ids)
        if not self.result_sets:
            raise ValueError("verified receipt requires at least one result set")
        for result in self.result_sets:
            _validated_conditions(result)
            if not set(result).issubset(self.source_condition_ids):
                raise ValueError("result condition ids must be a subset of source ids")
        if self.oracle_calls < 1 or self.cannot_check_calls < 0 or self.cannot_check_calls > self.oracle_calls:
            raise ValueError("oracle call counts are invalid")

    @property
    def grants_causal_authority(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def content_hash(self) -> str:
        return _canonical_hash(
            {
                "schema": "orion.failure-analysis-receipt.v1",
                "analysis_id": self.analysis_id,
                "kind": self.kind.value,
                "oracle_id": self.oracle_id,
                "context_hash": self.context_hash,
                "revision_id": self.revision_id,
                "target_id": self.target_id,
                "source_condition_ids": list(self.source_condition_ids),
                "result_sets": [list(result) for result in self.result_sets],
                "minimality_kind": self.minimality_kind.value,
                "oracle_calls": self.oracle_calls,
                "cannot_check_calls": self.cannot_check_calls,
                "notes": list(self.notes),
                "grants_causal_authority": False,
                "grants_scientific_authority": False,
                "grants_method_promotion_authority": False,
            }
        )


@dataclass(frozen=True)
class FailureAnalysisReport:
    verdict: FailureAnalysisVerdict
    reasons: Tuple[str, ...]
    receipt: FailureAnalysisReceipt | None = None
    oracle_calls: int = 0
    cannot_check_calls: int = 0

    @property
    def grants_causal_authority(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def _report(
    verdict: FailureAnalysisVerdict,
    reasons: Sequence[str],
    tracker: _TrackedOracle,
    receipt: FailureAnalysisReceipt | None = None,
) -> FailureAnalysisReport:
    return FailureAnalysisReport(
        verdict=verdict,
        reasons=tuple(reasons),
        receipt=receipt,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
    )


def minimize_failure_conditions(
    condition_ids: Iterable[str],
    oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    failure_id: str,
) -> FailureAnalysisReport:
    """Return a deterministic ddmin-style 1-minimal failure-inducing subset.

    ``FAIL`` means the exact registered failure is reproduced. ``PASS`` means it
    is not. Any ``CANNOT_CHECK`` encountered during the reduction or final
    minimality audit aborts certification rather than being treated as failure.
    """

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(oracle)
    initial = tracker(source)
    if initial is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("initial_failure_cannot_check",), tracker)
    if initial is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("initial_conditions_do_not_reproduce_registered_failure",), tracker)

    current = source
    n = 2
    while len(current) >= 2:
        subsets = _split(current, n)
        reduced = False

        for subset in subsets:
            verdict = tracker(subset)
            if verdict is OracleVerdict.CANNOT_CHECK:
                return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("subset_probe_cannot_check",), tracker)
            if verdict is OracleVerdict.FAIL:
                current = subset
                n = max(n - 1, 2)
                reduced = True
                break
        if reduced:
            continue

        for subset in subsets:
            complement = _without(current, subset)
            verdict = tracker(complement)
            if verdict is OracleVerdict.CANNOT_CHECK:
                return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("complement_probe_cannot_check",), tracker)
            if verdict is OracleVerdict.FAIL:
                current = complement
                n = max(n - 1, 2)
                reduced = True
                break
        if reduced:
            continue

        if n >= len(current):
            break
        n = min(len(current), n * 2)

    # Re-verify the result and the exact one-deletion minimality claim.
    final = tracker(current)
    if final is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("final_failure_recheck_cannot_check",), tracker)
    if final is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("minimized_conditions_no_longer_reproduce_failure",), tracker)
    for index in range(len(current)):
        trial = current[:index] + current[index + 1 :]
        verdict = tracker(trial)
        if verdict is OracleVerdict.CANNOT_CHECK:
            return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("one_minimality_probe_cannot_check",), tracker)
        if verdict is OracleVerdict.FAIL:
            return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("ddmin_result_not_one_minimal",), tracker)

    receipt = FailureAnalysisReceipt(
        analysis_id=analysis_id,
        kind=FailureAnalysisKind.FAILURE_CONDITION_MINIMIZATION,
        oracle_id=oracle_id,
        context_hash=context_hash,
        revision_id=revision_id,
        target_id=failure_id,
        source_condition_ids=source,
        result_sets=(current,),
        minimality_kind=MinimalityKind.ONE_MINIMAL,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
        notes=(
            "ddmin_style_parent_semantics",
            "one_minimal_not_global_minimum",
            "minimized_failure_context_is_not_causal_explanation",
        ),
    )
    return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("registered_failure_preserved", "one_minimality_verified"), tracker, receipt)


def find_minimal_conflict(
    condition_ids: Iterable[str],
    consistency_oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    conflict_id: str,
) -> FailureAnalysisReport:
    """Find one inclusion-minimal inconsistent subset by deletion.

    The consistency predicate is assumed monotone under removal of constraints:
    removing constraints from a consistent set cannot make it inconsistent.
    This is a simple correctness-first development implementation, not a claim
    to outperform QuickXplain.
    """

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(consistency_oracle)
    background = tracker(())
    if background is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("background_consistency_cannot_check",), tracker)
    if background is OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("background_itself_inconsistent_no_condition_conflict",), tracker)

    initial = tracker(source)
    if initial is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("initial_conflict_cannot_check",), tracker)
    if initial is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("source_conditions_are_consistent",), tracker)

    current = list(source)
    index = 0
    while index < len(current):
        trial = tuple(current[:index] + current[index + 1 :])
        verdict = tracker(trial)
        if verdict is OracleVerdict.CANNOT_CHECK:
            return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("conflict_reduction_probe_cannot_check",), tracker)
        if verdict is OracleVerdict.FAIL:
            current.pop(index)
        else:
            index += 1

    result = tuple(current)
    if tracker(result) is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("minimal_conflict_final_set_not_inconsistent",), tracker)
    for index in range(len(result)):
        trial = result[:index] + result[index + 1 :]
        verdict = tracker(trial)
        if verdict is OracleVerdict.CANNOT_CHECK:
            return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("conflict_minimality_probe_cannot_check",), tracker)
        if verdict is not OracleVerdict.PASS:
            return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("conflict_not_inclusion_minimal",), tracker)

    receipt = FailureAnalysisReceipt(
        analysis_id=analysis_id,
        kind=FailureAnalysisKind.MINIMAL_CONFLICT,
        oracle_id=oracle_id,
        context_hash=context_hash,
        revision_id=revision_id,
        target_id=conflict_id,
        source_condition_ids=source,
        result_sets=(result,),
        minimality_kind=MinimalityKind.INCLUSION_MINIMAL,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
        notes=(
            "deletion_based_correctness_first_baseline",
            "inclusion_minimal_not_minimum_cardinality",
            "constraint_conflict_is_not_causal_explanation",
        ),
    )
    return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("conflict_inconsistent", "inclusion_minimality_verified"), tracker, receipt)


def find_minimal_correction(
    condition_ids: Iterable[str],
    consistency_oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    correction_id: str,
) -> FailureAnalysisReport:
    """Find one inclusion-minimal removal set restoring consistency."""

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(consistency_oracle)
    background = tracker(())
    if background is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("background_consistency_cannot_check",), tracker)
    if background is OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("background_inconsistent_no_correction_using_source_conditions",), tracker)

    initial = tracker(source)
    if initial is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("initial_correction_cannot_check",), tracker)
    if initial is OracleVerdict.PASS:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("source_conditions_already_consistent",), tracker)

    removed = list(source)
    index = 0
    while index < len(removed):
        candidate_removed = removed[:index] + removed[index + 1 :]
        kept = _without(source, candidate_removed)
        verdict = tracker(kept)
        if verdict is OracleVerdict.CANNOT_CHECK:
            return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("correction_reduction_probe_cannot_check",), tracker)
        if verdict is OracleVerdict.PASS:
            removed.pop(index)
        else:
            index += 1

    result = tuple(removed)
    kept = _without(source, result)
    final = tracker(kept)
    if final is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("correction_final_recheck_cannot_check",), tracker)
    if final is not OracleVerdict.PASS:
        return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("correction_does_not_restore_consistency",), tracker)

    # Every removed element is necessary: returning it to the kept set must
    # restore inconsistency under the monotone consistency contract.
    for item in result:
        trial_removed = tuple(candidate for candidate in result if candidate != item)
        trial_kept = _without(source, trial_removed)
        verdict = tracker(trial_kept)
        if verdict is OracleVerdict.CANNOT_CHECK:
            return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("correction_minimality_probe_cannot_check",), tracker)
        if verdict is not OracleVerdict.FAIL:
            return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("correction_not_inclusion_minimal",), tracker)

    receipt = FailureAnalysisReceipt(
        analysis_id=analysis_id,
        kind=FailureAnalysisKind.MINIMAL_CORRECTION,
        oracle_id=oracle_id,
        context_hash=context_hash,
        revision_id=revision_id,
        target_id=correction_id,
        source_condition_ids=source,
        result_sets=(result,),
        minimality_kind=MinimalityKind.INCLUSION_MINIMAL,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
        notes=(
            "deletion_based_correctness_first_baseline",
            "minimal_correction_is_removal_set_not_conflict",
            "inclusion_minimal_not_minimum_cardinality",
        ),
    )
    return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("correction_restores_consistency", "inclusion_minimality_verified"), tracker, receipt)


def exhaustive_global_minimum_failure(
    condition_ids: Iterable[str],
    oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    failure_id: str,
) -> FailureAnalysisReport:
    """Exhaustive small-world oracle for a minimum-cardinality failure subset."""

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(oracle)
    initial = tracker(source)
    if initial is OracleVerdict.CANNOT_CHECK:
        return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("initial_failure_cannot_check",), tracker)
    if initial is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("initial_conditions_do_not_reproduce_registered_failure",), tracker)

    for size in range(0, len(source) + 1):
        winners: list[ConditionSet] = []
        for combo in combinations(source, size):
            verdict = tracker(tuple(combo))
            if verdict is OracleVerdict.CANNOT_CHECK:
                return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("exhaustive_failure_probe_cannot_check",), tracker)
            if verdict is OracleVerdict.FAIL:
                winners.append(tuple(combo))
        if winners:
            winners = sorted(winners)
            receipt = FailureAnalysisReceipt(
                analysis_id=analysis_id,
                kind=FailureAnalysisKind.GLOBAL_MINIMUM_FAILURE_ORACLE,
                oracle_id=oracle_id,
                context_hash=context_hash,
                revision_id=revision_id,
                target_id=failure_id,
                source_condition_ids=source,
                result_sets=tuple(winners),
                minimality_kind=MinimalityKind.GLOBAL_MINIMUM_CARDINALITY,
                oracle_calls=tracker.calls,
                cannot_check_calls=tracker.cannot_check_calls,
                notes=("exhaustive_small_world_oracle", "all_minimum_cardinality_failure_subsets_returned"),
            )
            return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("global_minimum_cardinality_verified_by_exhaustion",), tracker, receipt)

    return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("source_failed_but_no_exhaustive_failure_subset_found",), tracker)


def exhaustive_minimal_conflicts(
    condition_ids: Iterable[str],
    consistency_oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    conflict_id: str,
) -> FailureAnalysisReport:
    """Enumerate all inclusion-minimal inconsistent subsets in a small world."""

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(consistency_oracle)
    statuses: dict[ConditionSet, OracleVerdict] = {}
    for size in range(0, len(source) + 1):
        for combo in combinations(source, size):
            subset = tuple(combo)
            verdict = tracker(subset)
            if verdict is OracleVerdict.CANNOT_CHECK:
                return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("exhaustive_conflict_probe_cannot_check",), tracker)
            statuses[subset] = verdict

    if statuses[()] is OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("background_itself_inconsistent_no_condition_conflict",), tracker)
    if statuses[source] is not OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("source_conditions_are_consistent",), tracker)

    minimal: list[ConditionSet] = []
    for subset, verdict in statuses.items():
        if verdict is not OracleVerdict.FAIL:
            continue
        if all(statuses[subset[:i] + subset[i + 1 :]] is OracleVerdict.PASS for i in range(len(subset))):
            minimal.append(subset)
    minimal.sort()
    if not minimal:
        return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("inconsistent_source_without_minimal_conflict",), tracker)

    receipt = FailureAnalysisReceipt(
        analysis_id=analysis_id,
        kind=FailureAnalysisKind.ALL_MINIMAL_CONFLICTS_ORACLE,
        oracle_id=oracle_id,
        context_hash=context_hash,
        revision_id=revision_id,
        target_id=conflict_id,
        source_condition_ids=source,
        result_sets=tuple(minimal),
        minimality_kind=MinimalityKind.COMPLETE_ENUMERATION_OF_INCLUSION_MINIMAL_SETS,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
        notes=("exhaustive_small_world_oracle", "all_inclusion_minimal_conflicts_returned"),
    )
    return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("complete_minimal_conflict_enumeration_verified_by_exhaustion",), tracker, receipt)


def exhaustive_minimal_corrections(
    condition_ids: Iterable[str],
    consistency_oracle: Oracle,
    *,
    analysis_id: str,
    oracle_id: str,
    context_hash: str,
    revision_id: str,
    correction_id: str,
) -> FailureAnalysisReport:
    """Enumerate all inclusion-minimal removal sets restoring consistency."""

    source = _validated_conditions(condition_ids)
    tracker = _TrackedOracle(consistency_oracle)
    statuses: dict[ConditionSet, OracleVerdict] = {}
    for size in range(0, len(source) + 1):
        for combo in combinations(source, size):
            subset = tuple(combo)
            verdict = tracker(subset)
            if verdict is OracleVerdict.CANNOT_CHECK:
                return _report(FailureAnalysisVerdict.CANNOT_CHECK, ("exhaustive_correction_probe_cannot_check",), tracker)
            statuses[subset] = verdict

    if statuses[()] is OracleVerdict.FAIL:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("background_inconsistent_no_correction_using_source_conditions",), tracker)
    if statuses[source] is OracleVerdict.PASS:
        return _report(FailureAnalysisVerdict.NO_TARGET_PHENOMENON, ("source_conditions_already_consistent",), tracker)

    corrections: list[ConditionSet] = []
    for size in range(1, len(source) + 1):
        for removed in combinations(source, size):
            removed_tuple = tuple(removed)
            kept = _without(source, removed_tuple)
            if statuses[kept] is not OracleVerdict.PASS:
                continue
            minimal = True
            for index in range(len(removed_tuple)):
                smaller_removed = removed_tuple[:index] + removed_tuple[index + 1 :]
                smaller_kept = _without(source, smaller_removed)
                if statuses[smaller_kept] is OracleVerdict.PASS:
                    minimal = False
                    break
            if minimal:
                corrections.append(removed_tuple)
    corrections.sort()
    if not corrections:
        return _report(FailureAnalysisVerdict.INTERNAL_INVARIANT_FAILURE, ("inconsistent_source_without_minimal_correction",), tracker)

    receipt = FailureAnalysisReceipt(
        analysis_id=analysis_id,
        kind=FailureAnalysisKind.ALL_MINIMAL_CORRECTIONS_ORACLE,
        oracle_id=oracle_id,
        context_hash=context_hash,
        revision_id=revision_id,
        target_id=correction_id,
        source_condition_ids=source,
        result_sets=tuple(corrections),
        minimality_kind=MinimalityKind.COMPLETE_ENUMERATION_OF_INCLUSION_MINIMAL_SETS,
        oracle_calls=tracker.calls,
        cannot_check_calls=tracker.cannot_check_calls,
        notes=("exhaustive_small_world_oracle", "all_inclusion_minimal_corrections_returned"),
    )
    return _report(FailureAnalysisVerdict.VERIFIED_RESULT, ("complete_minimal_correction_enumeration_verified_by_exhaustion",), tracker, receipt)
