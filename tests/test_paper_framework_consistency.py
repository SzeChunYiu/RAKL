"""Tests for the paper-to-framework consistency checks.

The live bindings all pass, which is necessary but proves nothing on its own. The
bulk of these tests inject divergence and assert it is *caught* — a checker that
can only return CONSISTENT would satisfy the happy path while being useless.
"""

from __future__ import annotations

import json

import pytest

from rakl import paper_framework_consistency as pfc
from rakl.paper_framework_consistency import ConsistencyVerdict


def test_live_bindings_are_all_consistent():
    results = pfc.run_all()
    assert results, "no bindings evaluated"
    assert pfc.divergences(results) == ()


def test_no_binding_is_silently_unchecked():
    """CANNOT_CHECK is a distinct outcome and must not be present on a healthy tree."""
    results = pfc.run_all()
    unchecked = [r for r in results if r.verdict is ConsistencyVerdict.CANNOT_CHECK]
    assert unchecked == [], f"bindings could not be evaluated: {[r.binding_id for r in unchecked]}"


def test_every_declared_binding_has_an_executable_check():
    declared = {b["binding_id"] for b in pfc.load_bindings()["bindings"]}
    assert declared <= set(pfc.CHECKS), f"unimplemented: {declared - set(pfc.CHECKS)}"


# --- the checker must be able to fail ----------------------------------------------


def test_schema_pin_detects_missing_pointer():
    ok, detail = pfc._schema_pins_const(
        "schemas/epistemic-saturation.schema.json", ["properties", "no_such_field"], False
    )
    assert not ok and "absent" in detail


def test_schema_pin_detects_wrong_constant():
    ok, detail = pfc._schema_pins_const(
        "schemas/epistemic-saturation.schema.json", ["properties", "absolute_complete"], True
    )
    assert not ok and "expected" in detail


def test_schema_pin_detects_unpinned_field():
    """A field that merely exists is not a pin; only an explicit const counts."""
    ok, detail = pfc._schema_pins_const(
        "schemas/epistemic-saturation.schema.json", ["properties", "status"], False
    )
    assert not ok and "not pinned to a const" in detail


def test_schema_pin_detects_missing_schema_file():
    ok, detail = pfc._schema_pins_const("schemas/does-not-exist.json", ["a"], False)
    assert not ok and "not found" in detail


def test_proprietary_causal_eligibility_divergence_is_caught(monkeypatch):
    """Inject a proprietary system into the causal-eligible set; must go DIVERGENT."""
    from rakl import external_agent_registry as ear

    poisoned = json.loads(pfc._REPO.joinpath(
        "research/external_research_agents/registry.json").read_text(encoding="utf-8"))
    for system in poisoned["systems"]:
        if system["availability"] == "PROPRIETARY":
            system["comparator_class"] = "ARCHITECTURE_CAUSAL_ELIGIBLE"
            break
    else:  # pragma: no cover - registry always has a proprietary entry today
        pytest.skip("registry has no proprietary system to poison")

    monkeypatch.setattr(ear, "load_registry", lambda *a, **k: poisoned)
    monkeypatch.setattr(pfc, "_REPO", pfc._REPO)  # keep path resolution intact

    verdict, detail = pfc._check_proprietary_never_architecture_causal()
    assert verdict is ConsistencyVerdict.DIVERGENT
    assert "architecture-causal eligible" in detail


def test_scalar_ranking_divergence_is_caught(monkeypatch):
    """If an aggregate-score field appears on the audit surface, catch it."""
    from rakl import external_agent_registry as ear

    fields = dict(ear.LandscapeAudit.__dataclass_fields__)
    fields["orion_score"] = object()
    monkeypatch.setattr(ear.LandscapeAudit, "__dataclass_fields__", fields)

    verdict, detail = pfc._check_no_scalar_ranking_of_external_agents()
    assert verdict is ConsistencyVerdict.DIVERGENT
    assert "orion_score" in detail


def test_unregistered_binding_reports_cannot_check(tmp_path):
    payload = {"bindings": [{"binding_id": "PFC-NOT-IMPLEMENTED"}]}
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    results = pfc.run_all(path)
    assert len(results) == 1
    assert results[0].verdict is ConsistencyVerdict.CANNOT_CHECK


def test_crashing_check_is_cannot_check_not_consistent(monkeypatch, tmp_path):
    """A check that raises must never be mistaken for a passing check."""
    def boom() -> tuple[ConsistencyVerdict, str]:
        raise RuntimeError("probe exploded")

    monkeypatch.setitem(pfc.CHECKS, "PFC-BOOM", boom)
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps({"bindings": [{"binding_id": "PFC-BOOM"}]}), encoding="utf-8")

    results = pfc.run_all(path)
    assert results[0].verdict is ConsistencyVerdict.CANNOT_CHECK
    assert "probe exploded" in results[0].detail
    assert pfc.divergences(results) == ()


def test_bindings_declare_no_authority():
    assert pfc.load_bindings()["grants_scientific_authority"] is False


def test_bindings_record_open_residuals():
    residuals = pfc.load_bindings()["open_residuals"]
    assert residuals
    for item in residuals:
        assert item["closure_action"].strip()
