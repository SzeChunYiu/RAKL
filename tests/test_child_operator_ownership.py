from __future__ import annotations

from rakl.child_operators import CHILD_OPERATORS, validate_child_operator_ownership
from rakl.formal_contracts import METHOD_SURFACES
from rakl.prepolymarket import (
    AssumptionSensitivityVerdict,
    BootstrapVerdict,
    METHOD_CONTRACTS,
    ModelCriticismVerdict,
    validate_formal_closure,
)


def test_every_child_operator_is_owned_by_existing_method_surfaces():
    assert validate_child_operator_ownership() == ()
    assert CHILD_OPERATORS
    for operator in CHILD_OPERATORS:
        assert operator.parent_surfaces
        assert set(operator.parent_surfaces).issubset(set(METHOD_SURFACES))


def test_child_operators_do_not_expand_the_high_level_surface_inventory():
    assert len(METHOD_SURFACES) == 24
    assert len({contract.surface for contract in METHOD_CONTRACTS}) == 24
    assert validate_formal_closure(METHOD_CONTRACTS).missing_surfaces == ()


def test_prepolymarket_api_exposes_fail_closed_verdict_types():
    assert AssumptionSensitivityVerdict.CANNOT_CHECK.value == "CANNOT_CHECK"
    assert BootstrapVerdict.META_OVERFIT.value == "META_OVERFIT"
    assert ModelCriticismVerdict.TRIAL_INVALID.value == "TRIAL_INVALID"
