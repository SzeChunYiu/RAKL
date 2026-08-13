from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Tuple

from .vtg_hardening import ValidationEvidence, ValidationVerdict


def _hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


class NavigationQuotientVerdict(str, Enum):
    EXACT_REACHABILITY_PRESERVING = "EXACT_REACHABILITY_PRESERVING"
    SOUND_OVERAPPROX_REQUIRES_LIFTING = "SOUND_OVERAPPROX_REQUIRES_LIFTING"
    EMPIRICAL_ROUTING_ONLY = "EMPIRICAL_ROUTING_ONLY"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class NavigationQuotientValidation:
    """Reachability-specific validation for a semantic/problem quotient.

    All theorem-like coordinates are provenance-bearing validation evidence,
    never Booleans. The semantic quotient and its navigation validation remain
    proposal/routing objects and grant no mathematical authority.
    """

    validation_id: str
    quotient_id: str
    source_subject_hash: str
    abstract_subject_hash: str
    validation_subject_hash: str
    semantic_validation_evidence: ValidationEvidence
    target_preservation_evidence: ValidationEvidence | None = None
    forward_simulation_evidence: ValidationEvidence | None = None
    route_lifting_evidence: ValidationEvidence | None = None
    cost_relation_evidence: ValidationEvidence | None = None
    counterexample_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            (
                self.validation_id,
                self.quotient_id,
                self.source_subject_hash,
                self.abstract_subject_hash,
                self.validation_subject_hash,
            )
        ):
            raise ValueError("navigation quotient validation requires bound identities")
        if len(set(self.counterexample_ids)) != len(self.counterexample_ids):
            raise ValueError("counterexample ids must be unique")
        all_evidence = (
            self.semantic_validation_evidence,
            self.target_preservation_evidence,
            self.forward_simulation_evidence,
            self.route_lifting_evidence,
            self.cost_relation_evidence,
        )
        for evidence in all_evidence:
            if evidence is not None and evidence.subject_hash != self.validation_subject_hash:
                raise ValueError("navigation quotient evidence subject mismatch")
        if self.semantic_validation_evidence.claim_kind != "SEMANTIC_QUOTIENT_VALIDATION":
            raise ValueError("semantic quotient validation evidence claim kind mismatch")
        expected = {
            "target_preservation_evidence": (self.target_preservation_evidence, "NAVIGATION_TARGET_PRESERVATION"),
            "forward_simulation_evidence": (self.forward_simulation_evidence, "NAVIGATION_FORWARD_SIMULATION"),
            "route_lifting_evidence": (self.route_lifting_evidence, "NAVIGATION_ROUTE_LIFTING"),
            "cost_relation_evidence": (self.cost_relation_evidence, "NAVIGATION_COST_RELATION"),
        }
        for label, (evidence, kind) in expected.items():
            if evidence is not None and evidence.claim_kind != kind:
                raise ValueError(f"{label} claim kind mismatch")

    @property
    def semantic_validation_id(self) -> str:
        return self.semantic_validation_evidence.evidence_id

    @staticmethod
    def _state(evidence: ValidationEvidence | None) -> bool | None:
        if evidence is None:
            return None
        if evidence.verdict is ValidationVerdict.PASS:
            return True
        if evidence.verdict is ValidationVerdict.FAIL:
            return False
        return None

    @property
    def verdict(self) -> NavigationQuotientVerdict:
        semantic = self._state(self.semantic_validation_evidence)
        target = self._state(self.target_preservation_evidence)
        forward = self._state(self.forward_simulation_evidence)
        lifting = self._state(self.route_lifting_evidence)
        cost = self._state(self.cost_relation_evidence)

        if semantic is False or any(value is False for value in (target, forward, lifting, cost)):
            return NavigationQuotientVerdict.REJECT
        if semantic is None:
            return NavigationQuotientVerdict.CANNOT_CHECK
        if all(value is True for value in (target, forward, lifting, cost)):
            return NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING
        if target is True and forward is True:
            return NavigationQuotientVerdict.SOUND_OVERAPPROX_REQUIRES_LIFTING
        if all(value is None for value in (target, forward, lifting, cost)):
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

    @property
    def subject_hash(self) -> str:
        return _hash(
            {
                "schema": "orion.navigation-quotient-validation.v2",
                "quotient_id": self.quotient_id,
                "source_subject_hash": self.source_subject_hash,
                "abstract_subject_hash": self.abstract_subject_hash,
                "validation_subject_hash": self.validation_subject_hash,
            }
        )
