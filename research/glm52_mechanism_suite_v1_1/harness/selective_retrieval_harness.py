"""Lane 2 — selective retrieval harness (offline arm wiring + headroom gate)."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[3]
_V1 = _ROOT / "research" / "glm52_mechanism_suite_v1"
_SUITE = _ROOT / "research" / "glm52_mechanism_suite_v1_1"
for path in (_ROOT / "src", _V1, _SUITE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from common import mean, paired_normal_summary, stable_hash  # type: ignore[import-not-found]
from framework_adapter import CanonicalFrameworkAdapter, strip_gold_fields, visible_doc  # type: ignore[import-not-found]
from selective_retrieval import (  # type: ignore[import-not-found]
    EvidenceDoc,
    RetrievalTask,
    generic_hybrid,
    make_task,
    oracle_select,
    rakl_select,
)

RETRIEVAL_ARMS = (
    "GENERIC_HYBRID",
    "V1_TYPED_SELECTOR",
    "CURRENT_RAKL_EPISTEMIC_SEARCH",
    "GOLD_ORACLE",
    "NATIVE_LONG",
)

OUTCOME_ACCESS = "NO_NEW_GLM_OUTCOME"
DEFAULT_NATIVE_LIMIT_TOKENS = 950_000


def _task_to_adapter_envelope(task: RetrievalTask) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "family": task.family,
        "question": task.question,
        "entity": task.entity,
        "qoi": task.qoi,
        "context": task.context,
        "docs": [asdict(doc) for doc in task.docs],
        "verdict": task.verdict,
        "support_ids": list(task.support_ids),
        "refute_ids": list(task.refute_ids),
    }


def _docs_from_ids(task: RetrievalTask, ids: tuple[str, ...]) -> list[EvidenceDoc]:
    by_id = {doc.doc_id: doc for doc in task.docs}
    return [by_id[doc_id] for doc_id in ids if doc_id in by_id]


def select_for_arm(
    task: RetrievalTask,
    arm: str,
    *,
    budget_docs: int,
    native_limit_tokens: int = DEFAULT_NATIVE_LIMIT_TOKENS,
    adapter: CanonicalFrameworkAdapter | None = None,
) -> list[EvidenceDoc] | None:
    if arm == "GENERIC_HYBRID":
        return generic_hybrid(task, budget_docs)
    if arm == "V1_TYPED_SELECTOR":
        return rakl_select(task, budget_docs)
    if arm == "GOLD_ORACLE":
        return oracle_select(task, budget_docs)
    if arm == "NATIVE_LONG":
        est = len("\n".join(doc.render() for doc in task.docs)) // 4
        return list(task.docs) if est <= native_limit_tokens else None
    if arm == "CURRENT_RAKL_EPISTEMIC_SEARCH":
        adapter = adapter or CanonicalFrameworkAdapter(repo_root=_ROOT)
        receipt = adapter.retrieve(_task_to_adapter_envelope(task), budget=budget_docs)
        return _docs_from_ids(task, receipt.selected_candidate_ids)
    raise ValueError(f"unknown retrieval arm: {arm}")


def score_selection(task: RetrievalTask, selected: list[EvidenceDoc] | None) -> dict[str, float | bool | str]:
    if selected is None:
        return {"status": "CAPACITY_EXCEEDED", "gold_recall": 0.0, "exact_verdict_proxy": False}
    selected_ids = {doc.doc_id for doc in selected}
    gold_ids = set(task.gold_ids)
    recall = len(selected_ids & gold_ids) / len(gold_ids) if gold_ids else 1.0
    return {
        "status": "OK",
        "gold_recall": recall,
        "exact_verdict_proxy": recall >= 1.0,
        "selected_count": float(len(selected)),
    }


def evaluate_headroom_gate(summary: Mapping[str, Any]) -> dict[str, Any]:
    comparisons = summary.get("comparisons", {})
    arms = summary.get("arms", {})
    oracle_minus_generic = comparisons.get("oracle_minus_generic_recall", {})
    oracle_recall = float(arms.get("GOLD_ORACLE", {}).get("gold_recall", 0.0))
    delta = float(oracle_minus_generic.get("delta", 0.0))
    return {
        "oracle_headroom_required": 0.10,
        "oracle_recall_floor": 0.70,
        "oracle_minus_generic_recall_delta": delta,
        "oracle_recall": oracle_recall,
        "passes": delta >= 0.10 and oracle_recall >= 0.70,
        "terminal_if_fail": "NON_DISCRIMINATING_SELECTION_TASK",
        "rule": "Offline selection-recall proxy; hosted gate uses exact_verdict.",
        "outcome_access": OUTCOME_ACCESS,
    }


def run_offline_panel(
    *,
    phase: str = "dev",
    n_per_cell: int = 3,
    pressures: tuple[int, ...] = (32_000,),
    budget_docs: int = 8,
    native_limit_tokens: int = DEFAULT_NATIVE_LIMIT_TOKENS,
) -> dict[str, Any]:
    families = ("correction", "independent_conflict", "scope")
    seed0 = 11_000 if phase == "dev" else 91_000
    tasks = [
        make_task(seed0 + i * 17 + j, family, pressure)
        for pressure in pressures
        for i in range(n_per_cell)
        for j, family in enumerate(families)
    ]
    adapter = CanonicalFrameworkAdapter(repo_root=_ROOT)
    records: list[dict[str, Any]] = []
    for task in tasks:
        for arm in RETRIEVAL_ARMS:
            selected = select_for_arm(
                task, arm, budget_docs=budget_docs, native_limit_tokens=native_limit_tokens, adapter=adapter
            )
            score = score_selection(task, selected)
            records.append(
                {
                    "task_id": task.task_id,
                    "family": task.family,
                    "arm": arm,
                    "selected_ids": [doc.doc_id for doc in selected] if selected else [],
                    "gold_ids_hash": stable_hash(task.gold_ids),
                    "score": score,
                    "outcome_access": OUTCOME_ACCESS,
                }
            )

    by_task: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        if record["score"].get("status") == "OK":
            by_task.setdefault(record["task_id"], {})[record["arm"]] = record

    summary: dict[str, Any] = {
        "experiment": "selective_retrieval",
        "phase": phase,
        "arms": {},
        "comparisons": {},
        "outcome_access": OUTCOME_ACCESS,
        "model_runs": 0,
    }
    for arm in RETRIEVAL_ARMS:
        scored = [r for r in records if r["arm"] == arm and r["score"].get("status") == "OK"]
        summary["arms"][arm] = {
            "n_scored": len(scored),
            "gold_recall": mean([float(r["score"]["gold_recall"]) for r in scored]),
            "exact_verdict_proxy": mean([float(r["score"]["exact_verdict_proxy"]) for r in scored]),
            "capacity_exceeded": sum(1 for r in records if r["arm"] == arm and r["score"].get("status") == "CAPACITY_EXCEEDED"),
        }

    def paired(metric: str, a: str, b: str) -> dict[str, Any]:
        xs: list[float] = []
        ys: list[float] = []
        for cell in by_task.values():
            if a in cell and b in cell:
                xs.append(float(cell[a]["score"][metric]))
                ys.append(float(cell[b]["score"][metric]))
        return paired_normal_summary(xs, ys)

    summary["comparisons"] = {
        "oracle_minus_generic_recall": paired("gold_recall", "GOLD_ORACLE", "GENERIC_HYBRID"),
        "rakl_minus_generic_recall": paired("gold_recall", "CURRENT_RAKL_EPISTEMIC_SEARCH", "GENERIC_HYBRID"),
        "v1_minus_generic_recall": paired("gold_recall", "V1_TYPED_SELECTOR", "GENERIC_HYBRID"),
        "native_minus_generic_recall": paired("gold_recall", "NATIVE_LONG", "GENERIC_HYBRID"),
    }
    summary["dev_gate"] = evaluate_headroom_gate(summary)
    return {"summary": summary, "records": records}


def offline_selftest() -> None:
    task = make_task(4242, "correction", 4000)
    adapter = CanonicalFrameworkAdapter(repo_root=_ROOT)
    for arm in RETRIEVAL_ARMS:
        selected = select_for_arm(task, arm, budget_docs=8, adapter=adapter)
        assert selected is not None
        if arm != "NATIVE_LONG":
            assert len(selected) <= 8
    oracle_selected = select_for_arm(task, "GOLD_ORACLE", budget_docs=8)
    assert oracle_selected is not None
    assert set(task.gold_ids).issubset({doc.doc_id for doc in oracle_selected})
    envelope = strip_gold_fields(_task_to_adapter_envelope(task))
    assert "verdict" not in envelope
    panel = run_offline_panel(phase="dev", n_per_cell=1, pressures=(32_000,), budget_docs=8)
    assert panel["summary"]["model_runs"] == 0
    assert set(panel["summary"]["arms"]) == set(RETRIEVAL_ARMS)


def main() -> int:
    offline_selftest()
    print(json.dumps(run_offline_panel()["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
