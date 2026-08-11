"""Finite exact witnesses for C016 finite-state cover pruning.

The module propagates deterministic finite-state aggregators over exact sets of
input pairs.  It checks the set identities behind the C016 intersection-complexity
upper bound.  These finite executions are calibration evidence only; they are not
an asymptotic proof certificate and not a P-vs-NP result.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, ceil
from typing import Hashable, Mapping, Sequence


Edge = tuple[int, int]
State = Hashable
Symbol = Hashable


@dataclass(frozen=True)
class DFA:
    states: tuple[State, ...]
    alphabet: tuple[Symbol, ...]
    start: State
    accepting: frozenset[State]
    transition: Mapping[tuple[State, Symbol], State]

    def validate(self) -> None:
        state_set = set(self.states)
        alphabet_set = set(self.alphabet)
        if not self.states:
            raise ValueError("DFA must have at least one state")
        if not self.alphabet:
            raise ValueError("DFA must have at least one symbol")
        if len(state_set) != len(self.states):
            raise ValueError("DFA states must be unique")
        if len(alphabet_set) != len(self.alphabet):
            raise ValueError("DFA alphabet symbols must be unique")
        if self.start not in state_set:
            raise ValueError("DFA start state is not registered")
        if not self.accepting.issubset(state_set):
            raise ValueError("DFA accepting state is not registered")
        expected = {(q, a) for q in self.states for a in self.alphabet}
        if set(self.transition) != expected:
            raise ValueError("DFA transition map must be total on states x alphabet")
        if any(qp not in state_set for qp in self.transition.values()):
            raise ValueError("DFA transition targets must be registered states")


@dataclass(frozen=True)
class FiniteStateWitness:
    ambient_size: int
    coordinates: int
    accepted: frozenset[Edge]
    direct_accepted: frozenset[Edge]
    local_intersections: int
    transition_intersections: int
    upper_bound_intersections: int
    reachable_state_counts: tuple[int, ...]

    @property
    def counted_intersections(self) -> int:
        return self.local_intersections + self.transition_intersections


def _validate_symbol_partition(
    ambient: frozenset[Edge],
    symbol_sets: Sequence[Mapping[Symbol, frozenset[Edge]]],
    alphabet: tuple[Symbol, ...],
) -> None:
    alphabet_set = set(alphabet)
    for coordinate, partition in enumerate(symbol_sets):
        if set(partition) != alphabet_set:
            raise ValueError(f"coordinate {coordinate} does not define every alphabet symbol")
        union: set[Edge] = set()
        for symbol in alphabet:
            piece = partition[symbol]
            if union.intersection(piece):
                raise ValueError(f"coordinate {coordinate} symbol sets overlap")
            union.update(piece)
        if frozenset(union) != ambient:
            raise ValueError(f"coordinate {coordinate} symbol sets do not cover ambient space")


def finite_state_witness(
    *,
    ambient: frozenset[Edge],
    symbol_sets: Sequence[Mapping[Symbol, frozenset[Edge]]],
    dfa: DFA,
    local_intersection_costs: Sequence[int],
    direct_accepted: frozenset[Edge],
) -> FiniteStateWitness:
    """Propagate a DFA by intersections and unions on an exact finite ambient set.

    ``local_intersection_costs[i]`` is the separately justified cost of building
    all lifted local symbol sets at coordinate ``i``.  This helper checks the DFA
    propagation identity and counts only intersections with nonempty reachable
    prefix-state sets.  Therefore the transition count is automatically bounded
    by ``t * |Q| * |Sigma|``.
    """

    dfa.validate()
    if not symbol_sets:
        raise ValueError("at least one coordinate is required")
    if len(local_intersection_costs) != len(symbol_sets):
        raise ValueError("one local intersection cost is required per coordinate")
    if any(cost < 0 for cost in local_intersection_costs):
        raise ValueError("local intersection costs must be nonnegative")
    if not direct_accepted.issubset(ambient):
        raise ValueError("direct accepted set must be contained in ambient space")

    _validate_symbol_partition(ambient, symbol_sets, dfa.alphabet)

    prefix: dict[State, frozenset[Edge]] = {dfa.start: ambient}
    transition_intersections = 0
    reachable_counts = [1]

    for partition in symbol_sets:
        next_sets: dict[State, set[Edge]] = {}
        for state, prefix_set in prefix.items():
            if not prefix_set:
                continue
            for symbol in dfa.alphabet:
                transition_intersections += 1
                piece = prefix_set.intersection(partition[symbol])
                if not piece:
                    continue
                target_state = dfa.transition[(state, symbol)]
                next_sets.setdefault(target_state, set()).update(piece)
        prefix = {state: frozenset(piece) for state, piece in next_sets.items()}
        reachable_counts.append(len(prefix))

    accepted: set[Edge] = set()
    for state in dfa.accepting:
        accepted.update(prefix.get(state, frozenset()))

    accepted_frozen = frozenset(accepted)
    if accepted_frozen != direct_accepted:
        raise AssertionError("finite-state propagation does not match direct predicate")

    t = len(symbol_sets)
    local_cost = sum(local_intersection_costs)
    transition_upper = t * len(dfa.states) * len(dfa.alphabet)
    if transition_intersections > transition_upper:
        raise AssertionError("transition count exceeded theorem upper bound")

    return FiniteStateWitness(
        ambient_size=len(ambient),
        coordinates=t,
        accepted=accepted_frozen,
        direct_accepted=direct_accepted,
        local_intersections=local_cost,
        transition_intersections=transition_intersections,
        upper_bound_intersections=local_cost + transition_upper,
        reachable_state_counts=tuple(reachable_counts),
    )


def _ambient_for_bits(t: int) -> frozenset[Edge]:
    if t < 1:
        raise ValueError("t must be positive")
    if t > 8:
        raise ValueError("finite calibration guard: use t <= 8")
    n = 1 << t
    return frozenset((x, y) for x in range(n) for y in range(n))


def xor_symbol_sets(t: int) -> tuple[frozenset[Edge], list[dict[int, frozenset[Edge]]]]:
    """Return the exact XOR/XNOR symbol partition for each bit coordinate."""

    ambient = _ambient_for_bits(t)
    partitions: list[dict[int, frozenset[Edge]]] = []
    for bit in range(t):
        zero: set[Edge] = set()
        one: set[Edge] = set()
        for x, y in ambient:
            symbol = ((x >> bit) & 1) ^ ((y >> bit) & 1)
            (one if symbol else zero).add((x, y))
        partitions.append({0: frozenset(zero), 1: frozenset(one)})
    return ambient, partitions


def mod3_hamming_dfa() -> DFA:
    states = (0, 1, 2)
    alphabet = (0, 1)
    transition = {
        (state, symbol): (state + symbol) % 3
        for state in states
        for symbol in alphabet
    }
    return DFA(
        states=states,
        alphabet=alphabet,
        start=0,
        accepting=frozenset({0}),
        transition=transition,
    )


def parity_dfa() -> DFA:
    states = (0, 1)
    alphabet = (0, 1)
    transition = {
        (state, symbol): state ^ symbol
        for state in states
        for symbol in alphabet
    }
    return DFA(
        states=states,
        alphabet=alphabet,
        start=0,
        accepting=frozenset({1}),
        transition=transition,
    )


def hamming_mod3_witness(t: int) -> FiniteStateWitness:
    ambient, partitions = xor_symbol_sets(t)
    direct = frozenset(
        (x, y)
        for x, y in ambient
        if (x ^ y).bit_count() % 3 == 0
    )
    # XOR and XNOR each cost one intersection from literals, so the complete
    # local two-symbol partition costs two intersections per coordinate.
    return finite_state_witness(
        ambient=ambient,
        symbol_sets=partitions,
        dfa=mod3_hamming_dfa(),
        local_intersection_costs=[2] * t,
        direct_accepted=direct,
    )


def hamming_parity_witness(t: int) -> FiniteStateWitness:
    ambient, partitions = xor_symbol_sets(t)
    direct = frozenset(
        (x, y)
        for x, y in ambient
        if (x ^ y).bit_count() % 2 == 1
    )
    return finite_state_witness(
        ambient=ambient,
        symbol_sets=partitions,
        dfa=parity_dfa(),
        local_intersection_costs=[2] * t,
        direct_accepted=direct,
    )


def hamming_mod3_row_degree(t: int) -> int:
    if t < 1:
        raise ValueError("t must be positive")
    return sum(comb(t, weight) for weight in range(0, t + 1, 3))


def hamming_mod3_arboricity_lower_bound(t: int) -> int:
    """Elementary lower bound from total edges / maximum edges per forest."""

    n = 1 << t
    degree = hamming_mod3_row_degree(t)
    edge_count = n * degree
    return ceil(edge_count / (2 * n - 1))


if __name__ == "__main__":
    for bits in range(1, 6):
        witness = hamming_mod3_witness(bits)
        print(
            bits,
            witness.counted_intersections,
            witness.upper_bound_intersections,
            hamming_mod3_row_degree(bits),
            hamming_mod3_arboricity_lower_bound(bits),
        )
