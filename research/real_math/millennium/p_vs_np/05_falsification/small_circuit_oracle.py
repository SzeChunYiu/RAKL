"""Exact tiny Boolean-circuit search for RAKL P-vs-NP calibration.

This is deliberately resource-bounded. It is a counterexample/calibration oracle,
not a circuit-lower-bound proof system for asymptotic claims.

Basis: binary AND, binary OR, unary NOT, with constants 0/1 and input wires free.
A state is the set of truth tables currently available. Adding one new gate output
costs one. Breadth-first search is therefore exact for the bounded state graph.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    n_inputs: int
    max_gates: int
    target: int
    min_gates: int | None
    states_seen: int
    functions_seen: int


def variable_truth_table(n_inputs: int, index: int) -> int:
    table = 0
    for assignment in range(1 << n_inputs):
        if (assignment >> index) & 1:
            table |= 1 << assignment
    return table


def exact_min_gates(n_inputs: int, target: int, max_gates: int = 6) -> SearchResult:
    if n_inputs < 1:
        raise ValueError("n_inputs must be positive")
    if n_inputs > 3 or max_gates > 6:
        raise ValueError("strict calibration guard: use n_inputs <= 3 and max_gates <= 6")

    row_count = 1 << n_inputs
    mask = (1 << row_count) - 1
    if target < 0 or target > mask:
        raise ValueError("target does not fit the requested truth-table width")

    source = frozenset(
        {0, mask, *(variable_truth_table(n_inputs, i) for i in range(n_inputs))}
    )
    queue = deque([(source, 0)])
    state_depth = {source: 0}
    function_depth = {f: 0 for f in source}

    if target in source:
        return SearchResult(n_inputs, max_gates, target, 0, 1, len(function_depth))

    while queue:
        state, depth = queue.popleft()
        if depth >= max_gates:
            continue

        values = tuple(state)
        generated: set[int] = set()

        for a in values:
            generated.add(mask ^ a)

        for i, a in enumerate(values):
            for b in values[i:]:
                generated.add(a & b)
                generated.add(a | b)

        for output in generated.difference(state):
            next_depth = depth + 1
            function_depth.setdefault(output, next_depth)
            next_state = frozenset((*state, output))
            if next_state not in state_depth:
                state_depth[next_state] = next_depth
                queue.append((next_state, next_depth))

    return SearchResult(
        n_inputs=n_inputs,
        max_gates=max_gates,
        target=target,
        min_gates=function_depth.get(target),
        states_seen=len(state_depth),
        functions_seen=len(function_depth),
    )


def xor2_calibration() -> SearchResult:
    x = variable_truth_table(2, 0)
    y = variable_truth_table(2, 1)
    return exact_min_gates(2, x ^ y, max_gates=4)


if __name__ == "__main__":
    print(xor2_calibration())
