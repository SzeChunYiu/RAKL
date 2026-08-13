from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class NavigationQuotientVerdict(str, Enum):
    EXACT_REACHABILITY_PRESERVING = "EXACT_REACHABILITY_PRESERVING"
    SOUND_OVERAPPROX_REQUIRES_LIFTING = "SOUND_OVERAPPROX_REQUIRES_LIFTING"
    EMPIRICAL_ROUTING_ONLY = "EMPIRICAL_ROUTING_ONLY"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class NavigationQuotientValidation:
    """Reachability-specific validation for a semantic/problem quotient.

    Existing TCSQ/semantic-quotient validation asks whether an abstraction is
    sufficient for a target QoI and can be reconstructed/checked. That does not
    imply that solver paths are preserved. This sidecar records the additional
    obligations needed when a quotient is used as a navigation/search space.
    """

    validation_id: str
    quotient_id: str
    semantic_validation_id: str
    source_subject_hash: str
    abstract_subject_hash: str
    target_labels_preserved: bool | None
    forward_simulation_verified: bool | None
    route_lifting_verified: bool | None
    cost_relation_verified: bool | None
    verifier_ids: Tuple[str, ...] = ()
    counterexample_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            (
                self.validation_id,
                self.quotient_id,
                self.semantic_validation_id,
                self.source_subject_hash,
                self.abstract_subject_hash,
            )
        ):
            raise ValueError("navigation quotient validation requires bound identities")
        if len(set(self.verifier_ids)) != len(self.verifier_ids):
            raise ValueError("verifier ids must be unique")
        if len(set(self.counterexample_ids)) != len(self.counterexample_ids):
            raise ValueError("counterexample ids must be unique")

    @property
    def verdict(self) -> NavigationQuotientVerdict:
        required = (
            self.target_labels_preserved,
            self.forward_simulation_verified,
            self.route_lifting_verified,
            self.cost_relation_verified,
        )
        if any(value is False for value in required):
            # A failed cost relation does not invalidate reachability itself, but
            # it invalidates use of the quotient for geometry/cost claims. Fail
            # closed here because this object is specifically the navigation
            # geometry validation receipt.
            return NavigationQuotientVerdict.REJECT
        if self.target_labels_preserved is True and self.forward_simulation_verified is True and self.route_lifting_verified is True and self.cost_relation_verified is True:
            if not self.verifier_ids:
                return NavigationQuotientVerdict.CANNOT_CHECK
            return NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING
        if self.target_labels_preserved is True and self.forward_simulation_verified is True:
            if not self.verifier_ids:
                return NavigationQuotientVerdict.CANNOT_CHECK
            return NavigationQuotientVerdict.SOUND_OVERAPPROX_REQUIRES_LIFTING
        if all(value is None for value in required):
            return NavigationQuotientVerdict.EMPIRICAL_ROUTING_ONLY
        return NavigationQuotientVerdict.CANNOT_CHECK

    @property
    def abstract_route_can_mint_solution_authority(self) -> bool:
        return False

    @property
    def abstract_no_route_can_mint_impossibility_authority(self) -> bool:
        return False

    @property
    def requires_concrete_route_revalidation(self) -> bool:
        return self.verdict is not NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING

    @property
    def supports_exact_navigation_geometry_claim(self) -> bool:
        return self.verdict is NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING
