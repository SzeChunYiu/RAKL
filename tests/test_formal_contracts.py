from __future__ import annotations

from rakl.formal_contracts import (
    AuthorityEffect,
    ClosureVerdict,
    METHOD_SURFACES,
    MechanicContract,
    validate_formal_closure,
)
from rakl.method_specs import METHOD_CONTRACTS


def test_registry_covers_exactly_the_24_registered_method_surfaces():
    report = validate_formal_closure(METHOD_CONTRACTS)
    assert tuple(item.surface for item in METHOD_CONTRACTS) == METHOD_SURFACES
    assert report.verdict is ClosureVerdict.CLOSED_SCOPED
    assert report.missing_surfaces == ()
    assert report.duplicate_surfaces == ()
    assert report.contract_problems == ()


def test_every_contract_has_real_implementation_test_and_empirical_open_coordinate():
    for contract in METHOD_CONTRACTS:
        assert contract.implementation_refs
        assert contract.test_refs
        assert contract.mathematical_semantics
        assert contract.empirical_open_coordinates
        assert all(ref.startswith("src/rakl/") for ref in contract.implementation_refs)
        assert all(ref.startswith("tests/") for ref in contract.test_refs)


def test_formal_closure_never_implies_empirical_or_saturation_authority():
    report = validate_formal_closure(METHOD_CONTRACTS)
    assert report.grants_scientific_authority is False
    assert report.grants_empirical_superiority is False
    assert report.establishes_framework_saturation is False


def test_placeholder_or_destructive_contract_fails_closed():
    bad = MechanicContract(
        surface="decomposition",
        object="x",
        inputs=("x",),
        outputs=("y",),
        scope_context=("scope",),
        assumptions=("assumption",),
        state_read_set=("F",),
        state_write_set=("H-",),
        authority_effect=AuthorityEffect.PROPOSAL_ONLY,
        non_escalation_rules=("no escalation",),
        failure_semantics=("CANNOT_CHECK",),
        invariants=("negative history preserved",),
        mathematical_semantics=("f=(o,q,gamma,r,parent)",),
        implementation_refs=("src/rakl/core.py",),
        test_refs=("tests/test_core.py",),
        empirical_open_coordinates=("real benchmark open",),
    )
    report = validate_formal_closure((bad,))
    assert report.verdict is ClosureVerdict.OPEN_SPECIFICATION_GAPS
    assert "negative_history_destructive_write_forbidden" in bad.problems()
