"""Tests for the capability qualification V3 Stage 0/1 diagnostic (issue #447).

The checker is validated in both directions. A diagnostic that only ever fires is
worthless: every alarm assertion here is paired with a no-alarm assertion on input that
must stay silent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.paper2_capability_v3_diagnostic import (
    CANONICAL_EVIDENCE_ROLE_DEFINITION,
    audit_instruction_semantics,
    diagnose_stage_bottleneck,
    stage_decompose,
)

REPO = Path(__file__).resolve().parents[1]
V2_EXEC = REPO / "research" / "paper2_oracle_capability_gate_v2_exec"
OUT = REPO / "research" / "empirical_10_of_10_v1" / "CAPABILITY_QUALIFICATION"
TASK_IDS = ("T1", "T2", "T3", "T4", "T5")

FORMAT_ONLY_SURFACE = (
    "Return exactly one JSON object with these exact keys and no leading spaces in key "
    "names: verdict, selected_evidence_ids, rejected_evidence_ids, rationale_tags. "
    'The first non-whitespace character MUST be "{" and the last MUST be "}".'
)


def _task(task_id: str) -> dict:
    return json.loads((V2_EXEC / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))


def _generation(task_id: str) -> dict:
    path = (
        V2_EXEC
        / "native_job_3476813"
        / "runs"
        / "outputs"
        / f"LEARNING_ENABLED_{task_id}.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------
# Instruction-surface audit: must fire on the real defective surface, stay silent on a
# repaired one.
# --------------------------------------------------------------------------------------


def test_audit_fires_on_real_v2_exec_system_prompt() -> None:
    text = (V2_EXEC / "protocol" / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8")
    audit = audit_instruction_semantics(text, surface_label="SYSTEM_PROMPT.txt")
    assert audit.mentions_selected_field is True
    assert audit.mentions_rejected_field is True
    assert audit.defines_evidence_role is False
    assert audit.verdict == "EVIDENCE_ROLE_UNDEFINED"
    assert audit.role_language_matches == ()


def test_audit_fires_on_real_runner_instruction_block() -> None:
    src = (REPO / "src" / "rakl" / "paper2_experience_benchmark_runner.py").read_text(
        encoding="utf-8"
    )
    start = src.index("Return exactly one JSON object with these exact keys")
    end = src.index("Then stop. Do not wrap the JSON in markdown fences.")
    audit = audit_instruction_semantics(src[start:end], surface_label="runner")
    assert audit.defines_evidence_role is False
    assert audit.verdict == "EVIDENCE_ROLE_UNDEFINED"


def test_audit_silent_on_canonically_repaired_surface() -> None:
    """No-alarm case: the repaired interface must not be reported as defective."""
    repaired = FORMAT_ONLY_SURFACE + "\n" + CANONICAL_EVIDENCE_ROLE_DEFINITION
    audit = audit_instruction_semantics(repaired, surface_label="repaired")
    assert audit.canonical_definition_present is True
    assert audit.defines_evidence_role is True
    assert audit.verdict == "EVIDENCE_ROLE_DEFINED_CANONICAL"


@pytest.mark.parametrize(
    "definition",
    [
        "selected_evidence_ids must contain only the ids that license your verdict.",
        "Put in selected_evidence_ids the evidence you relied on to reach the verdict.",
        "selected_evidence_ids is the basis for your verdict; everything else is rejected.",
        "Selected means the evidence that justifies the verdict you chose.",
    ],
)
def test_audit_silent_on_noncanonical_role_definitions(definition: str) -> None:
    """No-alarm case: a differently worded definition must not read as 'undefined'.

    Without this, the absence claim would be an artefact of one narrow pattern.
    """
    audit = audit_instruction_semantics(
        FORMAT_ONLY_SURFACE + "\n" + definition, surface_label="noncanonical"
    )
    assert audit.defines_evidence_role is True
    assert audit.verdict == "EVIDENCE_ROLE_DEFINED_NONCANONICAL"


def test_audit_reports_absent_fields_distinctly() -> None:
    audit = audit_instruction_semantics("Answer with a verdict.", surface_label="unrelated")
    assert audit.verdict == "EVIDENCE_FIELDS_ABSENT"


# --------------------------------------------------------------------------------------
# Per-item decomposition against preserved data.
# --------------------------------------------------------------------------------------


def test_gold_uses_licenses_verdict_convention_not_relevance() -> None:
    """T1 rejects an on-topic mass reading, which rules out a relevance reading."""
    task = _task("T1")
    gold = task["sealed_answer"]
    e2 = next(e for e in task["evidence"] if e["id"] == "E2")
    assert "kg" in e2["text"]
    assert "E2" in gold["rejected_evidence_ids"]
    assert "E2" not in gold["selected_evidence_ids"]


def test_gold_partitions_are_total_and_disjoint() -> None:
    for task_id in TASK_IDS:
        task = _task(task_id)
        gold = task["sealed_answer"]
        selected = set(gold["selected_evidence_ids"])
        rejected = set(gold["rejected_evidence_ids"])
        all_ids = {e["id"] for e in task["evidence"]}
        assert not (selected & rejected), task_id
        assert selected | rejected == all_ids, task_id


def test_preserved_generations_show_exact_inversion_on_t2_and_t3() -> None:
    for task_id in ("T2", "T3"):
        diagnosis = stage_decompose(_generation(task_id), _task(task_id))
        assert diagnosis.partition_exact_inversion is True, task_id
        assert diagnosis.partition_exact_match is False, task_id
        assert set(diagnosis.predicted_selected) == set(diagnosis.gold_rejected), task_id
        assert set(diagnosis.predicted_rejected) == set(diagnosis.gold_selected), task_id


def test_t4_verdict_error_is_convention_invariant() -> None:
    """T4 is a real composition failure; the labelling confound does not excuse it."""
    diagnosis = stage_decompose(_generation("T4"), _task("T4"))
    assert diagnosis.verdict_correct is False
    assert diagnosis.gold_verdict == "REFUTE"
    assert diagnosis.predicted_verdict == "CANNOT_CHECK"
    assert diagnosis.partition_exact_inversion is False


def test_all_preserved_generations_parsed() -> None:
    for task_id in TASK_IDS:
        assert stage_decompose(_generation(task_id), _task(task_id)).parse_valid is True


def test_stage_decompose_reports_clean_match_without_alarm() -> None:
    """No-alarm case: a fully correct generation must not be flagged as inverted."""
    task = _task("T2")
    gold = task["sealed_answer"]
    perfect = {
        "parsed": {
            "verdict": gold["verdict"],
            "selected_evidence_ids": list(gold["selected_evidence_ids"]),
            "rejected_evidence_ids": list(gold["rejected_evidence_ids"]),
            "rationale_tags": [],
        }
    }
    diagnosis = stage_decompose(perfect, task)
    assert diagnosis.partition_exact_match is True
    assert diagnosis.partition_exact_inversion is False
    assert diagnosis.verdict_correct is True
    assert diagnosis.notes == ()


def test_stage_decompose_emits_no_score_field() -> None:
    """The module must offer no route to a convention-corrected score."""
    payload = stage_decompose(_generation("T2"), _task("T2")).as_dict()
    forbidden = {"score", "success", "corrected_score", "adjusted_score", "pass"}
    assert not (forbidden & set(payload)), payload.keys()


def test_inversion_not_identifiable_when_gold_sets_coincide() -> None:
    task = {
        "task_id": "X1",
        "sealed_answer": {
            "verdict": "CANNOT_CHECK",
            "selected_evidence_ids": [],
            "rejected_evidence_ids": [],
        },
    }
    generation = {
        "parsed": {
            "verdict": "CANNOT_CHECK",
            "selected_evidence_ids": [],
            "rejected_evidence_ids": [],
            "rationale_tags": [],
        }
    }
    diagnosis = stage_decompose(generation, task)
    assert diagnosis.inversion_identifiable is False
    assert diagnosis.partition_exact_inversion is False


# --------------------------------------------------------------------------------------
# Aggregate diagnosis: the construct-defect terminal requires BOTH conditions.
# --------------------------------------------------------------------------------------


def _diagnoses() -> list:
    return [stage_decompose(_generation(t), _task(t)) for t in TASK_IDS]


def _undefined_audit():
    return audit_instruction_semantics(FORMAT_ONLY_SURFACE, surface_label="undefined")


def _defined_audit():
    return audit_instruction_semantics(
        FORMAT_ONLY_SURFACE + "\n" + CANONICAL_EVIDENCE_ROLE_DEFINITION,
        surface_label="defined",
    )


def test_construct_defect_requires_inversion_and_undefined_surface() -> None:
    receipt = diagnose_stage_bottleneck(_diagnoses(), [_undefined_audit()])
    assert receipt["diagnosis_state"] == "BENCHMARK_CONSTRUCT_DEFECT"


def test_defined_surface_with_inversion_is_binding_floor_not_construct_defect() -> None:
    """No-alarm case: once the roles are stated, inversion is a genuine model failure."""
    receipt = diagnose_stage_bottleneck(_diagnoses(), [_defined_audit()])
    assert receipt["diagnosis_state"] == "EVIDENCE_BINDING_FLOOR"


def test_undefined_surface_without_inversion_is_not_construct_defect() -> None:
    """No-alarm case: a latent ambiguity nobody tripped over is not a demonstrated confound."""
    clean = [d for d in _diagnoses() if not d.partition_exact_inversion]
    receipt = diagnose_stage_bottleneck(clean, [_undefined_audit()])
    assert receipt["diagnosis_state"] != "BENCHMARK_CONSTRUCT_DEFECT"


def test_receipt_carries_no_rescore_and_no_authorization() -> None:
    receipt = diagnose_stage_bottleneck(_diagnoses(), [_undefined_audit()])
    assert "no_rescore_guarantee" in receipt
    assert "authorization_boundary" in receipt
    blob = json.dumps(receipt)
    assert "CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3" not in blob.replace(
        receipt["authorization_boundary"], ""
    )


def test_verdict_accuracy_carries_incomparability_note() -> None:
    receipt = diagnose_stage_bottleneck(_diagnoses(), [_undefined_audit()])
    note = receipt["stage_observables"]["E_VERDICT_COMPOSITION"]["comparability_note"]
    assert "NOT comparable" in note


def test_early_stages_marked_not_separable() -> None:
    receipt = diagnose_stage_bottleneck(_diagnoses(), [_undefined_audit()])
    key = "A_EVIDENCE_RELEVANCE__B_EVIDENCE_POLARITY__C_CONTEXT_QOI_ALIGNMENT"
    assert receipt["stage_observables"][key]["separability"] == "NOT_SEPARABLE_IN_MONOLITHIC_READOUT"


def test_empty_diagnoses_rejected() -> None:
    with pytest.raises(ValueError):
        diagnose_stage_bottleneck([], [_undefined_audit()])


# --------------------------------------------------------------------------------------
# Frozen artifacts.
# --------------------------------------------------------------------------------------


def test_frozen_receipt_matches_schema_consts() -> None:
    receipt = json.loads((OUT / "BOTTLENECK_RECEIPT.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (REPO / "schemas" / "paper2-capability-v3-bottleneck-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    for key, spec in schema["properties"].items():
        if "const" in spec:
            assert receipt[key] == spec["const"], key
    for key in schema["required"]:
        assert key in receipt, key


def test_frozen_receipt_preserves_sealed_verdict() -> None:
    receipt = json.loads((OUT / "BOTTLENECK_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["preserved_sealed_verdict"] == "MODEL_CAPABILITY_FLOOR_7B_V2_EXEC"
    assert receipt["preserved_sealed_verdict_status"] == "UNCHANGED_BY_THIS_RECEIPT"
    assert "rescoring job 3476813" in " ".join(receipt["downstream_effect"]["forbidden_next"])


def test_frozen_receipt_is_reproducible_from_preserved_data() -> None:
    frozen = json.loads((OUT / "BOTTLENECK_RECEIPT.json").read_text(encoding="utf-8"))
    recomputed = diagnose_stage_bottleneck(
        _diagnoses(),
        [
            audit_instruction_semantics(
                (V2_EXEC / "protocol" / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8"),
                surface_label="SYSTEM_PROMPT.txt",
            )
        ],
    )
    assert frozen["diagnosis_state"] == recomputed["diagnosis_state"]
    assert frozen["item_count"] == recomputed["item_count"]
    assert (
        frozen["stage_observables"]["D_EXACT_EVIDENCE_BINDING"]["partition_exact_inversion_count"]
        == recomputed["stage_observables"]["D_EXACT_EVIDENCE_BINDING"][
            "partition_exact_inversion_count"
        ]
    )


def test_gold_audit_frozen_verdicts() -> None:
    audit = json.loads((OUT / "GOLD_AUDIT.json").read_text(encoding="utf-8"))
    assert audit["gold_verdict"] == "GOLD_INTERNALLY_CONSISTENT"
    assert audit["stage0_verdict"] == "INSTRUMENT_DEFECT_EVIDENCE_ROLE_UNDEFINED"
    assert audit["gold_convention"] == "LICENSES_VERDICT"


def test_diagnostic_results_jsonl_covers_all_items() -> None:
    path = OUT / "DIAGNOSTIC_RESULTS" / "qwen2.5-7b-instruct.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    assert [r["task_id"] for r in rows] == list(TASK_IDS)
