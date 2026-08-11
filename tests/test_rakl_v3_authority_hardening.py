from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.evolution import EvolutionTrial, EvolutionVerdict
from rakl.evolution_archive import (
    RAKLVariant,
    VariantStatus,
    initialize_evolution_archive,
    promote_incumbent,
    record_evolution_trial,
    register_challenger,
    evolution_trial_subject_hash,
)
from rakl.experience_learning import ConsolidationVerdict, LessonConsolidationEvidence, assess_lesson_consolidation
from rakl.experience_substrate import (
    EpisodeOutcome,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    add_episode,
    add_lesson,
    episode_content_bytes,
    lesson_content_bytes,
)
from rakl.problem_fibre import LocalSection, ProblemAtom, ProblemDecomposition, glue_local_sections, local_section_subject_hash
from rakl.method_specs import V3_IMPLEMENTATION_OWNER_MAP, V3_PUBLIC_AUTHORITY_SURFACE_OWNERS, validate_v3_method_ownership
from rakl.v3_runtime import RAKLV3State, ToolProjectionSpec, consolidate_lesson, record_task_episode
from rakl.v3_authority import (
    AttestationPurpose,
    AuthorityTrustPolicy,
    EvidenceArtifact,
    ProtectedAttestation,
    ProtectedAuthorityContext,
    issue_protected_attestation,
)


KEY = b"protected-evaluator-key-material-32-bytes-minimum"
SIGNER = "protected-evaluator"
PROPOSER = "candidate-proposer"


def _artifact(artifact_id: str, payload: bytes, *, at: str, producer: str = "external-observer") -> EvidenceArtifact:
    return EvidenceArtifact(
        artifact_id=artifact_id,
        payload=payload,
        payload_sha256=sha256(payload).hexdigest(),
        frozen_at=at,
        producer_id=producer,
    )


def _context(artifacts: tuple[EvidenceArtifact, ...], attestations: tuple[ProtectedAttestation, ...]) -> ProtectedAuthorityContext:
    evaluator = _artifact("evaluator", b"protected evaluator v1", at="2026-08-11T08:00:00+00:00", producer=SIGNER)
    return ProtectedAuthorityContext(
        artifacts=(evaluator,) + artifacts,
        attestations=attestations,
        policy=AuthorityTrustPolicy(((SIGNER, KEY),)),
    )


def _episode(episode_id: str, *, outcome: EpisodeOutcome = EpisodeOutcome.SUCCESS, at: str = "2026-08-11T08:10:00+00:00") -> TaskEpisode:
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
        timestamp=at,
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _lesson(authority: LessonAuthority = LessonAuthority.CANDIDATE) -> Lesson:
    draft = Lesson(
        lesson_id="L1",
        kind=LessonKind.OPERATOR,
        trigger_signature=("structure",),
        context_scope=("ctx",),
        action="apply op",
        expected_effects=("progress",),
        boundaries=("scoped",),
        supporting_episode_ids=("E1",),
        contradicting_episode_ids=(),
        falsifier="counterexample",
        authority=authority,
        validation_obligations=("external replay",),
        evidence_pointers=("episode:E1",),
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


def _attestation(
    purpose: AttestationPurpose,
    subject_hash: str,
    artifacts: tuple[EvidenceArtifact, ...],
    *,
    attestation_id: str,
    issued_at: str = "2026-08-11T08:20:00+00:00",
) -> ProtectedAttestation:
    return issue_protected_attestation(
        attestation_id=attestation_id,
        purpose=purpose,
        subject_hash=subject_hash,
        subject_frozen_at="2026-08-11T08:10:00+00:00",
        evaluator_artifact_id="evaluator",
        evaluator_artifact_sha256=sha256(b"protected evaluator v1").hexdigest(),
        evidence_bindings=tuple((item.artifact_id, item.payload_sha256) for item in artifacts),
        proposer_id=PROPOSER,
        signer_id=SIGNER,
        issued_at=issued_at,
        verdict="PASS",
        signing_key=KEY,
    )


def test_episode_and_lesson_hashes_bind_exact_content_and_bare_authority_fails_closed() -> None:
    episode = _episode("E1")
    add_episode(ExperienceLedger(), episode)
    with pytest.raises(ValueError, match="artifact_hash_mismatch"):
        add_episode(ExperienceLedger(), replace(episode, action_trace=("changed",)))

    candidate = _lesson()
    ledger = add_episode(ExperienceLedger(), episode)
    add_lesson(ledger, candidate)
    forged_draft = replace(candidate, authority=LessonAuthority.PROOF_BACKED, artifact_hash="")
    forged = replace(forged_draft, artifact_hash=sha256(lesson_content_bytes(forged_draft)).hexdigest())
    with pytest.raises(ValueError, match="resolved protected authority attestation"):
        add_lesson(ledger, forged)


def test_consolidation_resolves_exact_evidence_evaluator_and_independence_not_bools() -> None:
    source = _episode("E1")
    transfer = _episode("E2", at="2026-08-11T08:11:00+00:00")
    ledger = add_episode(add_episode(ExperienceLedger(), source), transfer)
    candidate = _lesson()
    source_artifact = _artifact("episode:E1", episode_content_bytes(source), at=source.timestamp)
    transfer_artifact = _artifact("episode:E2", episode_content_bytes(transfer), at=transfer.timestamp)
    verification = _attestation(
        AttestationPurpose.LESSON_VERIFICATION,
        candidate.artifact_hash,
        (source_artifact,),
        attestation_id="verify",
    )
    transfer_attestation = _attestation(
        AttestationPurpose.LESSON_TRANSFER,
        candidate.artifact_hash,
        (source_artifact, transfer_artifact),
        attestation_id="transfer",
    )
    context = _context((source_artifact, transfer_artifact), (verification, transfer_attestation))

    caller_bools = assess_lesson_consolidation(
        ledger,
        candidate,
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_artifact_ids=("looks-real",),
            evaluator_separated=True,
            evidence_lineage_independent=True,
        ),
    )
    assert caller_bools.verdict is ConsolidationVerdict.CANNOT_CHECK
    caller_proof_ids = assess_lesson_consolidation(
        ledger,
        candidate,
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            verification_artifact_ids=("verification-label",),
            proof_certificate_ids=("proof-label",),
        ),
    )
    assert caller_proof_ids.verdict is ConsolidationVerdict.CANNOT_CHECK

    resolved = assess_lesson_consolidation(
        ledger,
        candidate,
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_attestation_id="verify",
            transfer_attestation_id="transfer",
            authority_context=context,
        ),
    )
    assert resolved.verdict is ConsolidationVerdict.CONDITIONALLY_REUSABLE
    state = record_task_episode(record_task_episode(RAKLV3State(), source), transfer)
    consolidated = consolidate_lesson(
        state,
        candidate,
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_attestation_id="verify",
            transfer_attestation_id="transfer",
            authority_context=context,
        ),
        promoted_lesson_id="L2",
        promoted_artifact_hash="caller-string-is-not-authority",
        tool_spec=ToolProjectionSpec("T1", "protected tool", "operator"),
    )
    assert consolidated.promoted_lesson_id == "L2"
    assert consolidated.projected_tool_id == "T1"
    assert consolidated.state.tools.tools[0].authority.value == "CONDITIONALLY_REUSABLE"

    forged_attestation = replace(transfer_attestation, signature="0" * 64)
    forged_context = _context((source_artifact, transfer_artifact), (verification, forged_attestation))
    rejected = assess_lesson_consolidation(
        ledger,
        candidate,
        LessonConsolidationEvidence(
            supporting_episode_ids=("E1",),
            fresh_transfer_episode_ids=("E2",),
            verification_attestation_id="verify",
            transfer_attestation_id="transfer",
            authority_context=forged_context,
        ),
    )
    assert rejected.verdict is ConsolidationVerdict.CANNOT_CHECK
    assert any("signature" in reason for reason in rejected.reasons)


def test_local_section_boolean_and_empty_evidence_never_grant_solution_authority() -> None:
    atom = ProblemAtom("A1", "solve", "ctx", ("x",), ("solve",))
    decomposition = ProblemDecomposition("P", (atom,))
    bare = LocalSection("S1", "A1", (("x", "1"),), (), ("op",), (), True)
    assert not glue_local_sections(decomposition, (bare,)).grants_solution_authority

    evidence = _artifact("section-evidence", b"formal checker receipt", at="2026-08-11T08:09:00+00:00")
    section_draft = replace(
        bare,
        evidence_ids=("section-evidence",),
        verification_attestation_id="section-check",
    )
    section = replace(section_draft, subject_hash=local_section_subject_hash(section_draft))
    attestation = _attestation(
        AttestationPurpose.LOCAL_SECTION_VERIFICATION,
        local_section_subject_hash(section),
        (evidence,),
        attestation_id="section-check",
    )
    report = glue_local_sections(decomposition, (section,), authority_context=_context((evidence,), (attestation,)))
    assert report.grants_solution_authority


def test_self_rakl_assurance_and_promotion_require_protected_attestations() -> None:
    parent = RAKLVariant("v1", sha256(b"v1").hexdigest(), (), ("research",), (("cost", 1.0),), (), VariantStatus.INCUMBENT)
    child = RAKLVariant("v2", sha256(b"v2").hexdigest(), ("v1",), ("research",), (("cost", 1.0),), ("E",), VariantStatus.CHALLENGER)
    archive = register_challenger(initialize_evolution_archive(parent), child)
    trial = EvolutionTrial(
        parent_version="v1",
        child_version="v2",
        development_benchmark_id="dev",
        development_improvements={"q": 0.1},
        assurance_benchmark_id="assurance",
        transfer_improvements={"q": 0.1},
        transfer_regressions={},
        assurance_benchmark_frozen_before_mutation=True,
        assurance_hidden_from_proposer=True,
        assurance_evaluator_separate=True,
        candidate_identity_verified=True,
        resource_comparability_verified=True,
    )
    archive2, assessment = record_evolution_trial(archive, trial_id="T", child_variant_id="v2", trial=trial)
    assert assessment.verdict is EvolutionVerdict.CANNOT_CHECK
    assert next(v for v in archive2.variants if v.variant_id == "v2").status is VariantStatus.CHALLENGER
    with pytest.raises(ValueError, match="protected governance attestation"):
        promote_incumbent(replace(archive2, variants=tuple(replace(v, status=VariantStatus.ASSURED) if v.variant_id == "v2" else v for v in archive2.variants)), "v2", governance_approved=True)

    receipt = _artifact("assurance-receipt", b"fresh matched assurance bytes", at="2026-08-11T08:10:00+00:00")
    assured = _attestation(
        AttestationPurpose.EVOLUTION_ASSURANCE,
        evolution_trial_subject_hash(trial),
        (receipt,),
        attestation_id="assurance",
    )
    governance = _attestation(
        AttestationPurpose.GOVERNANCE_PROMOTION,
        child.method_hash,
        (receipt,),
        attestation_id="governance",
    )
    context = _context((receipt,), (assured, governance))
    archive3, assessment3 = record_evolution_trial(
        archive,
        trial_id="T-protected",
        child_variant_id="v2",
        trial=trial,
        authority_context=context,
        assurance_attestation_id="assurance",
    )
    assert assessment3.supports_scoped_evolution
    assert next(v for v in archive3.variants if v.variant_id == "v2").status is VariantStatus.ASSURED
    promoted = promote_incumbent(
        archive3,
        "v2",
        authority_context=context,
        governance_attestation_id="governance",
    )
    assert promoted.incumbent_id == "v2"


def test_every_v3_module_and_authority_surface_has_a_canonical_method_owner() -> None:
    assert validate_v3_method_ownership() == ()
    assert "src/rakl/v3_authority.py" in V3_IMPLEMENTATION_OWNER_MAP
    assert V3_PUBLIC_AUTHORITY_SURFACE_OWNERS["promote_incumbent"] == "authority_promotion"
