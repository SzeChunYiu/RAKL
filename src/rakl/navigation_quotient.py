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


@dataclass(frozen=True)
class CompositeNavigationQuotientValidation:
    """Derived validation for a CHAIN of navigation quotients (audit I4).

    Forward simulations and route liftings compose, so the safe composite
    theorem is: all components EXACT_REACHABILITY_PRESERVING => the composite
    is EXACT_REACHABILITY_PRESERVING; all components at least sound
    overapproximations => the composite is a sound overapproximation that
    still requires lifting. Anything weaker fails closed. The chain is bound
    by subject hashes: each component must abstract exactly the subject the
    previous component produced. Composites are derived, never self-declared.
    """

    composite_id: str
    components: Tuple[NavigationQuotientValidation, ...]

    def __post_init__(self) -> None:
        if not self.composite_id:
            raise ValueError("composite navigation quotient validation requires an identity")
        if len(self.components) < 2:
            raise ValueError("composite navigation quotient validation requires at least two components")
        for first, second in zip(self.components, self.components[1:]):
            if first.abstract_subject_hash != second.source_subject_hash:
                raise ValueError(
                    "subject hash mismatch in navigation quotient chain: "
                    f"{first.validation_id!r} abstracts to {first.abstract_subject_hash!r} but "
                    f"{second.validation_id!r} quotients {second.source_subject_hash!r} (audit I4)"
                )

    @property
    def source_subject_hash(self) -> str:
        return self.components[0].source_subject_hash

    @property
    def abstract_subject_hash(self) -> str:
        return self.components[-1].abstract_subject_hash

    @property
    def verdict(self) -> NavigationQuotientVerdict:
        verdicts = tuple(component.verdict for component in self.components)
        if any(v is NavigationQuotientVerdict.REJECT for v in verdicts):
            return NavigationQuotientVerdict.REJECT
        if all(v is NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING for v in verdicts):
            return NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING
        sound = {
            NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING,
            NavigationQuotientVerdict.SOUND_OVERAPPROX_REQUIRES_LIFTING,
        }
        if all(v in sound for v in verdicts):
            return NavigationQuotientVerdict.SOUND_OVERAPPROX_REQUIRES_LIFTING
        # EMPIRICAL_ROUTING_ONLY or CANNOT_CHECK anywhere in the chain: no
        # composite soundness theorem applies; fail closed.
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


def compose_navigation_quotient_validations(
    first: NavigationQuotientValidation | CompositeNavigationQuotientValidation,
    second: NavigationQuotientValidation | CompositeNavigationQuotientValidation,
    *,
    composite_id: str,
) -> CompositeNavigationQuotientValidation:
    """Compose two (possibly already composite) quotient validations (audit I4)."""
    left = first.components if isinstance(first, CompositeNavigationQuotientValidation) else (first,)
    right = second.components if isinstance(second, CompositeNavigationQuotientValidation) else (second,)
    return CompositeNavigationQuotientValidation(composite_id, left + right)
