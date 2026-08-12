from rakl.problem_fibre import FibreKnowledgeItem, ProblemAtom, compile_problem_fibre
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    materialize_validated_quotient,
)
from rakl.semantic_quotient_runtime import (
    QuotientRuntimeRoute,
    compile_problem_fibre_with_quotient_fallback,
)


def _validated_view():
    source = ProblemRepresentation(
        representation_id="runtime-r",
        problem_id="runtime-p",
        atom_id="runtime-a",
        qoi="stability",
        context_hash="runtime-ctx",
        source_hash="runtime-source-hash",
        coordinates=("queue", "stability", "surface"),
        protected_fields=("queue", "stability"),
    )
    proposal = QuotientProposal(
        quotient_id="runtime-q",
        source_representation_id=source.representation_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        preserved_coordinates=("queue", "stability"),
        erased_coordinates=("surface",),
        preserved_invariants=("queue_stability",),
        protected_coordinates=("queue", "stability"),
        sufficiency_obligations=("answer_preserved",),
        falsifiers=("surface_changes_answer",),
    )
    report = QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("answer_preserved",),
        metamorphic_checks=("surface_orbit",),
        protected_coordinate_checks=("queue_present", "stability_present"),
        evidence_pointers=("runtime:receipt",),
    )
    return materialize_validated_quotient(source, proposal, report)


def _atom() -> ProblemAtom:
    return ProblemAtom(
        atom_id="runtime-a",
        goal="determine stability",
        context_hash="runtime-ctx",
        structural_coordinates=("queue", "stability", "surface"),
        desired_effects=(),
    )


def _items():
    return (
        FibreKnowledgeItem(
            item_id="a-surface",
            kind="surface",
            structural_signature=("surface",),
            effects=(),
            context_tags=(),
            authority="PROPOSAL_ONLY",
            payload_hash="surface-hash",
        ),
        FibreKnowledgeItem(
            item_id="z-structure",
            kind="structure",
            structural_signature=("queue", "stability"),
            effects=(),
            context_tags=(),
            authority="PROPOSAL_ONLY",
            payload_hash="structure-hash",
        ),
    )


def test_no_quotient_reproduces_incumbent_raw_fibre() -> None:
    atom = _atom()
    kwargs = {"knowledge_items": _items(), "top_k_each": 1}
    incumbent = compile_problem_fibre(atom, **kwargs)
    routed = compile_problem_fibre_with_quotient_fallback(atom, **kwargs)
    assert routed.route is QuotientRuntimeRoute.RAW_NO_QUOTIENT
    assert routed.fibre.snapshot_hash == incumbent.snapshot_hash
    assert routed.fibre.knowledge_items == incumbent.knowledge_items


def test_rejected_unknown_and_cost_negative_quotients_fall_back_to_raw() -> None:
    atom = _atom()
    kwargs = {"knowledge_items": _items(), "top_k_each": 1}
    incumbent = compile_problem_fibre(atom, **kwargs)

    rejected = compile_problem_fibre_with_quotient_fallback(
        atom, fallback_reason="REJECTED", **kwargs
    )
    unknown = compile_problem_fibre_with_quotient_fallback(
        atom, fallback_reason="CANNOT_CHECK", **kwargs
    )
    cost_negative = compile_problem_fibre_with_quotient_fallback(
        atom,
        quotient_view=_validated_view(),
        estimated_net_benefit=0.0,
        **kwargs,
    )

    assert rejected.route is QuotientRuntimeRoute.RAW_REJECTED
    assert unknown.route is QuotientRuntimeRoute.RAW_CANNOT_CHECK
    assert cost_negative.route is QuotientRuntimeRoute.RAW_COST_NEGATIVE
    for result in (rejected, unknown, cost_negative):
        assert result.fibre.snapshot_hash == incumbent.snapshot_hash


def test_validated_positive_route_can_change_retrieval_without_mutating_raw_atom() -> None:
    atom = _atom()
    raw_coordinates = atom.structural_coordinates
    routed = compile_problem_fibre_with_quotient_fallback(
        atom,
        quotient_view=_validated_view(),
        estimated_net_benefit=1.0,
        knowledge_items=_items(),
        top_k_each=1,
    )
    assert routed.route is QuotientRuntimeRoute.QUOTIENT
    assert routed.fibre.knowledge_items[0].item_id == "z-structure"
    assert atom.structural_coordinates == raw_coordinates
    assert routed.quotient_view_hash == _validated_view().content_hash
    assert len(routed.snapshot_hash) == 64
