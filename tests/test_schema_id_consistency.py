"""Frozen-world tests for the schema `$id` consistency checker (issue #148).

These tests build synthetic schema families under `tmp_path` so the checker's
discriminating power is validated against planted worlds, independent of the real
`schemas/` directory (which carries a live, owner-decision-pending split and must not
be edited by this change). A final test runs the checker against the real `schemas/`
and is marked `xfail(strict=True)` to surface the live defect without making CI red.

The checker is invoked as a subprocess (its production entry point), so these tests
exercise exactly the code path CI and operators run.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKER = REPO_ROOT / "scripts" / "audit_schema_id_consistency.py"

CLEAN_BASE = "https://github.com/SzeChunYiu/RAKL/schemas"


def write_schema(repo: Path, name: str, *, id_value: str | None) -> Path:
    """Write a minimal schema file under <repo>/schemas/ with the given $id.

    A None id_value writes a schema with no $id key at all.
    """
    schemas = repo / "schemas"
    schemas.mkdir(parents=True, exist_ok=True)
    document: dict[str, object] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": name,
        "type": "object",
    }
    if id_value is not None:
        document["$id"] = id_value
    path = schemas / name
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


def run_checker(repo: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--repo", str(repo), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def test_clean_control_must_not_fire(tmp_path: Path) -> None:
    """A unified family (one base, matching filenames, all with $id) passes clean."""
    write_schema(
        tmp_path,
        "alpha.schema.json",
        id_value=f"{CLEAN_BASE}/alpha.schema.json",
    )
    write_schema(
        tmp_path,
        "beta.schema.json",
        id_value=f"{CLEAN_BASE}/beta.schema.json",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "findings: none" in result.stdout
    assert "namespace_count: 1" in result.stdout


def test_missing_id_world_is_detected(tmp_path: Path) -> None:
    """A schema with no $id key is flagged MISSING_ID and fails the run."""
    write_schema(
        tmp_path,
        "alpha.schema.json",
        id_value=f"{CLEAN_BASE}/alpha.schema.json",
    )
    write_schema(tmp_path, "beta.schema.json", id_value=None)  # missing $id
    result = run_checker(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "MISSING_ID" in result.stdout
    assert "beta.schema.json" in result.stdout


def test_foreign_base_split_is_detected(tmp_path: Path) -> None:
    """Two schemas under different bases -> split family -> SPLIT_NAMESPACE, nonzero.

    This is the live defect shape (no --expected-base pinned): the implicit frozen
    expectation is "one coherent family = one base", and any divergence is foreign.
    """
    write_schema(
        tmp_path,
        "alpha.schema.json",
        id_value=f"{CLEAN_BASE}/alpha.schema.json",
    )
    write_schema(
        tmp_path,
        "beta.schema.json",
        id_value="https://example.invalid/rakl/beta.schema.json",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "SPLIT_NAMESPACE" in result.stdout
    assert "namespace_count: 2" in result.stdout


def test_foreign_base_against_expected_is_detected(tmp_path: Path) -> None:
    """With --expected-base pinned, a non-matching base is flagged FOREIGN_BASE."""
    write_schema(
        tmp_path,
        "alpha.schema.json",
        id_value=f"{CLEAN_BASE}/alpha.schema.json",
    )
    write_schema(
        tmp_path,
        "beta.schema.json",
        id_value="https://example.invalid/rakl/beta.schema.json",
    )
    result = run_checker(tmp_path, "--expected-base", CLEAN_BASE)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "FOREIGN_BASE" in result.stdout
    assert "beta.schema.json" in result.stdout


def test_filename_mismatch_world_is_detected(tmp_path: Path) -> None:
    """A $id whose filename component disagrees with the file basename is flagged."""
    write_schema(
        tmp_path,
        "alpha.schema.json",
        id_value=f"{CLEAN_BASE}/renamed-does-not-match.schema.json",
    )
    result = run_checker(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "FILENAME_MISMATCH" in result.stdout
    assert "alpha.schema.json" in result.stdout


@pytest.mark.xfail(
    strict=True,
    reason=(
        "issue #148: $id namespaces not yet unified — owner decision pending. "
        "The real schemas/ family is split across multiple bases; the checker "
        "correctly exits nonzero, so this 'assert pass' fails (XFAIL) until an "
        "owner picks one canonical base. When that happens the checker passes, "
        "this turns XPASS and the strict marker forces removing it."
    ),
)
def test_real_schemas_directory_is_unified() -> None:
    """The real schemas/ directory must ultimately pass the consistency checker.

    Until issue #148's owner decision lands, the family is split across bases, so
    the checker exits nonzero and this assertion fails — which is the expected
    XFAIL state. It documents the defect in the test suite without going red.
    """
    result = run_checker(REPO_ROOT)
    assert result.returncode == 0, (
        "schema $id consistency checker failed on real schemas/:\n"
        + result.stdout
        + result.stderr
    )
