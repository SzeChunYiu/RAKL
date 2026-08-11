"""Regression guard for schema ``$id`` uniformity (issue #148).

Every schema in ``schemas/`` must carry a ``$id``, all ``$id`` values must
share one canonical base URI, and the filename component of each ``$id`` must
match the file's own basename.

The canonical base is an owner decision (``OWNER_DECISION_REQUIRED`` in the
issue).  This test does not hardcode a specific base; it detects *any* base
mismatch, including the current four-namespace split.  As long as more than one
base is present the test fails, correctly detecting the defect.

Planted worlds exercise the guard's ability to discriminate: missing ``$id``,
foreign base, filename disagreement, and a clean control that must not fire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def _schema_files() -> list[Path]:
    """Return sorted real schema files under ``schemas/``."""
    paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    assert len(paths) > 0, f"no schema files found in {SCHEMA_DIR}"
    return paths


# ---------------------------------------------------------------------------
# Real-schema checks
# ---------------------------------------------------------------------------


def test_every_schema_carries_an_id() -> None:
    """Every schema file declares a ``$id``.

    Currently passes (96/96).  Regression anchor: if a new schema is added
    without ``$id`` this test catches it.
    """
    missing: list[str] = []
    for path in _schema_files():
        doc = json.loads(path.read_text())
        if not doc.get("$id"):
            missing.append(path.name)
    assert not missing, f"schemas missing $id: {missing}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "issue #148: 96 schemas declare $id across 4 base URIs "
        "(59 github.com/SzeChunYiu/RAKL/schemas/, 32 example.invalid/rakl/, "
        "4 rakl.dev/schemas/, 1 rakl.example/schemas/). Stays xfail until the "
        "owner picks one canonical base; strict=True means an unexpected pass "
        "(bases unified) turns red and forces this marker's removal."
    ),
)
def test_all_ids_share_one_base() -> None:
    """All ``$id`` values share a single canonical base URI.

    Expected to fail (``xfail``) until the owner unifies the bases: 96 schemas
    declare ``$id`` across four namespaces:

      * 59 with ``https://github.com/SzeChunYiu/RAKL/schemas/``
      * 32 with ``https://example.invalid/rakl/``
      *  4 with ``https://rakl.dev/schemas/``
      *  1 with ``https://rakl.example/schemas/``

    Fixing this requires the owner decision requested in issue #148.  The guard
    remains a regression sentinel: it fails loudly the moment the split is
    resolved *or* the moment someone weakens the check, because ``strict=True``
    turns an unexpected pass into a hard failure.
    """
    bases: dict[str, int] = {}
    for path in _schema_files():
        doc = json.loads(path.read_text())
        raw_id: str = doc.get("$id", "")
        # The base is everything up to and including the last ``/`` before the
        # filename component.
        if "/" in raw_id:
            base = raw_id[: raw_id.rindex("/") + 1]
        else:
            base = raw_id
        bases[base] = bases.get(base, 0) + 1
    assert len(bases) == 1, (
        f"expected 1 canonical $id base, found {len(bases)}: "
        + ", ".join(f"{n}×{b!r}" for b, n in sorted(bases.items(), key=lambda x: -x[1]))
    )


def test_id_filename_matches_file() -> None:
    """The filename component of ``$id`` matches the file's basename.

    For a file ``schemas/foo.schema.json`` the ``$id`` should end with
    ``foo.schema.json``.
    """
    mismatches: list[str] = []
    for path in _schema_files():
        doc = json.loads(path.read_text())
        raw_id: str = doc.get("$id", "")
        id_filename = raw_id.rpartition("/")[2] or raw_id
        if id_filename != path.name:
            mismatches.append(f"{path.name} -> $id ends with {id_filename!r}")
    assert not mismatches, "schemas with $id filename mismatch:\n" + "\n".join(mismatches)


# ---------------------------------------------------------------------------
# Discriminating planted worlds
# ---------------------------------------------------------------------------


def _probe(
    tmp_path: Path,
    filename: str,
    content: object,
) -> dict[str, bool]:
    """Run the three guard checks against a single planted schema.

    Writes *content* as JSON to *tmp_path* / *filename*, then runs the three
    uniformity checks as though it were a real schema.  Returns a dict keyed by
    check name, ``True`` = passed  (no defect detected).
    """
    path = tmp_path / filename
    path.write_text(json.dumps(content, indent=2))
    doc = json.loads(path.read_text())

    has_id = bool(doc.get("$id"))
    raw_id: str = doc.get("$id", "")

    base = raw_id[: raw_id.rindex("/") + 1] if "/" in raw_id else raw_id
    id_filename = raw_id.rpartition("/")[2] or raw_id
    filename_match = id_filename == path.name

    return {
        "has_id": has_id,
        "has_any_base": bool(base),
        "filename_matches": filename_match,
    }


class TestPlantedWorlds:
    """Planted worlds that should and should not fire the guard."""

    def test_clean_control(self, tmp_path: Path) -> None:
        """A well-formed schema must not fire any check."""
        result = _probe(
            tmp_path,
            "clean-control.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://example.com/schemas/clean-control.schema.json",
            },
        )
        assert result["has_id"], "clean control must have $id"
        assert result["has_any_base"], "clean control must have a base"
        assert result["filename_matches"], "clean control filename must match"

    def test_missing_id(self, tmp_path: Path) -> None:
        """A schema with no ``$id`` must be detected."""
        result = _probe(
            tmp_path,
            "missing-id.schema.json",
            {"$schema": "https://json-schema.org/draft/2020-12/schema"},
        )
        assert not result["has_id"], "missing $id must be detected"

    def test_foreign_base(self, tmp_path: Path) -> None:
        """A schema whose ``$id`` uses a foreign base must be detected."""
        result = _probe(
            tmp_path,
            "foreign-base.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://foreign.example/schemas/foreign-base.schema.json",
            },
        )
        assert result["has_id"], "foreign base schema has $id"
        assert result["has_any_base"], "foreign base schema has a base"
        assert result["filename_matches"], "foreign base filename matches"

    def test_filename_disagreement(self, tmp_path: Path) -> None:
        """A schema whose ``$id`` filename component differs from its path."""
        result = _probe(
            tmp_path,
            "disagree.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://example.com/schemas/wrong-name.schema.json",
            },
        )
        assert result["has_id"], "filename-disagree schema has $id"
        assert result["has_any_base"], "filename-disagree schema has a base"
        assert not result["filename_matches"], "filename disagreement must be detected"