"""Conformance audit: what the ORION packet SPECIFIED vs what the code CONTAINS.

Run from the repository root:

    PYTHONPATH=src python research/orion_engineering_closure_v1/run_conformance_audit.py

Every item below is a thing one of these documents names by name:

    IMPLEMENTATION_LADDER.md   waves E0-E8, the protocols and terminals
    ARCHITECTURE.md            planes, ProjectSnapshot, EpistemicStatus,
                               StateTransitionReceipt, BlobStore, metadata families
    API_AND_OBSERVATORY.md     the minimal API, the mutation contract, the 8 views
    HOSTILE_TEST_MATRIX.md     H01-H30
    GAP_LEDGER.json            fibres E1-E20

Resolution is by import/attribute/field/enum/table/behaviour -- never by
grepping a string out of the document that specified it.

The audit reports ONE axis: named-surface conformance. A fibre can defeat its
falsifier while its ladder-named abstraction is absent, and it can carry every
named symbol while its falsifier stands. Those are separate questions and this
file answers only the first one. The second is annotated per fibre from the
CLOSURE_ASSESSMENT_V3 claim, and marked CANNOT_CHECK where no mechanical test
was run here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from rakl.engineering_conformance import (  # noqa: E402
    ABSENT, CANNOT_CHECK, Finding, PARTIAL, PRESENT,
    check_attr, check_behavioural, check_enum_members, check_fields,
    check_methods, check_module, check_sqlite_tables, summarize,
)

OUT = Path("research/orion_engineering_closure_v1/CONFORMANCE_AUDIT_V1.json")

LADDER = "IMPLEMENTATION_LADDER.md"
ARCH = "ARCHITECTURE.md"
API = "API_AND_OBSERVATORY.md"
MATRIX = "HOSTILE_TEST_MATRIX.md"

findings: list[Finding] = []


def add(f: Finding) -> None:
    findings.append(f)


# ---------------------------------------------------------------------------
# ARCHITECTURE.md 2 -- ProjectSnapshot binds these heads
# ---------------------------------------------------------------------------

add(check_module("ARCH-MOD-state", ARCH, "rakl.engineering_state"))
add(check_fields(
    "ARCH-2-ProjectSnapshot", ARCH, "rakl.engineering_state", "ProjectSnapshot",
    ["evidence_cutoff", "semantic_state_revision", "metric_ledger_head", "episode_store_head",
     "saturation_basis_ids", "authority_projection_revision", "controller_epoch_id"]))

# ARCHITECTURE.md 3 -- EpistemicStatus required coordinates
add(check_fields(
    "ARCH-3-EpistemicStatus", ARCH, "rakl.engineering_state", "EpistemicStatus",
    ["project_snapshot_id", "target_id", "fiber_id", "axis_statuses", "required_routes",
     "covered_routes", "missing_routes", "active_residual_ids", "freshness_stale",
     "required_authority", "available_support_paths", "blocking_cut_ids", "hard_gate_ids",
     "next_action", "reasons", "metric_receipt_ids", "basis_fingerprints"]))
add(check_fields(
    "ARCH-3-EpistemicAxisStatus", ARCH, "rakl.engineering_state", "EpistemicAxisStatus",
    ["axis", "bounded_flat", "recent_retained_novelty", "independent_flat_routes"]))

# ARCHITECTURE.md 4 -- StateTransitionReceipt required content + terminals
add(check_fields(
    "ARCH-4-StateTransitionReceipt", ARCH, "rakl.engineering_state", "StateTransitionReceipt",
    ["before_snapshot_id", "after_snapshot_id", "action", "idempotency_key", "process_identity",
     "read_set", "write_set", "produced_artifact_ids", "metric_receipt_ids", "residual_ids",
     "status", "reasons"]))
add(check_enum_members(
    "ARCH-4-TransitionStatus", ARCH, "rakl.engineering_state", "TransitionStatus",
    ["COMMITTED", "ABORTED", "RETRY_REQUIRED", "RECOVERY_REQUIRED", "CANNOT_CHECK"]))

# ARCHITECTURE.md 6 -- BlobStore identity contract
add(check_methods(
    "ARCH-6-BlobStore", ARCH, "rakl.engineering_store", "BlobStore",
    ["put_if_absent", "get_verified", "exists_verified", "stat"]))
add(check_methods(
    "ARCH-6-BlobStore-local", ARCH, "rakl.engineering_blob", "LocalFilesystemBlobStore",
    ["put_if_absent", "get_verified", "exists_verified", "stat"]))

# ARCHITECTURE.md 7 -- external activity requirements
add(check_fields(
    "ARCH-7-ActivitySpec", ARCH, "rakl.engineering_workflow", "ActivitySpec",
    ["activity_id", "invocation_id", "input_digest", "retry_safe", "max_attempts"]))
add(check_fields(
    "ARCH-7-WorkerActivity", ARCH, "rakl.engineering_workflow_workers", "WorkerActivityRecord",
    ["attempt_count", "lease", "idempotency_key", "effect_started"]))
add(check_fields(
    "ARCH-7-Lease", ARCH, "rakl.engineering_workflow_workers", "Lease",
    ["heartbeat_at", "ttl", "lease_token"]))

# ARCHITECTURE.md 9 / API 'correlation context' -- the propagated context
add(check_fields(
    "ARCH-9-CorrelationContext", ARCH, "rakl.engineering_telemetry", "OperationalCorrelationContext",
    ["project_id", "snapshot_id", "workflow_id", "activity_id", "invocation_id",
     "research_round_id", "episode_id", "target_id", "fiber_id", "evaluation_epoch_id",
     "controller_decision_id"]))

# ---------------------------------------------------------------------------
# ARCHITECTURE.md 5 -- canonical metadata families, resolved from sqlite_master
# ---------------------------------------------------------------------------

FAMILY_TABLES = [
    ("projects/snapshots", "rakl.engineering_store", "SqliteEngineeringStateStore",
     ["project_heads", "snapshots"]),
    ("state_transition_receipts", "rakl.engineering_store", "SqliteEngineeringStateStore",
     ["transitions"]),
    ("evidence_records", "rakl.engineering_evidence_store", "SqliteEvidenceMetadataStore",
     ["engineering_evidence_records"]),
    ("fibres/atoms/atom_versions", "rakl.engineering_semantic_store", "SqliteSemanticStateStore",
     ["semantic_fibers", "semantic_atoms", "semantic_atom_versions"]),
    ("relations/relation_witnesses", "rakl.engineering_semantic_store", "SqliteSemanticStateStore",
     ["semantic_witnesses", "semantic_witness_versions"]),
    ("atlas_charts/transitions/obstructions", "rakl.engineering_atlas_store", "SqliteAtlasPlaneStore",
     ["atlas_charts", "atlas_transitions", "atlas_obstructions"]),
    ("executions/execution_events", "rakl.engineering_workflow", "SqliteReferenceWorkflowEngine",
     ["workflows", "workflow_activities", "workflow_events"]),
]
for name, mod, cls, tables in FAMILY_TABLES:
    add(check_sqlite_tables(f"ARCH-5-{name}", ARCH, mod, cls, tables))

# The families that ARCHITECTURE 5 names but that no store creates a table for.
# Probed against every engineering store, so "absent" means absent everywhere,
# not merely absent from the store I guessed.
_ALL_STORES = [
    ("rakl.engineering_store", "SqliteEngineeringStateStore"),
    ("rakl.engineering_semantic_store", "SqliteSemanticStateStore"),
    ("rakl.engineering_evidence_store", "SqliteEvidenceMetadataStore"),
    ("rakl.engineering_atlas_store", "SqliteAtlasPlaneStore"),
    ("rakl.engineering_control_store", "SqliteControlProjectionStore"),
    ("rakl.engineering_workflow", "SqliteReferenceWorkflowEngine"),
    ("rakl.engineering_workflow_workers", "SqliteWorkerWorkflowEngine"),
    ("rakl.engineering_atomic", "SqliteAtomicEngineeringCoordinator"),
]


def _all_tables() -> set[str]:
    import sqlite3
    import tempfile
    from rakl.engineering_conformance import _resolve_attr  # noqa: PLC0415

    seen: set[str] = set()
    with tempfile.TemporaryDirectory() as td:
        for i, (mod, cls_name) in enumerate(_ALL_STORES):
            cls, note = _resolve_attr(mod, cls_name)
            if cls is None:
                continue
            path = Path(td) / f"{i}.db"
            try:
                cls(path)
                con = sqlite3.connect(path)
                seen |= {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                con.close()
            except Exception:  # noqa: BLE001,S110 -- store-specific, recorded as unseen
                continue
    return seen


_TABLES = _all_tables()

UNBACKED_FAMILIES = [
    ("blob_bindings", ["blob_bindings"]),
    ("identity_assertions/lineage_edges", ["identity_assertions", "lineage_edges"]),
    ("residuals/residual_events", ["residuals", "residual_events"]),
    ("research_rounds/novelty_events", ["research_rounds", "novelty_events"]),
    ("saturation_bases/saturation_certificates", ["saturation_bases", "saturation_certificates"]),
    ("metric_definitions/metric_receipts", ["metric_definitions", "metric_receipts"]),
    ("hard_gate_observations/controller_decisions", ["hard_gate_observations", "controller_decisions"]),
    ("episodes/lessons/tools", ["episodes", "lessons", "tools"]),
    ("evolution_variants/promotion_events", ["evolution_variants", "promotion_events"]),
]
for name, wanted in UNBACKED_FAMILIES:
    got = [t for t in wanted if t in _TABLES]
    if len(got) == len(wanted):
        verdict, detail = PRESENT, f"tables: {','.join(got)}"
    elif got:
        verdict, detail = PARTIAL, f"present: {','.join(got)}; missing: {','.join(t for t in wanted if t not in got)}"
    else:
        verdict, detail = ABSENT, "no engineering store creates a table of this name"
    add(Finding(f"ARCH-5-{name}", ARCH, "table", f"metadata family {name}", verdict,
                "all 8 engineering sqlite stores probed", detail))

# The generic control projection is what stands in for four of those families.
add(check_enum_members(
    "ARCH-5-control-projection-kinds", ARCH, "rakl.engineering_control_store", "ControlArtifactKind",
    ["METRIC_RECEIPT", "SATURATION_CERTIFICATE", "HARD_GATE", "CONTROLLER_DECISION",
     "RESIDUAL_EVENT", "AUTHORITY_PROJECTION"]))

# ---------------------------------------------------------------------------
# IMPLEMENTATION_LADDER.md wave E2 -- the five named repository protocols
# ---------------------------------------------------------------------------

def find_symbol(item_id: str, source: str, symbol: str, candidates: list[str], note: str) -> Finding:
    """Resolve a named symbol against every plausible home before declaring it absent.

    A doc names a thing; the code may have put it elsewhere. Absence is only
    claimed after every candidate module resolved and none carried the symbol.
    An import that could not be performed at all yields CANNOT_CHECK.
    """
    hits, unchecked = [], []
    for mod in candidates:
        f = check_attr(item_id, source, mod, symbol)
        if f.verdict == PRESENT:
            hits.append(f"{mod}.{symbol}")
        elif f.verdict == CANNOT_CHECK:
            unchecked.append(f"{mod}: {f.detail}")
    if hits:
        return Finding(item_id, source, "attr", symbol, PRESENT, ";".join(hits), note)
    if unchecked and len(unchecked) == len(candidates):
        return Finding(item_id, source, "attr", symbol, CANNOT_CHECK,
                       f"searched {len(candidates)} modules", "; ".join(unchecked))
    return Finding(item_id, source, "attr", symbol, ABSENT,
                   f"searched: {', '.join(candidates)}",
                   f"{note}; no module carries this symbol"
                   + (f"; uncheckable: {'; '.join(unchecked)}" if unchecked else ""))


ENG_MODULES = [
    "rakl.engineering_contracts", "rakl.engineering_store", "rakl.engineering_state",
    "rakl.engineering_semantic_store", "rakl.engineering_control_store",
    "rakl.engineering_atomic", "rakl.engineering_service", "rakl.engineering_api",
    "rakl.engineering_workflow", "rakl.engineering_workflow_workers",
    "rakl.engineering_integration", "rakl.engineering_evidence_store", "rakl.engineering_blob",
]

for proto in ["BlobStore", "SnapshotRepository", "SemanticRepository",
              "MetrologyRepository", "TransitionRepository"]:
    add(find_symbol(f"LADDER-E2-{proto}", LADDER, proto, ENG_MODULES,
                    "wave-E2 repository interface"))

# IMPLEMENTATION_LADDER.md wave E5 -- the engine abstraction
add(find_symbol("LADDER-E5-ResearchWorkflowEngine", LADDER, "ResearchWorkflowEngine",
                ENG_MODULES, "wave-E5 workflow engine abstraction"))

# IMPLEMENTATION_LADDER.md wave E8 -- the allowed terminal vocabulary
E8_TERMINALS = ["PRODUCTION_READY_SCOPED", "SINGLE_NODE_READY_ONLY",
                "DURABILITY_READY_CONTROL_INTEGRATION_OPEN", "CONTROL_READY_DISTRIBUTED_RUNTIME_OPEN",
                "SECURITY_OR_RECOVERY_BLOCKED", "PERFORMANCE_ENVELOPE_EXCEEDED",
                "MIGRATION_PARITY_FAILED", "CANNOT_CHECK_RESOURCE_BOUND"]
_e8_homes = [("rakl.engineering_contracts", "WaveE8Terminal"),
             ("rakl.engineering_closure", "EngineeringFiberLevel"),
             ("rakl.engineering_deployment", "SupportVerdict")]
_t = None
for _mod, _cls in _e8_homes:
    _cand = check_enum_members("LADDER-E8-terminals", LADDER, _mod, _cls, E8_TERMINALS)
    if _cand.verdict in (PRESENT, PARTIAL):
        _t = _cand
        break
    if _t is None or _cand.verdict == CANNOT_CHECK:
        _t = _cand
if _t.verdict == ABSENT:
    _t = Finding("LADDER-E8-terminals", LADDER, "enum_member",
                 "the 8 allowed Wave-E8 terminals " + ",".join(E8_TERMINALS), ABSENT,
                 "searched " + ", ".join(f"{m}.{c}" for m, c in _e8_homes),
                 "no enum in the codebase carries the Wave-E8 terminal vocabulary")
add(_t)

# Wave E4 named control entry points -- searched across the whole rakl package,
# because the ladder names the function, not its module.
_SAT_HOMES = ["rakl.research_machine_workflow", "rakl.observability_adapters",
              "rakl.knowledge_saturation", "rakl.saturation", "rakl.epistemic_saturation",
              "rakl.saturation_vector", "rakl.core"]
add(find_symbol("LADDER-E4-assess_knowledge_saturation", LADDER, "assess_knowledge_saturation",
                _SAT_HOMES, "wave-E4 saturation entry point"))
add(find_symbol("LADDER-E4-bounded_saturation_artifacts", LADDER, "bounded_saturation_artifacts",
                _SAT_HOMES, "wave-E4 bounded-saturation artifacts"))

# ---------------------------------------------------------------------------
# API_AND_OBSERVATORY.md -- the minimal API, probed behaviourally
# ---------------------------------------------------------------------------


def _service():
    from rakl.engineering_http import Actor, Capability, EngineeringHttpService, IdentityProvider, SecretStore
    idp, sec = IdentityProvider(), SecretStore()
    svc = EngineeringHttpService(idp=idp, secrets=sec)
    token = idp.issue(Actor("auditor", frozenset({"p1"}), frozenset(Capability)))
    return svc, {"Authorization": f"Bearer {token}"}


def _mutation_body(payload: dict, *, key: str, expected: str) -> bytes:
    from rakl.engineering_http import content_hash
    return json.dumps({"idempotency_key": key, "expected_snapshot_id": expected,
                       "payload": payload, "payload_hash": content_hash(payload)}).encode()


ROUTES = [
    ("POST", "/v1/projects", True),
    ("GET", "/v1/projects/p1/head", False),
    ("GET", "/v1/projects/p1/snapshots/snap-0", False),
    ("POST", "/v1/projects/p1/evidence", True),
    ("POST", "/v1/projects/p1/research-rounds", True),
    ("GET", "/v1/projects/p1/epistemic-status", False),
    ("POST", "/v1/projects/p1/actions:plan", True),
    ("POST", "/v1/projects/p1/actions:execute", True),
    ("GET", "/v1/projects/p1/transitions/t1", False),
    ("GET", "/v1/projects/p1/decisions/d1", False),
    ("GET", "/v1/projects/p1/runs/r1", False),
    ("GET", "/v1/projects/p1/provenance/e1", False),
]

for _i, (method, path, mutating) in enumerate(ROUTES):
    def _probe(method=method, path=path, mutating=mutating, i=_i):
        svc, hdr = _service()
        body = _mutation_body({"a": i}, key=f"k{i}", expected="snap-0") if mutating else b""
        status, resp, _h = svc.handle(method, path, hdr, body)
        code = resp.get("error") if isinstance(resp, dict) else None
        if int(status) == 404 and code == "NOT_FOUND":
            return ABSENT, "rakl.engineering_http.EngineeringHttpService.handle", \
                f"{method} {path} -> 404 NOT_FOUND"
        return PRESENT, "rakl.engineering_http.EngineeringHttpService.handle", \
            f"{method} {path} -> {int(status)} {code or 'ok'}"
    add(check_behavioural(f"API-route-{method}-{path}", API, f"{method} {path}", _probe))


def _probe_query_params():
    """The spec'd epistemic-status route carries ?snapshot=&target=&fiber=."""
    svc, hdr = _service()
    status, resp, _h = svc.handle("GET", "/v1/projects/p1/status?snapshot=snap-0&target=t&fiber=f", hdr, b"")
    code = resp.get("error") if isinstance(resp, dict) else None
    if int(status) == 404:
        return ABSENT, "rakl.engineering_http.EngineeringHttpService.handle", \
            f"query string is not stripped from the path segment -> {int(status)} {code}"
    return PRESENT, "rakl.engineering_http.EngineeringHttpService.handle", f"{int(status)} {code or 'ok'}"


add(check_behavioural("API-query-params", API, "GET .../epistemic-status?snapshot=&target=&fiber=",
                      _probe_query_params))


def _probe_receipt_on_mutation():
    """'Every mutation returns a StateTransitionReceipt, even on RETRY_REQUIRED,
    RECOVERY_REQUIRED or CANNOT_CHECK.'"""
    import dataclasses as _dc
    from rakl.engineering_state import StateTransitionReceipt
    svc, hdr = _service()
    status, resp, _h = svc.handle("POST", "/v1/projects/p1/evidence", hdr,
                                  _mutation_body({"a": 1}, key="kr", expected="snap-0"))
    if int(status) != 200:
        return CANNOT_CHECK, "rakl.engineering_http", f"mutation did not succeed: {status} {resp}"
    required = {f.name for f in _dc.fields(StateTransitionReceipt)
                if f.default is _dc.MISSING and f.default_factory is _dc.MISSING}  # type: ignore[misc]
    have = set(resp) if isinstance(resp, dict) else set()
    missing = sorted(required - have)
    if not missing:
        return PRESENT, "rakl.engineering_http", "mutation response carries receipt fields"
    return ABSENT, "rakl.engineering_http.EngineeringHttpService.handle", (
        f"committed mutation returned keys {sorted(have)}; a StateTransitionReceipt "
        f"requires {sorted(required)} -- missing {missing}")


add(check_behavioural("API-mutation-returns-receipt", API,
                      "every mutation returns a StateTransitionReceipt", _probe_receipt_on_mutation))


def _probe_error_returns_receipt():
    """The same rule on the non-committed terminals."""
    import dataclasses as _dc
    from rakl.engineering_state import StateTransitionReceipt
    svc, hdr = _service()
    svc.handle("POST", "/v1/projects/p1/evidence", hdr, _mutation_body({"a": 1}, key="k1", expected="snap-0"))
    status, resp, _h = svc.handle("POST", "/v1/projects/p1/evidence", hdr,
                                  _mutation_body({"a": 2}, key="k2", expected="snap-0"))
    if int(status) == 200:
        return CANNOT_CHECK, "rakl.engineering_http", "expected a stale-snapshot refusal, got 200"
    required = {f.name for f in _dc.fields(StateTransitionReceipt)
                if f.default is _dc.MISSING and f.default_factory is _dc.MISSING}  # type: ignore[misc]
    have = set(resp) if isinstance(resp, dict) else set()
    if required <= have:
        return PRESENT, "rakl.engineering_http", "refusal carries receipt fields"
    return ABSENT, "rakl.engineering_http.EngineeringHttpService.handle", (
        f"refusal ({resp.get('error')}) returned keys {sorted(have)}, not a StateTransitionReceipt")


add(check_behavioural("API-refusal-returns-receipt", API,
                      "RETRY_REQUIRED/RECOVERY_REQUIRED/CANNOT_CHECK also return a receipt",
                      _probe_error_returns_receipt))

# The mutation contract itself (spec allows a request-body equivalent of the headers)
add(check_enum_members(
    "API-mutation-contract", API, "rakl.engineering_http", "ApiErrorCode",
    ["MISSING_IDEMPOTENCY_KEY", "MISSING_EXPECTED_SNAPSHOT", "IDEMPOTENCY_CONFLICT", "SNAPSHOT_STALE"]))

# ---------------------------------------------------------------------------
# API_AND_OBSERVATORY.md -- the 8 Observatory views
# ---------------------------------------------------------------------------

VIEWS = [
    ("1-project-head", ["project_id", "snapshot_id", "freshness"]),
    ("2-epistemic-status", ["saturation_axes", "route_coverage", "residuals", "freshness"]),
    ("3-decision-trace", ["hard_gates", "controller_decision"]),
    ("4-solver-state", ["compiled_view_identity", "support_paths", "cuts"]),
    ("5-evidence-provenance", ["provenance_ids"]),
    ("6-execution-recovery", ["workflow_states"]),
    ("7-evolution-history", ["evolution_history"]),
    ("8-operational-health", ["operational_health"]),
]
for view, fields in VIEWS:
    add(check_fields(f"API-view-{view}", API, "rakl.engineering_ops", "ObservatoryView", fields))

# ---------------------------------------------------------------------------
# HOSTILE_TEST_MATRIX.md -- H01..H30 vs the executed campaign
# ---------------------------------------------------------------------------

MATRIX_ROWS = {
    "H01": "kill during canonical blob write",
    "H02": "blob committed, metadata transition killed before commit",
    "H03": "metadata references unavailable blob",
    "H04": "mutate stored blob bytes",
    "H05": "torn episode JSONL tail",
    "H06": "delete interior episode record",
    "H07": "concurrent identical idempotency key, identical request",
    "H08": "same idempotency key, different request",
    "H09": "two writers plan on same project snapshot",
    "H10": "stale controller decision replayed after semantic mutation",
    "H11": "saturation certificate basis fingerprint changes",
    "H12": "new native residual after bounded saturation",
    "H13": "delete full-text/vector/graph index",
    "H14": "corrupt derived index to return nonexistent atom",
    "H15": "worker finishes external effect, crashes before completion record",
    "H16": "duplicate activity delivery",
    "H17": "DB failover mid-transition",
    "H18": "object store temporary outage",
    "H19": "restore backup into empty environment",
    "H20": "point-in-time replay to older snapshot",
    "H21": "partial schema migration",
    "H22": "rollback after failed migration",
    "H23": "secret rotation during worker lifetime",
    "H24": "infrastructure admin submits unverified scientific promotion",
    "H25": "malicious fabricated hard-gate ID in status",
    "H26": "clock skew on worker",
    "H27": "execution artifact rebuilt from different source but same label",
    "H28": "audit/log exporter unavailable",
    "H29": "high transaction contention",
    "H30": "huge knowledge lattice + context request",
}

# Per-case reading of run_hostile_assurance_v3.py, by hand, line by line: which
# MATRIX row (if any) each executed case actually attacks. The campaign reuses
# the H-prefix with its OWN numbering, so this mapping is by CONTENT, never by id.
#
# value = (matrix_row, PRESENT|PARTIAL, why)
CAMPAIGN_TO_MATRIX: dict[str, tuple[str, str, str] | None] = {
    "H01 stale snapshot mutation": (
        "H09", PRESENT,
        "second writer on the same expected snapshot is refused SNAPSHOT_STALE and the head does "
        "not move; the row's allowed result names RETRY_REQUIRED, the refusal is the same terminal class"),
    "H02 duplicate worker delivery": (
        "H16", PRESENT, "two claims on one activity: one ACQUIRED, one HELD_BY_LIVE_WORKER, attempt_count==1"),
    "H03 replayed decision, same key": ("H07", PRESENT, "identical key + identical request replays, head unmoved"),
    "H04 replayed decision, tampered payload": ("H08", PRESENT, "same key, different payload -> IDEMPOTENCY_CONFLICT"),
    "H05 corrupted backup blob": (
        "H19", PARTIAL,
        "exercises only the FAILURE branch (restore into a corrupted tree -> CORRUPTED_BLOB). "
        "'frozen snapshot identities reproduce' after a restore into an EMPTY environment is not "
        "asserted by this case"),
    "H06 delayed worker past lease": (
        "H15", PARTIAL,
        "a lease expiry/reclaim with a stale completion token refused. The row's actual attack -- "
        "external effect COMPLETED, then crash before the completion record, expecting "
        "RECOVERY_REQUIRED -- is not run; mark_effect_started/recover_ambiguous_activity are never "
        "invoked in the campaign"),
    "H07 clock skew: heartbeat in the past": (
        "H26", PRESENT, "a backwards heartbeat does not extend the lease; reclaim still occurs"),
    "H08 payload hash not binding effect": None,  # no corresponding matrix row
    "H09 authority projection via API": (
        "H24", PRESENT, "fully-capable actor cannot write the authority projection -> 403"),
    "H10 atlas plane half-write": (
        "H17", PARTIAL,
        "shows no partial commit survives an aborted multi-record batch, which is the row's "
        "INVARIANT; the row's mechanism (DB failover mid-transition) is not simulated"),
    "H11 mutable image tag": ("H27", PRESENT, "an artifact ref without a digest is refused"),
    "H12 secret value in provenance": (
        "H23", PARTIAL,
        "covers 'no secret in receipt/log' (reference only). Secret ROTATION during a worker "
        "lifetime, and the declared-revision change, are not exercised"),
}
COVERED = {v[0]: v for v in CAMPAIGN_TO_MATRIX.values() if v}

assurance_path = Path("research/orion_engineering_closure_v1/HOSTILE_ASSURANCE_V3.json")
try:
    assurance = json.loads(assurance_path.read_text())
    executed_ids = {r["case"] for r in assurance["results"]}
    executed_named = {f"{r['case']} {r['name']}" for r in assurance["results"]}
    assurance_readable = True
except Exception as exc:  # noqa: BLE001
    assurance, executed_ids, executed_named, assurance_readable = None, set(), set(), False
    add(Finding("MATRIX-assurance-readable", MATRIX, "artifact", str(assurance_path), CANNOT_CHECK,
                "-", f"{type(exc).__name__}: {exc}"))

if assurance_readable:
    unknown = sorted(executed_named - set(CAMPAIGN_TO_MATRIX))
    if unknown:
        add(Finding("MATRIX-campaign-drift", MATRIX, "artifact", "campaign case list", CANNOT_CHECK,
                    str(assurance_path),
                    f"executed cases not in the hand-read mapping: {unknown}; rerun the mapping"))
    for row, desc in MATRIX_ROWS.items():
        if row in COVERED:
            _r, _verdict, _why = COVERED[row]
            src = [k for k, v in CAMPAIGN_TO_MATRIX.items() if v and v[0] == row][0]
            add(Finding(f"MATRIX-{row}", MATRIX, "hostile_case", f"{row} {desc}", _verdict,
                        f"{assurance_path} :: campaign case {src!r}", _why))
        else:
            collides = row in executed_ids
            add(Finding(f"MATRIX-{row}", MATRIX, "hostile_case", f"{row} {desc}", ABSENT,
                        str(assurance_path),
                        ("NOT executed by the frozen campaign; the campaign REUSES this id for a "
                         "different attack" if collides else "NOT executed by the frozen campaign")))

# ---------------------------------------------------------------------------
# GAP_LEDGER fibres -- the modules CLOSURE_ASSESSMENT_V3 cites as evidence
# ---------------------------------------------------------------------------

V3_EVIDENCE = {
    "E1": ("rakl.engineering_state", None), "E2": ("rakl.engineering_store", None),
    "E3": ("rakl.engineering_atlas_store", None),
    "E4": ("rakl.project_runtime", "RAKLProject.next_action"),
    "E5": ("rakl.engineering_atomic", None),
    "E6": ("rakl.engineering_workflow_workers", None), "E7": ("rakl.engineering_index", None),
    "E8": ("rakl.engineering_service", None), "E9": ("rakl.governed_solver", "governed_solve"),
    "E10": ("rakl.engineering_http", None), "E11": ("rakl.engineering_ops", "project_observatory"),
    "E12": ("rakl.engineering_http", "Telemetry"), "E13": ("rakl.engineering_http", "IdentityProvider"),
    "E14": ("rakl.engineering_migration", None), "E15": ("rakl.engineering_ops", "verify_restore"),
    "E16": ("rakl.engineering_release", None), "E17": ("rakl.engineering_ops", "ResourceBudget"),
    "E18": (None, None), "E19": ("rakl.engineering_ops", "BuildProvenance"),
    "E20": ("rakl.engineering_ops", "OperatorDoctor"),
}
for fid, (mod, attr) in sorted(V3_EVIDENCE.items()):
    if mod is None:
        add(Finding(f"V3-evidence-{fid}", "CLOSURE_ASSESSMENT_V3.json", "artifact",
                    "run_hostile_assurance_v3.py + HOSTILE_ASSURANCE_V3.json",
                    PRESENT if assurance_readable else CANNOT_CHECK,
                    str(assurance_path), "see MATRIX-* rows for what it covers"))
    elif attr is None:
        add(check_module(f"V3-evidence-{fid}", "CLOSURE_ASSESSMENT_V3.json", mod))
    else:
        add(check_attr(f"V3-evidence-{fid}", "CLOSURE_ASSESSMENT_V3.json", mod, attr))

# ---------------------------------------------------------------------------
# Checker self-validation -- both directions, on hand-verified items
# ---------------------------------------------------------------------------

CONTROLS = [
    ("known-present-module", check_module("c", "self", "rakl.engineering_state"), PRESENT),
    ("known-present-field", check_fields("c", "self", "rakl.engineering_state", "ProjectSnapshot",
                                         ["evidence_cutoff"]), PRESENT),
    ("known-absent-attr", check_attr("c", "self", "rakl.engineering_state",
                                     "ThisSymbolDoesNotExist"), ABSENT),
    ("known-absent-module", check_module("c", "self", "rakl.no_such_module_xyz"), ABSENT),
    ("uncheckable-field-target", check_fields("c", "self", "rakl.engineering_state", "canonical_sha256",
                                              ["anything"]), CANNOT_CHECK),
]
controls = [{"control": n, "expected": exp, "got": f.verdict, "ok": f.verdict == exp}
            for n, f, exp in CONTROLS]

# ---------------------------------------------------------------------------

by_verdict = summarize(findings)
negatives = [f.to_dict() for f in findings if f.verdict in (ABSENT, PARTIAL, CANNOT_CHECK)]

report = {
    "audit_version": "orion-engineering-conformance-audit-v1",
    "axis": "NAMED_SURFACE_CONFORMANCE_ONLY",
    "what_this_does_not_decide": (
        "whether each GAP_LEDGER falsifier is defeated. A fibre can defeat its falsifier "
        "with a differently-named abstraction, and can carry every named symbol while its "
        "falsifier stands. Only the named-surface question is answered mechanically here."
    ),
    "grants_scientific_authority": False,
    "concurrent_work_qualifications": {
        "note": (
            "Other sessions landed files into this working tree while the audit ran. Each was "
            "checked against every ABSENT verdict below; none defines any symbol this audit "
            "reports as absent. Two qualifications are recorded so the negatives are not read "
            "more harshly than the evidence supports."),
        "qualifications": [
            {
                "audit_item": "API-view-4-solver-state",
                "mechanical_verdict": "ABSENT on rakl.engineering_ops.ObservatoryView",
                "qualification": (
                    "rakl.engineering_integration.SnapshotBoundSolverView already carries "
                    "support_structure_id, compiler_identity, obstruction_ids and source_evidence_ids, "
                    "all bound to project_snapshot_id, and solver_view_freshness computes staleness. "
                    "That IS API view 4's content. The ObservatoryView field is absent; the "
                    "capability is not. This is a wiring gap, not a missing mechanism."),
            },
            {
                "audit_item": "API-view-7-evolution-history",
                "mechanical_verdict": "ABSENT on rakl.engineering_ops.ObservatoryView",
                "qualification": (
                    "rakl.evolution_archive (RAKLVariant, VariantStatus, register_challenger, "
                    "variant_promotion_subject_hash) and rakl.promotion_attestation carry "
                    "challenger/promotion identities. The ObservatoryView field is absent; the "
                    "capability is not."),
            },
            {
                "audit_item": "API-view-8-operational-health",
                "mechanical_verdict": "ABSENT on rakl.engineering_ops.ObservatoryView",
                "qualification": (
                    "src/rakl/engineering_doctor_probes.py (landed concurrently) provides "
                    "probe_database / probe_object_store / probe_index / probe_workflow_workers / "
                    "probe_backup / probe_secrets. API_AND_OBSERVATORY view 8 requires operational "
                    "health 'clearly separated from scientific status', which a separate doctor "
                    "surface arguably satisfies. The ObservatoryView field is still absent; the "
                    "capability is not."),
            },
            {
                "audit_item": "ARCH-5 metadata families",
                "mechanical_verdict": "9 families ABSENT from all 8 sqlite stores",
                "qualification": (
                    "research/orion_engineering_closure_v1/POSTGRES_SCHEMA_V1.sql (landed "
                    "concurrently) mirrors the SQLite tables exactly and also contains none of the "
                    "9 missing families. The gap is therefore reproduced in the production-class "
                    "backend, not closed by it. This STRENGTHENS the finding."),
            },
        ],
    },
    "negative_history_preserved": {
        "note": (
            "The first execution of this audit, against the tree as the parent session left it, "
            "found these named surfaces ABSENT. They are recorded here permanently. Some were "
            "closed by this same session; the record of their absence is not rewritten."),
        "first_run_summary": {"PRESENT": 58, "ABSENT": 50, "PARTIAL": 4, "CANNOT_CHECK": 0},
        "absent_at_first_run_and_closed_by_this_session": [
            "IMPLEMENTATION_LADDER wave E2: SnapshotRepository",
            "IMPLEMENTATION_LADDER wave E2: SemanticRepository",
            "IMPLEMENTATION_LADDER wave E2: MetrologyRepository",
            "IMPLEMENTATION_LADDER wave E2: TransitionRepository",
            "IMPLEMENTATION_LADDER wave E5: ResearchWorkflowEngine",
            "IMPLEMENTATION_LADDER wave E8: the 8 allowed terminals",
        ],
        "closed_how": (
            "src/rakl/engineering_contracts.py -- runtime_checkable Protocols asserted against the "
            "existing concrete classes in tests/test_engineering_conformance.py, plus WaveE8Terminal. "
            "This closes the NAMED-SURFACE gap only. It adds no persistence, no routes and no "
            "production backend, and it does not move any fibre's production readiness."),
        "absent_at_first_run_and_STILL_OPEN": [
            "API_AND_OBSERVATORY: 10 of 12 named routes 404",
            "API_AND_OBSERVATORY: mutations do not return a StateTransitionReceipt",
            "API_AND_OBSERVATORY: query strings are not parsed out of the path segment",
            "API_AND_OBSERVATORY: Observatory views 4 (solver state), 7 (evolution history), "
            "8 (operational health) have no fields on ObservatoryView",
            "ARCHITECTURE 5: 9 named metadata families have no table in any engineering store",
            "HOSTILE_TEST_MATRIX: 19 of 30 rows never executed by the frozen campaign",
        ],
        "why_still_open": (
            "Those live in src/rakl/engineering_http.py and src/rakl/engineering_ops.py, which this "
            "audit does not own, and in the case of the hostile matrix they are execution "
            "obligations rather than missing symbols. They are reported, not patched."),
    },
    "checker_self_validation": {
        "controls": controls,
        "all_controls_passed": all(c["ok"] for c in controls),
    },
    "summary": dict(by_verdict),
    "hostile_matrix_coverage": {
        "rows_specified": len(MATRIX_ROWS),
        "rows_fully_attacked": sorted(r for r, (_, v, _w) in COVERED.items() if v == PRESENT),
        "rows_partially_attacked": sorted(r for r, (_, v, _w) in COVERED.items() if v == PARTIAL),
        "rows_not_attacked": sorted(set(MATRIX_ROWS) - set(COVERED)),
        "mapping_is_an_analyst_judgement": (
            "campaign_case_to_matrix_row below is a hand mapping by CONTENT, produced by reading "
            "run_hostile_assurance_v3.py case by case. It is not a mechanical result. The per-row "
            "'why' text in each MATRIX-* finding is what makes it reviewable; disagree with a row "
            "by disputing its reason, not the count."),
        "campaign_case_to_matrix_row": {
            k: (v[0] if v else None) for k, v in sorted(CAMPAIGN_TO_MATRIX.items())},
        "campaign_reuses_matrix_ids_for_different_attacks": sorted(
            k.split()[0] for k, v in CAMPAIGN_TO_MATRIX.items()
            if k.split()[0] in MATRIX_ROWS and (v is None or v[0] != k.split()[0])),
        "note": (
            "CLOSURE_ASSESSMENT_V3 reports hostile_assurance held=12 total=12. That is true of the "
            "campaign's OWN 12 cases. The campaign numbers them H01..H12, colliding with the "
            "HOSTILE_TEST_MATRIX namespace while attacking different things: campaign H01 is "
            "'stale snapshot mutation', matrix H01 is 'kill during canonical blob write'."),
    },
    "findings": [f.to_dict() for f in findings],
    "negatives_preserved": negatives,
    "closure_assessment_v3_review": {
        "claim_reviewed": "all 20 fibres REFERENCE_IMPLEMENTED, terminal "
                          "ALL_FIBRES_REFERENCE_IMPLEMENTED__PRODUCTION_RESIDUALS_TYPED",
        "verdict": "OVERCLAIMS ON TWO FIBRES (E10, E18); one citation defect (E4); "
                   "the remaining seventeen hold on the falsifier axis",
        "axis_note": (
            "'REFERENCE_IMPLEMENTED' in V3 asserts falsifier closure. A fibre can close its "
            "GAP_LEDGER falsifier while the surface the packet's own ladder/API named is absent. "
            "Only E10 and E18 are overclaims; the rest are gaps, citation defects, or nothing."),
        "per_fibre": [
            {"fiber": "E18", "verdict": "OVERCLAIM", "axis": "falsifier + spec obligation",
             "evidence": (
                 "V3 marks E18 REFERENCE_IMPLEMENTED citing a 12-case campaign. Those 12 cases "
                 "attack 7 of the 30 HOSTILE_TEST_MATRIX rows fully and 4 partially; 19 rows are "
                 "never executed. E18's own ledger 'next' is 'execute HOSTILE_TEST_MATRIX on "
                 "release candidate'. Compounding it, the campaign numbers its cases H01..H12, "
                 "colliding with the matrix namespace while attacking different things -- a reader "
                 "cross-referencing 'H01 held' concludes 'kill during canonical blob write' held. "
                 "It did not. run_hostile_assurance_v3.py itself is honest: its docstring freezes "
                 "its own list and never claims to be the matrix. The defect is in the assessment "
                 "that cites it as E18 closure, and in the colliding ID namespace.")},
            {"fiber": "E10", "verdict": "OVERCLAIM", "axis": "the packet's own API contract",
             "evidence": (
                 "The GAP_LEDGER falsifier ('a mutating request has no idempotency/snapshot "
                 "contract') IS defeated. But API_AND_OBSERVATORY.md is also spec: 10 of its 12 "
                 "named routes return 404 NOT_FOUND; query strings are not parsed out of the path "
                 "segment so the spec'd ?snapshot=&target=&fiber= form 404s; and 'Every mutation "
                 "returns a StateTransitionReceipt, even on RETRY_REQUIRED, RECOVERY_REQUIRED or "
                 "CANNOT_CHECK' does not hold -- a commit returns {committed, before_snapshot_id, "
                 "after_snapshot_id, payload_hash, api_version} and a refusal returns "
                 "{error, detail, api_version}. engineering_http.py never imports engineering_state "
                 "and keeps its own in-memory 'snap-N' state. V3's only named E10 residual is "
                 "'TLS, rate limits is deployment', which names none of this.")},
            {"fiber": "E11", "verdict": "PARTIAL_NOT_OVERCLAIM", "axis": "named surface",
             "evidence": (
                 "The falsifier is defeated: ObservatoryView has no method that computes a score "
                 "and every displayed field drills through provenance_ids. Views 1,2,3,5,6 of the "
                 "8 named are carried as fields; views 4,7,8 are not -- but each has a real "
                 "implementation elsewhere (see concurrent_work_qualifications). Wiring gap.")},
            {"fiber": "E4", "verdict": "CITATION_DEFECT", "axis": "evidence citation",
             "evidence": (
                 "V3 cites project_runtime.py::next_action -- a runtime decision function -- as "
                 "evidence for 'metric/decision/residual/saturation PERSISTENCE'. The thing that "
                 "actually persists these is engineering_control_store.SqliteControlProjectionStore "
                 "(ControlArtifactKind = METRIC_RECEIPT, SATURATION_CERTIFICATE, HARD_GATE, "
                 "CONTROLLER_DECISION, RESIDUAL_EVENT, AUTHORITY_PROJECTION). The fibre is "
                 "supported; the cited evidence is not what supports it.")},
            {"fiber": "E3/E4", "verdict": "GAP_NOT_OVERCLAIM", "axis": "named surface",
             "evidence": (
                 "9 of the metadata families ARCHITECTURE 5 names have no table in ANY of the 8 "
                 "engineering sqlite stores: blob_bindings, identity_assertions/lineage_edges, "
                 "residuals/residual_events, research_rounds/novelty_events, "
                 "saturation_bases/saturation_certificates, metric_definitions/metric_receipts, "
                 "hard_gate_observations/controller_decisions, episodes/lessons/tools, "
                 "evolution_variants/promotion_events. Four of those are served by one generic "
                 "control_projection table keyed by kind, without the per-family foreign keys "
                 "ARCHITECTURE 5 requires. V3 claims no more than REFERENCE_IMPLEMENTED here, so "
                 "this is an unstated gap rather than a false claim.")},
            {"fiber": "E2/E5/E6", "verdict": "NOT_AN_OVERCLAIM", "axis": "named surface",
             "evidence": (
                 "The ladder-named abstractions (BlobStore aside) were absent while working "
                 "semantic equivalents existed. Closed by src/rakl/engineering_contracts.py.")},
            {"fiber": "E1,E5,E7,E8,E9,E12,E13,E14,E15,E16,E17,E19,E20",
             "verdict": "CLAIM_HOLDS", "axis": "named surface",
             "evidence": (
                 "Every module and symbol V3 cites resolves, and every named field/enum/method "
                 "this audit checked for these fibres is PRESENT.")},
        ],
        "not_checked_here": (
            "This audit did not independently re-derive whether each falsifier is defeated by the "
            "existing tests. Where it says CLAIM_HOLDS it means the named surface is present and "
            "no contrary evidence was found -- not that the falsifier was re-executed."),
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("=" * 78)
print("ORION ENGINEERING CONFORMANCE AUDIT V1 -- named-surface axis")
print("=" * 78)
for f in findings:
    if f.verdict != PRESENT:
        print(f"  {f.verdict:<13} {f.item_id:<46} {f.detail[:80]}")
print("-" * 78)
print(f"  self-validation controls: {sum(1 for c in controls if c['ok'])}/{len(controls)} as expected")
for c in controls:
    if not c["ok"]:
        print(f"    CONTROL FAILED {c['control']}: expected {c['expected']}, got {c['got']}")
print(f"  {dict(by_verdict)}")
print(f"  hostile matrix: {sum(1 for _r,(_x,_v,_w) in COVERED.items() if _v==PRESENT)} fully + {sum(1 for _r,(_x,_v,_w) in COVERED.items() if _v==PARTIAL)} partial of {len(MATRIX_ROWS)} specified rows attacked by the frozen campaign")
print(f"wrote {OUT}")
