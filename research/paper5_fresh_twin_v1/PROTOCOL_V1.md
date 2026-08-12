# Paper 5 fresh replay twin protocol v1

**Status:** design freeze only — `NO_OUTCOME_ACCESSED`  
**Issue:** #446 lane 7 (fresh replay / twin causal bridge)  
**Parent:** #442 empirical campaign master

## Scientific question

Can fresh untouched structural twins, abstracted from historical failure families, support a prospective causal test of whether current RAKL improves **correct next gluing action** relative to reset and generic-retrieval controls — without reusing exact historical cases current RAKL may have already learned from?

## Exact estimand (per twin task)

Primary per-task outcome:

```text
1{ submitted_action == deterministic_correct_action }
```

Causal contrasts (future confirmatory packet only; not accessed here):

```text
CURRENT_RAKL_FULL_EXPERIENCE - MODEL_ONLY_RESET
CURRENT_RAKL_FULL_EXPERIENCE - GENERIC_RETRIEVAL
CURRENT_RAKL_FULL_EXPERIENCE - CURRENT_RAKL_NO_CROSS_CYCLE_MEMORY
CURRENT_RAKL_FULL_EXPERIENCE - SHAM_MEMORY   (optional)
```

## Protocol version

```text
paper5-fresh-twin-protocol-v1
generator: paper5-fresh-twin-generator-v1
```

## Framework / model subject

Not bound in this design freeze. Confirmatory execution must record exact RAKL SHA, method version, adapter identity, and model/provider before any arm outcome access.

## Twin design

For each registered failure family `F`:

```text
historical development case (motivation only)
    |
    +--> abstract structural signature (registry)
    |
    +--> fresh VALID twin   (hidden gold: ACCEPT_VALID_GLUE)
    +--> fresh INVALID twin (hidden gold: REJECT_FALSE_TRANSFER)
```

Registered families:

1. `QUANTIFIER_SCOPE_LOCAL_GLOBAL`
2. `POINTWISE_UNIFORM_FAMILY`
3. `NORM_CONORM_MISMATCH`
4. `PRODUCER_CONSUMER_SCOPE`
5. `SAME_ROOT_CORROBORATION`
6. `LOCAL_CORRECT_WRONG_CONSUMER`

## What changed (this packet)

- Added deterministic fresh-twin generator + family registry.
- Added solver/evaluator split with hidden gold hash.
- Added leakage sweep over forbidden historical tokens.
- Added freeze stub with manifest hash.

## What did not change

- Longitudinal `#253` harvest artifacts.
- Four-arm attribution preregistration (#251 lineage).
- GLM52 mechanism suite v1 (historical harness on main).
- Training-time ladder gates (#461 / #466 / #467).
- QuantifierCompatibilityWitness (#459) and pre-scratch hook (#464).

## Negative history preserved

Historical cycles remain development evidence only. Exact reruns of NS R8, Hodge C009/C010, YM R22/XM024 are explicitly forbidden as confirmatory evidence for current RAKL.

## Shortcut / contamination controls

- Solver bundle excludes `correct_action`, family labels, and historical ids.
- Family-specific forbidden token list enforced by leakage sweep.
- Task ids are content hashes (`FT-…`), not semantic family names.
- Deterministic verifier — no LLM judge for gold.
- Valid/invalid labels are not derived from perturbation identity exposed to solver.

## Tests

```bash
python -m pytest tests/test_paper5_fresh_twin_generator.py -q
```

## Outcome access status

```text
NO_OUTCOME_ACCESSED
```

No model run, no confirmatory arm execution, no causal lift measured.

## Authority / claim boundary

Process/design evidence only. Does not mint theorem authority, framework promotion, or Paper V 10/10 causal attribution.

## Issue ownership / dependencies

- Owner: #446
- Depends on: #442 campaign framing; capability gate #443 may block downstream four-arm bridge
- Blocks: confirmatory fresh-twin causal packet (not yet authored)
- Sibling lanes must not duplicate: GLM v1.1 (#443), metrology schema upgrade, #461, #459, #464

## Registered causal arms (future packet)

```text
A  MODEL_ONLY / RESET
B  GENERIC_RETRIEVAL
C  CURRENT_RAKL_NO_CROSS_CYCLE_MEMORY
D  CURRENT_RAKL_FULL_EXPERIENCE
E  SHAM_MEMORY (optional)
```

Primary outcomes when executed:

```text
correct next action
invalid glue / false transfer
valid transfer retention
residual contraction
CANNOT_CHECK correctness
cost-to-first-valid-scoped-result
```

## Confirmatory freeze checklist (future)

Before any confirmatory outcome access, freeze:

```text
repo/framework SHA
model/provider/revision
this protocol + generator hashes
family registry hash
task manifest hash
arm definitions + state/memory
evaluator binding
MDE / harm bounds / multiplicity
seeds
resource ceiling
stopping rule
```

Any load-bearing change after outcome access requires a new protocol version.
