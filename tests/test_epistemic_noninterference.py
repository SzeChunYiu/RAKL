"""Planted-world suite for the EPISTEMIC_NONINTERFERENCE invariant (refs #152).

Two frozen families:

* **benign worlds** — experience, routing, workspace, reflection and *method*
  authority all move; ``pi_auth`` must not. These must PASS.
* **leak worlds** — one per threat family, each of which must fail closed with
  its own distinct family and reason. A single catch-all failure reason would
  make a null result unattributable, which is the outcome this suite exists to
  prevent.

The suite also asserts anti-vacuity: an implementation that simply never moves
authority fails the legal-promotion control.
"""

from __future__ import annotations

import pytest

from rakl.authority_ledger import (
    AuthorityAxis,
    AuthorityLedger,
    AuthorityProposal,
    VerificationOutcome,
)
from rakl.epistemic_noninterference import (
    ComposedResearchState,
    bind_sources,
    EvidenceRoot,
    EvidenceRootKind,
    LeakFamily,
    NonAuthorityCoordinate,
    NoninterferenceStatus,
    Transition,
    TransitionKind,
    check_epistemic_noninterference,
    describe_integration_surface,
    pi_auth,
    pi_non_authority,
)
from rakl.experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
)

# --------------------------------------------------------------------------
# world builders
# --------------------------------------------------------------------------


def _episode(episode_id: str, outcome: EpisodeOutcome = EpisodeOutcome.SUCCESS) -> TaskEpisode:
    """A structurally valid episode. Short artifact hash skips digest binding,
    which this suite does not exercise (``test_rakl_v3_experience_substrate``
    owns that contract)."""

    return TaskEpisode(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="atom-1",
        context_hash="ctx-1",
        problem_signature=("sig",),
        fibre_snapshot_hash="fib-1",
        operator_ids=("op-a",),
        action_trace=("attempt",),
        observation_ids=("obs-1",),
        verification_ids=(),
        outcome=outcome,
        residual_signature=("residual",),
        evidence_pointers=("ptr-1",),
        artifact_hash=f"hash-{episode_id}",
        timestamp="2026-01-01T00:00:00Z",
    )


def _lesson(lesson_id: str, authority: LessonAuthority) -> Lesson:
    return Lesson(
        lesson_id=lesson_id,
        kind=LessonKind.ROUTING,
        trigger_signature=("sig",),
        context_scope=("scope",),
        action="prefer operator a",
        expected_effects=("faster route",),
        boundaries=("only in scope",),
        supporting_episode_ids=("ep-1",),
        contradicting_episode_ids=(),
        falsifier="operator a fails in scope",
        authority=authority,
        validation_obligations=("revalidate on scope change",),
        evidence_pointers=("ptr-1",),
        artifact_hash=f"hash-{lesson_id}",
    )


def _ledger_with(*grants: tuple[str, AuthorityAxis, str]) -> AuthorityLedger:
    ledger = AuthorityLedger()
    for index, (claim_id, axis, scope_id) in enumerate(grants):
        ledger.commit_verified(
            AuthorityProposal(
                proposal_id=f"prop-{index}",
                claim_id=claim_id,
                axis=axis,
                proposition=f"{claim_id} holds on {scope_id}",
                scope_id=scope_id,
                evidence_ids=("ev-1",),
            ),
            certificate_id=f"cert-{index}",
            outcome=VerificationOutcome.SUPPORTED,
        )
    return ledger


#: Registered evidence roots shared by the worlds below.
EXTERNAL_REPRESENTATION = EvidenceRoot(
    "obs-representation",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    frozenset({AuthorityAxis.REPRESENTATION}),
)
EXTERNAL_MECHANISM = EvidenceRoot(
    "obs-mechanism",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    frozenset({AuthorityAxis.REPRESENTATION, AuthorityAxis.MECHANISM}),
)
EPISODE_ROOT = EvidenceRoot("ep-1", EvidenceRootKind.TASK_EPISODE)
LESSON_ROOT = EvidenceRoot("lesson-1", EvidenceRootKind.LESSON)
#: Three reports that all descend from one experiment.
DERIVATIVES = (
    EvidenceRoot("paper-a", EvidenceRootKind.DERIVED_REPORT, frozenset({AuthorityAxis.MECHANISM}), "obs-mechanism"),
    EvidenceRoot("paper-b", EvidenceRootKind.DERIVED_REPORT, frozenset({AuthorityAxis.MECHANISM}), "obs-mechanism"),
    EvidenceRoot("paper-c", EvidenceRootKind.DERIVED_REPORT, frozenset({AuthorityAxis.MECHANISM}), "paper-a"),
)

BASE_ROOTS = (EXTERNAL_REPRESENTATION, EXTERNAL_MECHANISM, EPISODE_ROOT, LESSON_ROOT) + DERIVATIVES


def _state(
    *,
    episodes: tuple[str, ...] = (),
    lessons: tuple[tuple[str, LessonAuthority], ...] = (),
    ledger: AuthorityLedger | None = None,
    routing: tuple[tuple[str, float], ...] = (),
    access: tuple[tuple[str, int], ...] = (),
) -> ComposedResearchState:
    return ComposedResearchState(
        experience=ExperienceLedger(
            episodes=tuple(_episode(item) for item in episodes),
            lessons=tuple(_lesson(name, authority) for name, authority in lessons),
        ),
        authority=ledger,
        evidence_roots=BASE_ROOTS,
        routing_scores=routing,
        access_counts=access,
    )


#: The single pre-existing scientific grant every world starts from, so that an
#: authority ledger is composed and the check cannot trivially report
#: NO_INTEGRATION_SURFACE.
def _seed_ledger() -> AuthorityLedger:
    return _ledger_with(("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"))


# --------------------------------------------------------------------------
# benign worlds: experience changes behaviour, pi_auth is invariant
# --------------------------------------------------------------------------


def test_benign_experience_and_routing_changes_leave_authority_invariant() -> None:
    """Episodes, retrieval, routing, workspace and reflection all move; authority does not."""

    ledger = _seed_ledger()
    initial = _state(ledger=ledger)
    steps = (
        Transition("t1", TransitionKind.RECORD_EPISODE, _state(episodes=("ep-1",), ledger=ledger)),
        Transition("t2", TransitionKind.RETRIEVE, _state(episodes=("ep-1",), ledger=ledger, access=(("ep-1", 7),))),
        Transition(
            "t3",
            TransitionKind.UPDATE_ROUTING_POLICY,
            _state(episodes=("ep-1",), ledger=ledger, access=(("ep-1", 7),), routing=(("op-a", 0.9),)),
        ),
        Transition(
            "t4",
            TransitionKind.REFLECT,
            _state(episodes=("ep-1", "ep-2"), ledger=ledger, access=(("ep-1", 7),), routing=(("op-a", 0.9),)),
        ),
        Transition(
            "t5",
            TransitionKind.WORKSPACE_EVICT,
            _state(episodes=("ep-1", "ep-2"), ledger=ledger, routing=(("op-a", 0.9),)),
        ),
    )
    report = check_epistemic_noninterference(initial, steps)

    assert report.status is NoninterferenceStatus.PASS
    assert report.findings == ()
    assert report.checked_transitions == 5


def test_benign_world_actually_changes_behaviour_state() -> None:
    """Guards the benign control: a system that learns nothing would also pass
    the invariance assertion above, so assert the non-authority projection moved."""

    ledger = _seed_ledger()
    before = _state(ledger=ledger)
    after = _state(episodes=("ep-1",), ledger=ledger, access=(("ep-1", 7),), routing=(("op-a", 0.9),))

    assert pi_auth(before) == pi_auth(after)
    changed = {
        coordinate
        for coordinate in NonAuthorityCoordinate
        if pi_non_authority(before)[coordinate] != pi_non_authority(after)[coordinate]
    }
    assert NonAuthorityCoordinate.RETRIEVAL_PRIORITY in changed
    assert NonAuthorityCoordinate.COMPUTATIONAL_ACCESS in changed
    assert NonAuthorityCoordinate.STRATEGY_PREFERENCE in changed


def test_benign_method_authority_promotion_does_not_touch_scientific_authority() -> None:
    """A lesson legitimately promoted CANDIDATE -> VERIFIED_LOCAL is method
    authority. It must not register as a scientific-authority movement."""

    ledger = _seed_ledger()
    initial = _state(episodes=("ep-1",), lessons=(("lesson-1", LessonAuthority.CANDIDATE),), ledger=ledger)
    promoted = _state(
        episodes=("ep-1",),
        lessons=(("lesson-1", LessonAuthority.VERIFIED_LOCAL),),
        ledger=ledger,
    )
    report = check_epistemic_noninterference(
        initial, (Transition("t1", TransitionKind.CONSOLIDATE_LESSON, promoted),)
    )

    assert report.status is NoninterferenceStatus.PASS
    # ...and the method-authority coordinate really did move.
    assert (
        pi_non_authority(initial)[NonAuthorityCoordinate.LESSON_REUSE]
        != pi_non_authority(promoted)[NonAuthorityCoordinate.LESSON_REUSE]
    )


def test_legal_evidence_bearing_promotion_is_accepted() -> None:
    """The mandatory legal control. Without it, an implementation that never
    grants authority would pass every other test in this file."""

    ledger = _seed_ledger()
    after = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-1", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=ledger),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=after),
                claimed_evidence_root_ids=("obs-mechanism",),
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.PASS
    assert report.legal_promotions == 1


def test_registered_revocation_is_legal() -> None:
    """Refutation must be able to shrink the authority projection.

    Tightened at #242: the transition must now declare the *registered refuting
    evidence*. Before that, this control passed with no refuting evidence at all,
    which made it vacuous — it could not fail. See
    ``test_unattested_revocation_is_a_leak`` for the world it could not catch.
    """

    before = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after.revoke("cert-0", reason="counterexample observed in regime-A")

    report = check_epistemic_noninterference(
        _state(ledger=before),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=after),
                claimed_refutation_root_ids=("obs-mechanism",),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.PASS
    assert report.legal_revocations == 1


def test_unattested_revocation_is_a_leak() -> None:
    """``pi_auth`` is non-monotone, so withdrawal moves it exactly as minting does.

    Regression for a hole found while integrating #242 and verified against the
    pre-fix code: a revocation labelled ``EVIDENCE_BEARING_PROMOTION`` with a
    bare reason string produced zero findings and reported ``PASS``, because the
    promotion contract inspected only *added* grants.
    """

    before = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after.revoke("cert-0", reason="I changed my mind")

    report = check_epistemic_noninterference(
        _state(ledger=before),
        (Transition("t1", TransitionKind.EVIDENCE_BEARING_PROMOTION, _state(ledger=after)),),
    )
    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert report.families_detected() == frozenset({LeakFamily.UNATTESTED_REVOCATION})
    assert report.legal_revocations == 0


def test_experience_backed_revocation_is_still_a_leak() -> None:
    """A lesson or episode cannot refute a claim about nature either."""

    before = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after = _ledger_with(("claim-1", AuthorityAxis.MECHANISM, "regime-A"))
    after.revoke("cert-0", reason="our runs kept failing")

    report = check_epistemic_noninterference(
        _state(ledger=before),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=after),
                claimed_refutation_root_ids=("ep-1", "lesson-1"),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.UNATTESTED_REVOCATION in report.families_detected()


# --------------------------------------------------------------------------
# leak worlds: one per threat family, each failing closed with its own reason
# --------------------------------------------------------------------------


#: (transition kind, expected family) for leaks where a non-promotion
#: transition silently moves the authority projection.
_SILENT_LEAK_WORLDS = (
    (TransitionKind.RECORD_EPISODE, LeakFamily.EXPERIENCE_TO_EVIDENCE),
    (TransitionKind.RETRIEVE, LeakFamily.REPETITION_TO_AUTHORITY),
    (TransitionKind.UPDATE_ROUTING_POLICY, LeakFamily.ROUTING_TO_AUTHORITY),
    (TransitionKind.REFLECT, LeakFamily.REFLECTION_TO_AUTHORITY),
    (TransitionKind.RECORD_FAILURE, LeakFamily.FAILURE_TO_IMPOSSIBILITY),
    (TransitionKind.WORKSPACE_LOAD, LeakFamily.WORKSPACE_TO_AUTHORITY),
    (TransitionKind.SELF_EVOLUTION_WIN, LeakFamily.SELF_EVOLUTION_TO_AUTHORITY),
)


@pytest.mark.parametrize("kind,family", _SILENT_LEAK_WORLDS, ids=lambda value: getattr(value, "value", value))
def test_experience_side_transition_cannot_mint_authority(
    kind: TransitionKind, family: LeakFamily
) -> None:
    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-2", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (Transition("t1", kind, _state(ledger=escalated)),),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert report.families_detected() == frozenset({family})
    assert report.findings[0].added_grants


def test_experience_backed_promotion_is_authority_laundering() -> None:
    """The strongest leak world: a lesson whose *method* authority was legitimately
    earned is then used as the sole backing for a *scientific* authority grant."""

    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-2", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(lessons=(("lesson-1", LessonAuthority.PROOF_BACKED),), ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(lessons=(("lesson-1", LessonAuthority.PROOF_BACKED),), ledger=escalated),
                claimed_evidence_root_ids=("ep-1", "lesson-1"),
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.EXPERIENCE_TO_EVIDENCE in report.families_detected()


def test_derivative_sources_do_not_inflate_independent_evidence() -> None:
    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-2", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=escalated),
                claimed_evidence_root_ids=("paper-a", "paper-b", "paper-c"),
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.PROVENANCE_TO_INDEPENDENCE in report.families_detected()


def test_predictive_support_does_not_mint_mechanism_authority() -> None:
    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-1", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=escalated),
                claimed_evidence_root_ids=("obs-representation",),
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.PREDICTION_TO_MECHANISM in report.families_detected()


def test_mechanism_support_does_not_mint_identification_authority() -> None:
    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-1", AuthorityAxis.IDENTIFICATION, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=escalated),
                claimed_evidence_root_ids=("obs-mechanism",),
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.MECHANISM_TO_IDENTIFICATION in report.families_detected()


def test_self_attested_promotion_is_rejected() -> None:
    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-1", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                _state(ledger=escalated),
                claimed_evidence_root_ids=("obs-mechanism",),
                self_attested=True,
            ),
        ),
    )

    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.SELF_EVOLUTION_TO_AUTHORITY in report.families_detected()


def test_every_threat_family_has_a_planted_world() -> None:
    """Coverage guard: no threat family may be declared without a world that
    exercises it, otherwise a clean report would overstate what was tested."""

    exercised = {family for _, family in _SILENT_LEAK_WORLDS} | {
        LeakFamily.EXPERIENCE_TO_EVIDENCE,
        LeakFamily.PROVENANCE_TO_INDEPENDENCE,
        LeakFamily.PREDICTION_TO_MECHANISM,
        LeakFamily.MECHANISM_TO_IDENTIFICATION,
        LeakFamily.SELF_EVOLUTION_TO_AUTHORITY,
        # planted by test_unattested_revocation_is_a_leak and
        # test_experience_backed_revocation_is_still_a_leak (#242)
        LeakFamily.UNATTESTED_REVOCATION,
    }
    assert exercised == set(LeakFamily)


# --------------------------------------------------------------------------
# structural properties
# --------------------------------------------------------------------------


def test_mislabelling_a_promotion_does_not_evade_the_check() -> None:
    """Declaring a real promotion as retrieval fails harder, not softer."""

    escalated = _ledger_with(
        ("claim-1", AuthorityAxis.REPRESENTATION, "regime-A"),
        ("claim-1", AuthorityAxis.MECHANISM, "regime-A"),
    )
    report = check_epistemic_noninterference(
        _state(ledger=_seed_ledger()),
        (
            Transition(
                "t1",
                TransitionKind.RETRIEVE,
                _state(ledger=escalated),
                claimed_evidence_root_ids=("obs-mechanism",),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert report.families_detected() == frozenset({LeakFamily.REPETITION_TO_AUTHORITY})


def test_required_distinctions_are_not_collapsible() -> None:
    """The issue's non-collapsible list must remain separate coordinates."""

    assert len(set(NonAuthorityCoordinate)) == 6
    assert len(set(AuthorityAxis)) == 5
    overlap = {item.value for item in NonAuthorityCoordinate} & {
        item.name for item in AuthorityAxis
    }
    assert overlap == set()
    # Lesson reuse (method authority) is tracked, and is not an authority axis.
    assert NonAuthorityCoordinate.LESSON_REUSE.value not in {item.name for item in AuthorityAxis}


def test_uncomposed_state_reports_no_integration_surface_not_pass() -> None:
    """An absent channel is not an enforced invariant. Reporting PASS here would
    manufacture the result the operator explicitly forbade."""

    report = check_epistemic_noninterference(
        _state(),
        (Transition("t1", TransitionKind.RECORD_EPISODE, _state(episodes=("ep-1",))),),
    )
    assert report.status is NoninterferenceStatus.NO_INTEGRATION_SURFACE
    assert report.status is not NoninterferenceStatus.PASS
    assert not report.holds


def test_current_framework_revision_composes_an_integration_surface() -> None:
    """Structural audit of main, derived from the live dataclass.

    Inverted at #242. The prior assertion was ``composed is False``, with the
    documented intent that composing an authority ledger into the v3 state should
    fail that test as the signal to re-scope the invariant from prospective to
    enforced. That re-scope has now happened: ``RAKLV3State`` carries a
    ``ScientificAuthorityProjection``, so the leak channel is reachable and the
    invariant is exercised against a real surface.

    The historical negative finding is preserved verbatim in
    ``docs/EPISTEMIC_NONINTERFERENCE.md`` §9 rather than being overwritten.
    """

    surface = describe_integration_surface()
    assert surface.composed is True
    assert surface.authority_axis_carriers == ("scientific_authority",)
    assert "experience" in surface.v3_state_fields
    assert surface.reasons


def test_report_never_grants_authority() -> None:
    report = check_epistemic_noninterference(_state(ledger=_seed_ledger()), ())
    assert report.grants_authority is False


def test_noninterference_report_to_dict_validates_against_v2_schema() -> None:
    """Authority-boundary export must match the frozen JSON schema (#152, #242).

    Bumped to v2 at #242: the report gained ``legal_revocations`` and
    ``source_bindings``, and v1 declares ``additionalProperties: false``. v1
    stays on disk as the frozen contract for pre-#242 receipts.
    """

    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

    root = Path(__file__).resolve().parents[1]
    report = check_epistemic_noninterference(
        _state(),
        (Transition("t1", TransitionKind.RECORD_EPISODE, _state(episodes=("ep-1",))),),
    ).with_source_bindings(
        bind_sources(("src/rakl/epistemic_noninterference.py",), root=root)
    )
    payload = report.to_dict()
    schema_path = root / "schemas" / "epistemic-noninterference-report-v2.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    assert payload["grants_authority"] is False
    assert payload["status"] == "NO_INTEGRATION_SURFACE"
    assert payload["source_bindings"][0]["path"] == "src/rakl/epistemic_noninterference.py"


def test_schema_id_matches_its_filename() -> None:
    """Guards the copy-paste failure mode that previously blocked every PR."""

    import json
    from pathlib import Path

    schema_dir = Path(__file__).resolve().parents[1] / "schemas"
    for name in (
        "epistemic-noninterference-report-v1.schema.json",
        "epistemic-noninterference-report-v2.schema.json",
    ):
        schema = json.loads((schema_dir / name).read_text(encoding="utf-8"))
        assert schema["$id"].endswith("/" + name), name


def test_source_binding_refuses_to_silently_skip_a_missing_file() -> None:
    """A binding that quietly omits the file it claims to pin is worse than none."""

    from pathlib import Path

    with pytest.raises(FileNotFoundError):
        bind_sources(("src/rakl/does_not_exist.py",), root=Path(__file__).resolve().parents[1])
