# RH-ANA-001 — finite Li-prefix calibration

**Authority:** `EXACT_SYNTHETIC_CALIBRATION / NO_ZETA_ZERO_EVIDENCE / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`.

## Question tested

Can a long verified finite prefix of Li-type positivity, by itself, serve as a logically sufficient global RH certificate once the zero data obey the familiar conjugation and functional-equation symmetries?

No. The exact calibration below shows why a genuinely uniform-in-index mechanism is still required.

## Source-bound criterion

Li's criterion requires non-negativity of the full infinite sequence of Li coefficients. Bombieri–Lagarias place this in a general multiset framework and relate it to Weil's criterion. This calibration uses that general logical setting only as a known-answer test; it does **not** pretend that an arbitrary finite multiset has the arithmetic structure of the Riemann zeta function.

Take

`rho = 1/4 + 100 i`

and the off-critical quartet

`Q = {rho, conj(rho), 1-rho, 1-conj(rho)}`.

This is closed under conjugation and `rho -> 1-rho`, but it is deliberately not supported on `Re(rho)=1/2`.

Set

`z = 1 - 1/rho = (159997 + 1600 i)/160001`.

The quartet transforms are `z`, `conj(z)`, `1/z`, and `1/conj(z)`. Hence its Li-transform contribution is exactly

`Lambda_n(Q) = 4 - 2 Re(z^n + z^(-n))`.

The repository checker evaluates this recurrence using `fractions.Fraction`; floating point is not used to decide any sign.

## Exact result

The checker proves:

- `Lambda_n(Q) > 0` for every `1 <= n <= 626`;
- `Lambda_627(Q) < 0`.

For readability only,

- `Lambda_1 ≈ 1.9999125e-4`;
- `Lambda_626 ≈ 5.9385921e-4`;
- `Lambda_627 ≈ -1.3880873e-4`.

The exact fraction strings are not committed because they contain thousands of decimal digits; their SHA-256 values are bound in `05_oracles/RH_ANA_001_LI_PREFIX_CALIBRATION_20260811.json` and recomputed by the regression test.

## What this refutes

Inside the stated synthetic-multiset scope, this refutes the inference pattern

> sufficiently many initial Li signs are positive, therefore the all-index positivity obligation is effectively settled.

The problem is not Li's criterion. The problem is the attempted finite-to-infinite shortcut. A planted off-critical defect can remain invisible to hundreds of initial coordinates.

## What this does not refute

This does not show that any actual zeta zero is off the critical line. It does not refute Li's all-`n` criterion, Weil's criterion, Nyman–Beurling, mollifier methods, or any argument that supplies additional zeta-specific arithmetic structure plus a valid uniform theorem.

## Localized residual

The next analytic atom is `RH-ANA-002`:

> identify and falsify the weakest zeta-specific mechanism that can prove or propagate Li positivity uniformly for all coefficient indices, preferably through a prime-side/explicit-formula representation with an auditable tail bound, without assuming RH-equivalent zero-location information.

A candidate that only extends the verified finite prefix is low-information unless it also closes this uniformity bridge.

## Primary sources

- Xian-Jin Li, *The Positivity of a Sequence of Numbers and the Riemann Hypothesis*, Journal of Number Theory 65 (1997), 325–333, DOI `10.1006/jnth.1997.2137`.
- Enrico Bombieri and Jeffrey C. Lagarias, *Complements to Li's Criterion for the Riemann Hypothesis*, Journal of Number Theory 77 (1999), 274–287, DOI `10.1006/jnth.1999.2392`.

The parameter choice and repository calibration are retained for falsification value only; no novelty claim is made.
