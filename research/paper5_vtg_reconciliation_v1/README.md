# Paper V — VTG artifact reconciliation (`P5-VTG-RECONCILIATION-V1`)

**Status:** relation record. **Creates no new freeze.** Grants no scientific or promotion authority.
**Verdict on the registered discovery experiment:** `BLOCKED` / `CANNOT_CHECK` (substrate).

## Why this exists instead of a new preregistration

The task was to "scope the held-out theorem-family / verified-transformation-geometry evaluation
precisely and freeze it". Checking first showed that **Paper V already carries three VTG artifacts**,
two of which are frozen — and that **none of them states its relation to the others**. Writing a
fourth freeze would have been the parallel-framework failure, not the deliverable.

| Ref | Artifact | Kind |
|---|---|---|
| A1 | `publication/papers/paper-05-.../sections/11_verified_transformation_geometry.tex` | manuscript formulation |
| A2 | `research/deep_hardening_v1/VTG_PHASE0_1_PREREGISTRATION.md` | **frozen** preregistration |
| A3 | `research/p5_p6_saturation_v1/packets/vtg_lean_geometry_v2.json` (`MRP-P5-VTG-LEAN-V2`) | **frozen** mechanic research packet |

## The relation

**A1 ≡ A2 — same experiment.** A1's "Phase-0/1 falsification experiment" subsection is the manuscript
projection of A2. A2 is the canonical registered form.

**A2 is upstream of A3 — different scope, ordered.** They are not competing freezes:

| | A2 (Phase-0/1) | A3 (`MRP-P5-VTG-LEAN-V2`) |
|---|---|---|
| Question | Does a useful local navigation geometry **exist**? | What does geometry add **incrementally**? |
| Solver | **No LLM solving in Phase 0** | LLM tactic generators (BFS-Prover, HTPS, LeanProgress) |
| QoI | `N(k,B)` profile, componentwise | paired fully-costed benefit over strongest parents |
| Universe | evaluator-only gold universe, hidden routes | `VTG-LEAN-FACTORIAL-DEV-V2` / `-FRESH-V2` |
| Cost | no model term | charges `decode_cost`, `model/tactic_generation` |

A3 **presupposes A2's positive**: if A2 terminates at `NO_USEFUL_LOCAL_GEOMETRY_IN_REGISTERED_SCOPE`,
A3's incremental-value question has no object to measure. A3's own `applicability_gate_state` is
`UNASSESSED`, consistent with this reading.

**This ordering was stated in neither artifact before now.**

## Two defects found

### `P5-VTG-D1` — the manuscript offers an unregistered outcome branch

A1 line 171 lists `NO_SAFE_NAVIGATION_QUOTIENT_AT_TESTED_SCALE` among allowed narrower outcomes.
A2's terminal list does not contain it, and **it appears nowhere else in the repository** — a
repo-wide grep excluding `.git` returns only the manuscript file itself and byte-identical copies of
that file inside `.claude/worktrees`. The other three terminals all resolve to
`research/deep_hardening_v1/` artifacts.

**Consequence:** a Phase-1 run whose honest outcome is "no safe navigation quotient at the tested
scale" has no registered terminal to land in. Registering it *after* seeing such a result would be a
post-hoc registration, which the no-post-result-rescue rule forbids.

**Not repaired here.** A2 is a frozen preregistration; this packet holds no authority to amend it.
The repair must happen before any Phase-1 execution: either register the terminal in A2, or drop it
from A1.

### `P5-VTG-D2` — the registered experiment is substrate-blocked

A2 requires a frozen bounded Lean environment with an evaluator-only complete materialized
transition/proof universe and kernel replay receipts. **laptop billy — the only sanctioned compute
host — has no Lean toolchain**: `which lake lean elan` returns nothing and `~/.elan` is absent
(checked 2026-08-14).

Verdict: `CANNOT_CHECK`. Prerequisites to unblock are enumerated in `RECONCILIATION_V1.json`.

## What was deliberately not done

**No synthetic substitute was run and reported as a Phase-0/1 result.** On a world whose statistics
are authored in-house, a *positive* navigability finding would be near-worthless, and presenting one
as evidence for A2's question would be substrate substitution. A *negative* finding on such a world
could carry a structural constraint — but that is a different experiment and would need its own
freeze, which this packet does not create.

Installing elan + mathlib and building the evaluator-only gold universe is multi-session engineering,
not a within-fiber task. It is recorded as the next action with its prerequisite list rather than
half-started.

## Strongest currently-defensible Paper V claim

> Under a frozen subject, ORION's verified-transformation-geometry layer is **architecturally
> non-interfering**: map incompleteness, erroneous geometry, or a spurious abstract route can
> increase search cost or cause search failure, but cannot promote or refute the target theorem.
> This holds as a proposition with premises (i), (ii) and (iv) machine-enforced at the audited
> revision, and premise (iii) **only partially** — the quotient-revalidation obligation is
> contract-defined and unit-tested but has no production caller, so it is a caller obligation, not a
> machine-enforced invariant.

That is an **architectural** claim, not a discovery-performance claim. The discovery-performance
question — whether verifier-defined reachability admits a useful local navigable geometry — remains
**open and unexecuted**, now blocked at the substrate rather than at the specification.
