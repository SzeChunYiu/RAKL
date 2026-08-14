# Paper I / Epistemic Mechanics Extensions

## M6 — Active Fibre Discriminator (AFD)

Issue #539 already has this idea for diagnosis. Generalize it to every open fibre.

Let competing hypotheses be \(H=\{h_i\}\), admissible probes \(A\), and

\[
\pi_t(h)=P(h\mid D_t).
\]

Let decision risk be

\[
R(\pi)=\min_d \mathbb E_\pi[L(d,h)].
\]

For probe \(a\),

\[
VOI(a)=R(\pi_t)-\mathbb E_y[R(\pi_{t+1}^{a,y})]-c(a).
\]

Choose

\[
a^\*=\arg\max_{a\in A} VOI(a)
\]

when positive.

If probabilities are unjustified, use an ordinal/set-valued variant maximizing worst-case elimination of live environments or load-bearing distinctions.

Output is an `EvidenceAcquisitionProposal`, never authority.

### CANNOT_CHECK repair

`CANNOT_CHECK` should carry:

- missing load-bearing coordinate;
- admissible acquisition actions;
- expected cost;
- expiry;
- reason no cheaper probe suffices.

---

## M7 — Value-of-Information Saturation (VOIS)

Do not modify the frozen issue #630 revival. This is a later successor only if required.

Relative to declared action set \(A_t\), a fibre is VOI-saturated when

\[
\sup_{a\in A_t} VOI(a)\le\tau
\]

and no admitted representation mutation has positive expected decision value.

Certificate binds:

- action/query universe;
- utility/loss class;
- cost model;
- current hypothesis/representation set;
- expiry/reopen conditions.

If action enumeration is incomplete:

`CANNOT_CERTIFY_SATURATION`.

New evidence, a new parent, or a new representation reopens saturation.

---

## M8 — Assumption + Argument Environments (AAE)

Let \(A\) be defeasible assumptions.

An argument:

\[
\alpha=(Prem_\alpha,Rule_\alpha,Conc_\alpha,E_\alpha).
\]

An environment \(\Gamma\subseteq A\) supports \(\alpha\) if its premises are derivable under \(\Gamma\).

Maintain minimal nogoods:

\[
\mathcal N=\{\Gamma:\Gamma\text{ is minimally inconsistent}\}.
\]

Environment admissibility:

\[
\nexists N\in\mathcal N:N\subseteq\Gamma.
\]

Add typed attack relation

\[
\alpha\leadsto\beta
\]

with kinds `REBUT`, `UNDERCUT`, `EVIDENCE_ATTACK`, `SCOPE_ATTACK`.

Claim status becomes environment-indexed:

\[
status(c,\Gamma)\in
\{\mathrm{SUPPORTED},\mathrm{DEFEATED},\mathrm{UNDECIDED}\}.
\]

No forced deletion of a claim merely because another environment defeats it.

---

## M9 — Source-Monitoring Firewall (SMF)

For claim \(c\), maintain

\[
M(c)=(\mathrm{evidence\ roots},
\mathrm{source\ attribution},
\mathrm{competence},
\mathrm{familiarity},
\mathrm{exposure},
\mathrm{retrieval\ count}).
\]

Hard invariant:

\[
\frac{\partial Auth(c)}{\partial familiarity}=0,
\]

and likewise for exposure/retrieval count absent new admissible evidence.

Derived memories cannot amplify source authority.

If source-attribution confidence is insufficient while the claim is load-bearing:

`CANNOT_CHECK_SOURCE` + provenance-refresh action.

Adversarial benchmark: repeat/retrieve one fluent unsupported claim many times; authority must not move.

---

## M10 — Failure-Mode Triangulation Ledger (FMT)

Each evidence approach \(e\) declares key bias/failure modes

\[
B_e\subseteq\mathcal B
\]

and, where defensible, expected bias directions

\[
d_e:B_e\to\{-1,+1,?,0\}.
\]

A triangulation set \(T\) must address the same QoI/scope.

Count of papers is not the quantity.

A simple common-bias exclusion certificate requires

\[
\bigcap_{e\in T} B_e=\varnothing
\]

for the registered load-bearing bias universe, or a stronger domain-specific criterion.

This only says no single registered bias mechanism explains all concordant evidence. It does not prove truth.

Authority upgrade may require both evidence-root independence and bias-family diversity.

---

## M11 — Decision-Sufficient Projection (DSP)

Let canonical worlds be \(S\) and a declared decision class be \(D\).

Projection

\[
\pi:S\to Z
\]

is \(D\)-sufficient if, for every decision problem in \(D\), optimal risk using \(\pi(S)\) equals optimal risk using the full registered state.

When assumptions permit, compare projections in a Blackwell-style information order.

Seek the coarsest projection sufficient for the registered decision class.

This generalizes Paper I's collision theorem: a projection collision with different required actions immediately proves insufficiency.

---

## M12 — Dual-Store Schema Consolidation (DSC)

Fast store:

\[
F_t=\{\mathrm{immutable\ episodes,receipts,failures}\}.
\]

Slow store:

\[
G_t=\{\mathrm{proposal\!-\!grade\ schemas/lessons/mechanics}\}.
\]

Consolidator

\[
C:F^k\to SchemaProposal
\]

must use diverse episodes and run:

- negative replay;
- near-miss replay;
- boundary/regime replay;
- stale/superseded replay;
- fresh holdout assurance.

No schema consolidation deletes the underlying episode record.

A learned schema starts at authority floor and may affect routing only under its own admission contract.
