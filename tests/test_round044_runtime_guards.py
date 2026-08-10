from __future__ import annotations

from rakl.research_cycle import ResearchStage
from rakl.round044_runtime_guards import round044_guard_contracts, validate_round044_guard_contracts


def test_round044_runtime_guards_are_complete_and_valid():
    assert validate_round044_guard_contracts() == ()
    guards = round044_guard_contracts()
    assert len(guards) == 4
    assert all(not guard.llm_has_authority for guard in guards)


def test_lattice_guards_bind_to_atlas_update_and_context_compile():
    by_id = {guard.guard_id: guard for guard in round044_guard_contracts()}
    assert by_id["LATTICE_PRE_POST_METROLOGY"].stage is ResearchStage.UPDATE_ATLAS
    assert by_id["ACTIVE_LATTICE_CAPACITY"].stage is ResearchStage.COMPILE_WORKING_CONTEXT
    assert by_id["LATTICE_PRE_POST_METROLOGY"].implementation_owner == "lattice_metrology.py"


def test_exogenous_discovery_is_part_of_control_and_saturation_not_llm_authority():
    by_id = {guard.guard_id: guard for guard in round044_guard_contracts()}
    route = by_id["EXOGENOUS_DISCOVERY_ROUTE_EXPANSION"]
    gate = by_id["EXOGENOUS_DISCOVERY_SATURATION_GATE"]
    assert route.stage is ResearchStage.SELECT_NEXT_ACTION
    assert gate.stage is ResearchStage.CHECK_SATURATION
    assert "EXOGENOUS_CONCEPT_MISS" in gate.failure_semantics
    assert route.llm_has_authority is False
    assert gate.llm_has_authority is False
