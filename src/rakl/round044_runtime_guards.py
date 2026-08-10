from __future__ import annotations

from dataclasses import dataclass

from .research_cycle import ResearchStage


@dataclass(frozen=True)
class RuntimeGuardContract:
    """Supplemental invariant bound to an existing atomic research stage.

    Round 044 does not add hidden stages to the canonical 17-stage lifecycle. It
    makes new metrology/discovery/storage checks explicit as guards on already
    registered stage transitions so execution traces remain machine-auditable.
    """

    guard_id: str
    stage: ResearchStage
    purpose: str
    state_read_set: tuple[str, ...]
    state_write_set: tuple[str, ...]
    failure_semantics: tuple[str, ...]
    implementation_owner: str
    llm_has_authority: bool = False

    def problems(self) -> tuple[str, ...]:
        problems: list[str] = []
        if not self.guard_id:
            problems.append("guard_id_missing")
        if not self.purpose.strip():
            problems.append("purpose_missing")
        if not self.state_read_set:
            problems.append("state_read_set_missing")
        if not self.state_write_set:
            problems.append("state_write_set_missing")
        if not self.failure_semantics:
            problems.append("failure_semantics_missing")
        if not self.implementation_owner:
            problems.append("implementation_owner_missing")
        if self.llm_has_authority:
            problems.append("runtime_guard_cannot_delegate_authority_to_llm")
        return tuple(problems)


def round044_guard_contracts() -> tuple[RuntimeGuardContract, ...]:
    G = RuntimeGuardContract
    S = ResearchStage
    return (
        G(
            "CONTENT_ADDRESSED_EVIDENCE_ARCHIVE",
            S.INGEST_EVIDENCE,
            "bind canonical source identity to raw-content hash, losslessly compress when smaller, and deduplicate physical bytes without collapsing logical provenance records",
            ("source_payload", "raw_evidence_archive"),
            ("raw_evidence_archive", "archive_storage_metrics"),
            ("CONTENT_HASH_MISMATCH", "CANONICAL_RECORD_REBIND_FORBIDDEN", "ARCHIVE_CAPACITY_UNSATISFIABLE"),
            "content_addressed_archive.py",
        ),
        G(
            "LATTICE_PRE_POST_METROLOGY",
            S.UPDATE_ATLAS,
            "measure occupied volume, atom density, relation density and evidence density before/after an atlas update",
            ("knowledge_atlas_before", "atlas_delta", "provenance_ledger"),
            ("lattice_transition_metrics",),
            ("METROLOGY_UNAVAILABLE", "COMPARISON_INVALID"),
            "lattice_metrology.py",
        ),
        G(
            "ACTIVE_LATTICE_CAPACITY",
            S.COMPILE_WORKING_CONTEXT,
            "prevent active atlas/materialized context growth from becoming unbounded while preserving canonical archive roots",
            ("knowledge_atlas", "lattice_transition_metrics", "active_capacity_policy"),
            ("active_capacity_decision", "execution_workspace"),
            ("COMPACT_OR_DEMOTE_ACTIVE_VIEW", "CANNOT_COMPILE"),
            "lattice_metrology.py",
        ),
        G(
            "EXOGENOUS_DISCOVERY_ROUTE_EXPANSION",
            S.SELECT_NEXT_ACTION,
            "when external-method or novelty search is implicated, include function-first and adjacent-domain discovery routes instead of searching only current ontology labels",
            ("residual_ledger", "external_discovery_route_history", "target_function_facets"),
            ("external_discovery_plan",),
            ("ROUTE_COVERAGE_INCOMPLETE",),
            "discovery_coverage.py",
        ),
        G(
            "EXOGENOUS_DISCOVERY_SATURATION_GATE",
            S.CHECK_SATURATION,
            "block external-framework saturation after an uncovered route class or a later relevant exogenous concept miss",
            ("external_discovery_route_history", "exogenous_candidate_audit", "saturation_state"),
            ("saturation_state", "failure_memory"),
            ("EXOGENOUS_CONCEPT_MISS", "ROUTE_COVERAGE_INCOMPLETE", "REOPENED_BY_RESIDUAL"),
            "discovery_coverage.py",
        ),
    )


def validate_round044_guard_contracts(
    contracts: tuple[RuntimeGuardContract, ...] | None = None,
) -> tuple[str, ...]:
    pool = round044_guard_contracts() if contracts is None else contracts
    problems: list[str] = []
    seen: set[str] = set()
    for contract in pool:
        if contract.guard_id in seen:
            problems.append(f"duplicate_guard_id:{contract.guard_id}")
        seen.add(contract.guard_id)
        problems.extend(f"{contract.guard_id}:{item}" for item in contract.problems())
    required = {
        "CONTENT_ADDRESSED_EVIDENCE_ARCHIVE",
        "LATTICE_PRE_POST_METROLOGY",
        "ACTIVE_LATTICE_CAPACITY",
        "EXOGENOUS_DISCOVERY_ROUTE_EXPANSION",
        "EXOGENOUS_DISCOVERY_SATURATION_GATE",
    }
    for guard_id in sorted(required - seen):
        problems.append(f"required_guard_missing:{guard_id}")
    return tuple(problems)
