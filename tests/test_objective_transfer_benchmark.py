from rakl.objective_transfer_benchmark import (
    Decision, FAMILIES, generate, verify, extract, fit_threshold,
    semantic_decorrelation, evaluate, evaluate_twin
)


def test_generator_is_deterministic_and_balanced():
    a = generate(1234, 4, True)
    b = generate(1234, 4, True)
    assert a == b
    counts = {d: 0 for d in Decision}
    for task in a:
        counts[verify(task).decision] += 1
    assert counts[Decision.ACCEPT] == counts[Decision.REJECT]
    assert counts[Decision.CANNOT_CHECK] > 0
    for family in FAMILIES:
        assert any(task.family == family for task in a)


def test_verifier_does_not_use_perturbation_identity():
    tasks = generate(99, 2, True)
    for task in tasks:
        before = verify(task)
        mutated = type(task)(
            task.item_id, task.family, task.item_type, task.source_text,
            task.target_text, task.public, "fabricated-hidden-marker"
        )
        assert verify(mutated) == before


def test_lexical_development_baseline_is_midband_and_decorrelated():
    tasks = generate(2026081201, 10, True)
    gold = {task.item_id: verify(task).decision for task in tasks}
    threshold = fit_threshold(tasks, gold)
    result = evaluate(tasks, threshold)
    assert 0.35 <= result["lexical_accuracy_known"] <= 0.75
    decorrelation = semantic_decorrelation(tasks)
    assert all(abs(value["mean_diff"]) < 0.06 for value in decorrelation.values())


def test_full_structural_extractor_matches_exact_verifiers():
    tasks = generate(2026081201, 6, True)
    for task in tasks:
        assert extract(task).decision == verify(task).decision


def test_coordinate_ablated_twin_survives_but_is_not_perfect():
    tasks = generate(2026081201, 10, True)
    gold = {task.item_id: verify(task).decision for task in tasks}
    threshold = fit_threshold(tasks, gold)
    twin = evaluate_twin(tasks, threshold)
    baseline = evaluate(tasks, threshold)
    assert twin["exact3"] > baseline["lexical_exact3"]
    assert twin["exact3"] < 1.0
    assert twin["delta_brier_vs_lexical"] > 0


def test_named_hard_strata_exist_and_behave():
    tasks = generate(2026081201, 4, True)
    valid_distant = [task for task in tasks if task.item_type == "VALID_DISTANT_TRANSFER"]
    semantic_near_miss = [task for task in tasks if task.item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER"]
    assert valid_distant and semantic_near_miss
    assert all(verify(task).decision == Decision.ACCEPT for task in valid_distant)
    assert all(verify(task).decision == Decision.REJECT for task in semantic_near_miss)
