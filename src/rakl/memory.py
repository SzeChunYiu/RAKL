from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MemoryKind(str, Enum):
    SOURCE_PROJECTION = "SOURCE_PROJECTION"
    SEMANTIC_OBJECT = "SEMANTIC_OBJECT"
    RESEARCH_ROUND = "RESEARCH_ROUND"
    EXPERIMENT = "EXPERIMENT"
    FAILURE = "FAILURE"
    REVIEW = "REVIEW"
    METHOD_CHANGE = "METHOD_CHANGE"
    SATURATION = "SATURATION"


class MemoryAuthority(str, Enum):
    RAW = "RAW"
    NORMALIZED = "NORMALIZED"
    PROMOTED = "PROMOTED"
    REFUTED = "REFUTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    kind: MemoryKind
    payload_hash: str
    context_id: str
    authority: MemoryAuthority = MemoryAuthority.RAW
    evidence_ids: tuple[str, ...] = ()
    semantic_tags: tuple[str, ...] = ()
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SupersessionEdge:
    old_record_id: str
    new_record_id: str
    reason: str
    evidence_id: str | None = None


@dataclass
class ResearchMemory:
    """Append-only research memory with explicit supersession.

    Records are never deleted or mutated. A newer result can supersede an older one for
    active selection while preserving the historical record and reason.
    """

    records: dict[str, MemoryRecord] = field(default_factory=dict)
    supersessions: list[SupersessionEdge] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)

    def append(self, record: MemoryRecord) -> None:
        if not record.record_id:
            raise ValueError("record_id cannot be empty")
        if record.record_id in self.records:
            raise ValueError(f"duplicate record_id: {record.record_id}")
        missing_parents = [parent for parent in record.parent_ids if parent not in self.records]
        if missing_parents:
            raise KeyError(f"missing parent records: {missing_parents}")

        self.records[record.record_id] = record
        self.events.append(
            {
                "event": "APPEND",
                "record_id": record.record_id,
                "kind": record.kind.value,
                "authority": record.authority.value,
            }
        )

    def supersede(
        self,
        old_record_id: str,
        new_record_id: str,
        *,
        reason: str,
        evidence_id: str | None = None,
    ) -> None:
        if old_record_id not in self.records:
            raise KeyError(f"missing old record: {old_record_id}")
        if new_record_id not in self.records:
            raise KeyError(f"missing new record: {new_record_id}")
        if old_record_id == new_record_id:
            raise ValueError("a record cannot supersede itself")
        if not reason.strip():
            raise ValueError("supersession reason cannot be empty")

        edge = SupersessionEdge(
            old_record_id=old_record_id,
            new_record_id=new_record_id,
            reason=reason.strip(),
            evidence_id=evidence_id,
        )
        if edge in self.supersessions:
            raise ValueError("duplicate supersession edge")
        self.supersessions.append(edge)
        self.events.append(
            {
                "event": "SUPERSEDE",
                "old_record_id": old_record_id,
                "new_record_id": new_record_id,
                "reason": reason.strip(),
                "evidence_id": evidence_id,
            }
        )

    def superseded_ids(self) -> frozenset[str]:
        return frozenset(edge.old_record_id for edge in self.supersessions)

    def active_records(self) -> list[MemoryRecord]:
        superseded = self.superseded_ids()
        return [
            record
            for record_id, record in self.records.items()
            if record_id not in superseded
        ]

    def records_with_tag(self, tag: str, *, active_only: bool = False) -> list[MemoryRecord]:
        pool = self.active_records() if active_only else list(self.records.values())
        return [record for record in pool if tag in record.semantic_tags]

    def failure_records(self, *, active_only: bool = False) -> list[MemoryRecord]:
        pool = self.active_records() if active_only else list(self.records.values())
        return [record for record in pool if record.kind == MemoryKind.FAILURE]

    def lineage(self, record_id: str) -> list[str]:
        if record_id not in self.records:
            raise KeyError(record_id)

        result: list[str] = []
        seen: set[str] = set()

        def visit(current: str) -> None:
            if current in seen:
                raise ValueError(f"cycle detected in memory lineage at {current}")
            seen.add(current)
            for parent in self.records[current].parent_ids:
                visit(parent)
            result.append(current)

        visit(record_id)
        return result

    def supersession_chain(self, record_id: str) -> list[str]:
        if record_id not in self.records:
            raise KeyError(record_id)
        chain = [record_id]
        current = record_id
        seen = {current}
        while True:
            outgoing = [edge for edge in self.supersessions if edge.old_record_id == current]
            if not outgoing:
                return chain
            if len(outgoing) > 1:
                raise ValueError(
                    f"ambiguous supersession: record {current} has multiple active successors"
                )
            current = outgoing[0].new_record_id
            if current in seen:
                raise ValueError("cycle detected in supersession graph")
            seen.add(current)
            chain.append(current)
