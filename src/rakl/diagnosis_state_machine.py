"""Strict immutable state machine for mechanic diagnosis refinement.

This closes the gap between a one-shot signal classifier and a diagnosis process:
causes may be ruled out only by an explicit discriminator/evidence transition,
and a unique concrete cause cannot be hidden behind CANNOT_CHECK.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .canonical_commitment import sha256_digest


class DiagnosisVerdict(str, Enum):
    NO_GAP = "NO_GAP"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    DISCRIMINATOR_REQUIRED = "DISCRIMINATOR_REQUIRED"
    MECHANIC_GAP_IDENTIFIED = "MECHANIC_GAP_IDENTIFIED"
    CANNOT_CHECK = "CANNOT_CHECK"


class DiagnosisTransitionKind(str, Enum):
    DISCRIMINATOR = "DISCRIMINATOR"
    ESTABLISH_NO_GAP = "ESTABLISH_NO_GAP"


@dataclass(frozen=True)
class DiagnosisState:
    diagnosis_id: str
    candidate_causes: tuple[str, ...]
    ruled_out_causes: tuple[str, ...]
    discriminator_ids: tuple[str, ...]
    chosen_discriminator_id: str | None
    verdict: DiagnosisVerdict
    evidence_receipt_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.diagnosis_id:
            raise ValueError("diagnosis identity required")
        if len(set(self.candidate_causes)) != len(self.candidate_causes):
            raise ValueError("candidate causes must be unique")
        if len(set(self.ruled_out_causes)) != len(self.ruled_out_causes):
            raise ValueError("ruled-out causes must be unique")
        if set(self.candidate_causes) & set(self.ruled_out_causes):
            raise ValueError("cause cannot be candidate and ruled out")
        if self.chosen_discriminator_id and self.chosen_discriminator_id not in self.discriminator_ids:
            raise ValueError("chosen discriminator must be registered")
        _validate_shape(self)

    @property
    def digest(self) -> str:
        return sha256_digest(self, domain="rakl-mechanic-diagnosis-state/v1")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def _validate_shape(state: DiagnosisState) -> None:
    concrete = tuple(c for c in state.candidate_causes if c != "UNKNOWN")
    contains_unknown = "UNKNOWN" in state.candidate_causes
    if state.verdict is DiagnosisVerdict.NO_GAP:
        if state.candidate_causes or not state.evidence_receipt_ids:
            raise ValueError("NO_GAP requires no surviving causes plus evidence")
    elif state.verdict is DiagnosisVerdict.PARTIALLY_IDENTIFIED:
        if len(concrete) < 2 or contains_unknown:
            raise ValueError("PARTIALLY_IDENTIFIED requires >=2 concrete causes and no UNKNOWN")
    elif state.verdict is DiagnosisVerdict.DISCRIMINATOR_REQUIRED:
        if len(concrete) < 2 or contains_unknown or not state.discriminator_ids:
            raise ValueError("DISCRIMINATOR_REQUIRED needs competing concrete causes + discriminator")
    elif state.verdict is DiagnosisVerdict.MECHANIC_GAP_IDENTIFIED:
        if len(concrete) != 1 or len(state.candidate_causes) != 1 or not state.evidence_receipt_ids:
            raise ValueError("identified gap requires exactly one concrete cause plus evidence")
    elif state.verdict is DiagnosisVerdict.CANNOT_CHECK:
        if len(concrete) == 1 and len(state.candidate_causes) == 1:
            raise ValueError("CANNOT_CHECK cannot silently encode a unique concrete cause")


def unresolved_state(diagnosis_id: str, *, unknown_reason_receipt_id: str | None = None) -> DiagnosisState:
    evidence = (unknown_reason_receipt_id,) if unknown_reason_receipt_id else ()
    return DiagnosisState(diagnosis_id, ("UNKNOWN",), (), (), None, DiagnosisVerdict.CANNOT_CHECK, evidence)


def competing_state(diagnosis_id: str, causes: tuple[str, ...], *, discriminator_ids: tuple[str, ...]) -> DiagnosisState:
    if len(causes) < 2:
        raise ValueError("competing state requires at least two causes")
    verdict = DiagnosisVerdict.DISCRIMINATOR_REQUIRED if discriminator_ids else DiagnosisVerdict.PARTIALLY_IDENTIFIED
    return DiagnosisState(diagnosis_id, causes, (), discriminator_ids, None, verdict)


def resolve_discriminator(
    state: DiagnosisState,
    *,
    discriminator_id: str,
    surviving_causes: tuple[str, ...],
    evidence_receipt_id: str,
    next_discriminator_ids: tuple[str, ...] = (),
) -> DiagnosisState:
    if state.verdict is not DiagnosisVerdict.DISCRIMINATOR_REQUIRED:
        raise ValueError("discriminator can resolve only a DISCRIMINATOR_REQUIRED state")
    if discriminator_id not in state.discriminator_ids:
        raise ValueError("unregistered discriminator")
    if not evidence_receipt_id:
        raise ValueError("discriminator resolution requires evidence")
    if not surviving_causes or not set(surviving_causes) <= set(state.candidate_causes):
        raise ValueError("surviving causes must be nonempty subset of candidates")
    if "UNKNOWN" in surviving_causes:
        raise ValueError("UNKNOWN cannot be promoted as a concrete cause")
    ruled = tuple(dict.fromkeys(state.ruled_out_causes + tuple(c for c in state.candidate_causes if c not in surviving_causes)))
    if len(surviving_causes) == 1:
        verdict = DiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
        next_ids = ()
    elif next_discriminator_ids:
        verdict = DiagnosisVerdict.DISCRIMINATOR_REQUIRED
        next_ids = next_discriminator_ids
    else:
        verdict = DiagnosisVerdict.PARTIALLY_IDENTIFIED
        next_ids = ()
    return DiagnosisState(
        state.diagnosis_id,
        surviving_causes,
        ruled,
        next_ids,
        None,
        verdict,
        state.evidence_receipt_ids + (evidence_receipt_id,),
    )


def establish_no_gap(state: DiagnosisState, *, evidence_receipt_id: str) -> DiagnosisState:
    if not evidence_receipt_id:
        raise ValueError("NO_GAP transition requires evidence")
    ruled = tuple(dict.fromkeys(state.ruled_out_causes + tuple(c for c in state.candidate_causes if c != "UNKNOWN")))
    return DiagnosisState(
        state.diagnosis_id,
        (),
        ruled,
        (),
        None,
        DiagnosisVerdict.NO_GAP,
        state.evidence_receipt_ids + (evidence_receipt_id,),
    )


@dataclass(frozen=True)
class DiagnosisTransitionReceipt:
    transition_id: str
    diagnosis_id: str
    kind: DiagnosisTransitionKind
    before_state_digest: str
    after_state_digest: str
    evidence_receipt_id: str
    discriminator_id: str | None = None

    def __post_init__(self) -> None:
        if any(not x for x in (
            self.transition_id, self.diagnosis_id, self.before_state_digest,
            self.after_state_digest, self.evidence_receipt_id,
        )):
            raise ValueError("diagnosis transition requires immutable before/after/evidence binding")
        if self.kind is DiagnosisTransitionKind.DISCRIMINATOR and not self.discriminator_id:
            raise ValueError("discriminator transition requires discriminator identity")
        if self.kind is DiagnosisTransitionKind.ESTABLISH_NO_GAP and self.discriminator_id is not None:
            raise ValueError("NO_GAP transition must not invent a discriminator")

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def resolve_discriminator_with_receipt(
    state: DiagnosisState,
    *,
    transition_id: str,
    discriminator_id: str,
    surviving_causes: tuple[str, ...],
    evidence_receipt_id: str,
    next_discriminator_ids: tuple[str, ...] = (),
) -> tuple[DiagnosisState, DiagnosisTransitionReceipt]:
    after = resolve_discriminator(
        state, discriminator_id=discriminator_id, surviving_causes=surviving_causes,
        evidence_receipt_id=evidence_receipt_id, next_discriminator_ids=next_discriminator_ids,
    )
    receipt = DiagnosisTransitionReceipt(
        transition_id, state.diagnosis_id, DiagnosisTransitionKind.DISCRIMINATOR,
        state.digest, after.digest, evidence_receipt_id, discriminator_id,
    )
    return after, receipt


def establish_no_gap_with_receipt(
    state: DiagnosisState,
    *,
    transition_id: str,
    evidence_receipt_id: str,
) -> tuple[DiagnosisState, DiagnosisTransitionReceipt]:
    after = establish_no_gap(state, evidence_receipt_id=evidence_receipt_id)
    receipt = DiagnosisTransitionReceipt(
        transition_id, state.diagnosis_id, DiagnosisTransitionKind.ESTABLISH_NO_GAP,
        state.digest, after.digest, evidence_receipt_id, None,
    )
    return after, receipt
