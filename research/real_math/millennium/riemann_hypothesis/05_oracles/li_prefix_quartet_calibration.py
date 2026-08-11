#!/usr/bin/env python3
"""Exact synthetic Li-coefficient calibration for RH analytic research.

This is a known-answer falsifier, not a model of the actual zeta zero set.
For the off-critical functional-equation/conjugation-symmetric quartet

    Q = {rho, conj(rho), 1-rho, 1-conj(rho)},
    rho = 1/4 + 100 i,

let z = 1 - 1/rho.  The quartet contribution to the Li transform is

    Lambda_n(Q) = 4 - 2 Re(z**n + z**(-n)).

All sign decisions are made with fractions.Fraction; floating point is used
only for optional human-readable approximations.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from typing import Iterable


ComplexQ = tuple[Fraction, Fraction]


def _mul(a: ComplexQ, b: ComplexQ) -> ComplexQ:
    return (
        a[0] * b[0] - a[1] * b[1],
        a[0] * b[1] + a[1] * b[0],
    )


def _inv(a: ComplexQ) -> ComplexQ:
    norm = a[0] * a[0] + a[1] * a[1]
    if norm == 0:
        raise ZeroDivisionError("cannot invert zero")
    return (a[0] / norm, -a[1] / norm)


def _fraction_sha256(value: Fraction) -> str:
    payload = f"{value.numerator}/{value.denominator}".encode("ascii")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def quartet_transform(
    beta: Fraction = Fraction(1, 4),
    gamma: Fraction = Fraction(100, 1),
) -> ComplexQ:
    """Return z = 1 - 1/rho exactly for rho = beta + i gamma."""

    norm = beta * beta + gamma * gamma
    inv_rho = (beta / norm, -gamma / norm)
    return (Fraction(1, 1) - inv_rho[0], -inv_rho[1])


def li_quartet_values(
    limit: int = 627,
    *,
    beta: Fraction = Fraction(1, 4),
    gamma: Fraction = Fraction(100, 1),
) -> tuple[Fraction, ...]:
    """Compute Lambda_1(Q), ..., Lambda_limit(Q) exactly."""

    if limit < 1:
        raise ValueError("limit must be positive")
    z = quartet_transform(beta, gamma)
    z_inv = _inv(z)
    z_power: ComplexQ = (Fraction(1, 1), Fraction(0, 1))
    z_inv_power: ComplexQ = (Fraction(1, 1), Fraction(0, 1))
    values: list[Fraction] = []
    for _ in range(limit):
        z_power = _mul(z_power, z)
        z_inv_power = _mul(z_inv_power, z_inv)
        values.append(
            Fraction(4, 1) - 2 * (z_power[0] + z_inv_power[0])
        )
    return tuple(values)


def first_negative(values: Iterable[Fraction]) -> tuple[int, Fraction] | None:
    for index, value in enumerate(values, start=1):
        if value < 0:
            return index, value
    return None


def calibration_summary(limit: int = 627) -> dict[str, object]:
    z = quartet_transform()
    values = li_quartet_values(limit)
    negative = first_negative(values)
    if negative is None:
        raise ValueError("requested range contains no negative value")
    index, value = negative
    return {
        "z_real": f"{z[0].numerator}/{z[0].denominator}",
        "z_imag": f"{z[1].numerator}/{z[1].denominator}",
        "checked_through": limit,
        "positive_through": index - 1,
        "first_negative_index": index,
        "lambda_1_exact_fraction_sha256": _fraction_sha256(values[0]),
        "lambda_626_exact_fraction_sha256": _fraction_sha256(values[625]),
        "lambda_627_exact_fraction_sha256": _fraction_sha256(value),
        "lambda_1_approx": float(values[0]),
        "lambda_626_approx": float(values[625]),
        "lambda_627_approx": float(value),
    }


if __name__ == "__main__":
    print(json.dumps(calibration_summary(), indent=2, sort_keys=True))
