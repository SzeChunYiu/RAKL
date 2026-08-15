"""Tests for the E15 restore drill over the real ORION stores.

These assert the drill's load-bearing properties, not the whole campaign:

  * the legitimate restore is NOT flagged (a checker that only ever says "equal"
    or only ever says "broken" proves nothing, so both directions are asserted);
  * a plane that is absent comes back CANNOT_CHECK, never an empty-equals-empty
    pass, and probing it does not fabricate the missing store;
  * a byte-clean tree with divergent logical state IS caught, which is the whole
    reason the drill re-opens the stores instead of trusting the manifest.
"""

from __future__ import annotations

import importlib.util
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DRILL_PATH = REPO_ROOT / "research" / "orion_engineering_closure_v1" / "run_restore_drill.py"


def _load_drill():
    spec = importlib.util.spec_from_file_location("orion_restore_drill", DRILL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


drill = _load_drill()


@pytest.fixture(scope="module")
def drill_env():
    """Populate the real stores once, back them up, and hand out the artefacts."""

    work = Path(tempfile.mkdtemp(prefix="test-restore-drill-"))
    try:
        live_root = work / "live"
        live = drill.populate_phase_one(live_root)
        frozen_archive, _ = drill.make_backup(live_root, work, "frozen", live.frozen_snapshot_id)
        frozen_live = drill.copy.deepcopy(live)
        frozen_live.current_wf1_head = live.frozen_wf1_head
        frozen_reference = drill.logical_fingerprint(live_root, frozen_live)

        drill.populate_phase_two(live_root, live)
        archive, manifest = drill.make_backup(live_root, work, "current", live.snapshot_ids[-1])
        reference = drill.logical_fingerprint(live_root, live)
        yield {
            "work": work,
            "live": live,
            "archive": archive,
            "manifest": manifest,
            "reference": reference,
            "frozen_archive": frozen_archive,
            "frozen_live": frozen_live,
            "frozen_reference": frozen_reference,
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_population_touches_every_plane(drill_env):
    """The drill must populate real content, or every later comparison is vacuous."""

    reference = drill_env["reference"]
    assert set(reference) == set(drill.PLANES)
    assert all(plane["status"] == drill.RECONSTRUCTED for plane in reference.values())
    assert reference["evidence"]["count"] == 3
    assert len(reference["semantic"]["atom_version_ids"]) == 4
    assert reference["atlas"]["plane_counts"]["atlas_charts"] == 4
    assert reference["control_metrics_saturation_gates_decisions_residuals"]["count"] == 6
    assert reference["epistemic_status"]["present"] is True
    assert reference["workflow_history"]["wf-1"]["status"] == "COMPLETED"
    assert reference["workflow_history"]["wf-2"]["status"] == "RECOVERY_REQUIRED"
    assert reference["blobs"]["dangling_evidence_payloads"] == []


def test_clean_restore_is_exact_and_semantically_identical(drill_env):
    """NO-ALARM CONTROL: a legitimate restore must pass byte-wise AND semantically."""

    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-clean")
    verdict, offenders = drill.verify_restore(restored, drill_env["manifest"])
    assert verdict is drill.RestoreVerdict.EXACT
    assert offenders == ()

    planes = drill.compare_planes(
        drill_env["reference"], drill.logical_fingerprint(restored, drill_env["live"])
    )
    assert planes == {plane: drill.EQUAL for plane in drill.PLANES}


def test_workflow_hash_chain_verifies_against_its_sealed_head(drill_env):
    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-chain")
    fingerprint = drill.logical_fingerprint(restored, drill_env["live"])
    for workflow_id in ("wf-1", "wf-2"):
        entry = fingerprint["workflow_history"][workflow_id]
        assert entry["chain_valid"] is True
        assert entry["chain_valid_vs_sealed_current_head"] is True


def test_absent_plane_is_cannot_check_and_is_not_fabricated(drill_env):
    """A missing store must not be silently recreated as an empty one that 'matches'."""

    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-partial")
    (restored / drill.ATLAS_DB).unlink()

    verdict, offenders = drill.verify_restore(restored, drill_env["manifest"])
    assert verdict is drill.RestoreVerdict.MISSING_BLOB
    assert drill.ATLAS_DB in offenders

    fingerprint = drill.logical_fingerprint(restored, drill_env["live"])
    assert fingerprint["atlas"]["status"] == drill.CANNOT_CHECK
    # probing the plane must not have created the file it was looking for
    assert not (restored / drill.ATLAS_DB).exists()

    planes = drill.compare_planes(drill_env["reference"], fingerprint)
    assert planes["atlas"] == drill.CANNOT_CHECK
    assert planes["atlas"] != drill.EQUAL
    for plane in ("project_snapshots", "evidence", "semantic", "workflow_history", "blobs"):
        assert planes[plane] == drill.EQUAL


def test_corrupted_blob_is_detected_byte_wise_and_as_a_dangling_pointer(drill_env):
    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-corrupt")
    blob = sorted(p for p in (restored / drill.BLOB_DIR).rglob("*") if p.is_file())[0]
    blob.write_bytes(b"corrupted")

    verdict, offenders = drill.verify_restore(restored, drill_env["manifest"])
    assert verdict is drill.RestoreVerdict.CORRUPTED_BLOB
    assert len(offenders) == 1

    fingerprint = drill.logical_fingerprint(restored, drill_env["live"])
    assert len(fingerprint["blobs"]["dangling_evidence_payloads"]) == 1


def test_missing_blob_is_detected(drill_env):
    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-missing")
    sorted(p for p in (restored / drill.BLOB_DIR).rglob("*") if p.is_file())[0].unlink()

    verdict, _ = drill.verify_restore(restored, drill_env["manifest"])
    assert verdict is drill.RestoreVerdict.MISSING_BLOB
    fingerprint = drill.logical_fingerprint(restored, drill_env["live"])
    assert len(fingerprint["blobs"]["dangling_evidence_payloads"]) == 1


def test_tampered_manifest_is_rejected(drill_env):
    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-tamper")
    tampered = drill.copy.copy(drill_env["manifest"])
    entries = dict(drill_env["manifest"].entries)
    entries[sorted(entries)[0]] = "0" * 64
    object.__setattr__(tampered, "entries", entries)

    verdict, _ = drill.verify_restore(restored, tampered)
    assert verdict is drill.RestoreVerdict.MANIFEST_TAMPERED


def test_byte_clean_tree_with_divergent_logical_state_is_caught(drill_env):
    """CHECKER VALIDATION.

    The manifest is re-derived from the mutated tree, so byte verification is EXACT
    by construction. Only the semantic re-open can catch this. If it did not, the
    semantic half of the drill would prove nothing.
    """

    restored = drill.fresh_restore(drill_env["archive"], drill_env["work"], "t-diverge")
    db = sqlite3.connect(restored / drill.ORION_DB)
    try:
        db.execute(
            "DELETE FROM workflow_events WHERE workflow_id='wf-1' AND sequence="
            "(SELECT MAX(sequence) FROM workflow_events WHERE workflow_id='wf-1')"
        )
        db.commit()
    finally:
        db.close()

    self_manifest = drill.take_backup(restored, backup_id="self", created_at=drill.NOW)
    verdict, _ = drill.verify_restore(restored, self_manifest)
    assert verdict is drill.RestoreVerdict.EXACT, "bytes must agree, or the case proves nothing"

    fingerprint = drill.logical_fingerprint(restored, drill_env["live"])
    planes = drill.compare_planes(drill_env["reference"], fingerprint)
    assert planes["workflow_history"] == drill.DIVERGED
    assert fingerprint["workflow_history"]["wf-1"]["chain_valid"] is False
    assert fingerprint["workflow_history"]["wf-1"]["chain_valid_vs_sealed_current_head"] is False
    assert all(v == drill.EQUAL for k, v in planes.items() if k != "workflow_history")


def test_restore_to_frozen_snapshot_reconstructs_that_point_in_time(drill_env):
    live = drill_env["live"]
    restored = drill.fresh_restore(drill_env["frozen_archive"], drill_env["work"], "t-frozen")

    planes = drill.compare_planes(
        drill_env["frozen_reference"],
        drill.logical_fingerprint(restored, drill_env["frozen_live"]),
    )
    assert planes == {plane: drill.EQUAL for plane in drill.PLANES}

    state = drill.SqliteEngineeringStateStore(restored / drill.ORION_DB)
    assert state.head(drill.PROJECT).snapshot_id == live.frozen_snapshot_id
    with pytest.raises(KeyError):
        state.get_snapshot(live.snapshot_ids[-1])

    atlas = drill.SqliteAtlasPlaneStore(restored / drill.ATLAS_DB)
    assert atlas.batch_commit("atlas-batch-1") is not None
    assert atlas.batch_commit("atlas-batch-2") is None

    engine = drill.SqliteReferenceWorkflowEngine(restored / drill.ORION_DB)
    # tail truncation relative to a later sealed head must be detectable, and the
    # internally-valid shorter history must not be mistaken for the later one
    assert engine.verify_history("wf-1", expected_head_hash=live.frozen_wf1_head) is True
    assert engine.verify_history("wf-1", expected_head_hash=live.current_wf1_head) is False
    with pytest.raises(KeyError):
        engine.workflow("wf-2")


def test_restore_destination_must_be_empty(drill_env):
    destination = drill_env["work"] / "not-empty"
    destination.mkdir(exist_ok=True)
    (destination / "squatter").write_text("pre-existing")
    with pytest.raises(ValueError):
        drill.restore_reference_backup(drill_env["archive"], destination)
