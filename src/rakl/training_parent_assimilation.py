from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from math import isfinite
from typing import Sequence, Tuple

from .training_projection import (
    ProjectionVerdict,
    TrainingAllocationCandidate,
    TrainingProjectionSnapshot,
    assess_training_projection,
)


class ParentAssimilationVerdict(str, Enum):
    SELECT_PROPOSAL = "SELECT_PROPOSAL"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ParentLearnerValueBundle:
    """Frozen strongest-parent candidate values, higher = preferred.

    The bundle is a proposal-side routing artifact only.  It carries no
    scientific authority and cannot activate a training policy.
    """

    provider_id: str
    provider_revision: str
    model_checkpoint_hash: str
    candidate_scores: Tuple[Tuple[str, float], ...]
    frozen_before_outcome_access: bool | None
    bundle_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_training_policy_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class ParentAssimilationDecision:
    verdict: ParentAssimilationVerdict
    projection_snapshot_hash: str
    parent_bundle_hash: str
    selected_candidate_ids: Tuple[str, ...]
    rejected_candidate_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_training_policy_authority(self) -> bool:
        return False

    @property
    def claims_scheduler_efficacy(self) -> bool:
        return False


def _canonical_score_rows(rows: Sequence[Tuple[str, float]]) -> Tuple[Tuple[str, float], ...]:
    out: list[tuple[str, float]] = []
    for candidate_id, score in rows:
        if not candidate_id.strip():
            raise ValueError("parent score candidate identity cannot be blank")
        if not isfinite(float(score)):
            raise ValueError("parent learner-value score must be finite")
        out.append((candidate_id, float(score)))
    return tuple(sorted(out, key=lambda row: (row[0], row[1])))


def _bundle_hash(
    provider_id: str,
    provider_revision: str,
    model_checkpoint_hash: str,
    candidate_scores: Sequence[Tuple[str, float]],
    frozen_before_outcome_access: bool | None,
) -> str:
    payload = repr(
        (
            "RAKL_P4_PARENT_LEARNER_VALUE_BUNDLE_V1",
            provider_id,
            provider_revision,
            model_checkpoint_hash,
            _canonical_score_rows(candidate_scores),
            frozen_before_outcome_access,
        )
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def build_parent_learner_value_bundle(
    *,
    provider_id: str,
    provider_revision: str,
    model_checkpoint_hash: str,
    candidate_scores: Sequence[Tuple[str, float]],
    frozen_before_outcome_access: bool | None,
) -> ParentLearnerValueBundle:
    if not provider_id.strip() or not provider_revision.strip():
        raise ValueError("parent score provider identity and revision are required")
    if not model_checkpoint_hash.strip():
        raise ValueError("parent score bundle requires model checkpoint identity")
    rows = _canonical_score_rows(candidate_scores)
    if not rows:
        raise ValueError("parent score bundle requires at least one candidate score")
    return ParentLearnerValueBundle(
        provider_id=provider_id,
        provider_revision=provider_revision,
        model_checkpoint_hash=model_checkpoint_hash,
        candidate_scores=rows,
        frozen_before_outcome_access=frozen_before_outcome_access,
        bundle_hash=_bundle_hash(
            provider_id,
            provider_revision,
            model_checkpoint_hash,
            rows,
            frozen_before_outcome_access,
        ),
    )


def _safe_candidate(
    candidate: TrainingAllocationCandidate,
    *,
    max_forgetting_risk: float,
    max_negative_transfer_risk: float,
) -> bool:
    return (
        candidate.utility.forgetting_risk <= max_forgetting_risk
        and candidate.utility.negative_transfer_risk <= max_negative_transfer_risk
        and not candidate.confirmatory_target_leak
    )


def select_with_parent_assimilation(
    snapshot: TrainingProjectionSnapshot,
    parent_values: ParentLearnerValueBundle,
    *,
    batch_size: int,
    max_forgetting_risk: float = 0.10,
    max_negative_transfer_risk: float = 0.10,
) -> ParentAssimilationDecision:
    """Faithfully wrap a strongest-parent ranking with ORION hard gates.

    This function deliberately does not invent a new utility score.  If all
    candidates are admissible, selection is exactly the parent ordering.  RAKL
    may only veto candidates through pre-existing fail-closed projection,
    leakage, forgetting-risk and negative-transfer-risk constraints.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    for name, value in (
        ("max_forgetting_risk", max_forgetting_risk),
        ("max_negative_transfer_risk", max_negative_transfer_risk),
    ):
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0,1]")

    assessment = assess_training_projection(snapshot)
    if assessment.verdict is ProjectionVerdict.INVALID:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            assessment.reasons,
        )
    if assessment.verdict is not ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            assessment.reasons,
        )

    expected_bundle_hash = _bundle_hash(
        parent_values.provider_id,
        parent_values.provider_revision,
        parent_values.model_checkpoint_hash,
        parent_values.candidate_scores,
        parent_values.frozen_before_outcome_access,
    )
    if parent_values.bundle_hash != expected_bundle_hash:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            ("parent_value_bundle_content_hash_mismatch",),
        )
    if parent_values.frozen_before_outcome_access is None:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            ("parent_value_freeze_chronology_unknown",),
        )
    if parent_values.frozen_before_outcome_access is False:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            ("parent_values_defined_after_outcome_access",),
        )
    if parent_values.model_checkpoint_hash != snapshot.model_checkpoint_hash:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            ("parent_value_checkpoint_mismatch",),
        )

    score_ids = tuple(candidate_id for candidate_id, _ in parent_values.candidate_scores)
    if len(score_ids) != len(set(score_ids)):
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            ("parent_value_duplicate_candidate_identity",),
        )
    candidate_ids = {candidate.candidate_id for candidate in snapshot.candidates}
    score_id_set = set(score_ids)
    if score_id_set != candidate_ids:
        missing = tuple(sorted(candidate_ids - score_id_set))
        extra = tuple(sorted(score_id_set - candidate_ids))
        reasons = tuple(
            [*(f"parent_value_missing_candidate:{item}" for item in missing),
             *(f"parent_value_unknown_candidate:{item}" for item in extra)]
        )
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            (),
            reasons or ("parent_value_candidate_coverage_mismatch",),
        )

    scores = dict(parent_values.candidate_scores)
    safe: list[TrainingAllocationCandidate] = []
    rejected: list[TrainingAllocationCandidate] = []
    for candidate in snapshot.candidates:
        if _safe_candidate(
            candidate,
            max_forgetting_risk=max_forgetting_risk,
            max_negative_transfer_risk=max_negative_transfer_risk,
        ):
            safe.append(candidate)
        else:
            rejected.append(candidate)

    if len(safe) < batch_size:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_values.bundle_hash,
            (),
            tuple(sorted(item.candidate_id for item in rejected)),
            ("insufficient_candidates_after_noncompensatory_structural_veto",),
        )

    ranked = tuple(
        sorted(
            safe,
            key=lambda item: (-scores[item.candidate_id], item.candidate_id),
        )
    )
    selected = ranked[:batch_size]
    return ParentAssimilationDecision(
        ParentAssimilationVerdict.SELECT_PROPOSAL,
        snapshot.snapshot_hash,
        parent_values.bundle_hash,
        tuple(item.candidate_id for item in selected),
        tuple(sorted(item.candidate_id for item in rejected)),
        (
            "strongest_parent_order_preserved_within_structurally_admissible_set",
            "forgetting_and_negative_transfer_are_noncompensatory_vetoes",
            "proposal_only_no_training_or_scientific_authority",
        ),
    )
