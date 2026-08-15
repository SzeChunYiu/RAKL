"""Mechanical conformance resolvers: does a *named* specified thing exist in code?

The ORION engineering packet names modules, classes, dataclass fields, enum
members, HTTP routes, database tables and hostile-matrix cases. This module
answers, for each named thing, one question only:

    does the code actually contain the thing the document named?

It deliberately does NOT decide whether a fibre's falsifier is defeated. Those
are two different axes and merging them is how "closed" stops meaning anything:

  Axis A -- falsifier closure   (a semantic property, established by tests)
  Axis B -- named-surface conformance (this module, established by import)

Resolution is by ``importlib`` + ``getattr`` + ``dataclasses.fields`` +
behavioural invocation. Never by grepping a string out of a document.

Verdicts
--------
PRESENT       the named thing resolved
ABSENT        the lookup ran and the thing was not there
PARTIAL       the thing resolved but only some of its named parts did
CANNOT_CHECK  the lookup could not be performed (import error, missing dep,
              instantiation failure). This is *not* ABSENT and it is *not* fine.
"""

from __future__ import annotations

import dataclasses
import importlib
import sqlite3
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

PRESENT = "PRESENT"
ABSENT = "ABSENT"
PARTIAL = "PARTIAL"
CANNOT_CHECK = "CANNOT_CHECK"

VERDICTS = (PRESENT, ABSENT, PARTIAL, CANNOT_CHECK)


@dataclasses.dataclass(frozen=True)
class Finding:
    """One specified item, resolved."""

    item_id: str
    spec_source: str
    kind: str
    specified: str
    verdict: str
    evidence: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"{self.verdict!r} is not a conformance verdict")

    def to_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


# --- primitive resolvers ---------------------------------------------------


def _import(module: str) -> tuple[Any | None, str | None]:
    """Import, distinguishing 'not there' from 'could not check'.

    A ModuleNotFoundError naming *this* module is absence. Anything else --
    a missing third-party dependency, a syntax error, an import-time raise --
    is CANNOT_CHECK, because the question was never actually answered.
    """
    try:
        return importlib.import_module(module), None
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) == module:
            return None, f"ABSENT:{exc}"
        return None, f"CANNOT_CHECK:ModuleNotFoundError: {exc}"
    except Exception as exc:  # noqa: BLE001 -- any import-time failure is uncheckable
        return None, f"CANNOT_CHECK:{type(exc).__name__}: {exc}"


def _resolve_attr(module: str, dotted: str) -> tuple[Any | None, str]:
    mod, err = _import(module)
    if mod is None:
        return None, err or f"CANNOT_CHECK:unknown import failure for {module}"
    obj: Any = mod
    walked = module
    for part in dotted.split("."):
        if not hasattr(obj, part):
            return None, f"ABSENT:{walked} has no attribute {part!r}"
        obj = getattr(obj, part)
        walked = f"{walked}.{part}"
    return obj, f"PRESENT:{walked}"


def check_module(item_id: str, spec_source: str, module: str) -> Finding:
    mod, err = _import(module)
    if mod is not None:
        return Finding(item_id, spec_source, "module", module, PRESENT, getattr(mod, "__file__", module))
    verdict = ABSENT if (err or "").startswith("ABSENT") else CANNOT_CHECK
    return Finding(item_id, spec_source, "module", module, verdict, "-", (err or "").split(":", 1)[-1])


def check_attr(item_id: str, spec_source: str, module: str, dotted: str) -> Finding:
    obj, note = _resolve_attr(module, dotted)
    spec = f"{module}.{dotted}"
    if note.startswith("PRESENT"):
        return Finding(item_id, spec_source, "attr", spec, PRESENT, note.split(":", 1)[1])
    verdict = ABSENT if note.startswith("ABSENT") else CANNOT_CHECK
    return Finding(item_id, spec_source, "attr", spec, verdict, "-", note.split(":", 1)[1])


def check_fields(item_id: str, spec_source: str, module: str, cls_name: str,
                 required: Sequence[str]) -> Finding:
    """Dataclass field membership. A class attribute is not accepted as proof."""
    cls, note = _resolve_attr(module, cls_name)
    spec = f"{module}.{cls_name}({','.join(required)})"
    if cls is None:
        verdict = ABSENT if note.startswith("ABSENT") else CANNOT_CHECK
        return Finding(item_id, spec_source, "field", spec, verdict, "-", note.split(":", 1)[1])
    if not dataclasses.is_dataclass(cls):
        return Finding(item_id, spec_source, "field", spec, CANNOT_CHECK, f"{module}.{cls_name}",
                       "not a dataclass; field membership is not decidable this way")
    have = {f.name for f in dataclasses.fields(cls)}
    missing = [f for f in required if f not in have]
    if not missing:
        return Finding(item_id, spec_source, "field", spec, PRESENT, f"{module}.{cls_name}",
                       f"all {len(required)} fields present")
    verdict = ABSENT if len(missing) == len(required) else PARTIAL
    return Finding(item_id, spec_source, "field", spec, verdict, f"{module}.{cls_name}",
                   f"missing: {','.join(missing)}")


def check_enum_members(item_id: str, spec_source: str, module: str, cls_name: str,
                       required: Sequence[str]) -> Finding:
    cls, note = _resolve_attr(module, cls_name)
    spec = f"{module}.{cls_name}[{','.join(required)}]"
    if cls is None:
        verdict = ABSENT if note.startswith("ABSENT") else CANNOT_CHECK
        return Finding(item_id, spec_source, "enum_member", spec, verdict, "-", note.split(":", 1)[1])
    if not (isinstance(cls, type) and issubclass(cls, Enum)):
        return Finding(item_id, spec_source, "enum_member", spec, CANNOT_CHECK, f"{module}.{cls_name}",
                       "not an Enum")
    have = {m.name for m in cls} | {str(m.value) for m in cls}
    missing = [m for m in required if m not in have]
    if not missing:
        return Finding(item_id, spec_source, "enum_member", spec, PRESENT, f"{module}.{cls_name}",
                       f"all {len(required)} members present")
    verdict = ABSENT if len(missing) == len(required) else PARTIAL
    return Finding(item_id, spec_source, "enum_member", spec, verdict, f"{module}.{cls_name}",
                   f"missing: {','.join(missing)}")


def check_methods(item_id: str, spec_source: str, module: str, cls_name: str,
                  required: Sequence[str]) -> Finding:
    cls, note = _resolve_attr(module, cls_name)
    spec = f"{module}.{cls_name}.{{{','.join(required)}}}"
    if cls is None:
        verdict = ABSENT if note.startswith("ABSENT") else CANNOT_CHECK
        return Finding(item_id, spec_source, "method", spec, verdict, "-", note.split(":", 1)[1])
    missing = [m for m in required if not callable(getattr(cls, m, None))]
    if not missing:
        return Finding(item_id, spec_source, "method", spec, PRESENT, f"{module}.{cls_name}",
                       f"all {len(required)} methods present")
    verdict = ABSENT if len(missing) == len(required) else PARTIAL
    return Finding(item_id, spec_source, "method", spec, verdict, f"{module}.{cls_name}",
                   f"missing: {','.join(missing)}")


def check_sqlite_tables(item_id: str, spec_source: str, module: str, cls_name: str,
                        required: Sequence[str]) -> Finding:
    """Instantiate the store into a temp dir and read sqlite_master.

    Grepping for CREATE TABLE would accept a commented-out statement; this does
    not.
    """
    cls, note = _resolve_attr(module, cls_name)
    spec = f"{module}.{cls_name} tables[{','.join(required)}]"
    if cls is None:
        verdict = ABSENT if note.startswith("ABSENT") else CANNOT_CHECK
        return Finding(item_id, spec_source, "table", spec, verdict, "-", note.split(":", 1)[1])
    try:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "probe.db"
            cls(path)
            con = sqlite3.connect(path)
            try:
                have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            finally:
                con.close()
    except Exception as exc:  # noqa: BLE001
        return Finding(item_id, spec_source, "table", spec, CANNOT_CHECK, f"{module}.{cls_name}",
                       f"could not instantiate: {type(exc).__name__}: {exc}")
    missing = [t for t in required if t not in have]
    if not missing:
        return Finding(item_id, spec_source, "table", spec, PRESENT, f"{module}.{cls_name}",
                       f"tables: {','.join(sorted(have))}")
    verdict = ABSENT if len(missing) == len(required) else PARTIAL
    return Finding(item_id, spec_source, "table", spec, verdict, f"{module}.{cls_name}",
                   f"missing: {','.join(missing)}; present: {','.join(sorted(have))}")


def check_behavioural(item_id: str, spec_source: str, specified: str,
                      probe: Callable[[], tuple[str, str, str]]) -> Finding:
    """Run a probe returning (verdict, evidence, detail). Any raise is CANNOT_CHECK."""
    try:
        verdict, evidence, detail = probe()
    except Exception as exc:  # noqa: BLE001
        return Finding(item_id, spec_source, "behaviour", specified, CANNOT_CHECK, "-",
                       f"probe raised {type(exc).__name__}: {exc}")
    return Finding(item_id, spec_source, "behaviour", specified, verdict, evidence, detail)


def summarize(findings: Sequence[Finding]) -> Mapping[str, int]:
    out = {v: 0 for v in VERDICTS}
    for f in findings:
        out[f.verdict] += 1
    return out


__all__ = [
    "ABSENT", "CANNOT_CHECK", "Finding", "PARTIAL", "PRESENT", "VERDICTS",
    "check_attr", "check_behavioural", "check_enum_members", "check_fields",
    "check_methods", "check_module", "check_sqlite_tables", "summarize",
]
