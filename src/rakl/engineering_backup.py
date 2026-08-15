"""Reference backup/restore bundle for ORION local engineering stores.

Production PostgreSQL/object storage should use native backup/PITR mechanisms, but the
release gate needs a backend-neutral semantic: a backup binds an exact project snapshot
to exact bytes and a restore must reproduce those bytes before higher-level replay.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
from typing import Iterable, Mapping, Tuple
import zipfile

from .engineering_state import canonical_sha256


class BackupVerdict(str, Enum):
    VALID = "VALID"
    CORRUPT = "CORRUPT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class BackupEntry:
    logical_path: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        p = PurePosixPath(self.logical_path)
        if not self.logical_path or p.is_absolute() or ".." in p.parts:
            raise ValueError("backup logical path must be safe and relative")
        if len(self.sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.sha256):
            raise ValueError("backup entry sha256 must be lowercase SHA-256")
        if self.size_bytes < 0:
            raise ValueError("backup entry size cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "logical_path": self.logical_path,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
        }


@dataclass(frozen=True)
class BackupManifest:
    project_snapshot_id: str
    created_at_utc: str
    entries: Tuple[BackupEntry, ...]
    backup_id: str = ""

    def __post_init__(self) -> None:
        if not self.project_snapshot_id or not self.created_at_utc:
            raise ValueError("backup manifest requires snapshot and timestamp")
        normalized = self.created_at_utc[:-1] + "+00:00" if self.created_at_utc.endswith("Z") else self.created_at_utc
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError("backup created_at_utc must be timezone-aware UTC")
        names = [item.logical_path for item in self.entries]
        if not self.entries or len(names) != len(set(names)):
            raise ValueError("backup entries must be non-empty and unique")
        expected = "backup:" + canonical_sha256(self.identity_payload)
        if self.backup_id and self.backup_id != expected:
            raise ValueError("backup_id does not match manifest")
        if not self.backup_id:
            object.__setattr__(self, "backup_id", expected)

    @property
    def identity_payload(self) -> Mapping[str, object]:
        return {
            "project_snapshot_id": self.project_snapshot_id,
            "created_at_utc": self.created_at_utc,
            "entries": [item.to_dict() for item in self.entries],
        }

    def to_dict(self) -> dict[str, object]:
        return {**self.identity_payload, "backup_id": self.backup_id}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "BackupManifest":
        return cls(
            project_snapshot_id=str(value["project_snapshot_id"]),
            created_at_utc=str(value["created_at_utc"]),
            entries=tuple(
                BackupEntry(
                    logical_path=str(item["logical_path"]),
                    sha256=str(item["sha256"]),
                    size_bytes=int(item["size_bytes"]),
                )
                for item in value["entries"]
            ),
            backup_id=str(value.get("backup_id", "")),
        )


@dataclass(frozen=True)
class BackupVerification:
    verdict: BackupVerdict
    backup_id: str | None
    reasons: Tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.verdict is BackupVerdict.VALID


def _digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def _collect(inputs: Mapping[str, str | Path]) -> list[tuple[str, Path]]:
    result: list[tuple[str, Path]] = []
    for logical_root, source_value in sorted(inputs.items()):
        root = PurePosixPath(logical_root)
        if not logical_root or root.is_absolute() or ".." in root.parts:
            raise ValueError("backup input labels must be safe relative paths")
        source = Path(source_value)
        if source.is_symlink():
            raise ValueError(f"backup source cannot be symlink:{source}")
        if source.is_file():
            result.append((logical_root, source))
        elif source.is_dir():
            for child in sorted(path for path in source.rglob("*") if path.is_file() or path.is_symlink()):
                if child.is_symlink():
                    raise ValueError(f"backup tree cannot contain symlink:{child}")
                relative = child.relative_to(source).as_posix()
                result.append(((root / relative).as_posix(), child))
        else:
            raise FileNotFoundError(source)
    return result



def create_consistent_sqlite_copy(
    source_database: str | Path, destination_database: str | Path
) -> Path:
    """Create a transactionally consistent SQLite backup including live WAL state.

    Copying only the main ``.sqlite3`` file while the database runs in WAL mode can
    silently omit committed pages. SQLite's online backup API reads a coherent
    database snapshot and is therefore the reference backup primitive.
    """
    source = Path(source_database)
    destination = Path(destination_database)
    if not source.is_file():
        raise FileNotFoundError(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    src = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    dst = sqlite3.connect(destination)
    try:
        src.backup(dst)
        row = dst.execute("PRAGMA quick_check").fetchone()
        if row is None or row[0] != "ok":
            raise ValueError("SQLite backup quick_check failed")
        dst.commit()
    finally:
        dst.close(); src.close()
    return destination

def create_reference_backup(
    output_zip: str | Path,
    *,
    project_snapshot_id: str,
    created_at_utc: str,
    inputs: Mapping[str, str | Path],
) -> BackupManifest:
    files = _collect(inputs)
    entries: list[BackupEntry] = []
    payloads: dict[str, bytes] = {}
    for logical_path, path in files:
        data = path.read_bytes()
        payloads[logical_path] = data
        entries.append(BackupEntry(logical_path, _digest(data), len(data)))
    manifest = BackupManifest(project_snapshot_id, created_at_utc, tuple(entries))
    target = Path(output_zip)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for logical_path in sorted(payloads):
            archive.writestr(f"payloads/{logical_path}", payloads[logical_path])
        archive.writestr(
            "manifest.json",
            json.dumps(manifest.to_dict(), sort_keys=True, separators=(",", ":")),
        )
    return manifest


def verify_reference_backup(path: str | Path) -> BackupVerification:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                return BackupVerification(
                    BackupVerdict.CORRUPT,
                    None,
                    ("duplicate_archive_member_name",),
                )
            manifest = BackupManifest.from_dict(json.loads(archive.read("manifest.json")))
            expected_members = {"manifest.json"} | {
                f"payloads/{entry.logical_path}" for entry in manifest.entries
            }
            actual_members = set(names)
            reasons: list[str] = []
            for unexpected in sorted(actual_members - expected_members):
                reasons.append(f"unexpected_archive_member:{unexpected}")
            for missing in sorted(expected_members - actual_members):
                reasons.append(f"missing_archive_member:{missing}")
            for entry in manifest.entries:
                try:
                    data = archive.read(f"payloads/{entry.logical_path}")
                except KeyError:
                    reasons.append(f"missing_payload:{entry.logical_path}")
                    continue
                if len(data) != entry.size_bytes:
                    reasons.append(f"size_mismatch:{entry.logical_path}")
                if _digest(data) != entry.sha256:
                    reasons.append(f"digest_mismatch:{entry.logical_path}")
            if reasons:
                return BackupVerification(BackupVerdict.CORRUPT, manifest.backup_id, tuple(reasons))
            return BackupVerification(BackupVerdict.VALID, manifest.backup_id, ("all_backup_payloads_verified",))
    except (OSError, zipfile.BadZipFile, KeyError, ValueError, json.JSONDecodeError) as error:
        return BackupVerification(
            BackupVerdict.CANNOT_CHECK,
            None,
            (f"backup_unreadable_or_invalid:{error.__class__.__name__}",),
        )


def restore_reference_backup(path: str | Path, destination: str | Path) -> BackupManifest:
    verification = verify_reference_backup(path)
    if not verification.valid:
        raise ValueError(f"backup not restorable:{verification.verdict.value}")
    dest = Path(destination)
    if dest.exists() and any(dest.iterdir()):
        raise ValueError("restore destination must be empty")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "r") as archive:
        manifest = BackupManifest.from_dict(json.loads(archive.read("manifest.json")))
        for entry in manifest.entries:
            target = dest / PurePosixPath(entry.logical_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(f"payloads/{entry.logical_path}"))
    # Verify the restored filesystem independently of ZIP verification.
    for entry in manifest.entries:
        data = (dest / PurePosixPath(entry.logical_path)).read_bytes()
        if _digest(data) != entry.sha256:
            raise ValueError(f"restored digest mismatch:{entry.logical_path}")
    return manifest
