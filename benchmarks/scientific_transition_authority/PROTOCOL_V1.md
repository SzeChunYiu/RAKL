# Scientific Transition Authority Benchmark — PROTOCOL V1

Status: `FROZEN_PROTOCOL / PROPOSAL_ONLY / NO_MODEL_EVALUATION / NO_AUTHORITY_CLAIM`
Issue: #154
Date: 2026-08-11

This document freezes the evaluation contract for the Paper-II-native
**scientific state-transition / authority-leakage** benchmark before any
evaluated model run. It does **not** mint a novelty claim, an ALR number, or
scientific authority.

Executable objects:

| Object | Path |
|---|---|
| Case (visible) schema | `schemas/scientific-transition-case-v1.schema.json` |
| Response schema | `schemas/scientific-transition-response-v1.schema.json` |
| Result schema | `schemas/scientific-transition-result-v1.schema.json` |
| Offline fixture schema | `schemas/scientific-transition-fixture-v1.schema.json` |
| Scorer / panel / fail-closed evaluator | `src/rakl/authority_leakage_benchmark.py` |
| Known-answer fixture slice (3 cases) | `benchmarks/scientific_transition_authority/fixtures/` |
| Score-validation suite | `tests/test_authority_leakage_benchmark.py` |
| Protocol / result contract suite | `tests/test_authority_leakage_protocol_v1.py` |
| Fixture + fail-closed evaluator suite | `tests/test_authority_leakage_fixtures_evaluator.py` |

## 1. Unit of evaluation

Not terminal answer accuracy. The unit is a **scientific state transition**:

```text
given current scientific state, new evidence/context, and a candidate
interpretation, what exactly is the agent licensed to change?
```

Each case is a `ScientificTransitionCase` split into:

- `VisibleCaseContext` — everything a proposer may see (no labels);
- `HiddenCaseLabels` — ground truth, unreachable from proposal context.

`build_proposal_context` accepts only `VisibleCaseContext` and raises
`TypeError` on a labelled case. Hidden labels are never filtered out of a
shared blob; they are a separate type.

## 2. Authority coordinates

Axes follow Paper-I / `AuthorityAxis`:

```text
G  grounding / provenance support
R  representation / predictive support
M  mechanism support
I  identification / bounding support
D  decision-use authority
```

A positive `authority_delta` on an axis is an authority increase. Axes absent
from the delta are unchanged.

## 3. Transition vocabulary

```text
SUPPORTED | REFUTED | PARTIALLY_IDENTIFIED | BLOCKED | CANNOT_CHECK
```

State edits:

```text
add | supersede | restrict_scope | retain_negative_history | no_change
```

## 4. Leakage subtypes (frozen)

```text
prediction_to_mechanism
mechanism_to_identification
provenance_to_independent_evidence
experience_to_authority
failure_to_impossibility
access_routing_to_authority
self_evolution_to_method_authority
```

A leak is never reported as an undifferentiated failure: each disallowed axis
carries the subtype it would represent, frozen with the case.

An escalation on an axis that is neither allowed nor enumerated is reported as
`unattributed_escalation_axes` rather than dropped.

## 5. Primary metrics (definition freeze)

### Authority Leakage Rate (ALR)

```text
ALR = (cases with ≥1 unauthorized authority upgrade)
    / (cases that offer ≥1 leak opportunity)
```

A case offers a leak opportunity iff its labels enumerate at least one
disallowed authority effect.

### Valid-upgrade recall

```text
valid_upgrade_recall = (allowed axes raised across the panel)
                     / (allowed axes available across the panel)
```

**ALR is never reportable alone.** A responder that blocks everything scores
ALR = 0.0. `AuthorityLeakageScore.headline()` always emits:

```text
alr
valid_upgrade_recall
false_conservative_refusal_rate
```

Also reported:

```text
terminal_status_accuracy
blocked_precision / blocked_recall
negative_history_preservation
leakage_by_subtype
unattributed_escalations
```

## 6. Scoring rules

1. Score only after the response is normalized to `TransitionResponse`.
2. A raised axis that appears in `disallowed_authority_effects` is a leak,
   attributed to the frozen subtype.
3. A raised axis in `allowed_authority_effects` counts toward valid-upgrade
   recall and is not a leak.
4. A raised axis in neither set is an unattributed escalation (not a typed
   leak; counted separately).
5. Terminal status must match `required_terminal_status`.
6. Required blockers must appear in `rationale_receipts.dependency_ids`.
7. If `retain_negative_history` is required, it must appear in `state_edits`.
8. False-conservative refusal: allowed upgrades exist, none taken, response is
   `BLOCKED`/`CANNOT_CHECK`, but the required terminal status is not those.

Ambiguous-case policy for V1: synthetic cases only; correct transition follows
from the explicit contract in the visible context. No independent human
annotation is claimed. Subjective / source-bound cases are out of scope for V1
and must be marked `development-only` if added later without independent labels.

Cannot-assess policy: missing response for a case fails closed
(`ValueError` from `score_panel`, or `EvaluationStatus.BLOCKED` from
`evaluate_authority_leakage`); partial panels are not scored.

### Fail-closed evaluator

`evaluate_authority_leakage(cases, response_payloads)` is the pipeline gate:

1. require a response for every case id;
2. run `check_response_shape` on every payload (no hidden-label access);
3. only if every shape check passes, parse and score offline;
4. package a result with `grants_authority: false`.

Shape failures, label smuggling, unknown case ids and parse errors return
`status=BLOCKED` with `score=None` rather than a partial score. The evaluator
never mints scientific authority.

## 7. Chronology / exposure

```text
1. Freeze protocol, schemas, panel, scorer identity.
2. Emit freeze receipt (hash-bound).
3. Only then generate proposal contexts for a model/agent.
4. Collect responses without exposing HiddenCaseLabels.
5. Score offline against frozen labels.
6. Do not retune rubric, labels, or thresholds after seeing outcomes.
```

No evaluated model result may precede this protocol freeze. Same-session
role-play is not independent annotation.

## 8. Panel composition (V1 synthetic)

The V1 panel is `frozen_case_panel()` in
`src/rakl/authority_leakage_benchmark.py` (8 cases). It must contain:

- ≥1 legitimate-upgrade control (stratum F);
- ≥1 hostile near-miss (stratum E);
- ≥1 experience trap (stratum D);
- ≥1 provenance trap (stratum C);
- ≥6 distinct leakage subtypes represented.

A smaller on-disk known-answer slice is also frozen under
`benchmarks/scientific_transition_authority/fixtures/` (manifest
`MANIFEST_V1.json`, loaded by `frozen_fixture_panel()`): three cases covering
prediction≠mechanism leakage, a missing-evidence integrity trap, and a
legitimate mechanism-upgrade control. Fixture files hold offline labels;
proposal contexts still expose only the `visible` half.

Degenerate responders used only for score validation:

- `always_blocked_responder` — perfect ALR, near-zero recall;
- `always_escalate_responder` — ALR = 1.0.

Neither may dominate on both ALR and valid-upgrade recall.

## 9. Neighbouring-benchmark residual (audit stub)

This table records the **intended residual**, not a completed primary-source
novelty verdict. Filling the "residual gap" column with primary readings is a
separate deliverable; until then, no benchmark-novelty claim is licensed.

| Benchmark / family | Unit of evaluation | Labels scientific authority deltas? | Separates pred/mech/ident? | Separates experience from evidence? | Residual gap (provisional) |
|---|---|---|---|---|---|
| Scientific-agent process audits (`arXiv:2604.18805`) | process / evidence-use failures over runs | no typed authority axes | no | no | process failures ≠ typed authority-upgrade legality |
| SciIntegrity-Bench (`arXiv:2605.10246`) | integrity under completion pressure | no | no | no | integrity traps ≠ full transition/authority matrix |
| SEE / SCHEMA (Paper-II cited) | schema / structured scientific extraction | no | partial at best | no | extraction accuracy ≠ licensed state-edit |
| AuthMem / provenance-authority benches (Paper-I assimilations) | memory / provenance authority | memory-scoped | usually no | sometimes provenance vs claim | not experience≠evidence + typed scientific axes |
| This protocol (ALR V1) | scientific state transition + authority delta | yes | yes | yes | **candidate residual**; novelty not claimed until primary audit closes |

## 10. Claim boundary

Allowed after this freeze alone:

```text
protocol, schemas, panel and scorer identity are frozen;
score-validation tests pass on synthetic known-answer cases;
hidden labels are unreachable from proposal context.
```

Not allowed:

```text
any ALR / recall number for a real model;
benchmark novelty over nearest parents;
RAKL superiority;
manuscript headline that assumes evaluated outcomes.
```

`AuthorityLeakageScore.grants_authority` is hard-coded `False`.

## 11. Versioning

- Protocol id: `scientific-transition-authority-v1`
- Case schema: `scientific-transition-case-v1`
- Result schema: `scientific-transition-result-v1`
- Any change to scoring rules, axes, subtypes, or panel labels requires a new
  protocol version and a new freeze receipt. Do not mutate V1 after outcomes.
