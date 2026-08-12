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
    assert data["batch"]["non_confirmatory_cited"]["3476748"].startswith("MODEL_SCORED_NON_CONFIRMATORY")
    assert "upgrade-recall=0" in data["batch"]["non_confirmatory_cited"]["3476749"]
