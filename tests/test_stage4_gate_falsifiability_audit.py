"""The Stage-4 capability gate must be shown able to fail before it spends a budget.

The value of this audit is entirely in its controls. A gate that rejects a
perfect responder is mis-specified and its probe results mean nothing; a gate
that accepts a constant responder is a rubber stamp. Both are asserted here, and
both must keep holding, because this gate is what stands between the Paper III
fresh-task-lift lane and its next confirmatory run.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SRC = ROOT / "experiments" / "paper3" / "audit_stage4_gate_falsifiability.py"
RECEIPT = (
    ROOT
    / "research"
    / "paper3_gate_falsifiability_audit_v1"
    / "STAGE4_GATE_FALSIFIABILITY_AUDIT.json"
)


@pytest.fixture(scope="module")
def audit():
    spec = importlib.util.spec_from_file_location("stage4_audit", AUDIT_SRC)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["stage4_audit"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fixture_set(audit):
    freeze = json.loads(audit.FREEZE_PATH.read_text())
    tasks = audit.PANEL.build()
    return tasks, freeze, audit.oracle_records(tasks)


def test_oracle_responder_passes_the_gate(audit, fixture_set):
    """Control. If a perfect answer fails, the gate is mis-specified, not strict."""
    tasks, freeze, records = fixture_set
    assert len(tasks) == 132
    assert audit.make_gate(tasks, freeze)(records) is True


def test_constant_responders_are_all_rejected(audit, fixture_set):
    """Control. A gate a constant answer can clear is a rubber stamp."""
    tasks, freeze, _ = fixture_set
    shortcut = audit.RUNNER._shortcut_audit(list(tasks), freeze)
    assert shortcut["clean"] is True
    assert not any(shortcut["responders"].values())


@pytest.mark.parametrize(
    "probe_id",
    [
        "shuffle_verdicts_across_tasks",
        "shuffle_selected_evidence_ids",
        "swap_selected_and_rejected",
        "make_10pct_unparseable",
    ],
)
def test_destroying_the_answer_makes_the_gate_fail(audit, fixture_set, probe_id):
    """The gate must depend on the model actually being right."""
    import random

    tasks, freeze, records = fixture_set
    gate = audit.make_gate(tasks, freeze)
    perturbed = audit.PERTURBATIONS[probe_id](records, random.Random(f"test:{probe_id}"))
    assert gate(perturbed) is False, f"gate survived {probe_id} — it is not reading the answer"


def test_score_does_not_mutate_the_caller_records(audit, fixture_set):
    """_score annotates records in place; the gate wrapper must isolate that.

    Without the deep copy the first probe would poison every later one and the
    audit would silently measure the wrong thing.
    """
    tasks, freeze, records = fixture_set
    before = copy.deepcopy(records)
    audit.make_gate(tasks, freeze)(records)
    assert records == before


def test_recorded_verdict_is_falsifiable_and_grants_nothing():
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["verdict"] == "FALSIFIABLE"
    assert receipt["controls"]["oracle_responder_passes"] is True
    assert receipt["controls"]["shipped_shortcut_audit_clean"] is True
    assert receipt["grants_scientific_authority"] is False
    # A FALSIFIABLE verdict must never be recorded as qualifying a model.
    assert "does not qualify any model" in receipt["interpretation"]
