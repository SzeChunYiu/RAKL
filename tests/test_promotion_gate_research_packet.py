"""#546/#570/#573: a future mechanic cannot promote without preregistration.

Historical candidates are explicitly grandfathered by exact id; this preserves
negative/positive history without falsely calling it preregistered. Any new id
must bind a valid frozen MechanicResearchPacket before a positive or conditional
promotion survives the ordinary evidence/telemetry gate.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from rakl.mechanic_research_packet_io import load_packet_set  # noqa: E402
from promotion_gate import (  # noqa: E402
    CANDIDATES,
    PACKET_SET_PATH,
    PRE_PACKET_LEGACY_CANDIDATES,
    candidate_registration_problems,
    verdict_for,
)


@pytest.fixture
def repo_tmp():
    directory = Path(tempfile.mkdtemp(prefix="packetgate_", dir=str(ROOT)))
    yield directory
    shutil.rmtree(str(directory), ignore_errors=True)


def _positive_spec(repo_tmp: Path, *, variant_id: str | None) -> dict:
    artifact = repo_tmp / "positive.json"
    artifact.write_text(json.dumps({
        "grants_scientific_authority": False,
        "net_advantage": {"mean": 3.0, "lo": 1.0, "hi": 5.0},
    }))
    spec = {
        "artifact": artifact,
        "net_keys": ["net_advantage"],
        "cost_charged": True,
        "note": "synthetic positive used only to test the preregistration boundary",
    }
    if variant_id is not None:
        spec["research_packet_variant_id"] = variant_id
    return spec


def test_exact_live_candidate_set_is_the_frozen_pre_packet_legacy_set() -> None:
    # This equality is intentionally pinned at the P3 cutoff. Adding a candidate
    # can no longer be hidden by omission: it becomes post-contract and must bind
    # a packet unless a reviewer explicitly rewrites this historical cutoff.
    assert set(CANDIDATES) == set(PRE_PACKET_LEGACY_CANDIDATES)
    assert candidate_registration_problems() == ()


def test_legacy_candidate_keeps_historical_verdict_without_retroactive_packet() -> None:
    row = verdict_for("path_equivalence_quotient", CANDIDATES["path_equivalence_quotient"])
    assert row["verdict"] == "PROMOTE_CONDITIONALLY"
    assert row["research_packet"]["status"] == "LEGACY_PRE_PACKET"
    assert row["research_packet"]["gate_required"] is False


def test_future_positive_without_packet_is_downgraded_to_proposal_only(repo_tmp) -> None:
    spec = _positive_spec(repo_tmp, variant_id=None)
    row = verdict_for("future_candidate", spec)
    assert row["pre_research_packet_verdict"] == "PROMOTE_TO_MECHANIC"
    assert row["verdict"] == "KEEP_PROPOSAL_ONLY"
    assert row["reason"] == "research_packet_missing_or_invalid"
    assert row["research_packet"]["status"] == "MISSING"
    assert row["research_packet"]["eligible"] is False


def test_future_positive_with_unknown_packet_id_is_downgraded(repo_tmp) -> None:
    spec = _positive_spec(repo_tmp, variant_id="does-not-exist")
    row = verdict_for("future_candidate", spec)
    assert row["verdict"] == "KEEP_PROPOSAL_ONLY"
    assert row["research_packet"]["status"] == "MISSING"
    assert "research_packet_not_found" in row["research_packet"]["reasons"]


def test_future_positive_with_valid_frozen_packet_survives_packet_gate(repo_tmp) -> None:
    packet_set = load_packet_set(PACKET_SET_PATH)
    spec = _positive_spec(repo_tmp, variant_id="vtg_lean_geometry_v1")
    row = verdict_for("future_candidate", spec, packet_set=packet_set)
    assert row["verdict"] == "PROMOTE_TO_MECHANIC", row
    assert row["research_packet"]["status"] == "VALID"
    assert row["research_packet"]["eligible"] is True
    assert row["research_packet"]["packet_content_sha256"]


def test_registration_preflight_blocks_new_candidate_without_packet(repo_tmp) -> None:
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _positive_spec(repo_tmp, variant_id=None)
    problems = candidate_registration_problems(candidates=synthetic)
    assert problems == ("future_candidate:research_packet_variant_id_missing",)


def test_registration_preflight_accepts_new_candidate_with_valid_packet(repo_tmp) -> None:
    packet_set = load_packet_set(PACKET_SET_PATH)
    synthetic = copy.deepcopy(CANDIDATES)
    synthetic["future_candidate"] = _positive_spec(repo_tmp, variant_id="vtg_lean_geometry_v1")
    assert candidate_registration_problems(candidates=synthetic, packet_set=packet_set) == ()


def test_relabeling_historical_candidate_to_new_id_does_not_inherit_legacy_exemption(repo_tmp) -> None:
    spec = _positive_spec(repo_tmp, variant_id=None)
    row = verdict_for("path_equivalence_quotient_v2", spec)
    assert row["verdict"] == "KEEP_PROPOSAL_ONLY"
    assert row["research_packet"]["gate_required"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
