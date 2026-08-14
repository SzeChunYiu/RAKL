from rakl.controlled_witness_extraction import (
    controlled_span_manifest,
    drop_semantic_field,
    extract_controlled_task,
    render_controlled_task,
)
from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_benchmark_v2 import generate, verify


def test_two_controlled_surfaces_round_trip_to_unchanged_exact_verifier():
    tasks = generate(202608141001, 2, True)
    for task in tasks:
        gold = verify(task).decision
        for variant in (0, 1):
            text = render_controlled_task(task, variant=variant)
            parsed = extract_controlled_task(
                text, expected_span_sha256=dict(controlled_span_manifest(text))
            )
            assert parsed.complete
            assert parsed.task is not None
            assert verify(parsed.task).decision is gold
            assert parsed.grants_scientific_authority is False


def test_stale_source_span_binding_fails_closed():
    task = generate(202608141002, 1, True)[0]
    text = render_controlled_task(task)
    expected = dict(controlled_span_manifest(text))
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Target structural record :: "):
            lines[i] = line + " "
            break
    parsed = extract_controlled_task("\n".join(lines) + "\n", expected_span_sha256=expected)
    assert not parsed.complete
    assert any(reason.startswith("source_span_hash_mismatch:target") for reason in parsed.reasons)


def test_missing_mapping_is_not_reconstructed_from_surface_words():
    task = next(
        task
        for task in generate(202608141003, 1, True)
        if task.family in {"flow", "logic", "state", "sched", "stat"}
    )
    text = render_controlled_task(task)
    parsed = extract_controlled_task(drop_semantic_field(text, "mapping"))
    assert not parsed.complete
    assert "missing_field:mapping" in parsed.reasons


def test_unknown_coordinate_survives_text_round_trip_as_cannot_check():
    task = next(
        task
        for task in generate(202608141004, 3, True)
        if verify(task).decision is Decision.CANNOT_CHECK
    )
    text = render_controlled_task(task, variant=1)
    parsed = extract_controlled_task(
        text, expected_span_sha256=dict(controlled_span_manifest(text))
    )
    assert parsed.complete and parsed.task is not None
    assert verify(parsed.task).decision is Decision.CANNOT_CHECK
