from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence, Tuple


def _canonical_hash(payload: Mapping[str, object]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def _unique_nonempty(values: Sequence[str], field: str) -> None:
    if any(not value for value in values):
        raise ValueError(f"{field} contains an empty value")
    if len(set(values)) != len(values):
        raise ValueError(f"{field} must be unique")


class QuotientValidationVerdict(str, Enum):
    VALID_EXACT = "VALID_EXACT"
    VALID_APPROXIMATE = "VALID_APPROXIMATE"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ProblemRepresentation:
    """Immutable source-facing representation for proposing a task-conditioned quotient.

    This does not replace the canonical problem or evidence. ``source_hash`` pins the
    canonical source so every quotient remains a derived computational view.
    """

    representation_id: str
    problem_id: str
    atom_id: str
    qoi: str
    context_hash: str
    source_hash: str
    coordinates: Tuple[str, ...]
    relations: Tuple[str, ...] = ()
    constraints: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    protected_fields: Tuple[str, ...] = ()
    provenance_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "representation_id",
            "problem_id",
            "atom_id",
            "qoi",
            "context_hash",
            "source_hash",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")
        if not self.coordinates:
            raise ValueError("coordinates are required")
        for field_name in (
            "coordinates",
            "relations",
            "constraints",
            "assumptions",
            "protected_fields",
            "provenance_ids",
        ):
            _unique_nonempty(getattr(self, field_name), field_name)
        if not set(self.protected_fields).issubset(self.coordinates):
            raise ValueError("protected_fields must be source coordinates")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.problem_representation.v1",
            "representation_id": self.representation_id,
            "problem_id": self.problem_id,
            "atom_id": self.atom_id,
            "qoi": self.qoi,
            "context_hash": self.context_hash,
            "source_hash": self.source_hash,
            "coordinates": list(self.coordinates),
            "relations": list(self.relations),
            "constraints": list(self.constraints),
            "assumptions": list(self.assumptions),
            "protected_fields": list(self.protected_fields),
            "provenance_ids": list(self.provenance_ids),
        }

    @property
    def content_hash(self) -> str:
        return _canonical_hash(self.canonical_payload())


@dataclass(frozen=True)
class QuotientProposal:
    """Proposal-only erasure/preservation plan; it cannot self-certify sufficiency."""

    quotient_id: str
    source_representation_id: str
    source_hash: str
    qoi: str
    context_hash: str
    preserved_coordinates: Tuple[str, ...]
    erased_coordinates: Tuple[str, ...]
    conditionally_erased_coordinates: Tuple[str, ...] = ()
    equivalence_generators: Tuple[str, ...] = ()
    preserved_invariants: Tuple[str, ...] = ()
    protected_coordinates: Tuple[str, ...] = ()
    sufficiency_obligations: Tuple[str, ...] = ()
    reconstruction_bindings: Tuple[Tuple[str, str], ...] = ()
    falsifiers: Tuple[str, ...] = ()
    forbidden_losses: Tuple[str, ...] = ()
    proposer_kind: str = "RULE_BASED"
    evidence_pointers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "quotient_id",
            "source_representation_id",
            "source_hash",
            "qoi",
            "context_hash",
            "proposer_kind",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")
        for field_name in (
            "preserved_coordinates",
            "erased_coordinates",
            "conditionally_erased_coordinates",
            "equivalence_generators",
            "preserved_invariants",
            "protected_coordinates",
            "sufficiency_obligations",
            "falsifiers",
            "forbidden_losses",
            "evidence_pointers",
        ):
            _unique_nonempty(getattr(self, field_name), field_name)
        keys = [key for key, _ in self.reconstruction_bindings]
        if any(not key or not value for key, value in self.reconstruction_bindings):
            raise ValueError("reconstruction_bindings cannot contain empty values")
        if len(keys) != len(set(keys)):
            raise ValueError("reconstruction binding keys must be unique")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.task_conditioned_structural_quotient.proposal.v1",
            "quotient_id": self.quotient_id,
            "source_representation_id": self.source_representation_id,
            "source_hash": self.source_hash,
            "qoi": self.qoi,
            "context_hash": self.context_hash,
            "preserved_coordinates": list(self.preserved_coordinates),
            "erased_coordinates": list(self.erased_coordinates),
            "conditionally_erased_coordinates": list(self.conditionally_erased_coordinates),
            "equivalence_generators": list(self.equivalence_generators),
            "preserved_invariants": list(self.preserved_invariants),
            "protected_coordinates": list(self.protected_coordinates),
            "sufficiency_obligations": list(self.sufficiency_obligations),
            "reconstruction_bindings": [list(item) for item in self.reconstruction_bindings],
            "falsifiers": list(self.falsifiers),
            "forbidden_losses": list(self.forbidden_losses),
            "proposer_kind": self.proposer_kind,
            "evidence_pointers": list(self.evidence_pointers),
        }

    @property
    def content_hash(self) -> str:
        return _canonical_hash(self.canonical_payload())


@dataclass(frozen=True)
class QuotientValidationReport:
    quotient_id: str
    proposal_hash: str
    source_hash: str
    verdict: QuotientValidationVerdict
    verified_obligations: Tuple[str, ...] = ()
    failed_obligations: Tuple[str, ...] = ()
    unknown_obligations: Tuple[str, ...] = ()
    oracle_checks: Tuple[str, ...] = ()
    metamorphic_checks: Tuple[str, ...] = ()
    formal_checks: Tuple[str, ...] = ()
    counterexample_checks: Tuple[str, ...] = ()
    protected_coordinate_checks: Tuple[str, ...] = ()
    approximation_metric: str | None = None
    approximation_tolerance: float | None = None
    evidence_pointers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.quotient_id or not self.proposal_hash or not self.source_hash:
            raise ValueError("validation report requires quotient/proposal/source identity")
        for field_name in (
            "verified_obligations",
            "failed_obligations",
            "unknown_obligations",
            "oracle_checks",
            "metamorphic_checks",
            "formal_checks",
            "counterexample_checks",
            "protected_coordinate_checks",
            "evidence_pointers",
        ):
            _unique_nonempty(getattr(self, field_name), field_name)
        overlap = (
            set(self.verified_obligations) & set(self.failed_obligations)
            | set(self.verified_obligations) & set(self.unknown_obligations)
            | set(self.failed_obligations) & set(self.unknown_obligations)
        )
        if overlap:
            raise ValueError(f"validation obligation status overlap: {sorted(overlap)}")
        if self.approximation_tolerance is not None and self.approximation_tolerance < 0:
            raise ValueError("approximation_tolerance must be non-negative")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.task_conditioned_structural_quotient.validation.v1",
            "quotient_id": self.quotient_id,
            "proposal_hash": self.proposal_hash,
            "source_hash": self.source_hash,
            "verdict": self.verdict.value,
            "verified_obligations": list(self.verified_obligations),
            "failed_obligations": list(self.failed_obligations),
            "unknown_obligations": list(self.unknown_obligations),
            "oracle_checks": list(self.oracle_checks),
            "metamorphic_checks": list(self.metamorphic_checks),
            "formal_checks": list(self.formal_checks),
            "counterexample_checks": list(self.counterexample_checks),
            "protected_coordinate_checks": list(self.protected_coordinate_checks),
            "approximation_metric": self.approximation_metric,
            "approximation_tolerance": self.approximation_tolerance,
            "evidence_pointers": list(self.evidence_pointers),
        }

    @property
    def content_hash(self) -> str:
        return _canonical_hash(self.canonical_payload())


@dataclass(frozen=True)
class ValidatedQuotientView:
    quotient_id: str
    source_representation_id: str
    source_atom_id: str
    source_hash: str
    qoi: str
    context_hash: str
    structural_coordinates: Tuple[str, ...]
    desired_effects: Tuple[str, ...]
    erased_coordinates: Tuple[str, ...]
    conditionally_erased_coordinates: Tuple[str, ...]
    preserved_invariants: Tuple[str, ...]
    protected_coordinates: Tuple[str, ...]
    forbidden_losses: Tuple[str, ...]
    reconstruction_bindings: Tuple[Tuple[str, str], ...]
    proposal_hash: str
    validation_report_hash: str
    validation_verdict: QuotientValidationVerdict

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.task_conditioned_structural_quotient.view.v1",
            "quotient_id": self.quotient_id,
            "source_representation_id": self.source_representation_id,
            "source_atom_id": self.source_atom_id,
            "source_hash": self.source_hash,
            "qoi": self.qoi,
            "context_hash": self.context_hash,
            "structural_coordinates": list(self.structural_coordinates),
            "desired_effects": list(self.desired_effects),
            "erased_coordinates": list(self.erased_coordinates),
            "conditionally_erased_coordinates": list(self.conditionally_erased_coordinates),
            "preserved_invariants": list(self.preserved_invariants),
            "protected_coordinates": list(self.protected_coordinates),
            "forbidden_losses": list(self.forbidden_losses),
            "reconstruction_bindings": [list(item) for item in self.reconstruction_bindings],
            "proposal_hash": self.proposal_hash,
            "validation_report_hash": self.validation_report_hash,
            "validation_verdict": self.validation_verdict.value,
        }

    @property
    def content_hash(self) -> str:
        return _canonical_hash(self.canonical_payload())


@dataclass(frozen=True)
class ReconstructionReport:
    quotient_id: str
    quotient_view_hash: str
    source_problem_id: str
    source_hash: str
    quotient_solution_hash: str
    reconstructed_solution_hash: str
    original_problem_verification: str
    evidence_pointers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "quotient_id",
            "quotient_view_hash",
            "source_problem_id",
            "source_hash",
            "quotient_solution_hash",
            "reconstructed_solution_hash",
            "original_problem_verification",
        ):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} is required")
        _unique_nonempty(self.evidence_pointers, "evidence_pointers")

    @property
    def original_problem_verified(self) -> bool:
        return self.original_problem_verification == "PASS"

    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "rakl.task_conditioned_structural_quotient.reconstruction.v1",
            "quotient_id": self.quotient_id,
            "quotient_view_hash": self.quotient_view_hash,
            "source_problem_id": self.source_problem_id,
            "source_hash": self.source_hash,
            "quotient_solution_hash": self.quotient_solution_hash,
            "reconstructed_solution_hash": self.reconstructed_solution_hash,
            "original_problem_verification": self.original_problem_verification,
            "evidence_pointers": list(self.evidence_pointers),
        }

    @property
    def content_hash(self) -> str:
        return _canonical_hash(self.canonical_payload())


@dataclass(frozen=True)
class QuotientProblemFibre:
    """Trace wrapper keeping canonical atom and quotient identities distinct."""

    source_atom_id: str
    quotient_view_hash: str
    fibre_snapshot_hash: str
    derived_snapshot_hash: str
    fibre: Any


def validate_proposal_contract(
    source: ProblemRepresentation,
    proposal: QuotientProposal,
) -> Tuple[str, ...]:
    """Validate representation/erasure metadata only; not semantic sufficiency."""

    reasons: list[str] = []
    if proposal.source_representation_id != source.representation_id:
        reasons.append("source_representation_mismatch")
    if proposal.source_hash != source.source_hash:
        reasons.append("source_hash_mismatch")
    if proposal.qoi != source.qoi:
        reasons.append("qoi_mismatch")
    if proposal.context_hash != source.context_hash:
        reasons.append("context_hash_mismatch")

    source_coordinates = set(source.coordinates)
    preserved = set(proposal.preserved_coordinates)
    erased = set(proposal.erased_coordinates)
    conditional = set(proposal.conditionally_erased_coordinates)
    protected = set(source.protected_fields) | set(proposal.protected_coordinates)

    if preserved & erased or preserved & conditional or erased & conditional:
        reasons.append("coordinate_partition_conflict")
    if (preserved | erased | conditional) - source_coordinates:
        reasons.append("proposal_references_unknown_coordinate")
    if source_coordinates - (preserved | erased | conditional):
        reasons.append("source_coordinate_unclassified")
    if protected - source_coordinates:
        reasons.append("protected_coordinate_not_in_source")
    if protected & (erased | conditional):
        reasons.append("protected_coordinate_erased")
    if protected - preserved:
        reasons.append("protected_coordinate_not_preserved")
    if not proposal.preserved_coordinates:
        reasons.append("preserved_coordinates_missing")
    if not proposal.preserved_invariants:
        reasons.append("preserved_invariants_missing")
    if not proposal.sufficiency_obligations:
        reasons.append("sufficiency_obligations_missing")
    if not proposal.falsifiers:
        reasons.append("falsifiers_missing")
    if set(proposal.forbidden_losses) & set(proposal.erased_coordinates):
        reasons.append("forbidden_loss_erased")

    return tuple(dict.fromkeys(reasons))


def materialize_validated_quotient(
    source: ProblemRepresentation,
    proposal: QuotientProposal,
    report: QuotientValidationReport,
    *,
    desired_effects: Tuple[str, ...] = (),
) -> ValidatedQuotientView:
    """Create a solver-facing view only after a separately bound passing report."""

    reasons = validate_proposal_contract(source, proposal)
    if reasons:
        raise ValueError(f"invalid quotient proposal: {reasons}")
    if report.quotient_id != proposal.quotient_id:
        raise ValueError("validation_report_quotient_mismatch")
    if report.proposal_hash != proposal.content_hash:
        raise ValueError("validation_report_proposal_hash_mismatch")
    if report.source_hash != source.source_hash:
        raise ValueError("validation_report_source_hash_mismatch")
    if report.verdict not in {
        QuotientValidationVerdict.VALID_EXACT,
        QuotientValidationVerdict.VALID_APPROXIMATE,
    }:
        raise ValueError("quotient_not_validated_for_solver_use")
    if report.failed_obligations:
        raise ValueError("quotient_has_failed_sufficiency_obligations")
    if report.unknown_obligations:
        raise ValueError("quotient_has_unknown_sufficiency_obligations")
    missing_verified = set(proposal.sufficiency_obligations) - set(report.verified_obligations)
    if missing_verified:
        raise ValueError(f"sufficiency_obligations_not_verified:{sorted(missing_verified)}")
    validation_checks = (
        report.oracle_checks
        + report.metamorphic_checks
        + report.formal_checks
        + report.counterexample_checks
        + report.protected_coordinate_checks
    )
    if not validation_checks or not report.evidence_pointers:
        raise ValueError("validation_evidence_missing")
    if report.verdict is QuotientValidationVerdict.VALID_APPROXIMATE:
        if not report.approximation_metric or report.approximation_tolerance is None:
            raise ValueError("approximate_quotient_requires_metric_and_tolerance")

    return ValidatedQuotientView(
        quotient_id=proposal.quotient_id,
        source_representation_id=source.representation_id,
        source_atom_id=source.atom_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        structural_coordinates=proposal.preserved_coordinates,
        desired_effects=desired_effects,
        erased_coordinates=proposal.erased_coordinates,
        conditionally_erased_coordinates=proposal.conditionally_erased_coordinates,
        preserved_invariants=proposal.preserved_invariants,
        protected_coordinates=tuple(sorted(set(source.protected_fields) | set(proposal.protected_coordinates))),
        forbidden_losses=proposal.forbidden_losses,
        reconstruction_bindings=proposal.reconstruction_bindings,
        proposal_hash=proposal.content_hash,
        validation_report_hash=report.content_hash,
        validation_verdict=report.verdict,
    )


def quotient_to_memory_view(
    view: ValidatedQuotientView,
    *,
    canonical_record_id: str,
    canonical_payload_hash: str,
    source_authority_certificates: Tuple[str, ...] = (),
):
    """Materialize TCSQ as a derived memory view without authority escalation."""

    from .multires_memory import MemoryView, MemoryViewKind, SourcePin

    erasure_tags = tuple(f"ERASED:{item}" for item in view.erased_coordinates) + tuple(
        f"CONDITIONALLY_ERASED:{item}" for item in view.conditionally_erased_coordinates
    )
    kind = MemoryViewKind.DERIVED_LOSSY if erasure_tags else MemoryViewKind.DERIVED_LOSSLESS
    return MemoryView(
        record_id=f"tcsq:{view.quotient_id}:{view.content_hash[:12]}",
        payload_hash=view.content_hash,
        kind=kind,
        source_pins=(SourcePin(canonical_record_id, canonical_payload_hash),),
        transform_id=f"TCSQ:{view.quotient_id}",
        erasure_tags=erasure_tags,
        authority_certificates=source_authority_certificates,
        required_canonical_ids=(canonical_record_id,),
    )


def quotient_problem_atom(source_atom: Any, view: ValidatedQuotientView) -> Any:
    """Return a derived retrieval atom; never mutate the canonical source atom."""

    if getattr(source_atom, "atom_id", None) != view.source_atom_id:
        raise ValueError("quotient_source_atom_mismatch")
    if getattr(source_atom, "context_hash", None) != view.context_hash:
        raise ValueError("quotient_context_mismatch")
    return replace(
        source_atom,
        structural_coordinates=view.structural_coordinates,
        desired_effects=view.desired_effects or getattr(source_atom, "desired_effects"),
    )


def compile_quotient_problem_fibre(
    source_atom: Any,
    view: ValidatedQuotientView,
    **compile_kwargs: object,
) -> QuotientProblemFibre:
    """Compile incumbent ProblemFibre over a validated derived atom with explicit lineage."""

    from .problem_fibre import compile_problem_fibre

    derived_atom = quotient_problem_atom(source_atom, view)
    fibre = compile_problem_fibre(derived_atom, **compile_kwargs)
    derived_snapshot_hash = _canonical_hash(
        {
            "schema": "rakl.quotient_problem_fibre.v1",
            "source_atom_id": view.source_atom_id,
            "quotient_view_hash": view.content_hash,
            "fibre_snapshot_hash": fibre.snapshot_hash,
        }
    )
    return QuotientProblemFibre(
        source_atom_id=view.source_atom_id,
        quotient_view_hash=view.content_hash,
        fibre_snapshot_hash=fibre.snapshot_hash,
        derived_snapshot_hash=derived_snapshot_hash,
        fibre=fibre,
    )


def obstruction_from_validated_quotient(
    view: ValidatedQuotientView,
    *,
    obstruction_id: str,
    domain: str,
    roles: Tuple[str, ...],
    relations: Tuple[str, ...],
    constraints: Tuple[str, ...],
    failure_mechanisms: Tuple[str, ...],
):
    """Build an obstruction explicitly; never infer erased structure back silently."""

    from .semantic_shortcut import ObstructionFingerprint

    return ObstructionFingerprint(
        obstruction_id=obstruction_id,
        domain=domain,
        roles=roles,
        relations=relations,
        constraints=constraints + tuple(f"protected:{item}" for item in view.protected_coordinates),
        failure_mechanisms=failure_mechanisms,
        invariants_to_preserve=view.preserved_invariants,
        desired_transition=view.desired_effects or (view.qoi,),
        forbidden_losses=view.forbidden_losses,
    )
