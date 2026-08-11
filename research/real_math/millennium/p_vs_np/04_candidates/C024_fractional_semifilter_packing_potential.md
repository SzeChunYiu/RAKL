# C024 — Fractional semi-filter packing as a cyclic-fusion potential

**Atom:** `O9d12a2a1`

**Authority:** `SOURCE_BOUND_DERIVED_PROOF_DRAFT / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

## Frozen candidate

Let `A ⊂ Γ` be non-trivial, let `B ⊆ P(Γ)` be non-empty, and set `U=A^c`. Use the Cavalar–Oliveira cover graph `Φ_{A,B}=(V_pairs,V_filters,E)`: a right vertex is a semi-filter over `U` that is above some `a∈A`; a pair `p=(E,H)` is adjacent to a semi-filter `F` exactly when `F` does not preserve `p`.

A **fractional semi-filter packing** is a non-negative weight vector

`w : V_filters -> R_{>=0}`

such that for every pair `p∈V_pairs`,

`sum_{F adjacent to p} w(F) <= 1`.

Write `W(w)=sum_F w(F)`.

### Claim C024

For every fractional semi-filter packing `w`,

`D^cyc_intersection(A | B) = rho(A,B) >= W(w)`.

Equivalently, the non-scalar certificate `w` induces a local potential on any family `Λ` of counted fusion/intersection pairs,

`Phi_w(Λ) = sum_{F : some p∈Λ is adjacent to F} w(F)`,

with the following properties:

1. free unions change `Phi_w` by `0`;
2. adding one counted intersection pair changes `Phi_w` by at most `1`;
3. repeated reuse of the same pair or already-covered semi-filter contributes no new weight;
4. if `Λ` is the intersection-pair family of a cyclic construction generating `A`, then `Phi_w(Λ)=W(w)`.

Thus `W(w)` is a cyclic-reuse-safe lower-bound certificate.

## Proof draft

Cavalar–Oliveira Definition 21 identifies `rho(A,B)` with the minimum number of pair vertices whose neighbourhoods cover all relevant semi-filters, and Theorem 30 proves `rho(A,B)=D^cyc_intersection(A|B)`.

Let `Λ` be any pair cover of `V_filters`. Since its pair neighbourhoods cover every `F`,

`W(w) <= sum_{p∈Λ} sum_{F adjacent to p} w(F) <= sum_{p∈Λ} 1 = |Λ|`.

Taking the minimum over pair covers gives `W(w)<=rho(A,B)`. Theorem 30 gives the cyclic-intersection statement.

For the local-potential form, adding a pair `p` can newly cover only semi-filters adjacent to `p`; their total weight is at most `1` by feasibility. Union operations do not add a pair vertex. Defining the potential by the set of already-covered semi-filters makes duplicate/reused coverage idempotent. Finally, the pair family extracted from any cyclic construction generating `A` covers all relevant semi-filters in the exact-characterization proof, so the terminal potential is `W(w)`.

## Counterexample-first checks

- **Feasibility is load-bearing.** If the constraint `sum_{F~p}w(F)<=1` is dropped, concentrate arbitrarily large weight on a semi-filter adjacent to one pair; a single fusion then creates arbitrarily large potential. The local law fails immediately.
- **Additive charging without deduplication is unsafe.** Charging weight every time a semi-filter is re-covered would let cyclic reuse double-count. `Phi_w` therefore depends on the union of covered neighbourhoods, not on a multiset of operational visits.
- **Target value is not automatic.** The theorem supplies only a certificate interface. It does not imply the existence of an explicit target with `W(w)=omega(log N)`, nor that the fractional relaxation has a small integrality gap.

## Expert-cell same-context discussion

- **Complexity / graph-cover lead:** accepts the derivation as a direct consequence of the source-defined cover graph plus Theorem 30; no root implication is created.
- **Combinatorics / optimization lead:** identifies the certificate as the standard fractional set-cover dual packing specialized to semi-filters. This sharply raises rediscovery risk and blocks a novelty claim.
- **Adversarial falsification lead:** accepts only after making pair-feasibility and deduplication explicit; without either, one-step boundedness is false.
- **Formal-methods lead:** classifies this as a source-bound proof draft. No theorem-prover artifact or isolated proof recheck exists.
- **Novelty / research-value lead:** `NO_NOVELTY_CLAIM`; value is representational: it converts the vague non-scalar-potential residual into an explicit dual-certificate search problem.
- **Learning-control lead:** the useful mode was `REFLECTIVE_RESTRUCTURE + CONTRASTIVE_DISCRIMINATION`: instead of inventing another graph statistic, move to the cover graph already known to be an exact set-cover object and ask what certificate has a fusion-local budget by construction.

These are role-separated same-context passes, not independent review.

## Epistemic consequence

C024 closes only the **existence of a generic local-law interface**. It relocates the hard part from “find any cyclic-reuse-safe potential” to:

`C024-R1: construct an explicit, analysable pair-feasible weighting of relevant semi-filters with total mass omega(log N), for a target that also survives the existing upper-bound adversaries; or prove a ceiling for a broad candidate weighting class.`

The highest-partition next probe is not a full lower-bound proof. It is a symmetry-reduced fractional-packing calculation/derivation on calibration targets (first `G_NEQ`, then an R004 survivor such as QR only if the calibration does not collapse). A logarithmic/constant ceiling would kill the naive weighting family cheaply; super-log mass would create a bounded lower-bound candidate requiring fresh target-specific assurance.

## Primary source

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (2025), especially Definitions 18–21 and Theorem 30. The paper explicitly states that the cover graph is a set-cover instance and proves `rho(A,B)=D^cyc_intersection(A|B)`.
