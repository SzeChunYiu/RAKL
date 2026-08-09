import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from rakl.release_manifest import (
    ReleaseArtifactSpec,
    ReleaseManifest,
    ReleaseManifestVerdict,
    create_release_manifest,
    verify_release_manifest,
)


REV = "a" * 40


def test_release_manifest_is_deterministic_across_input_order(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    left = create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("data", "b.txt"), ReleaseArtifactSpec("paper", "a.txt")])
    right = create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("paper", "a.txt"), ReleaseArtifactSpec("data", "b.txt")])
    assert left.canonical_json == right.canonical_json
    assert left.manifest_sha256 == right.manifest_sha256
    assert left.authority_scope == "ENGINEERING_ARTIFACT_IDENTITY_ONLY"


def test_changed_and_missing_artifact_fail_verification(tmp_path):
    file = tmp_path / "a.txt"; file.write_text("a", encoding="utf-8")
    manifest = create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("data", "a.txt")])
    file.write_text("changed", encoding="utf-8")
    changed = verify_release_manifest(tmp_path, manifest)
    assert changed.verdict == ReleaseManifestVerdict.FAILED
    assert any("artifact_digest_mismatch" in issue for issue in changed.issues)
    file.unlink()
    missing = verify_release_manifest(tmp_path, manifest)
    assert missing.verdict == ReleaseManifestVerdict.FAILED
    assert any("artifact_unavailable_or_unsafe" in issue for issue in missing.issues)


def test_symlink_and_path_escape_are_rejected(tmp_path):
    outside = tmp_path.parent / "outside-rakl-test.txt"; outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError):
        create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("data", "link.txt")])
    with pytest.raises(ValueError):
        create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("data", "../outside-rakl-test.txt")])
    with pytest.raises(ValueError):
        create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("data", str(outside))])


def test_duplicate_role_path_and_bad_revision_rejected(tmp_path):
    (tmp_path / "a").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("x", "a"), ReleaseArtifactSpec("x", "a")])
    with pytest.raises(ValueError):
        create_release_manifest(tmp_path, source_revision="short", artifacts=[ReleaseArtifactSpec("x", "a")])


def test_manifest_self_tamper_detected(tmp_path):
    (tmp_path / "a").write_text("x", encoding="utf-8")
    manifest = create_release_manifest(tmp_path, source_revision=REV, artifacts=[ReleaseArtifactSpec("x", "a")])
    value = manifest.to_dict(); value["manifest_sha256"] = "0" * 64
    tampered = ReleaseManifest.from_dict(value)
    report = verify_release_manifest(tmp_path, tampered)
    assert report.verdict == ReleaseManifestVerdict.FAILED
    assert "manifest_self_digest_mismatch" in report.issues


def test_built_wheel_can_be_manifested_and_verified(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    release_root = tmp_path / "release"; release_root.mkdir()
    completed = subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "--wheel-dir", str(release_root)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    wheels = list(release_root.glob("*.whl")); assert len(wheels) == 1
    manifest = create_release_manifest(release_root, source_revision=REV, artifacts=[ReleaseArtifactSpec("python-wheel", wheels[0].name)])
    report = verify_release_manifest(release_root, manifest)
    assert report.verdict == ReleaseManifestVerdict.VERIFIED
    assert report.verified_artifact_count == 1
