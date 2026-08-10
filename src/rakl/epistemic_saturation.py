from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import hashlib
import json
from typing import Iterable


class SaturationStatus(str, Enum):
    OPEN = "OPEN"
    BOUNDED_SATURATED = "BOUNDED_SATURATED"
    INVALID_BASIS = "INVALID_BASIS"


@dataclass(frozen=True)
class SaturationBasis:
    """Frozen semantics for deciding whether substantive epistemic growth has stopped.

    Saturation is meaningful only relative to a fixed scope, identity policy, route
    family, novelty policy, evidence policy and freshness horizon.  Changing any of
    these coordinates changes the question and invalidates a longitudinal flatness
    comparison rather than manufacturing a new saturation claim.
    """

    basis_id: str
    scope: str
    identity_policy_id: str
    route_family_version: str
    novelty_policy_id: str
    evidence_policy_id: str

    def __post_init__(self) -> None:
        if any(
            not value.strip()
            for value in (
                self.basis_id,
                self.scope,
                self.identity_policy_id,
                self.route_family_version,
                self.novelty_policy_id,
                self.evidence_policy_id,
            )
        ):
            raise ValueError("all saturation-basis coordinates are required")

    @property
    def fingerprint(self) -> str:
        payload = {
            "basis_id": self.basis_id,
            "scope": self.scope,
            "identity_policy_id": self.identity_policy_id,
            "route_family_version": self.route_family_version,
            "novelty_policy_id": self.novelty_policy_id,
            "evidence_policy_id": self.evidence_policy_id,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EpistemicGrowthVector:
    """Non-compensatory marginal knowledge growth in one research/review round.

    Every coordinate records a scientifically meaningful state change.  Negative or
    adversarial findings count as growth because they narrow the admissible theory
    space.  Representation-only edits are deliberately excluded and recorded on the
    round instead, so rewriting or ontology bookkeeping cannot reset saturation.
    """

    mechanisms_added: int = 0
    derivations_added: int = 0
    independent_evidence_roots_added: int = 0
    contradictions_or_counterexamples_added: int = 0
    negative_results_added: int = 0
    novelty_boundary_updates: int = 0
    assumption_scope_updates: int = 0
    unresolved_fiber_updates: int = 0
    discovery_route_updates: int = 0

    def __post_init__(self) -> None:
        values = (
            self.mechanisms_added,
            self.derivations_added,
            self.independent_evidence_roots_added,
            self.contradictions_or_counterexamples_added,
            self.negative_results_added,
            self.novelty_boundary_updates,
            self.assumption_scope_updates,
            self.unresolved_fiber_updates,
            self.discovery_route_updates,
        )
        if min(values) < 0:
            raise ValueError("epistemic-growth coordinates cannot be negative")

    @property
    def total(self) -> int:
        return sum(
            (
                self.mechanisms_added,
                self.derivations_added,
                self.independent_evidence_roots_added,
                self.contradictions_or_counterexamples_added,
                self.negative_results_added,
                self.novelty_boundary_updates,
                self.assumption_scope_updates,
                self.unresolved_fiber_updates,
                self.discovery_route_updates,
            )
        )

    @property
    def completely_flat(self) -> bool:
        return self.total == 0


@dataclass(frozen=True)
class SaturationRound:
    round_id: str
    basis_fingerprint: str
    growth: EpistemicGrowthVector
    bounded_discovery_closed: bool
    route_coverage_stable: bool
    omission_audit_passed: bool
    nearest_work_audit_passed: bool
    freshness_cutoff: str
    blocking_fibers: tuple[str, ...] = ()
    representation_only_changes: int = 0

    def __post_init__(self) -> None:
        if not self.round_id.strip() or not self.basis_fingerprint.strip():
            raise ValueError("saturation round identity and basis fingerprint are required")
        date.fromisoformat(self.freshness_cutoff)
        if self.representation_only_changes < 0:
            raise ValueError("representation_only_changes cannot be negative")
        if any(not fiber.strip() for fiber in self.blocking_fibers):
            raise ValueError("blocking fiber ids cannot be empty")


@dataclass(frozen=True)
class SaturationReport:
    status: SaturationStatus
    basis_fingerprint: str
    evaluated_round_ids: tuple[str, ...]
    consecutive_flat_rounds: int
    freshness_cutoff: str | None
    reasons: tuple[str, ...]

    @property
    def absolute_complete(self) -> bool:
        """Unrestricted open-world completeness is never represented positively."""
        return False


def audit_bounded_epistemic_saturation(
    rounds: Iterable[SaturationRound],
    *,
    basis: SaturationBasis,
    required_consecutive_flat_rounds: int = 2,
    required_freshness_cutoff: str | None = None,
) -> SaturationReport:
    """Return a bounded saturation certificate only after repeated substantive flatness.

    The final ``required_consecutive_flat_rounds`` must all be substantively flat and
    must independently satisfy discovery, audit, route-stability, freshness and
    blocking-fiber obligations.  Any basis change invalidates the comparison.
    """

    if required_consecutive_flat_rounds < 1:
        raise ValueError("required_consecutive_flat_rounds must be positive")
    if required_freshness_cutoff is not None:
        required_date = date.fromisoformat(required_freshness_cutoff)
    else:
        required_date = None

    observed = tuple(rounds)
    if not observed:
        return SaturationReport(
            status=SaturationStatus.OPEN,
            basis_fingerprint=basis.fingerprint,
            evaluated_round_ids=(),
            consecutive_flat_rounds=0,
            freshness_cutoff=None,
            reasons=("no_saturation_rounds",),
        )

    if any(item.basis_fingerprint != basis.fingerprint for item in observed):
        return SaturationReport(
            status=SaturationStatus.INVALID_BASIS,
            basis_fingerprint=basis.fingerprint,
            evaluated_round_ids=tuple(item.round_id for item in observed),
            consecutive_flat_rounds=0,
            freshness_cutoff=max(item.freshness_cutoff for item in observed),
            reasons=("saturation_basis_fingerprint_changed",),
        )

    consecutive_flat = 0
    for item in reversed(observed):
        if item.growth.completely_flat:
            consecutive_flat += 1
        else:
            break

    reasons: list[str] = []
    if consecutive_flat < required_consecutive_flat_rounds:
        reasons.append("insufficient_consecutive_substantive_flat_rounds")

    tail = observed[-required_consecutive_flat_rounds:]
    if len(tail) < required_consecutive_flat_rounds:
        reasons.append("insufficient_round_count")

    for item in tail:
        if not item.bounded_discovery_closed:
            reasons.append(f"{item.round_id}:bounded_discovery_open")
        if not item.route_coverage_stable:
            reasons.append(f"{item.round_id}:route_coverage_unstable")
        if not item.omission_audit_passed:
            reasons.append(f"{item.round_id}:omission_audit_open")
        if not item.nearest_work_audit_passed:
            reasons.append(f"{item.round_id}:nearest_work_audit_open")
        if item.blocking_fibers:
            reasons.append(f"{item.round_id}:blocking_fibers_open")
        if required_date is not None and date.fromisoformat(item.freshness_cutoff) < required_date:
            reasons.append(f"{item.round_id}:freshness_cutoff_stale")

    status = SaturationStatus.BOUNDED_SATURATED if not reasons else SaturationStatus.OPEN
    return SaturationReport(
        status=status,
        basis_fingerprint=basis.fingerprint,
        evaluated_round_ids=tuple(item.round_id for item in observed),
        consecutive_flat_rounds=consecutive_flat,
        freshness_cutoff=max(item.freshness_cutoff for item in observed),
        reasons=tuple(dict.fromkeys(reasons)),
    )
