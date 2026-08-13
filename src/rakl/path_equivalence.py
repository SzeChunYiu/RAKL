from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Callable, Iterable, Tuple


def _hash(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _unordered_pair(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


class PathEquivalenceKind(str, Enum):
    EXACT_SEQUENCE = "EXACT_SEQUENCE"
    COMMUTES_WITH_WITNESS = "COMMUTES_WITH_WITNESS"
    INDEPENDENT_IN_CONTEXT = "INDEPENDENT_IN_CONTEXT"


@dataclass(frozen=True)
class TransitionIndependenceWitness:
    """Verifier-bound evidence that two transitions may be swapped in context."""

    witness_id: str
    left_transition_id: str
    right_transition_id: str
    context_hash: str
    verifier_ids: Tuple[str, ...]
    conditions: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all((self.witness_id, self.left_transition_id, self.right_transition_id, self.context_hash)):
            raise ValueError("independence witness requires identity, transitions, and context")
        if self.left_transition_id == self.right_transition_id:
            raise ValueError("transition cannot be independent from itself")
        if not self.verifier_ids:
            raise ValueError("independence witness requires verifier evidence")

    @property
    def pair(self) -> tuple[str, str]:
        return _unordered_pair(self.left_transition_id, self.right_transition_id)


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


def equivalent_under_declared_partial_order(
    left_history: Iterable[str],
    right_history: Iterable[str],
    dependencies: Iterable[tuple[str, str]] = (),
    *,
    independence_witnesses: Iterable[TransitionIndependenceWitness] = (),
    context_hash: str | None = None,
    prefix_context_resolver: Callable[[Tuple[str, ...]], str | None] | None = None,
    global_independence_certified: bool = False,
) -> bool:
    """Return true only when histories differ by certified independent swaps.

    Merely being two linear extensions of the same incomplete dependency list is
    not enough: absence of a declared dependency is not evidence of commutation.
    The implementation realizes a trace check by transforming one history into
    the other through adjacent swaps.

    Independence witnesses are CONTEXT-BOUND (audit finding U1): a witness whose
    ``context_hash`` is ``s`` certifies commutation only in the state ``s``, so
    it may license a swap only at a position whose prefix state is ``s``
    (asynchronous-transition-system style, state-indexed independence).

    - ``context_hash`` names the state in which the histories START. By default
      a witness therefore licenses swaps only at the head of the history (empty
      prefix), where the state is the declared start context.
    - ``prefix_context_resolver`` optionally maps an executed transition prefix
      (relative to the start context) to the state hash it reaches, extending
      licensing to interior positions whose prefix state can be named. Unknown
      prefixes must return ``None``; such swaps fail closed.
    - ``global_independence_certified=True`` restores the context-free
      (Mazurkiewicz global independence) reading: the caller asserts a
      machine-checked external certificate that every supplied witness pair
      commutes in EVERY reachable state. Without that certificate the
      context-free reading over-quotients and is unsound.
    """

    left = tuple(left_history)
    right = tuple(right_history)
    if set(left) != set(right) or len(left) != len(right):
        return False
    if len(set(left)) != len(left):
        return False
    trace = canonical_partial_order_trace(left, dependencies)

    def respects(history: tuple[str, ...]) -> bool:
        position = {item: index for index, item in enumerate(history)}
        return all(position[a] < position[b] for a, b in trace.dependencies)

    if not respects(left) or not respects(right):
        return False
    if left == right:
        return True

    transition_set = set(left)
    witnessed_contexts: dict[tuple[str, str], set[str]] = {}
    certified_global_pairs: set[tuple[str, str]] = set()
    for witness in independence_witnesses:
        if witness.left_transition_id not in transition_set or witness.right_transition_id not in transition_set:
            raise ValueError("independence witness references unknown transition")
        witnessed_contexts.setdefault(witness.pair, set()).add(witness.context_hash)
        if context_hash is None or witness.context_hash == context_hash:
            certified_global_pairs.add(witness.pair)

    if prefix_context_resolver is None:
        def prefix_context_resolver(prefix: Tuple[str, ...]) -> str | None:
            return context_hash if not prefix else None

    def swap_licensed(pair: tuple[str, str], prefix: Tuple[str, ...]) -> bool:
        if global_independence_certified:
            # Context-free reading; sound only under the caller-asserted global
            # independence certificate documented above.
            return pair in certified_global_pairs
        swap_context = prefix_context_resolver(prefix)
        if swap_context is None:
            return False  # fail closed: swap occurs in a state no witness names
        return swap_context in witnessed_contexts.get(pair, ())

    current = list(left)
    for target_index, desired in enumerate(right):
        try:
            current_index = current.index(desired, target_index)
        except ValueError:
            return False
        while current_index > target_index:
            neighbour = current[current_index - 1]
            prefix = tuple(current[: current_index - 1])
            if not swap_licensed(_unordered_pair(desired, neighbour), prefix):
                return False
            current[current_index - 1], current[current_index] = current[current_index], current[current_index - 1]
            current_index -= 1
    return tuple(current) == right
