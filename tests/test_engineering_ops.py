"""E11 / E15 / E17 / E19 / E20 — each tested against its falsifier."""

from __future__ import annotations

import pytest

from rakl.engineering_ops import (
    BackupManifest, BudgetVerdict, BuildProvenance, OperatorDoctor, ProbeResult, ProbeStatus,
    ProvenanceVerdict, ResourceBudget, RestoreVerdict, measure_slo, project_observatory,
    take_backup, verify_restore,
)


# --- E11: observatory never recomputes ----------------------------------


def test_observatory_carries_stored_values_and_computes_nothing() -> None:
    view = project_observatory({
        "project_id": "p", "project_snapshot_id": "s1", "status_id": "st1",
        "saturation_axes": {"knowledge": "SATURATED", "operators": "OPEN"},
        "freshness": "FRESH", "hard_gates": {"g1": "PASS"}, "controller_decision": "SOLVE_CURRENT",
        "provenance_ids": {"freshness": "status:st1", "hard_gates.g1": "receipt:r9"},
    })
    assert view.saturation_axes["knowledge"] == "SATURATED"
    assert view.freshness == "FRESH"
    # the negative property: no computing method exists
    assert not any(n.startswith(("compute", "score", "recompute")) for n in dir(view))


def test_observatory_drills_every_displayed_field_to_a_canonical_id() -> None:
    view = project_observatory({"project_id": "p", "provenance_ids": {"freshness": "status:st1"}})
    text = view.render()
    assert "freshness" in text and "status:st1" in text
    assert "drill-down" in text


def test_observatory_renders_absent_fields_as_absent_not_derived() -> None:
    view = project_observatory({"project_id": "p"})
    assert view.freshness == "UNKNOWN"
    assert view.saturation_axes == {}


# --- E15: restore must be exact ---------------------------------------


def test_backup_and_restore_round_trip_is_exact(tmp_path) -> None:
    src = tmp_path / "src"; (src / "a").mkdir(parents=True)
    (src / "a" / "x.json").write_text('{"k":1}'); (src / "b.bin").write_bytes(b"\x00\x01")
    m = take_backup(src, backup_id="b1", created_at="2026-08-15")
    dst = tmp_path / "empty"; dst.mkdir()
    for rel in m.entries:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        (dst / rel).write_bytes((src / rel).read_bytes())
    assert verify_restore(dst, m) == (RestoreVerdict.EXACT, ())


def test_corrupted_blob_and_missing_blob_are_detected(tmp_path) -> None:
    src = tmp_path / "src"; src.mkdir()
    (src / "x").write_text("good"); (src / "y").write_text("also")
    m = take_backup(src, backup_id="b1", created_at="t")
    dst = tmp_path / "dst"; dst.mkdir()
    (dst / "x").write_text("BAD"); (dst / "y").write_text("also")
    assert verify_restore(dst, m) == (RestoreVerdict.CORRUPTED_BLOB, ("x",))
    (dst / "y").unlink()
    assert verify_restore(dst, m)[0] is RestoreVerdict.MISSING_BLOB


def test_tampered_manifest_is_refused() -> None:
    m = BackupManifest("b1", "t", {"x": "aa"})
    with pytest.raises(ValueError, match="does not bind"):
        BackupManifest("b1", "t", {"x": "bb"}, manifest_digest=m.manifest_digest)


# --- E17: exhaustion is a typed refusal before any mutation ------------


def test_budget_refuses_typed_before_state_changes() -> None:
    b = ResourceBudget(max_inflight=2, max_queue=1, degrade_at_inflight=2)
    a1 = b.admit(); assert a1.verdict is BudgetVerdict.ADMITTED
    a2 = b.admit(); assert a2.verdict is BudgetVerdict.DEGRADED     # hit degrade threshold
    a3 = b.admit(); assert a3.verdict is BudgetVerdict.DEGRADED     # queued (backpressure)
    a4 = b.admit(); assert a4.verdict is BudgetVerdict.REFUSED_OVER_BUDGET
    assert b.refused == 1
    b.release(a1); b.release(a2); b.release(a3)
    assert b.admit().verdict in (BudgetVerdict.ADMITTED, BudgetVerdict.DEGRADED)


def test_budget_release_frees_exactly_the_slot_taken_and_never_ratchets() -> None:
    """Regression: an ADMITTED holder's release used to consume a QUEUED slot.

    4 admits + 1 queued, then an inflight holder releases: inflight must drop
    (and the queued caller is promoted into the freed slot), not stay pinned at
    the ceiling. Then cycle admit/release many times: inflight must return to
    zero, proving nothing ratchets.
    """

    b = ResourceBudget(max_inflight=4, max_queue=4, degrade_at_inflight=99)
    held = [b.admit() for _ in range(4)]
    queued = b.admit()
    assert (b.inflight, b.queued) == (4, 1)
    b.release(held[0])                     # one inflight frees; queued promotes
    assert (b.inflight, b.queued) == (4, 0)
    for a in held[1:]:
        b.release(a)
    b.release(queued)                      # the promoted caller finishes
    assert (b.inflight, b.queued) == (0, 0)
    for _ in range(6):                     # nothing ratchets across cycles
        a = b.admit(); assert a.verdict is BudgetVerdict.ADMITTED
        b.release(a)
    assert (b.inflight, b.queued) == (0, 0)


def test_slo_envelope_measures_and_judges() -> None:
    env = measure_slo("noop", lambda: None, samples=50, budget_p95_ms=50.0)
    assert env.samples == 50 and env.p50_ms <= env.p95_ms
    assert env.within is True
    slow = measure_slo("slow", lambda: sum(range(2000)), samples=20, budget_p95_ms=0.0)
    assert slow.within is False


# --- E19: strings are not identity ---------------------------------------


def _prov(**over):
    art = b"artifact-bytes"
    import hashlib
    d = dict(source_commit="abc", lock_digest="l", build_procedure_digest="b",
             artifact_ref="registry/orion@sha256:" + hashlib.sha256(art).hexdigest(),
             artifact_digest=hashlib.sha256(art).hexdigest(), config_digest="c", release_manifest_digest="r")
    d.update(over)
    return BuildProvenance(**d), art


def test_provenance_verifies_the_actual_bytes() -> None:
    p, art = _prov()
    assert p.verify(art) is ProvenanceVerdict.VERIFIED
    assert p.verify(b"different") is ProvenanceVerdict.ARTIFACT_MISMATCH


def test_mutable_tag_without_digest_is_rejected() -> None:
    p, art = _prov(artifact_ref="registry/orion:latest")
    assert p.verify(art) is ProvenanceVerdict.MUTABLE_TAG_WITHOUT_DIGEST


def test_missing_provenance_field_is_rejected() -> None:
    p, art = _prov(lock_digest="")
    assert p.verify(art) is ProvenanceVerdict.MISSING_FIELD


# --- E20: a probe that cannot run is CANNOT_CHECK, never OK -------------


def test_doctor_reports_each_subsystem_typed_and_never_swallows() -> None:
    d = OperatorDoctor()
    d.register("db", lambda: ProbeResult("db", ProbeStatus.OK, "reachable"))
    d.register("backups", lambda: ProbeResult("backups", ProbeStatus.DEGRADED, "last 26h ago"))

    def broken() -> ProbeResult:
        raise RuntimeError("index socket closed")

    d.register("index", broken)
    results = d.run()
    by = {r.subsystem: r for r in results}
    assert by["db"].status is ProbeStatus.OK
    assert by["backups"].status is ProbeStatus.DEGRADED
    assert by["index"].status is ProbeStatus.CANNOT_CHECK
    assert "index socket closed" in by["index"].detail
    text = OperatorDoctor.render(results)
    assert "overall=CANNOT_CHECK" in text
