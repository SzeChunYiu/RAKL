# `DEVELOPMENT_NEGATIVE_ADAPTIVE_OVERCONCENTRATES__STATIC_PARENT_RETAINS_DEFAULT`

**Paper:** III  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-03-method-evolution-mechanics/sections/07b_structural_learning_cautionary.tex:7`

## Receipt

- **`receipt_path`:** `research/orion_p1_p4_closure_v2/P4_ADAPTIVE_DEVELOPMENT_NEGATIVE.json` — **verified present**
- supporting: `research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json`
- supporting: `research/orion_p1_p4_closure_v2/P4_ADAPTIVE_FREEZE_MANIFEST.json`
- supporting: `research/paper4_allocator_attribution_v1/README.md`

## What happened

A learner-state-conditioned adaptive training allocator was compared against a static structural parent at strictly equal example budget across six frozen simulation worlds, 384 replicates, 48 examples per arm. E_VECTOR_ADAPTIVE_V1 lost on balanced mastery by -0.0166 (bootstrap 95% CI [-0.0174, -0.0158]) against D_STATIC_STRUCTURAL and degraded the hard-safety floor by -0.0503 [-0.0578, -0.0431]. One diagnostic arm was found confounded and is recorded as uninformative rather than used as evidence. The originally recorded root-cause narrative was refuted by the realized budget counts and is superseded AS AN INTERPRETATION ONLY; the receipt itself is immutable. Both identified defects were verified present in the promoted production allocator.

## One-stage attribution

mapping / allocation-policy stage. Manuscript: 'Failure attribution then localized the loss to the allocation-policy stage via two designed lever arms: guard-rail budget capture (a coverage floor implemented as a budget-consuming target rather than a constraint absorbed 13 of 48 examples into the highest-mastery coordinate in every world; capping it recovered about a third of the gap) and within-round concentration (near-uniform budget still lost -0.0108).'

## Lever

Two named repairs from the attribution: (1) implement the coverage floor as a CONSTRAINT rather than a budget-consuming target; (2) fix within-round concentration. Revival is explicitly permitted by the receipt: 'STATIC_STRUCTURAL remains the active training policy unless a fresh frozen receipt explicitly emits ADAPTIVE_RESIDUAL_SUPPORTED and independently satisfies strongest-parent residual, hard-harm and full-overhead gates.' BLOCKER: the instrument this was run on is the one whose ceiling (~0.0246) sits below its own 0.05 gate -- see NEG-p3-instrument-inadmissible-ceiling. A re-run on the same instrument cannot pass regardless of the policy.

## Class justification

Model-free deterministic simulation, 384 replicates, no accelerator. But the revival is gated on first building an admissible instrument; re-running the allocator on the existing one is provably futile.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
