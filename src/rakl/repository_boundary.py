"""Fail-closed repository-boundary checks for framework source trees."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


_MILLENNIUM_APPLICATION_BOUNDARY = (
    "research",
    "real_math",
    "millennium",
)
_INDEX_MODES = {"100644", "100755", "120000", "160000"}


@dataclass(frozen=True, slots=True)
class IndexEntry:
    mode: str
    object_id: str
    stage: int
    path: str


def parse_git_index_entries(raw: bytes) -> tuple[IndexEntry, ...]:
    """Parse ``git ls-files --stage -z`` output without path quoting loss."""

    entries: list[IndexEntry] = []
    records = raw.split(b"\0")
    if records[-1] != b"":
        raise ValueError("git index listing must be NUL terminated")

    for record in records[:-1]:
        try:
            metadata, path_raw = record.split(b"\t", 1)
            mode_raw, object_id_raw, stage_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            object_id = object_id_raw.decode("ascii")
            stage = int(stage_raw.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("malformed git index entry") from exc

        if mode not in _INDEX_MODES:
            raise ValueError(f"unsupported git index mode: {mode}")
        if len(object_id) not in {40, 64} or any(
            character not in "0123456789abcdef" for character in object_id
        ):
            raise ValueError("git object id must be raw lowercase hexadecimal")
        if stage not in {0, 1, 2, 3}:
            raise ValueError(f"unsupported git index stage: {stage}")
        if not path_raw:
            raise ValueError("git index path must not be empty")

        entries.append(
            IndexEntry(
                mode=mode,
                object_id=object_id,
                stage=stage,
                path=os.fsdecode(path_raw),
            )
        )

    return tuple(entries)


def tracked_index_entries(repository: Path) -> tuple[IndexEntry, ...]:
    """Return exact tracked index entries, including symlink/gitlink modes."""

    completed = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return parse_git_index_entries(completed.stdout)


def _normalized_parts(path: str) -> tuple[str, ...]:
    return tuple(
        part.casefold()
        for part in path.replace("\\", "/").split("/")
        if part not in {"", "."}
    )


def find_millennium_application_leaks(
    entries: tuple[IndexEntry, ...],
) -> tuple[IndexEntry, ...]:
    """Find exact or descendant paths in the forbidden application boundary."""

    boundary_length = len(_MILLENNIUM_APPLICATION_BOUNDARY)
    return tuple(
        entry
        for entry in entries
        if _normalized_parts(entry.path)[:boundary_length]
        == _MILLENNIUM_APPLICATION_BOUNDARY
    )
