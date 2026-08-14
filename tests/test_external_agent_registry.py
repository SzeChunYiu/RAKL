"""Tests for the issue #588 external research-agent registry and landscape saturation.

These cover both directions deliberately: the live registry must report an honest OPEN
landscape, *and* a synthetic saturated landscape must be able to reach
BOUNDED_SATURATED.  A checker that can only ever say OPEN would pass the first half
while being useless.
"""

from __future__ import annotations

import collections
import copy
import json

import pytest

from rakl.epistemic_saturation import SaturationStatus
from rakl.external_agent_registry import (
    REGISTRY_PATH,
    ROUNDS_PATH,
    UNKNOWN_SENTINEL,
    RegistryError,
    anchor_integrity_problems,
    architecture_causal_eligible,
    audit_landscape,
    cross_reference_mechanics,
    load_basis,
    load_mechanics,
    load_registry,
)


@pytest.fixture
def registry() -> dict:
    return load_registry()


@pytest.fixture
def rounds_payload() -> dict:
    return json.loads(ROUNDS_PATH.read_text(encoding="utf-8"))


def _write(tmp_path, registry: dict, rounds: dict):
    reg_path = tmp_path / "registry.json"
    rounds_path = tmp_path / "rounds.json"
    reg_path.write_text(json.dumps(registry), encoding="utf-8")
    rounds_path.write_text(json.dumps(rounds), encoding="utf-8")
    return reg_path, rounds_path


def test_live_registry_validates_against_schema(registry):
    assert registry["schema_version"] == "external-research-agent-registry-v1"
    assert registry["systems"] and registry["benchmarks"]


def test_registry_cannot_grant_authority_or_scalar_ranking(registry):
    assert registry["grants_scientific_authority"] is False
    assert registry["grants_promotion_authority"] is False
    assert registry["permits_scalar_ranking"] is False


def test_registry_fingerprint_matches_frozen_basis(registry):
    assert registry["basis_fingerprint"] == load_basis().fingerprint


def test_live_landscape_is_open_and_supports_no_completeness_claim():
    audit = audit_landscape()
    assert audit.status is SaturationStatus.OPEN
    assert audit.supports_completeness_claim is False
    assert audit.audits_performed is False
    assert "insufficient_consecutive_substantive_flat_rounds" in audit.report.reasons


def test_live_landscape_surfaces_weak_evidence_and_flagged_chronology():
    audit = audit_landscape()
    # Most of v1 rests on search snippets; that must be visible, not silently accepted.
    assert audit.weak_evidence_ids
    assert audit.flagged_chronology_anchor_ids


def test_proprietary_systems_are_not_architecture_causal_eligible(registry):
    eligible = set(architecture_causal_eligible(registry))
    for system in registry["systems"]:
        if system["availability"] == "PROPRIETARY":
            assert system["system_id"] not in eligible, (
                f"{system['system_id']} is proprietary but marked architecture-causal eligible"
            )


def test_same_substrate_system_is_system_level_only(registry):
    """ORION runs on Claude Code, so that entry can never be an independent arm."""
    entry = next(s for s in registry["systems"] if s["system_id"] == "SYS-CLAUDE_CODE_AS_RESEARCH_AGENT")
    assert entry["comparator_class"] == "SYSTEM_LEVEL_ONLY"


def test_every_entry_carries_at_least_one_source_anchor(registry):
    for item in (*registry["systems"], *registry["benchmarks"]):
        assert item["source_anchors"], f"{item} has no source anchor"


def test_benchmarks_document_a_distinct_capability(registry):
    """Phase 3 forbids adding a suite without saying what distinct capability it measures."""
    seen = set()
    for benchmark in registry["benchmarks"]:
        text = benchmark["distinct_capability_measured"]
        assert len(text) > 80, f"{benchmark['benchmark_id']} capability rationale is too thin"
        assert text not in seen, "two suites share an identical capability rationale"
        seen.add(text)


def test_fingerprint_mismatch_is_rejected(tmp_path, registry, rounds_payload):
    broken = copy.deepcopy(registry)
    broken["basis_fingerprint"] = "0" * 64
    reg_path, rounds_path = _write(tmp_path, broken, rounds_payload)
    with pytest.raises(RegistryError, match="basis_fingerprint"):
        audit_landscape(reg_path, rounds_path)


def test_optimistic_declared_status_is_rejected(tmp_path, registry, rounds_payload):
    """Hand-editing the registry to claim saturation must fail, not be believed."""
    lying = copy.deepcopy(registry)
    lying["saturation_status"] = "BOUNDED_SATURATED"
    reg_path, rounds_path = _write(tmp_path, lying, rounds_payload)
    with pytest.raises(RegistryError, match="derive"):
        audit_landscape(reg_path, rounds_path)


def _saturated_rounds(rounds_payload: dict, *, audit_performed: bool) -> dict:
    """Two consecutive fully-flat, fully-audited rounds appended to the record."""
    payload = copy.deepcopy(rounds_payload)
    # The two digests must DIFFER: identical digests mean no perturbation was actually
    # applied, so an all-identical audit would only prove the checker accepts a fake one.
    # A genuinely passing audit swaps the operator order, gets a different representation,
    # and finds the substantive difference flat anyway.
    flat = {
        "route_family": "closure probe",
        "audit_performed": audit_performed,
        "operator_order_digest": "d" * 64,
        "operator_order_swapped_digest": "e" * 64,
        "freshness_cutoff": "2026-08-14",
        "growth": {},
        "operator_order_difference": {},
        "bounded_discovery_closed": True,
        "route_coverage_stable": True,
        "omission_audit_passed": True,
        "nearest_work_audit_passed": True,
        "blocking_fibers": [],
    }
    for entry in payload["rounds"]:
        entry["audit_performed"] = audit_performed
        entry["operator_order_digest"] = "d" * 64
        entry["operator_order_swapped_digest"] = "e" * 64
    payload["rounds"] += [
        {**flat, "round_id": "RX-FLAT-1"},
        {**flat, "round_id": "RX-FLAT-2"},
    ]
    return payload


def test_synthetic_saturated_landscape_can_reach_bounded_saturated(tmp_path, registry, rounds_payload):
    """The no-alarm case: the checker must be capable of a positive verdict."""
    saturated = copy.deepcopy(registry)
    saturated["saturation_status"] = "BOUNDED_SATURATED"
    reg_path, rounds_path = _write(tmp_path, saturated, _saturated_rounds(rounds_payload, audit_performed=True))
    audit = audit_landscape(reg_path, rounds_path)
    assert audit.status is SaturationStatus.BOUNDED_SATURATED
    assert audit.supports_completeness_claim is True


def test_flat_rounds_without_performed_audit_still_cannot_saturate(tmp_path, registry, rounds_payload):
    """Defence in depth: flat growth alone must not buy a completeness claim."""
    reg_path, rounds_path = _write(tmp_path, registry, _saturated_rounds(rounds_payload, audit_performed=False))
    audit = audit_landscape(reg_path, rounds_path)
    assert audit.status is SaturationStatus.OPEN
    assert audit.supports_completeness_claim is False


def test_mechanic_cross_references_resolve():
    assert cross_reference_mechanics() == ()


def test_dangling_mechanic_reference_is_detected(registry):
    """The cross-reference check must be able to fail, not just return empty."""
    broken = copy.deepcopy(registry)
    broken["systems"][0]["candidate_mechanic_ids"] = ["MEC-DOES-NOT-EXIST"]
    problems = cross_reference_mechanics(broken, load_mechanics())
    assert any("MEC-DOES-NOT-EXIST" in item for item in problems)


def test_mechanics_claim_no_authority_and_no_independent_evidence_yet():
    mechanics = load_mechanics()
    assert mechanics["grants_scientific_authority"] is False
    assert mechanics["grants_promotion_authority"] is False
    for mechanic in mechanics["mechanics"]:
        # v1 has attempted no reproduction; a mechanic claiming independent evidence
        # here would be an unearned promotion of a competitor's own marketing claim.
        assert mechanic["independent_evidence"].startswith("NONE")
        assert mechanic["candidate_transfer_obligation"].strip()


def test_anchor_integrity_holds():
    assert anchor_integrity_problems() == ()


def test_divergent_anchor_content_is_detected(registry):
    """A reused anchor id carrying different content must be caught, not averaged over.

    Must mutate an anchor that genuinely appears on more than one entry - divergence is
    only definable across copies of the same id.
    """
    broken = copy.deepcopy(registry)
    counts = collections.Counter(
        anchor["anchor_id"]
        for item in (*broken["systems"], *broken["benchmarks"])
        for anchor in item["source_anchors"]
    )
    shared_id = next(aid for aid, n in counts.items() if n > 1)

    mutated = False
    for item in (*broken["systems"], *broken["benchmarks"]):
        for anchor in item["source_anchors"]:
            if anchor["anchor_id"] == shared_id and not mutated:
                anchor["retrieved_on"] = "2020-01-01"
                mutated = True
    assert mutated

    problems = anchor_integrity_problems(broken)
    assert any("divergent content" in item for item in problems)


def test_result_citing_undefined_anchor_is_detected(registry):
    broken = copy.deepcopy(registry)
    broken["systems"][0]["reported_results"][0]["anchor_ids"] = ["A-NOT-DEFINED"]
    problems = anchor_integrity_problems(broken)
    assert any("A-NOT-DEFINED" in item for item in problems)


def test_flagged_chronology_anchors_are_deduplicated():
    """Anchor ids are shared across entries; one flagged paper is one problem."""
    flagged = audit_landscape().flagged_chronology_anchor_ids
    assert len(flagged) == len(set(flagged))


def _field_value_strings(registry: dict):
    for system in registry["systems"]:
        yield from system["version_freeze"].values()
        yield from system["architecture"].values()
    for benchmark in registry["benchmarks"]:
        for key in ("task_count", "domains", "evaluation_protocol", "reported_ceiling"):
            if key in benchmark:
                yield benchmark[key]


def test_unknown_sentinel_vocabulary_is_exact(registry):
    """Only CANNOT_CHECK may mean 'not known'.

    The schema cannot express this (any non-empty string validates), so it is asserted
    here: a stray 'unknown' or 'TBD' would read as content and slip past the evidence audit.
    """
    lookalikes = {"unknown", "tbd", "n/a", "na", "?", "cannot check", "cannot_check", "none", "-", ""}
    for value in _field_value_strings(registry):
        assert value.strip().lower() not in lookalikes or value == UNKNOWN_SENTINEL, (
            f"{value!r} is a non-canonical unknown marker; use {UNKNOWN_SENTINEL}"
        )


def test_open_residuals_are_recorded(rounds_payload):
    residual_ids = {item["residual_id"] for item in rounds_payload["open_residuals"]}
    assert {"RES-EXT-001", "RES-EXT-002", "RES-EXT-003"} <= residual_ids
    for item in rounds_payload["open_residuals"]:
        assert item["closure_action"].strip()
