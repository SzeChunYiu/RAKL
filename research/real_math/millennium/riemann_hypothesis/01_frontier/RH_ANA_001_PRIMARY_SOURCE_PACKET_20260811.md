# RH-ANA-001 primary-source packet — 2026-08-11

## Purpose

Source-bound pre-candidate context for the first strict analytic Riemann-Hypothesis atom. This packet does **not** propose a proof or new inequality. It fixes the exact known representations and the mismatches that a later candidate would have to repair.

## Root status and official statement

Clay Mathematics Institute lists the Riemann Hypothesis as **Unsolved** and states the root condition as all nontrivial zeros of the Riemann zeta function having real part `1/2`.

Primary/authoritative anchors:

- Clay RH page: `https://www.claymath.org/millennium/riemann-hypothesis/`
- E. Bombieri, official problem description: `https://www.claymath.org/wp-content/uploads/2022/05/riemann.pdf`

Bombieri's official description fixes the zeta/xi statement, the prime-counting error equivalence, finite-field analogues, and the Weil explicit formula. In sections IV-V it emphasizes the finite-field cohomology/Frobenius mechanism and then records Weil's classical explicit-formula criterion: for the registered class `W`, RH is equivalent to a sign condition for multiplicative autocorrelations satisfying two moment constraints. In the finite-field curve setting the analogous sign follows from an algebraic index theorem. The classical case has no corresponding proved mechanism.

## Exact-criterion contrasts

### Weil explicit-formula sign criterion

Use Bombieri's official formulation as the canonical normalization for this first atom. The load-bearing facts are:

- the explicit formula relates the nontrivial-zero sum to prime-power local terms plus an archimedean term;
- the zero sum uses a stated limiting convention;
- the RH-equivalent sign condition ranges over an infinite admissible test class of multiplicative autocorrelations;
- the test generator has two moment constraints.

The research gap is **not** to restate this criterion. It is to determine whether its arithmetic functional admits a genuinely simpler, independently provable signed decomposition or localized residual.

### Li positivity

E. Bombieri and J. C. Lagarias, *Complements to Li's Criterion for the Riemann Hypothesis*, Journal of Number Theory 77 (1999), 274–287, DOI `10.1006/jnth.1999.2392`.

Their paper records Li's exact equivalence between RH and positivity of the full coefficient sequence, gives an arithmetic formula through the Guinand-Weil explicit formula, and relates Li positivity to Weil's criterion. A finite prefix is not a root certificate.

### Nyman–Beurling–Báez-Duarte approximation

- L. Báez-Duarte, *A strengthening of the Nyman-Beurling criterion for the Riemann Hypothesis*, `https://arxiv.org/abs/math/0202141`.
- L. Báez-Duarte, *A general strong Nyman-Beurling Criterion for the Riemann Hypothesis*, `https://arxiv.org/abs/math/0505453`.

These give exact Hilbert-space closure/approximation formulations. Their value here is contrastive: the root obstruction becomes an infinite limiting assertion. Any finite-dimensional success must remain calibration unless a uniform convergence theorem closes the limit.

### Mollifier / critical-line partial progress

- J. B. Conrey, *More than two fifths of the zeros of the Riemann zeta function are on the critical line*, J. reine angew. Math. 399 (1989), 1–26, DOI `10.1515/crll.1989.399.1`.
- K. Pratt, N. Robles, A. Zaharescu, D. Zeindler, *More than five-twelfths of the zeros of zeta are on the critical line*, Research in the Mathematical Sciences 7 (2020), DOI `10.1007/s40687-019-0199-8`.

These are genuine unconditional partial-success contexts: mollified mean-value methods force a substantial positive proportion of zeros onto the line. They do not establish that every zero is on the line. The transfer question is therefore not “use a longer mollifier” in the abstract, but to identify the first exact currently-unproved uniform correlation/moment obligation that separates partial occupancy from materially stronger control.

## Finite-field solved analogue

Bombieri's official description records the decisive structural disanalogy. For curves over finite fields, zeros are tied to Frobenius acting on cohomology, and the required sign has an algebraic/geometric mechanism. For general varieties the Weil-conjecture RH statement is supplied by Deligne's cohomological theory. No such classical Frobenius/cohomology/index theorem is currently available for `zeta(s)`.

Therefore finite-field geometry is retained as a **method-transfer source**, not evidence that a corresponding classical object exists.

## Candidate-independent obstruction selected

`RH-ANA-001`: determine which exact analytic representation exposes a sub-obligation strictly cheaper than RH itself. The primary probe will dissect the Weil arithmetic functional and build a known-answer/failure benchmark that rejects:

1. finite-to-infinite extrapolation;
2. restriction to a convenient test subclass without a density/continuity theorem;
3. a sign identity that is merely RH in disguised form;
4. a transform or zero-sum manipulation with unproved convergence/order interchange;
5. a partial critical-line proportion presented as universal zero control.

No mathematical candidate is generated in this packet.

## Source cutoff

Source refresh performed 2026-08-11. Technical claims above are anchored to the official Clay/Bombieri problem description and the named primary research papers. Later novelty work must refresh its own literature world rather than treating this bounded packet as a novelty certificate.
