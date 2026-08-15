"""Schema-integrity guard for the SQLite reference stores (HOSTILE_TEST_MATRIX H21).

The defect this closes: every engineering store ran ``CREATE TABLE IF NOT EXISTS``
on every open. A database that had lost a table -- a half-applied migration, a
botched restore, an operator ``DROP`` -- reopened without error, got the missing
table silently recreated EMPTY, and served the project head with a hole in its
ledger. ``HOSTILE_MATRIX_EXECUTION_V1.json`` H21 recorded exactly that:
``transitions`` dropped, store reopens, head served, receipt ``None``,
``PRAGMA user_version=0``.

The rule now:

* Each store registers itself, by component name, in one table
  ``engineering_schema_registry`` (component, schema_version, tables). Several
  stores legitimately share one database file (the atomic coordinator opens the
  state, semantic and evidence stores on one file), so the registry is
  per-component, not per-file.
* On open, if the component is registered, OR if any of its tables already
  exist, the database is *populated for this component* and is checked, never
  repaired: a missing table or a schema-version mismatch raises
  ``SchemaIntegrityError`` naming the component and the missing tables.
  ``CREATE TABLE IF NOT EXISTS`` is not executed over a populated database.
* Only a database with NONE of the component's tables is fresh; it is created
  and registered.
* A database created before this guard existed (all tables present, no registry
  row) is upgraded in place: verified, then registered. That is the only case
  where an unregistered-but-populated database is accepted, and it is accepted
  only when nothing is missing.

Indexes are not checked (a missing index is a performance fault, not a data
hole); tables are.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Sequence

REGISTRY_TABLE = "engineering_schema_registry"


class SchemaIntegrityError(RuntimeError):
    """The database is populated for this component and its schema is incomplete or mismatched.

    Raised on OPEN, before any table is created or any row is served. Carries the
    component name and the exact missing tables so an operator can tell a
    half-applied migration from a generic error.
    """

    def __init__(self, component: str, *, missing_tables: Sequence[str] = (),
                 stored_version: str | None = None, expected_version: str | None = None) -> None:
        self.component = component
        self.missing_tables = tuple(missing_tables)
        self.stored_version = stored_version
        self.expected_version = expected_version
        parts = [f"schema integrity failure for {component!r}"]
        if self.missing_tables:
            parts.append(f"missing tables: {', '.join(self.missing_tables)}")
        if stored_version is not None and expected_version is not None and stored_version != expected_version:
            parts.append(f"stored schema_version {stored_version!r} != expected {expected_version!r}")
        parts.append("the database is populated and will not be silently repaired; migrate or restore it")
        super().__init__("; ".join(parts))


def _existing_tables(db: sqlite3.Connection) -> set[str]:
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def guard_and_initialize_schema(
    db: sqlite3.Connection,
    *,
    component: str,
    schema_version: str,
    tables: Sequence[str],
    create_script: str,
) -> str:
    """Verify-or-create the component's schema on ``db``. Returns one of
    ``"CREATED"``, ``"VERIFIED"``, ``"UPGRADED_REGISTRY"``.

    ``create_script`` is the store's existing ``CREATE TABLE IF NOT EXISTS ...``
    script; it is executed ONLY when the database is fresh for this component.
    """

    expected = tuple(tables)
    if not expected:
        raise ValueError("a component must declare at least one table")
    db.execute(
        f"CREATE TABLE IF NOT EXISTS {REGISTRY_TABLE} ("
        " component TEXT PRIMARY KEY,"
        " schema_version TEXT NOT NULL,"
        " tables_json TEXT NOT NULL)"
    )
    row = db.execute(
        f"SELECT schema_version FROM {REGISTRY_TABLE} WHERE component=?", (component,)
    ).fetchone()
    present = _existing_tables(db)
    missing = [t for t in expected if t not in present]

    try:
        return _guard(db, component=component, schema_version=schema_version, expected=expected,
                      missing=missing, row=row, create_script=create_script)
    finally:
        if db.in_transaction:
            db.commit()


def _guard(db, *, component, schema_version, expected, missing, row, create_script) -> str:
    if row is not None:
        stored_version = row[0]
        if missing or stored_version != schema_version:
            raise SchemaIntegrityError(component, missing_tables=missing,
                                       stored_version=stored_version, expected_version=schema_version)
        return "VERIFIED"

    # unregistered: fresh, pre-guard, or partial
    if len(missing) == len(expected):
        db.executescript(create_script)
        db.execute(
            f"INSERT OR IGNORE INTO {REGISTRY_TABLE}(component,schema_version,tables_json) VALUES(?,?,?)",
            (component, schema_version, json.dumps(list(expected))),
        )
        return "CREATED"
    if missing:
        raise SchemaIntegrityError(component, missing_tables=missing, expected_version=schema_version)
    # every table present, no registry row: a database from before the guard existed
    db.execute(
        f"INSERT OR IGNORE INTO {REGISTRY_TABLE}(component,schema_version,tables_json) VALUES(?,?,?)",
        (component, schema_version, json.dumps(list(expected))),
    )
    return "UPGRADED_REGISTRY"


__all__ = ["REGISTRY_TABLE", "SchemaIntegrityError", "guard_and_initialize_schema"]
