"""Durable append-only episode store - JSONL-on-disk persistence for the
experience substrate (TaskEpisode / Lesson / ExperienceLedger entries) with a
tamper-evident content-hash chain.

The in-process experience substrate (:mod:`rakl.experience_substrate`) has a
strict content/hash contract but no durable cross-session store: P7 runtime
resumption persists only the controller epoch + MetricLedger, and the
content-addressed archive is in-memory. This module closes that gap with the
smallest durable primitive that preserves the existing invariants:

* **Append-only JSONL.** One record per line. Records are never rewritten,
  reordered, or deleted; the file is only ever extended.
* **Hash chain.** Every record embeds the previous record's ``record_hash``
  (empty for the first record), mirroring the research-trace invariant
  ``research_trace_hash_chain_is_tamper_evident``. A bit-flip in any stored
  record, an interior deletion, or a reordering breaks the chain at a specific
  index.
* **Typed verification.** :func:`verify_episode_store` walks the durable bytes
  and returns a typed :class:`ChainVerificationReport` - ``VALID`` /
  ``TAMPERED`` (with the first bad index) / ``TRUNCATED`` / ``CANNOT_CHECK``.
  A missing or unreadable file is ``CANNOT_CHECK``, never "checked and fine";
  no failure mode is collapsed into a bare bool.
* **Exact round-trip.** :func:`load_experience_ledger` reconstructs the frozen
  substrate dataclasses exactly (enums as members, tuples as tuples) after the
  chain verifies.
* **Copies, not references.** Queries rebuild fresh frozen instances from the
  stored payloads on every call; internal storage state is never handed out as
  a mutable reference.

Authority posture - the store mints NOTHING:

* Storing an episode never upgrades it. ``storage_admission`` is persisted
  verbatim; a ``PROPOSAL_SHADOW_STORED`` episode loads back shadow, and
  canonical inventory admission still requires the existing proposal-only
  admission path (:mod:`rakl.episode_admission` /
  :func:`rakl.experience_substrate.resolve_inventory_admission`).
* A stored lesson's ``authority`` is a persisted claim, not a granted one; the
  attestation checks in :func:`rakl.experience_substrate.add_lesson` remain the
  only admission path.
* Path, filename and store membership are never authority mechanisms. A
  ``VALID`` chain verdict is byte/chain integrity only - it is not promotion,
  review independence, or scientific authority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Tuple

from .experience_substrate import (
    EpisodeAdmissionReceipt,
    EpisodeOutcome,
    EpisodeStorageAdmission,
    ExperienceLedger,
    Lesson,
    LessonAuthority,
    LessonKind,
    SubstrateEdge,
    SubstrateKind,
    SubstrateNode,
    SubstrateRelation,
    TaskEpisode,
    validate_admission_receipt,
    validate_episode,
    validate_lesson,
)
from .v3_authority import canonical_json_bytes

STORE_SCHEMA_VERSION = "rakl-episode-store-v1"


class EpisodeStoreRecordKind(str, Enum):
    EPISODE = "EPISODE"
    LESSON = "LESSON"
    ADMISSION_RECEIPT = "ADMISSION_RECEIPT"
    SUBSTRATE_NODE = "SUBSTRATE_NODE"
    SUBSTRATE_EDGE = "SUBSTRATE_EDGE"


class ChainVerdict(str, Enum):
    """Typed outcome of walking the durable hash chain."""

    VALID = "VALID"
    TAMPERED = "TAMPERED"
    TRUNCATED = "TRUNCATED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ChainVerificationReport:
    """Machine-checkable chain-walk result for one store file.

    ``first_bad_index`` is the zero-based index of the first record at which
    the chain fails (``None`` for ``VALID`` and for file-level
    ``CANNOT_CHECK``). ``head_hash`` is the last verified record hash (empty
    string for an empty store, ``None`` when nothing could be verified).
    """

    verdict: ChainVerdict
    record_count: int
    first_bad_index: int | None
    reasons: Tuple[str, ...]
    head_hash: str | None

    @property
    def valid(self) -> bool:
        return self.verdict is ChainVerdict.VALID


class EpisodeStoreIntegrityError(ValueError):
    """The durable chain did not verify VALID; carries the typed report."""

    def __init__(self, report: ChainVerificationReport) -> None:
        super().__init__(
            f"episode store integrity failure: {report.verdict.value}"
            + (f" at record {report.first_bad_index}" if report.first_bad_index is not None else "")
            + (": " + ", ".join(report.reasons) if report.reasons else "")
        )
        self.report = report


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


# --- payload (de)serialization ------------------------------------------------
def _episode_payload(episode: TaskEpisode) -> Mapping[str, object]:
    return {
        "episode_id": episode.episode_id,
        "task_id": episode.task_id,
        "atom_id": episode.atom_id,
        "context_hash": episode.context_hash,
        "problem_signature": list(episode.problem_signature),
        "fibre_snapshot_hash": episode.fibre_snapshot_hash,
        "operator_ids": list(episode.operator_ids),
        "action_trace": list(episode.action_trace),
        "observation_ids": list(episode.observation_ids),
        "verification_ids": list(episode.verification_ids),
        "outcome": episode.outcome.value,
        "residual_signature": list(episode.residual_signature),
        "evidence_pointers": list(episode.evidence_pointers),
        "artifact_hash": episode.artifact_hash,
        "timestamp": episode.timestamp,
        "cost": episode.cost,
        "storage_admission": episode.storage_admission.value,
    }


def _restore_episode(d: Mapping[str, object]) -> TaskEpisode:
    return TaskEpisode(
        episode_id=d["episode_id"],
        task_id=d["task_id"],
        atom_id=d["atom_id"],
        context_hash=d["context_hash"],
        problem_signature=tuple(d["problem_signature"]),
        fibre_snapshot_hash=d["fibre_snapshot_hash"],
        operator_ids=tuple(d["operator_ids"]),
        action_trace=tuple(d["action_trace"]),
        observation_ids=tuple(d["observation_ids"]),
        verification_ids=tuple(d["verification_ids"]),
        outcome=EpisodeOutcome(d["outcome"]),
        residual_signature=tuple(d["residual_signature"]),
        evidence_pointers=tuple(d["evidence_pointers"]),
        artifact_hash=d["artifact_hash"],
        timestamp=d["timestamp"],
        cost=d["cost"],
        storage_admission=EpisodeStorageAdmission(d["storage_admission"]),
    )


def _lesson_payload(lesson: Lesson) -> Mapping[str, object]:
    return {
        "lesson_id": lesson.lesson_id,
        "kind": lesson.kind.value,
        "trigger_signature": list(lesson.trigger_signature),
        "context_scope": list(lesson.context_scope),
        "action": lesson.action,
        "expected_effects": list(lesson.expected_effects),
        "boundaries": list(lesson.boundaries),
        "supporting_episode_ids": list(lesson.supporting_episode_ids),
        "contradicting_episode_ids": list(lesson.contradicting_episode_ids),
        "falsifier": lesson.falsifier,
        "authority": lesson.authority.value,
        "validation_obligations": list(lesson.validation_obligations),
        "evidence_pointers": list(lesson.evidence_pointers),
        "artifact_hash": lesson.artifact_hash,
        "parent_lesson_id": lesson.parent_lesson_id,
        "authority_attestation_id": lesson.authority_attestation_id,
        "authority_subject_hash": lesson.authority_subject_hash,
        "authority_evidence_packet_hash": lesson.authority_evidence_packet_hash,
        "promotion_attestation_id": lesson.promotion_attestation_id,
        "authority_evidence_packet_artifact_id": lesson.authority_evidence_packet_artifact_id,
    }


def _restore_lesson(d: Mapping[str, object]) -> Lesson:
    return Lesson(
        lesson_id=d["lesson_id"],
        kind=LessonKind(d["kind"]),
        trigger_signature=tuple(d["trigger_signature"]),
        context_scope=tuple(d["context_scope"]),
        action=d["action"],
        expected_effects=tuple(d["expected_effects"]),
        boundaries=tuple(d["boundaries"]),
        supporting_episode_ids=tuple(d["supporting_episode_ids"]),
        contradicting_episode_ids=tuple(d["contradicting_episode_ids"]),
        falsifier=d["falsifier"],
        authority=LessonAuthority(d["authority"]),
        validation_obligations=tuple(d["validation_obligations"]),
        evidence_pointers=tuple(d["evidence_pointers"]),
        artifact_hash=d["artifact_hash"],
        parent_lesson_id=d["parent_lesson_id"],
        authority_attestation_id=d["authority_attestation_id"],
        authority_subject_hash=d["authority_subject_hash"],
        authority_evidence_packet_hash=d["authority_evidence_packet_hash"],
        promotion_attestation_id=d["promotion_attestation_id"],
        authority_evidence_packet_artifact_id=d["authority_evidence_packet_artifact_id"],
    )


def _receipt_payload(receipt: EpisodeAdmissionReceipt) -> Mapping[str, object]:
    return {
        "receipt_id": receipt.receipt_id,
        "episode_id": receipt.episode_id,
        "episode_artifact_hash": receipt.episode_artifact_hash,
        "storage_admission": receipt.storage_admission.value,
        "evidence_pointers": list(receipt.evidence_pointers),
        "artifact_hash": receipt.artifact_hash,
        "timestamp": receipt.timestamp,
    }


def _restore_receipt(d: Mapping[str, object]) -> EpisodeAdmissionReceipt:
    return EpisodeAdmissionReceipt(
        receipt_id=d["receipt_id"],
        episode_id=d["episode_id"],
        episode_artifact_hash=d["episode_artifact_hash"],
        storage_admission=EpisodeStorageAdmission(d["storage_admission"]),
        evidence_pointers=tuple(d["evidence_pointers"]),
        artifact_hash=d["artifact_hash"],
        timestamp=d["timestamp"],
    )


def _node_payload(node: SubstrateNode) -> Mapping[str, object]:
    return {
        "node_id": node.node_id,
        "kind": node.kind.value,
        "label": node.label,
        "payload_hash": node.payload_hash,
        "source_ids": list(node.source_ids),
        "metadata": [[key, value] for key, value in node.metadata],
    }


def _restore_node(d: Mapping[str, object]) -> SubstrateNode:
    return SubstrateNode(
        node_id=d["node_id"],
        kind=SubstrateKind(d["kind"]),
        label=d["label"],
        payload_hash=d["payload_hash"],
        source_ids=tuple(d["source_ids"]),
        metadata=tuple((key, value) for key, value in d["metadata"]),
    )


def _edge_payload(edge: SubstrateEdge) -> Mapping[str, object]:
    return {
        "source_id": edge.source_id,
        "target_id": edge.target_id,
        "relation": edge.relation.value,
        "rationale": edge.rationale,
        "evidence_pointers": list(edge.evidence_pointers),
    }


def _restore_edge(d: Mapping[str, object]) -> SubstrateEdge:
    return SubstrateEdge(
        source_id=d["source_id"],
        target_id=d["target_id"],
        relation=SubstrateRelation(d["relation"]),
        rationale=d["rationale"],
        evidence_pointers=tuple(d["evidence_pointers"]),
    )


_RECORD_HASH_FIELDS = (
    "schema_version",
    "sequence_index",
    "kind",
    "payload",
    "payload_hash",
    "previous_record_hash",
)


def _record_hash(record: Mapping[str, object]) -> str:
    """Digest over every record field except ``record_hash`` itself."""

    return sha256(
        canonical_json_bytes({name: record[name] for name in _RECORD_HASH_FIELDS})
    ).hexdigest()


# --- verification -------------------------------------------------------------
def verify_episode_store(
    path: str | Path,
    *,
    expected_head_hash: str | None = None,
) -> ChainVerificationReport:
    """Walk the durable chain and return a typed verdict; never a bare bool.

    * ``VALID``: every record recomputes to its ``record_hash``, every link
      matches the previous record's hash, and (when supplied) the head matches
      ``expected_head_hash``. An empty store is VALID with an empty head.
    * ``TAMPERED``: the first record whose bytes, payload hash, chain link, or
      sequence index fail recomputation, reported at ``first_bad_index``.
    * ``TRUNCATED``: an unparseable trailing record (torn tail write), or an
      internally valid chain whose head differs from ``expected_head_hash``
      (records lost from the end; without the expected head a history rewritten
      into a shorter internally-valid chain is indistinguishable from
      truncation, which is why resumption states carry the head hash).
    * ``CANNOT_CHECK``: the file is missing or unreadable. This is not
      "checked and fine" and must never be treated as VALID.
    """

    file_path = Path(path)
    try:
        content = file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ChainVerificationReport(
            verdict=ChainVerdict.CANNOT_CHECK,
            record_count=0,
            first_bad_index=None,
            reasons=("store_file_missing",),
            head_hash=None,
        )
    except OSError as error:
        return ChainVerificationReport(
            verdict=ChainVerdict.CANNOT_CHECK,
            record_count=0,
            first_bad_index=None,
            reasons=(f"store_file_unreadable:{error.__class__.__name__}",),
            head_hash=None,
        )

    lines = content.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]

    previous_hash = ""
    for index, line in enumerate(lines):
        prefix = f"record_{index}"
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                return ChainVerificationReport(
                    verdict=ChainVerdict.TRUNCATED,
                    record_count=index,
                    first_bad_index=index,
                    reasons=(f"{prefix}:trailing_record_unparseable_torn_write",),
                    head_hash=previous_hash,
                )
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:interior_record_unparseable",),
                head_hash=previous_hash,
            )
        missing = [
            name for name in (*_RECORD_HASH_FIELDS, "record_hash") if name not in record
        ]
        if missing:
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=tuple(f"{prefix}:field_missing:{name}" for name in missing),
                head_hash=previous_hash,
            )
        if _record_hash(record) != record["record_hash"]:
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:record_hash_mismatch",),
                head_hash=previous_hash,
            )
        if record["schema_version"] != STORE_SCHEMA_VERSION:
            return ChainVerificationReport(
                verdict=ChainVerdict.CANNOT_CHECK,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:unsupported_schema:{record['schema_version']}",),
                head_hash=previous_hash,
            )
        if record["sequence_index"] != index:
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:sequence_index_mismatch",),
                head_hash=previous_hash,
            )
        if index == 0 and record["previous_record_hash"] != "":
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:first_record_previous_hash_must_be_empty",),
                head_hash=previous_hash,
            )
        if index > 0 and record["previous_record_hash"] != previous_hash:
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:previous_record_hash_mismatch",),
                head_hash=previous_hash,
            )
        if (
            sha256(canonical_json_bytes(record["payload"])).hexdigest()
            != record["payload_hash"]
        ):
            return ChainVerificationReport(
                verdict=ChainVerdict.TAMPERED,
                record_count=index,
                first_bad_index=index,
                reasons=(f"{prefix}:payload_hash_mismatch",),
                head_hash=previous_hash,
            )
        previous_hash = record["record_hash"]

    if expected_head_hash is not None and expected_head_hash != previous_hash:
        return ChainVerificationReport(
            verdict=ChainVerdict.TRUNCATED,
            record_count=len(lines),
            first_bad_index=None,
            reasons=("head_hash_mismatch_on_internally_valid_chain",),
            head_hash=previous_hash,
        )

    return ChainVerificationReport(
        verdict=ChainVerdict.VALID,
        record_count=len(lines),
        first_bad_index=None,
        reasons=(),
        head_hash=previous_hash,
    )


# --- store --------------------------------------------------------------------
class EpisodeStore:
    """Append-only durable store over one JSONL file.

    Opening replays and verifies the durable chain; a store that does not
    verify ``VALID`` refuses to open (fail-closed - appends to a corrupted
    chain are never permitted). All query methods rebuild fresh frozen
    instances from the stored payloads on every call, so callers never receive
    references into the store's internal state.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        report = verify_episode_store(self._path)
        if report.verdict is ChainVerdict.CANNOT_CHECK and report.reasons == (
            "store_file_missing",
        ):
            self._records: list[dict] = []
        elif not report.valid:
            raise EpisodeStoreIntegrityError(report)
        else:
            with self._path.open("r", encoding="utf-8") as handle:
                self._records = [json.loads(line) for line in handle if line.strip()]
        self._head_hash = self._records[-1]["record_hash"] if self._records else ""
        self._ids_by_kind: dict[EpisodeStoreRecordKind, set[str]] = {
            kind: set() for kind in EpisodeStoreRecordKind
        }
        for record in self._records:
            kind = EpisodeStoreRecordKind(record["kind"])
            key = _payload_identity(kind, record["payload"])
            if key is not None:
                self._ids_by_kind[kind].add(key)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def head_hash(self) -> str:
        """Hash of the last appended record (empty for an empty store)."""

        return self._head_hash

    @property
    def record_count(self) -> int:
        return len(self._records)

    def verify(self, *, expected_head_hash: str | None = None) -> ChainVerificationReport:
        """Re-walk the durable bytes on disk (not the in-memory replay)."""

        return verify_episode_store(self._path, expected_head_hash=expected_head_hash)

    # --- append ---------------------------------------------------------------
    def _append(self, kind: EpisodeStoreRecordKind, payload: Mapping[str, object]) -> str:
        key = _payload_identity(kind, payload)
        if key is not None and key in self._ids_by_kind[kind]:
            raise ValueError(f"duplicate {kind.value.lower()} identity: {key}")
        record: dict[str, object] = {
            "schema_version": STORE_SCHEMA_VERSION,
            "sequence_index": len(self._records),
            "kind": kind.value,
            "payload": dict(payload),
            "payload_hash": sha256(canonical_json_bytes(payload)).hexdigest(),
            "previous_record_hash": self._head_hash,
        }
        record["record_hash"] = _record_hash(record)
        line = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        self._records.append(record)
        self._head_hash = record["record_hash"]
        if key is not None:
            self._ids_by_kind[kind].add(key)
        return self._head_hash

    def append_episode(self, episode: TaskEpisode) -> str:
        """Durably append one episode verbatim; storage never upgrades it."""

        reasons = validate_episode(episode)
        if reasons:
            raise ValueError("invalid episode: " + ", ".join(reasons))
        return self._append(EpisodeStoreRecordKind.EPISODE, _episode_payload(episode))

    def append_lesson(self, lesson: Lesson) -> str:
        """Durably append one lesson; its authority is a claim, not a grant."""

        reasons = validate_lesson(lesson)
        if reasons:
            raise ValueError("invalid lesson: " + ", ".join(reasons))
        return self._append(EpisodeStoreRecordKind.LESSON, _lesson_payload(lesson))

    def append_admission_receipt(self, receipt: EpisodeAdmissionReceipt) -> str:
        """Durably append one admission receipt minted by the admission path."""

        reasons = validate_admission_receipt(receipt)
        if reasons:
            raise ValueError("invalid admission receipt: " + ", ".join(reasons))
        return self._append(EpisodeStoreRecordKind.ADMISSION_RECEIPT, _receipt_payload(receipt))

    def append_substrate_node(self, node: SubstrateNode) -> str:
        return self._append(EpisodeStoreRecordKind.SUBSTRATE_NODE, _node_payload(node))

    def append_substrate_edge(self, edge: SubstrateEdge) -> str:
        return self._append(EpisodeStoreRecordKind.SUBSTRATE_EDGE, _edge_payload(edge))

    def append_experience_ledger(self, ledger: ExperienceLedger) -> str:
        """Snapshot a full in-memory ledger into an empty store.

        Refuses on a non-empty store so the exact round-trip contract
        (``load_experience_ledger(path) == ledger``) stays unambiguous.
        Returns the resulting head hash.
        """

        if self._records:
            raise ValueError("ledger snapshot requires an empty episode store")
        for episode in ledger.episodes:
            self.append_episode(episode)
        for lesson in ledger.lessons:
            self.append_lesson(lesson)
        for node in ledger.nodes:
            self.append_substrate_node(node)
        for edge in ledger.edges:
            self.append_substrate_edge(edge)
        for receipt in ledger.admission_receipts:
            self.append_admission_receipt(receipt)
        return self._head_hash

    # --- queries (always fresh copies) ---------------------------------------
    def _payloads(self, kind: EpisodeStoreRecordKind) -> Tuple[Mapping[str, object], ...]:
        return tuple(
            record["payload"] for record in self._records if record["kind"] == kind.value
        )

    def episodes(self) -> Tuple[TaskEpisode, ...]:
        return tuple(_restore_episode(p) for p in self._payloads(EpisodeStoreRecordKind.EPISODE))

    def lessons(self) -> Tuple[Lesson, ...]:
        return tuple(_restore_lesson(p) for p in self._payloads(EpisodeStoreRecordKind.LESSON))

    def admission_receipts(self) -> Tuple[EpisodeAdmissionReceipt, ...]:
        return tuple(
            _restore_receipt(p)
            for p in self._payloads(EpisodeStoreRecordKind.ADMISSION_RECEIPT)
        )

    def get_episode(self, episode_id: str) -> TaskEpisode | None:
        for payload in self._payloads(EpisodeStoreRecordKind.EPISODE):
            if payload["episode_id"] == episode_id:
                return _restore_episode(payload)
        return None

    def find_by_artifact_hash(
        self, artifact_hash: str
    ) -> Tuple[TaskEpisode | Lesson | EpisodeAdmissionReceipt, ...]:
        """All stored episodes/lessons/receipts whose content hash matches."""

        matches: list[TaskEpisode | Lesson | EpisodeAdmissionReceipt] = []
        for record in self._records:
            kind = EpisodeStoreRecordKind(record["kind"])
            payload = record["payload"]
            if kind is EpisodeStoreRecordKind.EPISODE and payload["artifact_hash"] == artifact_hash:
                matches.append(_restore_episode(payload))
            elif kind is EpisodeStoreRecordKind.LESSON and payload["artifact_hash"] == artifact_hash:
                matches.append(_restore_lesson(payload))
            elif (
                kind is EpisodeStoreRecordKind.ADMISSION_RECEIPT
                and payload["artifact_hash"] == artifact_hash
            ):
                matches.append(_restore_receipt(payload))
        return tuple(matches)

    def episodes_by_outcome(self, outcome: EpisodeOutcome) -> Tuple[TaskEpisode, ...]:
        return tuple(
            _restore_episode(payload)
            for payload in self._payloads(EpisodeStoreRecordKind.EPISODE)
            if payload["outcome"] == outcome.value
        )

    def episodes_in_time_range(self, start_utc: str, end_utc: str) -> Tuple[TaskEpisode, ...]:
        """Episodes whose timestamp lies in the inclusive [start, end] range."""

        start = _parse_time(start_utc)
        end = _parse_time(end_utc)
        if start is None or end is None:
            raise ValueError("time range bounds must be timezone-aware ISO-8601")
        if end < start:
            raise ValueError("time range end precedes start")
        selected: list[TaskEpisode] = []
        for payload in self._payloads(EpisodeStoreRecordKind.EPISODE):
            timestamp = _parse_time(payload["timestamp"])
            if timestamp is not None and start <= timestamp <= end:
                selected.append(_restore_episode(payload))
        return tuple(selected)


def _payload_identity(
    kind: EpisodeStoreRecordKind, payload: Mapping[str, object]
) -> str | None:
    """Uniqueness key per record kind (edges are intentionally unkeyed)."""

    if kind is EpisodeStoreRecordKind.EPISODE:
        return payload["episode_id"]
    if kind is EpisodeStoreRecordKind.LESSON:
        return payload["lesson_id"]
    if kind is EpisodeStoreRecordKind.ADMISSION_RECEIPT:
        return payload["receipt_id"]
    if kind is EpisodeStoreRecordKind.SUBSTRATE_NODE:
        return payload["node_id"]
    return None


def load_experience_ledger(path: str | Path) -> ExperienceLedger:
    """Verify the durable chain, then rebuild the exact in-memory ledger.

    Fails closed: a chain that is not ``VALID`` raises
    :class:`EpisodeStoreIntegrityError` carrying the typed report instead of
    returning a partially trusted ledger.
    """

    report = verify_episode_store(path)
    if not report.valid:
        raise EpisodeStoreIntegrityError(report)
    store = EpisodeStore(path)
    return ExperienceLedger(
        episodes=store.episodes(),
        lessons=store.lessons(),
        nodes=tuple(
            _restore_node(p) for p in store._payloads(EpisodeStoreRecordKind.SUBSTRATE_NODE)
        ),
        edges=tuple(
            _restore_edge(p) for p in store._payloads(EpisodeStoreRecordKind.SUBSTRATE_EDGE)
        ),
        admission_receipts=store.admission_receipts(),
    )
