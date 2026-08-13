"""Exact-base regressions for the reviewed current-main guard patches.

These tests are intended for the full RAKL checkout after the direct patches
have been applied by ``tools/apply_unified_handoff.py``.  They are not part of
the packet's isolated additive-module fixture.
"""
from math import inf, nan

import pytest

from rakl.authority_ledger import AuthorityAxis
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    validate_proposal_contract,
)
from rakl.v3_scientific_authority import ScientificEvidenceBinding, _check_evidence_contract


def test_approximation_tolerance_rejects_nonfinite_values() -> None:
    for value in (nan, inf, -inf):
        with pytest.raises(ValueError, match="finite and non-negative"):
            QuotientValidationReport(
                quotient_id="q",
                proposal_hash="p",
                source_hash="s",
                verdict=QuotientValidationVerdict.VALID_APPROXIMATE,
                approximation_metric="absolute_error",
                approximation_tolerance=value,
            )


def test_forbidden_loss_cannot_hide_in_conditional_erasure() -> None:
    source = ProblemRepresentation(
        representation_id="r",
        problem_id="p",
        atom_id="a",
        qoi="qoi",
        context_hash="ctx",
        source_hash="src",
        coordinates=("keep", "must_not_erase"),
        protected_fields=("keep",),
        provenance_ids=("prov",),
    )
    proposal = QuotientProposal(
        quotient_id="q",
        source_representation_id="r",
        source_hash="src",
        qoi="qoi",
        context_hash="ctx",
        preserved_coordinates=("keep",),
        erased_coordinates=(),
        conditionally_erased_coordinates=("must_not_erase",),
        preserved_invariants=("inv",),
        protected_coordinates=("keep",),
        sufficiency_obligations=("suff",),
        falsifiers=("falsifier",),
        forbidden_losses=("must_not_erase",),
    )
    assert "forbidden_loss_erased" in validate_proposal_contract(source, proposal)


def _binding(evidence_id: str, *, upstream: str | None = None) -> ScientificEvidenceBinding:
    return ScientificEvidenceBinding(
        evidence_id=evidence_id,
        kind=EvidenceRootKind.EXTERNAL_OBSERVATION,
        content_sha256=(evidence_id[0].lower() if evidence_id else "a") * 64,
        supports_axes=(AuthorityAxis.REPRESENTATION,),
        upstream_evidence_id=upstream,
    )


def test_scientific_authority_rejects_lineage_cycle() -> None:
    a = _binding("a", upstream="b")
    b = _binding("b", upstream="a")
    reasons = _check_evidence_contract(
        AuthorityAxis.REPRESENTATION,
        ("a", "b"),
        {"a": a, "b": b},
    )
    assert any(reason.startswith("scientific_evidence_lineage_cycle:") for reason in reasons)


def test_scientific_authority_rejects_unresolved_upstream_lineage() -> None:
    child = _binding("c", upstream="missing-root")
    reasons = _check_evidence_contract(
        AuthorityAxis.REPRESENTATION,
        ("c",),
        {"c": child},
    )
    assert "scientific_evidence_lineage_unresolved:missing-root" in reasons
