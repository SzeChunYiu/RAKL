import pytest

from rakl.core import KnowledgeFiber, Projection
from rakl.experience_substrate import SubstrateKind
from rakl.v3_metrology import compare_state_metrics, measure_state
from rakl.v3_runtime import RAKLV3State


def _legacy_fiber() -> KnowledgeFiber:
    fiber = KnowledgeFiber(
        fiber_id="legacy-fiber",
        object_id="object-1",
        atomic_step="legacy epistemic projection",
    )
    fiber.add_projection(
        Projection(
            projection_id="projection-1",
            object_id="object-1",
            facets=("definition",),
            claim="legacy claim",
            source="source://legacy",
        )
    )
    return fiber


def test_state_metrology_reports_when_legacy_knowledge_is_not_supplied():
    snapshot = measure_state(RAKLV3State())
    assert not snapshot.legacy_knowledge_included
    assert snapshot.legacy_knowledge_fiber_count == 0
    assert snapshot.legacy_knowledge_projection_count == 0
    assert "NO_LEGACY_KNOWLEDGE_FIBERS_SUPPLIED" in snapshot.measurement_scope


def test_state_metrology_can_include_explicit_legacy_knowledge_universe():
    snapshot = measure_state(RAKLV3State(), legacy_knowledge_fibers=(_legacy_fiber(),))
    assert snapshot.legacy_knowledge_included
    assert snapshot.legacy_knowledge_fiber_count == 1
    assert snapshot.legacy_knowledge_projection_count == 1
    assert "LEGACY_KNOWLEDGE_FIBERS_INCLUDED" in snapshot.measurement_scope
    assert dict(snapshot.node_counts)[SubstrateKind.EPISTEMIC.value] == 1


def test_growth_comparison_rejects_different_measurement_universes():
    state = RAKLV3State()
    without_legacy = measure_state(state)
    with_legacy = measure_state(state, legacy_knowledge_fibers=(_legacy_fiber(),))
    with pytest.raises(ValueError, match="different measurement scopes"):
        compare_state_metrics(without_legacy, with_legacy)
