from __future__ import annotations

from dataclasses import replace

import pytest

from rakl.semantic_shortcut import (
    ExhaustionWitness,
    MissingTransformationSpecification,
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationReview,
    RouteSearchStatus,
    ShortcutMode,
    ShortcutReviewVerdict,
    StructuralMappingWitness,
    TransformationCompositionWitness,
    TransformationEpisodeAuthority,
    audit_obstruction_transformation_review,
    rank_obstruction_transformations,
    repeated_residual_features,
    synthesize_missing_transformation_specification,
)


def _target() -> ObstructionFingerprint:
    return ObstructionFingerprint(
        obstruction_id="obs-target",
        domain="mathematics",
        roles=("many local states", "global proof obligation"),
        relations=("local dependencies feed global obstruction", "finite state revisitation"),
        constraints=("must preserve theorem statement", "finite state space"),
        failure_mechanisms=("local expansion causes search branching",),
        invariants_to_preserve=("logical equivalence",),
        desired_transition=("compress local family into tractable global object",),
        forbidden_losses=("do not weaken theorem statement",),
    )


def _episode(
    episode_id: str = "episode-shipping",
    *,
    source_domain: str = "logistics",
    relation: str = "finite state revisitation",
) -> ObstructionTransformationEpisode:
    return ObstructionTransformationEpisode(
        episode_id=episode_id,
        source_domain=source_domain,
        source_context="packages circulate among a finite set of depots",
        source_obstruction=ObstructionFingerprint(
            obstruction_id=f"source-{episode_id}",
            domain=source_domain,
            roles=("moving item", "finite locations"),
            relations=(relation,),
            constraints=("finite state space",),
            failure_mechanisms=("local expansion causes search branching",),
            invariants_to_preserve=("logical equivalence",),
            desired_transition=("compress local family into tractable global object",),
            forbidden_losses=("do not lose state identity",),
        ),
        transformation_name="aggregate-and-follow-state",
        operation="replace repeated local inspection with a global finite-state trajectory",
        preconditions=("finite state space",),
        resulting_relations=("global trajectory exposes repetition",),
        preserved_invariants=("logical equivalence",),
        relaxed_or_broken_constraints=("individual-step representation is no longer mandatory",),
        known_breakpoints=("fails when the state space is not finite",),
        evidence_pointers=("source:verified-episode",),
        authority=TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
        artifact_hash=f"sha256:{episode_id}",
    )


def _mapping(episode_id: str = "episode-shipping") -> StructuralMappingWitness:
    return StructuralMappingWitness(
        witness_id=f"map-{episode_id}",
        episode_id=episode_id,
        target_obstruction_id="obs-target",
        role_mapping=(("moving item", "proof state"), ("finite locations", "finite states")),
        shared_relations=("finite state revisitation",),
        shared_constraints=("finite state space",),
        disanalogies=("shipping transitions are physical while proof transitions are formal",),
        target_validation_obligations=("prove the transported transition preserves the theorem obligation",),
        evidence_pointers=("mapping:structural-witness",),
        artifact_hash=f"sha256:map-{episode_id}",
    )


def _search_review() -> ObstructionTransformationReview:
    return ObstructionTransformationReview(
        review_id="shortcut-review-C",
        target_atom_id="atom-C",
        target_context_hash="sha256:context",
        research_memory_review_hash="sha256:memory",
        episode_memory_snapshot_hash="sha256:episode-memory",
        obstruction=_target(),
        direct_search_status=RouteSearchStatus.MATCHES_FOUND,
        jump_search_status=RouteSearchStatus.NOT_RUN,
        glue_search_status=RouteSearchStatus.NOT_RUN,
        selected_mode=ShortcutMode.SEARCH,
        direct_candidate_episode_ids=("episode-direct",),
        selected_episode_ids=("episode-direct",),
        unresolved_warnings=("source success still requires target validation",),
        evidence_pointers=("episode-memory:snapshot",),
        artifact_hash="sha256:shortcut-review",
    )


def _audit(review: ObstructionTransformationReview):
    return audit_obstruction_transformation_review(
        review,
        atom_id="atom-C",
        context_hash="sha256:context",
        research_memory_review_hash="sha256:memory",
    )


def test_structural_ranking_uses_relational_coordinates_not_domain_name() -> None:
    cross_domain = _episode("cross-domain", source_domain="newspaper-logistics")
    lexical_decoy = _episode(
        "math-words-only",
        source_domain="mathematics",
        relation="unrelated relation",
    )
    lexical_decoy = replace(
        lexical_decoy,
        source_obstruction=replace(
            lexical_decoy.source_obstruction,
            constraints=("unrelated constraint",),
            failure_mechanisms=("unrelated failure",),
            invariants_to_preserve=("unrelated invariant",),
            desired_transition=("unrelated transition",),
        ),
    )

    matches = rank_obstruction_transformations(_target(), (lexical_decoy, cross_domain))
    assert matches
    assert matches[0].episode_id == "cross-domain"
    assert all(match.episode_id != "math-words-only" for match in matches)


def test_valid_direct_search_route_passes_without_forcing_invention() -> None:
    report = _audit(_search_review())
    assert report.verdict is ShortcutReviewVerdict.PASS
    assert report.selected_mode is ShortcutMode.SEARCH
    assert report.candidate_route_ready


def test_jump_requires_direct_search_exhaustion_and_structural_witness() -> None:
    review = replace(
        _search_review(),
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.MATCHES_FOUND,
        selected_mode=ShortcutMode.JUMP,
        direct_candidate_episode_ids=(),
        selected_episode_ids=("episode-shipping",),
        jump_mapping_witnesses=(),
    )
    missing = _audit(review)
    assert missing.verdict is ShortcutReviewVerdict.FAIL
    assert "jump_mapping_witness_missing" in missing.reasons

    passed = _audit(replace(review, jump_mapping_witnesses=(_mapping(),)))
    assert passed.verdict is ShortcutReviewVerdict.PASS


def test_surface_analogy_without_disanalogy_or_validation_fails_closed() -> None:
    weak_mapping = replace(
        _mapping(),
        disanalogies=(),
        target_validation_obligations=(),
    )
    review = replace(
        _search_review(),
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.MATCHES_FOUND,
        selected_mode=ShortcutMode.JUMP,
        direct_candidate_episode_ids=(),
        selected_episode_ids=("episode-shipping",),
        jump_mapping_witnesses=(weak_mapping,),
    )
    report = _audit(review)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "jump_disanalogies_missing" in report.reasons
    assert "jump_target_validation_obligations_missing" in report.reasons


def test_glue_requires_explicit_order_and_interface_obligations() -> None:
    glue = TransformationCompositionWitness(
        composition_id="glue-1",
        target_obstruction_id="obs-target",
        episode_ids=("episode-A", "episode-B"),
        operation_order=("episode-A", "episode-B"),
        interface_obligations=("output of A satisfies preconditions of B",),
        incompatibilities_checked=("A does not destroy the invariant required by B",),
        target_validation_obligations=("verify composed transformation in target domain",),
        evidence_pointers=("composition:witness",),
        artifact_hash="sha256:glue-1",
    )
    review = replace(
        _search_review(),
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        glue_search_status=RouteSearchStatus.MATCHES_FOUND,
        selected_mode=ShortcutMode.GLUE,
        direct_candidate_episode_ids=(),
        selected_episode_ids=("episode-A", "episode-B"),
        glue_witness=glue,
    )
    assert _audit(review).verdict is ShortcutReviewVerdict.PASS

    bad = replace(review, glue_witness=replace(glue, interface_obligations=()))
    report = _audit(bad)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "glue_interface_obligations_missing" in report.reasons


def test_repeated_residual_features_require_cross_attempt_support() -> None:
    repeated = repeated_residual_features(
        {
            "failure-1": ("branching", "parity mismatch"),
            "failure-2": ("branching", "boundary loss"),
            "failure-3": ("branching", "parity mismatch"),
        }
    )
    assert repeated == ("branching", "parity mismatch")


def test_lift_specification_is_synthesized_from_repeated_failure_not_one_failure() -> None:
    with pytest.raises(ValueError, match="at least two failed attempts"):
        synthesize_missing_transformation_specification(
            _target(),
            spec_id="lift-1",
            residual_signatures={"failure-1": ("branching",)},
            must_reduce=("proof search branching factor",),
            allowed_representation_changes=("introduce auxiliary aggregate object",),
            validation_obligations=("show target equivalence",),
            falsifiers=("find a case where aggregate loses a required distinction",),
            evidence_pointers=("failure:1",),
            artifact_hash="sha256:lift-1",
        )

    spec = synthesize_missing_transformation_specification(
        _target(),
        spec_id="lift-2",
        residual_signatures={
            "failure-1": ("branching", "local-only view"),
            "failure-2": ("branching", "local-only view"),
        },
        must_reduce=("proof search branching factor",),
        allowed_representation_changes=("introduce auxiliary aggregate object",),
        validation_obligations=("show target equivalence",),
        falsifiers=("find a case where aggregate loses a required distinction",),
        evidence_pointers=("failure:1", "failure:2"),
        artifact_hash="sha256:lift-2",
    )
    assert set(spec.must_break) == {"branching", "local-only view"}
    assert spec.must_preserve == _target().invariants_to_preserve


def _lift_review() -> ObstructionTransformationReview:
    exhaustion = ExhaustionWitness(
        target_obstruction_id="obs-target",
        search_boundary="registered math + science + engineering + everyday knowledge snapshot",
        searched_domains=("mathematics", "science", "engineering", "ordinary situations"),
        searched_method_families=("direct reuse", "structural jump", "composition"),
        rejected_direct_episode_ids=("direct-1",),
        rejected_jump_episode_ids=("jump-1",),
        rejected_glue_composition_ids=("glue-0",),
        rejection_reasons=("all retained routes violate a load-bearing target constraint",),
        residual_failure_ids=("failure-1", "failure-2"),
        repeated_residual_features=("branching",),
        evidence_pointers=("search:coverage", "failure:1", "failure:2"),
        artifact_hash="sha256:exhaustion",
    )
    spec = MissingTransformationSpecification(
        spec_id="missing-transform-1",
        target_obstruction_id="obs-target",
        residual_failure_ids=("failure-1", "failure-2"),
        must_preserve=("logical equivalence",),
        must_break=("branching",),
        must_expose=("compress local family into tractable global object",),
        must_reduce=("proof search branching factor",),
        allowed_representation_changes=("introduce auxiliary global object",),
        forbidden_shortcuts=("do not weaken theorem statement",),
        validation_obligations=("prove representation equivalence",),
        falsifiers=("counterexample showing lost target distinction",),
        evidence_pointers=("failure:1", "failure:2"),
        artifact_hash="sha256:missing-transform-1",
    )
    return ObstructionTransformationReview(
        review_id="shortcut-review-lift",
        target_atom_id="atom-C",
        target_context_hash="sha256:context",
        research_memory_review_hash="sha256:memory",
        episode_memory_snapshot_hash="sha256:episode-memory",
        obstruction=_target(),
        direct_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        jump_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        glue_search_status=RouteSearchStatus.NO_VIABLE_MATCH,
        selected_mode=ShortcutMode.LIFT,
        exhaustion_witness=exhaustion,
        missing_transformation_specification=spec,
        unresolved_warnings=("LIFT is a proposal specification, not a proof",),
        evidence_pointers=("shortcut:search-ladder",),
        artifact_hash="sha256:shortcut-lift",
    )


def test_lift_requires_search_jump_and_glue_exhaustion_plus_repeated_residual() -> None:
    assert _audit(_lift_review()).verdict is ShortcutReviewVerdict.PASS

    premature = replace(
        _lift_review(), direct_search_status=RouteSearchStatus.MATCHES_FOUND
    )
    report = _audit(premature)
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "lift_requires_direct_route_exhausted" in report.reasons


def test_lift_break_target_must_be_supported_by_repeated_residuals() -> None:
    review = _lift_review()
    assert review.missing_transformation_specification is not None
    unsupported = replace(
        review.missing_transformation_specification,
        must_break=("imagined feature absent from failures",),
    )
    report = _audit(
        replace(review, missing_transformation_specification=unsupported)
    )
    assert report.verdict is ShortcutReviewVerdict.FAIL
    assert "lift_spec_break_target_not_supported_by_repeated_residuals" in report.reasons


def test_shortcut_review_cannot_mint_candidate_route_when_unresolved() -> None:
    review = replace(
        _search_review(),
        selected_mode=ShortcutMode.CANNOT_CHECK,
        direct_search_status=RouteSearchStatus.NOT_RUN,
        direct_candidate_episode_ids=(),
        selected_episode_ids=(),
    )
    report = _audit(review)
    assert report.verdict is ShortcutReviewVerdict.CANNOT_CHECK
    assert not report.candidate_route_ready
