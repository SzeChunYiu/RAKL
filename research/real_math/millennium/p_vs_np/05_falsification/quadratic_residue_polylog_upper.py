"""Finite specification checks for C020.

This module validates the exact modular-arithmetic recurrence used by the C020
polylogarithmic full-cover upper-bound proof draft. It does not construct a
formal Boolean circuit and finite checks are never promoted to an asymptotic
proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2


@dataclass(frozen=True)
class ArithmeticSchedule:
    bit_width: int
    modular_add_calls_per_multiply_upper: int
    modular_multiply_calls_per_power_upper: int

    @property
    def modular_add_calls_per_power_upper(self) -> int:
        return (
            self.modular_add_calls_per_multiply_upper
            * self.modular_multiply_calls_per_power_upper
        )


def bit_width(p: int) -> int:
    if p < 3:
        raise ValueError("p must be an odd prime at least 3")
    return ceil(log2(p))


def arithmetic_schedule(p: int) -> ArithmeticSchedule:
    """Return the block-count envelope used in the C020 proof."""
    n = bit_width(p)
    return ArithmeticSchedule(
        bit_width=n,
        modular_add_calls_per_multiply_upper=2 * n,
        modular_multiply_calls_per_power_upper=2 * n,
    )


def add_mod(p: int, a: int, b: int) -> int:
    """Modular addition in the residue range, matching C020-L3."""
    if not (0 <= a < p and 0 <= b < p):
        raise ValueError("operands must be canonical residues")
    total = a + b
    return total - p if total >= p else total


def mul_mod_double_and_add(p: int, a: int, b: int) -> int:
    """MSB-first double-and-add multiplication from C020-L4."""
    if not (0 <= a < p and 0 <= b < p):
        raise ValueError("operands must be canonical residues")
    result = 0
    for bit in range(bit_width(p) - 1, -1, -1):
        result = add_mod(p, result, result)
        if (b >> bit) & 1:
            result = add_mod(p, result, a)
    return result


def pow_mod_square_and_multiply(p: int, base: int, exponent: int) -> int:
    """Fixed-width square-and-multiply recurrence from C020-L5."""
    if not 0 <= base < p:
        raise ValueError("base must be a canonical residue")
    if exponent < 0 or exponent >= p:
        raise ValueError("C020 only needs fixed exponents in [0,p)")
    result = 1 % p
    for bit in range(bit_width(p) - 1, -1, -1):
        result = mul_mod_double_and_add(p, result, result)
        if (exponent >> bit) & 1:
            result = mul_mod_double_and_add(p, result, base)
    return result


def quadratic_residues(p: int) -> set[int]:
    return {pow(x, 2, p) for x in range(1, p)}


def qr_relation_direct(p: int, x: int, y: int) -> bool:
    return (y - x) % p in quadratic_residues(p)


def qr_relation_via_euler(p: int, x: int, y: int) -> bool:
    d = (y - x) % p
    return pow(d, (p - 1) // 2, p) == 1


def qr_relation_via_constructive_power(p: int, x: int, y: int) -> bool:
    d = (y - x) % p
    return pow_mod_square_and_multiply(p, d, (p - 1) // 2) == 1


def exhaustive_relation_check(p: int) -> bool:
    return all(
        qr_relation_direct(p, x, y)
        == qr_relation_via_euler(p, x, y)
        == qr_relation_via_constructive_power(p, x, y)
        for x in range(p)
        for y in range(p)
    )


if __name__ == "__main__":
    for prime in (3, 5, 7, 11, 19, 43, 59):
        print(prime, exhaustive_relation_check(prime), arithmetic_schedule(prime))
