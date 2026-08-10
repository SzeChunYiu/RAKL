from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import zlib


class ArchiveCodec(str, Enum):
    RAW = "RAW"
    ZLIB = "ZLIB"


class ArchiveTier(str, Enum):
    HOT = "HOT"
    COLD = "COLD"


@dataclass(frozen=True)
class ArchiveRecord:
    record_id: str
    payload_hash: str
    raw_bytes: int
    insertion_index: int


@dataclass(frozen=True)
class StoredBlob:
    payload_hash: str
    raw_bytes: int
    stored_bytes: int
    codec: ArchiveCodec
    stored_payload: bytes
    tier: ArchiveTier


@dataclass(frozen=True)
class ArchivePutResult:
    record_id: str
    payload_hash: str
    new_logical_record: bool
    new_physical_blob: bool
    raw_bytes_delta: int
    stored_bytes_delta: int
    codec: ArchiveCodec


@dataclass(frozen=True)
class ArchiveMetrics:
    logical_records: int
    unique_blobs: int
    logical_raw_bytes: int
    unique_raw_bytes: int
    stored_physical_bytes: int
    hot_stored_bytes: int
    cold_stored_bytes: int
    hot_unique_blobs: int
    cold_unique_blobs: int
    deduplicated_raw_bytes: int
    compression_saved_bytes: int
    combined_saved_bytes: int
    storage_to_logical_ratio: float


@dataclass(frozen=True)
class HotArchivePolicy:
    max_hot_stored_bytes: int
    max_hot_unique_blobs: int

    def __post_init__(self) -> None:
        if self.max_hot_stored_bytes < 0 or self.max_hot_unique_blobs < 0:
            raise ValueError("hot archive capacity cannot be negative")


class ColdDemotionVerdict(str, Enum):
    ALREADY_WITHIN_CAPACITY = "ALREADY_WITHIN_CAPACITY"
    DEMOTION_PLAN_AVAILABLE = "DEMOTION_PLAN_AVAILABLE"
    CANNOT_SATISFY_WITH_PROTECTED_SET = "CANNOT_SATISFY_WITH_PROTECTED_SET"


@dataclass(frozen=True)
class ColdDemotionPlan:
    verdict: ColdDemotionVerdict
    demote_payload_hashes: tuple[str, ...]
    projected_hot_stored_bytes: int
    projected_hot_unique_blobs: int
    protected_payload_hashes: tuple[str, ...]


class ContentAddressedArchive:
    """Small reference backend for canonical evidence storage semantics.

    Identity is SHA-256 over the *raw* payload. Physical representation may be
    losslessly compressed, but compression never changes the content identity.
    Multiple logical records may reference one physical blob. Cold demotion changes
    storage temperature/accounting only; records and rehydration remain available.

    This is a deterministic in-memory reference implementation, not a cloud/object
    store. Production adapters should preserve these semantics.
    """

    def __init__(self) -> None:
        self._records: dict[str, ArchiveRecord] = {}
        self._blobs: dict[str, StoredBlob] = {}
        self._next_index = 0

    @staticmethod
    def digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _encode(payload: bytes) -> tuple[ArchiveCodec, bytes]:
        compressed = zlib.compress(payload, level=9)
        if len(compressed) < len(payload):
            return ArchiveCodec.ZLIB, compressed
        return ArchiveCodec.RAW, payload

    @property
    def records(self) -> tuple[ArchiveRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.insertion_index))

    @property
    def blobs(self) -> tuple[StoredBlob, ...]:
        return tuple(sorted(self._blobs.values(), key=lambda item: item.payload_hash))

    def put(self, record_id: str, payload: bytes) -> ArchivePutResult:
        if not record_id:
            raise ValueError("record_id is required")
        if not isinstance(payload, bytes):
            raise TypeError("payload must be bytes")

        payload_hash = self.digest(payload)
        existing_record = self._records.get(record_id)
        if existing_record is not None:
            if existing_record.payload_hash != payload_hash:
                raise ValueError("canonical record_id cannot be rebound to different content")
            blob = self._blobs[payload_hash]
            return ArchivePutResult(
                record_id,
                payload_hash,
                False,
                False,
                0,
                0,
                blob.codec,
            )

        new_blob = payload_hash not in self._blobs
        if new_blob:
            codec, stored = self._encode(payload)
            self._blobs[payload_hash] = StoredBlob(
                payload_hash=payload_hash,
                raw_bytes=len(payload),
                stored_bytes=len(stored),
                codec=codec,
                stored_payload=stored,
                tier=ArchiveTier.HOT,
            )
        blob = self._blobs[payload_hash]
        self._records[record_id] = ArchiveRecord(
            record_id=record_id,
            payload_hash=payload_hash,
            raw_bytes=len(payload),
            insertion_index=self._next_index,
        )
        self._next_index += 1
        return ArchivePutResult(
            record_id=record_id,
            payload_hash=payload_hash,
            new_logical_record=True,
            new_physical_blob=new_blob,
            raw_bytes_delta=len(payload),
            stored_bytes_delta=(blob.stored_bytes if new_blob else 0),
            codec=blob.codec,
        )

    def rehydrate(self, record_id: str) -> bytes:
        record = self._records[record_id]
        blob = self._blobs[record.payload_hash]
        if blob.codec is ArchiveCodec.RAW:
            payload = blob.stored_payload
        elif blob.codec is ArchiveCodec.ZLIB:
            payload = zlib.decompress(blob.stored_payload)
        else:  # pragma: no cover - defensive future-proofing
            raise ValueError(f"unsupported archive codec: {blob.codec}")
        if len(payload) != blob.raw_bytes:
            raise ValueError("rehydrated payload length mismatch")
        if self.digest(payload) != blob.payload_hash:
            raise ValueError("rehydrated payload hash mismatch")
        return payload

    def metrics(self) -> ArchiveMetrics:
        logical_raw = sum(record.raw_bytes for record in self._records.values())
        unique_raw = sum(blob.raw_bytes for blob in self._blobs.values())
        stored = sum(blob.stored_bytes for blob in self._blobs.values())
        hot = tuple(blob for blob in self._blobs.values() if blob.tier is ArchiveTier.HOT)
        cold = tuple(blob for blob in self._blobs.values() if blob.tier is ArchiveTier.COLD)
        dedup_saved = logical_raw - unique_raw
        compression_saved = unique_raw - stored
        combined_saved = logical_raw - stored
        return ArchiveMetrics(
            logical_records=len(self._records),
            unique_blobs=len(self._blobs),
            logical_raw_bytes=logical_raw,
            unique_raw_bytes=unique_raw,
            stored_physical_bytes=stored,
            hot_stored_bytes=sum(blob.stored_bytes for blob in hot),
            cold_stored_bytes=sum(blob.stored_bytes for blob in cold),
            hot_unique_blobs=len(hot),
            cold_unique_blobs=len(cold),
            deduplicated_raw_bytes=dedup_saved,
            compression_saved_bytes=compression_saved,
            combined_saved_bytes=combined_saved,
            storage_to_logical_ratio=(stored / logical_raw if logical_raw else 0.0),
        )

    def plan_cold_demotion(
        self,
        policy: HotArchivePolicy,
        *,
        protected_record_ids: tuple[str, ...] = (),
    ) -> ColdDemotionPlan:
        missing = tuple(record_id for record_id in protected_record_ids if record_id not in self._records)
        if missing:
            raise KeyError(f"unknown protected record ids: {missing}")

        protected_hashes = {
            self._records[record_id].payload_hash for record_id in protected_record_ids
        }
        metrics = self.metrics()
        if (
            metrics.hot_stored_bytes <= policy.max_hot_stored_bytes
            and metrics.hot_unique_blobs <= policy.max_hot_unique_blobs
        ):
            return ColdDemotionPlan(
                ColdDemotionVerdict.ALREADY_WITHIN_CAPACITY,
                (),
                metrics.hot_stored_bytes,
                metrics.hot_unique_blobs,
                tuple(sorted(protected_hashes)),
            )

        hot_candidates = [
            blob
            for blob in self._blobs.values()
            if blob.tier is ArchiveTier.HOT and blob.payload_hash not in protected_hashes
        ]
        # Largest-first minimizes the number of hot->cold moves needed to reduce
        # byte pressure; hash provides deterministic tie-breaking.
        hot_candidates.sort(key=lambda blob: (-blob.stored_bytes, blob.payload_hash))

        projected_bytes = metrics.hot_stored_bytes
        projected_blobs = metrics.hot_unique_blobs
        demote: list[str] = []
        for blob in hot_candidates:
            if (
                projected_bytes <= policy.max_hot_stored_bytes
                and projected_blobs <= policy.max_hot_unique_blobs
            ):
                break
            demote.append(blob.payload_hash)
            projected_bytes -= blob.stored_bytes
            projected_blobs -= 1

        if (
            projected_bytes <= policy.max_hot_stored_bytes
            and projected_blobs <= policy.max_hot_unique_blobs
        ):
            verdict = ColdDemotionVerdict.DEMOTION_PLAN_AVAILABLE
        else:
            verdict = ColdDemotionVerdict.CANNOT_SATISFY_WITH_PROTECTED_SET

        return ColdDemotionPlan(
            verdict,
            tuple(demote),
            projected_bytes,
            projected_blobs,
            tuple(sorted(protected_hashes)),
        )

    def apply_cold_demotion(self, plan: ColdDemotionPlan) -> None:
        if plan.verdict is ColdDemotionVerdict.CANNOT_SATISFY_WITH_PROTECTED_SET:
            raise ValueError("cannot apply an unsatisfied cold demotion plan")
        for payload_hash in plan.demote_payload_hashes:
            blob = self._blobs[payload_hash]
            self._blobs[payload_hash] = StoredBlob(
                payload_hash=blob.payload_hash,
                raw_bytes=blob.raw_bytes,
                stored_bytes=blob.stored_bytes,
                codec=blob.codec,
                stored_payload=blob.stored_payload,
                tier=ArchiveTier.COLD,
            )
