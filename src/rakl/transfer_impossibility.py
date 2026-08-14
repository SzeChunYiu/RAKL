"""Typed refusal for the structural transfer gate (#609 follow-on).

``assess_transfer`` returns ``REJECTED`` for two epistemically different things:

* the supplied witness is defective, but *some other* witness would license the
  transfer -- a repairable, witness-local failure; and
* *no* admissible witness can license the transfer -- a property of the two
  objects themselves.

This module adds the distinction without touching the existing gate.

The move is imported from the causal-transportability parent (Bareinboim &
Pearl, "Transportability of Causal Effects: Completeness Results", AAAI 2012).
There, ``sID`` FAILs with a structural certificate (Theorem 7, an s-hedge) and
Corollary 3 states ``sID`` is complete, so a FAIL means no transport formula
exists *from the given inputs*, "independently of the method used to obtain
such mapping". Crucially that is non-existence relative to a FIXED input tuple,
not absolute impossibility: the underlying proof exhibits two causal models
agreeing on every declared input yet disagreeing on the target quantity.

What transfers is only the *quantification structure* of the refusal, never the
causal machinery -- ORION has no causal diagram. Two source preconditions must
be discharged before the strong verdict is licensed here:

1. a complete declaration of what the verdict ranges over (the analogue of
   ``sID``'s fully specified selection diagram), supplied as an explicit
   closed-world declaration; and
2. an exhaustion over the presentation space that actually *completes*.

Where ORION is genuinely easier than the source: its presentation space is the
set of injective role mappings, which is finite, so exhaustion is decidable --
unlike a general do-calculus derivation search. Where it is harder: that space
is exponential, so the search carries a budget, and budget exhaustion yields
the WEAK verdict. An incomplete exhaustion certifies nothing.

Proposal-only. Grants no scientific or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .structural_transfer import assess_transfer
from .structural_types import (
    StructuralObject,
    StructuralWitness,
    TransferDecision,
)

#: Default ceiling on search-tree node expansions for the injective-mapping
#: exhaustion. Exceeding it makes the search *incomplete*, which downgrades the
#: verdict to ``MERELY_UNLICENSED``. It never upgrades anything.
DEFAULT_MAX_SEARCH_NODES = 200_000


class RefusalKind(str, Enum):
    #: No admissible witness can license this transfer, established by a
    #: completed exhaustion under a closed-world target declaration.
    CERTIFIABLY_IMPOSSIBLE = "CERTIFIABLY_IMPOSSIBLE"
    #: This witness does not license the transfer. Says nothing about whether
    #: another one would. This is the fail-closed default.
    MERELY_UNLICENSED = "MERELY_UNLICENSED"
    #: The base gate did not return REJECTED, so there is no refusal to type.
    NOT_A_REFUSAL = "NOT_A_REFUSAL"


@dataclass(frozen=True)
class TargetDeclaration:
    """Closed-world declaration for a target object.

    ``closed_world=True`` asserts that ``relations``, ``invariants`` and ``qoi``
    of the target are declared *completely*: an absent relation means the target
    does not have it, not that nobody recorded it. This is the honest analogue
    of ``sID``'s fully specified selection diagram, and it is the precondition
    the source theory requires and explicitly places outside its own formalism
    when unavailable.

    Without it no impossibility certificate is licensed, because absence of
    evidence in an open-world declaration is not evidence of absence.
    """

    target_structure_id: str
    closed_world: bool
    declared_by: str = ""

    def __post_init__(self) -> None:
        if not self.target_structure_id.strip():
            raise ValueError("target declaration requires a target structure id")
        if self.closed_world and not self.declared_by.strip():
            raise ValueError("a closed-world declaration must name its declarer")


@dataclass(frozen=True)
class ImpossibilityCertificate:
    """Witness-independent obstructions, the ORION analogue of an s-hedge.

    Every field is a property of the (source, target) pair alone. No field can
    be changed by supplying a different witness.
    """

    failed_criteria: tuple[str, ...]
    missing_invariants: tuple[str, ...]
    unmatchable_relation_types: tuple[str, ...]
    role_cardinality_obstruction: bool
    exhausted_mapping_count: int

    @property
    def is_empty(self) -> bool:
        return not self.failed_criteria


@dataclass(frozen=True)
class TypedRefusal:
    kind: RefusalKind
    base_decision: TransferDecision
    certificate: ImpossibilityCertificate | None
    search_completed: bool
    search_nodes: int
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _relation_type_key(relation_type: str, directed: bool) -> str:
    return f"{relation_type}:{int(directed)}"


def _target_relation_type_keys(target: StructuralObject) -> set[str]:
    return {
        _relation_type_key(relation.relation_type, relation.directed)
        for relation in target.relations
    }


def exists_licensing_role_mapping(
    source: StructuralObject,
    target: StructuralObject,
    *,
    max_search_nodes: int = DEFAULT_MAX_SEARCH_NODES,
) -> tuple[bool | None, int]:
    """Decide S3: does some injective role mapping preserve every source relation?

    Returns ``(result, nodes)`` where ``result`` is ``True``/``False`` when the
    search completed and ``None`` when the node budget was exhausted first.
    ``None`` must be treated as "no information", never as ``False``.

    Injectivity is required because ``StructuralWitness`` rejects a non-injective
    ``role_mapping`` at construction time, so a non-injective map is not an
    admissible presentation and must not be searched.
    """

    source_roles = sorted(source.role_ids)
    target_roles = sorted(target.role_ids)
    if not source_roles:
        return True, 0
    if len(source_roles) > len(target_roles):
        # No injective map can exist. Witness-independent, and free to detect.
        return False, 0

    target_signatures = {relation.signature for relation in target.relations}

    # Order source roles by relational degree so the most constrained role is
    # assigned first. This is pruning only; it cannot change the answer.
    degree: dict[str, int] = {role: 0 for role in source_roles}
    for relation in source.relations:
        degree[relation.source_role] += 1
        degree[relation.target_role] += 1
    order = sorted(source_roles, key=lambda role: (-degree[role], role))

    # Relations become checkable as soon as both endpoints are assigned.
    position = {role: index for index, role in enumerate(order)}
    checkpoint: dict[int, list] = {index: [] for index in range(len(order))}
    for relation in source.relations:
        ready_at = max(position[relation.source_role], position[relation.target_role])
        checkpoint[ready_at].append(relation)

    nodes = 0
    used: set[str] = set()
    assignment: dict[str, str] = {}

    def backtrack(index: int) -> bool | None:
        nonlocal nodes
        if index == len(order):
            return True
        role = order[index]
        for candidate in target_roles:
            if candidate in used:
                continue
            nodes += 1
            if nodes > max_search_nodes:
                return None
            assignment[role] = candidate
            used.add(candidate)
            consistent = True
            for relation in checkpoint[index]:
                mapped = (
                    assignment[relation.source_role],
                    relation.relation_type,
                    assignment[relation.target_role],
                    relation.directed,
                )
                if mapped not in target_signatures:
                    consistent = False
                    break
            if consistent:
                result = backtrack(index + 1)
                if result is None:
                    del assignment[role]
                    used.discard(candidate)
                    return None
                if result:
                    del assignment[role]
                    used.discard(candidate)
                    return True
            del assignment[role]
            used.discard(candidate)
        return False

    outcome = backtrack(0)
    return outcome, nodes


def structural_obstructions(
    source: StructuralObject,
    target: StructuralObject,
    *,
    max_search_nodes: int = DEFAULT_MAX_SEARCH_NODES,
) -> tuple[ImpossibilityCertificate, bool]:
    """Evaluate the three witness-independent criteria S1/S2/S3.

    Returns ``(certificate, search_completed)``. When ``search_completed`` is
    False the S3 verdict is unknown and the certificate must not be used.
    """

    failed: list[str] = []

    # S1 -- QoI. No witness field participates in this check.
    if source.qoi != target.qoi:
        failed.append("S1_QOI")

    # S2 -- invariants. assess_transfer requires
    #   source.invariants & declared & target.invariants == source.invariants,
    # so source.invariants <= target.invariants is forced whatever the witness
    # declares: declaring more is capped by the target intersection, declaring
    # less breaks the equality.
    missing_invariants = tuple(sorted(source.invariants - target.invariants))
    if missing_invariants:
        failed.append("S2_INVARIANTS")

    # S3 -- relations, existentially quantified over injective role mappings.
    licensable, nodes = exists_licensing_role_mapping(
        source, target, max_search_nodes=max_search_nodes
    )
    search_completed = licensable is not None
    if licensable is False:
        failed.append("S3_RELATIONS")

    cardinality_obstruction = len(source.role_ids) > len(target.role_ids)
    target_types = _target_relation_type_keys(target)
    unmatchable = tuple(
        sorted(
            {
                _relation_type_key(relation.relation_type, relation.directed)
                for relation in source.relations
            }
            - target_types
        )
    )

    certificate = ImpossibilityCertificate(
        failed_criteria=tuple(failed),
        missing_invariants=missing_invariants,
        unmatchable_relation_types=unmatchable,
        role_cardinality_obstruction=cardinality_obstruction,
        exhausted_mapping_count=nodes,
    )
    return certificate, search_completed


def classify_refusal(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitness,
    *,
    target_declaration: TargetDeclaration,
    max_search_nodes: int = DEFAULT_MAX_SEARCH_NODES,
) -> TypedRefusal:
    """CH-B: adapted transfer. Type a refusal, fail-closed to the weak verdict.

    ``CERTIFIABLY_IMPOSSIBLE`` requires all three of:

    1. the target carries a closed-world completeness declaration;
    2. the bounded exhaustion over the injective-mapping space *completed*; and
    3. at least one witness-independent criterion (S1/S2/S3) failed.

    Anything else -- an open-world target, an exhausted budget, or a refusal
    caused only by witness-local defects -- is ``MERELY_UNLICENSED``.
    """

    base = assess_transfer(source, target, witness)
    if base.decision is not TransferDecision.REJECTED:
        return TypedRefusal(
            kind=RefusalKind.NOT_A_REFUSAL,
            base_decision=base.decision,
            certificate=None,
            search_completed=True,
            search_nodes=0,
            reasons=(f"base_decision_is_{base.decision.value.lower()}",),
        )

    if target_declaration.target_structure_id != target.structure_id:
        return TypedRefusal(
            kind=RefusalKind.MERELY_UNLICENSED,
            base_decision=base.decision,
            certificate=None,
            search_completed=False,
            search_nodes=0,
            reasons=("target_declaration_identity_mismatch",),
        )

    if not target_declaration.closed_world:
        return TypedRefusal(
            kind=RefusalKind.MERELY_UNLICENSED,
            base_decision=base.decision,
            certificate=None,
            search_completed=False,
            search_nodes=0,
            reasons=("target_not_declared_closed_world",),
        )

    certificate, search_completed = structural_obstructions(
        source, target, max_search_nodes=max_search_nodes
    )

    if not search_completed:
        return TypedRefusal(
            kind=RefusalKind.MERELY_UNLICENSED,
            base_decision=base.decision,
            certificate=None,
            search_completed=False,
            search_nodes=certificate.exhausted_mapping_count,
            reasons=("presentation_space_exhaustion_incomplete",),
        )

    if certificate.is_empty:
        return TypedRefusal(
            kind=RefusalKind.MERELY_UNLICENSED,
            base_decision=base.decision,
            certificate=None,
            search_completed=True,
            search_nodes=certificate.exhausted_mapping_count,
            reasons=("refusal_is_witness_local_only",) + base.reasons,
        )

    return TypedRefusal(
        kind=RefusalKind.CERTIFIABLY_IMPOSSIBLE,
        base_decision=base.decision,
        certificate=certificate,
        search_completed=True,
        search_nodes=certificate.exhausted_mapping_count,
        reasons=tuple(certificate.failed_criteria),
    )


def classify_refusal_faithful_import(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitness,
) -> TypedRefusal:
    """CH-A: the control arm. Import the verdict form, skip the assumptions.

    This is what "our gate has completeness too" looks like when the source
    preconditions are not discharged: every ``REJECTED`` is relabelled as a
    proof of impossibility. It is expected to emit false certificates, and it
    exists so that the cost of skipping the preconditions can be measured
    rather than asserted.
    """

    base = assess_transfer(source, target, witness)
    if base.decision is not TransferDecision.REJECTED:
        return TypedRefusal(
            kind=RefusalKind.NOT_A_REFUSAL,
            base_decision=base.decision,
            certificate=None,
            search_completed=True,
            search_nodes=0,
            reasons=(f"base_decision_is_{base.decision.value.lower()}",),
        )
    return TypedRefusal(
        kind=RefusalKind.CERTIFIABLY_IMPOSSIBLE,
        base_decision=base.decision,
        certificate=None,
        search_completed=True,
        search_nodes=0,
        reasons=("faithful_import_treats_every_rejection_as_impossibility",),
    )
