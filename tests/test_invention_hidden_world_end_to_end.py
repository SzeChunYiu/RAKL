from rakl.formal_signatures import scientific_motif_signature
from rakl.invention_benchmark import (
    InventionAttempt,
    InventionBenchmarkCase,
    InventionBenchmarkVerdict,
    InventionWorldKind,
    evaluate_invention_attempt,
)
from rakl.symbolic_discovery import SymbolicDiscoverySpec, discover_symbolic_laws


def test_hidden_quadratic_structure_is_recovered_from_data_only():
    # Proposer/discovery receives rows + frozen grammar, not the evaluator target motif.
    rows = tuple(
        {"x": float(x), "y": 1.25 + 2.5 * float(x) ** 2}
        for x in range(-10, 11)
    )
    discovery = discover_symbolic_laws(
        rows,
        SymbolicDiscoverySpec(
            target_symbol="y",
            feature_symbols=("x",),
            max_depth=1,
            beam_width=24,
            max_generated=300,
            rows_are_training_partition=True,
            operator_set_frozen_before_scoring=True,
        ),
        top_k=5,
    )
    best = discovery.candidates[0]
    recovered = scientific_motif_signature(best.expression)

    # Hidden/evaluator-side target is introduced only after the candidate is frozen.
    case = InventionBenchmarkCase(
        benchmark_id="hidden-quadratic",
        world_kind=InventionWorldKind.RECONSTRUCTION,
        frozen_evidence_ids=("world:hidden-quadratic:data",),
        target_signature=("POWER:x:2",),
        minimum_signature_recall=1.0,
        minimum_signature_precision=0.5,
        hidden_target_id="law:y=a+b*x^2",
        target_hidden_from_proposer=True,
        thresholds_frozen_before_attempt=True,
        evaluator_separate=True,
    )
    attempt = InventionAttempt(
        benchmark_id=case.benchmark_id,
        candidate_id=best.candidate_id,
        recovered_signature=recovered,
        candidate_frozen_before_target_exposure=True,
        hidden_target_exposed=False,
        target_validation_passed=best.normalized_mse < 1e-16,
        formal_verification_passed=True,
    )
    report = evaluate_invention_attempt(case, attempt)
    assert report.verdict is InventionBenchmarkVerdict.INVENTION_RECOVERED


def test_hidden_cross_feature_interaction_is_novel_composition():
    rows = tuple(
        {
            "x": float(x),
            "z": float(z),
            "y": -0.75 + 1.8 * float(x) * float(z),
        }
        for x, z in zip(range(1, 22), range(23, 2, -1))
    )
    discovery = discover_symbolic_laws(
        rows,
        SymbolicDiscoverySpec(
            target_symbol="y",
            feature_symbols=("x", "z"),
            max_depth=1,
            beam_width=30,
            max_generated=600,
            rows_are_training_partition=True,
            operator_set_frozen_before_scoring=True,
        ),
        top_k=8,
    )
    best = discovery.candidates[0]
    recovered = scientific_motif_signature(best.expression)
    interaction = "INTERACTION:x*z"

    case = InventionBenchmarkCase(
        benchmark_id="hidden-interaction",
        world_kind=InventionWorldKind.NOVEL_COMPOSITION,
        frozen_evidence_ids=("world:hidden-interaction:data",),
        target_signature=(interaction,),
        minimum_signature_recall=1.0,
        minimum_signature_precision=0.5,
        hidden_target_id="law:y=a+b*x*z",
        target_hidden_from_proposer=True,
        thresholds_frozen_before_attempt=True,
        evaluator_separate=True,
        source_components=("x", "z"),
        required_novel_combinations=(interaction,),
    )
    attempt = InventionAttempt(
        benchmark_id=case.benchmark_id,
        candidate_id=best.candidate_id,
        recovered_signature=recovered,
        candidate_frozen_before_target_exposure=True,
        hidden_target_exposed=False,
        target_validation_passed=best.normalized_mse < 1e-16,
        formal_verification_passed=True,
        source_component_ids_used=("x", "z"),
        generated_combination_ids=recovered,
    )
    report = evaluate_invention_attempt(case, attempt)
    assert report.verdict is InventionBenchmarkVerdict.INVENTION_RECOVERED
    assert report.novel_combination_recall == 1.0
