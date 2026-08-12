"""Proposal-only quantifier / scope compatibility witness (issue #459).

Local-to-global gluing can preserve local correctness while silently changing the
global object when quantifier, norm, time, or limit scopes are substituted across
mismatched coordinates — for example pointwise vs global bounds, local-in-time vs
supremum norms, finite-sequence vs limit conclusions, or norm bounds vs uniform
quantifier statements.

This module freezes a narrow typed witness for that surface. It is intended to
affect **routing / gluing authority claims only**. It does not mint theorem,
proof, novelty, or identification authority.

Scope, stated as narrowly as the artifact supports:

* **Not wired into** ``glue_local_sections``, ``math_context``, or protected
  promotion paths. Automatic enforcement at those surfaces remains a separate
  Class-B framework-evolution change under the upgrade protocol.
* **Separate from** :mod:`rakl.summation_compatibility`. Summation/limit-order
  compatibility and quantifier-scope compatibility are distinct gluing surfaces.
* **Fail-closed.** Any ``UNKNOWN`` load-bearing field, or a ``MISALIGNED`` axis
  without an explicit permitted substitution witness, forces
  ``FAIL_CLOSED_UNKNOWN`` or ``INCOMPATIBLE`` and rejects gluing-authority
  consumers.
* **No theorem authority.** ``authority_claim`` is fixed to
  ``ROUTING_GLUING_ONLY_NOT_THEOREM``.

Development tests in ``tests/test_quantifier_compatibility.py`` use fresh gluing
worlds inspired by historical quantifier failure families. They are not
confirmatory evidence that the witness prevents real application failures.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

WITNESS_SCHEMA_VERSION = "quantifier-compatibility-witness-v1"
AUTHORITY_CLAIM = "ROUTING_GLUING_ONLY_NOT_THEOREM"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")

_SCOPE_AXIS_FIELDS = (
    "point_global_scope",
    "time_supremum_scope",
    "sequence_limit_scope",
    "norm_quantifier_scope",
)

_SUBSTITUTION_FIELDS = (
    "point_global_substitution_permitted",
    "time_supremum_substitution_permitted",
    "sequence_limit_substitution_permitted",
    "norm_quantifier_substitution_permitted",
)


class ScopeAlignment(str, Enum):
    """Whether a scope axis is aligned across the glued sections."""

    ALIGNED = "ALIGNED"
    MISALIGNED = "MISALIGNED"
    UNKNOWN = "UNKNOWN"


class PermissionStatus(str, Enum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class GluingStatus(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    CONDITIONAL = "CONDITIONAL"
    FAIL_CLOSED_UNKNOWN = "FAIL_CLOSED_UNKNOWN"


class GluingConsumer(str, Enum):
    """Consumers that may treat the witness as gluing/routing authority only."""

    ROUTING = "ROUTING"
    LOCAL_TO_GLOBAL_GLUING = "LOCAL_TO_GLOBAL_GLUING"
    CONTRADICTION_DIAGNOSIS = "CONTRADICTION_DIAGNOSIS"
    REVIEW = "REVIEW"
    THEOREM_AUTHORITY = "THEOREM_AUTHORITY"


class WitnessAuditVerdict(str, Enum):
    GLUING_AUTHORITY_OK = "GLUING_AUTHORITY_OK"
    FAIL_CLOSED_UNKNOWN = "FAIL_CLOSED_UNKNOWN"
    INCOMPATIBLE = "INCOMPATIBLE"
    CONDITIONAL_REQUIRES_CONDITION = "CONDITIONAL_REQUIRES_CONDITION"
    THEOREM_AUTHORITY_REJECTED = "THEOREM_AUTHORITY_REJECTED"
    WITNESS_UNVERIFIABLE = "WITNESS_UNVERIFIABLE"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _unknown_fields_from_values(
    *,
    point_global_scope: ScopeAlignment,
    time_supremum_scope: ScopeAlignment,
    sequence_limit_scope: ScopeAlignment,
    norm_quantifier_scope: ScopeAlignment,
    point_global_substitution_permitted: PermissionStatus,
    time_supremum_substitution_permitted: PermissionStatus,
    sequence_limit_substitution_permitted: PermissionStatus,
    norm_quantifier_substitution_permitted: PermissionStatus,
    required_scope_witness: str,
) -> Tuple[str, ...]:
    unknown: list[str] = []
    for name, value in zip(
        _SCOPE_AXIS_FIELDS,
        (
            point_global_scope,
            time_supremum_scope,
            sequence_limit_scope,
            norm_quantifier_scope,
        ),
    ):
        if value is ScopeAlignment.UNKNOWN:
            unknown.append(name)
    for name, value in zip(
        _SUBSTITUTION_FIELDS,
        (
            point_global_substitution_permitted,
            time_supremum_substitution_permitted,
            sequence_limit_substitution_permitted,
            norm_quantifier_substitution_permitted,
        ),
    ):
        if value is PermissionStatus.UNKNOWN:
            unknown.append(name)
    if required_scope_witness.strip().upper() == "UNKNOWN":
        unknown.append("required_scope_witness")
    return tuple(unknown)


def _misaligned_axes_without_substitution(
    *,
    point_global_scope: ScopeAlignment,
    time_supremum_scope: ScopeAlignment,
    sequence_limit_scope: ScopeAlignment,
    norm_quantifier_scope: ScopeAlignment,
    point_global_substitution_permitted: PermissionStatus,
    time_supremum_substitution_permitted: PermissionStatus,
    sequence_limit_substitution_permitted: PermissionStatus,
    norm_quantifier_substitution_permitted: PermissionStatus,
) -> Tuple[str, ...]:
    mismatches: list[str] = []
    pairs = zip(
        _SCOPE_AXIS_FIELDS,
        (
            point_global_scope,
            time_supremum_scope,
            sequence_limit_scope,
            norm_quantifier_scope,
        ),
        _SUBSTITUTION_FIELDS,
        (
            point_global_substitution_permitted,
            time_supremum_substitution_permitted,
            sequence_limit_substitution_permitted,
            norm_quantifier_substitution_permitted,
        ),
    )
    for scope_name, scope_value, substitution_name, substitution_value in pairs:
        if scope_value is ScopeAlignment.MISALIGNED and substitution_value is not PermissionStatus.YES:
            mismatches.append(f"{scope_name}:{substitution_name}")
    return tuple(mismatches)


@dataclass(frozen=True)
class QuantifierCompatibilityWitness:
    """Typed quantifier / scope compatibility record for one atom.

    Construction fail-closes: if any load-bearing field is ``UNKNOWN``, or a
    scope axis is ``MISALIGNED`` without substitution permission ``YES``,
    ``gluing_status`` must be ``FAIL_CLOSED_UNKNOWN`` or ``INCOMPATIBLE``.
    """

    witness_id: str
    atom_id: str
    source_claim_scope: str
    point_global_scope: ScopeAlignment
    time_supremum_scope: ScopeAlignment
    sequence_limit_scope: ScopeAlignment
    norm_quantifier_scope: ScopeAlignment
    point_global_substitution_permitted: PermissionStatus
    time_supremum_substitution_permitted: PermissionStatus
    sequence_limit_substitution_permitted: PermissionStatus
    norm_quantifier_substitution_permitted: PermissionStatus
    required_scope_witness: str
    gluing_status: GluingStatus
    evidence_pointers: Tuple[str, ...]
    recorded_at_utc: str
    condition: Optional[str] = None
    schema_version: str = WITNESS_SCHEMA_VERSION
    authority_claim: str = AUTHORITY_CLAIM

    def __post_init__(self) -> None:
        if not self.witness_id:
            raise ValueError("quantifier witness requires witness_id")
        if not self.atom_id:
            raise ValueError("quantifier witness requires atom_id")
        if not self.source_claim_scope.strip():
            raise ValueError("source_claim_scope is required")
        if not self.required_scope_witness.strip():
            raise ValueError("required_scope_witness is required")
        if not self.evidence_pointers:
            raise ValueError("evidence_pointers are required")
        if not _ISO_UTC_RE.match(self.recorded_at_utc):
            raise ValueError("recorded_at_utc must be ISO-8601 UTC ending in 'Z'")
        if self.authority_claim != AUTHORITY_CLAIM:
            raise ValueError("authority_claim must remain ROUTING_GLUING_ONLY_NOT_THEOREM")
        if self.gluing_status is GluingStatus.CONDITIONAL and not self.condition:
            raise ValueError("CONDITIONAL gluing_status requires an explicit condition")

        unknowns = self.unknown_fields
        mismatches = self.misaligned_axes_without_substitution
        if unknowns and self.gluing_status is not GluingStatus.FAIL_CLOSED_UNKNOWN:
            raise ValueError(
                "unknown load-bearing fields require gluing_status=FAIL_CLOSED_UNKNOWN: "
                + ",".join(unknowns)
            )
        if not unknowns and self.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN:
            raise ValueError(
                "FAIL_CLOSED_UNKNOWN requires at least one unknown load-bearing field"
            )
        if mismatches and self.gluing_status is GluingStatus.COMPATIBLE:
            raise ValueError(
                "misaligned scope axes without substitution witness cannot be COMPATIBLE: "
                + ",".join(mismatches)
            )
        if mismatches and self.gluing_status not in {
            GluingStatus.INCOMPATIBLE,
            GluingStatus.CONDITIONAL,
            GluingStatus.FAIL_CLOSED_UNKNOWN,
        }:
            raise ValueError(
                "misaligned scope axes require INCOMPATIBLE, CONDITIONAL, or FAIL_CLOSED_UNKNOWN: "
                + ",".join(mismatches)
            )

    @property
    def unknown_fields(self) -> Tuple[str, ...]:
        return _unknown_fields_from_values(
            point_global_scope=self.point_global_scope,
            time_supremum_scope=self.time_supremum_scope,
            sequence_limit_scope=self.sequence_limit_scope,
            norm_quantifier_scope=self.norm_quantifier_scope,
            point_global_substitution_permitted=self.point_global_substitution_permitted,
            time_supremum_substitution_permitted=self.time_supremum_substitution_permitted,
            sequence_limit_substitution_permitted=self.sequence_limit_substitution_permitted,
            norm_quantifier_substitution_permitted=self.norm_quantifier_substitution_permitted,
            required_scope_witness=self.required_scope_witness,
        )

    @property
    def misaligned_axes_without_substitution(self) -> Tuple[str, ...]:
        return _misaligned_axes_without_substitution(
            point_global_scope=self.point_global_scope,
            time_supremum_scope=self.time_supremum_scope,
            sequence_limit_scope=self.sequence_limit_scope,
            norm_quantifier_scope=self.norm_quantifier_scope,
            point_global_substitution_permitted=self.point_global_substitution_permitted,
            time_supremum_substitution_permitted=self.time_supremum_substitution_permitted,
            sequence_limit_substitution_permitted=self.sequence_limit_substitution_permitted,
            norm_quantifier_substitution_permitted=self.norm_quantifier_substitution_permitted,
        )

    def content(self) -> Mapping[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "witness_id": self.witness_id,
            "atom_id": self.atom_id,
            "source_claim_scope": self.source_claim_scope,
            "point_global_scope": self.point_global_scope.value,
            "time_supremum_scope": self.time_supremum_scope.value,
            "sequence_limit_scope": self.sequence_limit_scope.value,
            "norm_quantifier_scope": self.norm_quantifier_scope.value,
            "point_global_substitution_permitted": self.point_global_substitution_permitted.value,
            "time_supremum_substitution_permitted": self.time_supremum_substitution_permitted.value,
            "sequence_limit_substitution_permitted": self.sequence_limit_substitution_permitted.value,
            "norm_quantifier_substitution_permitted": self.norm_quantifier_substitution_permitted.value,
            "required_scope_witness": self.required_scope_witness,
            "gluing_status": self.gluing_status.value,
            "authority_claim": self.authority_claim,
            "evidence_pointers": list(self.evidence_pointers),
            "recorded_at_utc": self.recorded_at_utc,
            "unknown_fields": list(self.unknown_fields),
            "misaligned_axes_without_substitution": list(self.misaligned_axes_without_substitution),
        }
        if self.condition is not None:
            document["condition"] = self.condition
        return document

    @property
    def witness_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        payload = dict(self.content())
        payload["witness_canonical_sha256"] = self.witness_canonical_sha256
        return payload


@dataclass(frozen=True)
class QuantifierCompatibilityAudit:
    witness_id: str | None
    atom_id: str
    verdict: WitnessAuditVerdict
    reasons: Tuple[str, ...]
    gluing_status: GluingStatus | None
    grants_gluing_authority: bool
    grants_theorem_authority: bool = False

    @property
    def fail_closed(self) -> bool:
        return self.verdict in {
            WitnessAuditVerdict.FAIL_CLOSED_UNKNOWN,
            WitnessAuditVerdict.INCOMPATIBLE,
            WitnessAuditVerdict.CONDITIONAL_REQUIRES_CONDITION,
            WitnessAuditVerdict.THEOREM_AUTHORITY_REJECTED,
            WitnessAuditVerdict.WITNESS_UNVERIFIABLE,
        }


def build_fail_closed_unknown_witness(
    *,
    witness_id: str,
    atom_id: str,
    source_claim_scope: str,
    recorded_at_utc: str,
    evidence_pointers: Tuple[str, ...],
    required_scope_witness: str = "UNKNOWN",
    point_global_scope: ScopeAlignment = ScopeAlignment.UNKNOWN,
    time_supremum_scope: ScopeAlignment = ScopeAlignment.UNKNOWN,
    sequence_limit_scope: ScopeAlignment = ScopeAlignment.UNKNOWN,
    norm_quantifier_scope: ScopeAlignment = ScopeAlignment.UNKNOWN,
    point_global_substitution_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
    time_supremum_substitution_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
    sequence_limit_substitution_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
    norm_quantifier_substitution_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
) -> QuantifierCompatibilityWitness:
    """Construct a witness that honestly records unknowns and fail-closes."""

    return QuantifierCompatibilityWitness(
        witness_id=witness_id,
        atom_id=atom_id,
        source_claim_scope=source_claim_scope,
        point_global_scope=point_global_scope,
        time_supremum_scope=time_supremum_scope,
        sequence_limit_scope=sequence_limit_scope,
        norm_quantifier_scope=norm_quantifier_scope,
        point_global_substitution_permitted=point_global_substitution_permitted,
        time_supremum_substitution_permitted=time_supremum_substitution_permitted,
        sequence_limit_substitution_permitted=sequence_limit_substitution_permitted,
        norm_quantifier_substitution_permitted=norm_quantifier_substitution_permitted,
        required_scope_witness=required_scope_witness,
        gluing_status=GluingStatus.FAIL_CLOSED_UNKNOWN,
        evidence_pointers=evidence_pointers,
        recorded_at_utc=recorded_at_utc,
    )


def audit_quantifier_compatibility(
    witness: QuantifierCompatibilityWitness | None,
    *,
    expected_atom_id: str,
    consumer: GluingConsumer,
    claimed_witness_hash: str | None = None,
) -> QuantifierCompatibilityAudit:
    """Audit whether a witness may grant gluing/routing authority for an atom."""

    if consumer is GluingConsumer.THEOREM_AUTHORITY:
        return QuantifierCompatibilityAudit(
            witness_id=None if witness is None else witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.THEOREM_AUTHORITY_REJECTED,
            reasons=("quantifier_witness_never_mints_theorem_authority",),
            gluing_status=None if witness is None else witness.gluing_status,
            grants_gluing_authority=False,
            grants_theorem_authority=False,
        )

    if witness is None:
        return QuantifierCompatibilityAudit(
            witness_id=None,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.WITNESS_UNVERIFIABLE,
            reasons=("quantifier_compatibility_witness_missing",),
            gluing_status=None,
            grants_gluing_authority=False,
        )

    reasons: list[str] = []
    if witness.atom_id != expected_atom_id:
        reasons.append("witness_atom_id_mismatch")
    if claimed_witness_hash is not None:
        if not _SHA256_RE.match(claimed_witness_hash):
            reasons.append("claimed_witness_hash_malformed")
        elif claimed_witness_hash != witness.witness_canonical_sha256:
            reasons.append("claimed_witness_hash_mismatch")

    if reasons:
        return QuantifierCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.WITNESS_UNVERIFIABLE,
            reasons=tuple(reasons),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN or witness.unknown_fields:
        return QuantifierCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.FAIL_CLOSED_UNKNOWN,
            reasons=("unknown_load_bearing_fields:" + ",".join(witness.unknown_fields),),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.INCOMPATIBLE:
        return QuantifierCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.INCOMPATIBLE,
            reasons=("gluing_status_incompatible",),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.CONDITIONAL:
        if not witness.condition:
            return QuantifierCompatibilityAudit(
                witness_id=witness.witness_id,
                atom_id=expected_atom_id,
                verdict=WitnessAuditVerdict.CONDITIONAL_REQUIRES_CONDITION,
                reasons=("conditional_gluing_missing_condition",),
                gluing_status=witness.gluing_status,
                grants_gluing_authority=False,
            )
        return QuantifierCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.GLUING_AUTHORITY_OK,
            reasons=(f"conditional:{witness.condition}", f"consumer={consumer.value}"),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=True,
        )

    return QuantifierCompatibilityAudit(
        witness_id=witness.witness_id,
        atom_id=expected_atom_id,
        verdict=WitnessAuditVerdict.GLUING_AUTHORITY_OK,
        reasons=(f"consumer={consumer.value}",),
        gluing_status=witness.gluing_status,
        grants_gluing_authority=True,
    )
