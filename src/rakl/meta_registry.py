from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


_FIBER_ID_RE = re.compile(r"^META_N(?P<slot>\d{3,})_[A-Z0-9_]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RegistryIssueKind(str, Enum):
    INVALID_FIBER_ID = "INVALID_FIBER_ID"
    INVALID_SOURCE_HASH = "INVALID_SOURCE_HASH"
    SOURCE_IDENTITY_CONFLICT = "SOURCE_IDENTITY_CONFLICT"
    NAMESPACE_SLOT_COLLISION = "NAMESPACE_SLOT_COLLISION"
    DEFINITION_CONFLICT = "DEFINITION_CONFLICT"
    ORPHAN_REFERENCE = "ORPHAN_REFERENCE"
    SUPERSESSION_TARGET_ORPHAN = "SUPERSESSION_TARGET_ORPHAN"
    SUPERSESSION_CYCLE = "SUPERSESSION_CYCLE"
    ALIAS_TARGET_ORPHAN = "ALIAS_TARGET_ORPHAN"
    ALIAS_SOURCE_ORPHAN = "ALIAS_SOURCE_ORPHAN"
    ALIAS_CYCLE = "ALIAS_CYCLE"
    ALIAS_CHRONOLOGY_UNKNOWN = "ALIAS_CHRONOLOGY_UNKNOWN"
    POSTHOC_ALIAS = "POSTHOC_ALIAS"


class RegistryVerdict(str, Enum):
    CONSISTENT = "CONSISTENT"
    CONSISTENT_WITH_RECONCILIATION_HISTORY = "CONSISTENT_WITH_RECONCILIATION_HISTORY"
    CONFLICTED = "CONFLICTED"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class MetaFiberDefinition:
    fiber_id: str
    question: str
    source_id: str
    source_sha256: str
    sequence: int
    state: str = "OPEN"
    supersedes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class MetaFiberReference:
    reference_id: str
    fiber_id: str
    source_id: str
    source_sha256: str
    sequence: int


@dataclass(frozen=True)
class FiberAlias:
    alias_id: str
    source_fiber_id: str
    target_fiber_id: str
    source_id: str
    source_sha256: str
    sequence: int
    frozen_before_use: Optional[bool]


@dataclass(frozen=True)
class RegistryIssue:
    kind: RegistryIssueKind
    subject: str
    source_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]
    resolved_by: Tuple[str, ...] = ()

    @property
    def resolved(self) -> bool:
        return bool(self.resolved_by)


@dataclass(frozen=True)
class MetaFiberRegistryReport:
    verdict: RegistryVerdict
    canonical_definitions: Tuple[MetaFiberDefinition, ...]
    references: Tuple[MetaFiberReference, ...]
    aliases: Tuple[FiberAlias, ...]
    issues: Tuple[RegistryIssue, ...]
    canonical_id_map: Tuple[Tuple[str, str], ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def establishes_framework_saturation(self) -> bool:
        return False

    @property
    def eligible_for_saturation_bookkeeping(self) -> bool:
        return self.verdict in {
            RegistryVerdict.CONSISTENT,
            RegistryVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY,
        }


def fiber_namespace_slot(fiber_id: str) -> Optional[int]:
    match = _FIBER_ID_RE.fullmatch(fiber_id)
    if not match:
        return None
    return int(match.group("slot"))


def _valid_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))


def _source_record_pairs(definitions, references, aliases):
    for item in definitions:
        yield item.source_id, item.source_sha256
    for item in references:
        yield item.source_id, item.source_sha256
    for item in aliases:
        yield item.source_id, item.source_sha256


def _cycles(graph: dict[str, Tuple[str, ...]]) -> Tuple[Tuple[str, ...], ...]:
    found: set[Tuple[str, ...]] = set()
    visited: set[str] = set()
    stack: list[str] = []
    active: set[str] = set()

    def canonical_cycle(nodes: list[str]) -> Tuple[str, ...]:
        core = nodes[:-1]
        rotations = [tuple(core[i:] + core[:i]) for i in range(len(core))]
        best = min(rotations)
        return best + (best[0],)

    def visit(node: str) -> None:
        if node in active:
            idx = stack.index(node)
            found.add(canonical_cycle(stack[idx:] + [node]))
            return
        if node in visited:
            return
        visited.add(node)
        active.add(node)
        stack.append(node)
        for nxt in sorted(graph.get(node, ())):
            visit(nxt)
        stack.pop()
        active.remove(node)

    for node in sorted(graph):
        visit(node)
    return tuple(sorted(found))


def reconcile_meta_fiber_registry(
    definitions: Tuple[MetaFiberDefinition, ...],
    references: Tuple[MetaFiberReference, ...] = (),
    aliases: Tuple[FiberAlias, ...] = (),
) -> MetaFiberRegistryReport:
    """Validate a proposed meta-fiber registry without inferring semantic equivalence.

    The numeric META_N### slot is treated as a namespace resource in addition to
    the complete string identifier. Distinct full identifiers sharing one slot
    are blocking unless explicit, pre-use aliases reconcile all but one of them
    onto separately defined collision-free canonical identifiers.
    """

    definitions = tuple(sorted(definitions, key=lambda x: (x.fiber_id, x.sequence, x.source_id, x.source_sha256, x.question)))
    references = tuple(sorted(references, key=lambda x: (x.reference_id, x.sequence, x.source_id, x.fiber_id)))
    aliases = tuple(sorted(aliases, key=lambda x: (x.alias_id, x.sequence, x.source_id, x.source_fiber_id, x.target_fiber_id)))
    issues: list[RegistryIssue] = []

    for item in (*definitions, *references):
        if fiber_namespace_slot(item.fiber_id) is None:
            issues.append(RegistryIssue(RegistryIssueKind.INVALID_FIBER_ID, item.fiber_id, (item.source_id,), ("fiber_id_format_invalid",)))
    for alias in aliases:
        for label, value in (("alias_source", alias.source_fiber_id), ("alias_target", alias.target_fiber_id)):
            if fiber_namespace_slot(value) is None:
                issues.append(RegistryIssue(RegistryIssueKind.INVALID_FIBER_ID, value, (alias.source_id,), (f"{label}_fiber_id_format_invalid",)))

    source_hashes: dict[str, set[str]] = {}
    for source_id, source_hash in _source_record_pairs(definitions, references, aliases):
        if not source_id or not _valid_sha256(source_hash):
            issues.append(RegistryIssue(RegistryIssueKind.INVALID_SOURCE_HASH, source_id or "<missing-source-id>", (source_id,), ("source_id_or_sha256_invalid",)))
        source_hashes.setdefault(source_id, set()).add(source_hash)
    for source_id, hashes in sorted(source_hashes.items()):
        if source_id and len(hashes) > 1:
            issues.append(RegistryIssue(RegistryIssueKind.SOURCE_IDENTITY_CONFLICT, source_id, (source_id,), tuple(f"sha256:{h}" for h in sorted(hashes))))

    definitions_by_id: dict[str, list[MetaFiberDefinition]] = {}
    for definition in definitions:
        definitions_by_id.setdefault(definition.fiber_id, []).append(definition)

    canonical_by_id: dict[str, MetaFiberDefinition] = {}
    for fiber_id, group in sorted(definitions_by_id.items()):
        signatures = {(d.question.strip(), tuple(sorted(d.supersedes))) for d in group}
        if len(signatures) > 1:
            issues.append(RegistryIssue(
                RegistryIssueKind.DEFINITION_CONFLICT,
                fiber_id,
                tuple(sorted({d.source_id for d in group})),
                tuple(sorted({f"question:{d.question.strip()}|supersedes:{','.join(sorted(d.supersedes))}" for d in group})),
            ))
        canonical_by_id[fiber_id] = min(group, key=lambda d: (d.sequence, d.source_id, d.source_sha256, d.question))

    valid_aliases: dict[str, FiberAlias] = {}
    alias_graph: dict[str, Tuple[str, ...]] = {}
    for alias in aliases:
        if alias.frozen_before_use is None:
            issues.append(RegistryIssue(RegistryIssueKind.ALIAS_CHRONOLOGY_UNKNOWN, alias.alias_id, (alias.source_id,), ("alias_freeze_chronology_unknown",)))
            continue
        if alias.frozen_before_use is False:
            issues.append(RegistryIssue(RegistryIssueKind.POSTHOC_ALIAS, alias.alias_id, (alias.source_id,), ("posthoc_alias_definition",)))
            continue
        if alias.source_fiber_id not in canonical_by_id:
            issues.append(RegistryIssue(RegistryIssueKind.ALIAS_SOURCE_ORPHAN, alias.source_fiber_id, (alias.source_id,), ("alias_source_has_no_definition",)))
            continue
        if alias.target_fiber_id not in canonical_by_id:
            issues.append(RegistryIssue(RegistryIssueKind.ALIAS_TARGET_ORPHAN, alias.target_fiber_id, (alias.source_id,), ("alias_target_has_no_definition",)))
            continue
        previous = valid_aliases.get(alias.source_fiber_id)
        if previous is not None and previous.target_fiber_id != alias.target_fiber_id:
            issues.append(RegistryIssue(RegistryIssueKind.DEFINITION_CONFLICT, alias.source_fiber_id, tuple(sorted({previous.source_id, alias.source_id})), ("one_alias_source_maps_to_multiple_targets",)))
            continue
        valid_aliases[alias.source_fiber_id] = alias
        alias_graph[alias.source_fiber_id] = (alias.target_fiber_id,)

    for cycle in _cycles(alias_graph):
        issues.append(RegistryIssue(RegistryIssueKind.ALIAS_CYCLE, " -> ".join(cycle), tuple(sorted({valid_aliases[n].source_id for n in cycle[:-1] if n in valid_aliases})), ("alias_cycle_detected",)))

    def resolve_alias(fiber_id: str) -> str:
        seen: set[str] = set()
        current = fiber_id
        while current in valid_aliases and current not in seen:
            seen.add(current)
            current = valid_aliases[current].target_fiber_id
        return current

    slot_groups: dict[int, set[str]] = {}
    for fiber_id in canonical_by_id:
        slot = fiber_namespace_slot(fiber_id)
        if slot is not None:
            slot_groups.setdefault(slot, set()).add(fiber_id)
    for slot, ids in sorted(slot_groups.items()):
        if len(ids) <= 1:
            continue
        unresolved = []
        resolved_alias_ids = []
        target_slots: dict[int, list[str]] = {}
        for fiber_id in sorted(ids):
            resolved = resolve_alias(fiber_id)
            resolved_slot = fiber_namespace_slot(resolved)
            if resolved == fiber_id:
                unresolved.append(fiber_id)
            else:
                resolved_alias_ids.append(valid_aliases[fiber_id].alias_id)
            if resolved_slot is not None:
                target_slots.setdefault(resolved_slot, []).append(fiber_id)
        aliases_resolve_collision = len(unresolved) <= 1 and all(len(v) == 1 for v in target_slots.values())
        issues.append(RegistryIssue(
            RegistryIssueKind.NAMESPACE_SLOT_COLLISION,
            f"META_N{slot:03d}",
            tuple(sorted({canonical_by_id[f].source_id for f in ids})),
            tuple(f"fiber_id:{fiber_id}" for fiber_id in sorted(ids)),
            tuple(sorted(resolved_alias_ids)) if aliases_resolve_collision else (),
        ))

    for reference in references:
        if reference.fiber_id not in canonical_by_id:
            issues.append(RegistryIssue(RegistryIssueKind.ORPHAN_REFERENCE, reference.fiber_id, (reference.source_id,), (f"reference_id:{reference.reference_id}",)))

    supersession_graph: dict[str, Tuple[str, ...]] = {}
    for definition in canonical_by_id.values():
        valid_targets = []
        for target in definition.supersedes:
            if target not in canonical_by_id:
                issues.append(RegistryIssue(RegistryIssueKind.SUPERSESSION_TARGET_ORPHAN, target, (definition.source_id,), (f"superseded_by:{definition.fiber_id}",)))
            else:
                valid_targets.append(target)
        if valid_targets:
            supersession_graph[definition.fiber_id] = tuple(sorted(valid_targets))
    for cycle in _cycles(supersession_graph):
        issues.append(RegistryIssue(RegistryIssueKind.SUPERSESSION_CYCLE, " -> ".join(cycle), tuple(sorted({canonical_by_id[n].source_id for n in cycle[:-1] if n in canonical_by_id})), ("supersession_cycle_detected",)))

    invalid_kinds = {RegistryIssueKind.INVALID_FIBER_ID, RegistryIssueKind.POSTHOC_ALIAS}
    cannot_check_kinds = {RegistryIssueKind.INVALID_SOURCE_HASH, RegistryIssueKind.ALIAS_CHRONOLOGY_UNKNOWN}
    unresolved = [issue for issue in issues if not issue.resolved]
    if any(issue.kind in invalid_kinds for issue in unresolved):
        verdict = RegistryVerdict.TRIAL_INVALID
    elif any(issue.kind in cannot_check_kinds for issue in unresolved):
        verdict = RegistryVerdict.CANNOT_CHECK
    elif unresolved:
        verdict = RegistryVerdict.CONFLICTED
    elif issues:
        verdict = RegistryVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    else:
        verdict = RegistryVerdict.CONSISTENT

    canonical_map = tuple(sorted((fiber_id, resolve_alias(fiber_id)) for fiber_id in canonical_by_id))
    sorted_issues = tuple(sorted(issues, key=lambda i: (i.kind.value, i.subject, i.source_ids, i.reasons, i.resolved_by)))
    reasons = (
        f"definitions:{len(canonical_by_id)}",
        f"references:{len(references)}",
        f"aliases:{len(aliases)}",
        f"issues:{len(sorted_issues)}",
        f"unresolved_issues:{sum(1 for issue in sorted_issues if not issue.resolved)}",
        "semantic_similarity_never_auto_merges_identity",
        "registry_reconciliation_never_grants_scientific_or_method_authority",
    )
    return MetaFiberRegistryReport(
        verdict=verdict,
        canonical_definitions=tuple(sorted(canonical_by_id.values(), key=lambda d: d.fiber_id)),
        references=references,
        aliases=aliases,
        issues=sorted_issues,
        canonical_id_map=canonical_map,
        reasons=reasons,
    )
