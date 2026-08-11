# Closest-parent primary-source audit

Issue #156 · 2026-08-11 · Detail file for
[`PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md`](../PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md)

Per-parent extraction of object, update rule, authority semantics, persistence,
failure/repair, evidence and stated limitations. **Evidence level is recorded
per parent and governs what any matrix row measured against it may claim.**

| Parent | arXiv | Version | Evidence level |
|---|---|---|---|
| MemTX | 2607.23929 | v2, 2026-07-28 | `FULL_TEXT` |
| PPMF | 2607.29167 | v1, 2026-07-31 | `FULL_TEXT_PARTIAL` (pp. 1–6; appendices A–I unread) |
| AutoSci | 2605.31468 | v1, 2026-05-29 | `ABSTRACT_AND_REPO` |
| MemClaw | 2606.24535 | v1, 2026-06-23 | `ABSTRACT_ONLY` |
| AI-scientists audit | 2604.18805 | v1, 2026-04-20 | `ABSTRACT_ONLY` |

---

## MemTX — `FULL_TEXT`

**Object.** A governed record, not an opaque string: entity, attribute, value;
source with an authority weight; a permission block (owner, reader roles,
writer roles, share scope private/shared/public); derived-from edges forming a
derivation DAG; a type from {beliefs, summaries, profiles, index entries,
shared copies, tool actions}; a validity interval against a logical clock; and
the writer's confidence. Eight-state lifecycle: raw → tentative → validated →
committed → action-safe, plus quarantined, superseded, revoked.

**Update rule.** "A write is not a commit." A transaction declares a risk tier,
maps it to one of five isolation levels (raw-read, committed-read,
verified-read, causally-stable-read, action-safe-read) and captures a snapshot.
Writes stage as tentative, invisible at committed-read and above, then face four
ordered checks: evidence (confidence ≥ 0.6 unless source authority ≥ 0.9),
validity, rule-based semantic conflict on the entity+attribute slot, and
dependency stability against pending revocations. Failures quarantine with a
machine-readable reason.

**Authority.** A scalar weight on the record's **source** — not on claim kind.
Conflicts adjudicate by source authority, but **temporal precedence outranks
it**: a candidate whose rival committed after the snapshot aborts before any
authority comparison. Permissions inherit through derivation, and the conflict
detector blocks republishing a private-scope parent into a wider scope. Risk
tier is trusted harness configuration, not agent output, so a compromised agent
cannot downgrade past the gate.

**Failure/repair.** Abort and revocation share one routine over transitive
descendants, dispatching by type: beliefs revoked; summaries, profiles, index
entries and shared copies quarantined for rebuild; tool actions compensated if
reversible, else recorded as leaked irreversible effects. Every repair emits a
rollback-log entry.

**Evidence.** Invariants I1 (action-safety gating), I2 (cascade-repair
completeness) and corollary G3 (no committed or action-safe record has a revoked
transitive ancestor), via property-based testing over 10,000 traces plus bounded
exhaustive enumeration: 5,530,160 canonical states, 10,537,260 transitions, zero
violations. The checker recomputes reachability from each record's own
provenance rather than trusting the manager's bookkeeping. G3 verification
exposed a missed-cascade defect on the abort path, kept as a regression test.

**Stated limitations.** Repair covers only *recorded* provenance — an unwritten
derivation is never repaired. Compensation is a logged decision-level
obligation, not environment-level replay. Reversibility is a static per-tool
designation. Verification is bounded and runtime-level, "deliberately weaker
than the unbounded soundness theorems of prior formal work". Two negative
results are preserved: a **source-scope** blind spot where the agent transcribes
content without declaring the parent, so a declarative lineage check has nothing
to inspect; and a **temporal-scope** blind spot where retrying in a fresh
transaction makes a late write no longer late. The authors name the shared
shape — protections scope to a single commit or transaction — and call
provenance that follows content to action time "the most principled open
problem this conformance suite exposes".

**Relevance.** Owns transactional commit, provenance retention, supersession,
cascade repair and proposal-only staging. Its authority is source-typed, which
is where RAKL's residual lives.

---

## PPMF — `FULL_TEXT_PARTIAL` (pp. 1–6)

**Object.** `m = (c, s, τ, h, r, e)` — content, source, trust, transformation
history, risk labels, external-derived flag. Trust lattice
`U < E < T < H < C < S` = Unknown, External, TrustedTool, UserHistory,
User_Confirmed, System.

**Threat model.** *Memory provenance laundering*: during LLM consolidation an
external observation is rewritten so it looks like user history or workflow
support, "preserving an action trigger while erasing the low-trust source that
should limit its authority". The harmful object is an unauthorized authority
upgrade, not a malicious token sequence — so content filtering does not reach
it.

**The invariant.** For a memory `m = C(O)` derived from observations
`O = {oᵢ}`, each action-relevant claim `q ∈ m`

> auth(q, m) ⪯ min<sub>⪯</sub> { auth(oᵢ) : oᵢ ∈ supp(q) }

unless a platform-recorded declassification event bound to the same user
principal, action target, risk class and scope applies. Trust metadata is
platform-maintained; the gate reads only `(s, τ, h, r, e)` and ignores textual
cues, so a memory whose content says "user-confirmed" gains nothing.

**Gating.** Deterministic and pointer-first, not LLM-mediated. Action risk
labels READ, NAV, EFFECT, PURCHASE, CREDENTIAL; the implemented policy requires
at least External for READ, UserHistory for NAV, and User_Confirmed for EFFECT,
PURCHASE and CREDENTIAL. Ambiguous or conflicting support keeps all candidates
and the gate uses the **least trusted** support. Trusted-tool output inherits
the least trusted input taint.

**Scope.** Action and tool risk under indirect prompt injection (cs.CR). `q` is
"a schema-level claim linking a memory span to an action argument". **No
representation, mechanism or identification distinction appears anywhere in the
read sections.**

**Stated limitations.** The guarantee is conditional: "platform forgery or
mislabeling breaks the boundary". Cross-channel attacks that socially engineer a
real confirmation are out of the threat model. And explicitly: "A PPMF ASR of
0.000 means that no unauthorized high-risk action passes under the stated
provenance and risk-policy assumptions; it is not a claim of universal
robustness."

**Relevance.** This is the parent that owns non-amplification. RAKL cannot claim
it. What PPMF cannot express is *what kind of scientific support* a claim
carries — its ladder is over channels, and its claims are about action
arguments.

---

## AutoSci — `ABSTRACT_AND_REPO`

**Modules.** SciMem (Long-Term Knowledge Memory + Active Research Memory),
SciFlow (five-stage lifecycle from literature understanding to rebuttal),
SciDAG (DAG-structured multi-agent operators plus stage templates), SciEvolve
(feedback from users, experiments, reviews and environment into versioned
updates to memory organisation, skills and templates).

**Repository.** `github.com/skyllwt/AutoSci`, public, MIT, ~98 commits. The full
four-module paper system is on the `paper` branch at tag `arxiv-v1`; `main` is a
Claude-Code-oriented build. Requires an authenticated agent runtime; optional
Semantic Scholar / LLM review keys.

**Unread and needed.** `CANNOT_CHECK` on authority semantics, failure/repair
semantics and stated limitations — the abstract page carries none of them.

**Why this matters most.** AutoSci is the closest parent for four matrix rows.
Its SciEvolve module is the direct counterexample candidate for RAKL's
experience→authority noninterference residual. The decisive question is whether
SciEvolve's versioned updates can alter Long-Term Knowledge Memory *records*, or
only skills, templates and memory organisation. Read that first.

---

## MemClaw / Governed Shared Memory — `ABSTRACT_ONLY`

Production multi-tenant memory service with scoped retrieval, temporal
supersession, provenance tracking and policy-governed propagation, exercised by
the ArgusFleet harness over four governance dimensions. Writes are admitted
through a pipeline; conflicts resolve by temporal supersession with asynchronous
contradiction detection. Tenant/sub-tenant scoping reports zero cross-fleet
leakage and reconstruction of depth-four derivation chains.

Two production defects are preserved in the paper: sub-tenant scope bypassed on
direct GET-by-id for agent-scoped credentials, and a pipeline-ordering conflict
where a synchronous near-duplicate filter rejects contradictory writes before
the asynchronous contradiction detector sees them. The authors state it is a
measurement of one live service, explicitly "rather than a baseline comparison".

**Classification.** `CONCEPTUAL_COMPARISON_ONLY` — a proprietary service, not
reproducible and not fairly comparable as an experimental arm.

---

## AI scientists produce results without reasoning scientifically — `ABSTRACT_ONLY`

Not a system: an audit of >25,000 agent runs across eight domains. Base model
explains 41.4% of variance versus 1.5% for the scaffold. Evidence disregarded in
68% of traces; belief updated on refuting evidence in 26%. Deficits survive
being handed near-complete successful trajectories.

**Role.** Motivation and an external prior on baseline behaviour, and the
closest parent for the scientific-transition-audit row. Adjudicating that row
needs its trace coding scheme in full text — specifically whether its
annotations distinguish *types* of belief update or only whether one occurred.

**Classification.** `CONCEPTUAL_COMPARISON_ONLY`.

---

## Feasibility summary

| Parent | Classification | Why |
|---|---|---|
| AutoSci | `BLACK_BOX_PUBLIC_SYSTEM_FEASIBLE` | public MIT code, but needs an authenticated agent runtime and the paper system is on a separate frozen branch; exact reproduction of paper results is not established |
| MemTX | `FUNCTION_MATCHED_ABLATION_FEASIBLE` | no public implementation located; the commit-discipline function is reproducible as a RAKL-internal arm |
| PPMF | `FUNCTION_MATCHED_ABLATION_FEASIBLE` | no public implementation located; the non-amplification rule is simple enough to implement faithfully |
| MemClaw | `CONCEPTUAL_COMPARISON_ONLY` | proprietary production service |
| 2604.18805 | `CONCEPTUAL_COMPARISON_ONLY` | a measurement study, not a system |

No RAKL arm may be labelled with any of these names. See
[ABLATION_LADDER.md](ABLATION_LADDER.md).
