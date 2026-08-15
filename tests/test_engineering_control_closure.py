import pytest

from rakl.engineering_closure import (
    ENGINEERING_FIBERS,
    EngineeringFiberAssessment,
    EngineeringFiberLevel,
    EngineeringResearchRound,
    assess_engineering_closure,
    assess_engineering_research_saturation,
)
from rakl.engineering_control_store import (
    ControlArtifactKind,
    ControlArtifactProjection,
    SqliteControlProjectionStore,
)
from rakl.engineering_store import EngineeringIntegrityError


def test_control_projection_is_snapshot_unique_and_authority_neutral(tmp_path):
    store = SqliteControlProjectionStore(tmp_path / "control.sqlite3")
    first = ControlArtifactProjection(
        project_snapshot_id="snapshot:" + "a" * 64,
        kind=ControlArtifactKind.SATURATION_CERTIFICATE,
        source_object_id="sat:1",
        canonical_payload={"bounded_saturated": True},
        source_receipt_ids=("metric:1",),
    )
    assert store.record(first) == first
    assert store.record(first) == first
    assert not first.grants_scientific_authority
    with pytest.raises(EngineeringIntegrityError, match="recomputed"):
        store.record(
            ControlArtifactProjection(
                project_snapshot_id=first.project_snapshot_id,
                kind=first.kind,
                source_object_id=first.source_object_id,
                canonical_payload={"bounded_saturated": False},
            )
        )
    assert store.control_revision(first.project_snapshot_id).startswith("control-revision:")


def test_reference_saturation_does_not_imply_production_ready():
    assessments = tuple(
        EngineeringFiberAssessment(
            fiber,
            EngineeringFiberLevel.REFERENCE_IMPLEMENTED,
            (f"test:{fiber}",),
        )
        for fiber in ENGINEERING_FIBERS
    )
    report = assess_engineering_closure(assessments)
    assert report.reference_saturated
    assert not report.production_ready_scoped


def test_production_ready_requires_assured_or_absorbed_everywhere():
    assessments = tuple(
        EngineeringFiberAssessment(
            fiber,
            EngineeringFiberLevel.ASSURED,
            (f"assurance:{fiber}",),
        )
        for fiber in ENGINEERING_FIBERS
    )
    report = assess_engineering_closure(assessments)
    assert report.reference_saturated
    assert report.production_ready_scoped


def test_engineering_research_saturation_requires_flat_independent_routes():
    rounds = (
        EngineeringResearchRound("r1", "REPO_AUDIT", True, ()),
        EngineeringResearchRound("r2", "EXTERNAL_PARENTS", True, ()),
        EngineeringResearchRound("r3", "HOSTILE_TEST", True, ()),
    )
    report = assess_engineering_research_saturation(
        rounds,
        required_route_families=("REPO_AUDIT", "EXTERNAL_PARENTS", "HOSTILE_TEST"),
        min_independent_flat_routes=3,
        window=3,
    )
    assert report.bounded_saturated
    assert not report.grants_absolute_completeness


def test_integrated_control_projection_requires_real_snapshot(tmp_path):
    from rakl.engineering_state import ProjectSnapshot
    from rakl.engineering_store import SqliteEngineeringStateStore
    path = tmp_path / "integrated.sqlite3"
    state = SqliteEngineeringStateStore(path)
    state.initialize_project(ProjectSnapshot(
        project_id="p", sequence=0, previous_snapshot_id=None,
        evidence_cutoff="e", semantic_state_revision="s", metric_ledger_head="m",
        episode_store_head="ep", saturation_basis_ids=("b",),
        authority_projection_revision="a", controller_epoch_id="epoch",
        created_at_utc="2026-08-15T15:00:00+00:00",
    ))
    controls = SqliteControlProjectionStore(path)
    with pytest.raises(EngineeringIntegrityError, match="unknown project snapshot"):
        controls.record(ControlArtifactProjection(
            project_snapshot_id="snapshot:" + "f" * 64,
            kind=ControlArtifactKind.HARD_GATE,
            source_object_id="gate:ghost",
            canonical_payload={"status":"PASS"},
        ))
