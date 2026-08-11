# Paper-2 pendulum microtrial V4.4 (executable)

Status: **FROZEN_READY_NOT_EXECUTED** until a post-merge batch head binding.

## Difference vs V4.3.1

Leak repair only (`rakl_context_prompt_type_b_answer_key_leak_repair`). Gate, model
(Qwen2.5-1.5B-Instruct), seed 17, flat-shape interface, and V4.3.1 normalizer are
unchanged.

## Preconditions satisfied

1. Type B probe CLEAN on the bound arm pair.
2. Offline positive-control sensitivity PASS (`POSITIVE_CONTROL_SENSITIVITY_RECEIPT.json`).

## Claim boundary

- No RAKL-vs-DIRECT reclaim from sealed leaked v4_2 / v4_3_1 fields.
- No #247 capability-floor clearance from this packet freeze or a single microtrial.
