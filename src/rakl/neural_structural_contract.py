"""Preregistration contracts for neural TCSQ and directional witness learning.

The quotient objective (irrelevant distinctions) and witness objective
(directional transport/applicability) are typed separately.  A symmetric metric
cannot be declared sufficient for genuinely asymmetric witness panels.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DirectionalPairPanel:
    """Balanced ordered panel containing both directions of each unordered pair.

    The analytic symmetric-classifier ceiling below is valid only under this
    registered panel construction. If an experiment samples directions with
    unequal weights it must compute the appropriate weighted ceiling instead.
    """

    unordered_pair_count: int
    asymmetric_pair_count: int
    contains_both_directions_once: bool = True

    def __post_init__(self) -> None:
        if self.unordered_pair_count <= 0 or not 0 <= self.asymmetric_pair_count <= self.unordered_pair_count:
            raise ValueError("invalid pair-panel counts")
        if not self.contains_both_directions_once:
            raise ValueError("v1 analytic ceiling requires exactly both ordered directions per pair")

    @property
    def symmetric_classifier_accuracy_ceiling(self) -> float:
        return 1.0 - self.asymmetric_pair_count / (2.0 * self.unordered_pair_count)


@dataclass(frozen=True)
class NeuralStructuralPreregistration:
    preregistration_id: str
    quotient_objective_id: str
    witness_objective_id: str
    witness_scorer_is_symmetric: bool
    directional_panel: DirectionalPairPanel
    protected_coordinate_loss_id: str
    non_preservation_loss_id: str
    boundary_trap_panel_hash: str
    fresh_structural_ood_split_hash: str
    matched_compute_budget_hash: str
    comparator_ids: tuple[str, ...]
    matched_information_augmentation_control_id: str

    def __post_init__(self) -> None:
        required = (
            self.preregistration_id,
            self.quotient_objective_id,
            self.witness_objective_id,
            self.protected_coordinate_loss_id,
            self.non_preservation_loss_id,
            self.boundary_trap_panel_hash,
            self.fresh_structural_ood_split_hash,
            self.matched_compute_budget_hash,
            self.matched_information_augmentation_control_id,
        )
        if any(not x for x in required):
            raise ValueError("neural structural preregistration is incomplete")
        if self.directional_panel.asymmetric_pair_count and self.witness_scorer_is_symmetric:
            raise ValueError("symmetric witness scorer cannot represent registered asymmetric pairs")
        if len(self.comparator_ids) < 3:
            raise ValueError("require multiple strong parent controls, not only a weak baseline")
        if len(self.comparator_ids) != len(set(self.comparator_ids)) or any(not item for item in self.comparator_ids):
            raise ValueError("comparator identities must be unique and nonempty")
        if self.quotient_objective_id == self.witness_objective_id:
            raise ValueError("quotient and witness objectives must remain typed separately")

    @property
    def grants_scientific_authority(self) -> bool:
        return False
