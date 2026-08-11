# Experience → method promotion with protected fresh assurance — preregistration v1

Status: `DRAFT / PROPOSAL_ONLY / PENDING_FREEZE / NO_EMPIRICAL_CLAIM`
Issue: #157
Date: 2026-08-11

This freezes the **design** for the next executable gate. It does not run arms,
does not mint method authority, and does not claim Self-RAKL evolution evidence.

## Research question

Can RAKL convert repeated TaskEpisodes into a reusable procedural Lesson **only**
after protected fresh assurance, while preserving failed candidates as negative
history and without letting a promoted Lesson mint scientific-claim authority?

## Arms (matched resources)

| Arm | Intervention |
|---|---|
| `A_RESET_NO_LESSON` | no persistent lesson |
| `B_REFLECTION_ONLY` | same-session reflection text; no structured Lesson object |
| `C_UNRESTRICTED_LESSON` | candidate Lesson reusable after development evidence only |
| `D_RAKL_PROTECTED_LESSON` | candidate frozen → protected fresh assurance → promote/reject/narrow |
| `E_SHAM_LESSON` (optional) | matched memory object with non-causal content |

## Task families (minimum)

1. Genuine reusable repair (true transfer)
2. Development-only overfit
3. Boundary-scoped lesson (in-scope + hostile out-of-scope)
4. False diagnosis (missing evidence/tooling, not method)
5. Contradictory experience
6. Superseded lesson

## Fresh-assurance chronometry (blocking)

Before assurance outcomes are opened, freeze:

```text
candidate bytes/hash
development episode ids
assurance tasks + evaluator
model/tool/resource contract
promotion threshold / blockers
allowed candidate revisions
chronology receipt
```

If the candidate changes after seeing assurance, it is a new version requiring a
new protected evaluation.

## Admissibility gates (from #155/#238 lessons)

- **G1**: development must mint ≥1 verified corrective object before transfer
  scoring; failure-minted pseudo-lessons do not count (`CANNOT_IDENTIFY`).
- **G2**: if retrieval is specified, `retrieval_calls > 0` per task; whole-state
  stuffing is a protocol failure even when answers improve.
- Promoted procedural Lesson must not escalate scientific G/R/M/I/D authority
  (#152 noninterference).

## Upstream blockers (do not execute cells yet)

```text
#238 / #247 — discriminative verified-lesson learning path + capability gate
#242 — integrated scientific-authority surface stable enough for noninterference checks
#154 — ALR metrics available when authority outcomes are co-reported
```

Execution coordinates therefore remain `PENDING_FREEZE_*` until those hashes
exist. `PROTOCOL_FROZEN` and any `PENDING_FREEZE` sentinel are mutually exclusive.

## Outcomes (report separately)

```text
development gain
fresh-assurance gain
later fresh-reuse gain
invalid / out-of-scope reuse rates
lesson rejection precision/recall where labelled
cost of induction + assurance + per successful reuse
method-state counts: proposed / promoted / rejected / narrowed / superseded / CANNOT_CHECK
```

## Claim boundary

Allowed after this draft alone:

```text
arm vocabulary, family list, assurance chronometry and blockers are written down.
```

Not allowed:

```text
protected method-evolution empirical claim;
Self-RAKL promotion evidence;
equivalence to AutoSci SciEvolve.
```
