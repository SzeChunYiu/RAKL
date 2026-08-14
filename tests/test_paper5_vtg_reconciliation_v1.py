"""Consistency tests for P5-VTG-RECONCILIATION-V1.

The load-bearing test is `test_every_manuscript_terminal_is_registered_or_declared_a_defect`,
which is a LIVE check against the repository rather than a frozen assertion: it stays
true both before and after `P5-VTG-D1` is repaired, and fails if a new unregistered
outcome branch is introduced into the manuscript.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "research" / "paper5_vtg_reconciliation_v1"
RECON = PACKET / "RECONCILIATION_V1.json"

MANUSCRIPT = (
    ROOT
    / "publication"
    / "papers"
    / "paper-05-verified-discovery-in-mathematics"
    / "sections"
    / "11_verified_transformation_geometry.tex"
)
PREREG = ROOT / "research" / "deep_hardening_v1" / "VTG_PHASE0_1_PREREGISTRATION.md"
MECHANIC_PACKET = (
    ROOT / "research" / "p5_p6_saturation_v1" / "packets" / "vtg_lean_geometry_v2.json"
)

# An outcome terminal in this lane is an ALL_CAPS token mentioning geometry,
# navigability or a navigation quotient.
TERMINAL_RE = re.compile(r"\b[A-Z][A-Z0-9_]{15,}\b")
TERMINAL_HINT = ("GEOMETRY", "NAVIGABILITY", "NAVIGATION", "NAVIGABLE")


def _recon() -> dict:
    return json.loads(RECON.read_text())


def _terminals_in(text: str) -> set[str]:
    return {
        tok
        for tok in TERMINAL_RE.findall(text)
        if any(hint in tok for hint in TERMINAL_HINT)
    }


def test_referenced_artifacts_all_exist() -> None:
    for path in (MANUSCRIPT, PREREG, MECHANIC_PACKET):
        assert path.exists(), f"reconciliation references a missing artifact: {path}"


def test_packet_creates_no_freeze_and_grants_no_authority() -> None:
    doc = _recon()
    assert doc["creates_new_freeze"] is False
    assert doc["grants_scientific_authority"] is False
    assert doc["grants_promotion_authority"] is False


def test_every_manuscript_terminal_is_registered_or_declared_a_defect() -> None:
    """Live consistency check; survives repair of P5-VTG-D1."""
    registered = _terminals_in(PREREG.read_text())
    assert registered, "preregistration terminal list could not be parsed"

    declared_defective = " ".join(
        d["statement"] for d in _recon()["defects_found"]
    )

    for terminal in _terminals_in(MANUSCRIPT.read_text()):
        assert terminal in registered or terminal in declared_defective, (
            f"manuscript names outcome branch {terminal!r} that is neither registered "
            f"in the preregistration nor declared as an open defect"
        )


def test_d1_absence_claim_scope_is_recorded() -> None:
    """An absence claim needs a justified search scope, not just a null result."""
    d1 = next(d for d in _recon()["defects_found"] if d["defect_id"] == "P5-VTG-D1")
    assert "grep" in d1["search_scope_justifying_the_absence_claim"]
    assert d1["state"] == "OPEN"


def test_substrate_block_is_cannot_check_with_prerequisites() -> None:
    d2 = next(d for d in _recon()["defects_found"] if d["defect_id"] == "P5-VTG-D2")
    assert d2["verdict"] == "CANNOT_CHECK"
    assert d2["state"] == "BLOCKED"
    assert len(d2["prerequisites_to_unblock"]) >= 3
    assert "explicitly_not_done" in d2


def test_ordering_claim_carries_a_non_overlap_witness() -> None:
    rel = _recon()["relation"]
    assert rel["ordering"] == "A2 is UPSTREAM of A3."
    witness = rel["non_overlap_witness"]
    for key in ("solver_class", "qoi", "benchmark_universe", "cost_equation"):
        assert witness[key], f"non-overlap witness missing {key}"


def test_mechanic_packet_hash_matches_the_live_artifact() -> None:
    """The A3 identity recorded here must still be the packet on disk."""
    recorded = next(a for a in _recon()["artifacts"] if a["ref"] == "A3")
    live = json.loads(MECHANIC_PACKET.read_text())
    assert live["packet_id"] == recorded["packet_id"]
    assert live["packet_content_sha256"] == recorded["packet_content_sha256"]
    assert live["applicability_gate_state"] == recorded["applicability_gate_state"]


def test_prereg_still_forbids_an_llm_solver() -> None:
    """The A2-vs-A3 non-overlap witness depends on this; verify it live."""
    assert "No LLM solving in Phase 0" in PREREG.read_text()
