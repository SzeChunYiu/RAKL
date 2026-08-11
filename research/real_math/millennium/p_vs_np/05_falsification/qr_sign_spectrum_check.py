"""Exact finite checks for the C022 quadratic-residue sign-matrix identities.

This module is a calibration/falsification oracle only.  It verifies integer matrix
identities on small primes; it is not an asymptotic proof system and does not mint
cover-complexity or P-vs-NP authority.
"""

from __future__ import annotations


def _is_prime(p: int) -> bool:
    if p < 2:
        return False
    d = 2
    while d * d <= p:
        if p % d == 0:
            return False
        d += 1
    return True


def quadratic_character(a: int, p: int) -> int:
    """Return the Legendre character in {-1,0,+1} for an odd prime p."""
    if not _is_prime(p) or p % 2 == 0:
        raise ValueError("p must be an odd prime")
    a %= p
    if a == 0:
        return 0
    value = pow(a, (p - 1) // 2, p)
    if value == 1:
        return 1
    if value == p - 1:
        return -1
    raise AssertionError("Euler criterion returned an impossible value")


def character_matrix(p: int) -> list[list[int]]:
    return [
        [quadratic_character(y - x, p) for y in range(p)]
        for x in range(p)
    ]


def qr_sign_matrix(p: int) -> list[list[int]]:
    """+1 on nonzero QR differences, -1 otherwise, including the diagonal."""
    c = character_matrix(p)
    return [
        [c[x][y] - (1 if x == y else 0) for y in range(p)]
        for x in range(p)
    ]


def gram(matrix: list[list[int]]) -> list[list[int]]:
    rows = len(matrix)
    cols = len(matrix[0])
    if any(len(row) != cols for row in matrix):
        raise ValueError("matrix must be rectangular")
    return [
        [sum(matrix[i][k] * matrix[j][k] for k in range(cols)) for j in range(rows)]
        for i in range(rows)
    ]


def expected_character_gram(p: int) -> list[list[int]]:
    # p I - J: diagonal p-1, off-diagonal -1.
    return [
        [(p - 1) if i == j else -1 for j in range(p)]
        for i in range(p)
    ]


def expected_qr_sign_gram(p: int) -> list[list[int]]:
    """Return the exact C022 formula for A_p A_p^T."""
    c = character_matrix(p)
    eps = quadratic_character(-1, p)
    return [
        [
            (p + 1) * (1 if i == j else 0)
            - 1
            - (1 + eps) * c[i][j]
            for j in range(p)
        ]
        for i in range(p)
    ]


def exact_identity_check(p: int) -> bool:
    c = character_matrix(p)
    a = qr_sign_matrix(p)

    if gram(c) != expected_character_gram(p):
        return False
    if gram(a) != expected_qr_sign_gram(p):
        return False

    eps = quadratic_character(-1, p)
    for i in range(p):
        for j in range(p):
            if c[j][i] != eps * c[i][j]:
                return False
    return True


def predicted_operator_norm_squared(p: int) -> tuple[str, int]:
    """Encode the exact norm formula without floating-point comparison.

    Returns:
      ("integer", p+1) for p == 3 mod 4, meaning ||A||^2 = p+1.
      ("sqrt_plus_one", p) for p == 1 mod 4, meaning ||A|| = sqrt(p)+1.
    """
    if not _is_prime(p) or p % 2 == 0:
        raise ValueError("p must be an odd prime")
    if p % 4 == 3:
        return ("integer", p + 1)
    return ("sqrt_plus_one", p)


if __name__ == "__main__":
    for prime in (3, 5, 7, 11, 13, 17, 19, 23, 29, 31):
        print(prime, exact_identity_check(prime), predicted_operator_norm_squared(prime))
