"""Executable regression helpers for C012.

These routines check the Boolean recurrence and arithmetic used in the
source-derived parity-correlation cover ceiling. They are not a proof of an
asymptotic circuit lower bound and do not compute cover complexity.
"""

from __future__ import annotations


def xor_complement_pair(p: bool, q: bool, r: bool, s: bool) -> tuple[bool, bool]:
    """Apply the two-intersection recurrence from C012-L1.

    Preconditions are q == (not p) and s == (not r).
    The returned pair is (p XOR r, NOT(p XOR r)).
    """

    if q is not (not p):
        raise ValueError("q must be the Boolean complement of p")
    if s is not (not r):
        raise ValueError("s must be the Boolean complement of r")

    p_next = (p or r) and (q or s)
    q_next = (p or s) and (q or r)
    return p_next, q_next


def parity_with_complement(bits: tuple[bool, ...]) -> tuple[bool, bool]:
    """Evaluate parity via the C012 recurrence while maintaining its complement."""

    if not bits:
        raise ValueError("bits must be non-empty")

    p = bits[0]
    q = not p
    for bit in bits[1:]:
        p, q = xor_complement_pair(p, q, bit, not bit)
    return p, q


def c012_intersection_upper_bound(t: int, local_one: int, local_zero: int) -> int:
    """Return t(a+b)+2(t-1), the C012 construction bound."""

    if t < 1:
        raise ValueError("t must be positive")
    if local_one < 0 or local_zero < 0:
        raise ValueError("local intersection counts must be non-negative")
    return t * (local_one + local_zero) + 2 * (t - 1)


def inner_product_mod2(x: int, y: int, t: int) -> bool:
    """Return the mod-2 inner product of two t-bit integers."""

    if t < 1:
        raise ValueError("t must be positive")
    mask = (1 << t) - 1
    if x < 0 or y < 0 or x > mask or y > mask:
        raise ValueError("x and y must fit in t bits")
    return ((x & y).bit_count() & 1) == 1


def inner_product_via_local_parity(x: int, y: int, t: int) -> bool:
    """Compute inner product as parity of t local AND predicates."""

    bits = tuple(bool(((x >> i) & 1) and ((y >> i) & 1)) for i in range(t))
    parity, complement = parity_with_complement(bits)
    assert complement is (not parity)
    return parity
