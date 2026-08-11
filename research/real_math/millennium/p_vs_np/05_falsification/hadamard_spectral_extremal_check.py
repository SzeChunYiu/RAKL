"""Exact finite checks for C023's Walsh-Hadamard extremal identity.

Authority boundary: this module checks finite statement binding only. It does not
prove the asymptotic cover-complexity theorem or any P-vs-NP claim.
"""

from __future__ import annotations


def _parity(x: int) -> int:
    return x.bit_count() & 1


def inner_product_sign_matrix(t: int) -> list[list[int]]:
    """Return the +/-1 incidence matrix for odd mod-2 inner product.

    Entry +1 means <x,y>=1 mod 2, and -1 means <x,y>=0 mod 2.
    """
    if not isinstance(t, int) or t < 1 or t > 7:
        raise ValueError("strict finite guard: t must be an integer in [1,7]")
    n = 1 << t
    return [
        [1 if _parity(x & y) else -1 for y in range(n)]
        for x in range(n)
    ]


def gram(matrix: list[list[int]]) -> list[list[int]]:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("matrix must be nonempty and square")
    n = len(matrix)
    return [
        [sum(matrix[i][k] * matrix[j][k] for k in range(n)) for j in range(n)]
        for i in range(n)
    ]


def exact_hadamard_identity_check(t: int) -> bool:
    matrix = inner_product_sign_matrix(t)
    n = 1 << t
    product = gram(matrix)
    return all(
        product[i][j] == (n if i == j else 0)
        for i in range(n)
        for j in range(n)
    )


def spectral_ratio_squared_from_gram(t: int) -> tuple[int, int]:
    """Return the exact pair (N^2, ||A||^2) implied by the checked Gram identity."""
    if not exact_hadamard_identity_check(t):
        raise AssertionError("Walsh-Hadamard Gram identity failed")
    n = 1 << t
    return n * n, n


def c012_cover_upper_bound(t: int) -> int:
    if not isinstance(t, int) or t < 1:
        raise ValueError("t must be positive")
    return 3 * t - 2


if __name__ == "__main__":
    for width in range(1, 6):
        print(
            width,
            exact_hadamard_identity_check(width),
            spectral_ratio_squared_from_gram(width),
            c012_cover_upper_bound(width),
        )
