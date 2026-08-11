from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.evolution import EvolutionTrial, EvolutionVerdict
from rakl.evolution_archive import (
    RAKLVariant,
    EvolutionTrialAuthorityBindings,
    VariantStatus,
    initialize_evolution_archive,
    promote_incumbent,
    record_evolution_trial,
    register_challenger,
    evolution_trial_subject_hash,
    evolution_assurance_subject_hash,
    variant_promotion_subject_hash,
)
from rakl.experience_learning import ConsolidationVerdict, LessonConsolidationEvidence, assess_lesson_consolidation
from rakl.experience_learning import (
    lesson_to_research_tool,
    promoted_lesson_version,
    research_tool_content_bytes,
    research_tool_projection_preview,
)
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
    resolve_protected_attestation,
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
    with pytest.raises(ValueError, match="exact parent lesson"):
        add_lesson(ledger, forged)


def test_caller_generated_policy_key_and_attestation_cannot_enter_release_manifest() -> None:
    evidence = _artifact("attacker-evidence", b"attacker bytes", at="2026-08-11T08:00:00+00:00", producer="attacker")
    evaluator = _artifact("attacker-evaluator", b"attacker evaluator", at="2026-08-11T08:00:00+00:00", producer="attacker")
    attacker_key = b"attacker-controlled-key-material-over-32-bytes"
    forged = issue_protected_attestation(
        attestation_id="attacker-minted",
        purpose=AttestationPurpose.LOCAL_SECTION_VERIFICATION,
        subject_hash=sha256(b"forged-subject").hexdigest(),
        subject_frozen_at="2026-08-11T08:00:00+00:00",
        evaluator_artifact_id=evaluator.artifact_id,
        evaluator_artifact_sha256=evaluator.payload_sha256,
        evidence_bindings=((evidence.artifact_id, evidence.payload_sha256),),
        proposer_id="candidate",
        signer_id="attacker",
        issued_at="2026-08-11T08:10:00+00:00",
        verdict="PASS",
        signing_key=attacker_key,
    )
    attacker_context = ProtectedAuthorityContext(
        (evaluator, evidence),
        (forged,),
        AuthorityTrustPolicy((("attacker", attacker_key),)),
    )
    resolution = resolve_protected_attestation(
        attacker_context,
        forged.attestation_id,
        purpose=forged.purpose,
        subject_hash=forged.subject_hash,
        required_artifact_ids=(evidence.artifact_id,),
    )
    assert not resolution.valid
    assert "protected_attestation_not_in_release_manifest" in resolution.reasons


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

    evidence_packet = LessonConsolidationEvidence(
        supporting_episode_ids=("E1",),
        fresh_transfer_episode_ids=("E2",),
        verification_attestation_id="verify",
        transfer_attestation_id="transfer",
        authority_context=context,
    )
    resolved = assess_lesson_consolidation(
        ledger,
        candidate,
        evidence_packet,
    )
    assert resolved.verdict is ConsolidationVerdict.CONDITIONALLY_REUSABLE
    malicious_draft = replace(candidate, action="malicious different action", artifact_hash="")
    malicious = replace(malicious_draft, artifact_hash=sha256(lesson_content_bytes(malicious_draft)).hexdigest())
    with pytest.raises(ValueError, match="subject does not match exact candidate"):
        promoted_lesson_version(
            malicious,
            new_lesson_id="L-malicious",
            artifact_hash="ignored",
            report=resolved,
            evidence=LessonConsolidationEvidence(supporting_episode_ids=("E1",)),
        )
    with pytest.raises(ValueError, match="exact evidence packet"):
        promoted_lesson_version(
            candidate,
            new_lesson_id="L-reduced",
            artifact_hash="ignored",
            report=resolved,
            evidence=replace(evidence_packet, fresh_transfer_episode_ids=()),
        )
    preview = promoted_lesson_version(
        candidate,
        new_lesson_id="L2",
        artifact_hash="ignored",
        report=resolved,
        evidence=evidence_packet,
    )
    tool_preview = research_tool_projection_preview(
        preview, ledger, tool_id="T1", name="protected tool", kind="operator"
    )
    candidate_artifact = _artifact("lesson:L1", lesson_content_bytes(candidate), at="2026-08-11T08:10:00+00:00")
    promoted_artifact = _artifact("lesson:L2", lesson_content_bytes(preview), at="2026-08-11T08:14:00+00:00")
    tool_artifact = _artifact("tool:T1", research_tool_content_bytes(tool_preview), at="2026-08-11T08:15:00+00:00")
    tool_attestation = _attestation(
        AttestationPurpose.TOOL_PROJECTION,
        tool_preview.artifact_hash,
        (tool_artifact, promoted_artifact, candidate_artifact, source_artifact, transfer_artifact),
        attestation_id="tool-projection",
    )
    tool_context = _context(
        (tool_artifact, promoted_artifact, candidate_artifact, source_artifact, transfer_artifact),
        (verification, transfer_attestation, tool_attestation),
    )
    state = record_task_episode(record_task_episode(RAKLV3State(), source), transfer)
    consolidated = consolidate_lesson(
        state,
        candidate,
        evidence_packet,
        promoted_lesson_id="L2",
        promoted_artifact_hash="caller-string-is-not-authority",
        tool_spec=ToolProjectionSpec(
            "T1", "protected tool", "operator", (), "tool-projection", tool_context, "tool:T1"
        ),
    )
    assert consolidated.promoted_lesson_id == "L2"
    assert consolidated.projected_tool_id == "T1"
    assert consolidated.state.tools.tools[0].authority.value == "CONDITIONALLY_REUSABLE"
    assert consolidated.state.tools.tools[0].artifact_hash == tool_preview.artifact_hash
    assert f"source_lesson_sha256:{preview.artifact_hash}" in consolidated.state.tools.tools[0].evidence_pointers
    with pytest.raises(ValueError, match="exact content attestation"):
        consolidate_lesson(
            state,
            candidate,
            evidence_packet,
            promoted_lesson_id="L2",
            promoted_artifact_hash="ignored",
            tool_spec=ToolProjectionSpec(
                "T-evil", "arbitrary unreviewed tool", "different", (),
                "tool-projection", tool_context, "tool:T1"
            ),
        )
    reduced_draft = replace(
        preview,
        supporting_episode_ids=("E1",),
        artifact_hash="",
    )
    reduced = replace(
        reduced_draft,
        artifact_hash=sha256(lesson_content_bytes(reduced_draft)).hexdigest(),
    )
    with pytest.raises(ValueError, match="exact recorded lesson version"):
        lesson_to_research_tool(
            reduced,
            consolidated.state.experience,
            tool_id="T1",
            name="protected tool",
            kind="operator",
            authority_context=tool_context,
            projection_attestation_id="tool-projection",
            projection_artifact_id="tool:T1",
        )
    forged_final_draft = replace(preview, action="unreviewed operation", artifact_hash="")
    forged_final = replace(forged_final_draft, artifact_hash=sha256(lesson_content_bytes(forged_final_draft)).hexdigest())
    with pytest.raises(ValueError, match="changes unreviewed parent content"):
        add_lesson(add_lesson(ledger, candidate), forged_final, authority_context=context)

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
    section = replace(section_draft, subject_hash=local_section_subject_hash(section_draft, decomposition, atom))
    attestation = _attestation(
        AttestationPurpose.LOCAL_SECTION_VERIFICATION,
        local_section_subject_hash(section, decomposition, atom),
        (evidence,),
        attestation_id="section-check",
    )
    report = glue_local_sections(decomposition, (section,), authority_context=_context((evidence,), (attestation,)))
    assert report.grants_solution_authority
    pnp_atom = ProblemAtom("A1", "prove P=NP", "pnp", ("complexity",), ("proof",))
    pnp = ProblemDecomposition("P-vs-NP", (pnp_atom,))
    assert not glue_local_sections(pnp, (section,), authority_context=_context((evidence,), (attestation,))).grants_solution_authority


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

    dev = _artifact("development-benchmark", b"frozen development benchmark", at="2026-08-11T08:01:00+00:00")
    assurance_artifact = _artifact("assurance-benchmark", b"fresh assurance benchmark", at="2026-08-11T08:01:00+00:00")
    method = _artifact("candidate-method", b"v2", at="2026-08-11T08:02:00+00:00")
    receipt = _artifact("assurance-receipt", b"fresh matched assurance bytes", at="2026-08-11T08:10:00+00:00")
    bindings = EvolutionTrialAuthorityBindings(
        (dev.artifact_id, dev.payload_sha256),
        (assurance_artifact.artifact_id, assurance_artifact.payload_sha256),
        (method.artifact_id, method.payload_sha256),
        (receipt.artifact_id, receipt.payload_sha256),
    )
    assured = _attestation(
        AttestationPurpose.EVOLUTION_ASSURANCE,
        evolution_assurance_subject_hash(trial, bindings),
        (dev, assurance_artifact, method, receipt),
        attestation_id="assurance",
    )
    context = _context((dev, assurance_artifact, method, receipt), (assured,))
    archive3, assessment3 = record_evolution_trial(
        archive,
        trial_id="T-protected",
        child_variant_id="v2",
        trial=trial,
        authority_context=context,
        assurance_attestation_id="assurance",
        authority_bindings=bindings,
    )
    assert assessment3.supports_scoped_evolution
    assert next(v for v in archive3.variants if v.variant_id == "v2").status is VariantStatus.ASSURED
    governance = _attestation(
        AttestationPurpose.GOVERNANCE_PROMOTION,
        variant_promotion_subject_hash(archive3, "v2"),
        (receipt,),
        attestation_id="governance",
    )
    governance_context = _context((receipt,), (governance,))
    promoted = promote_incumbent(
        archive3,
        "v2",
        authority_context=governance_context,
        governance_attestation_id="governance",
    )
    assert promoted.incumbent_id == "v2"
    replay_variant = replace(next(v for v in archive3.variants if v.variant_id == "v2"), capability_tags=("different",))
    replay_archive = replace(archive3, variants=tuple(replay_variant if v.variant_id == "v2" else v for v in archive3.variants))
    with pytest.raises(ValueError, match="subject_mismatch"):
        promote_incumbent(
            replay_archive,
            "v2",
            authority_context=governance_context,
            governance_attestation_id="governance",
        )


def test_every_v3_module_and_authority_surface_has_a_canonical_method_owner() -> None:
    assert validate_v3_method_ownership() == ()
    assert "src/rakl/v3_authority.py" in V3_IMPLEMENTATION_OWNER_MAP
    assert V3_PUBLIC_AUTHORITY_SURFACE_OWNERS["promote_incumbent"] == "authority_promotion"
