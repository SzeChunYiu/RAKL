"""Exact finite regression for the C011 coordinate-combiner ceiling.

C011 concerns graphs on tuple vertices whose membership is a Boolean
combination of fixed local graph-membership bits.  The proof upper-bounds
intersection complexity by constructing both the true and false set for every
circuit gate (dual rails).  This module checks the set-theoretic simulation on
tiny instances and counts the constructive upper-bound intersections.

It does not compute minimum cover/intersection complexity and is not theorem
or novelty authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable, Literal


Point = tuple[tuple[int, ...], tuple[int, ...]]
Op = Literal["input", "not", "and", "or"]


@dataclass(frozen=True)
class Formula:
    op: Op
    index: int | None = None
    left: "Formula | None" = None
    right: "Formula | None" = None


def input_bit(index: int) -> Formula:
    if index < 0:
        raise ValueError("input index must be nonnegative")
    return Formula("input", index=index)


def neg(child: Formula) -> Formula:
    return Formula("not", left=child)


def conj(left: Formula, right: Formula) -> Formula:
    return Formula("and", left=left, right=right)


def disj(left: Formula, right: Formula) -> Formula:
    return Formula("or", left=left, right=right)


def xor2(left: Formula, right: Formula) -> Formula:
    # (a OR b) AND NOT(a AND b): three counted binary gates and one NOT.
    return conj(disj(left, right), neg(conj(left, right)))


def fold_or(arity: int) -> Formula:
    if arity < 1:
        raise ValueError("arity must be positive")
    result = input_bit(0)
    for index in range(1, arity):
        result = disj(result, input_bit(index))
    return result


def fold_and(arity: int) -> Formula:
    if arity < 1:
        raise ValueError("arity must be positive")
    result = input_bit(0)
    for index in range(1, arity):
        result = conj(result, input_bit(index))
    return result


def fold_xor(arity: int) -> Formula:
    if arity < 1:
        raise ValueError("arity must be positive")
    result = input_bit(0)
    for index in range(1, arity):
        result = xor2(result, input_bit(index))
    return result


def counted_binary_gates(formula: Formula) -> int:
    if formula.op == "input":
        return 0
    if formula.op == "not":
        assert formula.left is not None
        return counted_binary_gates(formula.left)
    assert formula.left is not None and formula.right is not None
    return 1 + counted_binary_gates(formula.left) + counted_binary_gates(formula.right)


def _check_formula_indices(formula: Formula, arity: int) -> None:
    if formula.op == "input":
        assert formula.index is not None
        if not 0 <= formula.index < arity:
            raise ValueError("formula references an input outside the declared arity")
        return
    assert formula.left is not None
    _check_formula_indices(formula.left, arity)
    if formula.op in {"and", "or"}:
        assert formula.right is not None
        _check_formula_indices(formula.right, arity)


def evaluate_formula(formula: Formula, bits: tuple[bool, ...]) -> bool:
    if formula.op == "input":
        assert formula.index is not None
        return bits[formula.index]
    assert formula.left is not None
    if formula.op == "not":
        return not evaluate_formula(formula.left, bits)
    assert formula.right is not None
    left = evaluate_formula(formula.left, bits)
    right = evaluate_formula(formula.right, bits)
    if formula.op == "and":
        return left and right
    if formula.op == "or":
        return left or right
    raise AssertionError("unreachable")


def tuple_ground(base_n: int, arity: int) -> frozenset[Point]:
    if base_n < 2 or arity < 1:
        raise ValueError("use base_n >= 2 and positive arity")
    vertices = tuple(product(range(base_n), repeat=arity))
    return frozenset((x, y) for x in vertices for y in vertices)


def local_rails(
    base_n: int,
    base_graph: set[tuple[int, int]],
    arity: int,
) -> tuple[tuple[frozenset[Point], frozenset[Point]], ...]:
    ground = tuple_ground(base_n, arity)
    for a, b in base_graph:
        if not (0 <= a < base_n and 0 <= b < base_n):
            raise ValueError("base graph edge lies outside the local ground set")
    rails: list[tuple[frozenset[Point], frozenset[Point]]] = []
    for index in range(arity):
        true_set = frozenset(
            (x, y) for x, y in ground if (x[index], y[index]) in base_graph
        )
        rails.append((true_set, ground - true_set))
    return tuple(rails)


def dual_rail_evaluate(
    formula: Formula,
    rails: tuple[tuple[frozenset[Point], frozenset[Point]], ...],
) -> tuple[frozenset[Point], frozenset[Point]]:
    if formula.op == "input":
        assert formula.index is not None
        return rails[formula.index]
    assert formula.left is not None
    left_true, left_false = dual_rail_evaluate(formula.left, rails)
    if formula.op == "not":
        return left_false, left_true
    assert formula.right is not None
    right_true, right_false = dual_rail_evaluate(formula.right, rails)
    if formula.op == "and":
        return left_true & right_true, left_false | right_false
    if formula.op == "or":
        return left_true | right_true, left_false & right_false
    raise AssertionError("unreachable")


def direct_combiner_graph(
    base_n: int,
    base_graph: set[tuple[int, int]],
    arity: int,
    formula: Formula,
) -> frozenset[Point]:
    _check_formula_indices(formula, arity)
    ground = tuple_ground(base_n, arity)
    return frozenset(
        (x, y)
        for x, y in ground
        if evaluate_formula(
            formula,
            tuple((x[i], y[i]) in base_graph for i in range(arity)),
        )
    )


def verify_dual_rail_simulation(
    base_n: int,
    base_graph: set[tuple[int, int]],
    arity: int,
    formula: Formula,
) -> bool:
    _check_formula_indices(formula, arity)
    rails = local_rails(base_n, base_graph, arity)
    true_set, false_set = dual_rail_evaluate(formula, rails)
    ground = tuple_ground(base_n, arity)
    return (
        true_set == direct_combiner_graph(base_n, base_graph, arity, formula)
        and not (true_set & false_set)
        and true_set | false_set == ground
    )


def constructive_intersection_bound(base_n: int, arity: int, formula: Formula) -> int:
    """Return the C011 bound t*n^2 + number of binary AND/OR gates."""
    if base_n < 2 or arity < 1:
        raise ValueError("use base_n >= 2 and positive arity")
    _check_formula_indices(formula, arity)
    return arity * base_n * base_n + counted_binary_gates(formula)
