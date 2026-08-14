"""AND-composition: derivation over a support hypergraph.

``support_solver`` finds OR-routes — any admissible chain from start to goal. A
mathematical derivation is not a chain: a lemma needs *all* of its premises at
once. The spec has always known this (``FORMAL_SYSTEM_SPECIFICATION.md`` §8's
multi-premise support relations ``H_t``); the implementation only had binary
edges. This module supplies the AND case, which is what makes solving mechanical
for proof-shaped problems: once the space holds verified inference steps, deriving
a target is forward closure over hyperedges — no reasoning engine in the loop,
only traversal.

The mechanical claim is demonstrated on real data in the tests: the dependency
graph of ``formal/RaklFormal.lean`` — whose every edge is kernel-checked — is
parsed into hyperedges, and a real theorem is re-derived from the axiom-free base
by traversal alone.

Honesty notes, load-bearing:

* ``DerivationReport.minimal_cost_claimed`` is ``False``. The extracted DAG is a
  valid derivation with a well-defined cost (sum of its distinct fired edges);
  global minimality over shared sub-derivations is not claimed, because it is not
  established.
* "Structurally underivable" and "authority-blocked" are different findings and
  are reported as such — the same distinction ``support_solver`` draws between
  UNREACHABLE_IN_PRINCIPLE and CUT.
* A derivation whose atom set realizes an obstructed cover is refused, exactly as
  in route search: obstruction-blindness is unsound for AND-composition too.

Proposal-only. A derivation is a support claim; it grants no scientific
authority.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from .support_solver import Obstruction


class DerivationOutcome(str, Enum):
    DERIVED = "DERIVED"
    AUTHORITY_BLOCKED = "AUTHORITY_BLOCKED"
    UNDERIVABLE_IN_PRINCIPLE = "UNDERIVABLE_IN_PRINCIPLE"
    OBSTRUCTED = "OBSTRUCTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class HyperEdge:
    """One inference step: ALL premises, jointly, license the conclusion."""

    edge_id: str
    premises: frozenset[str]
    conclusion: str
    cost: float = 1.0
    licensed_at: int = 0

    def __post_init__(self) -> None:
        if self.conclusion in self.premises:
            raise ValueError(f"{self.edge_id}: an edge may not presuppose its conclusion")
        if self.cost < 0:
            raise ValueError("edge cost must be non-negative")


@dataclass(frozen=True)
class DerivationDag:
    """The extracted derivation: which edge established each derived atom."""

    established: tuple[str, ...]
    fired: tuple[HyperEdge, ...]

    @property
    def cost(self) -> float:
        return sum(edge.cost for edge in self.fired)


@dataclass(frozen=True)
class DerivationReport:
    outcome: DerivationOutcome
    target: str
    dag: DerivationDag | None = None
    #: Atoms that never became derivable even ignoring authority. The AND-side
    #: analogue of an epistemic cut: what the space would have to acquire.
    missing: tuple[str, ...] = ()
    blocked_edges: tuple[str, ...] = ()
    realized_obstructions: tuple[str, ...] = ()
    minimal_cost_claimed: bool = False

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _closure(
    edges: Iterable[HyperEdge],
    base: frozenset[str],
    *,
    min_authority: int,
) -> tuple[frozenset[str], dict[str, HyperEdge]]:
    """Forward chaining: fire every edge whose premises are established.

    Deterministic and mechanical — this is the "machine traversing the space".
    When several edges can establish the same atom, the cheapest (by edge cost
    plus already-known premise-DAG cost) is recorded; ties break on edge_id so
    the derivation is reproducible.
    """
    established: set[str] = set(base)
    producer: dict[str, HyperEdge] = {}
    dag_cost: dict[str, float] = {atom: 0.0 for atom in base}

    def edge_dag_cost(edge: HyperEdge) -> float:
        return edge.cost + sum(dag_cost.get(p, 0.0) for p in edge.premises)

    changed = True
    admitted = [e for e in edges if e.licensed_at >= min_authority]
    while changed:
        changed = False
        for edge in sorted(admitted, key=lambda e: e.edge_id):
            if not edge.premises <= established:
                continue
            candidate_cost = edge_dag_cost(edge)
            if edge.conclusion not in established:
                established.add(edge.conclusion)
                producer[edge.conclusion] = edge
                dag_cost[edge.conclusion] = candidate_cost
                changed = True
            elif edge.conclusion in producer and candidate_cost < dag_cost[edge.conclusion]:
                producer[edge.conclusion] = edge
                dag_cost[edge.conclusion] = candidate_cost
                changed = True
    return frozenset(established), producer


def _extract_dag(
    target: str, base: frozenset[str], producer: dict[str, HyperEdge]
) -> DerivationDag:
    """Walk back from the target, collecting the distinct edges actually used."""
    needed: list[str] = [target]
    fired: dict[str, HyperEdge] = {}
    established: list[str] = []
    seen: set[str] = set()
    while needed:
        atom = needed.pop()
        if atom in seen or atom in base:
            continue
        seen.add(atom)
        edge = producer[atom]
        fired[edge.edge_id] = edge
        established.append(atom)
        needed.extend(edge.premises)
    ordered = tuple(sorted(fired.values(), key=lambda e: e.edge_id))
    return DerivationDag(established=tuple(sorted(established)), fired=ordered)


def derive(
    edges: Iterable[HyperEdge],
    base: Iterable[str],
    target: str,
    *,
    required_authority: int = 0,
    obstructions: Iterable[Obstruction] = (),
) -> DerivationReport:
    """Derive ``target`` from ``base`` by mechanical forward closure.

    Distinguishes, in order: derived; obstructed (the derivation's atom set
    realizes a cover with no global section); authority-blocked (derivable with
    weaker licensing — the blocked edges are named); underivable in principle
    (the missing atoms are named — the space's acquisition list).
    """
    edge_list = list(edges)
    base_set = frozenset(base)
    if target in base_set:
        return DerivationReport(
            outcome=DerivationOutcome.DERIVED,
            target=target,
            dag=DerivationDag(established=(), fired=()),
        )

    established, producer = _closure(edge_list, base_set, min_authority=required_authority)

    if target in established:
        dag = _extract_dag(target, base_set, producer)
        used = set(dag.established) | base_set
        realized = tuple(
            o.obstruction_id for o in obstructions if o.cover <= used
        )
        if realized:
            return DerivationReport(
                outcome=DerivationOutcome.OBSTRUCTED,
                target=target,
                realized_obstructions=realized,
            )
        return DerivationReport(
            outcome=DerivationOutcome.DERIVED, target=target, dag=dag
        )

    # Not derived at the demanded authority. Relax authority to attribute why.
    relaxed_established, _ = _closure(edge_list, base_set, min_authority=0)
    if target in relaxed_established:
        blocked = tuple(
            sorted(
                e.edge_id
                for e in edge_list
                if e.licensed_at < required_authority
                and e.premises <= relaxed_established
            )
        )
        return DerivationReport(
            outcome=DerivationOutcome.AUTHORITY_BLOCKED,
            target=target,
            blocked_edges=blocked,
        )

    # Underivable even ignoring authority: name what is missing. An atom is
    # missing if it is a premise of some edge on a potential path to the target
    # and is neither in the base nor derivable.
    all_premises = {p for e in edge_list for p in e.premises}
    missing = tuple(sorted(
        (all_premises | {target}) - relaxed_established
    ))
    return DerivationReport(
        outcome=DerivationOutcome.UNDERIVABLE_IN_PRINCIPLE,
        target=target,
        missing=missing,
    )
