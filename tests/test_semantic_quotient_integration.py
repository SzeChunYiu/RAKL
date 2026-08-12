from dataclasses import replace

from rakl.multires_memory import (
    MemoryView,
    MemoryViewKind,
    validate_memory_view,
)
from rakl.problem_fibre import FibreKnowledgeItem, ProblemAtom, compile_problem_fibre
from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    compile_quotient_problem_fibre,
    materialize_validated_quotient,
    obstruction_from_validated_quotient,
    quotient_to_memory_view,
)


def _view_for_retrieval():
    source = ProblemRepresentation(
        representation_id="r-retrieval",
        problem_id="p-retrieval",
        atom_id="a-retrieval",
        qoi="backlog_stability",
        context_hash="ctx-retrieval",
        source_hash="canonical-payload-hash",
        coordinates=("queue", "stability", "color", "story", "entity_name"),
        protected_fields=("queue", "stability"),
        provenance_ids=("prov:source",),
    )
    proposal = QuotientProposal(
        quotient_id="q-retrieval",
        source_representation_id=source.representation_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        preserved_coordinates=("queue", "stability"),
        erased_coordinates=("color", "story", "entity_name"),
        preserved_invariants=("arrival_gt_service_implies_growth",),
        protected_coordinates=("queue", "stability"),
        sufficiency_obligations=("stability_answer_preserved",),
        reconstruction_bindings=(("answer_scope", "original_problem"),),
        falsifiers=("nuisance_change_alters_stability_answer",),
        forbidden_losses=("arrival_service_direction",),
        evidence_pointers=("proposal:receipt",),
    )
    report = QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("stability_answer_preserved",),
        metamorphic_checks=("vary_color_story_name",),
        protected_coordinate_checks=("queue_preserved", "stability_preserved"),
        evidence_pointers=("validation:receipt",),
    )
    return materialize_validated_quotient(source, proposal, report)


def test_quotient_is_lossy_derived_memory_view_with_no_authority_escalation() -> None:
    view = _view_for_retrieval()
    canonical = MemoryView(
        record_id="canonical:p-retrieval",
        payload_hash="canonical-payload-hash",
        kind=MemoryViewKind.CANONICAL,
        authority_certificates=("authority:source",),
    )
    derived = quotient_to_memory_view(
        view,
        canonical_record_id=canonical.record_id,
        canonical_payload_hash=canonical.payload_hash,
        source_authority_certificates=canonical.authority_certificates,
    )
    assert derived.kind is MemoryViewKind.DERIVED_LOSSY
    assert set(derived.erasure_tags) == {
        "ERASED:color",
        "ERASED:story",
        "ERASED:entity_name",
    }
    report = validate_memory_view(derived.record_id, (canonical, derived))
    assert report.valid
    assert derived.authority_certificates == canonical.authority_certificates

    escalated = replace(
        derived,
        authority_certificates=("authority:source", "authority:new"),
    )
    bad = validate_memory_view(escalated.record_id, (canonical, escalated))
    assert not bad.valid
    assert "authority_escalation:authority:new" in bad.issues


def test_validated_quotient_changes_retrieval_without_mutating_raw_atom() -> None:
    view = _view_for_retrieval()
    raw_atom = ProblemAtom(
        atom_id="a-retrieval",
        goal="determine backlog stability",
        context_hash="ctx-retrieval",
        structural_coordinates=("queue", "stability", "color", "story", "entity_name"),
        desired_effects=(),
    )
    nuisance_item = FibreKnowledgeItem(
        item_id="a-noise",
        kind="nuisance_surface_match",
        structural_signature=("color", "story", "entity_name"),
        effects=(),
        context_tags=(),
        authority="PROPOSAL_ONLY",
        payload_hash="noise-hash",
    )
    structural_item = FibreKnowledgeItem(
        item_id="z-structure",
        kind="structural_match",
        structural_signature=("queue", "stability"),
        effects=(),
        context_tags=(),
        authority="PROPOSAL_ONLY",
        payload_hash="structure-hash",
    )

    raw_fibre = compile_problem_fibre(
        raw_atom,
        knowledge_items=(nuisance_item, structural_item),
        top_k_each=1,
    )
    quotient_fibre = compile_quotient_problem_fibre(
        raw_atom,
        view,
        knowledge_items=(nuisance_item, structural_item),
        top_k_each=1,
    )

    assert raw_fibre.knowledge_items[0].item_id == "a-noise"
    assert quotient_fibre.fibre.knowledge_items[0].item_id == "z-structure"
    assert raw_atom.structural_coordinates == (
        "queue",
        "stability",
        "color",
        "story",
        "entity_name",
    )
    assert quotient_fibre.source_atom_id == raw_atom.atom_id
    assert quotient_fibre.quotient_view_hash == view.content_hash
    assert quotient_fibre.fibre_snapshot_hash == quotient_fibre.fibre.snapshot_hash


def test_quotient_obstruction_carries_protected_invariants_and_forbidden_losses() -> None:
    view = _view_for_retrieval()
    obstruction = obstruction_from_validated_quotient(
        view,
        obstruction_id="obs:q-retrieval",
        domain="queue-domain",
        roles=("arrival", "service", "backlog"),
        relations=("arrival_increases_backlog", "service_decreases_backlog"),
        constraints=("nonnegative_rates",),
        failure_mechanisms=("arrival_exceeds_service",),
    )
    assert obstruction.invariants_to_preserve == (
        "arrival_gt_service_implies_growth",
    )
    assert obstruction.forbidden_losses == ("arrival_service_direction",)
    assert "protected:queue" in obstruction.constraints
    assert "protected:stability" in obstruction.constraints
    assert obstruction.desired_transition == ("backlog_stability",)
