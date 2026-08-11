"""Planted worlds for the #134 authority/chronology triad checker.

The inventory auditor in ``test_artifact_contract_coverage.py`` needs caller
observations.  This suite freezes the *repo-structure* checker: schema file,
declared hash identity field(s), owner module, and at least one test marker.
Missing any leg fails closed and blocks promotion credit.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.artifact_contract_coverage import (
    ARTIFACT_CONTRACT_COVERAGE_CHECK_NAME,
    AuthorityChronologyArtifactFamily,
    DEFAULT_AUTHORITY_CHRONOLOGY_FAMILIES,
    TriadCoverageVerdict,
    TriadLegStatus,
    assess_artifact_family_triad,
    check_authority_chronology_triads,
    main,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _family(**overrides: object) -> AuthorityChronologyArtifactFamily:
    values: dict[str, object] = {
        "artifact_type": "planted_family",
        "schema_filename": "planted-family.schema.json",
        "owner_module": "rakl.planted_family",
        "required_hash_fields": ("artifact_hash",),
        "test_markers": ("planted_family_marker",),
    }
    values.update(overrides)
    return AuthorityChronologyArtifactFamily(**values)  # type: ignore[arg-type]


def _write_schema(repo: Path, filename: str, hash_fields: tuple[str, ...]) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {field: {"type": "string"} for field in hash_fields},
        "required": list(hash_fields),
    }
    (repo / "schemas").mkdir(parents=True, exist_ok=True)
    (repo / "schemas" / filename).write_text(
        json.dumps(schema, indent=2) + "\n", encoding="utf-8"
    )


def _write_owner(repo: Path, module: str = "rakl.planted_family") -> None:
    path = repo / "src" / Path(*module.split(".")).with_suffix(".py")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('"""planted owner module"""\n', encoding="utf-8")


def _write_test(repo: Path, marker: str = "planted_family_marker") -> None:
    tests = repo / "tests"
    tests.mkdir(parents=True, exist_ok=True)
    (tests / "test_planted_family.py").write_text(
        f'"""planted"""\n\ndef test_marker() -> None:\n    assert "{marker}"\n',
        encoding="utf-8",
    )


def _complete_repo(tmp_path: Path) -> Path:
    _write_schema(tmp_path, "planted-family.schema.json", ("artifact_hash",))
    _write_owner(tmp_path)
    _write_test(tmp_path)
    return tmp_path


def test_complete_triad_permits_promotion_credit(tmp_path: Path) -> None:
    repo = _complete_repo(tmp_path)
    report = check_authority_chronology_triads(
        repo_root=repo, families=(_family(),)
    )
    assert report.verdict is TriadCoverageVerdict.ALL_TRIADS_SATISFIED
    assert report.permits_promotion_credit is True
    assert report.findings[0].status is TriadLegStatus.TRIAD_SATISFIED


def test_missing_schema_fails_closed(tmp_path: Path) -> None:
    _write_owner(tmp_path)
    _write_test(tmp_path)
    report = check_authority_chronology_triads(
        repo_root=tmp_path, families=(_family(),)
    )
    assert report.verdict is TriadCoverageVerdict.TRIAD_INCOMPLETE
    assert report.permits_promotion_credit is False
    assert report.findings[0].status is TriadLegStatus.SCHEMA_MISSING
    assert "SCHEMA_MISSING:planted_family" in report.reasons


def test_missing_hash_field_fails_closed(tmp_path: Path) -> None:
    _write_schema(tmp_path, "planted-family.schema.json", ("unrelated_field",))
    _write_owner(tmp_path)
    _write_test(tmp_path)
    report = check_authority_chronology_triads(
        repo_root=tmp_path, families=(_family(),)
    )
    assert report.permits_promotion_credit is False
    assert report.findings[0].status is TriadLegStatus.HASH_FIELD_MISSING
    assert "hash_field_missing:artifact_hash" in report.findings[0].reasons


def test_nested_hash_field_counts_as_present(tmp_path: Path) -> None:
    schema = {
        "type": "object",
        "properties": {
            "entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"artifact_hash": {"type": "string"}},
                    "required": ["artifact_hash"],
                },
            }
        },
    }
    (tmp_path / "schemas").mkdir(parents=True)
    (tmp_path / "schemas" / "planted-family.schema.json").write_text(
        json.dumps(schema), encoding="utf-8"
    )
    _write_owner(tmp_path)
    _write_test(tmp_path)
    finding = assess_artifact_family_triad(_family(), repo_root=tmp_path)
    assert finding.status is TriadLegStatus.TRIAD_SATISFIED


def test_missing_owner_module_fails_closed(tmp_path: Path) -> None:
    _write_schema(tmp_path, "planted-family.schema.json", ("artifact_hash",))
    _write_test(tmp_path)
    report = check_authority_chronology_triads(
        repo_root=tmp_path, families=(_family(),)
    )
    assert report.permits_promotion_credit is False
    assert report.findings[0].status is TriadLegStatus.OWNER_MODULE_MISSING


def test_missing_test_coverage_fails_closed(tmp_path: Path) -> None:
    _write_schema(tmp_path, "planted-family.schema.json", ("artifact_hash",))
    _write_owner(tmp_path)
    (tmp_path / "tests").mkdir(parents=True)
    (tmp_path / "tests" / "test_unrelated.py").write_text(
        "def test_ok() -> None:\n    assert True\n", encoding="utf-8"
    )
    report = check_authority_chronology_triads(
        repo_root=tmp_path, families=(_family(),)
    )
    assert report.permits_promotion_credit is False
    assert report.findings[0].status is TriadLegStatus.TEST_COVERAGE_MISSING


def test_empty_registry_fails_closed(tmp_path: Path) -> None:
    report = check_authority_chronology_triads(repo_root=tmp_path, families=())
    assert report.verdict is TriadCoverageVerdict.REGISTRY_EMPTY
    assert report.permits_promotion_credit is False


def test_live_repo_default_registry_is_complete() -> None:
    report = check_authority_chronology_triads(repo_root=REPO_ROOT)
    assert report.verdict is TriadCoverageVerdict.ALL_TRIADS_SATISFIED, report.reasons
    assert report.permits_promotion_credit is True
    assert len(report.findings) == len(DEFAULT_AUTHORITY_CHRONOLOGY_FAMILIES)
    assert report.to_dict()["check_name"] == ARTIFACT_CONTRACT_COVERAGE_CHECK_NAME
    assert report.to_dict()["grants_framework_authority"] is False


def test_cli_exits_nonzero_on_incomplete_triad(tmp_path: Path) -> None:
    _write_owner(tmp_path)
    assert main(["--repo", str(tmp_path)]) == 1


def test_cli_exits_zero_on_live_repo(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    assert main(["--repo", str(REPO_ROOT), "--json", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["verdict"] == "ALL_TRIADS_SATISFIED"
    assert payload["permits_promotion_credit"] is True


def test_family_construction_rejects_empty_hash_fields() -> None:
    with pytest.raises(ValueError, match="hash field"):
        _family(required_hash_fields=())
