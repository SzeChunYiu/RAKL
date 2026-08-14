import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "training_ladder" / "phase2_adaptive_v1.py"


def _module():
    spec = importlib.util.spec_from_file_location("p4_phase2_adaptive_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v3_protocol_is_only_outcome_authorizing_freeze():
    m = _module()
    protocol, inference = m._check_freeze()
    assert protocol["schema_version"] == "rakl-paper4-phase2-freeze-v3"
    assert protocol["outcomes_accessed_before_v3_freeze"] is False
    assert protocol["training"]["model_revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
    assert protocol["training"]["epochs"] == 12
    assert protocol["training"]["lora"]["dropout"] == 0.0
    assert inference["outcomes_accessed_before_freeze"] is False


def test_train_selection_and_assurance_are_case_and_prompt_disjoint():
    m = _module()
    protocol, _ = m._check_freeze()
    train, selection, assurance = m._build_data(protocol)
    train_ids = {x.case_id for rows in train.values() for x in rows}
    selection_ids = {x.case_id for rows in selection.values() for x in rows}
    assurance_ids = {x.case_id for rows in assurance.values() for x in rows}
    assert not train_ids & selection_ids
    assert not train_ids & assurance_ids
    assert not selection_ids & assurance_ids
    train_prompts = {x.prompt for rows in train.values() for x in rows}
    selection_prompts = {x.prompt for rows in selection.values() for x in rows}
    assurance_prompts = {x.prompt for rows in assurance.values() for x in rows}
    assert not train_prompts & selection_prompts
    assert not train_prompts & assurance_prompts
    assert not selection_prompts & assurance_prompts


def test_static_arm_is_exact_equal_structural_mix():
    m = _module()
    protocol, _ = m._check_freeze()
    train, _, _ = m._build_data(protocol)
    rows, trace = m._static_mix(train, protocol, protocol["training"]["training_seed"])
    assert len(rows) == 48
    assert Counter(trace) == Counter({exposure: 8 for exposure in m.EXPOSURES})


def test_uniform_random_and_semantic_diversity_never_read_gold_for_selection(monkeypatch):
    m = _module()
    protocol, _ = m._check_freeze()
    train, _, _ = m._build_data(protocol)
    # Replace gold with explosive objects. Both policies are required to select
    # solely from identity/prompt surfaces and must therefore still run.
    class Explosive:
        def __str__(self):
            raise AssertionError("gold was inspected by non-model selection policy")
    mutated = {
        exposure: [m.Example(x.case_id, x.exposure, x.prompt, Explosive()) for x in rows]
        for exposure, rows in train.items()
    }
    a, _ = m._uniform_random(mutated, 46601, 48)
    b, _ = m._semantic_diversity(mutated, 46601, 48)
    assert len(a) == 48
    assert len(b) == 48


def test_fresh_assurance_is_equal_stratum_and_large_enough_for_registered_mde():
    m = _module()
    protocol, _ = m._check_freeze()
    _, _, assurance = m._build_data(protocol)
    assert {k: len(v) for k, v in assurance.items()} == {k: 64 for k in m.EXPOSURES}
    assert sum(map(len, assurance.values())) == 384


def test_holm_is_monotone_and_never_smaller_than_raw_p():
    m = _module()
    raw = {"E-D": 0.01, "E-C": 0.03, "D-B": 0.04}
    adjusted = m._holm(raw)
    assert all(adjusted[k] >= raw[k] for k in raw)
    ordered = sorted(raw, key=raw.get)
    assert [adjusted[k] for k in ordered] == sorted(adjusted[k] for k in ordered)


def test_dry_run_writes_only_data_manifest_not_scientific_result(tmp_path):
    m = _module()
    rc = m.run(tmp_path, dry_run=True)
    assert rc == 0
    assert (tmp_path / "DATA_MANIFEST.json").exists()
    assert not (tmp_path / "FINAL_RECEIPT.json").exists()
    payload = json.loads((tmp_path / "DATA_MANIFEST.json").read_text())
    assert payload["sha256"].startswith("sha256:")
