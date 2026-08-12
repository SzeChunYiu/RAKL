import pytest

from rakl.multires_memory import (
    MemoryView,
    MemoryViewKind,
    SourcePin,
    validate_memory_view,
)
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    materialize_validated_quotient,
)
from rakl.semantic_quotient_memory import quotient_to_pinned_memory_view


def _validated_view():
    source = ProblemRepresentation(
        representation_id="r-memory",
        problem_id="p-memory",
        atom_id="a-memory",
        qoi="stability",
        context_hash="ctx-memory",
        source_hash="canonical-hash",
        coordinates=("signal", "nuisance"),
        protected_fields=("signal",),
    )
    proposal = QuotientProposal(
        quotient_id="q-memory",
        source_representation_id=source.representation_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        preserved_coordinates=("signal",),
        erased_coordinates=("nuisance",),
        preserved_invariants=("signal_preserved",),
        protected_coordinates=("signal",),
        sufficiency_obligations=("answer_preserved",),
        falsifiers=("nuisance_changes_answer",),
    )
    report = QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("answer_preserved",),
        metamorphic_checks=("nuisance_orbit",),
        protected_coordinate_checks=("signal_present",),
        evidence_pointers=("receipt:memory",),
    )
    return materialize_validated_quotient(source, proposal, report)


def test_pinned_constructor_copies_canonical_authority_and_validates_lineage() -> None:
    view = _validated_view()
    canonical = MemoryView(
        record_id="canonical:p-memory",
        payload_hash="canonical-hash",
        kind=MemoryViewKind.CANONICAL,
        authority_certificates=("authority:source",),
    )
    derived = quotient_to_pinned_memory_view(view, canonical)
    assert derived.kind is MemoryViewKind.DERIVED_LOSSY
    assert derived.authority_certificates == ("authority:source",)
    assert validate_memory_view(derived.record_id, (canonical, derived)).valid


def test_pinned_constructor_rejects_hash_mismatch_and_noncanonical_source() -> None:
    view = _validated_view()
    wrong_hash = MemoryView(
        record_id="canonical:wrong",
        payload_hash="wrong-hash",
        kind=MemoryViewKind.CANONICAL,
    )
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        quotient_to_pinned_memory_view(view, wrong_hash)

    derived_source = MemoryView(
        record_id="derived:wrong",
        payload_hash="canonical-hash",
        kind=MemoryViewKind.DERIVED_LOSSLESS,
        source_pins=(SourcePin("canonical:parent", "parent-hash"),),
        transform_id="noop",
    )
    with pytest.raises(ValueError, match="must_be_canonical"):
        quotient_to_pinned_memory_view(view, derived_source)
