"""Tests for the paper-to-framework consistency checks.

Four bindings are CONSISTENT and one is a genuine, independently verified
DIVERGENT finding on the live tree — which is the strongest evidence that the
checker works, since a checker validated only against fixtures can miss whole
classes of defect.

The rest of these tests inject divergence and assert it is *caught*: a checker
that could only ever return CONSISTENT would satisfy the happy path while being
useless. Acceptance of a known divergence is tested too — it must never soften
the verdict, and an acceptance with no closure action must not silence anything.
"""

from __future__ import annotations

import json

import pytest

from rakl import paper_framework_consistency as pfc
from rakl.paper_framework_consistency import ConsistencyVerdict


def test_no_blocking_divergences_on_the_live_tree():
    """Unaccepted divergences block. Accepted ones are still reported (see below)."""
    results = pfc.run_all()
    assert results, "no bindings evaluated"
    blocking = pfc.blocking_divergences(results)
    assert blocking == (), f"unaccepted divergence: {[(r.binding_id, r.detail) for r in blocking]}"


def test_checker_finds_the_known_real_divergence():
    """Validated against REAL data, not just fixtures: this check must actually fire.

    Both symbols declare themselves a production path while only tests reference
    them. If this ever stops firing it means either the divergence was repaired
    (then drop the acceptance) or the check silently stopped working.
    """
    results = {r.binding_id: r for r in pfc.run_all()}
    result = results["PFC-PRODUCTION-PATH-IS-LIVE"]
    assert result.verdict is ConsistencyVerdict.DIVERGENT
    assert "assured_compile_problem_fibre_with_quotient" in result.detail


def test_acceptance_does_not_soften_the_verdict():
    """Acceptance records a decision; it never turns DIVERGENT into CONSISTENT."""
    results = pfc.run_all()
    accepted = [r for r in pfc.divergences(results)
                if r not in pfc.blocking_divergences(results)]
    assert accepted, "expected at least one accepted divergence"
    for item in accepted:
        assert item.verdict is ConsistencyVerdict.DIVERGENT


def test_acceptance_without_closure_action_still_blocks(tmp_path, monkeypatch):
    """An acceptance that does not say what will be done cannot silence a finding."""
    bindings = {"bindings": [{
        "binding_id": "PFC-BAD-ACCEPT",
        "accepted_divergence": {"status": "OPEN_DIVERGENCE", "closure_action": "   "},
    }]}
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps(bindings), encoding="utf-8")
    monkeypatch.setitem(pfc.CHECKS, "PFC-BAD-ACCEPT",
                        lambda: (ConsistencyVerdict.DIVERGENT, "injected"))
    results = pfc.run_all(path)
    assert len(pfc.blocking_divergences(results, path)) == 1


def test_narrow_production_rule_avoids_false_positives():
    """Only first-line 'Production' declarations count.

    A looser rule matching any mention of the word fires on six further symbols
    that merely discuss production, and a checker that cries wolf on its first
    real run gets switched off.
    """
    symbols = pfc._production_claiming_symbols()
    names = {name for _, name in symbols}
    assert names == {
        "assured_compile_problem_fibre_with_quotient",
        "TypedShortcutResolutionV3",
    }, f"production-claim detection drifted: {sorted(names)}"


def test_outcome_receipt_check_finds_the_real_unbound_receipt():
    """Second real-data finding: an 'all_caught' receipt that nothing re-executes."""
    results = {r.binding_id: r for r in pfc.run_all()}
    result = results["PFC-OUTCOME-RECEIPT-IS-TEST-BOUND"]
    assert result.verdict is ConsistencyVerdict.DIVERGENT
    assert "RAKL_V3_NONINTERFERENCE_INTEGRATION" in result.detail


def test_outcome_receipt_scope_has_a_bound_control():
    """The rule must not flag everything: at least one in-scope receipt IS bound.

    Without a bound control the check could be firing on a repo-wide convention
    rather than on a genuine asymmetry, and would be noise.
    """
    receipts = pfc._outcome_asserting_receipts()
    assert any(bound for _, _, bound in receipts), "no bound control - rule is too broad"
    assert any(not bound for _, _, bound in receipts)


def test_raw_run_artifacts_are_excluded_from_receipt_rule():
    """Regression: the unscoped rule flagged a SLURM job artifact on its first run.

    Per-job outputs carrying slurm_job_id/pytest_exit_code are run records, not
    curated evidence. Nothing cites them and there may be thousands, so demanding
    a binding test for each would make the check useless noise.
    """
    flagged = {rel for rel, _, bound in pfc._outcome_asserting_receipts() if not bound}
    assert not any("native_job_" in rel for rel in flagged), (
        f"raw run artifact leaked into the receipt rule: {flagged}"
    )


def test_synthetic_unbound_outcome_receipt_would_be_caught(tmp_path, monkeypatch):
    """The check must fire on a receipt it has never seen, not just the known one."""
    fake_repo = tmp_path
    (fake_repo / "research").mkdir()
    (fake_repo / "tests").mkdir()
    (fake_repo / "research" / "NEW_RECEIPT.json").write_text(
        json.dumps({"verification": {"all_caught": True}}), encoding="utf-8"
    )
    (fake_repo / "tests" / "test_unrelated.py").write_text("# binds nothing\n", encoding="utf-8")
    monkeypatch.setattr(pfc, "_REPO", fake_repo)

    verdict, detail = pfc._check_outcome_receipts_are_test_bound()
    assert verdict is ConsistencyVerdict.DIVERGENT
    assert "NEW_RECEIPT.json" in detail


def test_bound_outcome_receipt_reports_consistent(tmp_path, monkeypatch):
    """The no-alarm case: a receipt a test references must not be flagged."""
    fake_repo = tmp_path
    (fake_repo / "research").mkdir()
    (fake_repo / "tests").mkdir()
    (fake_repo / "research" / "BOUND_RECEIPT.json").write_text(
        json.dumps({"verification": {"all_caught": True}}), encoding="utf-8"
    )
    (fake_repo / "tests" / "test_binds.py").write_text(
        "load('BOUND_RECEIPT.json')\n", encoding="utf-8"
    )
    monkeypatch.setattr(pfc, "_REPO", fake_repo)

    verdict, _ = pfc._check_outcome_receipts_are_test_bound()
    assert verdict is ConsistencyVerdict.CONSISTENT


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
