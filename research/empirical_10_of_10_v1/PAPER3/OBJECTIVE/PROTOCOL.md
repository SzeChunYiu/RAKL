# Paper III / V2 Paper II — objective lane scaffold (#444 Track A)

**Status:** `OBJECTIVE_LANE_SCAFFOLD_ONLY / NO_ITEMS_GENERATED / NO_OUTCOME_ACCESS`  
**Tip binding:** `496edc5ead136980287ac2e72efb486691945366`  
**Parent registration:** `research/paper3/PAPER3_TRACK_A_REGISTRATION_V1.md`  
**Executable witness v2:** `src/rakl/structural_transport_v2.py` (#491 / #486)

## Purpose

Create the directory contract and pre-outcome manifests for the **objective
known-answer benchmark** so Track A can proceed without inventing humans and
without claiming empirical results.

This packet does **not**:

- generate confirmatory items;
- access or invent gold decisions;
- run semantic or witness arms;
- authorize capability or Wave-2 confirmatory model jobs;
- substitute for independent natural-domain humans (Track C).

## Ordering (fail-closed)

```text
registration (Track A v1)
  -> this OBJECTIVE scaffold / generator manifest freeze
  -> generator+verifier implementation
  -> development set + anti-degeneracy + baseline mid-band check
  -> confirmatory set freeze BEFORE outcome access
  -> predictive / paired / family-robustness results
```

## Artifact contract

| File | Role now | When filled |
|------|----------|-------------|
| `PROTOCOL.md` | this scaffold | — |
| `GENERATOR_MANIFEST.json` | families / item types / freeze identity | before first generation |
| `HIDDEN_GOLD_MANIFEST.json` | sealed store path contract | before confirmatory freeze |
| `OBJECTIVE_TASKS.jsonl` | empty placeholder | after generation |
| `VERIFIER_BINDING.json` | verifier/witness schema binding | before outcome access |
| `DEGENERACY_AUDIT.json` | hostile responder plan | before candidate scoring |
| `POWER_RECEIPT.json` | pointer to Track A power table | before confirmatory n |
| `MACHINE_WITNESS_PROTOCOL.json` | StructuralWitnessV2 consumption | before arm run |
| `MACHINE_WITNESS_OUTPUTS.jsonl` | empty | after arm run |
| `SEMANTIC_CONTROL_MANIFEST.json` | control arm freeze | before arm run |
| `SEMANTIC_CONTROL_SCORES.jsonl` | empty | after arm run |
| `PREDICTIVE_RESULTS.json` | absent until outcomes | after paired analysis |
| `PAIRED_INFERENCE.json` | absent until outcomes | after paired analysis |
| `FAMILY_ROBUSTNESS.json` | absent until outcomes | after LOFO |

Outcome-bearing result files are intentionally **not** created here.

## Claim boundary

`OBJECTIVE_LANE_SCAFFOLD_ONLY`. No `PAPER3_EMPIRICAL_10_OF_10_*` terminal.
Natural-domain external validity remains `BLOCKED_HUMAN` (#216 / Track C).
