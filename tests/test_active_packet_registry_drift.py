from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/active_packet_registry_drift.py"


def _load_drift_module():
    spec = importlib.util.spec_from_file_location("active_packet_registry_drift_test_subject", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return proc.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_live_target_basis_drift_blocks_even_when_candidate_head_is_clean(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "rshea-test@example.invalid")
    _git(repo, "config", "user.name", "RSHEA test")

    tracked = repo / "research/mechanic_research_packets_v1/PAPER5_PAPER6_SUCCESSORS.json"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    tracked.write_text('{"basis": 1}\n', encoding="utf-8")
    original = _commit_all(repo, "original registry subject")

    (repo / "README.md").write_text("revalidation-safe change\n", encoding="utf-8")
    anchor = _commit_all(repo, "revalidation anchor")
    _git(repo, "branch", "candidate", anchor)

    # The live target advances with a load-bearing basis change after the
    # candidate was cut. Exact-head-only CI would not see this commit.
    tracked.write_text('{"basis": 2}\n', encoding="utf-8")
    target_sha = _commit_all(repo, "new saturation or packet basis on target")

    _git(repo, "checkout", "candidate")
    assert _git(repo, "rev-parse", "HEAD") == anchor
    assert _git(repo, "rev-parse", "main") == target_sha

    registry_path = repo / "registry.json"
    revalidation_path = repo / "revalidation.json"
    _write_json(registry_path, {"subject_main_sha": original})
    _write_json(
        revalidation_path,
        {
            "original_registry_subject_sha": original,
            "observed_current_main_sha": anchor,
            "relevant_path_changes": [],
        },
    )

    drift = _load_drift_module()
    monkeypatch.setattr(drift, "ROOT", repo)
    monkeypatch.setattr(drift, "REGISTRY", registry_path)
    monkeypatch.setattr(drift, "REVALIDATION", revalidation_path)
    monkeypatch.setenv(drift.TARGET_REF_ENV, "main")

    assert drift.main() == 1
    output = capsys.readouterr().out
    assert "ACTIVE_PACKET_REGISTRY_DRIFT=BLOCKED_KNOWLEDGE_BASIS_CHANGED_ON_TARGET" in output
    assert "PAPER5_PAPER6_SUCCESSORS.json" in output
    assert "ACTION_REQUIRED=explicit_registry_revalidation" in output
    assert "SCIENTIFIC_AUTHORITY_GRANTED=false" in output


def test_unresolvable_live_target_fails_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "rshea-test@example.invalid")
    _git(repo, "config", "user.name", "RSHEA test")

    (repo / "README.md").write_text("subject\n", encoding="utf-8")
    original = _commit_all(repo, "subject")

    registry_path = repo / "registry.json"
    revalidation_path = repo / "revalidation.json"
    _write_json(registry_path, {"subject_main_sha": original})
    _write_json(
        revalidation_path,
        {
            "original_registry_subject_sha": original,
            "observed_current_main_sha": original,
            "relevant_path_changes": [],
        },
    )

    drift = _load_drift_module()
    monkeypatch.setattr(drift, "ROOT", repo)
    monkeypatch.setattr(drift, "REGISTRY", registry_path)
    monkeypatch.setattr(drift, "REVALIDATION", revalidation_path)
    monkeypatch.setenv(drift.TARGET_REF_ENV, "refs/remotes/origin/does-not-exist")

    assert drift.main() == 1
    output = capsys.readouterr().out
    assert "ACTIVE_PACKET_REGISTRY_DRIFT=CANNOT_CHECK reason=target_ref_unresolvable" in output
    assert "SCIENTIFIC_AUTHORITY_GRANTED=false" in output
