from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Sequence, Tuple

from .training_projection import (
    ProjectionVerdict,
    TrainingAllocationCandidate,
    TrainingProjectionSnapshot,
    assess_training_projection,
)


MAX_FORGETTING_RISK = 0.10
MAX_NEGATIVE_TRANSFER_RISK = 0.10


class ParentAssimilationVerdict(str, Enum):
    SELECT_PROPOSAL = "SELECT_PROPOSAL"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ParentSelectionBundle:
    """Exact frozen strongest-parent proposal order.

    The Phase-2 strongest model-aware parent owns its NLL scoring, exposure
    tie-breaking and frozen queue order. This bundle transports that exact
    proposed candidate order without asking RAKL to reconstruct or rescore it.
    It is proposal-side only and carries no authority.
    """

    provider_id: str
    provider_revision: str
    model_checkpoint_hash: str
    candidate_order: Tuple[str, ...]
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


def _canonical_candidate_order(candidate_order: Sequence[str]) -> Tuple[str, ...]:
    rows = tuple(str(candidate_id) for candidate_id in candidate_order)
    if not rows:
        raise ValueError("parent selection bundle requires at least one candidate")
    if any(not candidate_id.strip() for candidate_id in rows):
        raise ValueError("parent selection candidate identity cannot be blank")
    return rows


def _bundle_hash(
    provider_id: str,
    provider_revision: str,
    model_checkpoint_hash: str,
    candidate_order: Sequence[str],
    frozen_before_outcome_access: bool | None,
) -> str:
    payload = repr(
        (
            "RAKL_P4_PARENT_SELECTION_BUNDLE_V1",
            provider_id,
            provider_revision,
            model_checkpoint_hash,
            _canonical_candidate_order(candidate_order),
            frozen_before_outcome_access,
        )
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def build_parent_selection_bundle(
    *,
    provider_id: str,
    provider_revision: str,
    model_checkpoint_hash: str,
    candidate_order: Sequence[str],
    frozen_before_outcome_access: bool | None,
) -> ParentSelectionBundle:
    if not provider_id.strip() or not provider_revision.strip():
        raise ValueError("parent selection provider identity and revision are required")
    if not model_checkpoint_hash.strip():
        raise ValueError("parent selection bundle requires model checkpoint identity")
    order = _canonical_candidate_order(candidate_order)
    return ParentSelectionBundle(
        provider_id=provider_id,
        provider_revision=provider_revision,
        model_checkpoint_hash=model_checkpoint_hash,
        candidate_order=order,
        frozen_before_outcome_access=frozen_before_outcome_access,
        bundle_hash=_bundle_hash(
            provider_id,
            provider_revision,
            model_checkpoint_hash,
            order,
            frozen_before_outcome_access,
        ),
    )


def _safe_candidate(candidate: TrainingAllocationCandidate) -> bool:
    return (
        candidate.utility.forgetting_risk <= MAX_FORGETTING_RISK
        and candidate.utility.negative_transfer_risk <= MAX_NEGATIVE_TRANSFER_RISK
        and not candidate.confirmatory_target_leak
    )


def select_with_parent_assimilation(
    snapshot: TrainingProjectionSnapshot,
    parent_selection: ParentSelectionBundle,
    *,
    batch_size: int,
) -> ParentAssimilationDecision:
    """Stable-filter a strongest-parent proposal through frozen ORION hard gates.

    No new learner-value heuristic is defined here. For an all-safe candidate
    set, the returned order is exactly the parent's supplied order. When an
    existing noncompensatory structural gate vetoes a candidate, the relative
    order of every surviving parent candidate is preserved. The harm thresholds
    are protocol constants and cannot be weakened by callers.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    assessment = assess_training_projection(snapshot)
    if assessment.verdict is ProjectionVerdict.INVALID:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            assessment.reasons,
        )
    if assessment.verdict is not ProjectionVerdict.READY_FOR_EXPERIMENTAL_ALLOCATION:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            assessment.reasons,
        )

    expected_bundle_hash = _bundle_hash(
        parent_selection.provider_id,
        parent_selection.provider_revision,
        parent_selection.model_checkpoint_hash,
        parent_selection.candidate_order,
        parent_selection.frozen_before_outcome_access,
    )
    if parent_selection.bundle_hash != expected_bundle_hash:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            ("parent_selection_bundle_content_hash_mismatch",),
        )
    if parent_selection.frozen_before_outcome_access is None:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            ("parent_selection_freeze_chronology_unknown",),
        )
    if parent_selection.frozen_before_outcome_access is False:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.INVALID,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            ("parent_selection_defined_after_outcome_access",),
        )
    if parent_selection.model_checkpoint_hash != snapshot.model_checkpoint_hash:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            ("parent_selection_checkpoint_mismatch",),
        )

    order = parent_selection.candidate_order
    if len(order) != len(set(order)):
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            ("parent_selection_duplicate_candidate_identity",),
        )

    candidate_by_id = {candidate.candidate_id: candidate for candidate in snapshot.candidates}
    candidate_ids = set(candidate_by_id)
    order_ids = set(order)
    if order_ids != candidate_ids:
        missing = tuple(sorted(candidate_ids - order_ids))
        extra = tuple(sorted(order_ids - candidate_ids))
        reasons = tuple(
            [
                *(f"parent_selection_missing_candidate:{item}" for item in missing),
                *(f"parent_selection_unknown_candidate:{item}" for item in extra),
            ]
        )
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            (),
            reasons or ("parent_selection_candidate_coverage_mismatch",),
        )

    selected: list[str] = []
    rejected: list[str] = []
    for candidate_id in order:
        candidate = candidate_by_id[candidate_id]
        if _safe_candidate(candidate):
            if len(selected) < batch_size:
                selected.append(candidate_id)
        else:
            rejected.append(candidate_id)

    safe_count = len(snapshot.candidates) - len(rejected)
    if safe_count < batch_size:
        return ParentAssimilationDecision(
            ParentAssimilationVerdict.CANNOT_CHECK,
            snapshot.snapshot_hash,
            parent_selection.bundle_hash,
            (),
            tuple(rejected),
            ("insufficient_candidates_after_noncompensatory_structural_veto",),
        )

    return ParentAssimilationDecision(
        ParentAssimilationVerdict.SELECT_PROPOSAL,
        snapshot.snapshot_hash,
        parent_selection.bundle_hash,
        tuple(selected),
        tuple(rejected),
        (
            "strongest_parent_relative_order_preserved_exactly",
            "forgetting_and_negative_transfer_are_noncompensatory_vetoes",
            "frozen_harm_thresholds:forgetting<=0.10;negative_transfer<=0.10",
            "proposal_only_no_training_or_scientific_authority",
        ),
    )
