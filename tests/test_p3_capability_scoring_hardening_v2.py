from __future__ import annotations

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "paper3"
sys.path.insert(0, str(EXP))

import build_capability_stage4_panel_v1 as PANEL  # noqa: E402
import run_capability_stage4_v1 as V1  # noqa: E402
import run_capability_stage4_v2 as V2  # noqa: E402
import validate_capability_stage4_v2_terminal as TERMINAL  # noqa: E402

FREEZE = json.loads(
    (
        ROOT
        / "research"
        / "empirical_10_of_10_v1"
        / "CAPABILITY_QUALIFICATION"
        / "STAGE3_5_FREEZE_V1.json"
    ).read_text()
)


def _gold_records(tasks: list[dict]) -> list[dict]:
    records = []
    for task in tasks:
        gold = task["gold"]
        records.append(
            {
                "task_id": task["task_id"],
                "family": task["family"],
                "parsed": {
                    "verdict": gold["verdict"],
                    "selected_evidence_ids": list(gold["selected_evidence_ids"]),
                    "rejected_evidence_ids": list(gold["rejected_evidence_ids"]),
                    "rationale_tags": [],
                },
                "parse_reasons": [],
            }
        )
    return records


def _denominator_evasion_records(tasks: list[dict]) -> list[dict]:
    """Construct a response set that v1 reports as passing despite bad CC precision.

    Nineteen non-CANNOT_CHECK cases are changed to syntactically valid
    CANNOT_CHECK responses with an incomplete evidence partition. They are spread
    across families so joint-exact remains >= .85 and every family remains >= .75.
    V1 excludes these predictions from CANNOT_CHECK precision and other affected
    denominators; V2 must count them.
    """

    records = _gold_records(tasks)
    by_id = {record["task_id"]: record for record in records}
    selected: list[dict] = []
    family_counts: Counter[str] = Counter()

    # Force the maximal allowed error load into the context-near-miss family so
    # v1 also demonstrates its conditional context-error denominator.
    for task in tasks:
        if (
            task["family"] == "CONTEXT_QOI_NEAR_MISS"
            and task["gold"]["verdict"] != "CANNOT_CHECK"
            and family_counts[task["family"]] < 3
        ):
            selected.append(task)
            family_counts[task["family"]] += 1
            if family_counts[task["family"]] == 3:
                break

    for task in tasks:
        if len(selected) >= 19:
            break
        if task in selected or task["gold"]["verdict"] == "CANNOT_CHECK":
            continue
        if family_counts[task["family"]] >= 3:
            continue
        selected.append(task)
        family_counts[task["family"]] += 1

    assert len(selected) == 19
    assert max(family_counts.values()) <= 3

    for task in selected:
        ids = sorted(V1._evidence_ids(task["prompt"]))
        assert ids
        record = by_id[task["task_id"]]
        record["parsed"] = {
            "verdict": "CANNOT_CHECK",
            "selected_evidence_ids": [],
            "rejected_evidence_ids": ids[:-1],
            "rationale_tags": [],
        }
    return records


def _terminal_receipt(path: Path, terminal: str) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "rakl-capability-qualification-stage5-result-v2",
                "terminal": terminal,
                "grants_scientific_authority": False,
                "scoring_hardening": {
                    "thresholds_changed_from_v1": False,
                    "panel_changed_from_v1": False,
                    "model_or_interface_changed_from_v1": False,
                },
            }
        )
        + "\n"
    )


def test_hardened_scorer_accepts_gold_exact_panel() -> None:
    tasks = PANEL.build()
    metrics = V2._score(deepcopy(tasks), _gold_records(tasks), FREEZE)
    assert metrics["all_vector_gates_pass"] is True
    assert metrics["parse_validity"] == 1.0
    assert metrics["exact_joint_verdict_and_binding"] == 1.0
    assert metrics["cannot_check_precision"] == 1.0
    assert metrics["context_qoi_error_rate"] == 0.0


def test_v1_denominator_evasion_counterexample_is_closed_by_v2() -> None:
    tasks = PANEL.build()
    records = _denominator_evasion_records(tasks)

    v1 = V1._score(deepcopy(tasks), deepcopy(records), FREEZE)
    v2 = V2._score(deepcopy(tasks), deepcopy(records), FREEZE)

    # This is the root-cause witness: v1 can report a full vector pass while 19
    # wrong CANNOT_CHECK predictions with incomplete evidence partitions are
    # absent from its precision denominator.
    assert v1["all_vector_gates_pass"] is True
    assert v1["parse_validity"] == 1.0
    assert v1["cannot_check_precision"] == 1.0
    assert v1["context_qoi_error_rate"] == 0.0
    assert v1["exact_joint_verdict_and_binding"] >= 0.85

    # V2 makes malformed structured readout fail closed and counts every parsed
    # CANNOT_CHECK prediction in precision, so the same adversarial record set
    # cannot authorize capability.
    assert v2["all_vector_gates_pass"] is False
    assert v2["parse_validity"] < FREEZE["vector_gate"]["parse_validity_min"]
    assert v2["cannot_check_precision"] < FREEZE["vector_gate"]["cannot_check_precision_min"]
    assert v2["context_qoi_error_rate"] > FREEZE["vector_gate"]["context_qoi_error_max"]


@pytest.mark.parametrize("terminal,runner_code", TERMINAL.EXPECTED_PROCESS_CODE.items())
def test_registered_scientific_terminals_are_valid_complete_runner_outcomes(
    tmp_path: Path, terminal: str, runner_code: int
) -> None:
    receipt = tmp_path / "FINAL_CAPABILITY_RECEIPT.json"
    _terminal_receipt(receipt, terminal)
    assert TERMINAL.validate(receipt, runner_code) == terminal


def test_runner_code_cannot_relabel_scientific_terminal(tmp_path: Path) -> None:
    receipt = tmp_path / "FINAL_CAPABILITY_RECEIPT.json"
    _terminal_receipt(receipt, "DIAGNOSTIC_OVERFIT_OR_INSUFFICIENT_CAPABILITY")
    with pytest.raises(RuntimeError, match="runner_code_terminal_mismatch"):
        TERMINAL.validate(receipt, 0)
