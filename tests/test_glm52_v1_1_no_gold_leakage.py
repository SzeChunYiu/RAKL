from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1_1"
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SUITE) not in sys.path:
    sys.path.insert(0, str(SUITE))


def test_strip_gold_fields_removes_hidden_labels() -> None:
    mod = importlib.import_module("framework_adapter")
    task = {
        "task_id": "T1",
        "question": "q",
        "entity": "e",
        "qoi": "q",
        "context": "c",
        "verdict": "SUPPORT",
        "support_ids": ["D1"],
        "hidden_truth": "SUPPORT",
        "docs": [{"doc_id": "D1", "summary": "visible", "is_gold": True, "finding_label": "SUPPORT"}],
    }
    visible = mod.strip_gold_fields(task)
    assert "verdict" not in visible
    assert "support_ids" not in visible
    assert "hidden_truth" not in visible
    doc_visible = mod.visible_doc(task["docs"][0])
    assert "is_gold" not in doc_visible
    assert "finding_label" not in doc_visible


def test_retrieval_rejects_benchmark_target_leak_candidates() -> None:
    mod = importlib.import_module("framework_adapter")
    adapter = mod.CanonicalFrameworkAdapter(repo_root=ROOT)
    task = {
        "task_id": "LEAK-1",
        "question": "Assess claim",
        "entity": "alpha",
        "qoi": "period",
        "context": "target",
        "docs": [
            {
                "doc_id": "GOOD",
                "entity": "alpha",
                "qoi": "period",
                "context": "target",
                "root": "r1",
                "kind": "measurement",
                "date": 2024,
                "summary": "ordinary measurement text",
            },
            {
                "doc_id": "LEAK",
                "entity": "alpha",
                "qoi": "period",
                "context": "target",
                "root": "r2",
                "kind": "measurement",
                "date": 2024,
                "summary": "contains gold_answer token",
            },
        ],
        "verdict": "SUPPORT",
        "support_ids": ["GOOD"],
    }
    receipt = adapter.retrieve(task, budget=4)
    assert "LEAK" not in receipt.selected_candidate_ids
    assert any(flag == "BENCHMARK_TARGET_LEAK" for _, flag in receipt.rejected_spam_flags)


def test_task_manifest_hash_ignores_gold_fields() -> None:
    mod = importlib.import_module("framework_adapter")
    adapter = mod.CanonicalFrameworkAdapter(repo_root=ROOT)
    base = {
        "task_id": "H1",
        "question": "q",
        "entity": "e",
        "qoi": "q",
        "context": "c",
        "docs": [],
    }
    with_gold = {**base, "verdict": "SUPPORT", "support_ids": ["D1"]}
    r1 = adapter.retrieve(base, budget=1)
    r2 = adapter.retrieve(with_gold, budget=1)
    assert r1.task_manifest_hash == r2.task_manifest_hash
