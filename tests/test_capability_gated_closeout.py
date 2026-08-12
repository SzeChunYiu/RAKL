from pathlib import Path

from rakl.capability_gated_closeout import load_closeout, validate_closeout

REPO = Path(__file__).resolve().parents[1]


def test_capability_gated_closeout_terminals():
    errors = validate_closeout(REPO)
    assert errors == [], errors
    data = load_closeout(REPO)
    assert data["receipts"][350]["terminal_status"] == "BLOCKED_CAPABLE_MODEL"
    assert data["receipts"][352]["terminal_status"] == "CANNOT_IDENTIFY"
    assert data["receipts"][398]["terminal_status"] == "BLOCKED_CAPABLE_MODEL"
    assert data["receipts"][367]["terminal_status"] == "BLOCKED_CAPABLE_MODEL"
    assert data["receipts"][399]["terminal_status"].startswith("BLOCKED_CAPABILITY")
    assert data["batch"]["capable_model_score"] == "NO_REFUTED"
    assert data["batch"]["CAPABLE_MODEL_AVAILABLE"] is False
    assert data["batch"]["confirmatory_lunarc_jobs_submitted"] is False
    cited = data["batch"].get("non_confirmatory_cited") or {}
    if cited:
        assert "3476748" in cited
        assert "3476749" in cited
