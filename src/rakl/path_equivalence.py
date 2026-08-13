from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Tuple


def _hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class PathEquivalenceKind(str, Enum):
    EXACT_SEQUENCE = "EXACT_SEQUENCE"
    COMMUTES_WITH_WITNESS = "COMMUTES_WITH_WITNESS"
    INDEPENDENT_IN_CONTEXT = "INDEPENDENT_IN_CONTEXT"


@dataclass(frozen=True)
class PathEquivalenceWitness:
    witness_id: str
    source_state_hash: str
    target_state_hash: str
    left_transition_ids: Tuple[str, ...]
    right_transition_ids: Tuple[str, ...]
    kind: PathEquivalenceKind
    conditions: Tuple[str, ...] = ()
    verifier_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.witness_id or not self.source_state_hash or not self.target_state_hash:
            raise ValueError("path equivalence requires witness/source/target identity")
        if not self.left_transition_ids or not self.right_transition_ids:
            raise ValueError("path equivalence requires two nonempty paths")
        if self.kind is not PathEquivalenceKind.EXACT_SEQUENCE and (not self.conditions or not self.verifier_ids):
            raise ValueError("nontrivial path equivalence requires conditions and verifier evidence")
        if self.kind is PathEquivalenceKind.EXACT_SEQUENCE and self.left_transition_ids != self.right_transition_ids:
            raise ValueError("EXACT_SEQUENCE requires identical transition sequences")

    @property
    def grants_proof_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class PartialOrderTrace:
    transition_ids: Tuple[str, ...]
    dependencies: Tuple[Tuple[str, str], ...]
    layers: Tuple[Tuple[str, ...], ...]
    signature: str

    @property
    def sequential_interleavings_are_authority_equivalent(self) -> bool:
        return False


def canonical_partial_order_trace(transition_ids: Iterable[str], dependencies: Iterable[tuple[str, str]] = ()) -> PartialOrderTrace:
    transitions = tuple(transition_ids)
    if not transitions or len(set(transitions)) != len(transitions):
        raise ValueError("transition ids must be nonempty and unique")
    transition_set = set(transitions)
    deps = tuple(sorted(set(tuple(pair) for pair in dependencies)))
    for left, right in deps:
        if left not in transition_set or right not in transition_set:
            raise ValueError("dependency references unknown transition")
        if left == right:
            raise ValueError("self dependency is invalid")

    incoming: dict[str, set[str]] = {item: set() for item in transitions}
    for left, right in deps:
        incoming[right].add(left)

    remaining = set(transitions)
    layers: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(sorted(item for item in remaining if not (incoming[item] & remaining)))
        if not ready:
            raise ValueError("dependency relation contains a cycle")
        layers.append(ready)
        remaining.difference_update(ready)

    canonical_transitions = tuple(sorted(transitions))
    payload = {"transitions": canonical_transitions, "dependencies": [list(item) for item in deps], "layers": [list(layer) for layer in layers]}
    return PartialOrderTrace(canonical_transitions, deps, tuple(layers), _hash(payload))


def equivalent_under_declared_partial_order(left_history: Iterable[str], right_history: Iterable[str], dependencies: Iterable[tuple[str, str]] = ()) -> bool:
    left = tuple(left_history)
    right = tuple(right_history)
    if set(left) != set(right) or len(left) != len(right):
        return False
    trace = canonical_partial_order_trace(left, dependencies)

    def respects(history: tuple[str, ...]) -> bool:
        position = {item: index for index, item in enumerate(history)}
        return all(position[a] < position[b] for a, b in trace.dependencies)

    return respects(left) and respects(right)
