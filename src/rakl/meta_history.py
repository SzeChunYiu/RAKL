from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable, Mapping


_NUMERIC_FIBER_RE = re.compile(r"^META_N(?P<slot>\d{3,})_[A-Z0-9_]+$")
_MARKDOWN_FIBER_RE = re.compile(r"`(META_N\d{3,}_[A-Z0-9_]+)`")
_ROUND_RE = re.compile(r"_(?P<round>\d{3})(?P<suffix>[A-Z]?)(?:_|\.)")


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
        match = _NUMERIC_FIBER_RE.fullmatch(self.canonical_fiber_id)
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

    def can_support_registry_bookkeeping(self) -> bool:
        return self.verdict in {
            HistoricalLedgerVerdict.CONSISTENT,
            HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY,
        }


def git_blob_sha(data: bytes) -> str:
    """Return the Git object id for exact blob bytes."""
    return sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _numeric_fiber_id(value: object) -> str | None:
    if isinstance(value, str) and _NUMERIC_FIBER_RE.fullmatch(value):
        return value
    return None


def _round_sequence(path: str, *, kind: str) -> tuple[int, int, int, str]:
    name = Path(path).name
    if name == "META_FIBER_BACKLOG.json":
        return (0, 0, 0, name)
    match = _ROUND_RE.search(name)
    if match is None:
        return (9999, 0, 99, name)
    round_number = int(match.group("round"))
    suffix = match.group("suffix")
    suffix_rank = 0 if not suffix else ord(suffix) - ord("A") + 1
    if kind == "reconciliation":
        phase = 20
    elif "_RECONCILIATION_DELTA" in name:
        phase = 30
    elif "_CLOSURE_DELTA" in name:
        phase = 40
    elif "_POSTVALIDATION_DELTA" in name:
        phase = 50
    else:
        phase = 25
    return (round_number, suffix_rank, phase, name)


def _artifact_snapshot(path: Path, repo_root: Path, *, kind: str) -> HistoricalArtifactSnapshot:
    data = path.read_bytes()
    rel = path.relative_to(repo_root).as_posix()
    return HistoricalArtifactSnapshot(
        path=rel,
        sha256=sha256(data).hexdigest(),
        git_blob_sha=git_blob_sha(data),
        sequence=_round_sequence(rel, kind=kind),
        kind=kind,
    )


def discover_meta_ledger_paths(research_dir: Path) -> tuple[Path, ...]:
    """Discover ledger artifacts without a hard-coded round manifest."""
    paths = set(research_dir.glob("META_FIBER_BACKLOG*.json"))
    paths.update(research_dir.glob("META_FIBER_REGISTRY_RECONCILIATION*.json"))
    return tuple(sorted(paths, key=lambda path: path.name))


def _extract_markdown_new_fibers(text: str) -> tuple[str, ...]:
    in_section = False
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            if in_section and heading != "new fibers":
                break
            in_section = heading == "new fibers"
            continue
        if in_section:
            found.extend(match.group(1) for match in _MARKDOWN_FIBER_RE.finditer(line))
    return tuple(found)


def _walk_records(
    value: Any,
    *,
    source_path: str,
    sequence: tuple[int, int, int, str],
    scoped_aliases: Mapping[tuple[str, str], str],
    alias_pairs: Mapping[str, str],
    location: str = "$",
    container_key: str | None = None,
) -> tuple[list[HistoricalFiberEvent], list[HistoricalLedgerIssue]]:
    events: list[HistoricalFiberEvent] = []
    issues: list[HistoricalLedgerIssue] = []
    definition_containers = {
        "items",
        "fibers",
        "new_fibers",
        "canonical_round034_fibers",
        "new_children",
        "child_fibers",
    }
    update_containers = {"updates", "fiber_updates"}
    recognized_update_fields = {
        "status",
        "state",
        "old_status",
        "new_status",
        "disposition",
        "priority",
        "target",
        "falsifier",
        "next_discriminator",
        "next_probe",
        "remaining_blocker",
        "blocking_condition",
    }

    if isinstance(value, Mapping):
        raw_id = _numeric_fiber_id(value.get("fiber_id"))
        consumed: set[str] = set()
        if raw_id is not None:
            id_location = f"{location}.fiber_id"
            consumed.add("fiber_id")
            canonical_id = scoped_aliases.get((source_path, raw_id), raw_id)
            question_obj = value.get("question")
            question = question_obj.strip() if isinstance(question_obj, str) and question_obj.strip() else None
            state: str | None = None
            for key in ("new_status", "state", "status", "disposition"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    state = candidate.strip()
                    break

            if container_key in update_containers:
                role = FiberEventRole.UPDATE
            elif container_key in definition_containers or question is not None:
                role = FiberEventRole.DEFINITION
            elif recognized_update_fields.intersection(value.keys()):
                role = FiberEventRole.UPDATE
            else:
                role = FiberEventRole.UPDATE
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
                    question=question,
                    state=state,
                    location=id_location,
                )
            )

            historical_id = _numeric_fiber_id(value.get("historical_id"))
            if historical_id is not None:
                expected = alias_pairs.get(historical_id)
                if expected == canonical_id:
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
            # Reconciliation alias pairs are parsed in a dedicated pass; they
            # are not ordinary global references.
            if container_key == "explicit_aliases" and key in {"historical_id", "canonical_id"}:
                continue
            child_location = f"{location}.{key}"
            if isinstance(child, str):
                raw_child = _numeric_fiber_id(child)
                if raw_child is not None:
                    canonical_child = scoped_aliases.get((source_path, raw_child), raw_child)
                    events.append(
                        HistoricalFiberEvent(
                            source_path=source_path,
                            sequence=sequence,
                            role=FiberEventRole.REFERENCE,
                            raw_fiber_id=raw_child,
                            canonical_fiber_id=canonical_child,
                            location=child_location,
                        )
                    )
                    continue
            child_events, child_issues = _walk_records(
                child,
                source_path=source_path,
                sequence=sequence,
                scoped_aliases=scoped_aliases,
                alias_pairs=alias_pairs,
                location=child_location,
                container_key=key,
            )
            events.extend(child_events)
            issues.extend(child_issues)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_location = f"{location}[{index}]"
            if isinstance(child, str):
                raw_child = _numeric_fiber_id(child)
                if raw_child is not None:
                    canonical_child = scoped_aliases.get((source_path, raw_child), raw_child)
                    events.append(
                        HistoricalFiberEvent(
                            source_path=source_path,
                            sequence=sequence,
                            role=FiberEventRole.REFERENCE,
                            raw_fiber_id=raw_child,
                            canonical_fiber_id=canonical_child,
                            location=child_location,
                        )
                    )
                    continue
            child_events, child_issues = _walk_records(
                child,
                source_path=source_path,
                sequence=sequence,
                scoped_aliases=scoped_aliases,
                alias_pairs=alias_pairs,
                location=child_location,
                container_key=container_key,
            )
            events.extend(child_events)
            issues.extend(child_issues)
    return events, issues


def _canonical_state(events: Iterable[HistoricalFiberEvent]) -> tuple[CanonicalFiberState, ...]:
    grouped: dict[str, list[HistoricalFiberEvent]] = {}
    for event in events:
        if event.role in {FiberEventRole.DEFINITION, FiberEventRole.UPDATE}:
            grouped.setdefault(event.canonical_fiber_id, []).append(event)
    states: list[CanonicalFiberState] = []
    for fiber_id, fiber_events in grouped.items():
        ordered = sorted(fiber_events, key=lambda event: (event.sequence, event.source_path, event.location))
        definitions = [event for event in ordered if event.role == FiberEventRole.DEFINITION]
        if not definitions:
            continue
        first = definitions[0]
        states.append(
            CanonicalFiberState(
                fiber_id=fiber_id,
                first_source_path=first.source_path,
                first_sequence=first.sequence,
                question=next((event.question for event in definitions if event.question), None),
                latest_state=next((event.state for event in reversed(ordered) if event.state), None),
                event_count=len(ordered),
            )
        )
    return tuple(sorted(states, key=lambda state: state.fiber_id))


def _digest(
    artifacts: Iterable[HistoricalArtifactSnapshot],
    events: Iterable[HistoricalFiberEvent],
    reallocations: Iterable[ScopedFiberReallocation],
    issues: Iterable[HistoricalLedgerIssue],
) -> str:
    payload = {
        "artifacts": [
            (a.path, a.sha256, a.git_blob_sha, a.sequence, a.kind)
            for a in sorted(artifacts, key=lambda item: item.path)
        ],
        "events": [
            (e.source_path, e.sequence, e.role.value, e.raw_fiber_id, e.canonical_fiber_id, e.question, e.state, e.location)
            for e in sorted(events, key=lambda item: (item.source_path, item.location, item.role.value, item.raw_fiber_id))
        ],
        "reallocations": [
            (r.source_path, r.historical_id, r.canonical_id, r.reconciliation_path, r.reconciliation_sequence)
            for r in sorted(reallocations, key=lambda item: (item.source_path, item.historical_id))
        ],
        "issues": [
            (i.kind.value, i.message, i.source_path, i.fiber_id, i.resolved, i.resolution)
            for i in sorted(issues, key=lambda item: (item.kind.value, item.source_path or "", item.fiber_id or "", item.message))
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def compile_meta_fiber_history(research_dir: Path) -> HistoricalMetaLedgerReport:
    """Compile immutable meta-fiber history with source-scoped reconciliation.

    The compiler deliberately separates raw identifier occurrences from
    canonical identity. A forward repair for one historical source never acts
    as a global string substitution, because the same raw numeric slot may be
    the valid canonical identity of an earlier fiber.
    """
    research_dir = Path(research_dir)
    repo_root = research_dir.parent
    artifacts: list[HistoricalArtifactSnapshot] = []
    parsed: dict[str, Any] = {}
    raw_bytes: dict[str, bytes] = {}
    issues: list[HistoricalLedgerIssue] = []

    for path in discover_meta_ledger_paths(research_dir):
        rel = path.relative_to(repo_root).as_posix()
        kind = "reconciliation" if path.name.startswith("META_FIBER_REGISTRY_RECONCILIATION") else "backlog"
        artifacts.append(_artifact_snapshot(path, repo_root, kind=kind))
        data = path.read_bytes()
        raw_bytes[rel] = data
        try:
            parsed[rel] = json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.INVALID_JSON,
                    message=f"Cannot parse {rel}: {exc}",
                    source_path=rel,
                )
            )

    reconciliation_artifacts = sorted(
        (a for a in artifacts if a.kind == "reconciliation" and a.path in parsed),
        key=lambda item: item.sequence,
    )
    reallocations: list[ScopedFiberReallocation] = []
    orphan_resolutions: dict[str, str] = {}
    alias_pairs: dict[str, str] = {}

    for artifact in reconciliation_artifacts:
        obj = parsed[artifact.path]
        if not isinstance(obj, Mapping):
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.INVALID_JSON,
                    message="Reconciliation root must be an object",
                    source_path=artifact.path,
                )
            )
            continue

        verified_sources: dict[str, str] = {}
        sources_obj = obj.get("sources", [])
        if isinstance(sources_obj, list):
            for source in sources_obj:
                if not isinstance(source, Mapping):
                    continue
                source_path = source.get("path")
                expected_blob = source.get("blob_sha")
                if not isinstance(source_path, str) or not isinstance(expected_blob, str):
                    continue
                source_file = repo_root / source_path
                if not source_file.exists():
                    issues.append(
                        HistoricalLedgerIssue(
                            kind=HistoricalIssueKind.SOURCE_MISSING,
                            message=f"Reconciliation source is missing: {source_path}",
                            source_path=artifact.path,
                        )
                    )
                    continue
                source_data = source_file.read_bytes()
                actual_blob = git_blob_sha(source_data)
                if actual_blob != expected_blob:
                    issues.append(
                        HistoricalLedgerIssue(
                            kind=HistoricalIssueKind.SOURCE_BLOB_MISMATCH,
                            message=f"Expected Git blob {expected_blob}, got {actual_blob} for {source_path}",
                            source_path=artifact.path,
                        )
                    )
                    continue
                verified_sources[source_path] = source_data.decode("utf-8")
                if source_path not in raw_bytes:
                    raw_bytes[source_path] = source_data
                    artifacts.append(_artifact_snapshot(source_file, repo_root, kind="reconciliation_source"))

        aliases_obj = obj.get("explicit_aliases", [])
        if isinstance(aliases_obj, list):
            for alias in aliases_obj:
                if not isinstance(alias, Mapping):
                    continue
                historical_id = _numeric_fiber_id(alias.get("historical_id"))
                canonical_id = _numeric_fiber_id(alias.get("canonical_id"))
                if historical_id is None or canonical_id is None:
                    continue
                matches = [path for path, text in verified_sources.items() if historical_id in text]
                if len(matches) != 1:
                    issues.append(
                        HistoricalLedgerIssue(
                            kind=HistoricalIssueKind.RECONCILIATION_SCOPE_UNVERIFIABLE,
                            message=f"Expected exactly one verified historical source containing {historical_id}; found {len(matches)}",
                            source_path=artifact.path,
                            fiber_id=historical_id,
                        )
                    )
                    continue
                source_path = matches[0]
                source_sequence = _round_sequence(source_path, kind="reconciliation_source")
                if source_sequence >= artifact.sequence:
                    issues.append(
                        HistoricalLedgerIssue(
                            kind=HistoricalIssueKind.RECONCILIATION_CHRONOLOGY_INVALID,
                            message=f"Historical source {source_path} is not earlier than reconciliation {artifact.path}",
                            source_path=artifact.path,
                            fiber_id=historical_id,
                        )
                    )
                    continue
                reallocations.append(
                    ScopedFiberReallocation(
                        source_path=source_path,
                        historical_id=historical_id,
                        canonical_id=canonical_id,
                        reconciliation_path=artifact.path,
                        reconciliation_sequence=artifact.sequence,
                    )
                )
                alias_pairs[historical_id] = canonical_id

        target_reference = _numeric_fiber_id(obj.get("target_reference"))
        disposition = obj.get("disposition")
        if (
            target_reference is not None
            and isinstance(disposition, str)
            and "HISTORICAL_ORPHAN_REFERENCE" in disposition
            and obj.get("retroactive_definition_created") is False
        ):
            orphan_resolutions[target_reference] = artifact.path

    scoped_aliases = {(r.source_path, r.historical_id): r.canonical_id for r in reallocations}

    events: list[HistoricalFiberEvent] = []
    for artifact in sorted(artifacts, key=lambda item: (item.sequence, item.path)):
        if artifact.kind == "reconciliation_source" or artifact.path not in parsed:
            continue
        artifact_events, artifact_issues = _walk_records(
            parsed[artifact.path],
            source_path=artifact.path,
            sequence=artifact.sequence,
            scoped_aliases=scoped_aliases,
            alias_pairs=alias_pairs,
        )
        events.extend(artifact_events)
        issues.extend(artifact_issues)

    # Only reconciliation-linked Markdown sections explicitly declaring new
    # fibers are promoted to definition events. Other prose mentions remain
    # evidence, not registry declarations.
    for artifact in sorted(artifacts, key=lambda item: (item.sequence, item.path)):
        if artifact.kind != "reconciliation_source" or not artifact.path.endswith(".md"):
            continue
        text = raw_bytes[artifact.path].decode("utf-8")
        for index, raw_id in enumerate(_extract_markdown_new_fibers(text)):
            events.append(
                HistoricalFiberEvent(
                    source_path=artifact.path,
                    sequence=artifact.sequence,
                    role=FiberEventRole.DEFINITION,
                    raw_fiber_id=raw_id,
                    canonical_fiber_id=scoped_aliases.get((artifact.path, raw_id), raw_id),
                    location=f"markdown:new_fibers[{index}]",
                )
            )

    events.sort(key=lambda event: (event.sequence, event.source_path, event.location, event.role.value, event.raw_fiber_id))

    raw_by_slot: dict[int, list[HistoricalFiberEvent]] = {}
    for event in events:
        if event.role != FiberEventRole.DEFINITION:
            continue
        match = _NUMERIC_FIBER_RE.fullmatch(event.raw_fiber_id)
        if match is not None:
            raw_by_slot.setdefault(int(match.group("slot")), []).append(event)
    for slot, slot_events in sorted(raw_by_slot.items()):
        ordered = sorted(slot_events, key=lambda event: (event.sequence, event.source_path, event.location))
        baseline_raw_id = ordered[0].raw_fiber_id
        distinct = sorted({event.raw_fiber_id for event in ordered})
        if len(distinct) <= 1:
            continue
        for event in ordered[1:]:
            if event.raw_fiber_id == baseline_raw_id:
                continue
            mapped = scoped_aliases.get((event.source_path, event.raw_fiber_id))
            resolved = mapped is not None and mapped != event.raw_fiber_id
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.NAMESPACE_SLOT_COLLISION,
                    message=f"Raw slot {slot} was allocated to {', '.join(distinct)}",
                    source_path=event.source_path,
                    fiber_id=event.raw_fiber_id,
                    resolved=resolved,
                    resolution=(f"source-scoped forward identity {event.raw_fiber_id} -> {mapped}" if resolved else None),
                )
            )

    definitions = [event for event in events if event.role == FiberEventRole.DEFINITION]
    canonical_by_slot: dict[int, set[str]] = {}
    for event in definitions:
        match = _NUMERIC_FIBER_RE.fullmatch(event.canonical_fiber_id)
        if match is not None:
            canonical_by_slot.setdefault(int(match.group("slot")), set()).add(event.canonical_fiber_id)
    for slot, ids in sorted(canonical_by_slot.items()):
        if len(ids) > 1:
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.CANONICAL_SLOT_COLLISION,
                    message=f"Canonical slot {slot} remains multiply allocated: {', '.join(sorted(ids))}",
                )
            )

    questions_by_id: dict[str, set[str]] = {}
    for event in definitions:
        if event.question:
            questions_by_id.setdefault(event.canonical_fiber_id, set()).add(" ".join(event.question.split()))
    for fiber_id, questions in sorted(questions_by_id.items()):
        if len(questions) > 1:
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.DEFINITION_CONFLICT,
                    message=f"Multiple distinct question definitions found for {fiber_id}",
                    fiber_id=fiber_id,
                )
            )

    defined_ids = {event.canonical_fiber_id for event in definitions}
    for reallocation in reallocations:
        if reallocation.canonical_id not in defined_ids:
            issues.append(
                HistoricalLedgerIssue(
                    kind=HistoricalIssueKind.RECONCILIATION_TARGET_ORPHAN,
                    message=f"Reconciliation target is never defined: {reallocation.canonical_id}",
                    source_path=reallocation.reconciliation_path,
                    fiber_id=reallocation.canonical_id,
                )
            )

    orphan_seen: set[tuple[str, str]] = set()
    for event in events:
        if event.role not in {FiberEventRole.REFERENCE, FiberEventRole.UPDATE}:
            continue
        if event.canonical_fiber_id in defined_ids:
            continue
        key = (event.source_path, event.canonical_fiber_id)
        if key in orphan_seen:
            continue
        orphan_seen.add(key)
        resolution_path = orphan_resolutions.get(event.canonical_fiber_id)
        issues.append(
            HistoricalLedgerIssue(
                kind=HistoricalIssueKind.ORPHAN_REFERENCE,
                message=f"Reference has no canonical definition: {event.canonical_fiber_id}",
                source_path=event.source_path,
                fiber_id=event.canonical_fiber_id,
                resolved=resolution_path is not None,
                resolution=(f"explicit non-retroactive orphan disposition in {resolution_path}" if resolution_path else None),
            )
        )

    unresolved = [issue for issue in issues if not issue.resolved]
    if any(issue.kind == HistoricalIssueKind.RECONCILIATION_CHRONOLOGY_INVALID for issue in unresolved):
        verdict = HistoricalLedgerVerdict.TRIAL_INVALID
    elif any(
        issue.kind in {
            HistoricalIssueKind.INVALID_JSON,
            HistoricalIssueKind.SOURCE_MISSING,
            HistoricalIssueKind.SOURCE_BLOB_MISMATCH,
            HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD,
            HistoricalIssueKind.RECONCILIATION_SCOPE_UNVERIFIABLE,
        }
        for issue in unresolved
    ):
        verdict = HistoricalLedgerVerdict.CANNOT_CHECK
    elif unresolved:
        verdict = HistoricalLedgerVerdict.CONFLICTED
    elif reallocations or any(issue.resolved for issue in issues):
        verdict = HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    else:
        verdict = HistoricalLedgerVerdict.CONSISTENT

    artifact_tuple = tuple(sorted(artifacts, key=lambda item: item.path))
    event_tuple = tuple(events)
    reallocation_tuple = tuple(sorted(reallocations, key=lambda item: (item.source_path, item.historical_id)))
    issue_tuple = tuple(sorted(issues, key=lambda item: (item.kind.value, item.source_path or "", item.fiber_id or "", item.message)))
    return HistoricalMetaLedgerReport(
        verdict=verdict,
        artifacts=artifact_tuple,
        events=event_tuple,
        reallocations=reallocation_tuple,
        issues=issue_tuple,
        canonical_fibers=_canonical_state(events),
        ledger_digest=_digest(artifact_tuple, event_tuple, reallocation_tuple, issue_tuple),
    )
