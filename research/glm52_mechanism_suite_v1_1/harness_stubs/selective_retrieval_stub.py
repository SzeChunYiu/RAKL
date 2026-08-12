from __future__ import annotations

from typing import Any, Mapping

from harness.selective_retrieval_harness import RETRIEVAL_ARMS, evaluate_headroom_gate, run_offline_panel, select_for_arm
from selective_retrieval import EvidenceDoc, RetrievalTask  # type: ignore[import-not-found]


def run_stub(task: Mapping[str, Any], budget: int = 8) -> dict[str, Any]:
    docs = tuple(EvidenceDoc(**doc) if isinstance(doc, dict) else doc for doc in task.get("docs", ()))
    retrieval_task = RetrievalTask(
        task_id=str(task.get("task_id", "stub")),
        family=str(task.get("family", "scope")),
        question=str(task.get("question", "")),
        entity=str(task.get("entity", "")),
        qoi=str(task.get("qoi", "")),
        context=str(task.get("context", "")),
        docs=docs,
        verdict=str(task.get("verdict", "CANNOT_CHECK")),
        support_ids=tuple(task.get("support_ids", ())),
        refute_ids=tuple(task.get("refute_ids", ())),
    )
    selected = select_for_arm(retrieval_task, "CURRENT_RAKL_EPISTEMIC_SEARCH", budget_docs=budget)
    panel = run_offline_panel(phase="dev", n_per_cell=1, pressures=(32_000,), budget_docs=budget)
    return {
        "experiment": "selective_retrieval",
        "lane": 2,
        "arms": list(RETRIEVAL_ARMS),
        "arm": "CURRENT_RAKL_EPISTEMIC_SEARCH",
        "outcome_access": "NO_NEW_GLM_OUTCOME",
        "selected_ids": [doc.doc_id for doc in selected] if selected else [],
        "dev_gate": evaluate_headroom_gate(panel["summary"]),
        "model_runs": 0,
    }
