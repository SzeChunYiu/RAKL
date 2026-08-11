"""Proposal-only pre-candidate contract binding a surrogate to a root coordinate.

A cross-domain audit reports one recurring shape:

    a locally meaningful, mathematically valid surrogate or lemma
    is not the root-critical quantity

until an explicit faithfulness / preservation interface is proved.  The cost is
paid *before* the defect surfaces: expensive candidate search runs against a
coordinate that was never charged with the root obligation.

This module answers the issue's own question — whether an existing v3 object
already covers this — with **no new bridge-bookkeeping primitive**.  The parts
that are genuinely bookkeeping are already carried elsewhere and are referenced
here rather than duplicated:

* ``ProblemAtom.structural_coordinates`` already names coordinates;
* ``failure_lattice`` already preserves hostile worlds, referenced by id;
* retrieval-universe completeness is a separate object (cf. RAKL #119).

What is new, and what none of the inspected objects can express, is a
**pre-candidate congruence contract plus a collision detector**:

* :class:`~rakl.problem_fibre.GluingObstruction` detects the *dual* defect —
  same interface key, *different* assigned value.  The failure here is the
  opposite: same surrogate value, *different* root outcome.  It has no
  root-versus-surrogate distinction and no notion of a downstream outcome.
* :class:`~rakl.failure_lattice.DifferenceWitness` governs reusing a *method*
  after a prior failure.  It says nothing about whether a coordinate preserves
  what the root obligation charges.
* :class:`~rakl.bridge_composition.BridgePath` composes approximation-error
  upper bounds along a chain.  A discrete projection collision has no numeric
  error semantics for it to accumulate.
* ``structural_transfer.StructuralWitness.preserved_invariants`` takes
  preservation as a *declared input* — which is exactly the unchecked claim
  this object exists to check.

The detector is deliberately weak and says so.  Finding no collision in a bound
probe set is not a faithfulness proof; it is the absence of a counterexample in
a stated universe, and the verdict is named accordingly.  A probe set in which
no collision *could* surface is reported as uninformative rather than clean —
otherwise an empty probe set would read as a licence.  A rejection is scoped:
per AGENTS.md a prior failure is a warning, never a blacklist, so a surrogate
that collides at one scope remains available at a narrower one whose own probe
set holds.

This module performs no network, git or filesystem access, and mints no
theorem, proof, tool, gluing, novelty or framework authority.  It does not
report its own error rate: false-accept and false-reject counts are properties
of a labelled fixture corpus, not of a checker.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Tuple


RECEIPT_SCHEMA_VERSION = "root-coordinate-preservation-receipt-v1"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: A probe class must hold at least this many observed probes before a collision
#: could possibly surface in it.  Below this, silence is uninformative.
MIN_PROBES_PER_INFORMATIVE_CLASS = 2


class CoordinateAuthority(str, Enum):
    """Authority attached to a source or target coordinate.

    ``ESTABLISHED`` marks a coordinate whose status is settled in its own
    domain.  Everything else is a coordinate still under proposal, and the
    distinction exists so that a surrogate cannot inherit authority merely by
    being bridged to something authoritative.
    """

    ESTABLISHED = "ESTABLISHED"
    CONDITIONAL = "CONDITIONAL"
    PROPOSED = "PROPOSED"
    UNVERIFIED = "UNVERIFIED"


class PreservationVerdict(str, Enum):
    """Outcome of one scoped preservation check.

    ``NO_COLLISION_IN_BOUND_PROBE_SET`` is the strongest available positive
    result and is still proposal-only.  It does not say the surrogate is
    faithful; it says no counterexample appeared in the universe that was
    actually probed.

    ``PROBE_SET_UNINFORMATIVE`` is separated from the positive result on
    purpose.  An empty probe set, or one where every probe lands in its own
    class, produces no collisions for structural reasons rather than
    evidential ones, and must never read as a licence.

    ``CONTRACT_INCOMPLETE`` covers a receipt whose own required fields are
    missing — most often the cheapest hostile world, which the issue names as
    load-bearing and which therefore fails closed when absent.
    """

    NO_COLLISION_IN_BOUND_PROBE_SET = "NO_COLLISION_IN_BOUND_PROBE_SET"
    SURROGATE_REJECTED_COLLISION_WITNESSED = "SURROGATE_REJECTED_COLLISION_WITNESSED"
    PROBE_SET_UNINFORMATIVE = "PROBE_SET_UNINFORMATIVE"
    CONTRACT_INCOMPLETE = "CONTRACT_INCOMPLETE"
    CANNOT_CHECK = "CANNOT_CHECK"


def canonical_json_bytes(value: object) -> bytes:
    """Return the UTF-8 RFC-8259-compatible representation used for hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def receipt_canonical_sha256(document: Mapping[str, Any]) -> str:
    """Hash a receipt document excluding its own content-hash field."""

    subject = dict(document)
    subject.pop("receipt_canonical_sha256", None)
    return canonical_json_sha256(subject)


@dataclass(frozen=True)
class RootCoordinateProbe:
    """One observation pairing a projected surrogate state with a root outcome.

    ``registered_root_outcome`` is ``None`` when the root side was not observed.
    Such a probe is excluded from the congruence check and reported, because an
    unobserved root outcome cannot witness agreement any more than disagreement.
    """

    probe_id: str
    projected_surrogate_state: str
    registered_root_outcome: str | None
    evidence_pointer: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "projected_surrogate_state": self.projected_surrogate_state,
            "registered_root_outcome": self.registered_root_outcome,
            "evidence_pointer": self.evidence_pointer,
        }


@dataclass(frozen=True)
class CollisionWitness:
    """Two or more probes agreeing on the surrogate and disagreeing on the root.

    This is the exact shape the motivating comment names:
    ``equal_projected_state / different_registered_downstream_outcome``.
    """

    projected_surrogate_state: str
    probe_ids: Tuple[str, ...]
    divergent_root_outcomes: Tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "projected_surrogate_state": self.projected_surrogate_state,
            "probe_ids": list(self.probe_ids),
            "divergent_root_outcomes": list(self.divergent_root_outcomes),
        }


@dataclass(frozen=True)
class RootCoordinatePreservationReceipt:
    """Scoped pre-candidate contract binding a surrogate to a root coordinate.

    Frozen *before* expensive candidate generation, route promotion, or any
    claim that a local result advances the root obligation.

    ``scope_id`` and ``scope_conditions`` are what keep a rejection from
    becoming a blacklist: the verdict attaches to this coordinate *at this
    scope*, and a narrower scope is a separate receipt with its own probe set.
    """

    root_claim_id: str
    root_coordinate: str
    surrogate_or_local_coordinate: str
    scope_id: str
    bridge_map: Tuple[Tuple[str, str], ...]
    cheapest_hostile_world: str
    public_trace_event_id: str
    source_authority: CoordinateAuthority = CoordinateAuthority.UNVERIFIED
    target_authority: CoordinateAuthority = CoordinateAuthority.UNVERIFIED
    enabling_assumptions: Tuple[str, ...] = ()
    non_compensatory_obligations: Tuple[str, ...] = ()
    known_disanalogies: Tuple[str, ...] = ()
    unproved_interface_edges: Tuple[str, ...] = ()
    reverification_triggers: Tuple[str, ...] = ()
    scope_conditions: Tuple[str, ...] = ()
    probes: Tuple[RootCoordinateProbe, ...] = ()
    failure_memory_ids: Tuple[str, ...] = ()
    coverage_receipt_id: str | None = None
    evidence_pointers: Tuple[str, ...] = ()
    receipt_canonical_sha256: str = ""
    schema_version: str = field(default=RECEIPT_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "root_claim_id": self.root_claim_id,
            "root_coordinate": self.root_coordinate,
            "surrogate_or_local_coordinate": self.surrogate_or_local_coordinate,
            "scope_id": self.scope_id,
            "bridge_map": [list(pair) for pair in self.bridge_map],
            "cheapest_hostile_world": self.cheapest_hostile_world,
            "public_trace_event_id": self.public_trace_event_id,
            "source_authority": self.source_authority.value,
            "target_authority": self.target_authority.value,
            "enabling_assumptions": list(self.enabling_assumptions),
            "non_compensatory_obligations": list(self.non_compensatory_obligations),
            "known_disanalogies": list(self.known_disanalogies),
            "unproved_interface_edges": list(self.unproved_interface_edges),
            "reverification_triggers": list(self.reverification_triggers),
            "scope_conditions": list(self.scope_conditions),
            "probes": [probe.to_dict() for probe in self.probes],
            "failure_memory_ids": list(self.failure_memory_ids),
            "coverage_receipt_id": self.coverage_receipt_id,
            "evidence_pointers": list(self.evidence_pointers),
            "receipt_canonical_sha256": self.receipt_canonical_sha256,
            "proves_surrogate_faithfulness": False,
            "claims_probe_universe_complete": False,
            "grants_theorem_authority": False,
            "grants_proof_authority": False,
            "grants_tool_authority": False,
            "grants_gluing_authority": False,
            "grants_novelty_authority": False,
            "grants_framework_authority": False,
        }

    def with_content_hash(self) -> "RootCoordinatePreservationReceipt":
        return replace(
            self, receipt_canonical_sha256=receipt_canonical_sha256(self.to_dict())
        )


@dataclass(frozen=True)
class PreservationReport:
    """Scoped conclusion.  No constructor argument sets the verdict."""

    verdict: PreservationVerdict
    reasons: Tuple[str, ...]
    scope_id: str = ""
    collision_witnesses: Tuple[CollisionWitness, ...] = ()
    informative_class_count: int = 0
    observed_probe_count: int = 0
    unobserved_probe_ids: Tuple[str, ...] = ()

    @property
    def surrogate_rejected(self) -> bool:
        return self.verdict is PreservationVerdict.SURROGATE_REJECTED_COLLISION_WITNESSED

    @property
    def licenses_expensive_candidate_search(self) -> bool:
        """Only a bound probe set that could have failed and did not."""

        return self.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET

    @property
    def proves_surrogate_faithfulness(self) -> bool:
        """Never.  Absence of a counterexample is not a preservation proof."""

        return False

    @property
    def claims_probe_universe_complete(self) -> bool:
        return False

    @property
    def blacklists_the_coordinate(self) -> bool:
        """Never.  A rejection is scoped; a narrower scope is a separate receipt."""

        return False

    @property
    def grants_theorem_authority(self) -> bool:
        return False

    @property
    def grants_proof_authority(self) -> bool:
        return False

    @property
    def grants_tool_authority(self) -> bool:
        return False

    @property
    def grants_gluing_authority(self) -> bool:
        return False

    @property
    def grants_novelty_authority(self) -> bool:
        return False

    @property
    def grants_framework_authority(self) -> bool:
        return False


def _structural_reasons(receipt: RootCoordinatePreservationReceipt) -> Tuple[str, ...]:
    reasons: list[str] = []
    if receipt.schema_version != RECEIPT_SCHEMA_VERSION:
        reasons.append("schema_version_unsupported")
    for name, value in (
        ("root_claim_id", receipt.root_claim_id),
        ("root_coordinate", receipt.root_coordinate),
        ("surrogate_or_local_coordinate", receipt.surrogate_or_local_coordinate),
        ("scope_id", receipt.scope_id),
        ("public_trace_event_id", receipt.public_trace_event_id),
    ):
        if not (value or "").strip():
            reasons.append(f"{name}_missing")
    if not (receipt.cheapest_hostile_world or "").strip():
        # The issue names this field load-bearing: a contract that cannot state
        # where the surrogate would look good while the root does not has not
        # been thought through, and must not license search.
        reasons.append("cheapest_hostile_world_missing")
    if not receipt.bridge_map:
        reasons.append("bridge_map_missing")
    else:
        for pair in receipt.bridge_map:
            if len(pair) != 2 or not all((part or "").strip() for part in pair):
                reasons.append("bridge_map_edge_malformed")
                break
    if not receipt.evidence_pointers:
        reasons.append("evidence_pointers_missing")

    seen: set[str] = set()
    for probe in receipt.probes:
        if not (probe.probe_id or "").strip():
            reasons.append("probe_id_missing")
            continue
        if probe.probe_id in seen:
            reasons.append("duplicate_probe_id")
        seen.add(probe.probe_id)
        if not (probe.projected_surrogate_state or "").strip():
            reasons.append("probe_projected_surrogate_state_missing")

    if not receipt.receipt_canonical_sha256:
        reasons.append("receipt_canonical_sha256_missing")
    elif not _SHA256_RE.match(receipt.receipt_canonical_sha256):
        reasons.append("receipt_canonical_sha256_malformed")
    return tuple(reasons)


def find_collision_witnesses(
    probes: Tuple[RootCoordinateProbe, ...],
) -> Tuple[CollisionWitness, ...]:
    """Return every equal-projection / different-root-outcome witness.

    Probes with an unobserved root outcome are skipped: they can witness
    neither agreement nor disagreement.
    """

    classes: "OrderedDict[str, OrderedDict[str, list[str]]]" = OrderedDict()
    for probe in probes:
        if probe.registered_root_outcome is None:
            continue
        outcomes = classes.setdefault(probe.projected_surrogate_state, OrderedDict())
        outcomes.setdefault(probe.registered_root_outcome, []).append(probe.probe_id)

    witnesses: list[CollisionWitness] = []
    for state, outcomes in classes.items():
        if len(outcomes) < 2:
            continue
        probe_ids: list[str] = []
        for ids in outcomes.values():
            probe_ids.extend(ids)
        witnesses.append(
            CollisionWitness(
                projected_surrogate_state=state,
                probe_ids=tuple(probe_ids),
                divergent_root_outcomes=tuple(outcomes),
            )
        )
    return tuple(witnesses)


def audit_root_coordinate_preservation(
    receipt: RootCoordinatePreservationReceipt | None,
) -> PreservationReport:
    """Decide, at this receipt's scope only, whether the surrogate may be used.

    The check is a congruence test on the bound probe set: if two probes project
    to the same surrogate state but register different root outcomes, the
    surrogate erases a root-facing distinction and is rejected *at this scope*.

    Three outcomes are deliberately kept apart, because collapsing them is how a
    checker becomes a rubber stamp:

    * a probe set that could have produced a collision and did not;
    * a probe set in which no collision could have surfaced at all;
    * a contract too incomplete to check.
    """

    if receipt is None:
        return PreservationReport(
            PreservationVerdict.CANNOT_CHECK,
            ("no_preservation_receipt_was_frozen_before_candidate_search",),
        )

    structural = _structural_reasons(receipt)
    if structural:
        return PreservationReport(
            PreservationVerdict.CONTRACT_INCOMPLETE,
            structural,
            scope_id=receipt.scope_id,
        )

    recomputed = receipt_canonical_sha256(receipt.to_dict())
    if recomputed != receipt.receipt_canonical_sha256:
        return PreservationReport(
            PreservationVerdict.CANNOT_CHECK,
            (
                "receipt_content_hash_does_not_match_receipt_content",
                f"declared={receipt.receipt_canonical_sha256}",
                f"recomputed={recomputed}",
            ),
            scope_id=receipt.scope_id,
        )

    unobserved = tuple(
        probe.probe_id
        for probe in receipt.probes
        if probe.registered_root_outcome is None
    )
    observed = tuple(
        probe for probe in receipt.probes if probe.registered_root_outcome is not None
    )

    witnesses = find_collision_witnesses(receipt.probes)

    class_sizes: dict[str, int] = {}
    for probe in observed:
        class_sizes[probe.projected_surrogate_state] = (
            class_sizes.get(probe.projected_surrogate_state, 0) + 1
        )
    informative = sum(
        1
        for size in class_sizes.values()
        if size >= MIN_PROBES_PER_INFORMATIVE_CLASS
    )

    if witnesses:
        return PreservationReport(
            PreservationVerdict.SURROGATE_REJECTED_COLLISION_WITNESSED,
            (
                "equal_projected_state_registered_different_root_outcomes",
                f"scope={receipt.scope_id}",
                "rejection_is_scoped_a_narrower_scope_needs_its_own_receipt",
            ),
            scope_id=receipt.scope_id,
            collision_witnesses=witnesses,
            informative_class_count=informative,
            observed_probe_count=len(observed),
            unobserved_probe_ids=unobserved,
        )

    if informative == 0:
        return PreservationReport(
            PreservationVerdict.PROBE_SET_UNINFORMATIVE,
            (
                "no_surrogate_class_holds_two_observed_probes",
                "absence_of_a_collision_here_is_structural_not_evidential",
            )
            + (
                ("some_probes_have_no_observed_root_outcome",) if unobserved else ()
            ),
            scope_id=receipt.scope_id,
            informative_class_count=0,
            observed_probe_count=len(observed),
            unobserved_probe_ids=unobserved,
        )

    reasons = (
        "no_equal_projection_different_root_outcome_witness_in_the_bound_probe_set",
        "this_is_not_a_faithfulness_proof",
        f"scope={receipt.scope_id}",
    )
    if receipt.unproved_interface_edges:
        reasons = reasons + ("unproved_interface_edges_remain_open",)
    if receipt.coverage_receipt_id is None:
        reasons = reasons + (
            "no_coverage_receipt_referenced_probe_universe_remains_unbound",
        )
    return PreservationReport(
        PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET,
        reasons,
        scope_id=receipt.scope_id,
        informative_class_count=informative,
        observed_probe_count=len(observed),
        unobserved_probe_ids=unobserved,
    )
