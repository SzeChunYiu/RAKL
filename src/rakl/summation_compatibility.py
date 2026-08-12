"""Proposal-only summation / limit-order compatibility witness (issue #384).

Local decompositions of infinite sums, integrals, spectral expansions, RG
iterations, or other limiting objects can preserve local correctness while
silently changing the global object when regrouping, reordering, exchanging
limits, or independently bounding components is unjustified.

This module freezes a narrow typed witness for that surface. It is intended to
affect **routing / gluing authority claims only**. It does not mint theorem,
proof, novelty, or identification authority.

Scope, stated as narrowly as the artifact supports:

* **Not wired into** ``glue_local_sections``, ``math_context``, or protected
  promotion paths. Automatic enforcement at those surfaces remains a separate
  Class-B framework-evolution change under the upgrade protocol.
* **Fail-closed.** Any ``UNKNOWN`` load-bearing field, or an alternate-method
  equivalence marked ``UNKNOWN`` when an alternate method is claimed, forces
  ``FAIL_CLOSED_UNKNOWN`` and rejects gluing-authority consumers.
* **No theorem authority.** ``authority_claim`` is fixed to
  ``ROUTING_GLUING_ONLY_NOT_THEOREM``.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Tuple

WITNESS_SCHEMA_VERSION = "summation-compatibility-witness-v1"
AUTHORITY_CLAIM = "ROUTING_GLUING_ONLY_NOT_THEOREM"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")

_LOAD_BEARING_TRI_STATE_FIELDS = (
    "convergence_status",
    "finite_grouping_permitted",
    "infinite_regrouping_reordering_permitted",
)


class ConvergenceStatus(str, Enum):
    ABSOLUTE = "ABSOLUTE"
    CONDITIONAL = "CONDITIONAL"
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
    convergence_status: ConvergenceStatus,
    finite_grouping_permitted: PermissionStatus,
    infinite_regrouping_reordering_permitted: PermissionStatus,
    nested_limit_order: str,
    local_block_definition: str,
    block_tail_or_convergence_theorem_required: str,
    alternate_summation_equivalence_proof: str,
) -> Tuple[str, ...]:
    unknown: list[str] = []
    if convergence_status is ConvergenceStatus.UNKNOWN:
        unknown.append("convergence_status")
    if finite_grouping_permitted is PermissionStatus.UNKNOWN:
        unknown.append("finite_grouping_permitted")
    if infinite_regrouping_reordering_permitted is PermissionStatus.UNKNOWN:
        unknown.append("infinite_regrouping_reordering_permitted")
    for name, value in (
        ("nested_limit_order", nested_limit_order),
        ("local_block_definition", local_block_definition),
        ("block_tail_or_convergence_theorem_required", block_tail_or_convergence_theorem_required),
        ("alternate_summation_equivalence_proof", alternate_summation_equivalence_proof),
    ):
        if value.strip().upper() == "UNKNOWN":
            unknown.append(name)
    return tuple(unknown)


@dataclass(frozen=True)
class SummationCompatibilityWitness:
    """Typed limit-order / summation compatibility record for one atom.

    Construction fail-closes: if any load-bearing field is ``UNKNOWN``,
    ``gluing_status`` is forced to ``FAIL_CLOSED_UNKNOWN``.
    """

    witness_id: str
    atom_id: str
    source_accumulation_method: str
    convergence_status: ConvergenceStatus
    finite_grouping_permitted: PermissionStatus
    infinite_regrouping_reordering_permitted: PermissionStatus
    nested_limit_order: str
    local_block_definition: str
    block_tail_or_convergence_theorem_required: str
    alternate_summation_equivalence_proof: str
    gluing_status: GluingStatus
    evidence_pointers: Tuple[str, ...]
    recorded_at_utc: str
    condition: Optional[str] = None
    schema_version: str = WITNESS_SCHEMA_VERSION
    authority_claim: str = AUTHORITY_CLAIM

    def __post_init__(self) -> None:
        if not self.witness_id:
            raise ValueError("summation witness requires witness_id")
        if not self.atom_id:
            raise ValueError("summation witness requires atom_id")
        if not self.source_accumulation_method.strip():
            raise ValueError("source_accumulation_method is required")
        if not self.nested_limit_order.strip():
            raise ValueError("nested_limit_order is required")
        if not self.local_block_definition.strip():
            raise ValueError("local_block_definition is required")
        if not self.block_tail_or_convergence_theorem_required.strip():
            raise ValueError("block_tail_or_convergence_theorem_required is required")
        if not self.alternate_summation_equivalence_proof.strip():
            raise ValueError("alternate_summation_equivalence_proof is required")
        if not self.evidence_pointers:
            raise ValueError("evidence_pointers are required")
        if not _ISO_UTC_RE.match(self.recorded_at_utc):
            raise ValueError("recorded_at_utc must be ISO-8601 UTC ending in 'Z'")
        if self.authority_claim != AUTHORITY_CLAIM:
            raise ValueError("authority_claim must remain ROUTING_GLUING_ONLY_NOT_THEOREM")
        if self.gluing_status is GluingStatus.CONDITIONAL and not self.condition:
            raise ValueError("CONDITIONAL gluing_status requires an explicit condition")

        unknowns = _unknown_fields_from_values(
            convergence_status=self.convergence_status,
            finite_grouping_permitted=self.finite_grouping_permitted,
            infinite_regrouping_reordering_permitted=self.infinite_regrouping_reordering_permitted,
            nested_limit_order=self.nested_limit_order,
            local_block_definition=self.local_block_definition,
            block_tail_or_convergence_theorem_required=self.block_tail_or_convergence_theorem_required,
            alternate_summation_equivalence_proof=self.alternate_summation_equivalence_proof,
        )
        if unknowns and self.gluing_status is not GluingStatus.FAIL_CLOSED_UNKNOWN:
            raise ValueError(
                "unknown load-bearing fields require gluing_status=FAIL_CLOSED_UNKNOWN: "
                + ",".join(unknowns)
            )
        if not unknowns and self.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN:
            raise ValueError(
                "FAIL_CLOSED_UNKNOWN requires at least one unknown load-bearing field"
            )

    @property
    def unknown_fields(self) -> Tuple[str, ...]:
        return _unknown_fields_from_values(
            convergence_status=self.convergence_status,
            finite_grouping_permitted=self.finite_grouping_permitted,
            infinite_regrouping_reordering_permitted=self.infinite_regrouping_reordering_permitted,
            nested_limit_order=self.nested_limit_order,
            local_block_definition=self.local_block_definition,
            block_tail_or_convergence_theorem_required=self.block_tail_or_convergence_theorem_required,
            alternate_summation_equivalence_proof=self.alternate_summation_equivalence_proof,
        )

    def content(self) -> Mapping[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "witness_id": self.witness_id,
            "atom_id": self.atom_id,
            "source_accumulation_method": self.source_accumulation_method,
            "convergence_status": self.convergence_status.value,
            "finite_grouping_permitted": self.finite_grouping_permitted.value,
            "infinite_regrouping_reordering_permitted": self.infinite_regrouping_reordering_permitted.value,
            "nested_limit_order": self.nested_limit_order,
            "local_block_definition": self.local_block_definition,
            "block_tail_or_convergence_theorem_required": self.block_tail_or_convergence_theorem_required,
            "alternate_summation_equivalence_proof": self.alternate_summation_equivalence_proof,
            "gluing_status": self.gluing_status.value,
            "authority_claim": self.authority_claim,
            "evidence_pointers": list(self.evidence_pointers),
            "recorded_at_utc": self.recorded_at_utc,
            "unknown_fields": list(self.unknown_fields),
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
class SummationCompatibilityAudit:
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
    source_accumulation_method: str,
    recorded_at_utc: str,
    evidence_pointers: Tuple[str, ...],
    nested_limit_order: str = "UNKNOWN",
    local_block_definition: str = "UNKNOWN",
    block_tail_or_convergence_theorem_required: str = "UNKNOWN",
    alternate_summation_equivalence_proof: str = "UNKNOWN",
    convergence_status: ConvergenceStatus = ConvergenceStatus.UNKNOWN,
    finite_grouping_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
    infinite_regrouping_reordering_permitted: PermissionStatus = PermissionStatus.UNKNOWN,
) -> SummationCompatibilityWitness:
    """Construct a witness that honestly records unknowns and fail-closes."""

    return SummationCompatibilityWitness(
        witness_id=witness_id,
        atom_id=atom_id,
        source_accumulation_method=source_accumulation_method,
        convergence_status=convergence_status,
        finite_grouping_permitted=finite_grouping_permitted,
        infinite_regrouping_reordering_permitted=infinite_regrouping_reordering_permitted,
        nested_limit_order=nested_limit_order,
        local_block_definition=local_block_definition,
        block_tail_or_convergence_theorem_required=block_tail_or_convergence_theorem_required,
        alternate_summation_equivalence_proof=alternate_summation_equivalence_proof,
        gluing_status=GluingStatus.FAIL_CLOSED_UNKNOWN,
        evidence_pointers=evidence_pointers,
        recorded_at_utc=recorded_at_utc,
    )


def audit_summation_compatibility(
    witness: SummationCompatibilityWitness | None,
    *,
    expected_atom_id: str,
    consumer: GluingConsumer,
    claimed_witness_hash: str | None = None,
) -> SummationCompatibilityAudit:
    """Audit whether a witness may grant gluing/routing authority for an atom.

    ``THEOREM_AUTHORITY`` consumers are always rejected. Missing / hash-mismatched
    / unknown witnesses fail closed.
    """

    if consumer is GluingConsumer.THEOREM_AUTHORITY:
        return SummationCompatibilityAudit(
            witness_id=None if witness is None else witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.THEOREM_AUTHORITY_REJECTED,
            reasons=("summation_witness_never_mints_theorem_authority",),
            gluing_status=None if witness is None else witness.gluing_status,
            grants_gluing_authority=False,
            grants_theorem_authority=False,
        )

    if witness is None:
        return SummationCompatibilityAudit(
            witness_id=None,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.WITNESS_UNVERIFIABLE,
            reasons=("summation_compatibility_witness_missing",),
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
        return SummationCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.WITNESS_UNVERIFIABLE,
            reasons=tuple(reasons),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.FAIL_CLOSED_UNKNOWN or witness.unknown_fields:
        return SummationCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.FAIL_CLOSED_UNKNOWN,
            reasons=("unknown_load_bearing_fields:" + ",".join(witness.unknown_fields),),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.INCOMPATIBLE:
        return SummationCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.INCOMPATIBLE,
            reasons=("gluing_status_incompatible",),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=False,
        )

    if witness.gluing_status is GluingStatus.CONDITIONAL:
        if not witness.condition:
            return SummationCompatibilityAudit(
                witness_id=witness.witness_id,
                atom_id=expected_atom_id,
                verdict=WitnessAuditVerdict.CONDITIONAL_REQUIRES_CONDITION,
                reasons=("conditional_gluing_missing_condition",),
                gluing_status=witness.gluing_status,
                grants_gluing_authority=False,
            )
        return SummationCompatibilityAudit(
            witness_id=witness.witness_id,
            atom_id=expected_atom_id,
            verdict=WitnessAuditVerdict.GLUING_AUTHORITY_OK,
            reasons=(f"conditional:{witness.condition}", f"consumer={consumer.value}"),
            gluing_status=witness.gluing_status,
            grants_gluing_authority=True,
        )

    return SummationCompatibilityAudit(
        witness_id=witness.witness_id,
        atom_id=expected_atom_id,
        verdict=WitnessAuditVerdict.GLUING_AUTHORITY_OK,
        reasons=(f"consumer={consumer.value}",),
        gluing_status=witness.gluing_status,
        grants_gluing_authority=True,
    )
