"""Validate the issue-#137 terminology auditor on planted worlds.

The auditor's own correctness is what the inventory report rests on, so it is
exercised against a synthetic repository with known-by-construction counts rather
than only against the live tree. Both the alarm case (terms present, counted at the
right surface) and the no-alarm case (clean file yields zero) are asserted.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
AUDITOR = REPO_ROOT / "scripts" / "audit_terminology_inventory.py"


def _load_auditor():
    spec = importlib.util.spec_from_file_location("audit_terminology_inventory", AUDITOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


auditor = _load_auditor()


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(
        ["git", *argv],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    )


@pytest.fixture()
def planted_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "planted"
    (repo / "docs").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "archive").mkdir()
    (repo / "schemas").mkdir()

    # Alarm world: two misleading global-structure phrases on a live reader surface.
    (repo / "docs" / "overview.md").write_text(
        "The global lattice is not one order-theoretic object.\n"
        "A knowledge lattice is only a local view.\n",
        encoding="utf-8",
    )
    # Justified world: the specialized failure contract, which must NOT be counted
    # as a misleading global-structure phrase. Two files exercise both alternation
    # branches of the pattern (CamelCase symbol and snake_case module reference).
    (repo / "src" / "failure_lattice.py").write_text(
        "class FailureLattice:\n    pass\n", encoding="utf-8"
    )
    (repo / "docs" / "failures.md").write_text(
        "See `failure_lattice` and the failure-lattice contract.\n", encoding="utf-8"
    )
    # Immutable world: same phrase inside a frozen archive artifact.
    (repo / "archive" / "frozen.md").write_text(
        "The global lattice wording was correct for that frozen version.\n",
        encoding="utf-8",
    )
    # No-alarm world: a clean file containing none of the tracked vocabulary.
    (repo / "docs" / "clean.md").write_text(
        "This document discusses evidence, fibres and verification only.\n",
        encoding="utf-8",
    )
    (repo / "schemas" / "thing.schema.json").write_text(
        '{"$id": "https://github.com/SzeChunYiu/RAKL/schemas/thing.schema.json"}\n', encoding="utf-8"
    )

    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "planted")
    return repo


def test_classify_maps_paths_to_expected_surfaces() -> None:
    assert auditor.classify("src/rakl/core.py") == "src (executable)"
    assert auditor.classify("archive/old.md") == "archive (immutable)"
    assert auditor.classify("research/x.json") == "research (archive)"
    assert auditor.classify("publication/papers/a/main.tex") == "papers/publication"
    assert auditor.classify("README.md") == "root/other"


def test_misleading_phrases_are_counted_at_the_right_surface(planted_repo: Path) -> None:
    report = auditor.measure(
        planted_repo,
        {"misleading": auditor.MISLEADING_GLOBAL_STRUCTURE},
    )
    rows = report["groups"]["misleading"]

    # Alarm case: both planted phrases found, with the archive occurrence separated out.
    assert rows["global lattice"]["total"] == 2
    assert rows["global lattice"]["by_surface"] == {
        "archive (immutable)": 1,
        "docs": 1,
    }
    assert rows["global lattice"]["immutable_share"] == 1
    assert rows["knowledge lattice"]["total"] == 1

    # No-alarm case: phrases that were not planted must report exactly zero,
    # not a missing key and not a nonzero smear from a near-miss match.
    assert rows["meta-lattice"]["total"] == 0
    assert rows["lattice path"]["total"] == 0


def test_failure_lattice_is_not_counted_as_misleading(planted_repo: Path) -> None:
    """The specialized FailureLattice contract is legitimate and must stay separate."""

    report = auditor.measure(
        planted_repo,
        {
            "misleading": auditor.MISLEADING_GLOBAL_STRUCTURE,
            "justified": auditor.JUSTIFIED_OR_BRAND,
        },
    )
    justified = report["groups"]["justified"]
    misleading = report["groups"]["misleading"]

    # Counts are over file CONTENT, not paths: the CamelCase symbol in src/ plus the
    # snake_case and hyphenated references in docs/ give three content occurrences.
    assert justified["failure lattice"]["total"] == 3
    assert justified["failure lattice"]["by_surface"] == {
        "docs": 2,
        "src (executable)": 1,
    }
    # None of the misleading rows may absorb the failure-lattice occurrences.
    assert misleading["knowledge lattice"]["by_surface"].get("src (executable)") is None
    assert misleading["global lattice"]["by_surface"].get("src (executable)") is None


def test_rename_blast_radius_reports_schema_namespaces(planted_repo: Path) -> None:
    radius = auditor.rename_blast_radius(planted_repo)
    assert radius["schema_count"] == 1
    assert radius["schema_id_namespaces"] == {"https://github.com/SzeChunYiu/RAKL/schemas": 1}
    assert radius["python_files_importing_rakl"] == 0


def test_auditor_runs_against_the_live_tree() -> None:
    """The tool must execute on the real repository without raising."""

    completed = subprocess.run(
        [sys.executable, str(AUDITOR), "--repo", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "mathematically_misleading_global_structure" in completed.stdout
    assert "rename blast radius" in completed.stdout


def test_auditor_selects_no_name_and_claims_no_authority() -> None:
    """Guard the claim boundary: this tool must never become a decision surface."""

    text = AUDITOR.read_text(encoding="utf-8")
    assert "measurement tool only" in text.lower()
    report_doc = REPO_ROOT / "docs" / "TERMINOLOGY_RENAME_INVENTORY_V1.md"
    body = report_doc.read_text(encoding="utf-8")
    assert "NO_NAME_SELECTED" in body
    assert "NO_DESTRUCTIVE_RENAME" in body
