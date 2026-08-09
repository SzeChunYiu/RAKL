from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class MemoryViewKind(str, Enum):
    CANONICAL = "CANONICAL"
    DERIVED_LOSSLESS = "DERIVED_LOSSLESS"
    DERIVED_LOSSY = "DERIVED_LOSSY"


class MemoryViewVerdict(str, Enum):
    VALID_CANONICAL = "VALID_CANONICAL"
    SOURCE_REHYDRATABLE = "SOURCE_REHYDRATABLE"
    REGENERATION_VERIFIED = "REGENERATION_VERIFIED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class SourcePin:
    record_id: str
    payload_hash: str

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("source record_id cannot be empty")
        if not self.payload_hash:
            raise ValueError("source payload_hash cannot be empty")


@dataclass(frozen=True)
class MemoryView:
    """One canonical record or a materialized view over other memory records.

    Derived views are representation/cache objects only.  They may preserve authority
    certificates already present in their sources, but this support layer never creates
    new scientific authority.  New epistemic claims belong in canonical memory with
    their own evidence lineage.
    """

    record_id: str
    payload_hash: str
    kind: MemoryViewKind
    source_pins: tuple[SourcePin, ...] = ()
    transform_id: str | None = None
    erasure_tags: tuple[str, ...] = ()
    authority_certificates: tuple[str, ...] = ()
    required_canonical_ids: tuple[str, ...] = ()
    reconstruction_witness_id: str | None = None
    reconstruction_verified: bool = False

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id cannot be empty")
        if not self.payload_hash:
            raise ValueError("payload_hash cannot be empty")
        if len({pin.record_id for pin in self.source_pins}) != len(self.source_pins):
            raise ValueError("duplicate source pin")
        if len(set(self.authority_certificates)) != len(self.authority_certificates):
            raise ValueError("duplicate authority certificate")
        if len(set(self.required_canonical_ids)) != len(self.required_canonical_ids):
            raise ValueError("duplicate required canonical id")

        if self.kind == MemoryViewKind.CANONICAL:
            if self.source_pins:
                raise ValueError("canonical records cannot depend on derived source pins")
            if self.erasure_tags:
                raise ValueError("canonical records cannot declare derivation erasures")
            if self.reconstruction_witness_id or self.reconstruction_verified:
                raise ValueError("canonical records do not use reconstruction witnesses")
        else:
            if not self.source_pins:
                raise ValueError("derived views require source_pins")
            if not self.transform_id:
                raise ValueError("derived views require transform_id")

        if self.kind == MemoryViewKind.DERIVED_LOSSY:
            if not self.erasure_tags:
                raise ValueError("lossy views require an erasure ledger")
            if self.reconstruction_verified:
                raise ValueError("lossy views cannot claim exact reconstruction")
            if self.reconstruction_witness_id:
                raise ValueError("lossy views cannot carry exact reconstruction witnesses")

        if self.reconstruction_verified and not self.reconstruction_witness_id:
            raise ValueError("verified reconstruction requires reconstruction_witness_id")
        if self.reconstruction_witness_id and not self.reconstruction_verified:
            raise ValueError("reconstruction_witness_id requires reconstruction_verified=True")


@dataclass(frozen=True)
class MemoryViewReport:
    view_id: str
    verdict: MemoryViewVerdict
    canonical_root_ids: tuple[str, ...]
    rehydration_order: tuple[str, ...]
    issues: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return self.verdict != MemoryViewVerdict.INVALID


def _registry(views: Iterable[MemoryView]) -> dict[str, MemoryView]:
    pool = tuple(views)
    result = {view.record_id: view for view in pool}
    if len(result) != len(pool):
        raise ValueError("duplicate memory view record_id")
    return result


def validate_memory_view(
    view_id: str,
    views: Iterable[MemoryView],
) -> MemoryViewReport:
    """Validate lineage and reconstructability claims for a memory view.

    The procedure verifies only metadata contracts: pinned immutable source identity,
    acyclic transitive source closure, erasure/reconstruction declarations, reachable
    required canonical roots, and representation-level authority non-escalation.
    It does not execute transforms or inspect source payload semantics.
    """

    registry = _registry(views)
    if view_id not in registry:
        raise KeyError(view_id)

    target = registry[view_id]
    issues: set[str] = set()
    roots: set[str] = set()
    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(current_id: str) -> None:
        if current_id in visited:
            return
        if current_id in visiting:
            issues.add("source_cycle")
            return
        visiting.add(current_id)
        current = registry[current_id]
        if current.kind == MemoryViewKind.CANONICAL:
            roots.add(current_id)
        else:
            direct_authority: set[str] = set()
            for pin in sorted(current.source_pins, key=lambda item: item.record_id):
                source = registry.get(pin.record_id)
                if source is None:
                    issues.add(f"dangling_source:{pin.record_id}")
                    continue
                if source.payload_hash != pin.payload_hash:
                    issues.add(f"source_hash_mismatch:{pin.record_id}")
                direct_authority.update(source.authority_certificates)
                visit(pin.record_id)
            unsupported = set(current.authority_certificates) - direct_authority
            for certificate in sorted(unsupported):
                issues.add(f"authority_escalation:{certificate}")
        visiting.remove(current_id)
        visited.add(current_id)
        order.append(current_id)

    visit(view_id)

    missing_required = set(target.required_canonical_ids) - roots
    for record_id in sorted(missing_required):
        issues.add(f"required_canonical_unreachable:{record_id}")

    if issues:
        return MemoryViewReport(
            view_id=view_id,
            verdict=MemoryViewVerdict.INVALID,
            canonical_root_ids=tuple(sorted(roots)),
            rehydration_order=tuple(order),
            issues=tuple(sorted(issues)),
        )

    if target.kind == MemoryViewKind.CANONICAL:
        verdict = MemoryViewVerdict.VALID_CANONICAL
    elif target.reconstruction_verified:
        verdict = MemoryViewVerdict.REGENERATION_VERIFIED
    else:
        verdict = MemoryViewVerdict.SOURCE_REHYDRATABLE

    return MemoryViewReport(
        view_id=view_id,
        verdict=verdict,
        canonical_root_ids=tuple(sorted(roots)),
        rehydration_order=tuple(order),
        issues=(),
    )


def canonical_source_closure(
    view_id: str,
    views: Iterable[MemoryView],
) -> tuple[str, ...]:
    """Return canonical roots only after the complete lineage validates."""

    report = validate_memory_view(view_id, views)
    if not report.valid:
        raise ValueError(f"invalid memory view {view_id}: {report.issues}")
    return report.canonical_root_ids
