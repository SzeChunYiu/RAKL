# GLM52 Mechanism Suite v1.1 — Protocol

**Protocol id:** `GLM52-MECHANISM-SUITE-V1.1`  
**Predecessor:** `GLM52-MECHANISM-SUITE-V1` (unchanged; historical control)  
**Outcome access:** `NO_NEW_GLM_OUTCOME` for this scaffold PR  
**Issue owner:** #443 (Paper II empirical)

## 1. Purpose

v1.1 preserves the frozen scientific questions and estimands from v1 while
replacing experiment-local RAKL approximations with a thin adapter to **current
canonical RAKL**:

| v1 approximation | v1.1 canonical binding |
|------------------|------------------------|
| `RAKL_SELECTIVE` typed selector | `CURRENT_RAKL_EPISTEMIC_SEARCH` via `epistemic_search` |
| `RAKL_MEMORY` | `CURRENT_RAKL_EXPERIENCE` via `compile_problem_fibre` |
| private governance gate scorer | `CURRENT_RAKL_TRAJECTORY` via `epistemic_trajectory` |

v1 arms remain available as historical comparators (`V1_TYPED_SELECTOR`,
`V1_RAKL_MEMORY`, `V1_RAKL_GOVERNED`).

## 2. Frozen from v1 (unchanged)

Unless a pre-outcome amendment is explicitly authored after confirming no model
outcomes were accessed:

- task family definitions and hidden gold semantics
- dev / confirm seed domains (disjoint)
- oracle headroom logic and baseline difficulty logic
- primary estimands and harm / noninferiority logic
- result vocabulary and dev-gate refusal rules

Task difficulty must **not** be tuned because current RAKL loses.

## 3. Provider contract (claude-cn aligned)

Hosted GLM-5.2 uses the **same Anthropic-compatible gateway profile as claude-cn**:

| Variable | Required | Notes |
|----------|----------|-------|
| `ANTHROPIC_BASE_URL` | yes | Z.AI gateway base (e.g. `https://api.z.ai/api/anthropic`) |
| `ANTHROPIC_AUTH_TOKEN` | yes | `x-api-key` header; never stored in repo |
| `ANTHROPIC_MODEL` | no | default `glm-5.2` |
| `RUN_MODEL` | no | script override; wins when set |
| `API_TIMEOUT_MS` | no | request timeout |
| `GLM52_MAX_RETRIES` | no | transport retries |

Typical operator setup: `source ~/.claude-cn.env`

## 4. Experiments (arms in `ARM_INTERVENTION_TABLE.json`)

### 4.1 Selective retrieval

**Primary estimand:** does current RAKL evidence selection improve fresh task
success / evidence fidelity over a strong generic retrieval control under matched
downstream evidence budget?

**Arms:** `GENERIC_HYBRID`, `V1_TYPED_SELECTOR`, `CURRENT_RAKL_EPISTEMIC_SEARCH`,
`GOLD_ORACLE`, `NATIVE_LONG`

**Dev gate (non-RAKL):** `GOLD_ORACLE − GENERIC_HYBRID` exact-verdict ≥ 0.10 and
oracle exact ≥ 0.70. Failure → `NON_DISCRIMINATING_SELECTION_TASK`.

### 4.2 Verified experience transfer

**Primary contrasts:** `CURRENT_RAKL_EXPERIENCE − SHAM_MEMORY`,
`CURRENT_RAKL_EXPERIENCE − GENERIC_MEMORY`, headroom
`GOLD_LESSON_ORACLE − RESET`.

**Arms:** `RESET`, `SHAM_MEMORY`, `GENERIC_MEMORY`, `V1_RAKL_MEMORY`,
`CURRENT_RAKL_EXPERIENCE`, `GOLD_LESSON_ORACLE`

### 4.3 Trajectory governance

**Success rule:** authority leakage decreases **and** valid-update recall stays
within frozen noninferiority bound. Always-abstain cannot win.

**Arms:** `DIRECT`, `V1_RAKL_GOVERNED`, `CURRENT_RAKL_TRAJECTORY`

## 5. Artifact binding (every receipt)

Each adapter output binds:

- protocol id / version
- framework git SHA and method version
- adapter code hash and relevant framework module content hashes
- provider model id and sampling configuration (when executed)
- task manifest hash and state hash

## 6. Development vs confirmatory

This PR lands **scaffold + hostile tests only**. Confirmatory execution remains
blocked until:

1. v1-style non-RAKL dev gates pass on a hosted development run, and
2. protocol coordinates are frozen before confirmatory outcome access.

## 7. Authority boundary

Hosted mechanism-suite evidence is empirical research only. It does not grant
framework promotion, manuscript claims, or model-weight attestation.
