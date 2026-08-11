"""Known-answer and hostile leakage tests for Paper 5 active sham matcher/validator.

These tests never open confirmatory four-arm outcomes. They only check that the
frozen sham construction algorithm matches budgets and fail-closes on leakage.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "research" / "paper5_sham_policy_v1" / "SHAM_POLICY.json"
RECEIPT_PATH = ROOT / "research" / "paper5_sham_policy_v1" / "SHAM_POLICY_FREEZE_RECEIPT.json"
SCHEMA_PATH = ROOT / "schemas" / "paper5-sham-policy-v1.schema.json"
MODULE_PATH = ROOT / "experiments" / "paper5" / "active_sham.py"


def _load_module() -> Any:
    import sys

    spec = importlib.util.spec_from_file_location("paper5_active_sham", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Python 3.13 dataclasses require the module to be present in sys.modules
    # while processing @dataclass at import time.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _obj(mod: Any, **kwargs: Any) -> Any:
    content = kwargs.pop("content_text")
    defaults = {
        "token_count": mod.estimate_token_count(content),
        "recency_rank": 1,
        "authority_level": "CANDIDATE",
        "content_hash": mod.canonical_sha256({"content_text": content}),
        "solution_artifact_ids": (),
    }
    defaults.update(kwargs)
    defaults["content_text"] = content
    return mod.MemoryObject(**defaults)


@pytest.fixture(scope="module")
def sham() -> Any:
    return _load_module()


@pytest.fixture(scope="module")
def policy(sham: Any) -> dict[str, Any]:
    return sham.load_policy(POLICY_PATH)


def test_frozen_policy_matches_schema_and_self_hash(policy: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(policy)
    assert policy["grants_scientific_authority"] is False
    assert policy["authorizes_confirmatory_execution"] is False
    assert policy["evaluated_results_accessed"] is False


def test_freeze_receipt_refuses_confirmatory_authority(sham: Any) -> None:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt["authorizes_confirmatory_execution"] is False
    assert receipt["grants_scientific_authority"] is False
    assert receipt["evaluated_results_accessed"] is False
    assert (
        receipt["confirmatory_four_arm_status"]
        == "UNAUTHORIZED_UNTIL_CAPABLE_MODEL_AND_FULL_PACKET_FREEZE"
    )
    assert receipt["policy_canonical_sha256"] == json.loads(POLICY_PATH.read_text())[
        "policy_canonical_sha256"
    ]
    assert receipt["matcher_module_sha256"] == sham.sha256_file(MODULE_PATH)
    assert receipt["policy_file_sha256"] == sham.sha256_file(POLICY_PATH)


def test_known_answer_clean_construction_passes(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="algebra-family",
            structural_signature=("rank-2", "local-section"),
            content_text="prefer local section check before global gluing claim",
            source_lineage_id="lineage-L1",
            recency_rank=1,
        ),
        _obj(
            sham,
            object_id="L2",
            object_type="failure",
            family_id="algebra-family",
            structural_signature=("authority-poset",),
            content_text="prediction success does not mint mechanism authority",
            source_lineage_id="lineage-L2",
            recency_rank=2,
        ),
        _obj(
            sham,
            object_id="L3",
            object_type="episode",
            family_id="algebra-family",
            structural_signature=("fresh-assurance",),
            content_text="fresh assurance packet required after method edit",
            source_lineage_id="lineage-L3",
            recency_rank=3,
        ),
    ]
    controls = [
        _obj(
            sham,
            object_id="C1",
            object_type="lesson",
            family_id="optics-family",
            structural_signature=("wave-optics", "interference"),
            content_text="match fringe spacing before claiming coherent source identity",
            source_lineage_id="lineage-C1",
            recency_rank=1,
        ),
        _obj(
            sham,
            object_id="C2",
            object_type="failure",
            family_id="optics-family",
            structural_signature=("detector-noise",),
            content_text="do not treat detector offset as a new physical law",
            source_lineage_id="lineage-C2",
            recency_rank=2,
        ),
        _obj(
            sham,
            object_id="C3",
            object_type="episode",
            family_id="optics-family",
            structural_signature=("calibration",),
            content_text="recalibrate intensity scale under frozen protocol",
            source_lineage_id="lineage-C3",
            recency_rank=3,
        ),
        # Extra unused control of wrong structural family to ensure selection is selective.
        _obj(
            sham,
            object_id="C4",
            object_type="tool",
            family_id="chemistry-family",
            structural_signature=("titration",),
            content_text="record endpoint volume before inferring concentration",
            source_lineage_id="lineage-C4",
            recency_rank=4,
        ),
    ]
    exclusion = sham.TargetExclusion(
        eligible_true_match_signatures=frozenset({"rank-2", "local-section", "authority-poset"}),
        forbidden_solution_artifact_ids=frozenset({"sol-algebra-42"}),
        hidden_answer_strings=frozenset({"HIDDEN_ANSWER_ALPHA"}),
    )
    result = sham.construct_active_sham(
        policy=policy,
        learned_objects=learned,
        control_pool=controls,
        exclusion=exclusion,
    )
    assert result.authorizes_confirmatory_execution is False
    assert set(result.selected_control_ids) == {"C1", "C2", "C3"}
    report = sham.validate_active_sham(
        policy=policy,
        learned_objects=learned,
        sham_objects=result.sham_objects,
        exclusion=exclusion,
    )
    assert report.status == "PASS"
    assert report.blockers == ()
    assert report.checks["no_eligible_true_match_signatures"] is True
    assert report.checks["no_answer_substring_overlap"] is True
    assert report.checks["type_histogram_matched"] is True
    assert report.checks["disjoint_family"] is True


def test_hostile_answer_leakage_fails_validator(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="fam-a",
            structural_signature=("sig-a",),
            content_text="keep evaluation targets hidden from solvers",
            source_lineage_id="lin-L1",
        )
    ]
    leaking = [
        _obj(
            sham,
            object_id="BAD",
            object_type="lesson",
            family_id="fam-b",
            structural_signature=("sig-b",),
            content_text="remember the gold label is HIDDEN_ANSWER_ALPHA for this task",
            source_lineage_id="lin-BAD",
        )
    ]
    exclusion = sham.TargetExclusion(
        eligible_true_match_signatures=frozenset({"sig-a"}),
        hidden_answer_strings=frozenset({"HIDDEN_ANSWER_ALPHA"}),
    )
    report = sham.validate_active_sham(
        policy=policy,
        learned_objects=learned,
        sham_objects=leaking,
        exclusion=exclusion,
    )
    assert report.status == "FAIL"
    assert any(b.startswith("sham_memory_answer_leakage:") for b in report.blockers)


def test_hostile_eligible_structural_match_fails_validator(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="fam-a",
            structural_signature=("sig-a",),
            content_text="structural coordinates must stay incompatible under sham",
            source_lineage_id="lin-L1",
        )
    ]
    near_miss = [
        _obj(
            sham,
            object_id="NEAR",
            object_type="lesson",
            family_id="fam-b",
            structural_signature=("sig-eligible", "noise"),
            content_text="this control still carries an eligible true-match signature",
            source_lineage_id="lin-NEAR",
        )
    ]
    exclusion = sham.TargetExclusion(
        eligible_true_match_signatures=frozenset({"sig-eligible"}),
        hidden_answer_strings=frozenset(),
    )
    report = sham.validate_active_sham(
        policy=policy,
        learned_objects=learned,
        sham_objects=near_miss,
        exclusion=exclusion,
    )
    assert report.status == "FAIL"
    assert any(b.startswith("sham_eligible_structural_true_match:") for b in report.blockers)


def test_matcher_refuses_eligible_or_same_family_controls(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="shared-family",
            structural_signature=("keep",),
            content_text="learned lesson about invariant preservation under rewrite",
            source_lineage_id="lin-L1",
        )
    ]
    bad_pool = [
        _obj(
            sham,
            object_id="SAME",
            object_type="lesson",
            family_id="shared-family",
            structural_signature=("other",),
            content_text="same family must not be selected as a sham control",
            source_lineage_id="lin-SAME",
        ),
        _obj(
            sham,
            object_id="ELIG",
            object_type="lesson",
            family_id="other-family",
            structural_signature=("eligible-sig",),
            content_text="eligible structural signature must be excluded from sham",
            source_lineage_id="lin-ELIG",
        ),
    ]
    exclusion = sham.TargetExclusion(
        eligible_true_match_signatures=frozenset({"eligible-sig"}),
    )
    with pytest.raises(ValueError, match="no eligible disjoint-family sham controls"):
        sham.construct_active_sham(
            policy=policy,
            learned_objects=learned,
            control_pool=bad_pool,
            exclusion=exclusion,
        )


def test_gibberish_only_controls_rejected(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="fam-a",
            structural_signature=("sig-a",),
            content_text="real procedural lesson text with enough tokens here",
            source_lineage_id="lin-L1",
        )
    ]
    gibberish = [
        _obj(
            sham,
            object_id="G1",
            object_type="lesson",
            family_id="fam-b",
            structural_signature=("sig-b",),
            content_text="asdf asdf asdf asdf",
            source_lineage_id="lin-G1",
        )
    ]
    exclusion = sham.TargetExclusion(eligible_true_match_signatures=frozenset({"sig-a"}))
    report = sham.validate_active_sham(
        policy=policy,
        learned_objects=learned,
        sham_objects=gibberish,
        exclusion=exclusion,
    )
    assert report.status == "FAIL"
    assert any(b.startswith("sham_gibberish_only_controls:") for b in report.blockers)


def test_solution_artifact_id_leakage_fails(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="fam-a",
            structural_signature=("sig-a",),
            content_text="do not attach evaluator-private solution artifacts to sham",
            source_lineage_id="lin-L1",
        )
    ]
    leaking = [
        _obj(
            sham,
            object_id="S1",
            object_type="lesson",
            family_id="fam-b",
            structural_signature=("sig-b",),
            content_text="procedural text that still carries a forbidden artifact id",
            source_lineage_id="lin-S1",
            solution_artifact_ids=("sol-task-9",),
        )
    ]
    exclusion = sham.TargetExclusion(
        eligible_true_match_signatures=frozenset({"sig-a"}),
        forbidden_solution_artifact_ids=frozenset({"sol-task-9"}),
    )
    report = sham.validate_active_sham(
        policy=policy,
        learned_objects=learned,
        sham_objects=leaking,
        exclusion=exclusion,
    )
    assert report.status == "FAIL"
    assert any(b.startswith("sham_solution_artifact_leakage:") for b in report.blockers)


def test_memory_object_from_dict_rejects_answer_fields(sham: Any) -> None:
    with pytest.raises(ValueError, match="forbidden answer fields"):
        sham.memory_object_from_dict(
            {
                "object_id": "X",
                "object_type": "lesson",
                "family_id": "f",
                "structural_signature": ["s"],
                "content_text": "text with enough tokens for validity checks here",
                "recency_rank": 1,
                "authority_level": "CANDIDATE",
                "source_lineage_id": "lin",
                "target_answer": "42",
            }
        )


def test_construction_is_deterministic_under_frozen_seed(sham: Any, policy: dict[str, Any]) -> None:
    learned = [
        _obj(
            sham,
            object_id="L1",
            object_type="lesson",
            family_id="fam-a",
            structural_signature=("sig-a",),
            content_text="deterministic construction must not drift across reruns",
            source_lineage_id="lin-L1",
            recency_rank=1,
            token_count=12,
        ),
        _obj(
            sham,
            object_id="L2",
            object_type="episode",
            family_id="fam-a",
            structural_signature=("sig-b",),
            content_text="second learned object for histogram matching coverage",
            source_lineage_id="lin-L2",
            recency_rank=2,
            token_count=11,
        ),
    ]
    controls = []
    for i in range(6):
        controls.append(
            _obj(
                sham,
                object_id=f"C{i}",
                object_type="lesson" if i % 2 == 0 else "episode",
                family_id="fam-control",
                structural_signature=(f"ctrl-{i}",),
                content_text=f"control lesson number {i} with stable procedural wording",
                source_lineage_id=f"lin-C{i}",
                recency_rank=i + 1,
                token_count=10 + (i % 3),
            )
        )
    exclusion = sham.TargetExclusion(eligible_true_match_signatures=frozenset({"sig-a", "sig-b"}))
    a = sham.construct_active_sham(
        policy=policy, learned_objects=learned, control_pool=controls, exclusion=exclusion
    )
    b = sham.construct_active_sham(
        policy=policy, learned_objects=learned, control_pool=controls, exclusion=exclusion
    )
    assert a.selected_control_ids == b.selected_control_ids
    assert a.construction_receipt_sha256 == b.construction_receipt_sha256


def test_freeze_policy_refuses_overwrite(sham: Any, tmp_path: Path) -> None:
    sham.freeze_policy_artifact(tmp_path, construction_seed=1, notes="tmp")
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        sham.freeze_policy_artifact(tmp_path, construction_seed=1, notes="tmp")
