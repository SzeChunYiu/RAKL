# GLM52 Mechanism Suite v1.1 — status

| Field | Value |
|-------|-------|
| protocol_id | `GLM52-MECHANISM-SUITE-V1.1` |
| outcome_access | `NO_NEW_GLM_OUTCOME` |
| adapter | `CanonicalFrameworkAdapter` v1.1.0 scaffold |
| provider | claude-cn / Z.AI Anthropic-compatible gateway (env-only) |
| provider manifest | `HOSTED_PROVIDER_CONFIG.json` |
| offline_selftest | **PASS** — see `OFFLINE_SELFTEST_RECEIPT.json` (29 pytest + wave2 stubs; 0 API calls) |
| hosted_smoke | **PASS** — see `HOSTED_SMOKE_RECEIPT.json` (1 non-confirmatory connectivity call; Mac hosted API) |
| CAPABLE_MODEL_AVAILABLE | `NO_REFUTED` — smoke does not flip oracle gates |
| confirmatory | **BLOCKED** until v1 non-RAKL dev gates pass on hosted runs |
| wave2_lanes | L2 retrieval, L3 experience, L4 governance — offline stubs only |
| wave2_freeze | `WAVE2_FREEZE_RECEIPT.json` + `NO_NEW_GLM_OUTCOME_RECEIPT.json` |
