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


def _phase2_cost_allows_active_default(final_receipt: Mapping[str, object] | None) -> bool:
    """Recompute the frozen <=2x E/D GPU-cost condition from admitted resources."""

    if not isinstance(final_receipt, Mapping):
        return False
    try:
        arms = final_receipt["arms"]
        e_gpu = float(arms["E_ADAPTIVE_RAKL_STRUCTURAL"]["resources"]["gpu_seconds"])
        d_gpu = float(arms["D_STATIC_RAKL_STRUCTURAL"]["resources"]["gpu_seconds"])
    except (KeyError, TypeError, ValueError):
        return False
    if d_gpu <= 0 or e_gpu < 0:
        return False
    return e_gpu / d_gpu <= 2.0


def choose_active_training_policy_from_phase2_bundle(
    *,
    final_receipt: Mapping[str, object] | None = None,
    data_manifest: Mapping[str, object] | None = None,
    assurance_by_arm: Mapping[str, Sequence[Mapping[str, object]]] | None = None,
    runtime_execution_receipt: Mapping[str, object] | None = None,
) -> TrainingPolicyDecision:
    """Canonical Paper-IV adaptive-policy activation path.

    The raw five-arm result is one necessary coordinate, not the entire authority
    subject.  The statistical/evidence bundle is independently admitted, the
    <=2x cost boundary is independently recomputed, and the external execution
    runtime must separately bind to a governed pre-outcome LUNARC runtime freeze.

    Until an actual RUNTIME_FREEZE_V1 digest is reviewed and compiled into
    :mod:`rakl.phase2_runtime_authority`, even a fully consistent positive
    synthetic/result bundle retains ``STATIC_STRUCTURAL``.  This is deliberate:
    execution reproducibility cannot be supplied by caller assertion after the
    outcome exists.
    """

    from rakl.phase2_adaptive_receipt_admission import admit_phase2_adaptive_result_bundle
    from rakl.phase2_runtime_authority import evaluate_phase2_runtime_activation

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
    if not _phase2_cost_allows_active_default(final_receipt):
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            (
                "phase2_recomputed_cost_terminal_high_cost_static_parent_retained",
                "positive_efficacy_cannot_override_frozen_cost_boundary",
            ),
        )

    runtime_gate = evaluate_phase2_runtime_activation(runtime_execution_receipt)
    if not runtime_gate.allowed:
        return TrainingPolicyDecision(
            TrainingPolicyMode.STATIC_STRUCTURAL,
            (
                "phase2_runtime_activation_gate_not_satisfied_static_parent_retained",
                *runtime_gate.reasons,
            ),
        )

    return TrainingPolicyDecision(
        TrainingPolicyMode.ADAPTIVE_STRUCTURAL,
        (
            "canonical_phase2_bundle_admitted",
            "phase2_cost_terminal_independently_recomputed",
            "phase2_runtime_freeze_and_execution_receipt_admitted",
            *admission.reasons,
            *runtime_gate.reasons,
        ),
        admission.receipt_id,
    )
