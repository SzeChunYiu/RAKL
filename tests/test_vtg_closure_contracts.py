from __future__ import annotations

from rakl.navigation_quotient import NavigationQuotientValidation, NavigationQuotientVerdict
from rakl.path_cost import (
    CostComparisonKind,
    CostCompositionKind,
    PathCostAlgebra,
    PathCostCoordinateRule,
)


def test_exact_navigation_quotient_requires_two_way_reachability_and_cost_witnesses():
    receipt = NavigationQuotientValidation(
        "nav", "q", "semantic", "source", "abstract",
        True, True, True, True,
        verifier_ids=("simulation-checker", "lifting-checker"),
    )
    assert receipt.verdict is NavigationQuotientVerdict.EXACT_REACHABILITY_PRESERVING
    assert receipt.supports_exact_navigation_geometry_claim is True
    assert receipt.abstract_route_can_mint_solution_authority is False
    assert receipt.abstract_no_route_can_mint_impossibility_authority is False


def test_forward_only_navigation_quotient_is_overapprox_and_requires_lifting():
    receipt = NavigationQuotientValidation(
        "nav", "q", "semantic", "source", "abstract",
        True, True, None, None,
        verifier_ids=("forward-simulation-checker",),
    )
    assert receipt.verdict is NavigationQuotientVerdict.SOUND_OVERAPPROX_REQUIRES_LIFTING
    assert receipt.requires_concrete_route_revalidation is True
    assert receipt.supports_exact_navigation_geometry_claim is False


def test_failed_navigation_obligation_rejects_exact_geometry_use():
    receipt = NavigationQuotientValidation(
        "nav", "q", "semantic", "source", "abstract",
        True, True, False, True,
        verifier_ids=("checker",),
        counterexample_ids=("spurious-route-1",),
    )
    assert receipt.verdict is NavigationQuotientVerdict.REJECT


def test_typed_path_cost_algebra_does_not_assume_every_coordinate_adds():
    algebra = PathCostAlgebra(
        "vtg-cost-v1",
        (
            PathCostCoordinateRule("compute", CostCompositionKind.SUM, CostComparisonKind.MINIMIZE, "seconds"),
            PathCostCoordinateRule("peak_memory", CostCompositionKind.MAX, CostComparisonKind.MINIMIZE, "bytes"),
            PathCostCoordinateRule("assumptions", CostCompositionKind.SET_UNION, CostComparisonKind.SET_INCLUSION, "axiom-set"),
            PathCostCoordinateRule("trust", CostCompositionKind.WORST_CASE, CostComparisonKind.REGISTERED_PARTIAL_ORDER, "trust-lattice-v1"),
        ),
        "math-hard-admissibility-v1",
    )
    assert algebra.is_uniformly_additive_numeric is False
    assert algebra.rule_for("assumptions").composition is CostCompositionKind.SET_UNION
