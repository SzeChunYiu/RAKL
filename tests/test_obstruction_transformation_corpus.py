"""Tests for obstruction–transformation corpus v1 (#402) and #352 terminal."""

from __future__ import annotations

from pathlib import Path

import pytest

from rakl.obstruction_transformation_corpus import (
    DESIGN_FIXTURE_EPISODE_IDS,
    classify_pair_relation,
    load_episode_rows,
    load_transformation_memory,
    refuse_synthetic_verified_promotion,
    validate_corpus,
)
from rakl.semantic_shortcut import TransformationEpisodeAuthority

ROOT = Path(__file__).resolve().parents[1]


def test_corpus_v1_validates_and_loads_runtime_memory() -> None:
    report = validate_corpus(ROOT)
    assert report.ok is True, report.reasons
    assert report.episode_count == 15
    assert report.grants_scientific_authority is False
    assert report.authority_counts["PROPOSAL_ONLY"] == 12
    assert report.authority_counts["VERIFIED_LOCAL"] == 2
    assert report.authority_counts["SUPERSEDED"] == 1

    memory = load_transformation_memory(ROOT)
    assert memory.memory_id == "otc-v1-seed-memory"
    assert memory.snapshot_hash == report.snapshot_hash
    assert len(memory.episodes) == 15
    # Proposal-only and superseded must not be treated as verified authorities.
    verified = {
        TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED,
        TransformationEpisodeAuthority.VERIFIED_LOCAL,
        TransformationEpisodeAuthority.PROOF_BACKED,
    }
    assert sum(1 for ep in memory.episodes if ep.authority in verified) == 2


def test_corpus_blocks_synthetic_verified_promotion() -> None:
    with pytest.raises(PermissionError, match="verified authority refused"):
        refuse_synthetic_verified_promotion(
            authority="SOURCE_EVENT_VERIFIED",
            has_source_verification_receipt=False,
        )
    refuse_synthetic_verified_promotion(
        authority="PROPOSAL_ONLY",
        has_source_verification_receipt=False,
    )
    refuse_synthetic_verified_promotion(
        authority="VERIFIED_LOCAL",
        has_source_verification_receipt=True,
    )


def test_corpus_dedup_keeps_material_precondition_and_forbidden_loss_splits() -> None:
    rows = load_episode_rows(ROOT)
    by_id = {row["episode_id"]: row for row in rows}
    restated = classify_pair_relation(
        by_id["OTC-V1-ALG-FINITE-REVISITATION-VISITED-SET"],
        by_id["OTC-V1-ALG-FINITE-REVISITATION-MARK-ARRAY"],
    )
    assert restated == "same_mechanism_restated_vocabulary"
    near_miss = classify_pair_relation(
        by_id["OTC-V1-ALG-FINITE-REVISITATION-VISITED-SET"],
        by_id["OTC-V1-ALG-FINITE-REVISITATION-ALLOW-REVISIT-CACHE"],
    )
    assert near_miss == "hostile_near_miss_shared_failure_divergent_forbidden_loss"
    different_transform = classify_pair_relation(
        by_id["OTC-V1-MATH-FORALL-BY-EXAMPLES-COUNTEREXAMPLE-FIRST"],
        by_id["OTC-V1-MATH-FORALL-BY-EXAMPLES-INDUCTION-SCHEMA"],
    )
    assert different_transform == "same_obstruction_different_transformation"


def test_corpus_splits_exclude_design_fixtures_for_issue_401() -> None:
    import json

    splits = json.loads(
        (ROOT / "research/obstruction_transformation_corpus_v1/SPLIT_MANIFEST.json").read_text(
            encoding="utf-8"
        )
    )
    leakage = json.loads(
        (ROOT / "research/obstruction_transformation_corpus_v1/LEAKAGE_AUDIT.json").read_text(
            encoding="utf-8"
        )
    )
    assert splits["bound_issue_for_confirmatory_eval"] == 401
    eval_ids = set(splits["partitions"]["EVALUATION_MEMORY"]["episode_ids"])
    fresh_ids = set(splits["partitions"]["FRESH_TARGETS"]["episode_ids"])
    assert not (eval_ids & DESIGN_FIXTURE_EPISODE_IDS)
    assert not (fresh_ids & DESIGN_FIXTURE_EPISODE_IDS)
    assert DESIGN_FIXTURE_EPISODE_IDS.issubset(
        set(leakage["design_fixture_episode_ids_excluded"])
    )


def test_corpus_binds_existing_issue_352_capability_terminal_as_evidence() -> None:
    """#352 already closed honestly under CAPABLE_MODEL=NO_REFUTED; corpus may cite it."""
    import json

    path = (
        ROOT
        / "research/capability_gated_closeout_20260812/ISSUE_352_TERMINAL_RECEIPT.json"
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert receipt["issue"] == 352
    assert receipt["grants_scientific_authority"] is False
    assert receipt["CAPABLE_MODEL_AVAILABLE"] == "NO_REFUTED"
    rows = load_episode_rows(ROOT)
    a3a4 = next(
        row for row in rows if row["episode_id"] == "OTC-V1-RAKL-A3A4-MATCHED-BLOCKED"
    )
    assert str(path.relative_to(ROOT)) in a3a4["evidence_pointers"]
