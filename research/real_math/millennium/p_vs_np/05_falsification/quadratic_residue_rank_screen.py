"""Exact finite admission screens for C019 quadratic-residue difference graphs.

This module constructs the p x p bipartite adjacency relation

    A[x,y] = 1 iff y-x is a nonzero quadratic residue modulo p

for primes p == 3 (mod 8), and measures the cheap structural screens used by
O9d11.  The calculations are finite implementation checks.  They are not a
proof certificate for the asymptotic rank theorem and do not establish a cover
complexity lower bound.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class QuadraticResidueScreen:
    prime: int
    degree: int
    edge_count: int
    gf2_rank: int
    distinct_rows: int
    distinct_columns: int
    translation_stabilizer: tuple[int, ...]
    forest_partition_density_lower_bound: int
    c018_rank_ceiling: int


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    divisor = 3
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 2
    return True


def validate_admissible_prime(p: int) -> None:
    if not is_prime(p):
        raise ValueError("p must be prime")
    if p % 8 != 3:
        raise ValueError("C019 admission screen requires p == 3 (mod 8)")


def quadratic_residues(p: int) -> frozenset[int]:
    if not is_prime(p) or p == 2:
        raise ValueError("quadratic_residues requires an odd prime")
    return frozenset((x * x) % p for x in range(1, p))


def adjacency_row_masks(p: int) -> tuple[int, ...]:
    validate_admissible_prime(p)
    residues = quadratic_residues(p)
    rows: list[int] = []
    for x in range(p):
        mask = 0
        for y in range(p):
            if (y - x) % p in residues:
                mask |= 1 << y
        rows.append(mask)
    return tuple(rows)


def gf2_rank(row_masks: tuple[int, ...], width: int) -> int:
    rows = list(row_masks)
    rank = 0
    for column in range(width):
        pivot = next(
            (index for index in range(rank, len(rows)) if (rows[index] >> column) & 1),
            None,
        )
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for index in range(len(rows)):
            if index != rank and ((rows[index] >> column) & 1):
                rows[index] ^= rows[rank]
        rank += 1
    return rank


def column_masks(row_masks: tuple[int, ...], width: int) -> tuple[int, ...]:
    return tuple(
        sum(((row_masks[row] >> column) & 1) << row for row in range(len(row_masks)))
        for column in range(width)
    )


def translation_stabilizer(p: int) -> tuple[int, ...]:
    validate_admissible_prime(p)
    residues = quadratic_residues(p)
    return tuple(
        shift
        for shift in range(p)
        if frozenset((value + shift) % p for value in residues) == residues
    )


def screen_quadratic_residue_graph(p: int) -> QuadraticResidueScreen:
    validate_admissible_prime(p)
    rows = adjacency_row_masks(p)
    columns = column_masks(rows, p)
    degree = (p - 1) // 2
    edge_count = p * degree
    forest_lb = math.ceil(edge_count / (2 * p - 1))
    rank = gf2_rank(rows, p)

    return QuadraticResidueScreen(
        prime=p,
        degree=degree,
        edge_count=edge_count,
        gf2_rank=rank,
        distinct_rows=len(set(rows)),
        distinct_columns=len(set(columns)),
        translation_stabilizer=translation_stabilizer(p),
        forest_partition_density_lower_bound=forest_lb,
        c018_rank_ceiling=3 * rank - 2 if rank else 0,
    )


if __name__ == "__main__":
    for prime in (3, 11, 19, 43, 59):
        print(screen_quadratic_residue_graph(prime))
