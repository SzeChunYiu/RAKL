from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


_NUMERIC = re.compile(r"^META_N(?P<slot>\d{3,})_[A-Z0-9_]+$")
_MARKDOWN = re.compile(r"`(META_N\d{3,}_[A-Z0-9_]+)`")
_ROUND = re.compile(r"_(?P<round>\d{3})(?P<suffix>[A-Z]?)(?:_|\.)")


class HistoricalLedgerVerdict(str, Enum):
    CONSISTENT = "CONSISTENT"
    CONSISTENT_WITH_RECONCILIATION_HISTORY = "CONSISTENT_WITH_RECONCILIATION_HISTORY"
    CONFLICTED = "CONFLICTED"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


class HistoricalIssueKind(str, Enum):
    INVALID_JSON = "INVALID_JSON"
    SOURCE_MISSING = "SOURCE_MISSING"
    SOURCE_BLOB_MISMATCH = "SOURCE_BLOB_MISMATCH"
    UNCLASSIFIED_FIBER_RECORD = "UNCLASSIFIED_FIBER_RECORD"
    NAMESPACE_SLOT_COLLISION = "NAMESPACE_SLOT_COLLISION"
    CANONICAL_SLOT_COLLISION = "CANONICAL_SLOT_COLLISION"
    DEFINITION_CONFLICT = "DEFINITION_CONFLICT"
    ORPHAN_REFERENCE = "ORPHAN_REFERENCE"
    RECONCILIATION_SCOPE_UNVERIFIABLE = "RECONCILIATION_SCOPE_UNVERIFIABLE"
    RECONCILIATION_TARGET_ORPHAN = "RECONCILIATION_TARGET_ORPHAN"
    RECONCILIATION_CHRONOLOGY_INVALID = "RECONCILIATION_CHRONOLOGY_INVALID"


class FiberEventRole(str, Enum):
    DEFINITION = "DEFINITION"
    UPDATE = "UPDATE"
    REFERENCE = "REFERENCE"
    HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"
    RECONCILIATION = "RECONCILIATION"


@dataclass(frozen=True)
class HistoricalArtifactSnapshot:
    path: str
    sha256: str
    git_blob_sha: str
    sequence: tuple[int, int, int, str]
    kind: str


@dataclass(frozen=True)
class ScopedFiberReallocation:
    source_path: str
    historical_id: str
    canonical_id: str
    reconciliation_path: str
    reconciliation_sequence: tuple[int, int, int, str]


@dataclass(frozen=True)
class HistoricalFiberEvent:
    source_path: str
    sequence: tuple[int, int, int, str]
    role: FiberEventRole
    raw_fiber_id: str
    canonical_fiber_id: str
    question: str | None = None
    state: str | None = None
    location: str = ""

    @property
    def slot(self) -> int:
        match = _NUMERIC.fullmatch(self.canonical_fiber_id)
        if match is None:
            raise ValueError(f"not a numeric fiber id: {self.canonical_fiber_id}")
        return int(match.group("slot"))


@dataclass(frozen=True)
class HistoricalLedgerIssue:
    kind: HistoricalIssueKind
    message: str
    source_path: str | None = None
    fiber_id: str | None = None
    resolved: bool = False
    resolution: str | None = None


@dataclass(frozen=True)
class CanonicalFiberState:
    fiber_id: str
    first_source_path: str
    first_sequence: tuple[int, int, int, str]
    question: str | None
    latest_state: str | None
    event_count: int


@dataclass(frozen=True)
class HistoricalMetaLedgerReport:
    verdict: HistoricalLedgerVerdict
    artifacts: tuple[HistoricalArtifactSnapshot, ...]
    events: tuple[HistoricalFiberEvent, ...]
    reallocations: tuple[ScopedFiberReallocation, ...]
    issues: tuple[HistoricalLedgerIssue, ...]
    canonical_fibers: tuple[CanonicalFiberState, ...]
    ledger_digest: str

    @property
    def unresolved_issues(self) -> tuple[HistoricalLedgerIssue, ...]:
        return tuple(issue for issue in self.issues if not issue.resolved)

    @property
    def covered_artifact_paths(self) -> tuple[str, ...]:
        return tuple(artifact.path for artifact in self.artifacts)

    def can_support_registry_bookkeeping(self) -> bool:
        return self.verdict in {
            HistoricalLedgerVerdict.CONSISTENT,
            HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY,
        }

    def can_grant_scientific_authority(self) -> bool:
        return False

    def can_grant_method_authority(self) -> bool:
        return False

    def can_grant_target_authority(self) -> bool:
        return False

    def can_grant_independent_review_credit(self) -> bool:
        return False

    def can_grant_framework_saturation(self) -> bool:
        return False


def git_blob_sha(data: bytes) -> str:
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _fiber(value: object) -> str | None:
    return value if isinstance(value, str) and _NUMERIC.fullmatch(value) else None


def _sequence(path: str, kind: str) -> tuple[int, int, int, str]:
    name = Path(path).name
    if name == "META_FIBER_BACKLOG.json":
        return (0, 0, 0, name)
    match = _ROUND.search(name)
    if match is None:
        return (9999, 0, 99, name)
    suffix = match.group("suffix")
    suffix_rank = 0 if not suffix else ord(suffix) - ord("A") + 1
    phase = 20 if kind == "reconciliation" else 25
    if "_RECONCILIATION_DELTA" in name:
        phase = 30
    elif "_CLOSURE_DELTA" in name:
        phase = 40
    elif "_POSTVALIDATION_DELTA" in name:
        phase = 50
    return (int(match.group("round")), suffix_rank, phase, name)


def _snapshot(path: Path, root: Path, kind: str) -> HistoricalArtifactSnapshot:
    data = path.read_bytes()
    rel = path.relative_to(root).as_posix()
    return HistoricalArtifactSnapshot(
        path=rel,
        sha256=sha256(data).hexdigest(),
        git_blob_sha=git_blob_sha(data),
        sequence=_sequence(rel, kind),
        kind=kind,
    )


def discover_meta_ledger_paths(research_dir: Path) -> tuple[Path, ...]:
    research_dir = Path(research_dir)
    paths = set(research_dir.glob("META_FIBER_BACKLOG*.json"))
    paths.update(research_dir.glob("META_FIBER_REGISTRY_RECONCILIATION*.json"))
    return tuple(sorted(paths, key=lambda path: path.name))


def _markdown_new_fibers(text: str) -> tuple[str, ...]:
    active = False
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            if active and heading != "new fibers":
                break
            active = heading == "new fibers"
            continue
        if active:
            found.extend(match.group(1) for match in _MARKDOWN.finditer(line))
    return tuple(found)


def _state(record: Mapping[str, Any]) -> str | None:
    for key in ("new_status", "state", "status", "disposition"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _question(record: Mapping[str, Any]) -> str | None:
    for key in ("question", "problem"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_definition(record: Mapping[str, Any], parent_key: str | None) -> bool:
    if parent_key in {
        "items",
        "fibers",
        "new_fibers",
        "canonical_round034_fibers",
        "new_children",
        "child_fibers",
        "new_meta_fibers",
    }:
        return True
    state = _state(record) or ""
    # Several early immutable deltas introduced new fibers inside `updates`.
    # NEW_* is therefore historical declaration evidence, not merely an update.
    if state.startswith("NEW") and (_question(record) is not None or "target" in record):
        return True
    return False


def _walk(
    value: Any,
    *,
    source_path: str,
    sequence: tuple[int, int, int, str],
    aliases: Mapping[tuple[str, str], str],
    alias_pairs: Mapping[str, str],
    location: str = "$",
    parent_key: str | None = None,
) -> tuple[list[HistoricalFiberEvent], list[HistoricalLedgerIssue]]:
    events: list[HistoricalFiberEvent] = []
    issues: list[HistoricalLedgerIssue] = []
    if isinstance(value, Mapping):
        raw_id = _fiber(value.get("fiber_id"))
        consumed: set[str] = set()
        if raw_id is not None:
            consumed.add("fiber_id")
            canonical_id = aliases.get((source_path, raw_id), raw_id)
            role = FiberEventRole.DEFINITION if _is_definition(value, parent_key) else FiberEventRole.UPDATE
            if role == FiberEventRole.UPDATE and not any(
                key in value
                for key in (
                    "status", "state", "new_status", "old_status", "disposition", "priority",
                    "evidence", "note", "remaining_gap", "remaining_blocker", "next_discriminator",
                    "next_probe", "target", "falsifier",
                )
            ):
                issues.append(
                    HistoricalLedgerIssue(
                        kind=HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD,
                        message=f"Cannot classify fiber_id record at {location}",
                        source_path=source_path,
                        fiber_id=raw_id,
                    )
                )
            events.append(
                HistoricalFiberEvent(
                    source_path=source_path,
                    sequence=sequence,
                    role=role,
                    raw_fiber_id=raw_id,
                    canonical_fiber_id=canonical_id,
                    question=_question(value),
                    state=_state(value),
                    location=f"{location}.fiber_id",
                )
            )
            historical_id = _fiber(value.get("historical_id"))
            if historical_id is not None and alias_pairs.get(historical_id) == canonical_id:
                consumed.add("historical_id")
                events.append(
                    HistoricalFiberEvent(
                        source_path=source_path,
                        sequence=sequence,
                        role=FiberEventRole.HISTORICAL_REFERENCE,
                        raw_fiber_id=historical_id,
                        canonical_fiber_id=canonical_id,
                        location=f"{location}.historical_id",
                    )
                )

        for key, child in value.items():
            if key in consumed:
                continue
            if parent_key == "explicit_aliases" and key in {"historical_id", "canonical_id"}:
                continue
            child_location = f"{location}.{key}"
            if isinstance(child, str):
                raw_child = _fiber(child)
                if raw_child is not None:
                    events.append(
                        HistoricalFiberEvent(
                            source_path=source_path,
                            sequence=sequence,
                            role=FiberEventRole.REFERENCE,
                            raw_fiber_id=raw_child,
                            canonical_fiber_id=aliases.get((source_path, raw_child), raw_child),
                            location=child_location,
                        )
                    )
                    continue
            child_events, child_issues = _walk(
                child,
                source_path=source_path,
                sequence=sequence,
                aliases=aliases,
                alias_pairs=alias_pairs,
                location=child_location,
                parent_key=key,
            )
            events.extend(child_events)
            issues.extend(child_issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_location = f"{location}[{index}]"
            if isinstance(child, str):
                raw_child = _fiber(child)
                if raw_child is not None:
                    events.append(
                        HistoricalFiberEvent(
                            source_path=source_path,
                            sequence=sequence,
                            role=FiberEventRole.REFERENCE,
                            raw_fiber_id=raw_child,
                            canonical_fiber_id=aliases.get((source_path, raw_child), raw_child),
                            location=child_location,
                        )
                    )
                    continue
            child_events, child_issues = _walk(
                child,
                source_path=source_path,
                sequence=sequence,
                aliases=aliases,
                alias_pairs=alias_pairs,
                location=child_location,
                parent_key=parent_key,
            )
            events.extend(child_events)
            issues.extend(child_issues)
    return events, issues


def _canonical_states(events: Iterable[HistoricalFiberEvent]) -> tuple[CanonicalFiberState, ...]:
    grouped: dict[str, list[HistoricalFiberEvent]] = {}
    for event in events:
        if event.role in {FiberEventRole.DEFINITION, FiberEventRole.UPDATE}:
            grouped.setdefault(event.canonical_fiber_id, []).append(event)
    result: list[CanonicalFiberState] = []
    for fiber_id, fiber_events in grouped.items():
        ordered = sorted(fiber_events, key=lambda event: (event.sequence, event.source_path, event.location))
        definitions = [event for event in ordered if event.role == FiberEventRole.DEFINITION]
        if not definitions:
            continue
        result.append(
            CanonicalFiberState(
                fiber_id=fiber_id,
                first_source_path=definitions[0].source_path,
                first_sequence=definitions[0].sequence,
                question=next((event.question for event in definitions if event.question), None),
                latest_state=next((event.state for event in reversed(ordered) if event.state), None),
                event_count=len(ordered),
            )
        )
    return tuple(sorted(result, key=lambda item: item.fiber_id))


def _digest(
    artifacts: Iterable[HistoricalArtifactSnapshot],
    events: Iterable[HistoricalFiberEvent],
    reallocations: Iterable[ScopedFiberReallocation],
    issues: Iterable[HistoricalLedgerIssue],
) -> str:
    payload = {
        "artifacts": [(a.path, a.sha256, a.git_blob_sha, a.sequence, a.kind) for a in sorted(artifacts, key=lambda x: x.path)],
        "events": [
            (e.source_path, e.sequence, e.role.value, e.raw_fiber_id, e.canonical_fiber_id, e.question, e.state, e.location)
            for e in sorted(events, key=lambda x: (x.source_path, x.location, x.role.value, x.raw_fiber_id))
        ],
        "reallocations": [
            (r.source_path, r.historical_id, r.canonical_id, r.reconciliation_path, r.reconciliation_sequence)
            for r in sorted(reallocations, key=lambda x: (x.source_path, x.historical_id))
        ],
        "issues": [
            (i.kind.value, i.message, i.source_path, i.fiber_id, i.resolved, i.resolution)
            for i in sorted(issues, key=lambda x: (x.kind.value, x.source_path or "", x.fiber_id or "", x.message))
        ],
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def compile_meta_fiber_history(research_dir: Path) -> HistoricalMetaLedgerReport:
    research_dir = Path(research_dir)
    root = research_dir.parent
    artifacts: list[HistoricalArtifactSnapshot] = []
    parsed: dict[str, Any] = {}
    raw: dict[str, bytes] = {}
    issues: list[HistoricalLedgerIssue] = []

    for path in discover_meta_ledger_paths(research_dir):
        rel = path.relative_to(root).as_posix()
        kind = "reconciliation" if path.name.startswith("META_FIBER_REGISTRY_RECONCILIATION") else "backlog"
        artifacts.append(_snapshot(path, root, kind))
        data = path.read_bytes()
        raw[rel] = data
        try:
            parsed[rel] = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(HistoricalLedgerIssue(HistoricalIssueKind.INVALID_JSON, f"Cannot parse {rel}: {exc}", rel))

    reallocations: list[ScopedFiberReallocation] = []
    orphan_resolutions: dict[str, str] = {}
    alias_pairs: dict[str, str] = {}
    reconciliation_artifacts = sorted(
        (a for a in artifacts if a.kind == "reconciliation" and a.path in parsed),
        key=lambda a: a.sequence,
    )
    for artifact in reconciliation_artifacts:
        obj = parsed[artifact.path]
        if not isinstance(obj, Mapping):
            issues.append(HistoricalLedgerIssue(HistoricalIssueKind.INVALID_JSON, "Reconciliation root must be an object", artifact.path))
            continue
        verified: dict[str, str] = {}
        sources = obj.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, Mapping):
                    continue
                source_path = source.get("path")
                expected = source.get("blob_sha")
                if not isinstance(source_path, str) or not isinstance(expected, str):
                    continue
                source_file = root / source_path
                if not source_file.exists():
                    issues.append(HistoricalLedgerIssue(HistoricalIssueKind.SOURCE_MISSING, f"Reconciliation source is missing: {source_path}", artifact.path))
                    continue
                data = source_file.read_bytes()
                actual = git_blob_sha(data)
                if actual != expected:
                    issues.append(HistoricalLedgerIssue(HistoricalIssueKind.SOURCE_BLOB_MISMATCH, f"Expected Git blob {expected}, got {actual} for {source_path}", artifact.path))
                    continue
                verified[source_path] = data.decode("utf-8")
                if source_path not in raw:
                    raw[source_path] = data
                    artifacts.append(_snapshot(source_file, root, "reconciliation_source"))

        aliases = obj.get("explicit_aliases", [])
        if isinstance(aliases, list):
            for alias in aliases:
                if not isinstance(alias, Mapping):
                    continue
                historical = _fiber(alias.get("historical_id"))
                canonical = _fiber(alias.get("canonical_id"))
                if historical is None or canonical is None:
                    continue
                matches = [path for path, text in verified.items() if historical in text]
                if len(matches) != 1:
                    issues.append(HistoricalLedgerIssue(
                        HistoricalIssueKind.RECONCILIATION_SCOPE_UNVERIFIABLE,
                        f"Expected exactly one verified historical source containing {historical}; found {len(matches)}",
                        artifact.path,
                        historical,
                    ))
                    continue
                source_path = matches[0]
                source_seq = _sequence(source_path, "reconciliation_source")
                if source_seq >= artifact.sequence:
                    issues.append(HistoricalLedgerIssue(
                        HistoricalIssueKind.RECONCILIATION_CHRONOLOGY_INVALID,
                        f"Historical source {source_path} is not earlier than reconciliation {artifact.path}",
                        artifact.path,
                        historical,
                    ))
                    continue
                reallocations.append(ScopedFiberReallocation(source_path, historical, canonical, artifact.path, artifact.sequence))
                alias_pairs[historical] = canonical

        target = _fiber(obj.get("target_reference"))
        disposition = obj.get("disposition")
        if target and isinstance(disposition, str) and "HISTORICAL_ORPHAN_REFERENCE" in disposition and obj.get("retroactive_definition_created") is False:
            orphan_resolutions[target] = artifact.path

    scoped_aliases = {(r.source_path, r.historical_id): r.canonical_id for r in reallocations}
    events: list[HistoricalFiberEvent] = []
    for artifact in sorted(artifacts, key=lambda a: (a.sequence, a.path)):
        if artifact.kind == "reconciliation_source" or artifact.path not in parsed:
            continue
        found, found_issues = _walk(
            parsed[artifact.path],
            source_path=artifact.path,
            sequence=artifact.sequence,
            aliases=scoped_aliases,
            alias_pairs=alias_pairs,
        )
        events.extend(found)
        issues.extend(found_issues)

    for artifact in sorted(artifacts, key=lambda a: (a.sequence, a.path)):
        if artifact.kind != "reconciliation_source" or not artifact.path.endswith(".md"):
            continue
        for index, raw_id in enumerate(_markdown_new_fibers(raw[artifact.path].decode("utf-8"))):
            events.append(HistoricalFiberEvent(
                artifact.path,
                artifact.sequence,
                FiberEventRole.DEFINITION,
                raw_id,
                scoped_aliases.get((artifact.path, raw_id), raw_id),
                location=f"markdown:new_fibers[{index}]",
            ))

    events.sort(key=lambda e: (e.sequence, e.source_path, e.location, e.role.value, e.raw_fiber_id))

    # Raw slot collisions remain visible forever. Only the exact historical
    # occurrence covered by a verified source-scoped reconciliation is resolved.
    raw_by_slot: dict[int, list[HistoricalFiberEvent]] = {}
    for event in events:
        if event.role != FiberEventRole.DEFINITION:
            continue
        match = _NUMERIC.fullmatch(event.raw_fiber_id)
        if match:
            raw_by_slot.setdefault(int(match.group("slot")), []).append(event)
    for slot, slot_events in sorted(raw_by_slot.items()):
        ordered = sorted(slot_events, key=lambda e: (e.sequence, e.source_path, e.location))
        baseline = ordered[0].raw_fiber_id
        distinct = sorted({event.raw_fiber_id for event in ordered})
        if len(distinct) <= 1:
            continue
        for event in ordered[1:]:
            if event.raw_fiber_id == baseline:
                continue
            mapped = scoped_aliases.get((event.source_path, event.raw_fiber_id))
            resolved = mapped is not None and mapped != event.raw_fiber_id
            issues.append(HistoricalLedgerIssue(
                HistoricalIssueKind.NAMESPACE_SLOT_COLLISION,
                f"Raw slot {slot} was allocated to {', '.join(distinct)}",
                event.source_path,
                event.raw_fiber_id,
                resolved,
                f"source-scoped forward identity {event.raw_fiber_id} -> {mapped}" if resolved else None,
            ))

    definitions = [event for event in events if event.role == FiberEventRole.DEFINITION]
    canonical_by_slot: dict[int, set[str]] = {}
    for event in definitions:
        match = _NUMERIC.fullmatch(event.canonical_fiber_id)
        if match:
            canonical_by_slot.setdefault(int(match.group("slot")), set()).add(event.canonical_fiber_id)
    for slot, ids in sorted(canonical_by_slot.items()):
        if len(ids) > 1:
            issues.append(HistoricalLedgerIssue(HistoricalIssueKind.CANONICAL_SLOT_COLLISION, f"Canonical slot {slot} remains multiply allocated: {', '.join(sorted(ids))}"))

    questions: dict[str, set[str]] = {}
    for event in definitions:
        if event.question:
            questions.setdefault(event.canonical_fiber_id, set()).add(" ".join(event.question.split()))
    for fiber_id, variants in sorted(questions.items()):
        if len(variants) > 1:
            issues.append(HistoricalLedgerIssue(HistoricalIssueKind.DEFINITION_CONFLICT, f"Multiple distinct question/problem definitions found for {fiber_id}", fiber_id=fiber_id))

    defined = {event.canonical_fiber_id for event in definitions}
    for reallocation in reallocations:
        if reallocation.canonical_id not in defined:
            issues.append(HistoricalLedgerIssue(HistoricalIssueKind.RECONCILIATION_TARGET_ORPHAN, f"Reconciliation target is never defined: {reallocation.canonical_id}", reallocation.reconciliation_path, reallocation.canonical_id))

    seen_orphans: set[tuple[str, str]] = set()
    for event in events:
        if event.role not in {FiberEventRole.REFERENCE, FiberEventRole.UPDATE} or event.canonical_fiber_id in defined:
            continue
        key = (event.source_path, event.canonical_fiber_id)
        if key in seen_orphans:
            continue
        seen_orphans.add(key)
        resolution = orphan_resolutions.get(event.canonical_fiber_id)
        issues.append(HistoricalLedgerIssue(
            HistoricalIssueKind.ORPHAN_REFERENCE,
            f"Reference has no canonical definition: {event.canonical_fiber_id}",
            event.source_path,
            event.canonical_fiber_id,
            resolution is not None,
            f"explicit non-retroactive orphan disposition in {resolution}" if resolution else None,
        ))

    unresolved = [issue for issue in issues if not issue.resolved]
    if any(issue.kind == HistoricalIssueKind.RECONCILIATION_CHRONOLOGY_INVALID for issue in unresolved):
        verdict = HistoricalLedgerVerdict.TRIAL_INVALID
    elif any(issue.kind in {
        HistoricalIssueKind.INVALID_JSON,
        HistoricalIssueKind.SOURCE_MISSING,
        HistoricalIssueKind.SOURCE_BLOB_MISMATCH,
        HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD,
        HistoricalIssueKind.RECONCILIATION_SCOPE_UNVERIFIABLE,
    } for issue in unresolved):
        verdict = HistoricalLedgerVerdict.CANNOT_CHECK
    elif unresolved:
        verdict = HistoricalLedgerVerdict.CONFLICTED
    elif reallocations or any(issue.resolved for issue in issues):
        verdict = HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    else:
        verdict = HistoricalLedgerVerdict.CONSISTENT

    artifact_tuple = tuple(sorted(artifacts, key=lambda a: a.path))
    event_tuple = tuple(events)
    reallocation_tuple = tuple(sorted(reallocations, key=lambda r: (r.source_path, r.historical_id)))
    issue_tuple = tuple(sorted(issues, key=lambda i: (i.kind.value, i.source_path or "", i.fiber_id or "", i.message)))
    return HistoricalMetaLedgerReport(
        verdict=verdict,
        artifacts=artifact_tuple,
        events=event_tuple,
        reallocations=reallocation_tuple,
        issues=issue_tuple,
        canonical_fibers=_canonical_states(events),
        ledger_digest=_digest(artifact_tuple, event_tuple, reallocation_tuple, issue_tuple),
    )
