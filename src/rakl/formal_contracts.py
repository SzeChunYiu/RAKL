from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


METHOD_SURFACES: Tuple[str, ...] = (
    "decomposition",
    "routing",
    "search_query_generation",
    "source_selection_reliability",
    "claim_extraction",
    "ontology_terminology_normalization",
    "mathematical_context_translation",
    "equivalence_similarity",
    "contextual_theory_gluing",
    "contradiction_diagnosis",
    "gap_discovery",
    "experiment_query_selection",
    "synthesis",
    "memory",
    "review",
    "benchmarking",
    "authority_promotion",
    "saturation_stopping",
    "prompting_context_policy",
    "capability_shaping",
    "software_architecture_execution",
    "research_portfolio_tree",
    "objective_evolution",
    "generator_transport",
)


class AuthorityEffect(str, Enum):
    NONE = "NONE"
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    SCOPED_CERTIFICATE_ONLY = "SCOPED_CERTIFICATE_ONLY"
    EXTERNAL_GATE_REQUIRED = "EXTERNAL_GATE_REQUIRED"


class ClosureVerdict(str, Enum):
    CLOSED_SCOPED = "CLOSED_SCOPED"
    OPEN_SPECIFICATION_GAPS = "OPEN_SPECIFICATION_GAPS"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MechanicContract:
    surface: str
    object: str
    inputs: Tuple[str, ...]
    outputs: Tuple[str, ...]
    scope_context: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    state_read_set: Tuple[str, ...]
    state_write_set: Tuple[str, ...]
    authority_effect: AuthorityEffect
    non_escalation_rules: Tuple[str, ...]
    failure_semantics: Tuple[str, ...]
    invariants: Tuple[str, ...]
    mathematical_semantics: Tuple[str, ...]
    implementation_refs: Tuple[str, ...]
    test_refs: Tuple[str, ...]
    empirical_open_coordinates: Tuple[str, ...]

    def problems(self) -> Tuple[str, ...]:
        problems: list[str] = []
        if self.surface not in METHOD_SURFACES:
            problems.append("surface_not_registered")
        required_text_fields = {
            "object": (self.object,),
            "inputs": self.inputs,
            "outputs": self.outputs,
            "scope_context": self.scope_context,
            "assumptions": self.assumptions,
            "state_read_set": self.state_read_set,
            "state_write_set": self.state_write_set,
            "non_escalation_rules": self.non_escalation_rules,
            "failure_semantics": self.failure_semantics,
            "invariants": self.invariants,
            "mathematical_semantics": self.mathematical_semantics,
            "implementation_refs": self.implementation_refs,
            "test_refs": self.test_refs,
            "empirical_open_coordinates": self.empirical_open_coordinates,
        }
        for name, values in required_text_fields.items():
            if not values or any(not str(value).strip() for value in values):
                problems.append(f"{name}_missing")
        if "H-" in self.state_write_set:
            problems.append("negative_history_destructive_write_forbidden")
        return tuple(problems)


@dataclass(frozen=True)
class FormalClosureReport:
    verdict: ClosureVerdict
    registered_surfaces: Tuple[str, ...]
    missing_surfaces: Tuple[str, ...]
    duplicate_surfaces: Tuple[str, ...]
    contract_problems: Tuple[Tuple[str, Tuple[str, ...]], ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_empirical_superiority(self) -> bool:
        return False

    @property
    def establishes_framework_saturation(self) -> bool:
        return False


def validate_formal_closure(contracts: Iterable[MechanicContract]) -> FormalClosureReport:
    contracts = tuple(contracts)
    by_surface: dict[str, list[MechanicContract]] = {}
    for contract in contracts:
        by_surface.setdefault(contract.surface, []).append(contract)

    missing = tuple(surface for surface in METHOD_SURFACES if surface not in by_surface)
    duplicates = tuple(sorted(surface for surface, group in by_surface.items() if len(group) != 1))
    problems = tuple(
        sorted(
            (
                contract.surface,
                contract.problems(),
            )
            for contract in contracts
            if contract.problems()
        )
    )
    unknown = tuple(sorted(surface for surface in by_surface if surface not in METHOD_SURFACES))

    if missing or duplicates or problems or unknown:
        verdict = ClosureVerdict.OPEN_SPECIFICATION_GAPS
    else:
        verdict = ClosureVerdict.CLOSED_SCOPED

    reasons = (
        f"registered_contracts:{len(contracts)}",
        f"required_surfaces:{len(METHOD_SURFACES)}",
        f"missing_surfaces:{len(missing)}",
        f"duplicate_or_unknown_surfaces:{len(duplicates) + len(unknown)}",
        f"contracts_with_problems:{len(problems)}",
        "formal_closure_is_not_empirical_validation",
        "formal_closure_is_not_framework_saturation",
        "new_native_residual_reopens_affected_surface",
    )
    return FormalClosureReport(
        verdict=verdict,
        registered_surfaces=tuple(sorted(by_surface)),
        missing_surfaces=missing,
        duplicate_surfaces=tuple(sorted(set(duplicates + unknown))),
        contract_problems=problems,
        reasons=reasons,
    )
