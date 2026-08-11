"""Finite specification checks for C021.

This module checks only the binding between the quadratic-residue graph relation
and a Jacobi-symbol predicate.  It does not implement Brent--Zimmermann's fast
algorithm and it carries no asymptotic proof authority.
"""

from __future__ import annotations


def jacobi_symbol(a: int, n: int) -> int:
    """Return the Jacobi symbol (a|n) for positive odd n."""
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be a positive odd integer")

    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result

        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n

    return result if n == 1 else 0


def direct_nonzero_quadratic_residues(p: int) -> set[int]:
    if p < 3 or p % 2 == 0:
        raise ValueError("p must be an odd integer at least 3")
    return {(z * z) % p for z in range(1, p)}


def qr_relation_via_jacobi(p: int, x: int, y: int) -> bool:
    if not (0 <= x < p and 0 <= y < p):
        raise ValueError("x and y must be valid row/column labels")
    d = (y - x) % p
    return jacobi_symbol(d, p) == 1


def qr_relation_direct(p: int, x: int, y: int) -> bool:
    if not (0 <= x < p and 0 <= y < p):
        raise ValueError("x and y must be valid row/column labels")
    d = (y - x) % p
    return d != 0 and d in direct_nonzero_quadratic_residues(p)


def exhaustive_relation_check(p: int) -> bool:
    return all(
        qr_relation_via_jacobi(p, x, y) == qr_relation_direct(p, x, y)
        for x in range(p)
        for y in range(p)
    )
