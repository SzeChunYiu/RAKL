# Scientific-transition ALR — model baseline preregistration v1

Status: `PREREG_FROZEN / MODEL_RUN_AUTHORIZED_NON_CONFIRMATORY / NO_AUTHORITY_CLAIM`
Issue: #154
Machine-readable: `research/paper2_alr_model_baselines_v1/BASELINE_PREREGISTRATION.json`
Runner: `src/rakl/alr_model_baselines.py`

Freezes baseline arms, power/MDE, and fail-closed execution against V2 before
model outcomes. First authorized LUNARC arm: `BASE_DIRECT_STRONG_PROMPT` on
staged Qwen2.5-0.5B-Instruct plus deterministic controls.

Scores are **non-confirmatory**. `#247` capability clearance is still required
before confirmatory claims. `grants_authority` remains false.
