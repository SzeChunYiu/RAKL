from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json

from rakl.structural_types import StructuralObject, StructuralRelation, TransferDecision


class ObligationKind(str, Enum):
    ROLE = "ROLE"
    RELATION = "RELATION"
    INVARIANT = "INVARIANT"
    PRECONDITION = "PRECONDITION"
    BOUNDARY = "BOUNDARY"
    QOI = "QOI"
    FORBIDDEN_LOSS = "FORBIDDEN_LOSS"


class ObligationRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    FORBIDDEN = "FORBIDDEN"


class ObligationStatus(str, Enum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class TransferObligation:
    obligation_id: str
    kind: ObligationKind
    source_ref: str
    target_ref: str
    requirement: ObligationRequirement = ObligationRequirement.REQUIRED
    evidence_ids: tuple[str, ...] = ()
    status: ObligationStatus = ObligationStatus.UNKNOWN
    rationale_code: str = ""

    def __post_init__(self) -> None:
        if not self.obligation_id.strip():
            raise ValueError("obligation_id is required")
        if self.requirement is ObligationRequirement.REQUIRED and not self.source_ref.strip():
            raise ValueError("required obligation needs source_ref")


@dataclass(frozen=True)
class StructuralWitnessV2:
    witness_id: str
    source_structure_id: str
    target_structure_id: str
    source_context_id: str
    target_context_id: str
    qoi: str
    role_mapping: tuple[tuple[str, str], ...]
    obligations: tuple[TransferObligation, ...]
    permitted_losses: frozenset[str] = frozenset()
    forbidden_losses: frozenset[str] = frozenset()
    uncertainty_note: str = ""

    def __post_init__(self) -> None:
        required = (
            self.witness_id,
            self.source_structure_id,
            self.target_structure_id,
            self.source_context_id,
            self.target_context_id,
            self.qoi,
        )
        if any(not value.strip() for value in required):
            raise ValueError("witness identity/context/QoI fields are required")
        source_roles = [source for source, _ in self.role_mapping]
        target_roles = [target for _, target in self.role_mapping]
        if len(source_roles) != len(set(source_roles)) or len(target_roles) != len(set(target_roles)):
            raise ValueError("role mapping must be one-to-one")
        obligation_ids = [obligation.obligation_id for obligation in self.obligations]
        if len(obligation_ids) != len(set(obligation_ids)):
            raise ValueError("obligation ids must be unique")
        overlap = self.permitted_losses & self.forbidden_losses
        if overlap:
            raise ValueError(f"loss cannot be both permitted and forbidden: {sorted(overlap)}")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.structural_witness.v2",
            "witness_id": self.witness_id,
            "source_structure_id": self.source_structure_id,
            "target_structure_id": self.target_structure_id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "qoi": self.qoi,
            "role_mapping": list(self.role_mapping),
            "obligations": [
                {
                    "obligation_id": obligation.obligation_id,
                    "kind": obligation.kind.value,
                    "source_ref": obligation.source_ref,
                    "target_ref": obligation.target_ref,
                    "requirement": obligation.requirement.value,
                    "evidence_ids": list(obligation.evidence_ids),
                    "status": obligation.status.value,
                    "rationale_code": obligation.rationale_code,
                }
                for obligation in self.obligations
            ],
            "permitted_losses": sorted(self.permitted_losses),
            "forbidden_losses": sorted(self.forbidden_losses),
            "uncertainty_note": self.uncertainty_note,
        }

    @property
    def content_hash(self) -> str:
        raw = json.dumps(self.canonical_payload(), sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class ObligationTrace:
    obligation_id: str
    status: ObligationStatus
    rationale_code: str
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class TransferAssessmentV2:
    decision: TransferDecision
    traces: tuple[ObligationTrace, ...]
    reasons: tuple[str, ...]
    witness_hash: str


# Kinds whose truth is decidable against the source/target objects themselves. A witness
# may never self-certify one of these SATISFIED: doing so would let the witness control
# both the query and its discharge. Non-derivable kinds (PRECONDITION, FORBIDDEN_LOSS)
# still require an external verifier's evidence-bound status.
_DERIVABLE_KINDS = frozenset(
    {
        ObligationKind.QOI,
        ObligationKind.ROLE,
        ObligationKind.INVARIANT,
        ObligationKind.BOUNDARY,
        ObligationKind.RELATION,
    }
)


def _relation_key(relation: StructuralRelation) -> str:
    """Canonical `source|relation|target|directed(0/1)` relation identity."""
    return (
        f"{relation.source_role}|{relation.relation_type}|"
        f"{relation.target_role}|{int(relation.directed)}"
    )


def _mapped_relation_key(relation: StructuralRelation, role_map: dict[str, str]) -> str | None:
    """Image of a source relation under the witness role mapping, or None if unmapped."""
    source_role = role_map.get(relation.source_role)
    target_role = role_map.get(relation.target_role)
    if source_role is None or target_role is None:
        return None
    return f"{source_role}|{relation.relation_type}|{target_role}|{int(relation.directed)}"


def _relation_present(target: StructuralObject, target_ref: str) -> bool:
    """Check canonical `source|relation|target|directed(0/1)` relation identity."""
    parts = target_ref.split("|")
    if len(parts) != 4:
        return False
    source_role, relation_type, target_role, directed = parts
    signature = (source_role, relation_type, target_role, directed == "1")
    return signature in {relation.signature for relation in target.relations}


def _coverage_gaps(source: StructuralObject, witness: StructuralWitnessV2) -> tuple[str, ...]:
    """Load-bearing content of the SOURCE that the witness failed to put in question.

    The obligation set is witness-supplied, so an empty or selectively thinned witness
    would otherwise license vacuously: with nothing asked, nothing can fail. Coverage is
    therefore derived from the source object and can only be discharged by obligations
    that are able to block (REQUIRED/FORBIDDEN) — an OPTIONAL obligation states nothing.
    """
    load_bearing = [
        obligation
        for obligation in witness.obligations
        if obligation.requirement
        in {ObligationRequirement.REQUIRED, ObligationRequirement.FORBIDDEN}
    ]
    covered_relations = {
        obligation.source_ref
        for obligation in load_bearing
        if obligation.kind is ObligationKind.RELATION
    }
    covered_invariants = {
        obligation.source_ref
        for obligation in load_bearing
        if obligation.kind is ObligationKind.INVARIANT
    }
    has_qoi = any(obligation.kind is ObligationKind.QOI for obligation in load_bearing)

    gaps: list[str] = []
    role_map = dict(witness.role_mapping)
    for role_id in sorted(source.role_ids - set(role_map)):
        gaps.append(f"unmapped_source_role:{role_id}")
    for relation in source.relations:
        key = _relation_key(relation)
        if key not in covered_relations:
            gaps.append(f"uncovered_source_relation:{key}")
    for invariant in sorted(source.invariants):
        if invariant not in covered_invariants:
            gaps.append(f"uncovered_source_invariant:{invariant}")
    if not has_qoi:
        gaps.append("uncovered_qoi")
    return tuple(gaps)


def _evaluate_obligation(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitnessV2,
    obligation: TransferObligation,
) -> ObligationTrace:
    # Explicit verifier status is accepted only when evidence is bound to a load-bearing claim.
    if obligation.status is not ObligationStatus.UNKNOWN:
        if obligation.requirement is ObligationRequirement.REQUIRED and not obligation.evidence_ids:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "missing_obligation_evidence",
                (),
            )
        # A self-asserted status is honoured only when it cannot loosen the outcome: an
        # admitted VIOLATED is always decisive, but a SATISFIED claim about a
        # structurally decidable fact is discarded in favour of deriving it below.
        if obligation.status is ObligationStatus.VIOLATED or obligation.kind not in _DERIVABLE_KINDS:
            return ObligationTrace(
                obligation.obligation_id,
                obligation.status,
                obligation.rationale_code or "explicit_status",
                obligation.evidence_ids,
            )

    if obligation.kind is ObligationKind.QOI:
        if not obligation.evidence_ids:
            return ObligationTrace(obligation.obligation_id, ObligationStatus.UNKNOWN, "missing_qoi_evidence", ())
        status = (
            ObligationStatus.SATISFIED
            if source.qoi == target.qoi == witness.qoi
            else ObligationStatus.VIOLATED
        )
        return ObligationTrace(
            obligation.obligation_id,
            status,
            "qoi_match" if status is ObligationStatus.SATISFIED else "qoi_mismatch",
            obligation.evidence_ids,
        )

    if obligation.kind is ObligationKind.ROLE:
        mapped = dict(witness.role_mapping).get(obligation.source_ref)
        if mapped is None:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "role_mapping_missing",
                obligation.evidence_ids,
            )
        status = (
            ObligationStatus.SATISFIED
            if mapped == obligation.target_ref and mapped in target.role_ids
            else ObligationStatus.VIOLATED
        )
        return ObligationTrace(
            obligation.obligation_id,
            status,
            "role_mapping_match" if status is ObligationStatus.SATISFIED else "role_mapping_conflict",
            obligation.evidence_ids,
        )

    if obligation.kind is ObligationKind.INVARIANT:
        if not obligation.evidence_ids:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "missing_invariant_evidence",
                (),
            )
        status = (
            ObligationStatus.SATISFIED
            if obligation.target_ref in target.invariants
            else ObligationStatus.VIOLATED
        )
        return ObligationTrace(
            obligation.obligation_id,
            status,
            "invariant_preserved" if status is ObligationStatus.SATISFIED else "invariant_missing",
            obligation.evidence_ids,
        )

    if obligation.kind is ObligationKind.BOUNDARY:
        if not obligation.evidence_ids:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "missing_boundary_evidence",
                (),
            )
        actual = target.boundary_map.get(obligation.source_ref)
        if actual is None:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "boundary_unknown",
                obligation.evidence_ids,
            )
        status = (
            ObligationStatus.SATISFIED if actual == obligation.target_ref else ObligationStatus.VIOLATED
        )
        return ObligationTrace(
            obligation.obligation_id,
            status,
            "boundary_match" if status is ObligationStatus.SATISFIED else "boundary_mismatch",
            obligation.evidence_ids,
        )

    if obligation.kind is ObligationKind.RELATION:
        if not obligation.evidence_ids:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "missing_relation_evidence",
                (),
            )
        # The obligation must name a real source relation and check its image under the
        # declared role mapping; otherwise the witness would choose which target relation
        # stands in for the source relation it claims to preserve.
        expected: str | None = None
        role_map = dict(witness.role_mapping)
        for relation in source.relations:
            if _relation_key(relation) == obligation.source_ref:
                expected = _mapped_relation_key(relation, role_map)
                break
        if expected is None:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "relation_source_ref_unresolved",
                obligation.evidence_ids,
            )
        if expected != obligation.target_ref:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "relation_target_ref_not_role_mapping_image",
                obligation.evidence_ids,
            )
        status = (
            ObligationStatus.SATISFIED
            if _relation_present(target, obligation.target_ref)
            else ObligationStatus.VIOLATED
        )
        return ObligationTrace(
            obligation.obligation_id,
            status,
            "relation_preserved" if status is ObligationStatus.SATISFIED else "relation_not_preserved",
            obligation.evidence_ids,
        )

    if obligation.kind is ObligationKind.FORBIDDEN_LOSS:
        if obligation.source_ref in witness.permitted_losses:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.VIOLATED,
                "forbidden_loss_permitted",
                obligation.evidence_ids,
            )
        if obligation.source_ref in witness.forbidden_losses:
            return ObligationTrace(
                obligation.obligation_id,
                ObligationStatus.UNKNOWN,
                "forbidden_loss_preservation_unverified",
                obligation.evidence_ids,
            )
        return ObligationTrace(
            obligation.obligation_id,
            ObligationStatus.UNKNOWN,
            "forbidden_loss_not_declared",
            obligation.evidence_ids,
        )

    # PRECONDITION (and future semantic obligations) requires an objective/external
    # verifier or an explicitly evidence-bound frozen status.
    return ObligationTrace(
        obligation.obligation_id,
        ObligationStatus.UNKNOWN,
        "requires_external_verifier",
        obligation.evidence_ids,
    )


def assess_transfer_v2(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitnessV2,
) -> TransferAssessmentV2:
    """Apply a fail-closed, non-compensatory directional transport contract.

    LICENSED requires every load-bearing obligation to be satisfied AND the witness's
    obligation set to cover the source object's load-bearing content (every source
    relation, every source invariant, the QoI, and a mapping for every source role).
    REJECTED requires a demonstrated violation. Otherwise unresolved or uncovered
    load-bearing facts yield CANNOT_CHECK.

    Coverage is derived from the source, never from the witness: the obligation set is
    witness-supplied, so without it an empty obligation list would license vacuously.
    """
    identity_reasons: list[str] = []
    if witness.source_structure_id != source.structure_id or witness.source_context_id != source.context_id:
        identity_reasons.append("source_identity_or_context_mismatch")
    if witness.target_structure_id != target.structure_id or witness.target_context_id != target.context_id:
        identity_reasons.append("target_identity_or_context_mismatch")
    if identity_reasons:
        return TransferAssessmentV2(
            TransferDecision.CANNOT_CHECK,
            (),
            tuple(identity_reasons),
            witness.content_hash,
        )

    traces = tuple(
        _evaluate_obligation(source, target, witness, obligation)
        for obligation in witness.obligations
    )
    load_bearing = [
        (obligation, trace)
        for obligation, trace in zip(witness.obligations, traces)
        if obligation.requirement
        in {ObligationRequirement.REQUIRED, ObligationRequirement.FORBIDDEN}
    ]
    violations = [
        trace for _, trace in load_bearing if trace.status is ObligationStatus.VIOLATED
    ]
    unknowns = [
        trace for _, trace in load_bearing if trace.status is ObligationStatus.UNKNOWN
    ]

    coverage_gaps = _coverage_gaps(source, witness)

    # A demonstrated violation stays decisive: incomplete coverage must not be able to
    # downgrade a REJECTED into an abstention.
    if violations:
        decision = TransferDecision.REJECTED
    elif coverage_gaps or unknowns or not load_bearing:
        decision = TransferDecision.CANNOT_CHECK
    else:
        decision = TransferDecision.LICENSED

    reasons = tuple(
        trace.rationale_code
        for trace in traces
        if trace.status is not ObligationStatus.SATISFIED
    ) + coverage_gaps
    if not load_bearing:
        # Fail-closed on an empty load-bearing obligation set: source-derived coverage
        # already abstains for any non-trivial source, but an empty set must never
        # license transfer, even for a degenerate source (#643 contract, kept explicit).
        reasons = ("empty_load_bearing_obligation_set", *reasons)
    return TransferAssessmentV2(decision, traces, reasons, witness.content_hash)
