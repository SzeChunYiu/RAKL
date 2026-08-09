from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class FrozenEvaluatorSpec:
    """Content-addressed definition of the evaluator allowed to judge a challenger.

    The spec is intentionally about the *judge*, not the candidate under test.
    It binds the evaluator revision, all known evaluator-influencing inputs, the
    execution definition and the allowed builder identities.  A candidate may add
    supplemental tests, but those additions cannot substitute for the frozen judge.
    """

    evaluator_revision_sha: str
    protected_input_fingerprints: Mapping[str, str]
    command_fingerprint: str
    environment_spec_fingerprint: str
    authorized_builder_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.evaluator_revision_sha:
            raise ValueError("evaluator_revision_sha cannot be empty")
        if not self.protected_input_fingerprints:
            raise ValueError("at least one protected evaluator input is required")
        if not self.command_fingerprint:
            raise ValueError("command_fingerprint cannot be empty")
        if not self.environment_spec_fingerprint:
            raise ValueError("environment_spec_fingerprint cannot be empty")
        if not self.authorized_builder_ids:
            raise ValueError("at least one authorized builder is required")


@dataclass(frozen=True)
class EvaluationAttestation:
    """Externally observed receipt for one candidate evaluation.

    This mirrors the useful separation in supply-chain attestations between the
    subject being evaluated and the materials/command/environment used by the
    builder.  ``material_fingerprints`` may contain extra candidate-provided
    artifacts, but every frozen protected input must be present and unchanged.
    """

    candidate_sha: str
    evaluator_revision_sha: str
    material_fingerprints: Mapping[str, str]
    command_fingerprint: str
    environment_spec_fingerprint: str
    builder_id: str
    check_name: str
    conclusion: str
    externally_observed: bool = True


@dataclass(frozen=True)
class EvaluatorIntegrityReport:
    valid: bool
    reasons: tuple[str, ...]
    changed_protected_paths: tuple[str, ...] = ()
    missing_protected_paths: tuple[str, ...] = ()


def verify_evaluation_attestation(
    spec: FrozenEvaluatorSpec,
    attestation: EvaluationAttestation,
) -> EvaluatorIntegrityReport:
    """Verify that a check was produced by the frozen evaluator bundle.

    The function is deliberately fail-closed.  It does not infer trust from a
    green result alone and it does not trust candidate-supplied supplemental
    files as replacements for frozen evaluator inputs.
    """

    reasons: list[str] = []

    if not attestation.externally_observed:
        reasons.append("evaluation attestation was not externally observed")
    if not attestation.candidate_sha:
        reasons.append("candidate SHA is missing")
    if attestation.evaluator_revision_sha != spec.evaluator_revision_sha:
        reasons.append(
            "evaluator revision does not match the frozen evaluator revision"
        )
    if attestation.command_fingerprint != spec.command_fingerprint:
        reasons.append("evaluation command definition changed")
    if attestation.environment_spec_fingerprint != spec.environment_spec_fingerprint:
        reasons.append("evaluation environment specification changed")
    if attestation.builder_id not in spec.authorized_builder_ids:
        reasons.append(f"builder {attestation.builder_id!r} is not authorized")

    expected = dict(spec.protected_input_fingerprints)
    observed = dict(attestation.material_fingerprints)
    missing = sorted(path for path in expected if path not in observed)
    changed = sorted(
        path
        for path, fingerprint in expected.items()
        if path in observed and observed[path] != fingerprint
    )

    reasons.extend(f"protected evaluator input missing: {path}" for path in missing)
    reasons.extend(f"protected evaluator input changed: {path}" for path in changed)

    return EvaluatorIntegrityReport(
        valid=not reasons,
        reasons=tuple(reasons),
        changed_protected_paths=tuple(changed),
        missing_protected_paths=tuple(missing),
    )
