"""Proposal-only artifact-contract coverage over a changed-artifact inventory.

A pull request can add authority- or chronology-bearing artifacts, pass a green
repository suite, and still have exercised none of those artifacts against their
canonical contract.  This module takes the inventory of what changed, resolves
each entry to the contract that owns its type, and returns an explicit result —
including an explicit *unowned* result when no contract owns the type at all.

The load-bearing design element is ``ArtifactLifecycle``.  Preservation is not
one rule: an immutable evidence artifact must stay byte-identical, an append-only
ledger may grow but never lose its prefix, and an intentionally evolving state
file may change freely provided its historical Git blob is still preserved.  A
naive preservation check that demanded byte-identity everywhere would freeze
legitimate state evolution, so the check is selected by lifecycle and the
declared lifecycle is itself verified against the owning contract.

The module performs no Git access, no file reads and no writes: the inventory and
every observation are supplied by an independent observer.  It grants no process
credit and mints no framework authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import Enum
from fnmatch import fnmatch
from typing import Any, Mapping, Tuple


RECEIPT_SCHEMA_VERSION = "artifact-contract-coverage-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class ArtifactLifecycle(str, Enum):
    """How an artifact is allowed to change after the commit that introduced it.

    ``IMMUTABLE_EVIDENCE``
        must remain byte-identical forever.
    ``APPEND_ONLY_LEDGER``
        may grow; its historical content must remain a prefix of the current
        content, so nothing already written is rewritten or dropped.
    ``EVOLVING_STATE``
        may change freely — a live problem DAG or obligation list.  Its
        historical Git blob must still be preserved so the past stays auditable.
    ``DERIVED_VIEW``
        may change, and must declare the source it is derived from, because a
        view that cannot name its source cannot be regenerated or checked.
    """

    IMMUTABLE_EVIDENCE = "IMMUTABLE_EVIDENCE"
    APPEND_ONLY_LEDGER = "APPEND_ONLY_LEDGER"
    EVOLVING_STATE = "EVOLVING_STATE"
    DERIVED_VIEW = "DERIVED_VIEW"


class ArtifactContractStatus(str, Enum):
    """Per-artifact outcome.

    The three "could not check" values are kept distinct from the defect values:
    ``UNOWNED_ARTIFACT_TYPE`` means no contract exists to check against,
    ``OBSERVATION_MISSING`` means the contract exists but the evidence to run it
    was not supplied, and ``MISDECLARED_AS_NON_ARTIFACT`` means a path inside an
    owned glob was declared out of scope.
    """

    CONTRACT_SATISFIED = "CONTRACT_SATISFIED"
    AUTHORIZED_EVIDENCE_REWRITE = "AUTHORIZED_EVIDENCE_REWRITE"
    UNOWNED_ARTIFACT_TYPE = "UNOWNED_ARTIFACT_TYPE"
    OBSERVATION_MISSING = "OBSERVATION_MISSING"
    MISDECLARED_AS_NON_ARTIFACT = "MISDECLARED_AS_NON_ARTIFACT"
    UNINVENTORIED_CHANGED_PATH = "UNINVENTORIED_CHANGED_PATH"
    INTERNAL_HASH_FALSE = "INTERNAL_HASH_FALSE"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    SCHEMA_VALID_RUNTIME_INVALID = "SCHEMA_VALID_RUNTIME_INVALID"
    CHRONOLOGY_IMPOSSIBLE = "CHRONOLOGY_IMPOSSIBLE"
    LIFECYCLE_MISCLASSIFIED = "LIFECYCLE_MISCLASSIFIED"
    UNAUTHORIZED_EVIDENCE_REWRITE = "UNAUTHORIZED_EVIDENCE_REWRITE"
    LEDGER_PREFIX_BROKEN = "LEDGER_PREFIX_BROKEN"
    HISTORICAL_BLOB_NOT_PRESERVED = "HISTORICAL_BLOB_NOT_PRESERVED"
    DERIVED_VIEW_SOURCE_UNDECLARED = "DERIVED_VIEW_SOURCE_UNDECLARED"


#: Statuses meaning "a contract exists and the artifact broke it".
_DEFECT_STATUSES = frozenset(
    {
        ArtifactContractStatus.INTERNAL_HASH_FALSE,
        ArtifactContractStatus.SCHEMA_INVALID,
        ArtifactContractStatus.SCHEMA_VALID_RUNTIME_INVALID,
        ArtifactContractStatus.CHRONOLOGY_IMPOSSIBLE,
        ArtifactContractStatus.LIFECYCLE_MISCLASSIFIED,
        ArtifactContractStatus.UNAUTHORIZED_EVIDENCE_REWRITE,
        ArtifactContractStatus.LEDGER_PREFIX_BROKEN,
        ArtifactContractStatus.HISTORICAL_BLOB_NOT_PRESERVED,
        ArtifactContractStatus.DERIVED_VIEW_SOURCE_UNDECLARED,
    }
)

#: Statuses meaning "the check could not be run", never "the check passed".
_UNCHECKED_STATUSES = frozenset(
    {
        ArtifactContractStatus.UNOWNED_ARTIFACT_TYPE,
        ArtifactContractStatus.OBSERVATION_MISSING,
        ArtifactContractStatus.MISDECLARED_AS_NON_ARTIFACT,
        ArtifactContractStatus.UNINVENTORIED_CHANGED_PATH,
    }
)

#: Statuses under which a contract was actually exercised and not broken.
_CLEARED_STATUSES = frozenset(
    {
        ArtifactContractStatus.CONTRACT_SATISFIED,
        ArtifactContractStatus.AUTHORIZED_EVIDENCE_REWRITE,
    }
)


class ContractCoverageVerdict(str, Enum):
    """Overall outcome for one changed-artifact inventory.

    ``NOT_ACTIVATED`` is a first-class result, not a pass: a prose-only change
    has no contract-bearing artifact, and a checker that reported anything else
    for it would fire on documentation edits and be switched off.
    """

    COVERAGE_SATISFIED_PROPOSAL_ONLY = "COVERAGE_SATISFIED_PROPOSAL_ONLY"
    NOT_ACTIVATED = "NOT_ACTIVATED"
    CONTRACT_VIOLATED = "CONTRACT_VIOLATED"
    COVERAGE_UNOWNED = "COVERAGE_UNOWNED"
    CANNOT_CHECK = "CANNOT_CHECK"


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


def _utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.utcoffset() != timedelta(0):
        return None
    return parsed


@dataclass(frozen=True)
class ArtifactContract:
    """The canonical owner of one artifact type."""

    artifact_type: str
    owner_module: str
    schema_id: str
    runtime_validator_id: str
    lifecycle: ArtifactLifecycle
    path_globs: Tuple[str, ...]

    def owns(self, path: str) -> bool:
        return any(fnmatch(path, pattern) for pattern in self.path_globs)


@dataclass(frozen=True)
class ChangedArtifact:
    """One changed path claimed to carry a contract-bearing artifact.

    Every field is an observation supplied by the caller.  ``None`` always means
    "not observed" and produces ``OBSERVATION_MISSING``, never a pass.
    """

    path: str
    artifact_type: str
    declared_lifecycle: ArtifactLifecycle
    historical_blob_sha: str
    historical_content_sha256: str
    historical_blob_preserved: bool | None = None
    current_content_sha256: str | None = None
    current_content_extends_historical: bool | None = None
    declared_internal_hash: str | None = None
    computed_internal_hash: str | None = None
    schema_valid: bool | None = None
    runtime_valid: bool | None = None
    artifact_event_at_utc: str | None = None
    introducing_commit_at_utc: str | None = None
    derived_from: str | None = None
    evidence_rewrite_authorization_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "artifact_type": self.artifact_type,
            "declared_lifecycle": self.declared_lifecycle.value,
            "historical_blob_sha": self.historical_blob_sha,
            "historical_content_sha256": self.historical_content_sha256,
            "historical_blob_preserved": self.historical_blob_preserved,
            "current_content_sha256": self.current_content_sha256,
            "current_content_extends_historical": self.current_content_extends_historical,
            "declared_internal_hash": self.declared_internal_hash,
            "computed_internal_hash": self.computed_internal_hash,
            "schema_valid": self.schema_valid,
            "runtime_valid": self.runtime_valid,
            "artifact_event_at_utc": self.artifact_event_at_utc,
            "introducing_commit_at_utc": self.introducing_commit_at_utc,
            "derived_from": self.derived_from,
            "evidence_rewrite_authorization_id": self.evidence_rewrite_authorization_id,
        }


@dataclass(frozen=True)
class DeclaredNonArtifact:
    """A changed path the author declares carries no contract-bearing artifact."""

    path: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "reason": self.reason}


@dataclass(frozen=True)
class ArtifactFinding:
    path: str
    artifact_type: str
    status: ArtifactContractStatus
    applied_lifecycle: ArtifactLifecycle | None
    reasons: Tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "artifact_type": self.artifact_type,
            "status": self.status.value,
            "applied_lifecycle": (
                self.applied_lifecycle.value if self.applied_lifecycle else None
            ),
            "reasons": list(self.reasons),
        }


def _check_preservation(
    artifact: ChangedArtifact, lifecycle: ArtifactLifecycle
) -> tuple[ArtifactContractStatus, Tuple[str, ...]] | None:
    """Run the preservation rule selected by lifecycle.

    Returns ``None`` when preservation holds.  The rules are deliberately
    different: applying the immutable-evidence rule to evolving state is exactly
    the regression this object exists to prevent.
    """

    if artifact.current_content_sha256 is None:
        return (
            ArtifactContractStatus.OBSERVATION_MISSING,
            ("current_content_not_observed",),
        )
    unchanged = artifact.current_content_sha256 == artifact.historical_content_sha256

    if lifecycle is ArtifactLifecycle.IMMUTABLE_EVIDENCE:
        if unchanged:
            return None
        if artifact.evidence_rewrite_authorization_id:
            # Authorized, but never silent: an evidence rewrite keeps its own
            # status so it cannot disappear inside a green verdict.
            return (
                ArtifactContractStatus.AUTHORIZED_EVIDENCE_REWRITE,
                (
                    "immutable evidence content changed under authorization "
                    f"{artifact.evidence_rewrite_authorization_id}",
                ),
            )
        return (
            ArtifactContractStatus.UNAUTHORIZED_EVIDENCE_REWRITE,
            ("immutable evidence content changed without an authorization id",),
        )

    if lifecycle is ArtifactLifecycle.APPEND_ONLY_LEDGER:
        if unchanged:
            return None
        if artifact.current_content_extends_historical is None:
            return (
                ArtifactContractStatus.OBSERVATION_MISSING,
                ("append_only_extension_not_observed",),
            )
        if not artifact.current_content_extends_historical:
            return (
                ArtifactContractStatus.LEDGER_PREFIX_BROKEN,
                ("append-only ledger no longer contains its historical prefix",),
            )
        return None

    # EVOLVING_STATE and DERIVED_VIEW may both change; what must survive is the
    # historical Git blob, so the past remains auditable after the change.
    if artifact.historical_blob_preserved is None:
        return (
            ArtifactContractStatus.OBSERVATION_MISSING,
            ("historical_blob_preservation_not_observed",),
        )
    if not artifact.historical_blob_preserved:
        return (
            ArtifactContractStatus.HISTORICAL_BLOB_NOT_PRESERVED,
            ("historical git blob is no longer reachable for a mutable artifact",),
        )
    if lifecycle is ArtifactLifecycle.DERIVED_VIEW and not (
        artifact.derived_from or ""
    ).strip():
        return (
            ArtifactContractStatus.DERIVED_VIEW_SOURCE_UNDECLARED,
            ("derived view does not declare the source it is derived from",),
        )
    return None


def assess_artifact(
    artifact: ChangedArtifact, contract: ArtifactContract | None
) -> ArtifactFinding:
    """Resolve one changed artifact against its owning contract."""

    if contract is None:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.UNOWNED_ARTIFACT_TYPE,
            None,
            ("no canonical contract owns this artifact type",),
        )

    if artifact.declared_lifecycle is not contract.lifecycle:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.LIFECYCLE_MISCLASSIFIED,
            contract.lifecycle,
            (
                f"declared_lifecycle={artifact.declared_lifecycle.value}",
                f"contract_lifecycle={contract.lifecycle.value}",
            ),
        )

    lifecycle = contract.lifecycle

    if artifact.declared_internal_hash is None or artifact.computed_internal_hash is None:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.OBSERVATION_MISSING,
            lifecycle,
            ("internal hash was not both declared and recomputed",),
        )
    if artifact.declared_internal_hash != artifact.computed_internal_hash:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.INTERNAL_HASH_FALSE,
            lifecycle,
            ("artifact asserts an internal hash it does not have",),
        )

    if artifact.schema_valid is None or artifact.runtime_valid is None:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.OBSERVATION_MISSING,
            lifecycle,
            ("schema and runtime validation were not both observed",),
        )
    if not artifact.schema_valid:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.SCHEMA_INVALID,
            lifecycle,
            (f"rejected by {contract.schema_id}",),
        )
    if not artifact.runtime_valid:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.SCHEMA_VALID_RUNTIME_INVALID,
            lifecycle,
            (
                f"accepted by {contract.schema_id} but rejected by "
                f"{contract.runtime_validator_id}",
            ),
        )

    if artifact.artifact_event_at_utc is None or artifact.introducing_commit_at_utc is None:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.OBSERVATION_MISSING,
            lifecycle,
            ("artifact event time or introducing commit time not observed",),
        )
    event_at = _utc(artifact.artifact_event_at_utc)
    commit_at = _utc(artifact.introducing_commit_at_utc)
    if event_at is None or commit_at is None:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.OBSERVATION_MISSING,
            lifecycle,
            ("chronology timestamps are not parseable UTC",),
        )
    if event_at > commit_at:
        return ArtifactFinding(
            artifact.path,
            artifact.artifact_type,
            ArtifactContractStatus.CHRONOLOGY_IMPOSSIBLE,
            lifecycle,
            ("artifact records an event later than the commit that introduced it",),
        )

    preservation = _check_preservation(artifact, lifecycle)
    if preservation is not None:
        status, reasons = preservation
        return ArtifactFinding(
            artifact.path, artifact.artifact_type, status, lifecycle, reasons
        )

    return ArtifactFinding(
        artifact.path,
        artifact.artifact_type,
        ArtifactContractStatus.CONTRACT_SATISFIED,
        lifecycle,
        (
            f"owned by {contract.owner_module}",
            f"{lifecycle.value} preservation rule applied",
        ),
    )


@dataclass(frozen=True)
class ArtifactContractCoverageReceipt:
    """Frozen record of a changed-artifact inventory and its contract results."""

    subject_repository: str
    subject_sha: str
    merge_base_sha: str
    changed_artifacts: Tuple[ChangedArtifact, ...]
    declared_non_artifacts: Tuple[DeclaredNonArtifact, ...]
    claim_boundary: str
    evidence_pointers: Tuple[str, ...] = ()
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "subject_repository": self.subject_repository,
            "subject_sha": self.subject_sha,
            "merge_base_sha": self.merge_base_sha,
            "changed_artifacts": [a.to_dict() for a in self.changed_artifacts],
            "declared_non_artifacts": [
                d.to_dict() for d in self.declared_non_artifacts
            ],
            "claim_boundary": self.claim_boundary,
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "grants_strict_process_credit": False,
            "grants_framework_authority": False,
            "is_independent_review": False,
        }

    def with_content_hash(self) -> "ArtifactContractCoverageReceipt":
        """Return a copy carrying its own canonical content hash."""

        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )


@dataclass(frozen=True)
class ContractCoverageReport:
    verdict: ContractCoverageVerdict
    findings: Tuple[ArtifactFinding, ...]
    reasons: Tuple[str, ...]

    @property
    def activated(self) -> bool:
        return self.verdict is not ContractCoverageVerdict.NOT_ACTIVATED

    @property
    def permits_strict_process_credit(self) -> bool:
        """Only a fully satisfied, activated inventory supports process credit."""

        return self.verdict is ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY

    @property
    def grants_framework_authority(self) -> bool:
        return False

    @property
    def is_independent_review(self) -> bool:
        return False


def _structural_reasons(receipt: ArtifactContractCoverageReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    for name, value in (
        ("subject_sha", receipt.subject_sha),
        ("merge_base_sha", receipt.merge_base_sha),
    ):
        if not _GIT_OID_RE.match(value or ""):
            reasons.append(f"{name}_invalid")
    for name, value in (
        ("subject_repository", receipt.subject_repository),
        ("claim_boundary", receipt.claim_boundary),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    paths = [a.path for a in receipt.changed_artifacts] + [
        d.path for d in receipt.declared_non_artifacts
    ]
    if len(set(paths)) != len(paths):
        reasons.append("duplicate_changed_path")
    for artifact in receipt.changed_artifacts:
        if not _GIT_OID_RE.match(artifact.historical_blob_sha or ""):
            reasons.append(f"historical_blob_sha_invalid:{artifact.path}")
        if not _SHA256_RE.match(artifact.historical_content_sha256 or ""):
            reasons.append(f"historical_content_sha256_invalid:{artifact.path}")
    for declared in receipt.declared_non_artifacts:
        if not declared.reason.strip():
            reasons.append(f"non_artifact_declared_without_reason:{declared.path}")
    if not receipt.receipt_canonical_sha256:
        reasons.append("receipt_canonical_sha256_missing")
    elif not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        reasons.append("receipt_canonical_sha256_malformed")
    return tuple(reasons)


def audit_artifact_contract_coverage(
    receipt: ArtifactContractCoverageReceipt | None,
    *,
    contracts: Tuple[ArtifactContract, ...],
    changed_paths: Tuple[str, ...],
) -> ContractCoverageReport:
    """Resolve every changed artifact against the contract registry.

    ``changed_paths`` is the observed diff, supplied independently of the
    receipt.  Every path in it must appear in exactly one of the receipt's two
    lists; a diff path in neither is ``UNINVENTORIED_CHANGED_PATH`` and fails
    closed.  Without that binding the receipt would only ever be checked against
    itself, and a change that added eleven artifacts while inventorying two
    would pass — which is the motivating failure this object exists to catch.

    A prose-only change activates nothing and returns ``NOT_ACTIVATED``.  A path
    declared as a non-artifact while sitting inside an owned glob does not get
    that exemption: it is reported as ``MISDECLARED_AS_NON_ARTIFACT`` so the
    declaration cannot be used to route an artifact around its contract.
    """

    if receipt is None:
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK,
            (),
            ("artifact_contract_coverage_receipt_missing",),
        )

    structural = _structural_reasons(receipt)
    if structural:
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK, (), structural
        )
    if receipt.receipt_canonical_sha256 != receipt_canonical_sha256(receipt.to_dict()):
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK,
            (),
            ("receipt_canonical_sha256_mismatch",),
        )

    inventoried = {a.path for a in receipt.changed_artifacts} | {
        d.path for d in receipt.declared_non_artifacts
    }
    observed = set(changed_paths)
    if inventoried - observed:
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK,
            (),
            tuple(
                f"inventoried_path_absent_from_changed_paths:{path}"
                for path in sorted(inventoried - observed)
            ),
        )

    by_type = {contract.artifact_type: contract for contract in contracts}
    findings = [
        assess_artifact(artifact, by_type.get(artifact.artifact_type))
        for artifact in receipt.changed_artifacts
    ]

    for path in sorted(observed - inventoried):
        owner = next((c for c in contracts if c.owns(path)), None)
        findings.append(
            ArtifactFinding(
                path,
                owner.artifact_type if owner else "",
                ArtifactContractStatus.UNINVENTORIED_CHANGED_PATH,
                owner.lifecycle if owner else None,
                ("path changed in the diff but absent from the inventory",),
            )
        )

    for declared in receipt.declared_non_artifacts:
        owner = next(
            (contract for contract in contracts if contract.owns(declared.path)), None
        )
        if owner is not None:
            findings.append(
                ArtifactFinding(
                    declared.path,
                    owner.artifact_type,
                    ArtifactContractStatus.MISDECLARED_AS_NON_ARTIFACT,
                    owner.lifecycle,
                    (
                        "path is inside an owned glob but was declared a non-artifact",
                        f"owner={owner.owner_module}",
                    ),
                )
            )

    findings_t = tuple(findings)
    if not findings_t:
        return ContractCoverageReport(
            ContractCoverageVerdict.NOT_ACTIVATED,
            (),
            (
                "no contract-bearing artifact changed",
                "prose-only and other non-artifact changes do not activate this check",
            ),
        )

    defects = tuple(f for f in findings_t if f.status in _DEFECT_STATUSES)
    if defects:
        return ContractCoverageReport(
            ContractCoverageVerdict.CONTRACT_VIOLATED,
            findings_t,
            tuple(f"{f.status.value}:{f.path}" for f in defects),
        )
    unowned = tuple(
        f
        for f in findings_t
        if f.status is ArtifactContractStatus.UNOWNED_ARTIFACT_TYPE
    )
    if unowned:
        return ContractCoverageReport(
            ContractCoverageVerdict.COVERAGE_UNOWNED,
            findings_t,
            tuple(f"unowned_artifact_type:{f.artifact_type}:{f.path}" for f in unowned),
        )
    unchecked = tuple(f for f in findings_t if f.status in _UNCHECKED_STATUSES)
    if unchecked:
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK,
            findings_t,
            tuple(f"{f.status.value}:{f.path}" for f in unchecked),
        )
    stray = tuple(f for f in findings_t if f.status not in _CLEARED_STATUSES)
    if stray:  # pragma: no cover - every status is routed above
        return ContractCoverageReport(
            ContractCoverageVerdict.CANNOT_CHECK,
            findings_t,
            tuple(f"unrouted_status:{f.status.value}:{f.path}" for f in stray),
        )
    rewrites = tuple(
        f for f in findings_t if f.status is ArtifactContractStatus.AUTHORIZED_EVIDENCE_REWRITE
    )
    return ContractCoverageReport(
        ContractCoverageVerdict.COVERAGE_SATISFIED_PROPOSAL_ONLY,
        findings_t,
        tuple(
            f"authorized_evidence_rewrite:{f.path}" for f in rewrites
        )
        + (
            "every changed path is inventoried and resolved to a canonical contract",
            "lifecycle-selected preservation rules applied; no rule was applied to a"
            " lifecycle it does not govern",
            "coverage receipt grants no strict-process credit and no framework authority",
        ),
    )
