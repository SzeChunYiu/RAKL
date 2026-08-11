# Paper II Novelty Campaign — Execution Order and Evidence Gates

**Status:** `PROPOSAL-ONLY / MASTER_DEPENDENCY_ISSUE / RESULTS_BEFORE_CLAIMS`
**Refs:** #158
**This is a coordination surface only. It grants no authority and changes no code.**

---

## Purpose

Coordinate the Paper-II novelty work so future AI sessions execute tasks in an evidence-preserving order rather than independently optimizing one attractive result. This document defines the proposed execution order, evidence gates, and operator decisions required before manuscript promotion.

Target research thesis:

> RAKL is a continually learning scientific-agent architecture in which experience can improve future search and method choice without being allowed to mint scientific authority; this separation should be formalized, attacked, measured, and tested against the strongest contemporary parent mechanisms.

---

## Scope and Issue Map

| Issue | Deliverable | Dependencies |
|-------|-------------|--------------|
| **#156** | Closest-parent function matrix + implementable ablation suite | None (can run in parallel with #152) |
| **#152** | Formal epistemic noninterference invariant + executable tests | None (can run in parallel with #156) |
| **#154** | Scientific state-transition benchmark + Authority Leakage Rate | #152 (for authority semantics) |
| **#138** | Base RESET vs LEARNING experience benchmark | Frozen contracts (already specified) |
| **#155** | 2x2 continual-learning × governance factorial | #152, #154, #138 |
| **#157** | Experience-to-method promotion with fresh assurance | Stable experience/authority interfaces from #152/#154 |
| **#131** | Breakthrough-learning modes (shadow trials) | Stable v3 integration; provides candidate mechanisms, does not substitute for #157 |

---

## Proposed Execution Order

### Phase 0 — Freeze novelty boundary

**Run first or in parallel:** #156 (closest-parent audit) and #152 (epistemic noninterference).

**Deliverable:**

```text
Inherited mechanisms
RAKL residual mechanisms
Nearest parent per residual
Falsifier per residual
Required experiment per residual
```

**Evidence gate:** Do not strengthen manuscript novelty language before this audit identifies what is genuinely residual.

**Operator decision:** Is the #156 audit complete? Are task families sufficient for the claimed residual?

---

### Phase 1 — Formal property

**Run:** #152 (epistemic noninterference).

**Deliverables:**

```text
Exact authority-state projection
Experience/routing operation inventory
EPISTEMIC_NONINTERFERENCE definition
Legal-transition controls
Hostile mutation tests
Machine-readable receipt
```

**Evidence gate to continue:**

```text
Property is non-vacuous
AND
Closest-parent audit does not show equivalent scientific-authority property
```

If this gate fails, narrow the Paper-II thesis before spending on confirmatory experiments.

**Operator decision:** Is the property non-vacuous? Does a parent already provide an equivalent invariant?

---

### Phase 2 — Measurement object

**Run:** #154 (authority-leakage benchmark).

**Deliverables:**

```text
Frozen transition ontology/rubric
Hostile + legal cases
Authority Leakage Rate (ALR) + subtype metrics
Valid-upgrade recall
BLOCKED/CANNOT_CHECK metrics
Negative-history/context metrics
Benchmark receipt
```

**Evidence gate to continue:**

```text
Benchmark labels are defensible
AND
Benchmark is not redundant with a current parent benchmark
AND
RAKL can fail the benchmark
```

**Operator decision:** Are the benchmark labels defensible? Is there redundancy with existing benchmarks?

---

### Phase 3 — Establish base experience effect

**Run:** #138 (RESET vs LEARNING under existing frozen contracts).

**Question:** Does persistent experience improve fresh tasks under matched resources at all?

**Do not infer governance benefit from this experiment.** This is a scoped baseline result, not a universal capability claim.

**Operator decision:** Is the #138 packet frozen? Is the model/tool/evaluator/resource contract stable?

---

### Phase 4 — Causal learning × governance test

**Run:** #155 (2x2 factorial) — ONLY after #152, #154, #138 are frozen.

**Question:** Does authority governance change the safety/capability frontier of continual learning?

**Required result matrix:**

```text
U-R  ungated reset
U-L  ungated learning
G-R  gated reset
G-L  gated learning
```

**Report capability and authority outcomes separately.**

**Operator decision:** Is the 2x2 estimand approved? Is the ungated control fair (non-straw)?

---

### Phase 5 — Protected method evolution

**Run:** #157 (experience-to-method promotion with fresh assurance).

**Run after:** Experience/authority interfaces are stable enough to freeze candidate methods and assurance receipts.

**Question:** Can RAKL distinguish transferable procedural lessons from development-only overfit before persistent method promotion?

**Operator decision:** Are the experience/authority interfaces frozen? Are the method-candidate and assurance contracts hash-bound?

---

### Phase 6 — Ablation attribution

**Run:** #156 empirical ablation ladder using #154/#155 outputs where compatible.

**Critical contrast:**

```text
Transactional/governed persistent memory
vs
Scientific claim-type authority layer
```

If the scientific-authority layer adds no measurable benefit over the closest function-matched parent at lower/equal cost, narrow Paper II.

**Operator decision:** Does the authority-typing layer earn its complexity under the benchmark?

---

### Phase 7 — Manuscript rewrite

**Run only after:** All relevant receipts are frozen.

**Do not rewrite Paper II around a hoped-for positive result.** After the receipts are frozen, update title, abstract, contribution list, nearest-work section, evaluation section, limitations/falsifiers, figures/tables.

**Operator decision:** Are all relevant receipts frozen? Does the rewritten claim match the frozen evidence?

---

## Evidence Gates Summary

| Phase | Gate |
|-------|------|
| Phase 0 | Closest-parent audit complete; residual mechanisms identified |
| Phase 1 | Property non-vacuous; no parent equivalent |
| Phase 2 | Benchmark defensible; non-redundant; RAKL can fail |
| Phase 3 | Base experience effect measured (scoped result only) |
| Phase 4 | Four-arm contrast estimated; interaction reported |
| Phase 5 | Protected promotion separates transfer from overfit |
| Phase 6 | Ablations attribute benefit to specific RAKL layers |
| Phase 7 | All receipts frozen before manuscript edit |

---

## Conservative — Operator Decisions Required

The following points require explicit operator decisions before proceeding. This document does not decide them; it surfaces them as open questions with options.

### 1. Is #138 frozen and executable?
- **Options:**
  - Packet is frozen with exact model/tool/evaluator/resource/state identities → proceed
  - Packet requires additional freeze work → block Phase 3
  - Packet is obsolete → specify new protocol

### 2. Is #152's epistemic noninterference property non-vacuous?
- **Options:**
  - Property is executable and passes hostile tests → proceed to Phase 2
  - Property is vacuous or parent already provides equivalent invariant → narrow thesis
  - Property cannot be formalized with current interfaces → report CANNOT_CHECK

### 3. Is #154's benchmark defensible and non-redundant?
- **Options:**
  - Labels are defensible; no current parent provides same unit → proceed
  - Primary-source audit finds redundancy → reuse or extend existing benchmark
  - Labels depend on author preference rather than explicit contracts → mark development-only

### 4. Are task families sufficient for the claimed residual?
- **Options:**
  - Current families (repeated-family, cross-domain, hostile-near-miss, authority-transition) → sufficient
  - Additional strata required (e.g., negative-history, context-mismatch) → expand packet
  - Task generation is insufficient → block empirical runs

### 5. Is the #155 2x2 estimand approved?
- **Options:**
  - Four-arm design is approved; ungated control is fair → proceed
  - Ungated control cannot be made fair without changing information access → report CANNOT_IDENTIFY
  - Factorial is infeasible under budget → use narrower ablations

### 6. Does the scientific-authority layer earn its complexity?
- **Options:**
  - Ablations show measurable benefit over transactional governance → retain claim
  - No measurable benefit; cost dominates → narrow to engineering integration
  - Result is mixed → retain with scoped claim

### 7. Are all receipts frozen before manuscript rewrite?
- **Options:**
  - All relevant receipts hash-bound → proceed to manuscript edit
  - Some receipts pending → block manuscript promotion
  - Negative results require narrowing → edit claim scope

---

## Target Manuscript Positioning

**Current broad positioning to avoid:**

```text
RAKL is novel because it has persistent scientific memory, workflows, skills,
experience learning, and self-evolution.
```

**Preferred thesis if the evidence supports it:**

```text
RAKL separates continually learned procedural/search state from scientific-authority
state. Experience may change what the agent tries, while typed evidence-bearing gates
control what can become scientifically authoritative. We formalize this noninterference
boundary, evaluate scientific state-transition accuracy/authority leakage, and test
whether governance preserves useful continual-learning gains under hostile transfer.
```

**Possible future title direction if results support it:**

```text
RAKL: Evidence-Governed Continual Scientific Agents
```

or

```text
Learning from Experience Without Authority Leakage in Scientific Agents
```

**Do not rename until results and nearest-work audit justify the change.**

---

## Research Panel Required for Synthesis

When integrating findings, convene at least these roles; these are same-context expert lenses unless genuinely independently sourced:

1. **Scientific-agent systems / closest prior art** — AutoSci and current AI-scientist architectures; what is genuinely inherited vs residual
2. **Formal methods / state-machine semantics** — noninterference definition, transition system, mutation tests
3. **Scientific methodology / epistemology** — representation vs mechanism vs identification; negative evidence; context
4. **Causal experimental design / statistics** — factorial identification, task-level inference, multiplicity, cost
5. **Agent memory / security / provenance** — MemTX, PPMF, governed memory; avoid renaming generic memory safety
6. **Hostile reviewer / significance** — ask whether the measured residual is worth the added framework complexity

Every headline finding should be challenged by at least two relevant lenses.

---

## Non-Negotiable Evidence Rules

```text
same-session review != independent review
architecture invariant != empirical superiority
conformance benchmark != natural-domain generalization
persistent experience != scientific evidence
routing gain != authority gain
repeated failure != impossibility
parent-inspired ablation != actual parent system
positive benchmark != universal scientific capability
negative result != failed project; it narrows the claim
```

---

## Completion Criteria

This campaign is complete when either:

### Positive path

- [ ] #156 closes the nearest-work boundary
- [ ] #152 establishes a non-vacuous executable noninterference invariant
- [ ] #154 provides a defensible authority-transition benchmark
- [ ] #138 provides matched continual-experience evidence
- [ ] #155 estimates the learning × governance interaction
- [ ] #157 tests protected method promotion/fresh reuse
- [ ] Ablations attribute any benefit to specific RAKL layers
- [ ] All resource/cost and negative outcomes are retained
- [ ] Paper II is rewritten strictly from frozen results
- [ ] Updated PDF/artifacts pass publication CI and external novelty review remains explicitly open

### Negative/narrowing path

If any core claim fails:

- Preserve the negative result
- Remove/narrow the corresponding novelty claim
- State which simpler parent/ablation suffices
- Keep useful framework features as engineering mechanisms without unsupported scientific significance

---

## Desired End State

Paper II should become publishable because it answers a hard, falsifiable question—not because it contains many components:

```text
Can a scientific agent learn persistently from its own research experience
without allowing that experience to become evidence, and does the governance
needed to enforce that separation measurably matter?
```

---

## Live scoreboard (2026-08-11, post #267/#273/#275 + next-gate slice)

| Issue | Design landed | Empirics | Closable now? | Exact residual / next gate |
|---|---|---|---|---|
| **#154** | V2 twin panel + degeneracy gate (#267); neighbour residual audit receipt | No model baselines | **No** | Full-text parent coding/rubric reads still pending for 2604.18805 / 2605.10246; ALR/valid-upgrade from evaluated runs; subjective annotation or development-only mark |
| **#155** | 2×2 preregistration + G1/G2 schema (#273) | No cells executed | **No** | Blocked on #238/#247 discriminative learning + capability; #154 scored ALR; execution coords still `PENDING_FREEZE_*` |
| **#156** | Function matrix + A0–A7 ladder (#275); **A3↔A4 cheap conformance receipt** | No matched empirical ablations | **No** | Resolve AutoSci/`CANNOT_CHECK` rows; run matched A3 vs A4 benefit/cost with uncertainty after #247/#154/#155 |
| **#157** | Experience→method preregistration draft + v2 schema | No arms executed | **No** | Same upstream blockers as #155; freeze assurance panel hashes before any promotion claim |
| **#158** | Coordination doc | Campaign incomplete | **No** | Umbrella stays open until child empirics + #257 manuscript promotion gates clear |
| **#152** | Noninterference surface (prior) | Conformance/hostile suites exist | Track separately | Integrated surface required before governance empirics |
| **#138/#247/#238** | Experience packets / capability staircase in flight | Partial native negatives preserved | Track separately | Discriminative verified-lesson path is the critical path for #155/#157 |

Authoritative cross-paper graph remains #258. Proposal-only issue closure is not evidence completion.

---

**Status:** `PROPOSAL-ONLY / MASTER_DEPENDENCY_ISSUE / RESULTS_BEFORE_CLAIMS`
**Refs:** #158
