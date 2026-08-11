# Closest-parent primary-source audit

Issue #156 · V2 full-text deepening 2026-08-12 · Detail file for
[`PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md`](../PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.md)

Per-parent extraction of object, update rule, authority semantics, persistence,
failure/repair, evidence and stated limitations. **Evidence level is recorded
per parent and governs what any matrix row measured against it may claim.**

V2 receipt: [`PRIMARY_SOURCE_AUDIT_V2_RECEIPT.json`](PRIMARY_SOURCE_AUDIT_V2_RECEIPT.json).

| Parent | arXiv | Version | Evidence level |
|---|---|---|---|
| MemTX | 2607.23929 | v2, 2026-07-28 | `FULL_TEXT` |
| PPMF | 2607.29167 | v1, 2026-07-31 | `FULL_TEXT_PARTIAL` (pp. 1–6 and 11–16; pp. 7–10 results narrative unread) |
| AutoSci | 2605.31468 | v1, 2026-05-29 | `FULL_TEXT` (V2) |
| MemClaw | 2606.24535 | v1, 2026-06-23 | `FULL_TEXT` (V2) |
| AI-scientists audit | 2604.18805 | v1, 2026-04-20 | `FULL_TEXT_PARTIAL` (V2: §§4.5–4.9) |

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

## PPMF — `FULL_TEXT_PARTIAL` (pp. 1–6, 11–16)

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

**Appendix A.** Restates the invariant as a runtime-monitor proposition with a
proof sketch: under platform-maintained provenance, append-only confirmation
events and deterministic support binding, "no action-relevant claim whose least
supporting source is below required(ρ) can authorize a call of risk ρ, unless a
scoped declassification event is bound to the same principal, target, risk
class, and scope". Table 5 enumerates all seven policy stages — memory write,
trust transition, retrieval, risk labeling, authorization, tool taint, conflict
handling.

**Scope.** Action and tool risk under indirect prompt injection (cs.CR). `q` is
"a schema-level claim linking a memory span to an action argument". **Every one
of the seven policy stages is keyed on source channel and action risk class. No
stage references a kind of scientific support**, and no representation,
mechanism or identification distinction appears anywhere in the read sections —
which now include the formal statement and the complete policy table, not only
the method summary.

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

## AutoSci — `FULL_TEXT` (V2)

**Modules.** SciMem (Long-Term Knowledge Memory typed entities
Topic/Paper/Foundation/Concept/Method/People + Active Research Memory
Idea/Experiment/Manuscript/Review with lifecycle states), SciFlow (five-stage
harness Literature→Ideation→Experiment→Writing→Rebuttal with >30 skills),
SciDAG (optional DAG multi-agent templates), SciEvolve (`/dream` SciMem
organization, `/forge` SciFlow skills, `/morph` SciDAG templates).

**Update / trust.** All SciMem writes pass Trust Guard (PASS/WARN/BLOCK on form
validity and content/evidence consistency). Cross-region consolidation can write
project findings back into Long-Term Knowledge Memory entity pages. SciFlow
equips each skill with a tailored SciMem view; SciDAG retrieves templates with
past execution experience.

**Authority.** Trust Guard is a form/content admission gate. There is **no**
multi-axis scientific-authority ledger and no claim-kind non-escalation rule
(prediction↛mechanism↛identification).

**SciEvolve.** Feedback from user/task/open environments becomes versioned
updates when recurring patterns are judged "stable enough". This is generic
self-improvement over organization/skills/templates — not held-out fresh
assurance generated after a challenger exists.

**Adjudication (V2).** Experience-conditioned routing and open-world discovery
routes are inherited. Experience→authority noninterference survives only as
typed authority-coordinate noninterference (not "experience never updates
knowledge"). Fresh-assurance self-evolution survives as the held-out
post-challenger gate. Cascade repair remains MemTX's stronger parent.

**Repository.** `github.com/skyllwt/AutoSci`, public MIT; paper system on
`paper` / `arxiv-v1`. Runtime not re-executed in this literature lane.

---

## MemClaw / Governed Shared Memory — `FULL_TEXT` (V2)

Fleet-memory system \(F=(A,M,G,P,T)\) with scoped retrieval, temporal
supersession, provenance tracking and policy-governed propagation; ArgusFleet
exercises the live REST API. Scope-soundness invariant Inv-Scope: no agent
receives a memory outside nested agent⊑fleet⊑tenant entitlement.

Preserved production defects remain: initial GET-by-id sub-tenant bypass
(remediated during study); near-duplicate filter can reject contradictory writes
before asynchronous contradiction detection. Evaluation is explicitly one live
service, not a baseline comparison.

**Adjudication (V2).** Shared-memory governance, provenance reconstruction and
per-record temporal supersession are inherited / conceptual parents.
**Bounded freshness-expiring saturation** remains a narrow residual: MemClaw
expires individual rows, not a route-indexed hypothesis-space coverage
certificate.

**Classification.** `CONCEPTUAL_COMPARISON_ONLY` as an experimental arm
(proprietary service), but full-text sufficient for function adjudication.

---

## AI scientists produce results without reasoning scientifically — `FULL_TEXT_PARTIAL` (V2)

Measurement study (>25,000 runs). Manual marker taxonomy over
behavior-relevant nodes; epistemological graphs label nodes as hypothesis /
test / evidence / judgment / update / commitment with testing / observing /
using / contradicting / competing / updating edges (§§4.5–4.9).

**Adjudication (V2).** Closest parent for scientific-transition-audit
*measurement*. Coding distinguishes epistemic operations and failure modes, not
G/R/M/I/D authority-axis escalations. Narrow residual retained; confirmatory
rate comparison on the RAKL side remains separately blocked by the capability
floor.

**Classification.** `CONCEPTUAL_COMPARISON_ONLY` as a system ablation target.

---

## Feasibility summary

| Parent | Classification | Why |
|---|---|---|
| AutoSci | `BLACK_BOX_PUBLIC_SYSTEM_FEASIBLE` | public MIT code, but needs an authenticated agent runtime and the paper system is on a separate frozen branch; exact reproduction of paper results is not established |
| MemTX | `FUNCTION_MATCHED_ABLATION_FEASIBLE` | no public implementation located; the commit-discipline function is reproducible as a RAKL-internal arm |
| PPMF | `FUNCTION_MATCHED_ABLATION_FEASIBLE` | no public implementation located; the non-amplification rule is simple enough to implement faithfully |
| MemClaw | `CONCEPTUAL_COMPARISON_ONLY` | proprietary production service |
| 2604.18805 | `CONCEPTUAL_COMPARISON_ONLY` | a measurement study, not a system |

**Scope of the "no public implementation located" claim.** GitHub repository
search for `MemTX transactional memory agent`, `PPMF provenance preserving
memory firewall` and `provenance memory firewall LLM`, plus GitHub code search
for `transactional belief commit MemTX` — all zero results on 2026-08-11.
Neither abstract page links code; PPMF's Appendix B names a project directory
rather than a repository. An absence claim is only as good as the search behind
it, so the search is recorded rather than asserted. If either implementation
surfaces, MemTX moves toward `EXACT_REPRODUCTION_FEASIBLE` and Deliverable 4
changes.

No RAKL arm may be labelled with any of these names. See
[ABLATION_LADDER.md](ABLATION_LADDER.md).
