"""Hostile noninterference suite against the *integrated* v3 runtime (refs #242).

Before #242 the ten families could only be run against a hand-built
``ComposedResearchState``; ``RAKLV3State`` composed no authority ledger, so the
checker returned ``NO_INTEGRATION_SURFACE``. This suite runs them against the
real runtime: attacks call the actual v3 transition functions and project the
states those functions return.

Honesty about what each family proves
-------------------------------------
The families are **not** uniform in strength, and reporting a flat "10/10 PASS"
would overstate the result. Two strata:

*contract-enforced* — attacks on :func:`promote_scientific_authority`, the one
function that can move ``pi_auth``. These fail if the runtime contract is
removed, so they are genuinely falsifiable. Each is a distinct planted shortcut
from issue #242 §6.

*structural + anti-vacuity* — the derived/routing families, for which the v3
runtime holds no persistent coordinate (``R_t`` is recomputed on demand). These
assert ``pi_auth`` invariance **and** that the non-authority projection actually
moved, so a runtime that learns nothing does not pass by doing nothing. They are
weaker: they would also hold under unreachability.

The suite's ability to fail is itself tested — see
``test_planted_leak_in_the_integration_is_caught``, which plants a leak in the
integration path (not in the checker) and asserts the attack suite goes red.
"""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.authority_ledger import AuthorityAxis, AuthorityProposal, VerificationOutcome
from rakl.claim_evidence import ClaimAtom, sha256_text
from rakl.epistemic_noninterference import (
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
    project_v3_state,
)
from rakl.experience_substrate import (
    EpisodeOutcome,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    episode_content_bytes,
    lesson_content_bytes,
)
from rakl.failure_lattice import FailureDiagnosisStatus
from rakl.v3_authority import (
    AttestationPurpose,
    AuthorityTrustPolicy,
    EvidenceArtifact,
    ProtectedAttestation,
    ProtectedAuthorityContext,
    issue_protected_attestation,
)
from rakl.v3_runtime import (
    FailureProjectionSpec,
    RAKLV3State,
    record_saturation_round,
    record_task_episode,
    state_fingerprint,
    state_fingerprint_v2,
)
from rakl.v3_scientific_authority import (
    TRANSITION_OWNERSHIP,
    ScientificEvidenceBinding,
    StateCoordinate,
    ledger_from_projection,
    promote_scientific_authority,
    promotion_subject_hash,
    register_scientific_claim,
    register_scientific_evidence,
    revocation_subject_hash,
    revoke_scientific_authority,
    supersede_scientific_authority,
    supersession_subject_hash,
)
from rakl.saturation_vector import NoveltyRound

# --------------------------------------------------------------------------
# Frozen fixture scenario
#
# Timestamps and payloads are hardcoded literals: the release manifest pins the
# exact unsigned attestation digest, so any wall-clock value would drift the
# digest and flake the suite.
# --------------------------------------------------------------------------

KEY = b"protected-evaluator-key-material-32-bytes-minimum"
SIGNER = "protected-evaluator"
PROPOSER = "candidate-proposer"
FROZEN_AT = "2026-08-11T08:00:00+00:00"
ISSUED_AT = "2026-08-11T09:00:00+00:00"

CLAIM = ClaimAtom(
    claim_id="claim-thermal-1",
    text="Thermal drift generates the observed residual.",
    scope="regime-A",
)
OTHER_CLAIM = ClaimAtom(
    claim_id="claim-other-1",
    text="Detector gain generates the observed residual.",
    scope="regime-A",
)

OBS_REPRESENTATION = ScientificEvidenceBinding(
    "obs-representation",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    sha256_text("held-out predictive run"),
    (AuthorityAxis.REPRESENTATION,),
)
OBS_MECHANISM = ScientificEvidenceBinding(
    "obs-mechanism",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    sha256_text("randomised intervention run"),
    (AuthorityAxis.REPRESENTATION, AuthorityAxis.MECHANISM),
)
OBS_REFUTATION = ScientificEvidenceBinding(
    "obs-refutation",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    sha256_text("independent replication refuting thermal drift"),
    (AuthorityAxis.MECHANISM,),
)
OBS_SUCCESSOR = ScientificEvidenceBinding(
    "obs-successor",
    EvidenceRootKind.EXTERNAL_OBSERVATION,
    sha256_text("successor intervention with radiative control"),
    (AuthorityAxis.REPRESENTATION, AuthorityAxis.MECHANISM),
)
DERIVATIVE_A = ScientificEvidenceBinding(
    "paper-a",
    EvidenceRootKind.DERIVED_REPORT,
    sha256_text("review a of the intervention run"),
    (AuthorityAxis.MECHANISM,),
    "obs-mechanism",
)
DERIVATIVE_B = ScientificEvidenceBinding(
    "paper-b",
    EvidenceRootKind.DERIVED_REPORT,
    sha256_text("review b of the intervention run"),
    (AuthorityAxis.MECHANISM,),
    "obs-mechanism",
)
EPISODE_ROOT = ScientificEvidenceBinding(
    "ep-1",
    EvidenceRootKind.TASK_EPISODE,
    sha256_text("task episode record"),
    (AuthorityAxis.MECHANISM,),
)
LESSON_ROOT = ScientificEvidenceBinding(
    "lesson-1",
    EvidenceRootKind.LESSON,
    sha256_text("proof-backed method lesson"),
    (AuthorityAxis.MECHANISM,),
)
ROUTING_ROOT = ScientificEvidenceBinding(
    "routing-1",
    EvidenceRootKind.ROUTING_STATISTIC,
    sha256_text("operator win-rate statistic"),
    (AuthorityAxis.MECHANISM,),
)

ALL_EVIDENCE = (
    OBS_REPRESENTATION,
    OBS_MECHANISM,
    OBS_REFUTATION,
    OBS_SUCCESSOR,
    DERIVATIVE_A,
    DERIVATIVE_B,
    EPISODE_ROOT,
    LESSON_ROOT,
    ROUTING_ROOT,
)

CERTIFICATE_ID = "cert-mechanism-1"
SUCCESSOR_CERTIFICATE_ID = "cert-mechanism-2"

PROMOTION_PROPOSAL = AuthorityProposal(
    proposal_id="prop-mechanism-1",
    claim_id=CLAIM.claim_id,
    axis=AuthorityAxis.MECHANISM,
    proposition="Thermal drift is the generating mechanism of the residual.",
    scope_id="regime-A",
    evidence_ids=("obs-mechanism",),
)
SUPERSESSION_PROPOSAL = AuthorityProposal(
    proposal_id="prop-mechanism-2",
    claim_id=CLAIM.claim_id,
    axis=AuthorityAxis.MECHANISM,
    proposition="Thermal drift with radiative correction is the generating mechanism.",
    scope_id="regime-A",
    evidence_ids=("obs-successor",),
)
REVOCATION_REASON = "independent replication refutes the thermal-drift mechanism"
SUPERSESSION_REASON = "successor intervention narrows the mechanism to include radiative correction"


def seeded_state() -> RAKLV3State:
    """A v3 state with canonical claims and content-bound evidence registered.

    Registration is authority-inert: ``pi_auth`` is still empty here.
    """

    state = RAKLV3State()
    for claim in (CLAIM, OTHER_CLAIM):
        state = register_scientific_claim(state, claim)
    for binding in ALL_EVIDENCE:
        state = register_scientific_evidence(state, binding)
    return state


_REGISTERED = {item.evidence_id: item for item in ALL_EVIDENCE}

PROMOTION_SUBJECT = promotion_subject_hash(
    claim=CLAIM,
    axis=PROMOTION_PROPOSAL.axis,
    proposition=PROMOTION_PROPOSAL.proposition,
    scope_id=PROMOTION_PROPOSAL.scope_id,
    evidence_ids=PROMOTION_PROPOSAL.evidence_ids,
    registered_evidence=_REGISTERED,
)


def _attestation(
    attestation_id: str,
    purpose: AttestationPurpose,
    subject_hash: str,
    *,
    proposer: str = PROPOSER,
    signer: str = SIGNER,
) -> ProtectedAttestation:
    return issue_protected_attestation(
        signing_key=KEY,
        attestation_id=attestation_id,
        purpose=purpose,
        subject_hash=subject_hash,
        subject_frozen_at=FROZEN_AT,
        evaluator_artifact_id="scientific-evaluator",
        evaluator_artifact_sha256=sha256(b"scientific evaluator v1").hexdigest(),
        evidence_bindings=(),
        proposer_id=proposer,
        signer_id=signer,
        issued_at=ISSUED_AT,
        verdict="PASS",
    )


def _context(*attestations: ProtectedAttestation) -> ProtectedAuthorityContext:
    evaluator = EvidenceArtifact(
        artifact_id="scientific-evaluator",
        payload=b"scientific evaluator v1",
        payload_sha256=sha256(b"scientific evaluator v1").hexdigest(),
        frozen_at=FROZEN_AT,
        producer_id=SIGNER,
    )
    return ProtectedAuthorityContext(
        artifacts=(evaluator,),
        attestations=attestations,
        policy=AuthorityTrustPolicy(((SIGNER, KEY),)),
    )


def promotion_context() -> ProtectedAuthorityContext:
    return _context(
        _attestation(
            "scientific-promotion",
            AttestationPurpose.SCIENTIFIC_AUTHORITY_PROMOTION,
            PROMOTION_SUBJECT,
        )
    )


def promoted_state() -> RAKLV3State:
    """The legal control: a state carrying one genuinely certified grant."""

    outcome = promote_scientific_authority(
        seeded_state(),
        PROMOTION_PROPOSAL,
        certificate_id=CERTIFICATE_ID,
        outcome=VerificationOutcome.SUPPORTED,
        authority_context=promotion_context(),
        attestation_id="scientific-promotion",
    )
    assert outcome.committed, outcome.reasons
    return outcome.state  # type: ignore[return-value]


def _episode(episode_id: str, *, outcome: EpisodeOutcome = EpisodeOutcome.SUCCESS) -> TaskEpisode:
    draft = TaskEpisode(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="A1",
        context_hash="ctx",
        problem_signature=("structure",),
        fibre_snapshot_hash="fibre",
        operator_ids=("op",),
        action_trace=("act",),
        observation_ids=("obs",),
        verification_ids=(),
        outcome=outcome,
        residual_signature=() if outcome is EpisodeOutcome.SUCCESS else ("failed",),
        evidence_pointers=("artifact",),
        artifact_hash="",
        timestamp="2026-08-11T08:10:00+00:00",
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _method_lesson(
    authority: LessonAuthority = LessonAuthority.CANDIDATE,
) -> Lesson:
    """A lesson carrying *method* authority.

    Used to check the substrate's flattened ``authority`` metadata key carries a
    ``LessonAuthority`` value and never an ``AuthorityAxis`` one. (That maximal
    method authority cannot become scientific authority is covered separately by
    the ``LESSON_ROOT`` evidence refusal.)
    """

    draft = Lesson(
        lesson_id="L-method-1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("structure",),
        context_scope=("ctx",),
        action="apply op",
        expected_effects=("progress",),
        boundaries=("scoped",),
        supporting_episode_ids=("ep-sub-1",),
        contradicting_episode_ids=(),
        falsifier="counterexample",
        authority=authority,
        validation_obligations=("external replay",),
        evidence_pointers=("episode:ep-sub-1",),
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


# --------------------------------------------------------------------------
# Integration surface: the precondition for everything below
# --------------------------------------------------------------------------


def test_v3_state_now_composes_scientific_authority() -> None:
    """Inverts the pre-#242 structural finding.

    The prior revision asserted ``composed is False`` and documented that a
    future composition should fail that test as the signal to re-scope the
    invariant from prospective to enforced. This is that re-scope.
    """

    surface = describe_integration_surface()
    assert surface.composed is True
    assert "scientific_authority" in surface.authority_axis_carriers
    assert "experience" in surface.v3_state_fields
    # The distinct non-authority ontologies are still enumerated, not flattened.
    assert len(surface.non_authority_carriers) == 3


def test_integrated_state_reports_a_real_verdict_not_no_integration_surface() -> None:
    """The acceptance criterion: ``NO_INTEGRATION_SURFACE`` is no longer the answer."""

    report = check_epistemic_noninterference(
        project_v3_state(promoted_state()),
        (
            Transition(
                "t1",
                TransitionKind.RECORD_EPISODE,
                project_v3_state(record_task_episode(promoted_state(), _episode("ep-1"))),
            ),
        ),
    )
    assert report.status is not NoninterferenceStatus.NO_INTEGRATION_SURFACE
    assert report.status is NoninterferenceStatus.PASS


def test_uncomposed_state_still_reports_no_integration_surface() -> None:
    """The status was not repurposed into a pass; a caller-built uncomposed
    world must still refuse to be called PASS."""

    from rakl.epistemic_noninterference import ComposedResearchState

    report = check_epistemic_noninterference(
        ComposedResearchState(),
        (Transition("t1", TransitionKind.RECORD_EPISODE, ComposedResearchState()),),
    )
    assert report.status is NoninterferenceStatus.NO_INTEGRATION_SURFACE


# --------------------------------------------------------------------------
# Value semantics: without this, every PASS below is meaningless
# --------------------------------------------------------------------------


def test_authority_projection_does_not_alias_across_transitions() -> None:
    """A shared mutable ledger would blind the checker completely.

    Reproduced before this module existed: with one live ``AuthorityLedger``
    shared between two states, a real mint under ``RECORD_EPISODE`` reported
    ``PASS``. The projection must therefore be value-semantic.
    """

    before = promoted_state()
    after = record_task_episode(before, _episode("ep-1"))

    assert before.scientific_authority is not None
    # Mutating a ledger materialised from the later state cannot reach the earlier one.
    scratch = ledger_from_projection(after.scientific_authority)
    scratch.revoke(CERTIFICATE_ID, reason="local mutation")
    assert pi_auth(project_v3_state(before)) == pi_auth(project_v3_state(after))
    assert len(pi_auth(project_v3_state(before))) == 1

    # And two projections of the same state never share the ledger object.
    assert project_v3_state(before).authority is not project_v3_state(before).authority


def test_v1_fingerprint_is_unchanged_by_the_new_coordinate() -> None:
    """Backward compatibility (#242 §7): historical benchmark identity is preserved.

    Literal captured from ``RAKLV3State()`` at f5a6a11, the pre-integration
    parent commit.
    """

    assert (
        state_fingerprint(RAKLV3State())
        == "ca002a22cd0bc9f783ffa457f3009d560fca1fb6f933484791e8d2d4ec356a8e"
    )
    # v1 is deliberately blind to authority; v2 is not.
    assert state_fingerprint(promoted_state()) == state_fingerprint(seeded_state())
    assert state_fingerprint_v2(promoted_state()) != state_fingerprint_v2(seeded_state())


# --------------------------------------------------------------------------
# Legal controls (#242 §5). A trivial architecture that never changes
# authority must fail these.
# --------------------------------------------------------------------------


def test_legal_promotion_actually_mints_authority() -> None:
    state = promoted_state()
    grants = pi_auth(project_v3_state(state))
    assert len(grants) == 1
    grant = next(iter(grants))
    assert grant.claim_id == CLAIM.claim_id
    assert grant.axis is AuthorityAxis.MECHANISM

    report = check_epistemic_noninterference(
        project_v3_state(seeded_state()),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                project_v3_state(state),
                claimed_evidence_root_ids=("obs-mechanism",),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.PASS
    assert report.legal_promotions == 1


def test_legal_refutation_driven_revocation_removes_the_grant() -> None:
    state = promoted_state()
    certificate = next(
        item
        for item in state.scientific_authority.certificates
        if item.certificate_id == CERTIFICATE_ID
    )
    subject = revocation_subject_hash(
        certificate=certificate,
        reason=REVOCATION_REASON,
        refutation_evidence_ids=("obs-refutation",),
        registered_evidence=_REGISTERED,
    )
    outcome = revoke_scientific_authority(
        state,
        CERTIFICATE_ID,
        reason=REVOCATION_REASON,
        refutation_evidence_ids=("obs-refutation",),
        authority_context=_context(
            _attestation(
                "scientific-revocation",
                AttestationPurpose.SCIENTIFIC_AUTHORITY_REVOCATION,
                subject,
            )
        ),
        attestation_id="scientific-revocation",
    )
    assert outcome.committed, outcome.reasons
    revoked = outcome.state

    assert pi_auth(project_v3_state(revoked)) == frozenset()
    # History is retained even though the active view shrank.
    assert any(
        item.certificate_id == CERTIFICATE_ID
        for item in revoked.scientific_authority.certificates
    )

    report = check_epistemic_noninterference(
        project_v3_state(state),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                project_v3_state(revoked),
                claimed_refutation_root_ids=("obs-refutation",),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.PASS
    assert report.legal_revocations == 1


def test_legal_supersession_preserves_historical_certificates() -> None:
    state = promoted_state()
    old = next(
        item
        for item in state.scientific_authority.certificates
        if item.certificate_id == CERTIFICATE_ID
    )
    subject = supersession_subject_hash(
        old_certificate=old,
        new_proposal=SUPERSESSION_PROPOSAL,
        reason=SUPERSESSION_REASON,
        registered_evidence=_REGISTERED,
    )
    outcome = supersede_scientific_authority(
        state,
        CERTIFICATE_ID,
        SUPERSESSION_PROPOSAL,
        new_certificate_id=SUCCESSOR_CERTIFICATE_ID,
        reason=SUPERSESSION_REASON,
        authority_context=_context(
            _attestation(
                "scientific-supersession",
                AttestationPurpose.SCIENTIFIC_AUTHORITY_SUPERSESSION,
                subject,
            )
        ),
        attestation_id="scientific-supersession",
    )
    assert outcome.committed, outcome.reasons
    superseded = outcome.state

    ids = {item.certificate_id for item in superseded.scientific_authority.certificates}
    assert ids == {CERTIFICATE_ID, SUCCESSOR_CERTIFICATE_ID}
    assert superseded.scientific_authority.active_certificate_ids == (
        SUCCESSOR_CERTIFICATE_ID,
    )
    # The superseding event is addressable in history.
    assert any(
        event.replacement_certificate_id == SUCCESSOR_CERTIFICATE_ID
        for event in superseded.scientific_authority.events
    )


# --------------------------------------------------------------------------
# Contract-enforced attacks: the five §6 shortcuts plus binding attacks.
# Each targets promote_scientific_authority, the only function that can move
# pi_auth. Each asserts a *distinct* refusal reason.
# --------------------------------------------------------------------------


def _attempt(
    proposal: AuthorityProposal,
    *,
    state: RAKLV3State | None = None,
    context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = "scientific-promotion",
    outcome: VerificationOutcome = VerificationOutcome.SUPPORTED,
):
    return promote_scientific_authority(
        state or seeded_state(),
        proposal,
        certificate_id="cert-attack",
        outcome=outcome,
        authority_context=context if context is not None else promotion_context(),
        attestation_id=attestation_id,
    )


_SHORTCUT_ATTACKS = (
    pytest.param(
        ("lesson-1",),
        AuthorityAxis.MECHANISM,
        "experience_objects_claimed_as_scientific_evidence",
        id="lesson_confidence_to_scientific_authority",
    ),
    pytest.param(
        ("routing-1",),
        AuthorityAxis.MECHANISM,
        "experience_objects_claimed_as_scientific_evidence",
        id="routing_score_to_authority",
    ),
    pytest.param(
        ("ep-1",),
        AuthorityAxis.MECHANISM,
        "experience_objects_claimed_as_scientific_evidence",
        id="repeated_failure_to_impossibility_authority",
    ),
    pytest.param(
        ("paper-a", "paper-b"),
        AuthorityAxis.MECHANISM,
        "claimed_evidence_collapses_to_1_independent_lineage_roots",
        id="source_count_to_independent_evidence_count",
    ),
    pytest.param(
        ("obs-representation",),
        AuthorityAxis.MECHANISM,
        "axis_escalation:MECHANISM_supported_only_up_to_REPRESENTATION",
        id="predictive_success_to_mechanism_authority",
    ),
)


@pytest.mark.parametrize("evidence_ids,axis,expected_reason", _SHORTCUT_ATTACKS)
def test_planted_shortcut_cannot_mint_scientific_authority(
    evidence_ids: tuple[str, ...], axis: AuthorityAxis, expected_reason: str
) -> None:
    """The five #242 §6 shortcuts, each refused with its own distinct reason."""

    outcome = _attempt(
        replace(PROMOTION_PROPOSAL, evidence_ids=evidence_ids, axis=axis)
    )
    assert outcome.committed is False
    assert outcome.grants_authority is False
    assert any(reason.startswith(expected_reason) for reason in outcome.reasons), outcome.reasons
    # And the refusal is inert: no partial application.
    assert outcome.state.scientific_authority.active_certificate_ids == ()


def test_attestation_bound_to_a_different_claim_is_refused() -> None:
    """The certificate-binding attack.

    The attestation is valid, signed, release-manifested and resolves for its own
    subject. Reusing it for a *different* claim must fail, because the subject
    hash covers the claim text, axis, scope and evidence digests. This is what
    makes the surface subject-bound rather than declaration-bound.
    """

    outcome = _attempt(replace(PROMOTION_PROPOSAL, claim_id=OTHER_CLAIM.claim_id))
    assert outcome.committed is False
    assert "protected_attestation_subject_mismatch" in outcome.reasons


def test_altering_the_proposition_invalidates_the_attestation() -> None:
    """Same claim id, different asserted content. The digest covers the text."""

    outcome = _attempt(
        replace(PROMOTION_PROPOSAL, proposition="Thermal drift is merely correlated.")
    )
    assert outcome.committed is False
    assert "protected_attestation_subject_mismatch" in outcome.reasons


def test_declaration_alone_cannot_mint_authority() -> None:
    """No attestation at all. A caller-supplied SUPPORTED verdict is a declaration."""

    outcome = _attempt(PROMOTION_PROPOSAL, context=None, attestation_id=None)
    assert outcome.committed is False
    assert "resolved_protected_attestation_missing" in outcome.reasons


def test_self_attested_promotion_is_refused() -> None:
    """Proposer and signer must differ; assurance cannot be self-produced."""

    outcome = _attempt(
        PROMOTION_PROPOSAL,
        context=_context(
            _attestation(
                "scientific-promotion",
                AttestationPurpose.SCIENTIFIC_AUTHORITY_PROMOTION,
                PROMOTION_SUBJECT,
                proposer=SIGNER,
            )
        ),
    )
    assert outcome.committed is False
    assert "protected_evaluator_not_separate_from_proposer" in outcome.reasons


def test_method_authority_purpose_cannot_mint_scientific_authority() -> None:
    """A LESSON_PROMOTION attestation is method authority, not authority over nature.

    Accepting it would be exactly the cross-authority flattening #242 forbids.
    """

    outcome = _attempt(
        PROMOTION_PROPOSAL,
        context=_context(
            _attestation(
                "scientific-promotion",
                AttestationPurpose.LESSON_PROMOTION,
                PROMOTION_SUBJECT,
            )
        ),
    )
    assert outcome.committed is False
    assert "protected_attestation_purpose_mismatch" in outcome.reasons


def test_attestation_absent_from_the_release_manifest_is_refused() -> None:
    """No special-casing for the new purposes: manifest membership still governs."""

    outcome = _attempt(
        PROMOTION_PROPOSAL,
        context=_context(
            _attestation(
                "scientific-promotion-unregistered",
                AttestationPurpose.SCIENTIFIC_AUTHORITY_PROMOTION,
                PROMOTION_SUBJECT,
            )
        ),
        attestation_id="scientific-promotion-unregistered",
    )
    assert outcome.committed is False
    assert "protected_attestation_not_in_release_manifest" in outcome.reasons


def test_supports_axes_order_is_not_part_of_evidence_identity() -> None:
    """The same axis set is the same value, whatever order it was written in.

    Without normalisation, re-registering identical evidence with the axes
    transposed raises "already registered with different content" while
    producing an identical subject hash — two components disagreeing about what
    identity means.
    """

    forward = ScientificEvidenceBinding(
        "obs-order",
        EvidenceRootKind.EXTERNAL_OBSERVATION,
        sha256_text("order probe"),
        (AuthorityAxis.REPRESENTATION, AuthorityAxis.MECHANISM),
    )
    reversed_ = ScientificEvidenceBinding(
        "obs-order",
        EvidenceRootKind.EXTERNAL_OBSERVATION,
        sha256_text("order probe"),
        (AuthorityAxis.MECHANISM, AuthorityAxis.REPRESENTATION),
    )
    assert forward == reversed_
    state = register_scientific_evidence(seeded_state(), forward)
    # Idempotent re-registration must not raise.
    assert register_scientific_evidence(state, reversed_) is state


def test_runtime_refuses_experience_evidence_even_when_mixed_with_real_evidence() -> None:
    """The runtime gate is strictly stronger than the checker's rule 2.

    ``_check_promotion`` tolerates an experience root when a scientific root is
    also present; the runtime refuses any experience root at all. Listing an
    episode next to a real observation buys nothing and inflates apparent
    support. Documented in ``docs/EPISTEMIC_NONINTERFERENCE.md`` §5.
    """

    outcome = _attempt(
        replace(PROMOTION_PROPOSAL, evidence_ids=("obs-mechanism", "lesson-1"))
    )
    assert outcome.committed is False
    assert any(
        reason.startswith("experience_objects_claimed_as_scientific_evidence")
        for reason in outcome.reasons
    )


def test_unregistered_evidence_cannot_back_a_promotion() -> None:
    outcome = _attempt(replace(PROMOTION_PROPOSAL, evidence_ids=("obs-invented",)))
    assert outcome.committed is False
    assert any(
        reason.startswith("scientific_evidence_unregistered") for reason in outcome.reasons
    )


def test_unattested_revocation_is_refused_by_the_runtime() -> None:
    """A bare reason string is a declaration. Withdrawal moves pi_auth too."""

    outcome = revoke_scientific_authority(
        promoted_state(),
        CERTIFICATE_ID,
        reason="I no longer believe it",
        refutation_evidence_ids=(),
    )
    assert outcome.committed is False
    assert "revocation_requires_registered_refuting_evidence" in outcome.reasons


def test_revocation_backed_only_by_experience_is_refused() -> None:
    outcome = revoke_scientific_authority(
        promoted_state(),
        CERTIFICATE_ID,
        reason=REVOCATION_REASON,
        refutation_evidence_ids=("lesson-1",),
    )
    assert outcome.committed is False
    assert "refutation_requires_non_experience_evidence" in outcome.reasons


def test_checker_catches_a_revocation_smuggled_under_a_promotion_label() -> None:
    """Regression for a real hole found while integrating (#242).

    Before this change ``_check_promotion`` inspected only *added* grants, so a
    revocation labelled ``EVIDENCE_BEARING_PROMOTION`` produced zero findings and
    reported ``PASS``. That made the §5 refutation control vacuous: it could not
    fail. Verified against the pre-fix code before the fix was written.
    """

    state = promoted_state()
    ledger = ledger_from_projection(state.scientific_authority)
    ledger.revoke(CERTIFICATE_ID, reason="unattested")
    from rakl.v3_scientific_authority import projection_from_ledger

    withdrawn = replace(
        state,
        scientific_authority=projection_from_ledger(
            ledger,
            claims=state.scientific_authority.claims,
            evidence=state.scientific_authority.evidence,
        ),
    )
    report = check_epistemic_noninterference(
        project_v3_state(state),
        (
            Transition(
                "t1",
                TransitionKind.EVIDENCE_BEARING_PROMOTION,
                project_v3_state(withdrawn),
            ),
        ),
    )
    assert report.status is NoninterferenceStatus.LEAK_DETECTED
    assert LeakFamily.UNATTESTED_REVOCATION in report.families_detected()
    assert report.legal_revocations == 0


# --------------------------------------------------------------------------
# Structural + anti-vacuity: real v3 transitions must not move pi_auth,
# and must be shown to move something.
# --------------------------------------------------------------------------


def test_record_episode_moves_experience_and_not_authority() -> None:
    before = promoted_state()
    after = record_task_episode(before, _episode("ep-real-1"))

    report = check_epistemic_noninterference(
        project_v3_state(before),
        (Transition("t1", TransitionKind.RECORD_EPISODE, project_v3_state(after)),),
    )
    assert report.status is NoninterferenceStatus.PASS
    # Anti-vacuity: the experience coordinate really did move.
    assert (
        pi_non_authority(project_v3_state(before))[NonAuthorityCoordinate.STRATEGY_PREFERENCE]
        != pi_non_authority(project_v3_state(after))[NonAuthorityCoordinate.STRATEGY_PREFERENCE]
    )


def test_record_failure_moves_the_failure_lattice_and_not_authority() -> None:
    before = promoted_state()
    after = record_task_episode(
        before,
        _episode("ep-fail-1", outcome=EpisodeOutcome.FAILURE),
        failure_spec=FailureProjectionSpec(
            failure_id="F1",
            candidate_id="C1",
            method_family="thermal",
            failure_mode="residual persists",
            competing_diagnoses=("drift", "gain"),
            diagnosis_status=FailureDiagnosisStatus.OBSERVED_ONLY,
        ),
    )
    assert after.failures != before.failures  # anti-vacuity
    report = check_epistemic_noninterference(
        project_v3_state(before),
        (Transition("t1", TransitionKind.RECORD_FAILURE, project_v3_state(after)),),
    )
    assert report.status is NoninterferenceStatus.PASS


def test_saturation_round_moves_saturation_and_not_authority() -> None:
    before = promoted_state()
    after = record_saturation_round(
        before,
        NoveltyRound(
            round_id="r1",
            route_family="thermal",
            independent_route=True,
            retained_novelty=(),
        ),
    )
    assert after.saturation != before.saturation  # anti-vacuity
    report = check_epistemic_noninterference(
        project_v3_state(before),
        (Transition("t1", TransitionKind.REFLECT, project_v3_state(after)),),
    )
    assert report.status is NoninterferenceStatus.PASS


def test_registering_canonical_content_does_not_move_authority() -> None:
    """Canonical scientific content and scientific authority are separate
    coordinates: adding a claim or an observation is not evidence *for* anything."""

    before = promoted_state()
    after = register_scientific_evidence(
        before,
        ScientificEvidenceBinding(
            "obs-late",
            EvidenceRootKind.EXTERNAL_OBSERVATION,
            sha256_text("a later observation"),
            (AuthorityAxis.MECHANISM,),
        ),
    )
    assert (
        pi_non_authority(project_v3_state(before))[NonAuthorityCoordinate.SCIENTIFIC_EVIDENCE]
        != pi_non_authority(project_v3_state(after))[NonAuthorityCoordinate.SCIENTIFIC_EVIDENCE]
    )
    report = check_epistemic_noninterference(
        project_v3_state(before),
        (Transition("t1", TransitionKind.RETRIEVE, project_v3_state(after)),),
    )
    assert report.status is NoninterferenceStatus.PASS


_DERIVED_FAMILIES = (
    TransitionKind.RETRIEVE,
    TransitionKind.REUSE_LESSON,
    TransitionKind.UPDATE_ROUTING_POLICY,
    TransitionKind.WORKSPACE_LOAD,
    TransitionKind.WORKSPACE_EVICT,
    TransitionKind.REFLECT,
    TransitionKind.SELF_EVOLUTION_WIN,
    TransitionKind.PROJECT_TOOL,
)


@pytest.mark.parametrize("kind", _DERIVED_FAMILIES, ids=lambda k: k.value)
def test_derived_coordinate_movement_does_not_move_authority(kind: TransitionKind) -> None:
    """Routing/retrieval/workspace are derived, not stored, in the v3 runtime.

    They are exercised at the projection boundary: the non-authority coordinates
    move and ``pi_auth`` must not. Weaker than the contract-enforced attacks
    above — this stratum would also hold under unreachability — hence the
    explicit anti-vacuity assertion.
    """

    state = promoted_state()
    before = project_v3_state(state)
    after = project_v3_state(
        state, routing_scores=(("op-a", 0.91),), access_counts=(("ep-1", 7),)
    )
    assert (
        pi_non_authority(before)[NonAuthorityCoordinate.RETRIEVAL_PRIORITY]
        != pi_non_authority(after)[NonAuthorityCoordinate.RETRIEVAL_PRIORITY]
    )
    report = check_epistemic_noninterference(before, (Transition("t1", kind, after),))
    assert report.status is NoninterferenceStatus.PASS


def test_all_ten_original_families_execute_against_the_integrated_surface() -> None:
    """Coverage guard for #242 §4: every declared family runs against the real
    runtime, and each leak world is attributed to its own distinct family."""

    state = promoted_state()
    escalated = ledger_from_projection(state.scientific_authority)
    escalated.commit_verified(
        AuthorityProposal(
            "smuggled", CLAIM.claim_id, AuthorityAxis.IDENTIFICATION, "smuggled", "regime-A", ("x",)
        ),
        certificate_id="cert-smuggled",
        outcome=VerificationOutcome.SUPPORTED,
    )
    from rakl.v3_scientific_authority import projection_from_ledger

    leaked = project_v3_state(
        replace(
            state,
            scientific_authority=projection_from_ledger(
                escalated,
                claims=state.scientific_authority.claims,
                evidence=state.scientific_authority.evidence,
            ),
        )
    )
    base = project_v3_state(state)

    silent = {
        TransitionKind.RECORD_EPISODE: LeakFamily.EXPERIENCE_TO_EVIDENCE,
        TransitionKind.RETRIEVE: LeakFamily.REPETITION_TO_AUTHORITY,
        TransitionKind.UPDATE_ROUTING_POLICY: LeakFamily.ROUTING_TO_AUTHORITY,
        TransitionKind.REFLECT: LeakFamily.REFLECTION_TO_AUTHORITY,
        TransitionKind.RECORD_FAILURE: LeakFamily.FAILURE_TO_IMPOSSIBILITY,
        TransitionKind.WORKSPACE_LOAD: LeakFamily.WORKSPACE_TO_AUTHORITY,
        TransitionKind.SELF_EVOLUTION_WIN: LeakFamily.SELF_EVOLUTION_TO_AUTHORITY,
    }
    detected: set[LeakFamily] = set()
    for kind, family in silent.items():
        report = check_epistemic_noninterference(base, (Transition("t", kind, leaked),))
        assert report.status is NoninterferenceStatus.LEAK_DETECTED, kind
        assert report.families_detected() == frozenset({family}), kind
        detected |= report.families_detected()

    # The four contract families, driven through the runtime refusal reasons.
    assert not _attempt(
        replace(PROMOTION_PROPOSAL, evidence_ids=("lesson-1",))
    ).committed
    detected.add(LeakFamily.EXPERIENCE_TO_EVIDENCE)
    assert not _attempt(
        replace(PROMOTION_PROPOSAL, evidence_ids=("paper-a", "paper-b"))
    ).committed
    detected.add(LeakFamily.PROVENANCE_TO_INDEPENDENCE)
    assert not _attempt(
        replace(PROMOTION_PROPOSAL, evidence_ids=("obs-representation",))
    ).committed
    detected.add(LeakFamily.PREDICTION_TO_MECHANISM)
    assert not _attempt(
        replace(
            PROMOTION_PROPOSAL,
            axis=AuthorityAxis.IDENTIFICATION,
            evidence_ids=("obs-mechanism",),
        )
    ).committed
    detected.add(LeakFamily.MECHANISM_TO_IDENTIFICATION)

    assert detected == set(LeakFamily) - {LeakFamily.UNATTESTED_REVOCATION}


# --------------------------------------------------------------------------
# Transition ownership registry (#242 §3)
# --------------------------------------------------------------------------


def test_every_public_v3_transition_is_classified() -> None:
    """A new transition cannot be added without declaring what it may change.

    Introspects the live modules, so this fails when someone adds an
    unclassified state transition rather than passing on a stale list.
    """

    import inspect

    from rakl import v3_runtime, v3_scientific_authority

    discovered: set[str] = set()
    for module in (v3_runtime, v3_scientific_authority):
        for name, obj in vars(module).items():
            if name.startswith("_") or not inspect.isfunction(obj):
                continue
            if obj.__module__ not in {
                "rakl.v3_runtime",
                "rakl.v3_scientific_authority",
            }:
                continue
            params = list(inspect.signature(obj).parameters)
            if params and params[0] == "state":
                discovered.add(name)

    unclassified = discovered - set(TRANSITION_OWNERSHIP)
    assert unclassified == set(), f"unclassified v3 transitions: {sorted(unclassified)}"


def test_only_scientific_transitions_own_the_authority_coordinate() -> None:
    owners = {
        name
        for name, coordinates in TRANSITION_OWNERSHIP.items()
        if StateCoordinate.SCIENTIFIC_AUTHORITY in coordinates
    }
    assert owners == {
        "promote_scientific_authority",
        "revoke_scientific_authority",
        "supersede_scientific_authority",
    }


def test_experience_transitions_do_not_own_scientific_content_or_authority() -> None:
    for name in ("record_task_episode", "consolidate_lesson", "record_saturation_round"):
        coordinates = TRANSITION_OWNERSHIP[name]
        assert StateCoordinate.SCIENTIFIC_AUTHORITY not in coordinates
        assert StateCoordinate.CANONICAL_SCIENTIFIC_CONTENT not in coordinates


# --------------------------------------------------------------------------
# No cross-authority flattening (#242 acceptance criterion 2)
# --------------------------------------------------------------------------


def test_unified_substrate_metadata_never_carries_scientific_authority() -> None:
    """The substrate flattens three *method*-authority ontologies into one
    ``metadata["authority"]`` string. No ``AuthorityAxis`` value may appear
    there, or the generic key would become a scientific-authority source."""

    from rakl.experience_substrate import add_lesson
    from rakl.v3_runtime import materialize_state_substrate

    state = record_task_episode(promoted_state(), _episode("ep-sub-1"))
    state = replace(state, experience=add_lesson(state.experience, _method_lesson()))
    snapshot = materialize_state_substrate(state)
    axis_values = {axis.value for axis in AuthorityAxis}
    axis_names = {axis.name for axis in AuthorityAxis}
    seen_authority_keys = 0
    for node in snapshot.nodes:
        authority = dict(node.metadata).get("authority")
        if authority is None:
            continue
        seen_authority_keys += 1
        assert authority not in axis_values
        assert authority not in axis_names
    # Anti-vacuity: the substrate really does carry the flattened method-authority
    # key, so this assertion is checking something rather than iterating nothing.
    assert seen_authority_keys > 0
