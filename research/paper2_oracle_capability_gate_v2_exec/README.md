# ORACLE capability-gate v2.0 EXEC — sealed tasks + executable freeze (#379)

**Protocol version:** `ORACLE_CAPABILITY_GATE_V2_0_EXEC`  
**Packet:** `paper2-oracle-capability-gate-v2-exec`  
**Status:** `PROTOCOL_FROZEN_AWAITING_EXECUTION`  
**protocol_subject_hash:** `e20eeadcc7d8b431095db8cfadbd9f9e73841f4fea29ece81302348c2dd542d1`  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED`  
**First authorized ORACLE:** `Qwen2.5-7B-Instruct` (ceiling revisit; not 14B/32B)

Successor to protocol-only `ORACLE_CAPABILITY_GATE_V2_0` (`7b186eae…`).  
Sealed transfer set **T1–T5** preserves REPEATED_FAMILY / CROSS_DOMAIN_TRANSFER / HOSTILE_NEAR_MISS and adds CONTEXT_ALIGNMENT + MISSING_EVIDENCE.  
Evaluator thresholds unchanged (`EXPERIENCE_V1_EXACT_STRUCTURED_MATCH`, success ≥2/3 exact).

## Submit

```bash
experiments/paper2/lunarc/submit_oracle_capability_gate_v2_exec_oracle.sh <exact-origin-main-sha>
```

## Forbidden

- 14B/32B ORACLE
- Phase-0 / confirmatory learning jobs while NO_REFUTED
- Softening evaluator thresholds
- Treating failed episodes as Lessons
- Inventing a CAPABLE_MODEL pass
