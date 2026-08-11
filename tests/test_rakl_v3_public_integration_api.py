from __future__ import annotations

from rakl.v3 import (
    ExperienceBenchmarkArm,
    ProblemNoveltyClass,
    assess_experience_benchmark,
    assess_rakl_triviality,
    experience_memory_views,
    knowledge_items_from_legacy_fiber,
    validate_experience_benchmark,
    resolve_protected_attestation,
    AttestationPurpose,
)


def test_v3_facade_exports_integration_and_evaluation_apis() -> None:
    assert ExperienceBenchmarkArm.LEARNING_ENABLED.value == "LEARNING_ENABLED"
    assert ProblemNoveltyClass.RAKL_TRIVIAL.value == "RAKL_TRIVIAL"
    assert callable(assess_experience_benchmark)
    assert callable(validate_experience_benchmark)
    assert callable(assess_rakl_triviality)
    assert callable(experience_memory_views)
    assert callable(knowledge_items_from_legacy_fiber)
    assert callable(resolve_protected_attestation)
    assert AttestationPurpose.BENCHMARK_MATCH.value == "BENCHMARK_MATCH"
