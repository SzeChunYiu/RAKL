"""Lane 3 — experience-transfer harness (offline arms + hostile cases)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[3]
_V1 = _ROOT / "research" / "glm52_mechanism_suite_v1"
_SUITE = _ROOT / "research" / "glm52_mechanism_suite_v1_1"
for path in (_ROOT / "src", _V1, _SUITE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from common import mean, paired_normal_summary, stable_hash  # type: ignore[import-not-found]
from experience_transfer import (  # type: ignore[import-not-found]
    Lesson,
    TransferTask,
    gold_memory,
    lexical_memory,
    lesson_bank,
    make_task,
    rakl_memory,
    sham_memory,
)
from framework_adapter import CanonicalFrameworkAdapter  # type: ignore[import-not-found]

EXPERIENCE_ARMS = (
    "RESET",
    "SHAM_MEMORY",
    "GENERIC_MEMORY",
    "V1_RAKL_MEMORY",
    "CURRENT_RAKL_EXPERIENCE",
    "GOLD_LESSON_ORACLE",
)

HOSTILE_FAMILIES = (
    "root_independence",
    "scope_alignment",
    "correction",
    "missing_evidence",
    "hostile_near_miss",
    "stale_lesson",
    "negative_history_route",
)

OUTCOME_ACCESS = "NO_NEW_GLM_OUTCOME"


def make_hostile_task(seed: int, family: str) -> TransferTask:
    if family == "hostile_near_miss":
        return TransferTask(
            task_id=f"EXP-hostile-nm-{seed}",
            question="Assess whether independent roots conflict without adjudication.",
            evidence="Report R1: SUPPORT ROOT=alpha. Report R2: REFUTE ROOT=beta.",
            verdict="CANNOT_CHECK",
            gold_lesson_id="L-ROOT-INDEPENDENCE",
        )
    if family == "stale_lesson":
        return TransferTask(
            task_id=f"EXP-stale-{seed}",
            question="Assess after a superseding correction.",
            evidence="2021 SUPPORT; 2024 correction REFUTE supersedes 2021.",
            verdict="REFUTE",
            gold_lesson_id="L-CORRECTION",
        )
    if family == "negative_history_route":
        return TransferTask(
            task_id=f"EXP-neg-hist-{seed}",
            question="Route should change after preserved negative history.",
            evidence="Prior route failed; target-context evidence absent.",
            verdict="CANNOT_CHECK",
            gold_lesson_id="L-MISSING-EVIDENCE",
        )
    return make_task(seed, family)


def materialize_for_arm(
    task: TransferTask,
    bank: tuple[Lesson, ...],
    arm: str,
    *,
    budget: int = 2,
    adapter: CanonicalFrameworkAdapter | None = None,
) -> dict[str, Any]:
    if arm == "RESET":
        lessons: list[Lesson] = []
    elif arm == "SHAM_MEMORY":
        lessons = sham_memory(task, bank, budget)
    elif arm == "GENERIC_MEMORY":
        lessons = lexical_memory(task, bank, budget)
    elif arm == "V1_RAKL_MEMORY":
        lessons = rakl_memory(task, bank, budget)
    elif arm == "GOLD_LESSON_ORACLE":
        lessons = gold_memory(task, bank, budget)
    elif arm == "CURRENT_RAKL_EXPERIENCE":
        adapter = adapter or CanonicalFrameworkAdapter(repo_root=_ROOT)
        envelope = {
            "task_id": task.task_id,
            "question": task.question,
            "entity": "experience",
            "qoi": "transfer",
            "context": "target",
            "family": "scope_alignment",
            "verdict": task.verdict,
            "evidence": task.evidence,
        }
        receipt = adapter.materialize_experience(envelope, {}, budget=budget)
        lessons = rakl_memory(task, bank, budget)
        return {
            "arm": arm,
            "lesson_ids": [lesson.lesson_id for lesson in lessons],
            "fibre_snapshot_hash": receipt.fibre_snapshot_hash,
            "framework_binding": "CanonicalFrameworkAdapter.materialize_experience",
            "outcome_access": OUTCOME_ACCESS,
        }
    else:
        raise ValueError(f"unknown experience arm: {arm}")

    return {
        "arm": arm,
        "lesson_ids": [lesson.lesson_id for lesson in lessons],
        "outcome_access": OUTCOME_ACCESS,
    }


def score_materialization(task: TransferTask, materialized: Mapping[str, Any]) -> dict[str, float | bool]:
    lesson_ids = {str(x) for x in materialized.get("lesson_ids", ())}
    gold_present = task.gold_lesson_id in lesson_ids
    return {
        "gold_lesson_recall": float(gold_present),
        "exact_verdict_proxy": gold_present,
        "overtransfer": any(item.startswith("L-DECOY-") for item in lesson_ids),
        "sham_only": bool(lesson_ids) and not gold_present and materialized.get("arm") == "SHAM_MEMORY",
    }


def evaluate_dev_gate(summary: Mapping[str, Any]) -> dict[str, Any]:
    comparisons = summary.get("comparisons", {})
    arms = summary.get("arms", {})
    delta = float(comparisons.get("oracle_minus_reset_recall", {}).get("delta", 0.0))
    oracle_recall = float(arms.get("GOLD_LESSON_ORACLE", {}).get("gold_lesson_recall", 0.0))
    return {
        "oracle_headroom_required": 0.10,
        "oracle_recall_floor": 0.70,
        "oracle_minus_reset_recall_delta": delta,
        "oracle_recall": oracle_recall,
        "passes": delta >= 0.10 and oracle_recall >= 0.70,
        "rule": "Offline lesson-recall proxy; hosted gate uses exact_verdict.",
        "outcome_access": OUTCOME_ACCESS,
    }


def run_offline_panel(*, phase: str = "dev", n_per_family: int = 2, memory_objects: int = 2, bank_seed: int = 707) -> dict[str, Any]:
    bank = lesson_bank(bank_seed)
    seed0 = 21_000 if phase == "dev" else 121_000
    tasks = [make_hostile_task(seed0 + i * 13 + j, family) for i in range(n_per_family) for j, family in enumerate(HOSTILE_FAMILIES)]
    adapter = CanonicalFrameworkAdapter(repo_root=_ROOT)
    records: list[dict[str, Any]] = []
    for task in tasks:
        for arm in EXPERIENCE_ARMS:
            materialized = materialize_for_arm(task, bank, arm, budget=memory_objects, adapter=adapter)
            records.append(
                {
                    "task_id": task.task_id,
                    "arm": arm,
                    "materialized": materialized,
                    "score": score_materialization(task, materialized),
                    "outcome_access": OUTCOME_ACCESS,
                }
            )

    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        by_task.setdefault(record["task_id"], {})[record["arm"]] = record

    summary: dict[str, Any] = {
        "experiment": "experience_transfer",
        "phase": phase,
        "hostile_families": list(HOSTILE_FAMILIES),
        "arms": {},
        "comparisons": {},
        "memory_bank_hash": stable_hash([lesson.render() for lesson in bank]),
        "outcome_access": OUTCOME_ACCESS,
        "model_runs": 0,
    }
    for arm in EXPERIENCE_ARMS:
        scored = [r for r in records if r["arm"] == arm]
        summary["arms"][arm] = {
            "n_scored": len(scored),
            "gold_lesson_recall": mean([float(r["score"]["gold_lesson_recall"]) for r in scored]),
            "overtransfer_rate": mean([float(r["score"]["overtransfer"]) for r in scored]),
        }

    def paired(a: str, b: str, metric: str = "gold_lesson_recall") -> dict[str, Any]:
        xs: list[float] = []
        ys: list[float] = []
        for cell in by_task.values():
            if a in cell and b in cell:
                xs.append(float(cell[a]["score"][metric]))
                ys.append(float(cell[b]["score"][metric]))
        return paired_normal_summary(xs, ys)

    summary["comparisons"] = {
        "oracle_minus_reset_recall": paired("GOLD_LESSON_ORACLE", "RESET"),
        "rakl_minus_reset_recall": paired("CURRENT_RAKL_EXPERIENCE", "RESET"),
        "rakl_minus_sham_recall": paired("CURRENT_RAKL_EXPERIENCE", "SHAM_MEMORY"),
        "rakl_minus_generic_recall": paired("CURRENT_RAKL_EXPERIENCE", "GENERIC_MEMORY"),
        "v1_minus_generic_recall": paired("V1_RAKL_MEMORY", "GENERIC_MEMORY"),
    }
    summary["dev_gate"] = evaluate_dev_gate(summary)
    return {"summary": summary, "records": records}


def offline_selftest() -> None:
    bank = lesson_bank(7)
    for i, family in enumerate(HOSTILE_FAMILIES):
        task = make_hostile_task(100 + i, family)
        for arm in EXPERIENCE_ARMS:
            assert materialize_for_arm(task, bank, arm, budget=2)["outcome_access"] == OUTCOME_ACCESS
    panel = run_offline_panel(phase="dev", n_per_family=1)
    assert panel["summary"]["model_runs"] == 0
    assert set(panel["summary"]["arms"]) == set(EXPERIENCE_ARMS)


def main() -> int:
    offline_selftest()
    print(json.dumps(run_offline_panel()["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
