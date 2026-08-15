"""E18: hostile assurance campaign on the integrated engineering layer.

Cases are FROZEN in this file before execution — the list below is the
registration. Each attacks a specific invariant across the layers landed this
session, and every outcome, negative or positive, is preserved in the receipt.

Case ids are A01..A12. They were H01..H12 in the first execution, which
collided with the HOSTILE_TEST_MATRIX.md namespace while attacking DIFFERENT
things (campaign "H01 stale snapshot mutation" vs matrix "H01 kill during
canonical blob write"). CONFORMANCE_AUDIT_V1.json recorded that collision; the
ids were renamed so a reader cross-referencing "A01 held" cannot conclude that
matrix row H01 held. This campaign is NOT the matrix. The matrix is executed,
row by row, in run_hostile_matrix.py -> HOSTILE_MATRIX_EXECUTION_V1.json.

    A01 stale snapshot mutation             -> SNAPSHOT_STALE, no state change
    A02 duplicate worker delivery           -> second claim HELD/RECLAIMED, one execution
    A03 replayed decision (same key)        -> same response, head unmoved
    A04 replayed decision (tampered payload)-> IDEMPOTENCY_CONFLICT
    A05 corrupted backup blob               -> CORRUPTED_BLOB, not EXACT
    A06 delayed worker past lease           -> stale token refused, cannot complete
    A07 clock skew (heartbeat in the past)  -> lease treated as expired, reclaimable
    A08 payload not binding effect          -> PAYLOAD_HASH_MISMATCH, no state change
    A09 authority projection via API        -> AUTHORITY_PROJECTION_IMMUTABLE
    A10 atlas plane half-write              -> rolled back, counts unchanged
    A11 mutable image tag                   -> MUTABLE_TAG_WITHOUT_DIGEST
    A12 secret value in provenance          -> never appears; reference only

What this campaign is NOT: an independently executed pass on an exact
production release. That is a separate obligation and it is recorded as open.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

from rakl.engineering_atlas_store import (  # noqa: E402
    ATLAS_GENESIS_REVISION, AtlasChartRecord, AtlasObstructionRecord, AtlasPlaneBatch, AtlasTransitionRecord,
    SqliteAtlasPlaneStore, atlas_revision_for,
)
from rakl.engineering_http import (  # noqa: E402
    Actor, Capability, EngineeringHttpService, IdentityProvider, SecretStore, content_hash,
)
from rakl.engineering_ops import BuildProvenance, ProvenanceVerdict, RestoreVerdict, take_backup, verify_restore  # noqa: E402
from rakl.engineering_workflow import ActivitySpec  # noqa: E402
from rakl.engineering_workflow_workers import ClaimVerdict, SqliteWorkerWorkflowEngine  # noqa: E402

OUT = Path("research/orion_engineering_closure_v1/HOSTILE_ASSURANCE_V3.json")
RESULTS: list[dict] = []


def case(cid: str, name: str, fn):
    try:
        held, detail = fn()
        RESULTS.append({"case": cid, "name": name, "held": bool(held), "detail": str(detail)})
        print(f"  {'HELD ' if held else 'BROKE'} {cid} {name:<42} {detail}")
    except Exception as exc:  # noqa: BLE001
        RESULTS.append({"case": cid, "name": name, "held": False, "detail": f"EXCEPTION {type(exc).__name__}: {exc}"})
        print(f"  BROKE {cid} {name:<42} EXCEPTION {exc}")


# The service was rewritten (operate lane) to run over the REAL stores: `POST /v1/projects` is
# genesis, `expected_snapshot_id` must name a real snapshot, and a stale expected snapshot is a
# RETRY_REQUIRED *receipt* (HTTP 409), not a SNAPSHOT_STALE error. The attacks below are the same
# attacks as the first execution; only the helpers speak the new contract.


def api():
    idp, sec = IdentityProvider(), SecretStore()
    svc = EngineeringHttpService(idp=idp, secrets=sec)
    tok = idp.issue(Actor("w", frozenset({"p"}), frozenset(Capability)))
    hdr = {"Authorization": f"Bearer {tok}"}
    st, body, _ = svc.handle("POST", "/v1/projects", hdr, json.dumps({"project_id": "p"}).encode())
    assert int(st) in (200, 201), body
    return svc, hdr, sec


def head_id(svc, hdr):
    return svc.handle("GET", "/v1/projects/p/head", hdr, b"")[1]["snapshot_id"]


def head_seq(svc, hdr):
    return svc.handle("GET", "/v1/projects/p/head", hdr, b"")[1]["sequence"]


def post(svc, hdr, payload, key="k", expected=None, phash=None):
    if expected is None:
        expected = head_id(svc, hdr)
    body = json.dumps({"idempotency_key": key, "expected_snapshot_id": expected, "payload": payload,
                       "payload_hash": phash or content_hash(payload)}).encode()
    return svc.handle("POST", "/v1/projects/p/evidence", hdr, body)


def h01():
    svc, hdr, _ = api()
    genesis = head_id(svc, hdr)
    post(svc, hdr, {"content_utf8": "a"}, key="k1", expected=genesis)
    st, body, _ = post(svc, hdr, {"content_utf8": "b"}, key="k2", expected=genesis)   # stale: head moved
    return (int(st) == 409 and body.get("status") == "RETRY_REQUIRED" and body.get("after_snapshot_id") is None
            and head_seq(svc, hdr) == 1), f"{body.get('status')} (receipt), head seq {head_seq(svc, hdr)}"


def h02():
    with tempfile.TemporaryDirectory() as td:
        eng = SqliteWorkerWorkflowEngine(Path(td) / "w.db")
        eng.schedule("w", ActivitySpec("a", "i", "d", True, False), idempotency_key="k")
        a = eng.claim("w", "a", worker_id="A", now=0, ttl=30)
        b = eng.claim("w", "a", worker_id="B", now=1, ttl=30)
        return (a.verdict is ClaimVerdict.ACQUIRED and b.verdict is ClaimVerdict.HELD_BY_LIVE_WORKER
                and eng.activity("w", "a").attempt_count == 1), f"{a.verdict.value}/{b.verdict.value}"


def h03():
    svc, hdr, _ = api()
    genesis = head_id(svc, hdr)
    s1, r1, _ = post(svc, hdr, {"content_utf8": "a"}, expected=genesis)
    s2, r2, _ = post(svc, hdr, {"content_utf8": "a"}, expected=genesis)   # exact replay, same key+payload
    return (int(s1) == int(s2) == 200 and r2.get("replayed") is True and r2.get("transition_id") == r1.get("transition_id")
            and head_seq(svc, hdr) == 1), f"replayed, same transition_id, seq={head_seq(svc, hdr)}"


def h04():
    svc, hdr, _ = api()
    genesis = head_id(svc, hdr)
    post(svc, hdr, {"content_utf8": "a"}, expected=genesis)
    st, body, _ = post(svc, hdr, {"content_utf8": "b"}, expected=genesis)   # same key, tampered payload
    return int(st) == 409 and body.get("error") == "IDEMPOTENCY_CONFLICT", body.get("error")


def h05():
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "s"; src.mkdir(); (src / "x").write_text("ok")
        m = take_backup(src, backup_id="b", created_at="t")
        dst = Path(td) / "d"; dst.mkdir(); (dst / "x").write_text("corrupt")
        v, which = verify_restore(dst, m)
        return v is RestoreVerdict.CORRUPTED_BLOB and which == ("x",), v.value


def h06():
    with tempfile.TemporaryDirectory() as td:
        eng = SqliteWorkerWorkflowEngine(Path(td) / "w.db")
        eng.schedule("w", ActivitySpec("a", "i", "d", True, False), idempotency_key="k")
        a = eng.claim("w", "a", worker_id="A", now=0, ttl=10)
        b = eng.claim("w", "a", worker_id="B", now=20, ttl=10)
        late = eng.complete(a.lease, result_digest="stale")
        return b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER and late is False, "stale token refused"


def h07():
    with tempfile.TemporaryDirectory() as td:
        eng = SqliteWorkerWorkflowEngine(Path(td) / "w.db")
        eng.schedule("w", ActivitySpec("a", "i", "d", True, False), idempotency_key="k")
        a = eng.claim("w", "a", worker_id="A", now=100, ttl=10)
        # skewed worker heartbeats "in the past" -- an earlier now than acquisition
        eng.heartbeat(a.lease, now=50)
        b = eng.claim("w", "a", worker_id="B", now=111, ttl=10)
        return b.verdict is ClaimVerdict.RECLAIMED_FROM_DEAD_WORKER, "skewed heartbeat did not extend the lease"


def h08():
    svc, hdr, _ = api()
    st, body, _ = post(svc, hdr, {"content_utf8": "a"}, phash="0" * 64)
    return int(st) == 400 and body.get("error") == "PAYLOAD_HASH_MISMATCH" and head_seq(svc, hdr) == 0, body.get("error")


def h09():
    svc, hdr, _ = api()
    before = svc.handle("GET", "/v1/projects/p/head", hdr, b"")[1]["authority_projection_revision"]
    st, body, _ = post(svc, hdr, {"authority_projection_revision": "auth-99"})
    after = svc.handle("GET", "/v1/projects/p/head", hdr, b"")[1]["authority_projection_revision"]
    return (int(st) == 403 and body.get("error") == "AUTHORITY_PROJECTION_IMMUTABLE" and before == after), body.get("error")


def h10():
    with tempfile.TemporaryDirectory() as td:
        st = SqliteAtlasPlaneStore(Path(td) / "a.db")
        # the store now enforces sequence + base-revision CAS (X11/X12); a batch must name the plane's real position
        b1 = AtlasPlaneBatch(1, ATLAS_GENESIS_REVISION, "b1",
                             charts=(AtlasChartRecord("c1", "s"), AtlasChartRecord("c2", "s")),
                             transitions=(AtlasTransitionRecord("t1", "c1", "c2"),),
                             obstructions=(AtlasObstructionRecord("o1", "t1"),))
        r1 = st.commit_batch(b1, committed_snapshot_id="s1", expected_atlas_revision=atlas_revision_for(1, b1))
        before = st.plane_counts()
        b2 = AtlasPlaneBatch(2, r1.atlas_revision, "b2",
                             charts=(AtlasChartRecord("c9", "s"), AtlasChartRecord("c8", "s")),
                             transitions=(AtlasTransitionRecord("t9", "c9", "c8"),),
                             obstructions=(AtlasObstructionRecord("o1", "t9"),))  # o1 collides with the committed plane
        try:
            st.commit_batch(b2, committed_snapshot_id="s2", expected_atlas_revision=atlas_revision_for(2, b2))
            return False, "collision was accepted"
        except Exception:
            return st.plane_counts() == before, "rolled back, counts unchanged"


def h11():
    art = b"bytes"
    p = BuildProvenance("c", "l", "b", "img:latest", hashlib.sha256(art).hexdigest(), "cf", "rm")
    return p.verify(art) is ProvenanceVerdict.MUTABLE_TAG_WITHOUT_DIGEST, "MUTABLE_TAG_WITHOUT_DIGEST"


def h12():
    svc, hdr, sec = api()
    sec.put("api_key", "s3cr3t-value")
    post(svc, hdr, {"content_utf8": "x", "secret_names": ["api_key"]})
    st, prov, _ = svc.handle("GET", "/v1/projects/p/provenance", hdr, b"")
    text = json.dumps(prov)
    return "s3cr3t-value" not in text and "secret://api_key@v1" in text, "reference only"


print("=" * 78)
print("HOSTILE ASSURANCE V3 — integrated engineering layer")
print("=" * 78)
case("A01", "stale snapshot mutation", h01)
case("A02", "duplicate worker delivery", h02)
case("A03", "replayed decision, same key", h03)
case("A04", "replayed decision, tampered payload", h04)
case("A05", "corrupted backup blob", h05)
case("A06", "delayed worker past lease", h06)
case("A07", "clock skew: heartbeat in the past", h07)
case("A08", "payload hash not binding effect", h08)
case("A09", "authority projection via API", h09)
case("A10", "atlas plane half-write", h10)
case("A11", "mutable image tag", h11)
case("A12", "secret value in provenance", h12)

held = sum(1 for r in RESULTS if r["held"])
print("=" * 78)
print(f"held {held}/{len(RESULTS)}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "schema_version": "orion-hostile-assurance-v3",
    "case_id_namespace": "A01..A12 (renamed from H01..H12; NOT HOSTILE_TEST_MATRIX rows -- see run_hostile_matrix.py)",
    "status": "FROZEN_CASES_EXECUTED__ALL_OUTCOMES_PRESERVED",
    "grants_scientific_authority": False,
    "cases_frozen_before_execution": True,
    "held": held, "total": len(RESULTS), "results": RESULTS,
    "not_claimed": [
        "an independently executed pass on an exact production release",
        "distributed exactly-once across external effects",
    ],
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {OUT}")
