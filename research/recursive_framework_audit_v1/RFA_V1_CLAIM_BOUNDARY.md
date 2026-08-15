# RFA v1 — claim boundary (frozen 2026-08-15)

Status: binding freeze for the Recursive Framework Audit v1 implementation.
Frozen BEFORE any implementation outcome was observed ("do not edit the freeze
after outcomes"). The frozen benchmark is `RFA_V1_FROZEN_BENCHMARK.json`.

## What RFA v1 is

A proposal-side, vertical recursive controller over the existing L0–L7
mechanics. It applies one audit operator to three scopes:

```text
1. a new problem's formulation (question, framework, decomposition,
   interfaces, measurement, evaluator) before commitment;
2. every descendant fiber after a material residual;
3. RAKL's own method evolution (escalation only, never bypass).
```

It selects among 14 pursuit actions (SOLVE_CURRENT, REFRAME_QUESTION,
CHALLENGE_FRAMEWORK, SPLIT, MERGE, REPAIR_INTERFACE, REVISE_MEASUREMENT,
AUDIT_EVALUATOR, RUN_DISCRIMINATOR, DESCEND, ASCEND, EXTERNAL_TRUST_ROOT,
STOP_BOUNDED, CANNOT_CHECK). None mints authority.

## What RFA v1 is not

- **Not a new authority architecture.** No L8; no second authority poset; no
  scalar framework score. Authority updates remain governed by L3 and the
  existing certificate gates.
- **Not a method-promotion gate.** RFA may request Self-RAKL escalation; it
  cannot bypass `CURRENT_SELF_EVOLUTION_CONTROLLER`
  (`src/rakl/self_evolution_controller.py`), which stays non-sovereign.
- **Not utility evidence.** Passing the known-world conformance benchmark
  shows executable, fail-closed control semantics only. It says nothing about
  whether recursive formulation improves fresh-task outcomes.

## Standing invariants (violation = defect, not tuning target)

```text
audit actions do not mint scientific authority
negative history remains addressable after reframing
multiple plausible responsibility levels require a discriminator before revision
atomicity is target/evaluator/split-family/cutoff relative
ancestor supersession stales dependent descendant closure certificates
evaluator change closes the evaluation epoch
resource exhaustion with material open audit yields CANNOT_CHECK
```

## Utility path (NOT preregistered here)

The RFC-v1 benchmark design (7 arms A–G, families F0–F10 with hidden
independently validated defect labels, cost metrics, hard gates, terminals
incl. STATIC_FRAMEWORK_SUFFICIENT and FALSE_REFRAME_HARM) is vendored as
`reference/RFC_V1_BENCHMARK_DESIGN.json` with status
DESIGN_FOR_FUTURE_FREEZE. Before any utility execution it must be re-frozen
on the implementation subject. Epoch A (un unfamiliar-problem arm comparison
with well-posed controls) and Epoch B (governed self-improvement on disjoint
fresh tasks under a fixed evaluator) are Paper VI obligations.

## Non-claims

No superiority over DIRECT_SOLVE, STATIC_CURRENT_RAKL, GENERIC_SELF_REFLECTION
or any parent arm. No claim that a globally correct formulation exists or is
discoverable. No scientific, method-promotion, or publication authority.
