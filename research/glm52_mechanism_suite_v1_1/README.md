# GLM-5.2 Mechanism Suite v1.1 — current-framework adapter scaffold

Successor to merged v1 (`research/glm52_mechanism_suite_v1/`). v1 remains a
historical registered harness; v1.1 binds the same experimental questions to
canonical RAKL machinery:

- epistemic search (`ScientificSearchQuestion`, typed intents, diversification)
- `ProblemFibre` / experience materialization
- typed authority (`v3_authority`)
- epistemic trajectory scoring (`evaluate_epistemic_trajectory`)

**Status:** `REGISTRATION_ONLY` — `NO_NEW_GLM_OUTCOME`. L1 adapter + Wave 2 offline
harness lanes (see `WAVE2_HANDOFF_LANES.md`); no confirmatory model runs until
non-RAKL dev gates pass.

## Provider (claude-cn / Z.AI gateway)

Hosted GLM-5.2 uses the **same env profile as claude-cn**:

```bash
source ~/.claude-cn.env
# or export ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN manually
```

Implementation: `rakl.hosted_anthropic_client` (shared) and thin
`provider.py` in this directory. Credentials never enter Git, artifacts, or logs.

## Documents

| File | Role |
|------|------|
| `PROTOCOL_V1_1.md` | Frozen scientific design inherited from v1 + adapter delta |
| `WAVE2_HANDOFF_LANES.md` | Lane 2–4 offline harness map (post-L1) |
| `FRAMEWORK_ADAPTER_SPEC.md` | Adapter contract and canonical binding |
| `HOSTED_PROVIDER_CONFIG.json` | claude-cn-aligned env manifest (no secrets) |
| `FRAMEWORK_SUBJECT_MANIFEST.json` | Framework SHA, method version, module hashes |
| `ARM_INTERVENTION_TABLE.json` | Arm definitions (docs/stubs only in this PR) |

## Issue ownership

Paper II empirical owner: **#443**.
