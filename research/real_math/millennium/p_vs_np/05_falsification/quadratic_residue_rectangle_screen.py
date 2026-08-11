"""Finite falsification/calibration helpers for C020.

The analytic C020 lemmas are proofs on paper.  This module only checks finite
instances of the quadratic-character correlation identity, computes exact maximum
edge-rectangle area for small primes, and builds the k=1 row/column separating
pairs used to regression-test the low-local-witness definition.

No finite output from this file has asymptotic theorem or novelty authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


Edge = tuple[int, int]
Pair = tuple[frozenset[Edge], frozenset[Edge]]


@dataclass(frozen=True)
class RectangleScreenResult:
    prime: int
    edge_count: int
    analytic_rectangle_area_ceiling: int
    exact_max_rectangle_area: int | None
    correlation_identity_ok: bool


def _is_prime(value: int) -> bool:
    if value < 2:
        return False
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            return value == divisor
        divisor += 1 if divisor == 2 else 2
    return True


def _validate_prime(prime: int) -> None:
    if not _is_prime(prime) or prime % 8 != 3:
        raise ValueError("C020 requires a prime congruent to 3 modulo 8")


def quadratic_residues(prime: int) -> set[int]:
    _validate_prime(prime)
    return {value * value % prime for value in range(1, prime)}


def quadratic_character(prime: int, value: int) -> int:
    residues = quadratic_residues(prime)
    residue = value % prime
    if residue == 0:
        return 0
    return 1 if residue in residues else -1


def sign_matrix(prime: int) -> tuple[tuple[int, ...], ...]:
    _validate_prime(prime)
    residues = quadratic_residues(prime)

    def chi(value: int) -> int:
        residue = value % prime
        if residue == 0:
            return 0
        return 1 if residue in residues else -1

    return tuple(
        tuple(chi(y - x) for y in range(prime))
        for x in range(prime)
    )


def verify_character_correlation_identity(prime: int) -> bool:
    """Check M M^T = p I - J exactly over the integers."""
    matrix = sign_matrix(prime)
    for x in range(prime):
        for z in range(prime):
            dot = sum(matrix[x][y] * matrix[z][y] for y in range(prime))
            expected = prime - 1 if x == z else -1
            if dot != expected:
                return False
    return True


def adjacency_row_masks(prime: int) -> tuple[int, ...]:
    _validate_prime(prime)
    residues = quadratic_residues(prime)
    rows: list[int] = []
    for x in range(prime):
        mask = 0
        for y in range(prime):
            if (y - x) % prime in residues:
                mask |= 1 << y
        rows.append(mask)
    return tuple(rows)


def exact_max_edge_rectangle_area(prime: int, *, max_prime: int = 19) -> int:
    """Exhaustively maximize |A|*|B| over A x B contained in QR_p.

    The search enumerates all left subsets, so it is intentionally guarded.
    """
    _validate_prime(prime)
    if prime > max_prime:
        raise ValueError(
            f"strict exhaustive-search guard: prime={prime} exceeds max_prime={max_prime}"
        )

    rows = adjacency_row_masks(prime)
    full = (1 << prime) - 1
    common_neighbours = [0] * (1 << prime)
    common_neighbours[0] = full
    best = 0

    for left_mask in range(1, 1 << prime):
        low_bit = left_mask & -left_mask
        row_index = low_bit.bit_length() - 1
        previous = left_mask ^ low_bit
        common = common_neighbours[previous] & rows[row_index]
        common_neighbours[left_mask] = common
        area = left_mask.bit_count() * common.bit_count()
        if area > best:
            best = area

    return best


def screen_quadratic_residue_rectangles(
    prime: int, *, exact: bool = True
) -> RectangleScreenResult:
    _validate_prime(prime)
    exact_area = exact_max_edge_rectangle_area(prime) if exact else None
    return RectangleScreenResult(
        prime=prime,
        edge_count=prime * (prime - 1) // 2,
        analytic_rectangle_area_ceiling=prime,
        exact_max_rectangle_area=exact_area,
        correlation_identity_ok=verify_character_correlation_identity(prime),
    )


def k1_row_column_separating_pairs(
    n_vertices_per_side: int, complement: set[Edge]
) -> tuple[Pair, ...]:
    """Return the simple binary k=1 row/column pair family from C020-L4.

    For k=1, binary row and column codes separate every index from every other
    index using at most 2*ceil(log2 N) pairs.  This is only a finite witness for
    the general probabilistic separating-family proof in C020-L4.
    """
    if n_vertices_per_side < 2:
        raise ValueError("n_vertices_per_side must be at least 2")
    for u, v in complement:
        if not (0 <= u < n_vertices_per_side and 0 <= v < n_vertices_per_side):
            raise ValueError("complement edge lies outside the requested ground set")

    bits = math.ceil(math.log2(n_vertices_per_side))
    pairs: list[Pair] = []
    for axis in (0, 1):
        for bit in range(bits):
            ones = frozenset(
                edge for edge in complement if ((edge[axis] >> bit) & 1) == 1
            )
            zeros = frozenset(complement.difference(ones))
            pairs.append((ones, zeros))
    return tuple(pairs)


if __name__ == "__main__":
    for candidate_prime in (3, 11, 19):
        print(screen_quadratic_residue_rectangles(candidate_prime))
