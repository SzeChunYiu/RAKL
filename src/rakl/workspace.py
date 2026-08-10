from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping


class WorkspacePartition(str, Enum):
    CORE = "CORE"
    CHALLENGE = "CHALLENGE"
    NOVEL = "NOVEL"
    HISTORY = "HISTORY"


@dataclass(frozen=True)
class WorkspaceCandidate:
    item_id: str
    content_ref: str
    partition: WorkspacePartition
    priority: float
    broadcast_targets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.item_id or not self.content_ref:
            raise ValueError("workspace item identity and content reference are required")
        if self.priority < 0:
            raise ValueError("workspace priority cannot be negative")
        if any(not target for target in self.broadcast_targets):
            raise ValueError("broadcast targets cannot contain empty values")


@dataclass(frozen=True)
class WorkspaceGatePolicy:
    capacity: int
    reservations: tuple[tuple[WorkspacePartition, int], ...] = (
        (WorkspacePartition.CHALLENGE, 1),
        (WorkspacePartition.NOVEL, 1),
        (WorkspacePartition.HISTORY, 1),
    )

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise ValueError("workspace capacity must be positive")
        if len({partition for partition, _ in self.reservations}) != len(self.reservations):
            raise ValueError("workspace reservations cannot repeat a partition")
        if any(count < 0 for _, count in self.reservations):
            raise ValueError("workspace reservations cannot be negative")
        if sum(count for _, count in self.reservations) > self.capacity:
            raise ValueError("workspace reservations exceed capacity")


@dataclass(frozen=True)
class WorkspaceSelectionRecord:
    item_id: str
    partition: WorkspacePartition
    reason: str
    rank: int


@dataclass(frozen=True)
class WorkspaceFrame:
    selected_items: tuple[WorkspaceCandidate, ...]
    broadcast_map: tuple[tuple[str, tuple[str, ...]], ...]
    selection_ledger: tuple[WorkspaceSelectionRecord, ...]
    capacity: int
    lifetime_steps: int = 1

    def __post_init__(self) -> None:
        if len(self.selected_items) > self.capacity:
            raise ValueError("workspace frame exceeds capacity")
        if self.lifetime_steps < 1:
            raise ValueError("workspace lifetime must be positive")

    @property
    def selected_item_ids(self) -> tuple[str, ...]:
        return tuple(item.item_id for item in self.selected_items)


def gate_workspace(
    candidates: Iterable[WorkspaceCandidate],
    policy: WorkspaceGatePolicy,
) -> WorkspaceFrame:
    pool = tuple(candidates)
    if len({item.item_id for item in pool}) != len(pool):
        raise ValueError("duplicate workspace item_id")

    selected: list[WorkspaceCandidate] = []
    ledger: list[WorkspaceSelectionRecord] = []
    selected_ids: set[str] = set()

    for partition, count in policy.reservations:
        options = sorted(
            (item for item in pool if item.partition is partition),
            key=lambda item: (-item.priority, item.item_id),
        )
        if len(options) < count:
            raise ValueError(
                f"workspace cannot satisfy {partition.value} reservation: required {count}, observed {len(options)}"
            )
        for item in options[:count]:
            selected.append(item)
            selected_ids.add(item.item_id)
            ledger.append(
                WorkspaceSelectionRecord(
                    item_id=item.item_id,
                    partition=item.partition,
                    reason="reserved_partition",
                    rank=len(ledger),
                )
            )

    remaining = sorted(
        (item for item in pool if item.item_id not in selected_ids),
        key=lambda item: (-item.priority, item.item_id),
    )
    for item in remaining:
        if len(selected) >= policy.capacity:
            break
        selected.append(item)
        selected_ids.add(item.item_id)
        ledger.append(
            WorkspaceSelectionRecord(
                item_id=item.item_id,
                partition=item.partition,
                reason="global_priority_fill",
                rank=len(ledger),
            )
        )

    broadcast_map = tuple(
        (item.item_id, tuple(dict.fromkeys(item.broadcast_targets)))
        for item in selected
    )
    return WorkspaceFrame(
        selected_items=tuple(selected),
        broadcast_map=broadcast_map,
        selection_ledger=tuple(ledger),
        capacity=policy.capacity,
    )


@dataclass(frozen=True)
class WorkspaceProposal:
    proposal_id: str
    source_item_ids: tuple[str, ...]
    target_operator: str
    payload: str

    def __post_init__(self) -> None:
        if not self.proposal_id or not self.target_operator or not self.payload:
            raise ValueError("proposal identity, target operator and payload are required")
        if not self.source_item_ids:
            raise ValueError("workspace proposal must cite at least one selected item")


def proposals_from_workspace(
    frame: WorkspaceFrame,
    proposal_payloads: Mapping[str, str],
) -> tuple[WorkspaceProposal, ...]:
    selected = set(frame.selected_item_ids)
    proposals: list[WorkspaceProposal] = []
    for item_id, targets in frame.broadcast_map:
        for target in targets:
            key = f"{item_id}:{target}"
            payload = proposal_payloads.get(key)
            if payload is None:
                continue
            if item_id not in selected:
                raise ValueError("proposal source is not selected in workspace")
            proposals.append(
                WorkspaceProposal(
                    proposal_id=f"proposal:{key}",
                    source_item_ids=(item_id,),
                    target_operator=target,
                    payload=payload,
                )
            )
    return tuple(proposals)


class WorkspaceInterventionKind(str, Enum):
    DROP = "DROP"
    SUBSTITUTE = "SUBSTITUTE"
    REWEIGHT = "REWEIGHT"


@dataclass(frozen=True)
class WorkspaceIntervention:
    kind: WorkspaceInterventionKind
    target_item_id: str
    substitute: WorkspaceCandidate | None = None
    weight_multiplier: float | None = None

    def __post_init__(self) -> None:
        if not self.target_item_id:
            raise ValueError("intervention target_item_id cannot be empty")
        if self.kind is WorkspaceInterventionKind.SUBSTITUTE and self.substitute is None:
            raise ValueError("substitution intervention requires a replacement")
        if self.kind is WorkspaceInterventionKind.REWEIGHT:
            if self.weight_multiplier is None or self.weight_multiplier < 0:
                raise ValueError("reweight intervention requires a non-negative multiplier")


def intervene_candidates(
    candidates: Iterable[WorkspaceCandidate],
    intervention: WorkspaceIntervention,
) -> tuple[WorkspaceCandidate, ...]:
    pool = list(candidates)
    matched = False
    output: list[WorkspaceCandidate] = []
    for item in pool:
        if item.item_id != intervention.target_item_id:
            output.append(item)
            continue
        matched = True
        if intervention.kind is WorkspaceInterventionKind.DROP:
            continue
        if intervention.kind is WorkspaceInterventionKind.SUBSTITUTE:
            assert intervention.substitute is not None
            output.append(intervention.substitute)
            continue
        assert intervention.weight_multiplier is not None
        output.append(
            WorkspaceCandidate(
                item_id=item.item_id,
                content_ref=item.content_ref,
                partition=item.partition,
                priority=item.priority * intervention.weight_multiplier,
                broadcast_targets=item.broadcast_targets,
            )
        )
    if not matched:
        raise KeyError(f"workspace intervention target not found: {intervention.target_item_id}")
    return tuple(output)


@dataclass(frozen=True)
class CognitiveProvenanceEdge:
    source_item_id: str
    downstream_proposal_id: str
    intervention_id: str | None = None


@dataclass(frozen=True)
class EvidentialProvenanceEdge:
    evidence_id: str
    claim_id: str
    verification_id: str


def coactivation_pairs(frame: WorkspaceFrame) -> tuple[frozenset[str], ...]:
    """Return co-active pairs only, never compatibility/gluing/authority witnesses."""
    ids = frame.selected_item_ids
    return tuple(
        frozenset((left, right))
        for index, left in enumerate(ids)
        for right in ids[index + 1 :]
    )
