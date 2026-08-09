from rakl.evaluator import (
    EvaluationAttestation,
    FrozenEvaluatorSpec,
    verify_evaluation_attestation,
)


INCUMBENT = "a" * 40
CANDIDATE = "b" * 40


def frozen_spec() -> FrozenEvaluatorSpec:
    return FrozenEvaluatorSpec(
        evaluator_revision_sha=INCUMBENT,
        protected_input_fingerprints={
            ".github/workflows/test.yml": "workflow-v1",
            "pyproject.toml": "pytest-config-v1",
            "tests/test_core.py": "core-tests-v1",
            "src/rakl/promotion.py": "promotion-judge-v1",
        },
        command_fingerprint="pytest-explicit-parent-suite-v1",
        environment_spec_fingerprint="python311-eval-env-v1",
        authorized_builder_ids=("github-actions:test",),
    )


def clean_attestation(**overrides) -> EvaluationAttestation:
    values = {
        "candidate_sha": CANDIDATE,
        "evaluator_revision_sha": INCUMBENT,
        "material_fingerprints": {
            ".github/workflows/test.yml": "workflow-v1",
            "pyproject.toml": "pytest-config-v1",
            "tests/test_core.py": "core-tests-v1",
            "src/rakl/promotion.py": "promotion-judge-v1",
        },
        "command_fingerprint": "pytest-explicit-parent-suite-v1",
        "environment_spec_fingerprint": "python311-eval-env-v1",
        "builder_id": "github-actions:test",
        "check_name": "frozen-parent-eval",
        "conclusion": "SUCCESS",
        "externally_observed": True,
    }
    values.update(overrides)
    return EvaluationAttestation(**values)


def test_clean_frozen_evaluator_attestation_is_valid():
    report = verify_evaluation_attestation(frozen_spec(), clean_attestation())
    assert report.valid
    assert report.reasons == ()


def test_test_discovery_configuration_tampering_is_detected():
    materials = dict(clean_attestation().material_fingerprints)
    materials["pyproject.toml"] = "hostile-testpaths-only-smoke"
    report = verify_evaluation_attestation(
        frozen_spec(), clean_attestation(material_fingerprints=materials)
    )
    assert not report.valid
    assert report.changed_protected_paths == ("pyproject.toml",)
    assert any("pyproject.toml" in reason for reason in report.reasons)


def test_judge_code_tampering_is_detected():
    materials = dict(clean_attestation().material_fingerprints)
    materials["src/rakl/promotion.py"] = "candidate-weakened-judge"
    report = verify_evaluation_attestation(
        frozen_spec(), clean_attestation(material_fingerprints=materials)
    )
    assert not report.valid
    assert report.changed_protected_paths == ("src/rakl/promotion.py",)


def test_missing_frozen_test_is_detected():
    materials = dict(clean_attestation().material_fingerprints)
    del materials["tests/test_core.py"]
    report = verify_evaluation_attestation(
        frozen_spec(), clean_attestation(material_fingerprints=materials)
    )
    assert not report.valid
    assert report.missing_protected_paths == ("tests/test_core.py",)


def test_supplemental_candidate_tests_do_not_replace_or_invalidate_frozen_inputs():
    materials = dict(clean_attestation().material_fingerprints)
    materials["candidate_tests/test_new_feature.py"] = "supplemental-v1"
    report = verify_evaluation_attestation(
        frozen_spec(), clean_attestation(material_fingerprints=materials)
    )
    assert report.valid


def test_command_environment_builder_and_revision_are_part_of_evaluator_identity():
    cases = [
        clean_attestation(command_fingerprint="pytest-candidate-config"),
        clean_attestation(environment_spec_fingerprint="unknown-runner"),
        clean_attestation(builder_id="candidate-self-report"),
        clean_attestation(evaluator_revision_sha=CANDIDATE),
        clean_attestation(externally_observed=False),
    ]
    for attestation in cases:
        assert not verify_evaluation_attestation(frozen_spec(), attestation).valid
