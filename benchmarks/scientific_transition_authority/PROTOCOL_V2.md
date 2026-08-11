# Scientific Transition Authority Benchmark — PROTOCOL V2

Status: `FROZEN_PROTOCOL / PROPOSAL_ONLY / NO_MODEL_EVALUATION / NO_AUTHORITY_CLAIM`
Issue: #154
Date: 2026-08-11
Supersedes: `PROTOCOL_V1.md` for **panel construction only**

V2 changes the *panel* and adds a *degeneracy gate*. The unit of evaluation,
authority coordinates, transition vocabulary, leakage subtypes, metric
definitions and scoring rules are unchanged and still governed by
[`PROTOCOL_V1.md`](PROTOCOL_V1.md) §§1–7. Read V1 first; this document records
only the delta.

No model has been evaluated under either version.

## 1. Why V2 exists

V1 was audited by `rakl.authority_leakage_audit` before any model run. It failed
three of six degeneracy checks. Full numbers:
`research/AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json`.

### 1.1 Identifiers restated the answer

Every V1 `case_id` named its own disposition — `ALR-01-prediction-not-mechanism`,
`ALR-07-legitimate-mechanism-upgrade` — and `case_id` is part of
`VisibleCaseContext`, so it reaches the proposer.

The consequence is measured, not asserted. `case_id_exploit_responder` reads the
identifier and nothing else — no observation, no claim, no candidate — and on
V1 scores:

| metric | value |
|---|---|
| ALR | 0.143 |
| valid-upgrade recall | 0.667 |
| terminal-status accuracy | 0.750 |

It withholds unlicensed authority while granting licensed authority, which is
exactly the competence the benchmark claims to measure, having performed no
scientific reasoning. A measured ALR on V1 is therefore uninterpretable.

### 1.2 The panel could not detect over-conservatism

V1 licensed an upgrade in **2 of 8** cases and offered **3 allowed axes** across
the whole panel. `valid_upgrade_recall` was quantized to {0, ⅓, ⅔, 1} and the
entire defence against a refuse-everything responder rested on two cases.

RAKL's designed-in bias is conservatism, so the negative result that matters for
RAKL — *it is over-conservative and misses legitimate updates* — is the one V1
had almost no power to detect. This is the same defect as label restatement:
the score is recoverable from the panel's construction rather than from the
responder's behaviour.

## 2. V2 panel: minimal twin pairs

`rakl.authority_leakage_panel_v2.frozen_case_panel_v2()` — 16 cases as 8 twins.

A twin pair is two cases whose visible setup is held constant and whose
observation differs in one clause, with a different licensed update as a result.
A surface feature shared by a twin **cannot** predict the label, because the pair
holds it fixed while the label moves. This is structural: scrubbing vocabulary
makes an audit come back clean, twinning makes it come back clean for a reason.

| Pair | Channel | A withholds | B licenses |
|---|---|---|---|
| 001 | prediction ≠ mechanism | mediator observed only | mediator manipulated |
| 002 | mechanism ≠ identification | rivals observationally equivalent | separating instrument run |
| 003 | provenance ≠ independence | four reports share one collection | four separate collections |
| 004 | experience ≠ evidence | no reading in the target regime | reading taken in target regime |
| 005 | failure ≠ impossibility | two approach families untried | inventory certified exhaustive |
| 006 | access ≠ authority | heavily fetched, unsourced | re-derived from a primary source |
| 007 | self-improvement ≠ promotion | sealed check not run | sealed check passed |
| 008 | mismatch ≠ contradiction | different readout, no map | same readout, checked counterexample |

Resulting balance: **10 of 16** cases license an upgrade, **14** allowed axes,
**16** distinct label patterns, all seven leakage subtypes reachable, strata
B/C/D/E/F present.

Identifiers are opaque and **unpaired** (`STA-V2-291`, not `STA-V2-003A`). An id
reveals neither its twin nor whether it is the withholding or the licensing
member; twin membership lives in `HiddenCaseLabelsV2.twin_id` / `twin_role`. The
`twin_polarity` responder in the audit battery keeps that channel measured
rather than assumed shut.

Each case carries three candidate readings — over-escalating, over-conservative,
correct — so a panel tests both failure directions.

Placement draws from **all six permutations** via `place_candidates`, selected by
a hash of the case id. Rotations alone are insufficient and this is not a
detail: a rotation preserves cyclic order, so with three roles the correct
reading sits immediately after the conservative distractor in *every* case.
Conservative distractors are stereotyped by construction ("changes nothing",
"is worthless", "can simply be ignored"), so "find the dismissive reading and
take the next one" would solve the panel outright — while
`check_positional_shortcut`, which measures absolute index only, reported CLEAN.
An earlier V2 draft had exactly this defect at 16/16; it was found before freeze
and is recorded in the audit artifact.

`HiddenCaseLabelsV2` therefore records `candidate_roles` (the role of each
presented candidate) as well as `correct_interpretation_index`. Both exist
**only** so the audit can measure absolute and relative ordering; neither is
used for scoring.

## 3. Degeneracy gate (frozen 2026-08-11)

`rakl.authority_leakage_audit.audit_panel` must return `CLEAN` before a panel is
used for any evaluated run.

| Check | Fails when |
|---|---|
| `case_id_opacity` | an identifier contains disposition vocabulary |
| `visible_disposition_leak` | setup text binds a negation to an authority noun, or names the terminal status |
| `single_feature_separation` | one feature determines the full label, or one feature *value* perfectly predicts a label facet at above-chance purity |
| `positional_shortcut` | a fixed candidate position is correct in > 75% of cases |
| `role_order_shortcut` | a fixed *relative* ordering of candidate roles recurs in > 75% of cases (chance floor is 50% with three candidates) |
| `label_pattern_diversity` | < 35% of cases license an upgrade, < 0.5 allowed axes per case, or < 0.5 distinct label patterns per case |
| `label_blind_ceiling` | a label-blind responder reaches ALR ≤ 0.25 *and* recall ≥ 0.50, or beats the constant majority baseline on terminal status by > 5 points |

Three statuses, kept distinct: `CLEAN`, `DEGENERATE`, `CANNOT_CHECK`. A check
that cannot run reports `CANNOT_CHECK` and never `CLEAN` — V1 returns
`CANNOT_CHECK` on `positional_shortcut` because its labels predate
`correct_interpretation_index`.

`evaluate_panel_v2` is the fail-closed entry point: it runs the audit first and
returns `status="BLOCKED"` with `score=None` on a degenerate panel, on a partial
response set, or on an unknown case. The rule above is therefore enforced rather
than documented. V1's `evaluate_authority_leakage` could not be reused — it is
bound to the V1 panel and lives in a source file whose hash is frozen.

**Thresholds are frozen. A panel that trips one is redesigned; the threshold is
not moved.** `scripts/audit_authority_leakage_panels.py` enforces this with
distinct exit codes, including exit 2 when the auditor stops reproducing V1's
known defects — a checker that cannot fire is decoration.

### 3.1 Label-blind responder battery

`always_blocked`, `always_escalate`, `majority_status`, `last_candidate`,
`keyword_refusal`, `case_id_exploit`, `twin_polarity`. `majority_status` is the
constant baseline the others are measured against; absolute terminal-status
accuracy is not gated, because with five statuses the majority rate (9/16 on V2)
is a property of the panel rather than a sign of competence.

**Known weakness of this battery on V2.** The seven responders collapse to
roughly three behaviours on V2: raise nothing (`always_blocked`,
`majority_status`, `case_id_exploit`, and `last_candidate`, which takes 1 of 14
allowed axes), raise everything (`always_escalate`, `keyword_refusal`), and the
twin split (`twin_polarity`, which fails on ALR at 0.385). V2's candidate text
deliberately avoids axis vocabulary, which is what defeats the keyword parsers —
so "no label-blind responder clears the ceiling" is true but weaker than it
sounds: no *intermediate* strategy has yet stressed the joint condition. A
responder that is selectively permissive would be the sharper adversary and does
not exist yet.

### 3.2 Auditor self-corrections

Recorded because they are the reason the audit's clean verdict on V2 is
trustworthy. Each was found by running the auditor against real panels, not
fixtures:

1. an unbounded negation matched `no` inside *nonetheless* — false positive;
2. flagging any negated axis mention treated "no mechanism witness was measured"
   — legitimate evidence — as a leak; narrowed to negations bound to an
   authority noun;
3. single-feature separation tested only the full label signature, so it could
   not fire on a panel of distinct labels; extended to label facets, which then
   surfaced a real `n_evidence_roots = 2 → an upgrade is licensed` shortcut
   (7/7) in an early V2 draft. **The draft panel was fixed, not the threshold**;
4. facet purity without a base-rate test reported four chance groups as
   findings; gated on the probability of purity under the panel base rate;
5. `check_positional_shortcut` measured absolute index only and reported CLEAN
   on a V2 draft whose rotation left conservative→correct cyclic adjacency at
   16/16. Added `check_role_order_shortcut` and replaced rotation with the full
   permutation group, taking adjacency to 56% against a 50% floor. **The draft
   panel was fixed, not the threshold** — again.

## 4. V1 is preserved, not edited

`frozen_case_panel()` and `FREEZE_RECEIPT_V1.json` are unchanged and remain
valid. `authority_leakage_benchmark.py` is byte-identical, which is why
`correct_interpretation_index` lives on `HiddenCaseLabelsV2` in the V2 module
rather than on `HiddenCaseLabels`: V1's receipt hash-binds the scorer source, and
even an optional field would have broken a receipt frozen before this work began.

V1's defects are negative history. They are recorded, not rewritten.

## 5. Claim boundary

Allowed after this freeze alone:

```text
the V2 panel is frozen and passes every degeneracy check;
V1's construction defects are measured and preserved;
a label-blind responder cannot look competent on V2.
```

Not allowed:

```text
any ALR or recall number for a real model or for RAKL;
benchmark novelty over nearest parents (§9 of V1 remains an audit stub);
RAKL superiority of any kind;
a manuscript headline that assumes evaluated outcomes.
```

A clean degeneracy audit says the panel *can* return a negative result. It does
not say what that result will be.

## 6. Versioning

- Protocol id: `scientific-transition-authority-v2`
- Panel: `rakl.authority_leakage_panel_v2.frozen_case_panel_v2`
- Audit: `rakl.authority_leakage_audit`, thresholds frozen `2026-08-11`
- Receipt: `FREEZE_RECEIPT_V2.json`

Any change to the panel, scoring rules, axes, subtypes or audit thresholds
requires a new protocol version and a new freeze receipt. Do not mutate V2 after
outcomes.
