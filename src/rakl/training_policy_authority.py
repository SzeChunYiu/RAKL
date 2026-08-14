from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple


class TrainingPolicyMode(str, Enum):
    """Active training-policy mode, separate from scientific authority."""

    STATIC_STRUCTURAL = "STATIC_STRUCTURAL"
    ADAPTIVE_STRUCTURAL = "ADAPTIVE_STRUCTURAL"


@dataclass(frozen=True)
class AdaptivePolicyAuthorization:
    """Legacy external evidence summary used by the v1 policy chooser.

    This type is retained for compatibility and negative-history tests.  New
    production activation must use choose_active_training_policy_from_phase2_bundle,
    which independently admits the frozen Phase-2 evidence bundle instead of
    trusting caller-asserted summary booleans.
    """

    receipt_id: str
    terminal: str
    evaluated_subject_hash: str
    evidence_ids: Tuple[str, ...]
    fresh_assurance: bool
    strongest_parent_residual: bool
    hard_harms_pass: bool
    full_overhead_accounted: bool

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class TrainingPolicyDecision:
    mode: TrainingPolicyMode
    reasons: Tuple[str, ...]
    authorization_receipt_id: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_REQUIRED_ADAPTIVE_TERMINAL = "ADAPTIVE_RESIDUAL_SUPPORTED"


def choose_active_training_policy(
    authorization: AdaptivePolicyAuthorization | None = None,
) -> TrainingPolicyDecision:
    """Legacy v1 chooser retained byte-semantically for compatibility.

    Static structural allocation is the authoritative default.  This historical
    entry point accepts a summarized AdaptivePolicyAuthorization and therefore is
    not the canonical admission path for new adaptive activation.
    """

    if authorization is None:
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            ("no_adaptive_residual_authorization_static_parent_retained",),
        )
    if not authorization.receipt_id.strip() or not authorization.evaluated_subject_hash.strip():
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            ("adaptive_authorization_identity_invalid_static_parent_retained",),
        )
    if not authorization.evidence_ids or any(not item.strip() for item in authorization.evidence_ids):
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            ("adaptive_authorization_evidence_missing_static_parent_retained",),
        )
    gates = (
        authorization.terminal == _REQUIRED_ADAPTIVE_TERMINAL,
        authorization.fresh_assurance,
        authorization.strongest_parent_residual,
        authorization.hard_harms_pass,
        authorization.full_overhead_accounted,
    )
    if not all(gates):
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            (
                "adaptive_promotion_gate_not_satisfied_static_parent_retained",
                f"observed_terminal:{authorization.terminal}",
            ),
        )
    return TrainingPolicyDecision(
        TrainingPolicyMode.ADAPTIVE_STRUCTURAL,
        (
            "fresh_adaptive_residual_supported",
            "strongest_parent_residual_supported",
            "hard_harms_and_full_overhead_passed",
        ),
        authorization.receipt_id,
    )


def choose_active_training_policy_from_phase2_bundle(
    *,
    final_receipt: Mapping[str, object] | None = None,
    data_manifest: Mapping[str, object] | None = None,
    assurance_by_arm: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
) -> TrainingPolicyDecision:
    """Canonical v2 Paper-IV policy activation path.

    Unlike the legacy summarized authorization object, this entry point derives
    the activation gates from the frozen Phase-2 artifact bundle.  Missing,
    malformed, stale or nonpositive evidence always retains STATIC_STRUCTURAL.
    """

    from rakl.phase2_adaptive_receipt_admission import admit_phase2_adaptive_result_bundle

    admission = admit_phase2_adaptive_result_bundle(
        final_receipt=final_receipt,
        data_manifest=data_manifest,
        assurance_by_arm=assurance_by_arm,
    )
    if not admission.admitted:
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            (
                "canonical_phase2_admission_not_satisfied_static_parent_retained",
                *admission.reasons,
            ),
        )
    return TrainingPolicyDecision(
        TrainingPolicyMode.ADAPTIVE_STRUCTURAL,
        (
            "canonical_phase2_bundle_admitted",
            *admission.reasons,
        ),
        admission.receipt_id,
    )
