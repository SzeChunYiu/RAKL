# RAKL / ORION — START HERE

Read this file first. It is the entry point to 90 documents that were previously flat and
alphabetical with no index.

The framework is a **progressive build**: each layer introduces atoms and becomes able to
express something the layers beneath it cannot. A layer may depend only on layers beneath it.
Read downward; do not start in the middle.

- **Full index:** [`MAP.md`](MAP.md) — every document, assigned to a layer or a kind.
- **Machine-checkable ladder:** `research/framework_ladder/ladder.json`, checked by
  `python -m rakl.framework_ladder`.
- **Formal source:** [`FORMAL_SYSTEM_SPECIFICATION.md`](FORMAL_SYSTEM_SPECIFICATION.md). The
  ladder is *read off* its 14 sections, which were already ordered by dependency. This is not a
  new taxonomy.

## The ladder

| Layer | What becomes expressible | Primary document |
|---|---|---|
| **L0 · Object** | Two sources describing one object through different projections under different contexts. Without it, disagreement cannot be told from difference-of-view. | [`APPLE_PRINCIPLE`](APPLE_PRINCIPLE.md) |
| **L1 · Transition** | A step has a type, and composing steps is licensed or not. Without it, any two claims chain. | [`PROBLEM_SOLVING_ALGEBRA`](PROBLEM_SOLVING_ALGEBRA.md) |
| **L2 · Gluing** | Locally consistent pieces may have **no global section**. Obstructions become first-class. | [`CONTEXTUAL_ATLAS_GLUING`](CONTEXTUAL_ATLAS_GLUING.md) |
| **L3 · Authority** | Evidential standing is multi-coordinate, and only certified transitions change it. Without it, fluency substitutes for evidence. | [`AUTHORITY_POSET`](AUTHORITY_POSET.md) |
| **L4 · Navigation** | Solving is search for an authority-valid support structure reaching the target — and **failing is informative**: the min-cost cut names what must be established. | [`EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION`](EPISTEMIC_PATHFINDING_AND_GAP_COMPLETION.md) |
| **L5 · Saturation** | When search may stop. Certifiable only over a finite basis — which is what distillation supplies. | [`EPISTEMIC_SATURATION`](EPISTEMIC_SATURATION.md) |
| **L6 · Method evolution** | The method itself is an object the system may revise. | [`SELF_RAKL`](SELF_RAKL.md) |
| **L7 · Assimilation** | A competitor's mechanism can be absorbed under RAKL conditions. | [`METHOD_ASSIMILATION`](METHOD_ASSIMILATION.md) |

**L4 is the framework's verb.** Everything else names a noun. It is the layer that says what
the structure is *for*, and until 2026-08-14 it had no paper home: its specification sat in a
document marked non-activating, and its three appearances across the papers were all
*constraining* — Paper I's is inside a noninterference section. See issue #627.

## Readiness — how a layer is closed out

A layer is **READY** only when all of the following hold. They are **non-compensatory**: a
strong soundness coordinate never offsets an absent benefit coordinate, exactly as the
framework's own no-scalarization result requires.

```text
spec_present        the layer is specified, not quarantined
paper_home          a paper states it as a positive claim, not only as a constraint
soundness           claims proved or machine-checked
gate_falsifiable    its gates are capable of failing
benefit_measured    its benefit obligation has been executed
```

The **frontier** is the lowest layer that is not READY. Work happens at the frontier: a higher
layer's benefit is not interpretable while a lower layer's is unmeasured.

```bash
python -m rakl.framework_ladder      # prints readiness and the current frontier
```

## The assimilation stance

Nearest and prior work is **food, never a threat**. The working loop — the same one the
framework implements — applies to the framework's own construction: *see a lot, saturate
the knowledge space, absorb every strong parent, synthesize the unique fibre.*

Absorbing a parent means chewing it: compile its mechanic in RAKL vocabulary
(`research/external_research_agents/mechanics/`), design faithful-vs-adapted challengers,
and measure the transfer. Uniqueness comes from the synthesis plus the delta organs —
authority transport, fail-closed refusal, obstruction preservation — not from avoiding
overlap. If a parent already has one of those organs, record it and eat that too.

Never lead with threat language ("RED", "occupies our signature") — a superior parent is a
map of the mechanism space. Measured precedent: the causal-transportability parent was
rated RED, absorbed instead of defended against, and its adapted transfer became Paper II's
strongest result.

## Two standing hazards

**Soundness is not benefit.** Every non-interference theorem in this programme is satisfied by
a system that never acts. That is why each mechanized claim must name a non-vacuity witness,
and why `research/mechanism_benefit_ledger/` tracks benefit as a column separate from
soundness. See `src/rakl/mechanism_benefit.py`.

**A gate that cannot fail is worse than no gate.** It consumes a confirmatory budget, emits
PASS, and licenses a claim the evidence never supported. Audit gates with
`src/rakl/gate_falsifiability.py` *before* spending on an experiment, and audit **per
condition** — a composite gate can look falsifiable while most of its components are
decorative.

Related: self-authored measurement is the recurring failure. If the same author writes both the
renderer and the extractor, or the gate and the outcome, the result measures the authorship.

## Where to go next

| You want to | Read |
|---|---|
| Understand the whole formal system | [`FORMAL_SYSTEM_SPECIFICATION`](FORMAL_SYSTEM_SPECIFICATION.md) |
| Know what may change scientific authority | [`CONSTITUTION`](CONSTITUTION.md) |
| Run the system | [`REFERENCE_RUNTIME`](REFERENCE_RUNTIME.md), [`RAKL_V3_API`](RAKL_V3_API.md) |
| Measure it | [`RAKL_QUANTITATIVE_EVALUATION_MODEL`](RAKL_QUANTITATIVE_EVALUATION_MODEL.md) — a full measurement architecture, still marked research-only |
| See every document | [`MAP.md`](MAP.md) |

## Reading the `[research-only]` marker

Nine documents declare themselves non-activating. That status is **not** self-evidently wrong —
some are parked deliberately. But the quarantine held the framework's generative half,
including L4's specification and the measurement architecture, while the papers carried the
constraining half. Treat the marker as a question, not an answer.
