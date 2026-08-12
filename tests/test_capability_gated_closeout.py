from pathlib import Path

from rakl.capability_gated_closeout import load_closeout, validate_closeout

REPO = Path(__file__).resolve().parents[1]


def test_capability_gated_closeout_terminals():
    errors = validate_closeout(REPO)
    assert errors == [], errors
    data = load_closeout(REPO)
    assert data["receipts"][350]["terminal_status"] == (
        "BLOCKED_CAPABILITY__CANNOT_EXECUTE_CONFIRMATORY_ALR"
    )
    assert data["receipts"][352]["terminal_status"] == (
        "BLOCKED_CAPABILITY__CANNOT_IDENTIFY_A3_A4"
    )
    assert data["receipts"][398]["terminal_status"] == (
        "TERMINAL_STOP__ORACLE_CAPABILITY_GATE_LEFTOVER"
    )
    assert data["receipts"][367]["terminal_status"] == (
        "BLOCKED_CAPABILITY__CANNOT_BIND_CONFIRMATORY_FOUR_ARM"
    )
    assert data["receipts"][399]["terminal_status"] == (
        "BLOCKED_CAPABILITY__CANNOT_IDENTIFY_RAKL_LEARNING"
    )
    assert data["batch"]["capable_model_score"] == "NO_REFUTED"
    assert data["batch"]["CAPABLE_MODEL_AVAILABLE"] is False
    assert data["batch"]["confirmatory_lunarc_jobs_submitted"] is False
