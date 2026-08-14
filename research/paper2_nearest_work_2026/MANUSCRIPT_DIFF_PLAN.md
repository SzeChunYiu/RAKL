# Paper II manuscript diff plan — #487 nearest-work audit

Date: 2026-08-14. Proposal only. No manuscript file is edited by this audit.

## DELETE — claims that will not survive review

**Abstract, and `01b_shared_experience_nearest_work.tex`.** Any sentence
presenting as residual novelty the conjunction "directional … binds QoI, source
preconditions, role mappings, preserved invariants, target boundaries and
uncertainty … fail-closed". Every one of those conjuncts is in the `sID`
signature of Bareinboim & Pearl (AAAI 2012), and their FAIL branch is *stronger*
than fail-closed — Corollary 3 makes refusal a certificate of impossibility.

**Anywhere reporting invalid-transfer false-accept alone.** A trivial
always-REJECT gate attains false-accept 0.000. Report the paired
valid-transfer retention figure with every false-accept figure or delete the
sentence.

## NARROW — claims that survive only at reduced scope

**Abstract sentence on the six-family extension.** The extension has now been
executed (seed `2026081212`, n=810) and passes every registered gate. It must
not be reported as broad generalization: the gate is non-falsifiable (12/12
arbitrary seeds give 6/6, p=0.03125), the full arm is the gold function with
constant loss 0.0004, 66.7% of the gain comes from two strata with mechanism
exact3 of exactly 0.000, and scrambling all natural-language text leaves gold
unchanged 810/810. Report as scoped known-world coordinate specification.
Evidence: PR #593.

**§03c objective confirmatory result.** The existing disclaimer ("does not
establish that a system recovers them from unstructured prose") is correct but
too weak. Strengthen: the benchmark contains *zero* extraction signal, not
merely insufficient signal — no arm except the lexical diagnostic reads the
task text at all.

**§02b directionality evidence.** Directionality is not novel. Transportability
is directional by construction (Π → Π\*). Narrow to the cross-vocabulary case
where the correspondence must be established rather than assumed.

## STRENGTHEN — the four surviving residuals

Rewrite the residual novelty claim to exactly these, and only these:

1. **The returned third verdict.** Transportability is complete *conditional on
   a fully specified selection diagram* and has no way to return "I cannot
   evaluate this". PNAS 2016 p. 7351 pushes that case outside the formalism as a
   user obligation. A contract that *returns* `CANNOT_CHECK` when its own
   preconditions are unverifiable is genuinely outside it.
2. **Cross-vocabulary role/relation mapping under a licence.** Transportability
   presumes shared variable identity; SMT/SME maps but does not license. Nobody
   does both.
3. **Applicability without a causal graph, over non-causal research artifacts.**
4. **Explicit forbidden-loss enumeration.** No counterpart found in any of the
   five searched literature families.

## ADD — new prose required

**§01b.** A paragraph naming Bareinboim & Pearl as the **acknowledged formal
parent** of the transport contract, with the conjunct-by-conjunct table from
`NOVELTY_THREAT_RANKING.md`. Presenting this as ordinary related work will read
as either ignorance or concealment.

**§01b.** A distinguishing paragraph for SKILL.nb (`arXiv:2606.08049`), the
nearest live contemporary in reusable-experience governance. A reviewer who
knows it will raise it.

**§01b.** One sentence each conceding that SMT/SME owns role/relation mapping
and that selective-prediction/conformal owns the abstain channel.

**§05 evaluation plan.** The mandatory arm set from
`COMPARATOR_REQUIREMENTS.md`, above all a transportability oracle comparator on
items expressible as causal transport problems.

## CORRECT — factual error

`ARN: Analogical Reasoning on Narratives` is **TACL 12, 2024**, not TACL 2026 as
recorded in #487. Authors: Sourati, Ilievski, Sommerauer, Jiang.

## Bibliography

Apply `BIBLIOGRAPHY_PATCH.tex` (25 entries, all primary-source verified).
