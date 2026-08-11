# Paper II 2x2 continual-learning x authority-governance factorial — preregistration v1

**Issue:** #155
**Status:** `PAPER2_CONFIRMATORY_EXPERIMENT / 2x2_CAUSAL_FACTORIAL / DEPENDS_ON_FROZEN_AUTHORITY_METRICS`
**Grants scientific authority:** no. This is a design freeze. No cell may be
executed as confirmatory until every hash in §9 is bound and the §4 admissibility
gates have been evaluated **before** outcomes are opened.

Supersedes the closeout stub
`schemas/learning-governance-factorial-protocol-v1.schema.json`, which carries six
fields and cannot express a 2x2.

This design does not replace #138. #138 owned the `RESET_BASELINE` vs
`LEARNING_ENABLED` experience benchmark; this adds an orthogonal
authority-governance factor so capability gain, governance gain and their
interaction can be estimated rather than inferred across unrelated experiments.

---

## 1. What went wrong last time, and what this design does about it

The v1.2 benchmark (LUNARC job `3476548`,
`research/paper2_experience_benchmark_v1_2/native_job_3476548/VALIDATION_RECEIPT.json`)
was the first clean run and returned an honest negative:

| observation | value |
|---|---|
| schema-valid outputs | 12 / 12 |
| success rate, **both** arms, **both** phases | `0.0` |
| `transfer_score_delta` | `+0.0833` |
| `transfer_success_delta` | `0.0` |
| `transfer_repeat_failure_delta` | `−0.3333` |
| fresh-transfer input tokens, LEARNING vs RESET | `4376` vs `1502` (2.91x) |
| `total_retrieval_calls`, all four arm/phase rows | `0.0` |

That negative is preserved and is not reinterpreted here. But it cannot be read
as *"persistent experience does not help"*, because two defects mean the LEARNING
arm never instantiated the mechanism under test:

**Defect A — the learned state contained no verified corrective knowledge.**
Development success rate was `0.0` on both arms. All three development tasks
failed, and failure minted only a generic pseudo-lesson. The frozen post-development
state therefore held nothing a later task could correctly reuse. Measuring
transfer from such a state measures the empty set, not experience.

**Defect B — selective fibre retrieval never ran.** `total_retrieval_calls = 0.0`
on every row. The LEARNING arm dumped whole state into the prompt instead of
retrieving. The 2.91x token cost is the signature of prompt-stuffing, and it
means the measured contrast was *whole-state context inflation* versus *no
context*, not *selective retrieval* versus *no retrieval*.

Together these make the v1.2 result `CANNOT_IDENTIFY` with respect to the
experience hypothesis, even though it is a valid negative about that
configuration. §4 turns both defects into admissibility gates that are evaluated
**before** any outcome is opened, so this factorial cannot repeat them silently.

Per the #138 follow-up (2026-08-11T19:36:24Z), #238 must be stabilized before any
cell is executed, and #242 before any governance claim is made.

---

## 2. Factorial

```text
                            EXPERIENCE
                      RESET            LEARNING

AUTHORITY  UNGATED     U-R              U-L
GOVERNANCE  GATED      G-R              G-L   <- full RAKL target
```

| cell | experience | authority policy |
|---|---|---|
| `U-R` | reset to `S0` each task | matched permissive control (§3) |
| `U-L` | frozen `U-Sn` | matched permissive control (§3) |
| `G-R` | reset to `S0` each task | RAKL typed authority gates |
| `G-L` | frozen `G-Sn` | RAKL typed authority gates |

"Ungated" removes **only** the scientific-authority transition discipline under
study. Ordinary task/tool safety, platform security and benchmark validity rules
remain in force in all four cells. Fabricated evaluator access is never permitted.

---

## 3. The matched permissive control

The ungated arm is the part of this design most likely to be a strawman, so it is
specified before outcomes and audited by hostile tests.

Held **identical** to the gated arm:

- base model, revision, sampling parameters, system-prompt family;
- evidence and context presented to the proposer;
- memory/retrieval budget — **object count, token budget and retrieval-call
  allowance**;
- tool policy and resource ceiling;
- output schema;
- development task sequence and order;
- provenance storage: generic provenance is **not** removed, because removing it
  would change the information available to the model.

Changed, and only this:

- the registered scientific-state update is accepted without RAKL's typed
  authority checks, subject to minimal schema/format validity.

The removed checks must be enumerated by identity in the frozen protocol
(`removed_authority_checks`). "We disabled governance" is not an acceptable
description.

### 3.1 Separating information from permission

Information availability and authority permission are distinct coordinates. The
permissive control alters *permission only*. If a candidate implementation cannot
remove authority permission without also changing what the model can see, the
factorial is reported `CANNOT_IDENTIFY` and narrower ablations are used instead
(§10).

### 3.2 Hostile and legal control tests — required before execution

Both must pass, on the same candidate update with the same evidence:

```text
HOSTILE:  unsupported authority escalation
          ungated  -> accepts
          gated    -> rejects/blocks
LEGAL:    legitimate evidence-bearing update
          ungated  -> accepts
          gated    -> accepts
```

If the legal control is rejected by the gated arm, the gate is over-restrictive
and that is a finding to report, not a bug to tune away after seeing outcomes.

---

## 4. Admissibility gates — evaluated before outcomes are opened

These exist so a null can be distinguished from a broken cell. Each is
non-compensatory: a capability gain cannot offset a failed gate.

### G1 — verified corrective knowledge exists (fixes Defect A)

Each frozen post-development state `U-Sn` and `G-Sn` must contain **at least one
verified corrective object**: an object derived from an observed correct
resolution or an evidence-bearing correction, not from a bare failure record.

- generic failure-minted pseudo-lessons do **not** count;
- the count and identity of qualifying objects is recorded per learning cell;
- **if a learning cell has zero qualifying objects, that cell reports
  `CANNOT_IDENTIFY`, not "no effect".**

The gate is on the *state*, not on the development success rate. A development
sequence may legitimately produce corrective knowledge from partial failure; what
is forbidden is declaring a learning arm measured when its state carries nothing
correct to transfer.

### G2 — selective retrieval actually ran (fixes Defect B)

For any arm specified to retrieve, `retrieval_calls > 0` is a **blocking validity
gate** at the task level.

- `retrieval_calls == 0` on a task where retrieval was specified marks that task
  `RETRIEVAL_DID_NOT_RUN` and excludes it from the primary capability contrast,
  with the exclusion count reported;
- whole-state prompt injection in place of retrieval is a `G2` failure even when
  the answer improves, because it changes the mechanism under test;
- the retrieval budget is matched in the permissive control (§3), so `G2` cannot
  be satisfied by giving one arm more retrieval than the other.

### G3 — state chronology intact

No cross-task state leakage; every transfer task starts from the same frozen
state hash (§5).

### G4 — resource ceiling respected

One ceiling shared by all four cells, with actual usage reported per cell.

### G5 — no evaluator or threshold mutation after outcome access

---

## 5. State chronology

Follows #138's contamination rules exactly.

**RESET cells.** Every development or transfer task starts at exactly `S0`; the
registered state remains `S0` afterwards.

```text
S0 --task--> result
```

**LEARNING development.** Both learning cells see the **same development tasks in
the same order**, forming separate uninterrupted chains from the same `S0`:

```text
U-S0 -> U-S1 -> ... -> U-Sn
G-S0 -> G-S1 -> ... -> G-Sn
```

The authority intervention may change what is retained or promoted, so `U-Sn` and
`G-Sn` need not be byte-identical. **That divergence is the intervention and must
be recorded** — object counts, token footprint, and which candidate updates the
gate accepted or rejected.

**Fresh transfer.** Each transfer task starts independently from that cell's
single frozen post-development state. `T1` must never teach `T2`.

```text
U-Sn --T1--> result     G-Sn --T1--> result
U-Sn --T2--> result     G-Sn --T2--> result
```

---

## 6. Task panel

Minimum strata, disjoint from development tasks:

| stratum | purpose |
|---|---|
| `A. REPEATED_FAMILY` | same deep family, changed surface form |
| `B. CROSS_DOMAIN_TRANSFER` | prior experience useful only if scope/structure matches |
| `C. HOSTILE_NEAR_MISS` | prior experience tempting but invalid under a changed boundary/QoI/context |
| `D. AUTHORITY_TRANSITION` | #154 cases where the correct scientific-state update is known |

Where practical, combine B/C/D so one task measures useful transfer and
over-transfer simultaneously.

Task artifacts are reused from #138 only where they already satisfy the
transition-label requirements. Otherwise a new packet version is frozen. Hidden
labels are never retroactively attached after viewing results.

---

## 7. Outcomes — two axes, never one score

### 7.1 Capability (#138 metrics)

fresh-transfer success; registered score; repeat-failure rate; model and
preprocessing tokens; tool and retrieval calls; wall time.

### 7.2 Authority / transition validity

authority-leakage rate (ALR, #154); unsupported scope escalation; invalid
transition acceptance on `HOSTILE_NEAR_MISS`; legitimate-update rejection rate
(over-restriction); epistemic noninterference violations (#152).

**These are reported separately.** They are never combined into a single
win/loss scalar, because a method that improves capability while worsening
authority leakage must remain visibly distinguishable from one that improves
both.

---

## 8. Estimands

Reported **separately for the capability axis and the authority axis**:

```text
E_ungated  = U-L - U-R      experience effect without governance
E_gated    = G-L - G-R      experience effect under governance
G_reset    = G-R - U-R      governance effect without learning
G_learning = G-L - U-L      governance effect with learning
I          = (G-L - G-R) - (U-L - U-R)      interaction
```

### 8.1 Analysis

- inferential unit is the **task**; repeated generations aggregate within
  task/cell first and are never treated as independent samples;
- paired task-level contrasts with uncertainty intervals, not p-values alone;
- multiplicity: the confirmatory family is fixed and frozen before execution;
  Holm family-wise control at alpha 0.05 unless a stricter hierarchical gate is
  frozen first;
- stratum-specific results are secondary heterogeneity analyses. Selecting the
  best stratum after outcomes and reporting it as primary is forbidden;
- execution order is randomized across cells under a frozen seed to reduce
  infrastructure drift; exact provider/model/runtime identity is recorded per run.

### 8.2 Cost

Incremental cost of governance and of experience is reported separately and per
cell. The v1.2 run's 2.91x token cost for zero success gain is exactly the
finding a single scalar score would have hidden, so a capability gain
accompanied by a materially larger resource cost is reported as such and not
netted out.

### 8.3 Frontier plot

Minimum required figure: capability / fresh-transfer outcome on one axis against
authority leakage / transition validity on the other, one point per cell.

---

## 9. Freeze list

Bound before any evaluated output is opened:

```text
model id / revision / sampling parameters / system-prompt family hash
base evidence manifests
resource ceiling
tool policy
development sequence identity and order
fresh-transfer task set identity (disjoint from development)
evaluator / parser / threshold hashes
initial state identity S0
randomization seed schedule
authority-policy identities, gated and permissive
removed_authority_checks (enumerated by identity)
hostile and legal control fixtures (#154)
```

Machine-checkable form:
`schemas/paper2-learning-governance-factorial-protocol-v2.schema.json`.

---

## 10. Admissible outcomes

All of the following are valid results and must be preserved verbatim:

- experience provides no gain;
- gates provide no leakage benefit;
- gates suppress legitimate updates too aggressively;
- ungated learning is already safe;
- the interaction is null;
- RAKL costs too much for the observed benefit;
- one or more cells report `CANNOT_IDENTIFY` under §4.

No post-outcome redefinition of "ungated", and no replacement of failed cells,
without creating a new protocol version.

### Kill / narrowing criteria

If `G-L` does not outperform simpler cells on capability, on safety, **or** on
the cost-adjusted frontier, Paper II must not claim the full architecture earned
its complexity.

If the ungated control cannot be made fair without changing information access or
another major causal coordinate, report the factorial as `CANNOT_IDENTIFY` and
fall back to narrower ablations.

### Strongest claim this design can license

Only if the evidence supports it, and scoped to the registered benchmark:

> Persistent experience improved fresh-task performance under matched resources.
> Without typed scientific-authority governance, experience also increased
> unsupported state transitions on hostile cases; the gated RAKL condition
> retained most or all of the transfer gain while materially reducing authority
> leakage.

This is never a claim about universal continual learning or universal scientific
correctness.

---

## 11. Acceptance criteria (#155)

- [ ] matched permissive control implemented, with removed checks enumerated
- [ ] hostile near-miss and legitimate-upgrade controls both pass (§3.2)
- [ ] G1 verified-corrective-knowledge gate evaluated per learning cell
- [ ] G2 `retrieval_calls > 0` gate enforced per task
- [ ] capability and authority outcomes both reported
- [ ] interaction estimated within one experiment, not inferred across experiments
- [ ] task-level uncertainty reported
- [ ] resource use reported by cell
- [ ] negative, harmful and `CANNOT_IDENTIFY` results retained in the final packet
