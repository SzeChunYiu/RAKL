"""Proposal-only root-coordinate preservation receipt (benchmark object).

A cross-Millennium method audit reports one recurring research-process shape: a
locally meaningful, mathematically valid surrogate or lemma is not the
root-critical quantity until an explicit faithfulness/preservation interface is
proved. Agents can therefore spend cycles optimizing a locally attractive
coordinate before testing whether it is root-relevant.

This module freezes that binding *before* expensive candidate search. It is
search control only. It grants no theorem, proof, tool, gluing, novelty or
framework authority, and it is not required for free-form brainstorming.

Composition versus new primitive
--------------------------------
Issue #124 asks whether existing v3 surfaces suffice. Three of the receipt's
fields have no home:

* :class:`~rakl.problem_fibre.ProblemAtom` carries ``structural_coordinates`` as
  a flat label tuple. It can name a root and a surrogate coordinate; it cannot
  express the *directed* bridge between them, nor per-edge proof status.
* :class:`~rakl.problem_fibre.GluingReport` is local-to-global **solution
  assembly** and exposes ``grants_solution_authority``. Reusing it here would
  both act at the wrong stage — the representation-selection failure happens
  earlier — and leak solution-authority semantics into a pre-candidate
  search-control object, which the issue explicitly forbids.
* :class:`~rakl.failure_lattice.DifferenceWitness` is the closest analogue and
  contributes the ``cheapest_repeat_failure_test`` idiom reused below, but it is
  structurally bound to ``prior_failure_ids``. The moment this receipt targets is
  usually *before* any failure exists, so requiring a prior failure would make
  the object unusable exactly when it is needed.

So this is a new object, composed with the existing ones rather than replacing
them: coordinates stay :class:`ProblemAtom` structural coordinates, prior
failures are referenced by id, and gluing is deliberately not involved.

What is actually checked
------------------------
Not a form. Three decidable checks, all on supplied observations:

1. **State-projection congruence** (the ``state_projection_congruence``
   coordinate added in the issue comment). Two registered states with the *same*
   projected surrogate state and *different* registered downstream outcomes
   refute the projection: ``equal_projected_state /
   different_registered_downstream_outcome``.
2. **Non-compensatory obligations.** An obligation declared non-compensatory may
   not be discharged by surrogate evidence alone; surrogate gains never pay for
   it.
3. **Unproved interface edges.** While any bridge edge is unproved, the receipt
   cannot report that the surrogate advances the root. That is the typed
   interface residual the issue asks for, not a failure.

An absent hostile world is never evidence of faithfulness. Zero registered
observations yield ``CANNOT_CHECK``, never congruence — that regression risk is
named in the issue and is asserted in the frozen worlds.

This module performs no network access and no writes.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple

RECEIPT_SCHEMA_VERSION = "root-coordinate-preservation-receipt-v1"


class EdgeProofStatus(str, Enum):
    """Proof status of one bridge edge.

    ``UNSPECIFIED`` fails closed into the unproved class: an unstated proof
    status is not a proof.
    """

    PROVED = "PROVED"
    CONDITIONAL = "CONDITIONAL"
    UNPROVED = "UNPROVED"
    UNSPECIFIED = "UNSPECIFIED"


#: Only a discharged edge lets the bridge be reported as locally congruent.
#: ``CONDITIONAL`` is deliberately excluded: an edge proved under an unverified
#: hypothesis is an open interface, not a closed one.
_DISCHARGED_EDGE_STATUSES = frozenset({EdgeProofStatus.PROVED})


class CoordinateAuthority(str, Enum):
    """Authority of a source or target coordinate at receipt time."""

    ESTABLISHED = "ESTABLISHED"
    CONDITIONAL = "CONDITIONAL"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    UNSPECIFIED = "UNSPECIFIED"


class PreservationVerdict(str, Enum):
    """Outcome of auditing a surrogate-to-root bridge.

    ``BRIDGE_LOCALLY_CONGRUENT``
        checked: no congruence violation on the registered observations and every
        bridge edge discharged. Search control only — never theorem authority,
        and never a claim that no hostile world exists.
    ``INTERFACE_UNPROVED``
        checked: no violation found, but at least one interface edge is open.
        This is the typed "local success, root still open" residual, not a defect.
    ``SURROGATE_BRIDGE_REFUTED``
        checked and defective: a congruence violation, or a non-compensatory
        obligation discharged by surrogate evidence alone.
    ``CANNOT_CHECK``
        not checked: no registered observations, or a malformed receipt. An
        unavailable hostile world is never evidence that a surrogate is faithful.
    """

    BRIDGE_LOCALLY_CONGRUENT = "BRIDGE_LOCALLY_CONGRUENT"
    INTERFACE_UNPROVED = "INTERFACE_UNPROVED"
    SURROGATE_BRIDGE_REFUTED = "SURROGATE_BRIDGE_REFUTED"
    CANNOT_CHECK = "CANNOT_CHECK"


def canonical_json_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BridgeEdge:
    """One directed step of the surrogate-to-root interface map."""

    edge_id: str
    source_coordinate: str
    target_coordinate: str
    interface_map: str
    proof_status: EdgeProofStatus
    enabling_assumptions: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.edge_id or not self.source_coordinate or not self.target_coordinate:
            raise ValueError("bridge edge requires edge_id, source and target coordinates")
        if not self.interface_map:
            raise ValueError("bridge edge requires an explicit interface map")

    @property
    def is_discharged(self) -> bool:
        return self.proof_status in _DISCHARGED_EDGE_STATUSES


@dataclass(frozen=True)
class Obligation:
    """A root obligation, and whether surrogate gains may pay for it."""

    obligation_id: str
    description: str
    non_compensatory: bool
    discharged_by_surrogate_evidence_only: bool = False

    def __post_init__(self) -> None:
        if not self.obligation_id:
            raise ValueError("obligation requires an obligation_id")


@dataclass(frozen=True)
class RegisteredStateObservation:
    """One registered state, its projected surrogate state, and its outcome.

    ``projected_state`` is the surrogate/compressed coordinate the agent proposes
    to optimize; ``registered_downstream_outcome`` is the root-facing result that
    the projection claims to determine.
    """

    state_id: str
    projected_state: str
    registered_downstream_outcome: str

    def __post_init__(self) -> None:
        if not self.state_id or not self.projected_state:
            raise ValueError("state observation requires state_id and projected_state")
        if not self.registered_downstream_outcome:
            raise ValueError("state observation requires a registered downstream outcome")


@dataclass(frozen=True)
class RootCoordinatePreservationReceipt:
    """Frozen before treating a surrogate as progress toward a root obligation."""

    receipt_id: str
    root_claim_id: str
    root_coordinate: str
    surrogate_coordinate: str
    bridge_edges: Tuple[BridgeEdge, ...]
    obligations: Tuple[Obligation, ...]
    known_disanalogies: Tuple[str, ...]
    source_authority: CoordinateAuthority
    target_authority: CoordinateAuthority
    cheapest_hostile_world: str
    registered_observations: Tuple[RegisteredStateObservation, ...]
    reverification_triggers: Tuple[str, ...]
    prior_failure_ids: Tuple[str, ...] = ()
    schema_version: str = RECEIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.receipt_id or not self.root_claim_id:
            raise ValueError("preservation receipt requires receipt_id and root_claim_id")
        if not self.root_coordinate or not self.surrogate_coordinate:
            raise ValueError("preservation receipt requires root and surrogate coordinates")
        if self.root_coordinate == self.surrogate_coordinate:
            raise ValueError("a coordinate cannot be its own surrogate")
        if not self.cheapest_hostile_world:
            # The issue makes this field load-bearing: a receipt that cannot name
            # the world where the surrogate looks good and the root does not has
            # not done the thinking the receipt exists to force.
            raise ValueError("preservation receipt requires a cheapest hostile world")

    @property
    def unproved_interface_edge_ids(self) -> Tuple[str, ...]:
        return tuple(edge.edge_id for edge in self.bridge_edges if not edge.is_discharged)

    @property
    def enabling_assumptions(self) -> Tuple[str, ...]:
        seen: list[str] = []
        for edge in self.bridge_edges:
            for assumption in edge.enabling_assumptions:
                if assumption not in seen:
                    seen.append(assumption)
        return tuple(seen)

    def content(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "root_claim_id": self.root_claim_id,
            "root_coordinate": self.root_coordinate,
            "surrogate_coordinate": self.surrogate_coordinate,
            "bridge_edges": [
                {
                    "edge_id": edge.edge_id,
                    "source_coordinate": edge.source_coordinate,
                    "target_coordinate": edge.target_coordinate,
                    "interface_map": edge.interface_map,
                    "proof_status": edge.proof_status.value,
                    "enabling_assumptions": list(edge.enabling_assumptions),
                }
                for edge in self.bridge_edges
            ],
            "obligations": [
                {
                    "obligation_id": item.obligation_id,
                    "description": item.description,
                    "non_compensatory": item.non_compensatory,
                    "discharged_by_surrogate_evidence_only": (
                        item.discharged_by_surrogate_evidence_only
                    ),
                }
                for item in self.obligations
            ],
            "known_disanalogies": list(self.known_disanalogies),
            "source_authority": self.source_authority.value,
            "target_authority": self.target_authority.value,
            "cheapest_hostile_world": self.cheapest_hostile_world,
            "registered_observations": [
                {
                    "state_id": item.state_id,
                    "projected_state": item.projected_state,
                    "registered_downstream_outcome": item.registered_downstream_outcome,
                }
                for item in self.registered_observations
            ],
            "reverification_triggers": list(self.reverification_triggers),
            "prior_failure_ids": list(self.prior_failure_ids),
        }

    def document(self) -> Mapping[str, Any]:
        document = dict(self.content())
        document["receipt_canonical_sha256"] = canonical_json_sha256(self.content())
        return document


@dataclass(frozen=True)
class PreservationReport:
    """Result of auditing one receipt. Search control only."""

    verdict: PreservationVerdict
    reasons: Tuple[str, ...]
    congruence_violations: Tuple[Tuple[str, str], ...]
    unproved_interface_edge_ids: Tuple[str, ...]

    @property
    def advances_root_claim(self) -> bool:
        """Never true. A preservation receipt is not progress on the root claim.

        Congruence on the registered observations is evidence about a projection,
        not about the root obligation. This property exists so that the negative
        is explicit and testable rather than merely intended.
        """

        return False

    @property
    def surrogate_may_be_prioritized(self) -> bool:
        """Whether search may keep investing in the surrogate coordinate.

        A refuted bridge stops the investment. An open interface does not: an
        unproved edge is a residual to close, not a reason to abandon a
        coordinate — that is the false-reject the issue warns about.
        """

        return self.verdict is not PreservationVerdict.SURROGATE_BRIDGE_REFUTED


def find_congruence_violations(
    observations: Tuple[RegisteredStateObservation, ...],
) -> Tuple[Tuple[str, str], ...]:
    """Return state-id pairs sharing a projection but not a downstream outcome.

    This is the ``equal_projected_state / different_registered_downstream_outcome``
    world: the projection erases a distinction the root obligation registers.
    """

    by_projection: dict[str, list[RegisteredStateObservation]] = defaultdict(list)
    for observation in observations:
        by_projection[observation.projected_state].append(observation)

    violations: list[Tuple[str, str]] = []
    for group in by_projection.values():
        for index, left in enumerate(group):
            for right in group[index + 1 :]:
                if left.registered_downstream_outcome != right.registered_downstream_outcome:
                    violations.append((left.state_id, right.state_id))
    return tuple(violations)


def audit_root_coordinate_preservation(
    receipt: RootCoordinatePreservationReceipt,
) -> PreservationReport:
    """Audit a surrogate-to-root bridge before expensive candidate search."""

    reasons: list[str] = []
    unproved = receipt.unproved_interface_edge_ids

    if not receipt.bridge_edges:
        return PreservationReport(
            verdict=PreservationVerdict.CANNOT_CHECK,
            reasons=("no_bridge_edges_declared",),
            congruence_violations=(),
            unproved_interface_edge_ids=(),
        )

    violations = find_congruence_violations(receipt.registered_observations)

    compensated = tuple(
        item.obligation_id
        for item in receipt.obligations
        if item.non_compensatory and item.discharged_by_surrogate_evidence_only
    )
    for obligation_id in compensated:
        reasons.append(f"non_compensatory_obligation_discharged_by_surrogate:{obligation_id}")

    if violations:
        for left, right in violations:
            reasons.append(
                "equal_projected_state_different_registered_downstream_outcome:"
                f"{left}|{right}"
            )

    if reasons:
        return PreservationReport(
            verdict=PreservationVerdict.SURROGATE_BRIDGE_REFUTED,
            reasons=tuple(reasons),
            congruence_violations=violations,
            unproved_interface_edge_ids=unproved,
        )

    if not receipt.registered_observations:
        # An unavailable hostile world is not evidence of faithfulness.
        return PreservationReport(
            verdict=PreservationVerdict.CANNOT_CHECK,
            reasons=("no_registered_observations_to_test_the_projection",),
            congruence_violations=(),
            unproved_interface_edge_ids=unproved,
        )

    if unproved:
        return PreservationReport(
            verdict=PreservationVerdict.INTERFACE_UNPROVED,
            reasons=tuple(f"interface_edge_not_discharged:{edge_id}" for edge_id in unproved),
            congruence_violations=(),
            unproved_interface_edge_ids=unproved,
        )

    return PreservationReport(
        verdict=PreservationVerdict.BRIDGE_LOCALLY_CONGRUENT,
        reasons=(),
        congruence_violations=(),
        unproved_interface_edge_ids=(),
    )
