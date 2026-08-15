"""E18: hostile assurance campaign on the integrated engineering layer.

Cases are FROZEN in this file before execution — the list below is the
registration. Each attacks a specific invariant across the layers landed this
session, and every outcome, negative or positive, is preserved in the receipt.

    H01 stale snapshot mutation             -> SNAPSHOT_STALE, no state change
    H02 duplicate worker delivery           -> second claim HELD/RECLAIMED, one execution
    H03 replayed decision (same key)        -> same response, head unmoved
    H04 replayed decision (tampered payload)-> IDEMPOTENCY_CONFLICT
    H05 corrupted backup blob               -> CORRUPTED_BLOB, not EXACT
    H06 delayed worker past lease           -> stale token refused, cannot complete
    H07 clock skew (heartbeat in the past)  -> lease treated as expired, reclaimable
    H08 payload not binding effect          -> PAYLOAD_HASH_MISMATCH, no state change
    H09 authority projection via API        -> AUTHORITY_PROJECTION_IMMUTABLE
    H10 atlas plane half-write              -> rolled back, counts unchanged
    H11 mutable image tag                   -> MUTABLE_TAG_WITHOUT_DIGEST
    H12 secret value in provenance          -> never appears; reference only

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
    SqliteAtlasPlaneStore,
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


def api():
    idp, sec = IdentityProvider(), SecretStore()
    svc = EngineeringHttpService(idp=idp, secrets=sec)
    tok = idp.issue(Actor("w", frozenset({"p"}), frozenset(Capability)))
    hdr = {"Authorization": f"Bearer {tok}"}
    return svc, hdr, sec


def post(svc, hdr, payload, key="k", expected="snap-0", phash=None):
    body = json.dumps({"idempotency_key": key, "expected_snapshot_id": expected, "payload": payload,
                       "payload_hash": phash or content_hash(payload)}).encode()
    return svc.handle("POST", "/v1/projects/p/evidence", hdr, body)


def h01():
    svc, hdr, _ = api()
    post(svc, hdr, {"a": 1}, key="k1")
    st, body, _ = post(svc, hdr, {"b": 2}, key="k2", expected="snap-0")
    return st == 409 and body["error"] == "SNAPSHOT_STALE" and svc.projects["p"].sequence == 1, body["error"]


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
    s1, r1, _ = post(svc, hdr, {"a": 1})
    s2, r2, _ = post(svc, hdr, {"a": 1})
    return s1 == s2 == 200 and r2.get("replayed") and svc.projects["p"].sequence == 1, "replayed, seq=1"


def h04():
    svc, hdr, _ = api()
    post(svc, hdr, {"a": 1})
    st, body, _ = post(svc, hdr, {"a": 2})
    return st == 409 and body["error"] == "IDEMPOTENCY_CONFLICT", body["error"]


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
    st, body, _ = post(svc, hdr, {"a": 1}, phash="0" * 64)
    return st == 400 and body["error"] == "PAYLOAD_HASH_MISMATCH" and svc.projects["p"].sequence == 0, body["error"]


def h09():
    svc, hdr, _ = api()
    st, body, _ = post(svc, hdr, {"authority_projection_revision": "auth-99"})
    return (st == 403 and body["error"] == "AUTHORITY_PROJECTION_IMMUTABLE"
            and svc.projects["p"].authority_projection_revision == "auth-0"), body["error"]


def h10():
    with tempfile.TemporaryDirectory() as td:
        st = SqliteAtlasPlaneStore(Path(td) / "a.db")
        b1 = AtlasPlaneBatch(1, ATLAS_GENESIS_REVISION, "b1", charts=(AtlasChartRecord("c1", "s"), AtlasChartRecord("c2", "s")),
                             transitions=(AtlasTransitionRecord("t1", "c1", "c2"),),
                             obstructions=(AtlasObstructionRecord("o1", "t1"),))
        c1 = st.commit_batch(b1, committed_snapshot_id="s1", expected_atlas_revision="")
        before = st.plane_counts()
        b2 = AtlasPlaneBatch(2, c1.atlas_revision, "b2", charts=(AtlasChartRecord("c9", "s"), AtlasChartRecord("c8", "s")),
                             transitions=(AtlasTransitionRecord("t9", "c9", "c8"),),
                             obstructions=(AtlasObstructionRecord("o1", "t9"),))  # collides
        try:
            st.commit_batch(b2, committed_snapshot_id="s2", expected_atlas_revision="")
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
    post(svc, hdr, {"secret_names": ["api_key"]})
    st, prov, _ = svc.handle("GET", "/v1/projects/p/provenance", hdr, b"")
    text = json.dumps(prov)
    return "s3cr3t-value" not in text and "secret://api_key@v1" in text, "reference only"


print("=" * 78)
print("HOSTILE ASSURANCE V3 — integrated engineering layer")
print("=" * 78)
case("H01", "stale snapshot mutation", h01)
case("H02", "duplicate worker delivery", h02)
case("H03", "replayed decision, same key", h03)
case("H04", "replayed decision, tampered payload", h04)
case("H05", "corrupted backup blob", h05)
case("H06", "delayed worker past lease", h06)
case("H07", "clock skew: heartbeat in the past", h07)
case("H08", "payload hash not binding effect", h08)
case("H09", "authority projection via API", h09)
case("H10", "atlas plane half-write", h10)
case("H11", "mutable image tag", h11)
case("H12", "secret value in provenance", h12)

held = sum(1 for r in RESULTS if r["held"])
print("=" * 78)
print(f"held {held}/{len(RESULTS)}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "schema_version": "orion-hostile-assurance-v3",
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
