"""Contract tests for the V2 twin-pair panel (issue #154).

V2's defence against surface shortcuts is structural: twins hold a feature
constant while the label moves, so no shared feature *can* predict the label.
These tests assert the structure holds, rather than trusting that an audit
happened to come back clean.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rakl.authority_leakage_audit import AuditStatus, audit_panel
from rakl.authority_leakage_benchmark import (
    CaseStratum,
    LABEL_FIELD_NAMES,
    LeakageSubtype,
    TransitionDecision,
    build_proposal_context,
    panel_to_json,
)
from rakl.authority_leakage_panel_v2 import (
    LABEL_FIELD_NAMES_V2,
    PANEL_V2_ID,
    TWIN_PAIRS,
    build_freeze_receipt_v2,
    frozen_case_panel_v2,
    rotate_candidates,
    twin_pairs,
)

PANEL = frozen_case_panel_v2()
PAIRS = twin_pairs()


def test_panel_is_twice_the_twin_pair_count() -> None:
    assert len(PANEL) == 2 * TWIN_PAIRS == 16
    assert len(PAIRS) == TWIN_PAIRS


def test_case_ids_are_unique_and_opaque() -> None:
    ids = [case.case_id for case in PANEL]
    assert len(set(ids)) == len(ids)
    for case_id in ids:
        assert case_id.startswith("STA-V2-")


@pytest.mark.parametrize("pair_index", range(TWIN_PAIRS))
def test_twins_hold_setup_constant_while_the_label_moves(pair_index: int) -> None:
    """The minimal-twin property, asserted pair by pair.

    Shared setup means a responder cannot separate the twins on those fields;
    a differing label means it must separate them on the observation.
    """

    a, b = PAIRS[pair_index]
    assert a.visible.pre_state == b.visible.pre_state
    assert a.visible.claim_types == b.visible.claim_types
    assert a.visible.context_regime == b.visible.context_regime
    assert a.visible.registered_claims == b.visible.registered_claims
    assert len(a.visible.candidate_interpretations) == len(b.visible.candidate_interpretations)

    assert a.visible.new_observation != b.visible.new_observation
    moved = (
        a.labels.allowed_authority_effects != b.labels.allowed_authority_effects
        or a.labels.required_terminal_status != b.labels.required_terminal_status
    )
    assert moved, f"{a.case_id}/{b.case_id} are twins with the same licensed update"


def test_every_b_twin_licenses_at_least_as_much_as_its_a_twin() -> None:
    """B is the case where the withheld upgrade becomes licensed."""

    for a, b in PAIRS:
        assert b.labels.allowed_authority_effects >= a.labels.allowed_authority_effects, (
            f"{b.case_id} licenses less than {a.case_id}"
        )


def test_panel_can_detect_over_conservatism() -> None:
    """The V1 defect this panel exists to fix.

    V1 licensed an upgrade in 2 of 8 cases with 3 allowed axes in total, so a
    responder that refused everything was nearly indistinguishable from a
    disciplined one.
    """

    licensing = [c for c in PANEL if c.labels.allowed_authority_effects]
    total_axes = sum(len(c.labels.allowed_authority_effects) for c in PANEL)
    assert len(licensing) >= len(PANEL) * 0.35
    assert total_axes >= len(PANEL) * 0.5


def test_at_least_six_leakage_subtypes_are_represented() -> None:
    subtypes = {
        subtype
        for case in PANEL
        for subtype in case.labels.disallowed_authority_effects.values()
    }
    assert len(subtypes) >= 6, sorted(s.value for s in subtypes)


def test_required_strata_are_present() -> None:
    strata = {case.stratum for case in PANEL}
    for required in (
        CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        CaseStratum.HOSTILE_NEAR_MISS,
        CaseStratum.EXPERIENCE_TRAP,
        CaseStratum.PROVENANCE_TRAP,
        CaseStratum.MULTI_STEP_HISTORY,
    ):
        assert required in strata


def test_both_refusal_and_upgrade_terminal_states_occur() -> None:
    statuses = {case.labels.required_terminal_status for case in PANEL}
    assert TransitionDecision.SUPPORTED in statuses
    assert TransitionDecision.REFUTED in statuses
    assert TransitionDecision.PARTIALLY_IDENTIFIED in statuses
    assert TransitionDecision.CANNOT_CHECK in statuses
    assert TransitionDecision.BLOCKED in statuses


# --------------------------------------------------------------------------
# candidate ordering
# --------------------------------------------------------------------------


def test_every_case_labels_its_correct_candidate() -> None:
    for case in PANEL:
        index = case.labels.correct_interpretation_index  # type: ignore[attr-defined]
        assert index is not None
        assert 0 <= index < len(case.visible.candidate_interpretations)


def test_rotation_is_deterministic_and_preserves_the_correct_reading() -> None:
    canonical = ("escalating", "conservative", "correct")
    first, index_a = rotate_candidates("STA-V2-001A", canonical)
    second, index_b = rotate_candidates("STA-V2-001A", canonical)
    assert first == second and index_a == index_b
    assert first[index_a] == "correct"


def test_no_single_candidate_position_dominates() -> None:
    indices = [c.labels.correct_interpretation_index for c in PANEL]  # type: ignore[attr-defined]
    for position in set(indices):
        assert indices.count(position) / len(PANEL) <= 0.75


# --------------------------------------------------------------------------
# label containment
# --------------------------------------------------------------------------


def test_hidden_labels_are_unreachable_from_the_proposal_context() -> None:
    for case in PANEL:
        context = build_proposal_context(case.visible)
        for name in LABEL_FIELD_NAMES_V2:
            assert name not in context
            assert not hasattr(case.visible, name)


def test_serialized_visible_panel_leaks_no_label_vocabulary() -> None:
    rendered = panel_to_json(PANEL)
    for name in LABEL_FIELD_NAMES_V2:
        assert name not in rendered
    for decision in TransitionDecision:
        assert decision.value not in rendered
    for subtype in LeakageSubtype:
        assert subtype.value not in rendered


def test_v2_label_field_names_extend_v1() -> None:
    assert set(LABEL_FIELD_NAMES) < set(LABEL_FIELD_NAMES_V2)
    assert "correct_interpretation_index" in LABEL_FIELD_NAMES_V2


# --------------------------------------------------------------------------
# the audit
# --------------------------------------------------------------------------


def test_panel_passes_every_degeneracy_check() -> None:
    report = audit_panel(PANEL, PANEL_V2_ID)
    assert report.status is AuditStatus.CLEAN, [
        (c.check_id, c.status.value, c.message) for c in report.checks
    ]


# --------------------------------------------------------------------------
# freeze binding
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = REPO_ROOT / "benchmarks" / "scientific_transition_authority"
PROTOCOL_V2_PATH = BENCH_DIR / "PROTOCOL_V2.md"
RECEIPT_V2_PATH = BENCH_DIR / "FREEZE_RECEIPT_V2.json"
AUDIT_ARTIFACT_PATH = REPO_ROOT / "research" / "AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json"


def test_protocol_and_receipt_are_committed() -> None:
    assert PROTOCOL_V2_PATH.is_file()
    assert RECEIPT_V2_PATH.is_file()
    assert AUDIT_ARTIFACT_PATH.is_file()


def test_committed_receipt_matches_live_builder() -> None:
    """Any drift in protocol, panel, auditor or scorer breaks this."""

    committed = json.loads(RECEIPT_V2_PATH.read_text(encoding="utf-8"))
    live = build_freeze_receipt_v2()
    assert committed == live


def test_receipt_records_the_v2_repair() -> None:
    receipt = json.loads(RECEIPT_V2_PATH.read_text(encoding="utf-8"))
    assert receipt["degeneracy_audit_status"] == "CLEAN"
    assert receipt["v1_preserved_verbatim"] is True
    assert receipt["grants_authority"] is False
    assert receipt["leakage_subtype_count"] >= 6


def test_v1_freeze_receipt_is_still_valid() -> None:
    """V2 must not have invalidated V1's freeze.

    V1's receipt hash-binds the scorer source, so this fails if
    ``authority_leakage_benchmark.py`` was edited to make room for V2.
    """

    v1_receipt = json.loads((BENCH_DIR / "FREEZE_RECEIPT_V1.json").read_text(encoding="utf-8"))
    scorer = REPO_ROOT / "src" / "rakl" / "authority_leakage_benchmark.py"
    live_sha = hashlib.sha256(scorer.read_bytes()).hexdigest()
    assert v1_receipt["scorer_source_sha256"] == live_sha


def test_audit_artifact_reports_v1_degenerate_and_v2_clean() -> None:
    artifact = json.loads(AUDIT_ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert artifact["summary"]["v1_status"] == "DEGENERATE"
    assert artifact["summary"]["v2_status"] == "CLEAN"
    assert artifact["grants_scientific_authority"] is False
    # Negative history is preserved verbatim, not summarised away.
    assert len(artifact["negative_history"]["v1_defects_found"]) >= 3
    assert len(artifact["negative_history"]["auditor_self_corrections"]) >= 4
