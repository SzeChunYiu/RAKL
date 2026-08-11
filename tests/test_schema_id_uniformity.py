"""Regression guard for schema ``$id`` uniformity (issue #148).

Every schema in ``schemas/`` must carry a ``$id``, all ``$id`` values must
share the frozen canonical base URI, and the filename component of each ``$id``
must match the file's own basename.

Canonical base (owner decision recorded while closing #148):

    https://github.com/SzeChunYiu/RAKL/schemas/

Chosen because it was already the majority namespace (59/96), is the only
non-placeholder base pointing at this repository, and is what validators already
resolve by path. Placeholder domains ``example.invalid`` / ``rakl.example`` and
the uncontrolled ``rakl.dev`` domain are retired for new and existing schema
definitions under ``schemas/``.

Planted worlds exercise the guard's ability to discriminate: missing ``$id``,
foreign base, filename disagreement, and a clean control that must not fire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
CANONICAL_BASE = "https://github.com/SzeChunYiu/RAKL/schemas/"


def _schema_files() -> list[Path]:
    """Return sorted real schema files under ``schemas/``."""
    paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    assert len(paths) > 0, f"no schema files found in {SCHEMA_DIR}"
    return paths


def _base_of(raw_id: str) -> str:
    """Return the URI directory base of a schema ``$id``."""
    if "/" in raw_id:
        return raw_id[: raw_id.rindex("/") + 1]
    return raw_id


# ---------------------------------------------------------------------------
# Real-schema checks
# ---------------------------------------------------------------------------


def test_every_schema_carries_an_id() -> None:
    """Every schema file declares a ``$id``.

    Regression anchor: if a new schema is added without ``$id`` this test
    catches it.
    """
    missing: list[str] = []
    for path in _schema_files():
        doc = json.loads(path.read_text())
        if not doc.get("$id"):
            missing.append(path.name)
    assert not missing, f"schemas missing $id: {missing}"


def test_all_ids_share_one_base() -> None:
    """All ``$id`` values share the frozen canonical GitHub schemas base.

Currently passes: all 96 schemas declare ``$id`` under the single
    canonical base ``https://github.com/SzeChunYiu/RAKL/schemas/``
    (owner decision made in issue #148; previously split across four
    namespaces).  Regression anchor: any new schema with a foreign base
    fails this test.
    """
    bases: dict[str, int] = {}
    foreign: list[str] = []
    for path in _schema_files():
        doc = json.loads(path.read_text())
        raw_id: str = doc.get("$id", "")
        base = _base_of(raw_id)
        bases[base] = bases.get(base, 0) + 1
        if base != CANONICAL_BASE:
            foreign.append(f"{path.name}: {raw_id}")
    assert len(bases) == 1, (
        f"expected 1 canonical $id base, found {len(bases)}: "
        + ", ".join(f"{n}×{b!r}" for b, n in sorted(bases.items(), key=lambda x: -x[1]))
    )
    assert not foreign, (
        f"schemas not using frozen canonical base {CANONICAL_BASE!r}:\n"
        + "\n".join(foreign)
    )
    assert next(iter(bases)) == CANONICAL_BASE


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


def test_every_id_equals_canonical_base_plus_basename() -> None:
    """Each ``$id`` is exactly ``CANONICAL_BASE`` + filename."""
    bad: list[str] = []
    for path in _schema_files():
        doc = json.loads(path.read_text())
        expected = CANONICAL_BASE + path.name
        raw_id = doc.get("$id", "")
        if raw_id != expected:
            bad.append(f"{path.name}: {raw_id!r} != {expected!r}")
    assert not bad, "schemas with non-canonical exact $id:\n" + "\n".join(bad)


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

    base = _base_of(raw_id)
    id_filename = raw_id.rpartition("/")[2] or raw_id
    filename_match = id_filename == path.name
    uses_canonical_base = base == CANONICAL_BASE

    return {
        "has_id": has_id,
        "has_any_base": bool(base),
        "filename_matches": filename_match,
        "uses_canonical_base": uses_canonical_base,
    }


class TestPlantedWorlds:
    """Planted worlds that should and should not fire the guard."""

    def test_clean_control(self, tmp_path: Path) -> None:
        """A well-formed schema on the canonical base must not fire any check."""
        result = _probe(
            tmp_path,
            "clean-control.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": CANONICAL_BASE + "clean-control.schema.json",
            },
        )
        assert result["has_id"], "clean control must have $id"
        assert result["has_any_base"], "clean control must have a base"
        assert result["filename_matches"], "clean control filename must match"
        assert result["uses_canonical_base"], "clean control must use canonical base"

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
        assert not result["uses_canonical_base"], "foreign base must be detected"

    def test_retired_placeholder_base(self, tmp_path: Path) -> None:
        """Retired placeholder bases must not count as canonical."""
        for foreign in (
            "https://example.invalid/rakl/retired.schema.json",
            "https://rakl.dev/schemas/retired.schema.json",
            "https://rakl.example/schemas/retired.schema.json",
        ):
            result = _probe(
                tmp_path,
                "retired.schema.json",
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": foreign,
                },
            )
            assert result["has_id"]
            assert result["filename_matches"]
            assert not result["uses_canonical_base"], foreign

    def test_filename_disagreement(self, tmp_path: Path) -> None:
        """A schema whose ``$id`` filename component differs from its path."""
        result = _probe(
            tmp_path,
            "disagree.schema.json",
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": CANONICAL_BASE + "wrong-name.schema.json",
            },
        )
        assert result["has_id"], "filename-disagree schema has $id"
        assert result["has_any_base"], "filename-disagree schema has a base"
        assert result["uses_canonical_base"], "base is canonical"
        assert not result["filename_matches"], "filename disagreement must be detected"
