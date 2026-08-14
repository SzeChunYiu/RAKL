from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class TrainingPolicyMode(str, Enum):
    """Active training-policy mode, separate from scientific authority."""

    STATIC_STRUCTURAL = "STATIC_STRUCTURAL"
    ADAPTIVE_STRUCTURAL = "ADAPTIVE_STRUCTURAL"


@dataclass(frozen=True)
class AdaptivePolicyAuthorization:
    """External evidence needed before adaptive allocation can become active default.

    The scheduler being evaluated cannot mint this object from its own telemetry.
    This is training-policy authority only and grants no scientific authority.
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
    """Choose the active ORION training policy fail-safely.

    Static structural allocation is the authoritative default.  Merely having a
    learner-state vector or an adaptive scheduler implementation does not authorize
    adaptive training.  Adaptive becomes active only after a fresh external receipt
    establishes the preregistered E-D residual, the strongest-parent residual, hard
    safety gates and full selection/training/probe overhead.

    Negative, null, underpowered and RESOURCE_BLOCKED receipts are therefore useful
    RSHEA evidence but never active failed dependencies: they retain the static parent.
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
