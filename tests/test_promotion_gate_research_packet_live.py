from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from promotion_gate import CANDIDATES, verdict_for  # noqa: E402


EXPECTED_VERDICTS = {
    "fieldability_given_field": "PROMOTE_TO_MECHANIC",
    "field_construction": "KEEP_PROPOSAL_ONLY",
    "field_construction_successor": "KEEP_PROPOSAL_ONLY",
    "navigation_dynamics": "KEEP_PROPOSAL_ONLY",
    "navigation_dynamics_successor": "KEEP_PROPOSAL_ONLY",
    "navigation_dynamics_parallel": "PROMOTE_CONDITIONALLY",
    "path_equivalence_quotient": "PROMOTE_CONDITIONALLY",
    "mechanic_diagnosis": "KEEP_PROPOSAL_ONLY",
    "diagnosis_active_successor": "KEEP_PROPOSAL_ONLY",
    "tcsq_sq3": "KEEP_PROPOSAL_ONLY",
    "tcsq_sq3_successor": "PROMOTE_CONDITIONALLY",
    "identity_reuse": "PROMOTE_TO_MECHANIC",
    "six_family_law": "PROMOTE_TO_MECHANIC",
}


def test_p3_does_not_change_any_historical_candidate_verdict() -> None:
    observed = {name: verdict_for(name, spec)["verdict"] for name, spec in CANDIDATES.items()}
    assert observed == EXPECTED_VERDICTS


def test_every_historical_candidate_is_explicitly_tagged_not_retroactively_preregistered() -> None:
    for name, spec in CANDIDATES.items():
        row = verdict_for(name, spec)
        assert row["research_packet"]["status"] == "LEGACY_PRE_PACKET", name
        assert row["research_packet"]["gate_required"] is False, name
