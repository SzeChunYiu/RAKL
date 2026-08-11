from __future__ import annotations

import io
import json
from pathlib import Path
from urllib.error import HTTPError
import urllib.request

import pytest
import rakl.paper2_cpu_staging_v3_1 as staging


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/paper2_microtrial_v3/CPU_STAGING_ASSET_MANIFEST_V3.json"


class _Response(io.BytesIO):
    status = 200

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def test_artifact_get_uses_same_bound_user_agent_as_probe(tmp_path: Path) -> None:
    observed: list[urllib.request.Request] = []

    def opener(request: urllib.request.Request, *, timeout: int) -> _Response:
        observed.append(request)
        assert timeout == 1800
        return _Response(b"receipt-bound bytes")

    destination = tmp_path / "artifact.bin"
    artifact = {
        "artifact_id": "artifact:test",
        "url": "https://example.invalid/artifact.bin",
    }
    staging._download_artifact(artifact, destination, opener=opener)

    assert destination.read_bytes() == b"receipt-bound bytes"
    assert len(observed) == 1
    request = observed[0]
    assert request.get_method() == "GET"
    assert request.get_header("User-agent") == staging.STAGING_USER_AGENT
    assert staging.STAGING_USER_AGENT == "RAKL-Paper2-Staging-V3/1"


def test_http_error_receipt_records_exact_active_artifact_url_and_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_sha = "a" * 40
    contract = {
        "construction_parent_sha": "b" * 40,
        "candidate_root": str(tmp_path / "candidate"),
        "final_root": str(tmp_path / "final"),
        "failure_root": str(tmp_path / "failures"),
        "fs9_root": str(tmp_path),
        "staging_attestation_policy": {"minimum_free_bytes": 0},
    }
    probe_job_id = "122"
    stage_job_id = "123"
    probe = {
        "verdict": "NETWORK_PROBE_PASS",
        "contract_canonical_sha256": staging._canonical_sha256(contract),
        "expected_repo_sha": expected_sha,
        "observed_repo_sha": expected_sha,
        "slurm_job_id": probe_job_id,
        "observations": [
            {"artifact_id": item["artifact_id"], "http_status": 200, "reachable": True}
            for item in manifest["artifacts"]
        ],
    }
    probe_path = tmp_path / "probe.json"
    probe_path.write_text(json.dumps(probe), encoding="utf-8")
    (tmp_path / "failures").mkdir()
    monkeypatch.setenv("SLURM_JOB_ID", stage_job_id)
    monkeypatch.setenv("RAKL_PROBE_JOB_ID", probe_job_id)
    monkeypatch.setattr(staging, "validate_staging_contract", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(
        staging,
        "_git_attestation",
        lambda *_args: {
            "repo_sha": expected_sha,
            "repo_tree_sha": "c" * 40,
            "checkout_clean": True,
            "construction_parent_sha": contract["construction_parent_sha"],
            "construction_parent_ancestor": True,
        },
    )
    monkeypatch.setattr(staging, "_binding_path", lambda *_args: MANIFEST)
    active = manifest["artifacts"][0]

    def fail_download(artifact: dict, _destination: Path, **_: object) -> None:
        assert artifact == active
        cause = HTTPError(artifact["url"], 403, "Forbidden", hdrs=None, fp=None)
        raise staging.ArtifactDownloadError(artifact, cause) from cause

    monkeypatch.setattr(staging, "_download_artifact", fail_download)
    receipt = staging._stage_assets_impl(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha=expected_sha,
        probe_receipt_path=probe_path,
    )

    assert receipt["verdict"] == "STAGING_FAILED_PRESERVED"
    assert receipt["error_type"] == "ArtifactDownloadError"
    assert receipt["failed_artifact_id"] == active["artifact_id"]
    assert receipt["failed_artifact_url"] == active["url"]
    assert receipt["http_status"] == 403
    assert receipt["candidate_preserved"] is True
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
    assert json.loads((tmp_path / "failures/staging-failed-123.json").read_text()) == receipt
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (ROOT / "schemas/paper2-cpu-staging-result-receipt-v3-1.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(receipt)


def test_setup_failure_never_claims_preservation_without_a_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = {
        "candidate_root": str(tmp_path / ".candidate"),
        "final_root": str(tmp_path / "final"),
        "failure_root": str(tmp_path / "failures"),
    }
    monkeypatch.setenv("SLURM_JOB_ID", "123")
    monkeypatch.setenv("RAKL_PROBE_JOB_ID", "122")

    def fail_setup(**_: object) -> dict:
        raise RuntimeError("planted setup failure")

    monkeypatch.setattr(staging, "_stage_assets_impl", fail_setup)
    receipt = staging.stage_assets(
        contract=contract,
        repository_root=ROOT,
        expected_repo_sha="a" * 40,
        probe_receipt_path=tmp_path / "missing-probe.json",
    )
    assert receipt["verdict"] == "STAGING_FAILED_PRESERVATION_UNVERIFIED"
    assert receipt["candidate_preserved"] is False
    assert receipt["final_exists"] is False
    assert receipt["model_execution_performed"] is False
    assert receipt["evaluated_result_record_count"] == 0
