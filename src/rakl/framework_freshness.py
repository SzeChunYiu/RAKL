"""Proposal-only framework freshness / adoption receipt.

An application repository pins a framework subject.  When current framework
``main`` moves ahead of that pin, an application cycle may legitimately read
current ``main`` directly in shadow mode instead of synchronizing the pin.  That
is a weaker act than a tested dependency synchronization, and the difference is
invisible to any later case-study attribution unless it is emitted as one bound,
machine-readable episode-start record.

This module emits that record.  It performs no network access, no git access and
no writes: every observation must be supplied by an independent observer, in the
same spirit as :mod:`rakl.promotion_attestation`.  It deliberately exposes no API
that updates a submodule pin, mints method authority, or converts a
direct-current-main read into a synchronization claim.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Mapping, Tuple


RECEIPT_SCHEMA_VERSION = "framework-freshness-receipt-v1"

_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PinRelation(str, Enum):
    """Ancestry relation between the application's pin and current framework main.

    ``UNOBSERVED`` is a first-class value: an unobserved relation is never
    collapsed into ``EQUAL``.
    """

    EQUAL = "EQUAL"
    PIN_BEHIND_CURRENT_MAIN = "PIN_BEHIND_CURRENT_MAIN"
    PIN_AHEAD_OF_CURRENT_MAIN = "PIN_AHEAD_OF_CURRENT_MAIN"
    DIVERGED = "DIVERGED"
    UNOBSERVED = "UNOBSERVED"


class FreshnessExecutionStatus(str, Enum):
    """What the application cycle actually did about the pin/main delta.

    The three adoption statuses are ``PIN_CURRENT``,
    ``CURRENT_MAIN_READ_DIRECTLY_SHADOW`` and ``PIN_SYNCHRONIZED_AND_TESTED``.
    The remaining values are fail-closed outcomes and are deliberately distinct
    from each other:

    ``STALE_PIN_TREATED_AS_AUTHORITATIVE``
        checked, and the process was defective — the pin was stale and no
        current-main surface was consulted.
    ``PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS``
        checked, and the synchronization is real but untested.
    ``APPLICATION_TEST_BINDING_MISSING``
        *not* checked — a synchronization is claimed with no test binding at all.
    ``CURRENT_MAIN_UNOBSERVED``
        *not* checked — current framework main was never observed.
    ``RECEIPT_UNVERIFIABLE``
        *not* checked — the receipt itself is malformed or unbound.
    """

    PIN_CURRENT = "PIN_CURRENT"
    CURRENT_MAIN_READ_DIRECTLY_SHADOW = "CURRENT_MAIN_READ_DIRECTLY_SHADOW"
    PIN_SYNCHRONIZED_AND_TESTED = "PIN_SYNCHRONIZED_AND_TESTED"
    STALE_PIN_TREATED_AS_AUTHORITATIVE = "STALE_PIN_TREATED_AS_AUTHORITATIVE"
    PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS = (
        "PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS"
    )
    APPLICATION_TEST_BINDING_MISSING = "APPLICATION_TEST_BINDING_MISSING"
    CURRENT_MAIN_UNOBSERVED = "CURRENT_MAIN_UNOBSERVED"
    RECEIPT_UNVERIFIABLE = "RECEIPT_UNVERIFIABLE"


class FreshnessVerdict(str, Enum):
    """Integrity of the receipt, separate from the execution status it carries.

    A well-formed receipt that honestly records a defective process is
    ``RECORDED_PROPOSAL_ONLY``; the defect travels in the effective status, not
    in the verdict.
    """

    RECORDED_PROPOSAL_ONLY = "RECORDED_PROPOSAL_ONLY"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


class CompletenessFreshnessBindingVerdict(str, Enum):
    """Whether a freshness receipt licenses proceeding to a completeness claim.

    Completeness / counting claims (and case-study attribution of what was
    searched under which framework subject) require the pin/current-main relation
    to be *bound* first.  Binding means: current framework ``main`` SHA was
    observed, and the pin relation — equality *or* mismatch — was derived from
    that observation.  An unbound current main or an unobserved pin relation is
    never treated as ``EQUAL`` / current.
    """

    BOUND_PROPOSAL_ONLY = "BOUND_PROPOSAL_ONLY"
    REJECTED_UNBOUND_CURRENT_MAIN = "REJECTED_UNBOUND_CURRENT_MAIN"
    REJECTED_UNBOUND_PIN_RELATION = "REJECTED_UNBOUND_PIN_RELATION"
    REJECTED_FRESHNESS_RECEIPT_UNVERIFIABLE = (
        "REJECTED_FRESHNESS_RECEIPT_UNVERIFIABLE"
    )
    REJECTED_FRESHNESS_REFUTED = "REJECTED_FRESHNESS_REFUTED"


class HistoricalReplayCondition(str, Enum):
    """The three planted historical-replay worlds named by the motivating issue.

    ``UNCLASSIFIED`` is fail-closed: a receipt that cannot be checked, or that
    does not match one of the three worlds, is never forced into a planted label.
    """

    CURRENT_PIN = "CURRENT_PIN"
    STALE_PIN_SHADOW_ADOPTION = "STALE_PIN_SHADOW_ADOPTION"
    STALE_PIN_TREATED_AS_AUTHORITATIVE = "STALE_PIN_TREATED_AS_AUTHORITATIVE"
    UNCLASSIFIED = "UNCLASSIFIED"


#: Ordinal rank of the dependency claim each status licenses.  The ladder is
#: rank 0 = no adoption claim (fail-closed or defective), rank 1 = current main
#: was consulted in shadow mode only, rank 2 = the pinned subject itself is the
#: current or newly written subject, rank 3 = that subject is also test-bound.
#: The ranks exist only to detect an implicit upgrade of a declared status; they
#: are never used as a score or threshold.
_ADOPTION_CLAIM_RANK: Mapping[FreshnessExecutionStatus, int] = {
    FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE: 0,
    FreshnessExecutionStatus.CURRENT_MAIN_UNOBSERVED: 0,
    FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING: 0,
    FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE: 0,
    FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW: 1,
    FreshnessExecutionStatus.PIN_CURRENT: 2,
    FreshnessExecutionStatus.PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS: 2,
    FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED: 3,
}

#: Statuses that record an adoption *action* taken because of a pin/main delta.
#: Only these must name the framework feature set claimed operational, because
#: only these assert that specific current-main contracts were consulted.
#: ``PIN_CURRENT`` is excluded: no delta existed, so there is no delta-driven
#: consultation to evidence.
_ADOPTION_ACTION_STATUSES = frozenset(
    {
        FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW,
        FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED,
        FreshnessExecutionStatus.PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS,
    }
)


def canonical_json_bytes(value: object) -> bytes:
    """Return the UTF-8 RFC-8259-compatible representation used for hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def receipt_canonical_sha256(document: Mapping[str, Any]) -> str:
    """Hash a receipt document excluding its own content-hash field."""

    subject = dict(document)
    subject.pop("receipt_canonical_sha256", None)
    return canonical_json_sha256(subject)


def _is_utc_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.utcoffset() == timedelta(0)


@dataclass(frozen=True)
class InspectedSurface:
    """One framework contract/surface actually read during the episode.

    ``subject_sha`` is load-bearing: reading ``AGENTS.md`` at the stale pin is
    not reading it at current main, and only the latter can support a
    direct-current-main adoption claim.
    """

    path: str
    subject_sha: str
    blob_sha: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "subject_sha": self.subject_sha,
            "blob_sha": self.blob_sha,
        }


@dataclass(frozen=True)
class ApplicationTestBinding:
    """Evidence that the complete application suite ran against a framework subject."""

    framework_subject_sha: str
    application_subject_sha: str
    command: str
    run_reference: str
    complete_suite: bool
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_subject_sha": self.framework_subject_sha,
            "application_subject_sha": self.application_subject_sha,
            "command": self.command,
            "run_reference": self.run_reference,
            "complete_suite": self.complete_suite,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class FrameworkFreshnessReceipt:
    """Frozen episode-start record of the pin/current-main relation.

    ``declared_*`` fields are what the episode asserts.  Every one of them is
    re-derived from the observations by :func:`audit_framework_freshness`; the
    declaration is never trusted on its own.
    """

    application_repository: str
    application_subject_sha: str
    framework_repository: str
    framework_pin_sha: str
    task_episode_id: str
    public_trace_event_id: str
    declared_pin_relation: PinRelation
    declared_execution_status: FreshnessExecutionStatus
    claim_boundary: str
    observed_current_main_sha: str | None = None
    current_main_observed_at_utc: str | None = None
    pin_is_ancestor_of_current_main: bool | None = None
    current_main_is_ancestor_of_pin: bool | None = None
    commits_behind_current_main: int | None = None
    commits_ahead_of_current_main: int | None = None
    inspected_surfaces: Tuple[InspectedSurface, ...] = ()
    v3_feature_set_claimed_operational: Tuple[str, ...] = ()
    application_pin_updated_in_episode: bool = False
    application_test_binding: ApplicationTestBinding | None = None
    evidence_pointers: Tuple[str, ...] = ()
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "application_repository": self.application_repository,
            "application_subject_sha": self.application_subject_sha,
            "framework_repository": self.framework_repository,
            "framework_pin_sha": self.framework_pin_sha,
            "task_episode_id": self.task_episode_id,
            "public_trace_event_id": self.public_trace_event_id,
            "declared_pin_relation": self.declared_pin_relation.value,
            "declared_execution_status": self.declared_execution_status.value,
            "claim_boundary": self.claim_boundary,
            "observed_current_main_sha": self.observed_current_main_sha,
            "current_main_observed_at_utc": self.current_main_observed_at_utc,
            "pin_is_ancestor_of_current_main": self.pin_is_ancestor_of_current_main,
            "current_main_is_ancestor_of_pin": self.current_main_is_ancestor_of_pin,
            "commits_behind_current_main": self.commits_behind_current_main,
            "commits_ahead_of_current_main": self.commits_ahead_of_current_main,
            "inspected_surfaces": [item.to_dict() for item in self.inspected_surfaces],
            "v3_feature_set_claimed_operational": list(
                self.v3_feature_set_claimed_operational
            ),
            "application_pin_updated_in_episode": self.application_pin_updated_in_episode,
            "application_test_binding": (
                self.application_test_binding.to_dict()
                if self.application_test_binding is not None
                else None
            ),
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "performs_submodule_update": False,
            "grants_method_authority": False,
            "grants_application_mathematical_authority": False,
        }

    def with_content_hash(self) -> "FrameworkFreshnessReceipt":
        """Return a copy carrying its own canonical content hash."""

        from dataclasses import replace

        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )

    @property
    def watched_subjects(self) -> dict[str, str | None]:
        """The three values whose change triggers revalidation."""

        return {
            "application_subject_sha": self.application_subject_sha,
            "framework_pin_sha": self.framework_pin_sha,
            "framework_main_sha": self.observed_current_main_sha,
        }


@dataclass(frozen=True)
class FrameworkFreshnessReport:
    verdict: FreshnessVerdict
    effective_status: FreshnessExecutionStatus
    derived_pin_relation: PinRelation
    reasons: Tuple[str, ...]

    @property
    def permits_dependency_synchronization_claim(self) -> bool:
        """Only a verified, test-bound synchronization licenses that claim."""

        return (
            self.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
            and self.effective_status
            is FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED
        )

    @property
    def current_main_sha_bound(self) -> bool:
        """True once current framework main was observed enough to decide currency."""

        return self.derived_pin_relation is not PinRelation.UNOBSERVED

    @property
    def pin_mismatch_bound(self) -> bool:
        """True when a non-equal pin/main relation was derived from observations.

        Equality is also a bound relation (see :meth:`pin_relation_bound`); this
        property isolates the mismatch case the motivating issue requires to be
        explicit before completeness claims over a stale-pin episode.
        """

        return self.derived_pin_relation in (
            PinRelation.PIN_BEHIND_CURRENT_MAIN,
            PinRelation.PIN_AHEAD_OF_CURRENT_MAIN,
            PinRelation.DIVERGED,
        )

    @property
    def pin_relation_bound(self) -> bool:
        """True when the pin/current-main relation was derived, equal or not."""

        return self.derived_pin_relation is not PinRelation.UNOBSERVED

    @property
    def permits_completeness_claim(self) -> bool:
        """Completeness claims require a bound current-main SHA and pin relation.

        The adoption status may still record a defective process; the gate is
        about whether the pin/main observation was bound, not about whether the
        adoption was clean.  A refuted or unverifiable receipt never licenses a
        completeness claim.
        """

        return (
            self.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
            and self.current_main_sha_bound
            and self.pin_relation_bound
        )

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def performs_submodule_update(self) -> bool:
        return False


@dataclass(frozen=True)
class CompletenessFreshnessBindingReport:
    """Result of the freshness prerequisite check for a completeness claim."""

    verdict: CompletenessFreshnessBindingVerdict
    effective_status: FreshnessExecutionStatus
    derived_pin_relation: PinRelation
    observed_current_main_sha: str | None
    reasons: Tuple[str, ...]

    @property
    def permits_completeness_claim(self) -> bool:
        return self.verdict is CompletenessFreshnessBindingVerdict.BOUND_PROPOSAL_ONLY

    @property
    def grants_method_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class HistoricalReplayReport:
    condition: HistoricalReplayCondition
    freshness: FrameworkFreshnessReport
    reasons: Tuple[str, ...]

    @property
    def classified(self) -> bool:
        return self.condition is not HistoricalReplayCondition.UNCLASSIFIED


def derive_pin_relation(receipt: FrameworkFreshnessReceipt) -> PinRelation:
    """Derive the pin/current-main relation from observations only."""

    if not receipt.observed_current_main_sha or not receipt.current_main_observed_at_utc:
        return PinRelation.UNOBSERVED
    if receipt.framework_pin_sha == receipt.observed_current_main_sha:
        return PinRelation.EQUAL
    if (
        receipt.pin_is_ancestor_of_current_main is None
        or receipt.current_main_is_ancestor_of_pin is None
    ):
        return PinRelation.UNOBSERVED
    if receipt.pin_is_ancestor_of_current_main and receipt.current_main_is_ancestor_of_pin:
        # Mutual ancestry with unequal SHAs is not a reachable git state.
        return PinRelation.UNOBSERVED
    if receipt.pin_is_ancestor_of_current_main:
        return PinRelation.PIN_BEHIND_CURRENT_MAIN
    if receipt.current_main_is_ancestor_of_pin:
        return PinRelation.PIN_AHEAD_OF_CURRENT_MAIN
    return PinRelation.DIVERGED


def _structural_reasons(receipt: FrameworkFreshnessReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    for name, value in (
        ("application_subject_sha", receipt.application_subject_sha),
        ("framework_pin_sha", receipt.framework_pin_sha),
    ):
        if not _GIT_OID_RE.match(value or ""):
            reasons.append(f"{name}_invalid")
    if receipt.observed_current_main_sha is not None and not _GIT_OID_RE.match(
        receipt.observed_current_main_sha
    ):
        reasons.append("observed_current_main_sha_invalid")
    if receipt.current_main_observed_at_utc is not None and not _is_utc_timestamp(
        receipt.current_main_observed_at_utc
    ):
        reasons.append("current_main_observed_at_utc_not_utc")
    for name, value in (
        ("application_repository", receipt.application_repository),
        ("framework_repository", receipt.framework_repository),
        ("task_episode_id", receipt.task_episode_id),
        ("public_trace_event_id", receipt.public_trace_event_id),
        ("claim_boundary", receipt.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not receipt.evidence_pointers:
        reasons.append("evidence_pointers_missing")
    for surface in receipt.inspected_surfaces:
        if not surface.path.strip() or not _GIT_OID_RE.match(surface.subject_sha or ""):
            reasons.append("inspected_surface_binding_invalid")
            break
    return tuple(reasons)


def audit_framework_freshness(
    receipt: FrameworkFreshnessReceipt | None,
) -> FrameworkFreshnessReport:
    """Classify an application episode's framework-freshness posture.

    Fails closed: an unobserved current main, an unbound synchronization claim,
    or a malformed receipt each yield a distinct ``CANNOT_CHECK`` status rather
    than a default of ``PIN_CURRENT``.
    """

    if receipt is None:
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            PinRelation.UNOBSERVED,
            ("framework_freshness_receipt_missing",),
        )

    structural = _structural_reasons(receipt)
    if structural:
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            PinRelation.UNOBSERVED,
            structural,
        )

    if not receipt.receipt_canonical_sha256:
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            PinRelation.UNOBSERVED,
            ("receipt_canonical_sha256_missing",),
        )
    if not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            PinRelation.UNOBSERVED,
            ("receipt_canonical_sha256_malformed",),
        )
    if receipt.receipt_canonical_sha256 != receipt_canonical_sha256(receipt.to_dict()):
        return FrameworkFreshnessReport(
            FreshnessVerdict.REFUTED_CLAIM,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            PinRelation.UNOBSERVED,
            ("receipt_canonical_sha256_mismatch",),
        )

    relation = derive_pin_relation(receipt)
    # ``integrity`` holds contradictions between what the episode declared and
    # what was observed.  ``notes`` holds descriptive facts about the derived
    # status.  An honestly declared defective process is a valid receipt, so only
    # ``integrity`` may downgrade the verdict.
    integrity: list[str] = []
    notes: list[str] = []
    if receipt.declared_pin_relation is not relation:
        integrity.append("declared_pin_relation_contradicts_observation")

    if relation is PinRelation.UNOBSERVED:
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.CURRENT_MAIN_UNOBSERVED,
            relation,
            tuple(integrity)
            + (
                "current framework main was not observed; pin currency cannot be decided",
            ),
        )

    binding = receipt.application_test_binding
    if receipt.application_pin_updated_in_episode:
        if binding is None:
            return FrameworkFreshnessReport(
                FreshnessVerdict.CANNOT_CHECK,
                FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING,
                relation,
                tuple(integrity)
                + (
                    "pin synchronization is claimed without any application-test binding",
                ),
            )
        unbound: list[str] = []
        if binding.framework_subject_sha != receipt.framework_pin_sha:
            unbound.append("application_tests_bound_to_other_framework_subject")
        if binding.application_subject_sha != receipt.application_subject_sha:
            unbound.append("application_tests_bound_to_other_application_subject")
        if unbound:
            return FrameworkFreshnessReport(
                FreshnessVerdict.CANNOT_CHECK,
                FreshnessExecutionStatus.APPLICATION_TEST_BINDING_MISSING,
                relation,
                tuple(integrity) + tuple(unbound),
            )
        if binding.complete_suite and binding.passed:
            derived = FreshnessExecutionStatus.PIN_SYNCHRONIZED_AND_TESTED
        else:
            derived = (
                FreshnessExecutionStatus.PIN_SYNCHRONIZED_WITHOUT_APPLICATION_TESTS
            )
            notes.append("synchronized pin lacks a complete passing application suite")
    elif relation is PinRelation.EQUAL:
        derived = FreshnessExecutionStatus.PIN_CURRENT
    else:
        current_main_surfaces = tuple(
            surface
            for surface in receipt.inspected_surfaces
            if surface.subject_sha == receipt.observed_current_main_sha
        )
        if current_main_surfaces:
            derived = FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW
            notes.append(
                "current main was read directly in shadow mode; this is not a"
                " tested dependency synchronization"
            )
        else:
            derived = FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE
            notes.append(
                "pin is not current and no framework surface was read at current main"
            )

    if receipt.declared_execution_status is not derived:
        if (
            _ADOPTION_CLAIM_RANK[receipt.declared_execution_status]
            > _ADOPTION_CLAIM_RANK[derived]
        ):
            integrity.append("declared_status_upgrades_evidence")
        else:
            integrity.append("declared_status_contradicts_evidence")
        return FrameworkFreshnessReport(
            FreshnessVerdict.REFUTED_CLAIM,
            derived,
            relation,
            tuple(integrity) + tuple(notes),
        )

    if integrity:
        return FrameworkFreshnessReport(
            FreshnessVerdict.REFUTED_CLAIM,
            derived,
            relation,
            tuple(integrity) + tuple(notes),
        )

    if (
        derived in _ADOPTION_ACTION_STATUSES
        and not receipt.v3_feature_set_claimed_operational
    ):
        return FrameworkFreshnessReport(
            FreshnessVerdict.CANNOT_CHECK,
            FreshnessExecutionStatus.RECEIPT_UNVERIFIABLE,
            relation,
            tuple(notes)
            + ("adoption_recorded_without_naming_the_operational_feature_set",),
        )

    return FrameworkFreshnessReport(
        FreshnessVerdict.RECORDED_PROPOSAL_ONLY,
        derived,
        relation,
        tuple(notes)
        + (
            "pin/current-main relation and adoption status match the bound observations",
            "receipt is framework-process telemetry and mints no method or application authority",
        ),
    )


@dataclass(frozen=True)
class RevalidationReport:
    required: bool
    changed_subjects: Tuple[str, ...]
    reasons: Tuple[str, ...]


def revalidation_required(
    receipt: FrameworkFreshnessReceipt,
    *,
    observed_application_subject_sha: str | None,
    observed_framework_pin_sha: str | None,
    observed_framework_main_sha: str | None,
) -> RevalidationReport:
    """Fail closed on any watched subject that moved or could not be re-observed."""

    observed: dict[str, str | None] = {
        "application_subject_sha": observed_application_subject_sha,
        "framework_pin_sha": observed_framework_pin_sha,
        "framework_main_sha": observed_framework_main_sha,
    }
    changed: list[str] = []
    reasons: list[str] = []
    for name, recorded in receipt.watched_subjects.items():
        now = observed[name]
        if not now:
            changed.append(name)
            reasons.append(f"{name}_not_re_observed")
            continue
        if recorded is None:
            changed.append(name)
            reasons.append(f"{name}_was_never_bound_by_the_receipt")
            continue
        if now != recorded:
            changed.append(name)
            reasons.append(f"{name}_changed_since_receipt")
    if changed:
        return RevalidationReport(True, tuple(changed), tuple(reasons))
    return RevalidationReport(
        False, (), ("all watched subjects re-observed unchanged",)
    )


def audit_completeness_claim_freshness_binding(
    receipt: FrameworkFreshnessReceipt | None,
) -> CompletenessFreshnessBindingReport:
    """Gate completeness claims on a bound current-main SHA and pin relation.

    This is the fail-closed prerequisite the freshness receipt exists to enforce:
    a completeness or counting claim (and any later case-study attribution of
    which framework subject was actually consulted) is not licensed until the
    episode has bound observed current framework ``main`` and derived the
    pin/main relation — including an explicit mismatch when the pin is stale.

    The gate does not require a clean adoption status.  An honestly recorded
    ``STALE_PIN_TREATED_AS_AUTHORITATIVE`` still binds the mismatch; a missing or
    unobserved current main never does.  Naming a current-main SHA without the
    ancestry facts needed to derive equality-or-mismatch is
    ``REJECTED_UNBOUND_PIN_RELATION``, not a silent default to current.
    """

    freshness = audit_framework_freshness(receipt)
    observed_sha = None if receipt is None else receipt.observed_current_main_sha

    if receipt is None:
        return CompletenessFreshnessBindingReport(
            CompletenessFreshnessBindingVerdict.REJECTED_FRESHNESS_RECEIPT_UNVERIFIABLE,
            freshness.effective_status,
            freshness.derived_pin_relation,
            None,
            freshness.reasons
            + (
                "completeness claim rejected: freshness receipt could not be verified",
            ),
        )

    if not receipt.observed_current_main_sha or not receipt.current_main_observed_at_utc:
        return CompletenessFreshnessBindingReport(
            CompletenessFreshnessBindingVerdict.REJECTED_UNBOUND_CURRENT_MAIN,
            freshness.effective_status,
            freshness.derived_pin_relation,
            observed_sha,
            freshness.reasons
            + (
                "completeness claim rejected: current framework main SHA was not bound",
            ),
        )

    relation = derive_pin_relation(receipt)
    if relation is PinRelation.UNOBSERVED:
        return CompletenessFreshnessBindingReport(
            CompletenessFreshnessBindingVerdict.REJECTED_UNBOUND_PIN_RELATION,
            freshness.effective_status,
            relation,
            observed_sha,
            freshness.reasons
            + (
                "completeness claim rejected: pin/current-main relation was not bound",
            ),
        )

    if freshness.verdict is FreshnessVerdict.REFUTED_CLAIM:
        return CompletenessFreshnessBindingReport(
            CompletenessFreshnessBindingVerdict.REJECTED_FRESHNESS_REFUTED,
            freshness.effective_status,
            relation,
            observed_sha,
            freshness.reasons
            + (
                "completeness claim rejected: freshness receipt contradicts its observations",
            ),
        )

    if freshness.verdict is FreshnessVerdict.CANNOT_CHECK:
        return CompletenessFreshnessBindingReport(
            CompletenessFreshnessBindingVerdict.REJECTED_FRESHNESS_RECEIPT_UNVERIFIABLE,
            freshness.effective_status,
            relation,
            observed_sha,
            freshness.reasons
            + (
                "completeness claim rejected: freshness receipt could not be verified",
            ),
        )

    mismatch_note = (
        "pin/current-main mismatch is bound on the freshness receipt"
        if relation
        in (
            PinRelation.PIN_BEHIND_CURRENT_MAIN,
            PinRelation.PIN_AHEAD_OF_CURRENT_MAIN,
            PinRelation.DIVERGED,
        )
        else "pin equals observed current main; relation is bound with no mismatch"
    )
    return CompletenessFreshnessBindingReport(
        CompletenessFreshnessBindingVerdict.BOUND_PROPOSAL_ONLY,
        freshness.effective_status,
        relation,
        observed_sha,
        freshness.reasons
        + (
            mismatch_note,
            "completeness claim may proceed against this bound freshness receipt only",
            "binding mints no method or application authority",
        ),
    )


def classify_historical_replay(
    receipt: FrameworkFreshnessReceipt | None,
) -> HistoricalReplayReport:
    """Classify a receipt into one of the three planted historical-replay worlds.

    Fails closed to ``UNCLASSIFIED`` when current-main observation or
    application-test binding is missing in a way that prevents deciding among
    the planted conditions, or when the receipt is otherwise unverifiable.
    """

    freshness = audit_framework_freshness(receipt)
    status = freshness.effective_status

    if status is FreshnessExecutionStatus.PIN_CURRENT and (
        freshness.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    ):
        return HistoricalReplayReport(
            HistoricalReplayCondition.CURRENT_PIN,
            freshness,
            ("planted world: application pin equals observed current main",),
        )

    if status is FreshnessExecutionStatus.CURRENT_MAIN_READ_DIRECTLY_SHADOW and (
        freshness.verdict is FreshnessVerdict.RECORDED_PROPOSAL_ONLY
    ):
        return HistoricalReplayReport(
            HistoricalReplayCondition.STALE_PIN_SHADOW_ADOPTION,
            freshness,
            (
                "planted world: stale pin with direct current-main shadow adoption",
                "not a tested dependency synchronization",
            ),
        )

    if status is FreshnessExecutionStatus.STALE_PIN_TREATED_AS_AUTHORITATIVE:
        # Both the honestly recorded defect and the refuted false declaration map
        # onto the same planted world; the freshness verdict carries the rest.
        return HistoricalReplayReport(
            HistoricalReplayCondition.STALE_PIN_TREATED_AS_AUTHORITATIVE,
            freshness,
            (
                "planted world: stale pin treated as authoritative",
                "no framework surface was read at observed current main",
            ),
        )

    return HistoricalReplayReport(
        HistoricalReplayCondition.UNCLASSIFIED,
        freshness,
        freshness.reasons
        + (
            "receipt does not match a planted historical-replay condition",
        ),
    )
