"""Registry-bound framework closure certificates.

Paper VI and the framework use *bounded closure*, never global completeness.
A sentence such as "all registered mechanics are closed" is meaningful only
relative to an exact mechanic roster at an exact subject/cutoff.  Adding a new
mechanic candidate must therefore invalidate the old closure certificate
without rewriting its historical truth.

This module is deliberately authority-neutral.  A closure certificate records
engineering/research bookkeeping only; it never mints scientific authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Iterable, Tuple


class ClosureVerdict(str, Enum):
    CLOSED_AT_REGISTERED_CUTOFF = "CLOSED_AT_REGISTERED_CUTOFF"
    OPEN_AT_REGISTERED_CUTOFF = "OPEN_AT_REGISTERED_CUTOFF"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class MechanicClosureRecord:
    mechanic_id: str
    implementation_present: bool
    tests_present: bool
    evidence_present: bool
    paper_owner_present: bool
    open_question_registered: bool

    def __post_init__(self) -> None:
        if not self.mechanic_id.strip():
            raise ValueError("mechanic_id cannot be blank")

    @property
    def locally_closed(self) -> bool:
        return all(
            (
                self.implementation_present,
                self.tests_present,
                self.evidence_present,
                self.paper_owner_present,
                self.open_question_registered,
            )
        )


@dataclass(frozen=True)
class BoundedClosureCertificate:
    subject_sha: str
    cutoff: str
    registry_hash: str
    mechanic_ids: Tuple[str, ...]
    closed_mechanic_ids: Tuple[str, ...]
    verdict: ClosureVerdict

    @property
    def global_completeness_claimed(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    def valid_for(self, records: Iterable[MechanicClosureRecord]) -> bool:
        records = tuple(records)
        return (
            self.registry_hash == mechanic_registry_digest(records)
            and self.mechanic_ids == tuple(sorted(record.mechanic_id for record in records))
        )


def mechanic_registry_digest(records: Iterable[MechanicClosureRecord]) -> str:
    records = tuple(records)
    ids = [record.mechanic_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("mechanic registry contains duplicate ids")
    canonical = tuple(
        sorted(
            (
                record.mechanic_id,
                record.implementation_present,
                record.tests_present,
                record.evidence_present,
                record.paper_owner_present,
                record.open_question_registered,
            )
            for record in records
        )
    )
    return sha256(repr(("RAKL_BOUNDED_CLOSURE_REGISTRY_V1", canonical)).encode()).hexdigest()


def assess_bounded_closure(
    records: Iterable[MechanicClosureRecord],
    *,
    subject_sha: str,
    cutoff: str,
) -> BoundedClosureCertificate:
    records = tuple(records)
    if not subject_sha.strip() or not cutoff.strip():
        raise ValueError("bounded closure requires exact subject_sha and cutoff")
    if not records:
        return BoundedClosureCertificate(
            subject_sha=subject_sha,
            cutoff=cutoff,
            registry_hash=mechanic_registry_digest(records),
            mechanic_ids=(),
            closed_mechanic_ids=(),
            verdict=ClosureVerdict.CANNOT_CHECK,
        )

    ids = tuple(sorted(record.mechanic_id for record in records))
    closed = tuple(sorted(record.mechanic_id for record in records if record.locally_closed))
    verdict = (
        ClosureVerdict.CLOSED_AT_REGISTERED_CUTOFF
        if len(closed) == len(ids)
        else ClosureVerdict.OPEN_AT_REGISTERED_CUTOFF
    )
    return BoundedClosureCertificate(
        subject_sha=subject_sha,
        cutoff=cutoff,
        registry_hash=mechanic_registry_digest(records),
        mechanic_ids=ids,
        closed_mechanic_ids=closed,
        verdict=verdict,
    )
