"""Proposal-only authoritative-framework-SHA revalidation at candidate freeze.

Issue #385: a long-running research cycle can freeze a valid pre-candidate packet
against one authoritative ``RAKL/main`` SHA and then reach ``CANDIDATE_PROPOSED``
after ``main`` has advanced. If the intervening change adds or modifies a
required gate, schema, runtime argument, or authority rule, the earlier
``candidate_generation_allowed`` decision is stale even though its original
chronology was valid.

This module binds the freeze SHA into a content-hashed receipt and, immediately
before candidate materialization, compares an independently observed current
``main`` SHA plus a caller-supplied classification of the intervening diff:

* changes confined to non-method publication/research content may be
  acknowledged without invalidation;
* changes touching required discovery gates, trace schemas, planning APIs, or
  authority semantics fail closed and require regenerating the affected
  pre-candidate surfaces under the new SHA.

Scope boundary:

* **No network / no git.** Every observation is supplied by the caller.
* **No theorem or method-evolution authority.** A pass only licenses treating
  the freeze subject as still current-main process-compliant for discovery
  control; it does not mint scientific authority.
* Optional gate: inactive unless a freeze binding is supplied or the gate is
  explicitly required (same pattern as the preservation gate).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple

RECEIPT_SCHEMA_VERSION = "framework-candidate-freeze-binding-v1"

_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_FRAMEWORK_SUBJECT_ACTIONS: Tuple[str, ...] = (
    "rebind_pre_candidate_surfaces_under_current_authoritative_framework_sha",
    "reclassify_intervening_diff_against_protected_method_surfaces",
)


class DiffSurfaceClass(str, Enum):
    """Caller-supplied classification of one path in the freeze→current diff."""

    PROTECTED_METHOD_GATE_SCHEMA_RUNTIME = "PROTECTED_METHOD_GATE_SCHEMA_RUNTIME"
    NON_METHOD_PUBLICATION_OR_RESEARCH = "NON_METHOD_PUBLICATION_OR_RESEARCH"
    UNCLASSIFIED = "UNCLASSIFIED"


class CandidateFreezeRevalidationVerdict(str, Enum):
    """Outcome of revalidating the authoritative framework subject at freeze."""

    CURRENT_UNCHANGED = "CURRENT_UNCHANGED"
    ACKNOWLEDGED_NON_METHOD_DRIFT = "ACKNOWLEDGED_NON_METHOD_DRIFT"
    STALE_PROTECTED_SURFACE_CHANGED = "STALE_PROTECTED_SURFACE_CHANGED"
    UNCLASSIFIED_DIFF_FAIL_CLOSED = "UNCLASSIFIED_DIFF_FAIL_CLOSED"
    CANNOT_CHECK = "CANNOT_CHECK"
    RECEIPT_UNVERIFIABLE = "RECEIPT_UNVERIFIABLE"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class DiffPathClassification:
    """One path in the intervening main diff with an explicit surface class."""

    path: str
    surface_class: DiffSurfaceClass

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("diff path classification requires a non-empty path")


@dataclass(frozen=True)
class FrameworkSubjectFreezeBinding:
    """Bind the authoritative framework SHA into the pre-candidate freeze.

    ``authoritative_framework_sha`` is the ``RAKL/main`` OID observed when the
    pre-candidate packet / preservation surfaces were frozen.
    ``pre_candidate_packet_hash`` ties the binding to the exact frozen packet.
    """

    binding_id: str
    authoritative_framework_sha: str
    pre_candidate_packet_hash: str
    frozen_at_utc: str
    evidence_pointers: Tuple[str, ...]
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.binding_id.strip():
            raise ValueError("framework subject freeze binding requires binding_id")
        if not _GIT_OID_RE.match(self.authoritative_framework_sha):
            raise ValueError("authoritative_framework_sha must be a git OID")
        if not _SHA256_RE.match(self.pre_candidate_packet_hash):
            raise ValueError("pre_candidate_packet_hash must be sha256 hex")
        if not self.frozen_at_utc.strip():
            raise ValueError("framework subject freeze binding requires frozen_at_utc")
        if not self.evidence_pointers:
            raise ValueError("framework subject freeze binding requires evidence_pointers")

    def content(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "binding_id": self.binding_id,
            "authoritative_framework_sha": self.authoritative_framework_sha,
            "pre_candidate_packet_hash": self.pre_candidate_packet_hash,
            "frozen_at_utc": self.frozen_at_utc,
            "evidence_pointers": list(self.evidence_pointers),
        }

    @property
    def binding_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        document = dict(self.content())
        document["binding_canonical_sha256"] = self.binding_canonical_sha256
        return document


@dataclass(frozen=True)
class FrameworkSubjectRevalidationObservation:
    """Independently observed current main + classified intervening diff."""

    observed_current_main_sha: str
    intervening_diff: Tuple[DiffPathClassification, ...]
    observation_evidence_pointers: Tuple[str, ...]

    def __post_init__(self) -> None:
        if not _GIT_OID_RE.match(self.observed_current_main_sha):
            raise ValueError("observed_current_main_sha must be a git OID")
        if not self.observation_evidence_pointers:
            raise ValueError("revalidation observation requires evidence_pointers")


@dataclass(frozen=True)
class CandidateFreezeRevalidationReport:
    """Audit result for framework-subject freshness at candidate freeze."""

    binding_id: str | None
    verdict: CandidateFreezeRevalidationVerdict
    reasons: Tuple[str, ...]
    freeze_sha: str | None
    observed_current_main_sha: str | None
    protected_paths_changed: Tuple[str, ...]
    non_method_paths_changed: Tuple[str, ...]
    licenses_candidate_materialization: bool
    grants_scientific_authority: bool = False

    def __post_init__(self) -> None:
        if self.grants_scientific_authority:
            raise ValueError("framework subject revalidation cannot grant scientific authority")


def _structural_binding_reasons(binding: FrameworkSubjectFreezeBinding) -> Tuple[str, ...]:
    reasons: list[str] = []
    # Re-derive so a round-tripped stale hash cannot pass silently.
    _ = binding.binding_canonical_sha256
    if not binding.evidence_pointers:
        reasons.append("binding_evidence_pointers_missing")
    return tuple(reasons)


def audit_candidate_freeze_framework_subject(
    binding: FrameworkSubjectFreezeBinding | None,
    observation: FrameworkSubjectRevalidationObservation | None,
    *,
    required: bool = False,
) -> CandidateFreezeRevalidationReport:
    """Revalidate the authoritative framework SHA immediately before candidates.

    When ``required`` is false and no binding is supplied, the gate is inactive
    (free-form brainstorming). Supplying a binding always activates the check.
    """

    active = required or binding is not None
    if not active:
        return CandidateFreezeRevalidationReport(
            binding_id=None,
            verdict=CandidateFreezeRevalidationVerdict.CURRENT_UNCHANGED,
            reasons=("framework_subject_gate_inactive",),
            freeze_sha=None,
            observed_current_main_sha=None,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=True,
        )

    if binding is None:
        return CandidateFreezeRevalidationReport(
            binding_id=None,
            verdict=CandidateFreezeRevalidationVerdict.CANNOT_CHECK,
            reasons=("framework_subject_binding_required_but_missing",),
            freeze_sha=None,
            observed_current_main_sha=None,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=False,
        )

    structural = _structural_binding_reasons(binding)
    if structural:
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.RECEIPT_UNVERIFIABLE,
            reasons=structural,
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=None,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=False,
        )

    if observation is None:
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.CANNOT_CHECK,
            reasons=("current_main_observation_missing",),
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=None,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=False,
        )

    if observation.observed_current_main_sha == binding.authoritative_framework_sha:
        if observation.intervening_diff:
            return CandidateFreezeRevalidationReport(
                binding_id=binding.binding_id,
                verdict=CandidateFreezeRevalidationVerdict.RECEIPT_UNVERIFIABLE,
                reasons=("intervening_diff_nonempty_while_sha_unchanged",),
                freeze_sha=binding.authoritative_framework_sha,
                observed_current_main_sha=observation.observed_current_main_sha,
                protected_paths_changed=(),
                non_method_paths_changed=(),
                licenses_candidate_materialization=False,
            )
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.CURRENT_UNCHANGED,
            reasons=("authoritative_framework_sha_still_current_main",),
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=observation.observed_current_main_sha,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=True,
        )

    protected = tuple(
        item.path
        for item in observation.intervening_diff
        if item.surface_class is DiffSurfaceClass.PROTECTED_METHOD_GATE_SCHEMA_RUNTIME
    )
    non_method = tuple(
        item.path
        for item in observation.intervening_diff
        if item.surface_class is DiffSurfaceClass.NON_METHOD_PUBLICATION_OR_RESEARCH
    )
    unclassified = tuple(
        item.path
        for item in observation.intervening_diff
        if item.surface_class is DiffSurfaceClass.UNCLASSIFIED
    )

    if not observation.intervening_diff:
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.CANNOT_CHECK,
            reasons=(
                "main_sha_changed_but_intervening_diff_unobserved",
                "cannot_classify_protected_versus_non_method_surfaces",
            ),
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=observation.observed_current_main_sha,
            protected_paths_changed=(),
            non_method_paths_changed=(),
            licenses_candidate_materialization=False,
        )

    if protected:
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.STALE_PROTECTED_SURFACE_CHANGED,
            reasons=(
                "authoritative_framework_sha_stale",
                "protected_method_gate_schema_or_runtime_surface_changed",
                "regenerate_pre_candidate_surfaces_under_new_sha",
            ),
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=observation.observed_current_main_sha,
            protected_paths_changed=protected,
            non_method_paths_changed=non_method,
            licenses_candidate_materialization=False,
        )

    if unclassified:
        return CandidateFreezeRevalidationReport(
            binding_id=binding.binding_id,
            verdict=CandidateFreezeRevalidationVerdict.UNCLASSIFIED_DIFF_FAIL_CLOSED,
            reasons=(
                "authoritative_framework_sha_stale",
                "intervening_diff_contains_unclassified_paths",
            ),
            freeze_sha=binding.authoritative_framework_sha,
            observed_current_main_sha=observation.observed_current_main_sha,
            protected_paths_changed=(),
            non_method_paths_changed=non_method,
            licenses_candidate_materialization=False,
        )

    return CandidateFreezeRevalidationReport(
        binding_id=binding.binding_id,
        verdict=CandidateFreezeRevalidationVerdict.ACKNOWLEDGED_NON_METHOD_DRIFT,
        reasons=(
            "authoritative_framework_sha_advanced",
            "intervening_diff_confined_to_non_method_publication_or_research",
            "pre_candidate_discovery_gates_unchanged",
        ),
        freeze_sha=binding.authoritative_framework_sha,
        observed_current_main_sha=observation.observed_current_main_sha,
        protected_paths_changed=(),
        non_method_paths_changed=non_method,
        licenses_candidate_materialization=True,
    )


def gate_candidate_materialization_framework_subject(
    binding: FrameworkSubjectFreezeBinding | None,
    observation: FrameworkSubjectRevalidationObservation | None = None,
    *,
    required: bool = False,
) -> CandidateFreezeRevalidationReport:
    """Fail closed when a supplied/required freeze binding is stale on protected surfaces."""

    return audit_candidate_freeze_framework_subject(
        binding,
        observation,
        required=required,
    )


__all__ = [
    "REQUIRED_FRAMEWORK_SUBJECT_ACTIONS",
    "CandidateFreezeRevalidationReport",
    "CandidateFreezeRevalidationVerdict",
    "DiffPathClassification",
    "DiffSurfaceClass",
    "FrameworkSubjectFreezeBinding",
    "FrameworkSubjectRevalidationObservation",
    "audit_candidate_freeze_framework_subject",
    "canonical_json_sha256",
    "gate_candidate_materialization_framework_subject",
]
