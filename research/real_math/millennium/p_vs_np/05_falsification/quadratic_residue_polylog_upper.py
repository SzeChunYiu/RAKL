"""Finite specification checks for C020.

This module validates the quadratic-residue relation used by the C020
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
    """Return the block-count envelope used in the C020 proof.

    Double-and-add multiplication uses at most two modular-add blocks per
    multiplier bit. Fixed-exponent square-and-multiply uses at most two
    modular multiplications per exponent bit. Each modular-add/mux block has
    linear Boolean size, giving an overall cubic gate envelope.
    """
    n = bit_width(p)
    return ArithmeticSchedule(
        bit_width=n,
        modular_add_calls_per_multiply_upper=2 * n,
        modular_multiply_calls_per_power_upper=2 * n,
    )


def quadratic_residues(p: int) -> set[int]:
    return {pow(x, 2, p) for x in range(1, p)}


def qr_relation_direct(p: int, x: int, y: int) -> bool:
    return (y - x) % p in quadratic_residues(p)


def qr_relation_via_euler(p: int, x: int, y: int) -> bool:
    d = (y - x) % p
    return pow(d, (p - 1) // 2, p) == 1


def exhaustive_relation_check(p: int) -> bool:
    return all(
        qr_relation_direct(p, x, y) == qr_relation_via_euler(p, x, y)
        for x in range(p)
        for y in range(p)
    )


if __name__ == "__main__":
    for prime in (3, 5, 7, 11, 19, 43, 59):
        print(prime, exhaustive_relation_check(prime), arithmetic_schedule(prime))
