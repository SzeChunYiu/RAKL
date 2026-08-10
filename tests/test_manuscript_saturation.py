from __future__ import annotations

from rakl.manuscript_saturation import (
    ManuscriptOpenItem,
    ManuscriptOpenState,
    ManuscriptReviewPass,
    ManuscriptSaturationProtocol,
    ManuscriptSemanticKind,
    ManuscriptSemanticObject,
)

LENSES = frozenset({"epistemology", "geometry", "agents", "repro"})
ROUTES = frozenset({"foundational", "function-first", "freshness", "adversarial"})


def protocol() -> ManuscriptSaturationProtocol:
    p = ManuscriptSaturationProtocol(LENSES, ROUTES, "2026-08-10")
    p.freshness_scan_complete = True
    p.nearest_work_audit_complete = True
    p.proof_obligation_audit_complete = True
    p.section_purpose_audit_complete = True
    return p


def flat(pid: str, lens: str, route: str) -> ManuscriptReviewPass:
    return ManuscriptReviewPass(pid, lens, route, "same-context")


def test_local_saturation_requires_post_growth_coverage_of_all_lenses_and_routes():
    p = protocol()
    obj = ManuscriptSemanticObject(
        "O1", ManuscriptSemanticKind.CLAIM_DISTINCTION, "new boundary"
    )
    p.record_pass(
        ManuscriptReviewPass("g", "epistemology", "foundational", "same", (obj,))
    )
    p.record_pass(flat("e", "epistemology", "foundational"))
    p.record_pass(flat("m", "geometry", "function-first"))
    p.record_pass(flat("a", "agents", "freshness"))
    assert not p.locally_saturated
    p.record_pass(flat("r", "repro", "adversarial"))
    assert p.locally_saturated


def test_new_semantic_growth_resets_flat_tail():
    p = protocol()
    for i, (lens, route) in enumerate(zip(sorted(LENSES), sorted(ROUTES))):
        p.record_pass(flat(f"f{i}", lens, route))
    assert p.locally_saturated
    obj = ManuscriptSemanticObject(
        "O2", ManuscriptSemanticKind.PROOF_OBLIGATION, "new proof"
    )
    p.record_pass(
        ManuscriptReviewPass("growth", "geometry", "adversarial", "same", (obj,))
    )
    assert not p.locally_saturated
    assert not p.post_growth_tail


def test_duplicate_semantic_object_is_flat_after_canonicalization():
    p = protocol()
    obj = ManuscriptSemanticObject(
        "O3", ManuscriptSemanticKind.CITATION_CLUSTER, "prior-art cluster"
    )
    first = p.record_pass(
        ManuscriptReviewPass("p1", "agents", "freshness", "same", (obj,))
    )
    second = p.record_pass(
        ManuscriptReviewPass("p2", "agents", "freshness", "same", (obj,))
    )
    assert not first.flat
    assert second.flat


def test_material_open_blocks_but_deferred_does_not_masquerade_as_missing_history():
    p = protocol()
    for i, (lens, route) in enumerate(zip(sorted(LENSES), sorted(ROUTES))):
        p.record_pass(flat(f"f{i}", lens, route))
    p.set_open_items(
        [
            ManuscriptOpenItem(
                "E1", ManuscriptOpenState.EMPIRICAL_DEFERRED, "matched trial"
            ),
            ManuscriptOpenItem(
                "M1", ManuscriptOpenState.MATERIAL_OPEN, "unresolved formal gap"
            ),
        ]
    )
    assert not p.locally_saturated
    p.set_open_items(
        [
            ManuscriptOpenItem(
                "E1", ManuscriptOpenState.EMPIRICAL_DEFERRED, "matched trial"
            ),
            ManuscriptOpenItem(
                "B1",
                ManuscriptOpenState.BLOCKED_MISSING_EVIDENCE,
                "independent review",
            ),
        ]
    )
    assert p.locally_saturated


def test_exogenous_object_reopens_and_receipt_never_mints_independence():
    p = protocol()
    for i, (lens, route) in enumerate(zip(sorted(LENSES), sorted(ROUTES))):
        p.record_pass(flat(f"f{i}", lens, route))
    assert p.locally_saturated
    obj = ManuscriptSemanticObject(
        "X1", ManuscriptSemanticKind.NOVELTY_BOUNDARY, "remote prior work"
    )
    p.register_exogenous_object(
        obj, reason="external reviewer supplied closer prior art"
    )
    receipt = p.closure_receipt()
    assert not receipt["same_context_local_saturation"]
    assert receipt["independent_saturation"] is False
    assert receipt["independent_peer_review"] is False
