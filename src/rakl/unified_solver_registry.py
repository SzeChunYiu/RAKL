from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .formal_contracts import AuthorityEffect, METHOD_SURFACES


@dataclass(frozen=True)
class UnifiedSolverMechanicSpec:
    mechanic_id: str
    module_path: str
    owner_surface: str
    test_paths: Tuple[str, ...]
    authority_effect: AuthorityEffect
    purpose: str
    empirical_open_coordinates: Tuple[str, ...]

    def problems(self) -> Tuple[str, ...]:
        problems: list[str] = []
        if not self.mechanic_id.strip():
            problems.append("mechanic_id_missing")
        if not self.module_path.startswith("src/rakl/") or not self.module_path.endswith(".py"):
            problems.append("module_path_invalid")
        if self.owner_surface not in METHOD_SURFACES:
            problems.append("owner_surface_not_canonical")
        if not self.test_paths or any(not item.startswith("tests/") for item in self.test_paths):
            problems.append("test_path_invalid_or_missing")
        if self.authority_effect not in {AuthorityEffect.NONE, AuthorityEffect.PROPOSAL_ONLY}:
            problems.append("solver_sidecar_authority_too_strong")
        if not self.purpose.strip():
            problems.append("purpose_missing")
        if not self.empirical_open_coordinates or any(not item.strip() for item in self.empirical_open_coordinates):
            problems.append("empirical_open_coordinate_missing")
        return tuple(problems)


UNIFIED_SOLVER_MECHANICS: Tuple[UnifiedSolverMechanicSpec, ...] = (
    UnifiedSolverMechanicSpec(
        "operational_map_belief",
        "src/rakl/operational_map.py",
        "routing",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Separate verifier-legal/materialized transitions from partial operational map belief and coverage.",
        ("real partial-map navigation and coverage calibration",),
    ),
    UnifiedSolverMechanicSpec(
        "path_equivalence_concurrency",
        "src/rakl/path_equivalence.py",
        "equivalence_similarity",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Quotient verifier-witnessed equivalent/commuting transformation histories without erasing raw chronology.",
        ("formal-proof search reduction from path/interleaving quotienting",),
    ),
    UnifiedSolverMechanicSpec(
        "navigation_quotient_validation",
        "src/rakl/navigation_quotient.py",
        "equivalence_similarity",
        ("tests/test_vtg_closure_contracts.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Separate target/QoI quotient sufficiency from solver reachability, route-lifting, and cost-distortion obligations.",
        ("safe quotient acceleration on real theorem-search state spaces",),
    ),
    UnifiedSolverMechanicSpec(
        "path_cost_algebra",
        "src/rakl/path_cost.py",
        "routing",
        ("tests/test_unified_solver_framework.py", "tests/test_vtg_closure_contracts.py"),
        AuthorityEffect.PROPOSAL_ONLY,
        "Apply noncompensatory admissibility before a registered typed path-cost algebra, Pareto frontier, or explicitly scoped numeric development projection.",
        ("task-valid path-cost composition semantics and multiobjective utility",),
    ),
    UnifiedSolverMechanicSpec(
        "fieldability_and_geometry_lifecycle",
        "src/rakl/fieldability.py",
        "routing",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Measure local/global navigability, geometry certification class, construction/reuse economics, and invalidation without treating distance as truth.",
        ("held-out formal reachability geometry and cross-family local navigation",),
    ),
    UnifiedSolverMechanicSpec(
        "mechanic_differential_diagnosis",
        "src/rakl/mechanic_diagnosis.py",
        "gap_discovery",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Represent competing solver-substrate failure causes and require discriminators when one cause is not identified.",
        ("hidden-cause diagnosis utility under matched repair/discriminator budgets",),
    ),
    UnifiedSolverMechanicSpec(
        "verified_solver_compilation",
        "src/rakl/solver_compilation.py",
        "capability_shaping",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Bind representation, solver, decoder and verifier choices with preservation, total cost, reuse and staleness semantics.",
        ("joint representation-solver selection beyond strongest simple selection parents",),
    ),
    UnifiedSolverMechanicSpec(
        "trajectory_to_certificate_assembly",
        "src/rakl/solution_assembly.py",
        "synthesis",
        ("tests/test_unified_solver_framework.py",),
        AuthorityEffect.PROPOSAL_ONLY,
        "Separate chronological discovery trajectories from dependency-complete proof certificates bound to the ordinary audited proof receipt.",
        ("real long-horizon certificate assembly and verifier scheduling",),
    ),
)


@dataclass(frozen=True)
class UnifiedSolverRegistryReport:
    valid: bool
    mechanic_ids: Tuple[str, ...]
    duplicate_ids: Tuple[str, ...]
    duplicate_modules: Tuple[str, ...]
    problems: Tuple[Tuple[str, Tuple[str, ...]], ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def establishes_global_framework_completeness(self) -> bool:
        return False


def validate_unified_solver_registry(
    specs: Tuple[UnifiedSolverMechanicSpec, ...] = UNIFIED_SOLVER_MECHANICS,
) -> UnifiedSolverRegistryReport:
    ids = tuple(item.mechanic_id for item in specs)
    modules = tuple(item.module_path for item in specs)
    duplicate_ids = tuple(sorted({item for item in ids if ids.count(item) > 1}))
    duplicate_modules = tuple(sorted({item for item in modules if modules.count(item) > 1}))
    problems = tuple((item.mechanic_id, item.problems()) for item in specs if item.problems())
    valid = bool(specs) and not duplicate_ids and not duplicate_modules and not problems
    return UnifiedSolverRegistryReport(
        valid=valid,
        mechanic_ids=ids,
        duplicate_ids=duplicate_ids,
        duplicate_modules=duplicate_modules,
        problems=problems,
        reasons=(
            f"registered_unified_solver_mechanics:{len(specs)}",
            "all_new_modules_owned_by_existing_canonical_method_surfaces",
            "solver_sidecars_are_none_or_proposal_only_authority",
            "formal_registry_validity_is_not_empirical_utility",
            "formal_registry_validity_is_not_global_framework_completeness",
        ),
    )
