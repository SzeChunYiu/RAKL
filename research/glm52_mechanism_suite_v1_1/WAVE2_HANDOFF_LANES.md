# Wave 2 handoff lanes — GLM52 Mechanism Suite v1.1 (#443)

**Outcome access:** `NO_NEW_GLM_OUTCOME` until hosted dev gates pass.

After L1 (`CanonicalFrameworkAdapter` in PR #472), three parallel offline harness
lanes wire experiment arms, gate logic, and hostile cases without model runs.

| Lane | Module | Arms |
|------|--------|------|
| 2 | `harness/selective_retrieval_harness.py` | `GENERIC_HYBRID`, `V1_TYPED_SELECTOR`, `CURRENT_RAKL_EPISTEMIC_SEARCH`, `GOLD_ORACLE`, `NATIVE_LONG` |
| 3 | `harness/experience_transfer_harness.py` | `RESET`, `SHAM_MEMORY`, `GENERIC_MEMORY`, `V1_RAKL_MEMORY`, `CURRENT_RAKL_EXPERIENCE`, `GOLD_LESSON_ORACLE` |
| 4 | `harness/trajectory_governance_harness.py` | `DIRECT`, `V1_RAKL_GOVERNED`, `CURRENT_RAKL_TRAJECTORY` |

v1 harness is read-only. Proxies stand in for hosted `exact_verdict` until dev gates pass.

```bash
python research/glm52_mechanism_suite_v1_1/offline_selftest.py
pytest tests/test_glm52_v1_1_wave2_harness.py
```
