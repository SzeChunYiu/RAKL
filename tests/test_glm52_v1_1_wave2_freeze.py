from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1_1"
V1 = ROOT / "research" / "glm52_mechanism_suite_v1"
SRC = ROOT / "src"

for path in (SRC, SUITE, V1):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _load(name: str):
    return importlib.import_module(name)


def test_wave2_freeze_receipt_matches_live_builder() -> None:
    mod = _load("wave2_freeze")
    failures = mod.validate_committed_receipts(ROOT)
    assert failures == []


def test_no_new_glm_outcome_receipt_blocks_live_runs() -> None:
    receipt = json.loads((SUITE / "NO_NEW_GLM_OUTCOME_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["outcome_access_status"] == "NO_NEW_GLM_OUTCOME"
    assert receipt["model_runs"] == 0
    assert receipt["grants_scientific_authority"] is False
    assert "hosted_dev_gates:not_passed_on_live_model" in receipt["live_run_blockers"]


def test_wave2_freeze_binds_all_three_lanes_without_model_runs() -> None:
    freeze = json.loads((SUITE / "WAVE2_FREEZE_RECEIPT.json").read_text(encoding="utf-8"))
    lanes = freeze["wave2_lanes"]
    assert lanes["lane2_selective_retrieval"]["model_runs"] == 0
    assert lanes["lane3_experience_transfer"]["model_runs"] == 0
    assert lanes["lane4_trajectory_governance"]["model_runs"] == 0


def test_empirical_instrument_bindings_reference_paper2_and_paper3_scaffolds() -> None:
    bindings = json.loads((SUITE / "EMPIRICAL_INSTRUMENT_BINDINGS.json").read_text(encoding="utf-8"))
    assert bindings["paper2"]["matched_a3_a4_arms"]["module"].endswith("ablation_a3_a4_matched_empirical.py")
    assert bindings["paper2"]["microtrial_ingest_hooks"]["matched_microtrial"].endswith("matched_microtrial.py")
    assert bindings["paper3"]["semantic_descriptor_builder"]["builder"] == "build_semantic_descriptor_receipt"
    assert (ROOT / bindings["paper2"]["matched_a3_a4_arms"]["packet"]).is_file()
    assert (ROOT / bindings["paper3"]["semantic_descriptor_builder"]["lunarc_contract"]).is_file()
    assert (ROOT / bindings["paper3"]["semantic_descriptor_builder"]["lunarc_runtime"]).is_file()
