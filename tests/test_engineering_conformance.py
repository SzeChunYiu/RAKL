"""The conformance checker is itself checked -- in BOTH directions.

A checker that has only ever been run against passing cases proves nothing. Every
resolver here is asserted against a thing that is known to exist AND a thing that
is known not to exist, plus the uncheckable case, which must never be reported as
either.
"""

from __future__ import annotations

import dataclasses

import pytest

from rakl.engineering_conformance import (
    ABSENT, CANNOT_CHECK, Finding, PARTIAL, PRESENT,
    check_attr, check_behavioural, check_enum_members, check_fields,
    check_methods, check_module, check_sqlite_tables, summarize,
)


# --- module resolver -------------------------------------------------------


def test_module_present() -> None:
    f = check_module("i", "s", "rakl.engineering_state")
    assert f.verdict == PRESENT
    assert f.evidence.endswith("engineering_state.py")


def test_module_absent() -> None:
    assert check_module("i", "s", "rakl.definitely_not_a_module_9f2a").verdict == ABSENT


def test_import_failure_is_cannot_check_not_absent(tmp_path, monkeypatch) -> None:
    """A module that raises on import has NOT been checked. It is not absent."""
    pkg = tmp_path / "brokenpkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "boom.py").write_text("raise RuntimeError('import-time failure')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    f = check_module("i", "s", "brokenpkg.boom")
    assert f.verdict == CANNOT_CHECK
    assert "RuntimeError" in f.detail


def test_missing_third_party_dep_is_cannot_check(tmp_path, monkeypatch) -> None:
    """Absence of a *dependency* is not absence of the module under test."""
    pkg = tmp_path / "deppkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "needs.py").write_text("import a_package_that_is_not_installed_7b1\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    f = check_module("i", "s", "deppkg.needs")
    assert f.verdict == CANNOT_CHECK


# --- attribute resolver ----------------------------------------------------


def test_attr_present() -> None:
    f = check_attr("i", "s", "rakl.engineering_state", "ProjectSnapshot")
    assert f.verdict == PRESENT
    assert f.evidence == "rakl.engineering_state.ProjectSnapshot"


def test_attr_absent() -> None:
    f = check_attr("i", "s", "rakl.engineering_state", "ThisSymbolDoesNotExist")
    assert f.verdict == ABSENT
    assert "no attribute" in f.detail


def test_attr_absent_in_absent_module_is_absent_not_cannot_check() -> None:
    assert check_attr("i", "s", "rakl.no_such_module_4c8", "Anything").verdict == ABSENT


def test_ladder_named_protocols_are_absent_from_the_store_module() -> None:
    """Negative control: the resolver must report absence where absence is real.

    These four are ladder-named. They now live in `rakl.engineering_contracts`
    (landed by this audit) and are still NOT in `rakl.engineering_store`, so the
    same resolver, pointed at the wrong module, must say ABSENT.
    """
    for symbol in ("SnapshotRepository", "SemanticRepository", "MetrologyRepository",
                   "TransitionRepository"):
        f = check_attr("i", "s", "rakl.engineering_store", symbol)
        assert f.verdict == ABSENT, f"{symbol} resolved unexpectedly: {f}"


def test_blobstore_is_present_alongside_the_absent_ones() -> None:
    """The same resolver, same module, opposite answer. Rules out a blanket ABSENT."""
    assert check_attr("i", "s", "rakl.engineering_store", "BlobStore").verdict == PRESENT


# --- field resolver --------------------------------------------------------


def test_fields_all_present() -> None:
    f = check_fields("i", "s", "rakl.engineering_state", "ProjectSnapshot",
                     ["evidence_cutoff", "semantic_state_revision", "controller_epoch_id"])
    assert f.verdict == PRESENT


def test_fields_partial() -> None:
    f = check_fields("i", "s", "rakl.engineering_state", "ProjectSnapshot",
                     ["evidence_cutoff", "a_field_that_is_not_there"])
    assert f.verdict == PARTIAL
    assert "a_field_that_is_not_there" in f.detail


def test_fields_all_missing_is_absent() -> None:
    f = check_fields("i", "s", "rakl.engineering_state", "ProjectSnapshot", ["nope_a", "nope_b"])
    assert f.verdict == ABSENT


def test_fields_on_non_dataclass_is_cannot_check() -> None:
    f = check_fields("i", "s", "rakl.engineering_state", "canonical_sha256", ["x"])
    assert f.verdict == CANNOT_CHECK


def test_class_attribute_is_not_accepted_as_a_dataclass_field(tmp_path, monkeypatch) -> None:
    """A plain class attribute must not be mistaken for a declared field."""
    pkg = tmp_path / "fieldpkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "m.py").write_text(
        "import dataclasses\n"
        "@dataclasses.dataclass\n"
        "class C:\n"
        "    real: int = 0\n"
        "    not_a_field = 1\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    assert check_fields("i", "s", "fieldpkg.m", "C", ["real"]).verdict == PRESENT
    assert check_fields("i", "s", "fieldpkg.m", "C", ["not_a_field"]).verdict == ABSENT


# --- enum resolver ---------------------------------------------------------


def test_enum_members_present_by_name_and_value() -> None:
    f = check_enum_members("i", "s", "rakl.engineering_state", "TransitionStatus",
                           ["COMMITTED", "RETRY_REQUIRED", "RECOVERY_REQUIRED", "CANNOT_CHECK"])
    assert f.verdict == PRESENT


def test_enum_members_absent() -> None:
    f = check_enum_members("i", "s", "rakl.engineering_state", "TransitionStatus",
                           ["NOT_A_REAL_TERMINAL"])
    assert f.verdict == ABSENT


def test_enum_resolver_on_non_enum_is_cannot_check() -> None:
    f = check_enum_members("i", "s", "rakl.engineering_state", "ProjectSnapshot", ["x"])
    assert f.verdict == CANNOT_CHECK


# --- method + table resolvers ---------------------------------------------


def test_blobstore_methods_present() -> None:
    f = check_methods("i", "s", "rakl.engineering_store", "BlobStore",
                      ["put_if_absent", "get_verified", "exists_verified", "stat"])
    assert f.verdict == PRESENT


def test_methods_partial() -> None:
    f = check_methods("i", "s", "rakl.engineering_store", "BlobStore",
                      ["put_if_absent", "no_such_method"])
    assert f.verdict == PARTIAL


def test_tables_resolved_from_sqlite_master_present() -> None:
    f = check_sqlite_tables("i", "s", "rakl.engineering_store", "SqliteEngineeringStateStore",
                            ["project_heads", "snapshots", "transitions"])
    assert f.verdict == PRESENT


def test_tables_absent() -> None:
    f = check_sqlite_tables("i", "s", "rakl.engineering_store", "SqliteEngineeringStateStore",
                            ["saturation_bases", "metric_definitions"])
    assert f.verdict == ABSENT


def test_tables_partial() -> None:
    f = check_sqlite_tables("i", "s", "rakl.engineering_store", "SqliteEngineeringStateStore",
                            ["snapshots", "evolution_variants"])
    assert f.verdict == PARTIAL


# --- behavioural resolver --------------------------------------------------


def test_behavioural_probe_that_raises_is_cannot_check() -> None:
    def boom() -> tuple[str, str, str]:
        raise ValueError("probe blew up")

    f = check_behavioural("i", "s", "x", boom)
    assert f.verdict == CANNOT_CHECK
    assert "ValueError" in f.detail


def test_behavioural_probe_passthrough() -> None:
    assert check_behavioural("i", "s", "x", lambda: (PRESENT, "e", "d")).verdict == PRESENT


# --- the specific behavioural facts the audit reports ----------------------
#
# HISTORY, kept on purpose. The first run of this audit found, against the
# original engineering_http.py: 10 of the 12 API_AND_OBSERVATORY routes 404'd,
# query strings were not parsed out of the path segment, and a committed
# mutation returned {committed, before_snapshot_id, after_snapshot_id,
# payload_hash, api_version} -- not a StateTransitionReceipt. The tests below
# originally PINNED those defects (asserting the 404s, asserting the missing
# receipt). The operate lane then rewired the service over the real stores and
# every one of those assertions inverted. The docstrings say what used to be
# wrong; the assertions say what is true now. A flipped test that reads as if it
# always passed loses the history, so the history is here.


def _service():
    """The rewritten service: real stores in an ephemeral tempdir; project 'p1' created at genesis."""
    import json

    from rakl.engineering_http import (
        Actor, Capability, EngineeringHttpService, IdentityProvider, SecretStore,
    )
    idp, sec = IdentityProvider(), SecretStore()
    svc = EngineeringHttpService(idp=idp, secrets=sec)
    token = idp.issue(Actor("t", frozenset({"p1"}), frozenset(Capability)))
    hdr = {"Authorization": f"Bearer {token}"}
    status, body, _h = svc.handle("POST", "/v1/projects", hdr, json.dumps({"project_id": "p1"}).encode())
    assert int(status) in (200, 201), body
    return svc, hdr, body["snapshot"]["snapshot_id"]


def _mutation(payload: dict, *, key: str, expected: str) -> bytes:
    import json

    from rakl.engineering_http import content_hash
    return json.dumps({"idempotency_key": key, "expected_snapshot_id": expected,
                       "payload": payload, "payload_hash": content_hash(payload)}).encode()


@pytest.mark.parametrize("method,path,mutating", [
    ("GET", "/v1/projects/p1/head", False),
    ("GET", "/v1/projects/p1/snapshots/{genesis}", False),
    ("POST", "/v1/projects/p1/research-rounds", True),
    ("GET", "/v1/projects/p1/epistemic-status", False),
    ("POST", "/v1/projects/p1/actions:plan", True),
    ("POST", "/v1/projects/p1/actions:execute", True),
    ("GET", "/v1/projects/p1/transitions/t1", False),
    ("GET", "/v1/projects/p1/decisions/d1", False),
    ("GET", "/v1/projects/p1/runs/r1", False),
    ("GET", "/v1/projects/p1/provenance/e1", False),
])
def test_specified_api_routes_are_served(method: str, path: str, mutating: bool) -> None:
    """FLIPPED. These routes returned 404 NOT_FOUND ('unknown route') at first audit.

    'Served' here means the route is recognised: the response is anything but the
    unknown-route 404. A typed 4xx from the route's own validation (a missing
    transition id, an unauthenticated caller) is a served route.
    """
    svc, hdr, genesis = _service()
    path = path.format(genesis=genesis)
    body = _mutation({"content_utf8": "x"}, key="k", expected=genesis) if mutating else b""
    status, resp, _h = svc.handle(method, path, hdr, body)
    assert not (int(status) == 404 and resp.get("error") == "NOT_FOUND" and resp.get("detail") == "unknown route"), \
        (method, path, status, resp)
    # and unauthenticated is still gated, not open
    status2, resp2, _h2 = svc.handle(method, path, {}, body)
    assert int(status2) == 401 and resp2.get("error") == "UNAUTHENTICATED", (method, path, status2, resp2)


def test_project_genesis_route_is_served() -> None:
    """FLIPPED. POST /v1/projects was 404 at first audit; it is genesis now (201, a ProjectSnapshot, no receipt)."""
    _svc, _hdr, genesis = _service()
    assert genesis.startswith("snapshot:")


def test_evidence_route_is_served_no_alarm_control() -> None:
    """The one route that was ALWAYS served -- kept so the block above is not a blanket assertion."""
    svc, hdr, genesis = _service()
    status, resp, _h = svc.handle("POST", "/v1/projects/p1/evidence", hdr,
                                  _mutation({"content_utf8": "x"}, key="k", expected=genesis))
    assert int(status) == 200 and resp["status"] == "COMMITTED", (status, resp)


def test_query_string_resolves_on_the_status_route() -> None:
    """FLIPPED. The spec'd ?snapshot=&target=&fiber= form 404'd at first audit because the
    query string was left inside the last path segment. It parses now."""
    svc, hdr, genesis = _service()
    status, body, _h = svc.handle(
        "GET", f"/v1/projects/p1/epistemic-status?snapshot={genesis}&target=t&fiber=f", hdr, b"")
    assert not (int(status) == 404 and body.get("detail") == "unknown route"), (status, body)
    assert body.get("error") != "NOT_FOUND" or "no GET" not in str(body.get("detail")), (status, body)


def test_mutation_response_is_a_state_transition_receipt() -> None:
    """FLIPPED. API_AND_OBSERVATORY.md: 'Every mutation returns a StateTransitionReceipt.'

    At first audit a commit returned {committed, before_snapshot_id, after_snapshot_id,
    payload_hash, api_version} and a refusal returned {error, detail, api_version}. Now
    the body round-trips through StateTransitionReceipt.from_dict on COMMITTED and on
    the RETRY_REQUIRED refusal alike, and `status` is in the TransitionStatus vocabulary.
    """
    from rakl.engineering_state import StateTransitionReceipt, TransitionStatus

    svc, hdr, genesis = _service()
    status, resp, _h = svc.handle("POST", "/v1/projects/p1/evidence", hdr,
                                  _mutation({"content_utf8": "one"}, key="k1", expected=genesis))
    assert int(status) == 200
    receipt = StateTransitionReceipt.from_dict(resp)
    assert receipt.status is TransitionStatus.COMMITTED and receipt.transition_id == resp["transition_id"]
    # a stale-snapshot refusal is ALSO a receipt
    status2, resp2, _h2 = svc.handle("POST", "/v1/projects/p1/evidence", hdr,
                                     _mutation({"content_utf8": "two"}, key="k2", expected=genesis))
    receipt2 = StateTransitionReceipt.from_dict(resp2)
    assert int(status2) == 409 and receipt2.status is TransitionStatus.RETRY_REQUIRED
    assert receipt2.after_snapshot_id is None


def test_the_two_workflow_engines_share_no_common_scheduling_surface() -> None:
    """IMPLEMENTATION_LADDER wave E5 names one `ResearchWorkflowEngine`. There isn't one."""
    from rakl.engineering_workflow import SqliteReferenceWorkflowEngine
    from rakl.engineering_workflow_workers import SqliteWorkerWorkflowEngine

    a = {n for n in dir(SqliteReferenceWorkflowEngine) if not n.startswith("_")}
    b = {n for n in dir(SqliteWorkerWorkflowEngine) if not n.startswith("_")}
    assert a & b == {"activity", "events", "verify_history"}
    assert "schedule_activity" in a and "schedule_activity" not in b
    assert "claim" in b and "claim" not in a


def test_hostile_campaign_ids_no_longer_collide_with_the_matrix_namespace() -> None:
    r"""FLIPPED. HOSTILE_ASSURANCE_V3 originally numbered its 12 cases H01..H12 -- the
    HOSTILE_TEST_MATRIX namespace -- while attacking different things (campaign 'H01
    stale snapshot mutation' vs matrix 'H01 kill during canonical blob write'). The
    ids are A01..A12 now; no campaign case may match ^H\d\d$."""
    import json
    import re
    from pathlib import Path

    p = Path("research/orion_engineering_closure_v1/HOSTILE_ASSURANCE_V3.json")
    if not p.exists():
        pytest.skip("assurance receipt not present in this checkout")
    data = json.loads(p.read_text())
    ids = [r["case"] for r in data["results"]]
    assert len(ids) == 12
    assert not any(re.fullmatch(r"H\d\d", i) for i in ids), ids
    assert all(re.fullmatch(r"A\d\d", i) for i in ids), ids
    assert "A01..A12" in data.get("case_id_namespace", "")


def test_matrix_execution_receipt_covers_all_thirty_rows() -> None:
    """The matrix itself is executed row-by-row in run_hostile_matrix.py; every row has an outcome."""
    import json
    from pathlib import Path

    p = Path("research/orion_engineering_closure_v1/HOSTILE_MATRIX_EXECUTION_V1.json")
    if not p.exists():
        pytest.skip("matrix execution receipt not present in this checkout")
    data = json.loads(p.read_text())
    rows = {r["row"] for r in data["results"]}
    assert rows == {f"H{i:02d}" for i in range(1, 31)}
    assert all(r["verdict"] in ("HELD", "BROKE", "CANNOT_CHECK") for r in data["results"])
    assert data["harness_self_validation"]["all_broke_as_required"] is True


# --- Finding hygiene -------------------------------------------------------


def test_finding_rejects_an_invented_verdict() -> None:
    with pytest.raises(ValueError):
        Finding("i", "s", "attr", "x", "PROBABLY_FINE", "e")


def test_summarize_counts_every_verdict_class() -> None:
    fs = [Finding("a", "s", "attr", "x", PRESENT, "e"), Finding("b", "s", "attr", "y", ABSENT, "-")]
    out = summarize(fs)
    assert out[PRESENT] == 1 and out[ABSENT] == 1 and out[CANNOT_CHECK] == 0


# --- the ladder-named contracts, asserted against the concrete classes -----
#
# A Protocol nothing is checked against is decoration. These assert that the
# existing reference implementations really do satisfy the interfaces the
# IMPLEMENTATION_LADDER named -- and record, as a first-class negative, the one
# place where they do not.


def test_snapshot_and_transition_repositories_are_satisfied() -> None:
    from rakl.engineering_contracts import SnapshotRepository, TransitionRepository
    from rakl.engineering_store import SqliteEngineeringStateStore

    assert issubclass(SqliteEngineeringStateStore, SnapshotRepository)
    assert issubclass(SqliteEngineeringStateStore, TransitionRepository)


def test_semantic_repository_is_satisfied() -> None:
    from rakl.engineering_contracts import SemanticRepository
    from rakl.engineering_semantic_store import SqliteSemanticStateStore

    assert issubclass(SqliteSemanticStateStore, SemanticRepository)


def test_metrology_repository_is_satisfied() -> None:
    from rakl.engineering_contracts import MetrologyRepository
    from rakl.engineering_control_store import SqliteControlProjectionStore

    assert issubclass(SqliteControlProjectionStore, MetrologyRepository)


def test_protocols_are_not_vacuous() -> None:
    """A Protocol every object satisfies would make the assertions above worthless."""
    from rakl.engineering_contracts import (
        MetrologyRepository, ResearchWorkflowEngine, SemanticRepository,
        SnapshotRepository, TransitionRepository,
    )

    class Bare:
        pass

    for proto in (SnapshotRepository, TransitionRepository, SemanticRepository,
                  MetrologyRepository, ResearchWorkflowEngine):
        assert not issubclass(Bare, proto)
        assert not issubclass(dict, proto)


def test_repositories_do_not_cross_satisfy() -> None:
    """The semantic store must not accidentally satisfy the snapshot contract."""
    from rakl.engineering_contracts import SemanticRepository, SnapshotRepository
    from rakl.engineering_semantic_store import SqliteSemanticStateStore
    from rakl.engineering_store import SqliteEngineeringStateStore

    assert not issubclass(SqliteSemanticStateStore, SnapshotRepository)
    assert not issubclass(SqliteEngineeringStateStore, SemanticRepository)


def test_blobstore_adapters_agree_on_identity_for_the_same_bytes(tmp_path) -> None:
    """ARCHITECTURE 6: adapters must return the same identity for the same bytes."""
    from rakl.engineering_contracts import BlobStore
    from rakl.engineering_blob import LocalFilesystemBlobStore

    a = LocalFilesystemBlobStore(tmp_path / "a")
    b = LocalFilesystemBlobStore(tmp_path / "b")
    assert isinstance(a, BlobStore)
    payload = b"canonical bytes"
    assert a.put_if_absent(payload) == b.put_if_absent(payload)
    assert a.get_verified(a.put_if_absent(payload)) == payload


def test_reference_engine_satisfies_the_wave_e5_engine() -> None:
    from rakl.engineering_contracts import ResearchWorkflowEngine, WorkflowHistory
    from rakl.engineering_workflow import SqliteReferenceWorkflowEngine

    assert issubclass(SqliteReferenceWorkflowEngine, WorkflowHistory)
    assert issubclass(SqliteReferenceWorkflowEngine, ResearchWorkflowEngine)


def test_worker_engine_does_not_satisfy_the_wave_e5_engine() -> None:
    """A preserved negative: the two reference engines are NOT interchangeable.

    The worker engine schedules by lease/claim and has no
    schedule_activity/begin_activity/complete_activity/recover_ambiguous_activity.
    Substituting one for the other is a typed error, not a config choice. If this
    ever starts failing, the engines converged -- update the contract, do not
    delete the assertion.
    """
    from rakl.engineering_contracts import ResearchWorkflowEngine, WorkflowHistory
    from rakl.engineering_workflow_workers import SqliteWorkerWorkflowEngine

    assert issubclass(SqliteWorkerWorkflowEngine, WorkflowHistory)
    assert not issubclass(SqliteWorkerWorkflowEngine, ResearchWorkflowEngine)
    missing = [m for m in ("schedule_activity", "begin_activity", "complete_activity",
                           "fail_activity", "recover_ambiguous_activity")
               if not hasattr(SqliteWorkerWorkflowEngine, m)]
    assert missing == ["schedule_activity", "begin_activity", "complete_activity",
                       "fail_activity", "recover_ambiguous_activity"]


def test_key_repository_signatures_are_what_the_protocol_implies() -> None:
    """runtime_checkable checks presence, not signatures. These are load-bearing."""
    import inspect

    from rakl.engineering_semantic_store import SqliteSemanticStateStore
    from rakl.engineering_store import SqliteEngineeringStateStore

    commit = inspect.signature(SqliteSemanticStateStore.commit_batch).parameters
    assert "committed_snapshot_id" in commit and "expected_semantic_revision" in commit
    assert commit["expected_semantic_revision"].kind is inspect.Parameter.KEYWORD_ONLY

    noncommitted = inspect.signature(SqliteEngineeringStateStore.record_noncommitted_transition).parameters
    assert "status" in noncommitted and "reasons" in noncommitted


def test_wave_e8_terminal_vocabulary_is_exactly_the_ladder_list() -> None:
    from rakl.engineering_contracts import WaveE8Terminal

    assert {t.value for t in WaveE8Terminal} == {
        "PRODUCTION_READY_SCOPED", "SINGLE_NODE_READY_ONLY",
        "DURABILITY_READY_CONTROL_INTEGRATION_OPEN", "CONTROL_READY_DISTRIBUTED_RUNTIME_OPEN",
        "SECURITY_OR_RECOVERY_BLOCKED", "PERFORMANCE_ENVELOPE_EXCEEDED",
        "MIGRATION_PARITY_FAILED", "CANNOT_CHECK_RESOURCE_BOUND",
    }
    assert not WaveE8Terminal.PRODUCTION_READY_SCOPED.grants_scientific_authority


def test_audit_now_finds_the_previously_absent_named_surfaces() -> None:
    """End-to-end: the resolvers that reported ABSENT now report PRESENT."""
    for symbol in ("SnapshotRepository", "SemanticRepository", "MetrologyRepository",
                   "TransitionRepository", "ResearchWorkflowEngine", "BlobStore"):
        assert check_attr("i", "s", "rakl.engineering_contracts", symbol).verdict == PRESENT
    assert check_enum_members(
        "i", "s", "rakl.engineering_contracts", "WaveE8Terminal",
        ["PRODUCTION_READY_SCOPED", "MIGRATION_PARITY_FAILED", "CANNOT_CHECK_RESOURCE_BOUND"],
    ).verdict == PRESENT
