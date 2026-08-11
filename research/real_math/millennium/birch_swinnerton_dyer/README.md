# RAKL Verified Discovery — Birch and Swinnerton-Dyer

Persistent workspace for the Birch and Swinnerton-Dyer Millennium problem over `Q`.

## Root authority

`OPEN_NO_SOLUTION_CERTIFICATE`

The official Clay/Wiles rank statement asks whether, for every elliptic curve `E/Q`,

`ord_{s=1} L(E,s) = rank E(Q)`.

The refined formula additionally binds the leading coefficient to the Tate-Shafarevich group, the Néron-Tate regulator, the real period, bad-prime local/Tamagawa factors, and torsion. These obligations are tracked separately.

Persistent GitHub control surface: issue #91.

## Current analytic-lane atom

`BSD-A1-RANK2-BRIDGE`

The first strict atom does **not** propose a solution. It isolates the first generic rank beyond the accepted analytic-rank `0/1` regime: when `ord_{s=1}L(E,s)=2`, what unconditional arithmetic object can certify two independent Mordell-Weil directions and support the rank-two regulator/Sha contribution without assuming BSD or an equivalent-strength conjecture?

The first post-context action is a theorem-dependency audit of:

`analytic input -> arithmetic determinant/exterior object -> nontriviality -> Selmer control -> Mordell-Weil independence -> Sha control -> regulator identity -> exact leading term`.

## Source/authority anchors

- Andrew Wiles, official Clay BSD problem description: https://www.claymath.org/wp-content/uploads/2022/05/birchswin.pdf
- Clay current problem page: https://www.claymath.org/millennium/birch-and-swinnerton-dyer-conjecture/
- Gross-Zagier, Invent. Math. 84 (1986), DOI `10.1007/BF01388809`.
- Kolyvagin, Math. USSR-Izv. 32 (1989), DOI `10.1070/IM1989v032n03ABEH000779`.
- Burns-Sano, IMRN 2021, DOI `10.1093/imrn/rnz103`.
- Chan-Ho Kim, `arXiv:2203.12161`, version dated 2026-03-22; preprint authority only.
- Burungale-Tian, Annals of Mathematics 203 (2026), DOI `10.4007/annals.2026.203.1.1`; scoped CM rank-zero converse only.

Unreviewed claims of complete BSD or generic analytic-rank-two proofs are not imported as theorem authority.

## Strict discovery rule

Any materially new candidate must pass the current `main` context, dual-memory, expert-review, hash-chained trace, falsification, formalization, proof, novelty, and independent-review gates. Same-context expert roles are not independent peer review. Breakthrough-learning primitives may propose search modes but never mint theorem truth.
