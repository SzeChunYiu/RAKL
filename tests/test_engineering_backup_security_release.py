from hashlib import sha256
import json
from pathlib import Path
import zipfile

from rakl.engineering_backup import (
    BackupVerdict,
    create_reference_backup,
    restore_reference_backup,
    verify_reference_backup,
)
from rakl.engineering_doctor import (
    DiagnosticSeverity,
    build_doctor_report,
    classify_transition_status,
)
from rakl.engineering_release import (
    ArtifactVerificationVerdict,
    RuntimeArtifactIdentity,
    verify_runtime_artifact,
)
from rakl.engineering_security import (
    InfraCapability,
    InfrastructurePrincipal,
    authorize_infrastructure,
)
from rakl.engineering_state import TransitionStatus


def test_backup_restore_reproduces_exact_files_and_detects_corruption(tmp_path):
    db = tmp_path / "state.sqlite3"
    db.write_bytes(b"sqlite bytes")
    blobs = tmp_path / "blobs"
    (blobs / "aa").mkdir(parents=True)
    (blobs / "aa" / "object").write_bytes(b"blob bytes")
    archive = tmp_path / "backup.zip"
    manifest = create_reference_backup(
        archive,
        project_snapshot_id="snapshot:" + "a" * 64,
        created_at_utc="2026-08-15T15:00:00+00:00",
        inputs={"metadata/state.sqlite3": db, "blobs": blobs},
    )
    assert verify_reference_backup(archive).verdict is BackupVerdict.VALID
    restored = tmp_path / "restored"
    assert restore_reference_backup(archive, restored).backup_id == manifest.backup_id
    assert (restored / "metadata/state.sqlite3").read_bytes() == b"sqlite bytes"
    assert (restored / "blobs/aa/object").read_bytes() == b"blob bytes"

    corrupt = tmp_path / "corrupt.zip"
    with zipfile.ZipFile(archive, "r") as src, zipfile.ZipFile(corrupt, "w") as dst:
        for name in src.namelist():
            data = src.read(name)
            if name == "payloads/metadata/state.sqlite3":
                data = b"corrupt"
            dst.writestr(name, data)
    assert verify_reference_backup(corrupt).verdict is BackupVerdict.CORRUPT


def test_infrastructure_authorization_is_not_scientific_authority():
    principal = InfrastructurePrincipal(
        principal_id="worker:1",
        workload_identity="spiffe://example.org/orion/worker",
        capabilities=(InfraCapability.EXECUTE, InfraCapability.OBSERVE),
    )
    assert authorize_infrastructure(principal, InfraCapability.EXECUTE).allowed
    assert not authorize_infrastructure(principal, InfraCapability.GOVERNANCE_PROMOTE).allowed
    assert not principal.grants_scientific_authority


def test_runtime_artifact_binds_exact_bytes_and_digest_pinned_image():
    payload = b"orion executable"
    identity = RuntimeArtifactIdentity(
        artifact_name="orion-worker",
        artifact_sha256=sha256(payload).hexdigest(),
        source_revision="git:abc123",
        builder_id="builder:ci:v1",
        build_type="https://example.org/build/python-wheel",
        provenance_id="slsa:attestation:1",
        image_digest="sha256:" + "b" * 64,
    )
    assert verify_runtime_artifact(identity, payload).verdict is ArtifactVerificationVerdict.VERIFIED
    assert verify_runtime_artifact(identity, b"wrong").verdict is ArtifactVerificationVerdict.MISMATCH
    assert not identity.grants_scientific_authority


def test_doctor_keeps_retry_separate_from_manual_recovery():
    retry = classify_transition_status(TransitionStatus.RETRY_REQUIRED, "stale snapshot")
    recovery = classify_transition_status(TransitionStatus.RECOVERY_REQUIRED, "possible side effect")
    retry_report = build_doctor_report((retry,))
    assert retry_report.healthy
    assert not retry_report.requires_manual_recovery
    recovery_report = build_doctor_report((recovery,))
    assert not recovery_report.healthy
    assert recovery_report.requires_manual_recovery
    assert recovery.severity is DiagnosticSeverity.RECOVERY


def test_reference_backup_rejects_symlink_escape(tmp_path):
    outside = tmp_path / "secret.txt"; outside.write_text("secret")
    root = tmp_path / "tree"; root.mkdir()
    (root / "escape").symlink_to(outside)
    import pytest
    with pytest.raises(ValueError, match="symlink"):
        create_reference_backup(
            tmp_path / "bad.zip",
            project_snapshot_id="snapshot:" + "a" * 64,
            created_at_utc="2026-08-15T15:00:00+00:00",
            inputs={"tree": root},
        )


def test_runtime_artifact_rejects_malformed_digest_pinned_image():
    import pytest
    payload = b"artifact"
    with pytest.raises(ValueError, match="SHA-256"):
        RuntimeArtifactIdentity(
            artifact_name="orion", artifact_sha256=sha256(payload).hexdigest(),
            source_revision="git:x", builder_id="b", build_type="wheel", provenance_id="p",
            image_digest="sha256:not-a-real-digest",
        )


def test_sqlite_consistent_copy_includes_committed_wal_state(tmp_path):
    import sqlite3
    from rakl.engineering_backup import create_consistent_sqlite_copy
    source = tmp_path / "live.sqlite3"
    db = sqlite3.connect(source)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE t(x TEXT)")
    db.execute("INSERT INTO t VALUES('committed-in-wal')")
    db.commit()
    stable = create_consistent_sqlite_copy(source, tmp_path / "stable.sqlite3")
    with sqlite3.connect(stable) as restored:
        assert restored.execute("SELECT x FROM t").fetchone()[0] == "committed-in-wal"
    db.close()


def test_backup_rejects_duplicate_or_unmanifested_archive_members(tmp_path):
    import zipfile
    source = tmp_path / "state.bin"; source.write_bytes(b"state")
    backup = tmp_path / "backup.zip"
    create_reference_backup(
        backup, project_snapshot_id="snapshot:" + "a" * 64,
        created_at_utc="2026-08-15T15:00:00+00:00", inputs={"state.bin": source},
    )
    with zipfile.ZipFile(backup, "a") as z:
        z.writestr("payloads/unmanifested.bin", b"shadow")
    assert verify_reference_backup(backup).verdict is BackupVerdict.CORRUPT

    clean = tmp_path / "clean.zip"
    create_reference_backup(
        clean, project_snapshot_id="snapshot:" + "a" * 64,
        created_at_utc="2026-08-15T15:00:00+00:00", inputs={"state.bin": source},
    )
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(clean, "a") as z:
            # ZIP permits duplicate names. An ambiguous archive is invalid even when one
            # copy matches the manifest.
            z.writestr("payloads/state.bin", b"other")
    assert verify_reference_backup(clean).verdict is BackupVerdict.CORRUPT
