from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple


META_FIBER_PATTERN = re.compile(r"\bMETA_N(?P<slot>\d{3,})_[A-Z0-9_]+\b")


@dataclass(frozen=True)
class MetaFiberOccurrence:
    fiber_id: str
    slot: int
    source_path: str
    source_sha256: str
    line_number: int
    line_sha256: str


@dataclass(frozen=True)
class MetaFiberLedger:
    occurrences: Tuple[MetaFiberOccurrence, ...]
    fiber_ids: Tuple[str, ...]
    slots: Tuple[Tuple[int, Tuple[str, ...]], ...]
    source_files: Tuple[str, ...]

    @property
    def namespace_collisions(self) -> Tuple[Tuple[int, Tuple[str, ...]], ...]:
        return tuple((slot, ids) for slot, ids in self.slots if len(ids) > 1)

    @property
    def grants_identity_reconciliation(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_meta_fiber_ledger(
    root: Path,
    *,
    include_roots: Iterable[str] = ("research", "docs"),
    suffixes: Tuple[str, ...] = (".json", ".md"),
) -> MetaFiberLedger:
    """Compile literal META_N identifiers from immutable repository ledgers.

    Compilation is intentionally syntactic. It inventories occurrences, source
    hashes, line numbers, and namespace-slot multiplicity; it does not infer
    semantic equivalence and therefore cannot silently reconcile collisions.
    """
    root = Path(root).resolve()
    occurrences: list[MetaFiberOccurrence] = []
    source_files: set[str] = set()

    for relative_root in include_roots:
        base = (root / relative_root).resolve()
        try:
            base.relative_to(root)
        except ValueError as exc:
            raise ValueError("include root escapes repository root") from exc
        if not base.exists():
            continue
        for path in sorted(p for p in base.rglob("*") if p.is_file() and p.suffix in suffixes):
            raw = path.read_bytes()
            source_hash = _sha256(raw)
            relative = path.relative_to(root).as_posix()
            source_files.add(relative)
            text = raw.decode("utf-8")
            for line_number, line in enumerate(text.splitlines(), start=1):
                line_hash = _sha256(line.encode("utf-8"))
                for match in META_FIBER_PATTERN.finditer(line):
                    fiber_id = match.group(0)
                    occurrences.append(
                        MetaFiberOccurrence(
                            fiber_id=fiber_id,
                            slot=int(match.group("slot")),
                            source_path=relative,
                            source_sha256=source_hash,
                            line_number=line_number,
                            line_sha256=line_hash,
                        )
                    )

    occurrences.sort(
        key=lambda item: (
            item.fiber_id,
            item.source_path,
            item.line_number,
            item.line_sha256,
        )
    )
    fiber_ids = tuple(sorted({item.fiber_id for item in occurrences}))
    by_slot: dict[int, set[str]] = {}
    for fiber_id in fiber_ids:
        match = META_FIBER_PATTERN.fullmatch(fiber_id)
        if match is None:
            continue
        by_slot.setdefault(int(match.group("slot")), set()).add(fiber_id)
    slots = tuple((slot, tuple(sorted(ids))) for slot, ids in sorted(by_slot.items()))
    return MetaFiberLedger(
        occurrences=tuple(occurrences),
        fiber_ids=fiber_ids,
        slots=slots,
        source_files=tuple(sorted(source_files)),
    )
