"""Seed-corpus migration: SELF_RAKL_RESEARCH_* file receipts -> episode store.

Maps every ``research/SELF_RAKL_RESEARCH_*`` file receipt (the de facto durable
episode record identified by the ORION architecture audit) into a
:class:`rakl.experience_substrate.TaskEpisode` and appends it to a durable
:class:`rakl.episode_store.EpisodeStore` JSONL file (PLAN.md P2.1 seed corpus).

Posture (all inherited, none invented here):

* **Raw receipts stay canonical.** The original files are the immutable
  evidence roots. This migration never modifies, moves, or rewrites them.
  Every episode carries a source reference (repo-relative path + content
  sha256) in ``evidence_pointers``.
* **Proposal-only admission.** Every episode is stored with
  ``EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED`` and audited through the
  existing :mod:`rakl.episode_admission` proposal flow
  (:func:`rakl.episode_admission.retain_proposal_shadow_episode`).  Nothing is
  minted as canonical; storage never upgrades admission; ingestion grants no
  scientific, review, or promotion authority.
* **Typed UNKNOWN, never fabrication.** Fields that cannot be recovered from a
  receipt's own content get typed ``UNKNOWN:*`` markers.  Times are derived
  from receipt content only (json ``date``/``frozen_at`` fields, markdown
  ``Date:`` lines); no timestamp is minted at run time.
* **CANNOT_PARSE / NO_RECOVERABLE_DATE are first-class.** A receipt that
  cannot be parsed, or whose date cannot be recovered (the store schema
  requires a valid episode timestamp, so an UNKNOWN date is unrepresentable
  as a stored episode), is recorded in a typed skip-list with a reason - never
  silently dropped.  ``ingested + skipped == inventory`` is asserted.
* **Deterministic.** Files are processed in sorted filename order and every
  byte of the output store derives from receipt content, so the same input
  tree produces byte-identical store output.

Identity note: ``episode_id`` / ``task_id`` / ``atom_id`` are derived from the
receipt filename purely as deterministic identity bookkeeping.  Consistent
with the episode-admission module, path and filename are never authority
mechanisms - they decide nothing about admission or outcome.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from rakl.episode_admission import (  # noqa: E402
    AdmissionVerdict,
    EpisodeAdmissionReceipt,
    EpisodeStorageStatus,
    retain_proposal_shadow_episode,
)
from rakl.episode_store import (  # noqa: E402
    ChainVerificationReport,
    EpisodeStore,
    verify_episode_store,
)
from rakl.experience_substrate import (  # noqa: E402
    EpisodeOutcome,
    EpisodeStorageAdmission,
    TaskEpisode,
    episode_content_bytes,
    validate_episode,
)

RECEIPT_GLOB_PREFIX = "SELF_RAKL_RESEARCH_"
STORE_FILENAME = "seed_corpus.jsonl"
SKIP_LIST_FILENAME = "skip_list.json"
ADMISSION_RECEIPTS_FILENAME = "admission_receipts.json"
SHADOW_REGISTRY_ID = "shadow:self_rakl_seed_corpus_v1"

# Typed skip reasons - first-class outcomes, never silent drops.
REASON_CANNOT_PARSE = "CANNOT_PARSE"
REASON_NO_RECOVERABLE_DATE = "NO_RECOVERABLE_DATE"

# Typed UNKNOWN markers - honest gaps, never fabricated values.
UNKNOWN_CONTEXT_HASH = "UNKNOWN:context_hash_not_recoverable_from_receipt"
UNKNOWN_FIBRE_SNAPSHOT_HASH = "UNKNOWN:fibre_snapshot_hash_not_recoverable_from_receipt"
UNKNOWN_ACTION_TRACE = "UNKNOWN:action_trace_not_recoverable_from_receipt"
UNKNOWN_OPERATOR_IDS = "UNKNOWN:operator_ids_not_recoverable_from_receipt"
UNKNOWN_OBSERVATION_IDS = "UNKNOWN:observation_ids_not_recoverable_from_receipt"
UNKNOWN_VERIFICATION_IDS = "UNKNOWN:verification_ids_not_recoverable_from_receipt"

_STEM_RE = re.compile(r"^SELF_RAKL_RESEARCH_(\d+[A-Z]?)(?:_(.+))?$")
_MD_DATE_RE = re.compile(r"^\*{0,2}Date\*{0,2}:?\s*:?\s*`?(20\d{2}-\d{2}-\d{2})`?", re.M)
_MD_OBJECT_RE = re.compile(r"^\*{0,2}Object\*{0,2}:?\s*:?\s*`?([^`\n]+)`?\s*$", re.M)
_MD_STATUS_RE = re.compile(r"^\*{0,2}Status\*{0,2}:?\s*:?\s*(.+)$", re.M)
_DATE_ONLY_RE = re.compile(r"^20\d{2}-\d{2}-\d{2}$")

_JSON_DOC_ID_KEYS = (
    "receipt_id",
    "benchmark_id",
    "validation_id",
    "erratum_id",
    "pointer_id",
    "supplement_id",
    "fiber_id",
)


@dataclass(frozen=True)
class SkipEntry:
    """One receipt that could not become a stored episode, with a typed reason."""

    file: str
    reason: str
    detail: str


@dataclass(frozen=True)
class ParsedReceipt:
    """Fields recovered from one receipt file's own content."""

    path: Path
    relative_path: str
    content_sha256: str
    task_number: str
    role: str
    raw_date: str | None
    date_source: str | None
    doc_id: str | None
    object_name: str | None
    status: str | None
    promotion_status: str | None
    research_status: str | None
    residual_ids: Tuple[str, ...]
    verification_ids: Tuple[str, ...]


@dataclass(frozen=True)
class MigrationResult:
    inventory_count: int
    ingested_count: int
    skipped: Tuple[SkipEntry, ...]
    head_hash: str
    verification: ChainVerificationReport
    admission_verdicts: Mapping[str, str]
    store_path: Path


def inventory(research_dir: Path) -> Tuple[Path, ...]:
    """All receipt files in deterministic (sorted filename) order."""

    return tuple(
        sorted(
            path
            for path in research_dir.iterdir()
            if path.is_file() and path.name.startswith(RECEIPT_GLOB_PREFIX)
        )
    )


def _identity_from_stem(stem: str) -> Tuple[str, str] | None:
    match = _STEM_RE.match(stem)
    if match is None:
        return None
    role = match.group(2) or "MAIN"
    return match.group(1), role


def parse_receipt_file(path: Path, research_dir: Path) -> ParsedReceipt | SkipEntry:
    """Parse one receipt.  CANNOT_PARSE is a typed first-class outcome."""

    relative = f"research/{path.relative_to(research_dir)}"
    try:
        raw = path.read_bytes()
    except OSError as error:
        return SkipEntry(relative, REASON_CANNOT_PARSE, f"unreadable:{error.__class__.__name__}")
    digest = sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return SkipEntry(relative, REASON_CANNOT_PARSE, "not_utf8")

    identity = _identity_from_stem(path.stem)
    if identity is None:
        return SkipEntry(relative, REASON_CANNOT_PARSE, "filename_identity_unrecognized")
    task_number, role = identity

    if path.suffix == ".json":
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as error:
            return SkipEntry(relative, REASON_CANNOT_PARSE, f"invalid_json:line_{error.lineno}")
        if not isinstance(doc, dict):
            return SkipEntry(relative, REASON_CANNOT_PARSE, "json_root_not_object")
        return _parse_json_receipt(path, relative, digest, task_number, role, doc)
    return _parse_md_receipt(path, relative, digest, task_number, role, text)


def _parse_json_receipt(
    path: Path,
    relative: str,
    digest: str,
    task_number: str,
    role: str,
    doc: Mapping[str, object],
) -> ParsedReceipt:
    raw_date: str | None = None
    date_source: str | None = None
    for key in ("date", "frozen_at"):
        value = doc.get(key)
        if isinstance(value, str) and value:
            raw_date = value
            date_source = f"json_{key}_field"
            break

    doc_id = next(
        (doc[key] for key in _JSON_DOC_ID_KEYS if isinstance(doc.get(key), str)), None
    )
    object_name = doc.get("object") if isinstance(doc.get("object"), str) else None
    status = doc.get("status") if isinstance(doc.get("status"), str) else None
    research_status = (
        doc.get("research_status") if isinstance(doc.get("research_status"), str) else None
    )
    promotion = doc.get("promotion")
    promotion_status = (
        promotion.get("status")
        if isinstance(promotion, dict) and isinstance(promotion.get("status"), str)
        else None
    )

    residual_ids: list[str] = []
    native_residual = doc.get("native_process_residual")
    if (
        isinstance(native_residual, dict)
        and native_residual.get("found") is True
        and isinstance(native_residual.get("id"), str)
    ):
        residual_ids.append(f"native_process_residual:{native_residual['id']}")

    verification_ids: list[str] = []
    for holder_key in ("final_candidate", "post_promotion_main_validation"):
        holder = doc.get(holder_key)
        if isinstance(holder, dict) and isinstance(holder.get("ci_run_id"), int):
            verification_ids.append(f"ci_run:{holder['ci_run_id']}")
    if isinstance(doc.get("workflow_run_id"), int):
        verification_ids.append(f"ci_run:{doc['workflow_run_id']}")

    return ParsedReceipt(
        path=path,
        relative_path=relative,
        content_sha256=digest,
        task_number=task_number,
        role=role,
        raw_date=raw_date,
        date_source=date_source,
        doc_id=doc_id,
        object_name=object_name,
        status=status,
        promotion_status=promotion_status,
        research_status=research_status,
        residual_ids=tuple(residual_ids),
        verification_ids=tuple(verification_ids),
    )


def _parse_md_receipt(
    path: Path,
    relative: str,
    digest: str,
    task_number: str,
    role: str,
    text: str,
) -> ParsedReceipt:
    date_match = _MD_DATE_RE.search(text)
    object_match = _MD_OBJECT_RE.search(text)
    status_match = _MD_STATUS_RE.search(text)
    return ParsedReceipt(
        path=path,
        relative_path=relative,
        content_sha256=digest,
        task_number=task_number,
        role=role,
        raw_date=date_match.group(1) if date_match else None,
        date_source="md_date_line" if date_match else None,
        doc_id=None,
        object_name=object_match.group(1).strip().strip("`") if object_match else None,
        status=status_match.group(1).strip().strip("`") if status_match else None,
        promotion_status=None,
        research_status=None,
        residual_ids=(),
        verification_ids=(),
    )


def _derive_timestamp(parsed: ParsedReceipt) -> Tuple[str, str] | None:
    """Content-derived episode timestamp, or None when unrecoverable.

    A date-only value is encoded at UTC midnight (day-resolution encoding of
    content-recovered information, documented via the ``timestamp_source``
    evidence pointer - not a minted clock time).  A full timezone-aware value
    is kept verbatim.
    """

    if parsed.raw_date is None or parsed.date_source is None:
        return None
    value = parsed.raw_date
    if _DATE_ONLY_RE.match(value):
        return f"{value}T00:00:00Z", f"{parsed.date_source}:day_resolution"
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        candidate = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if candidate.tzinfo is None or candidate.utcoffset() is None:
        return None
    return value, f"{parsed.date_source}:full_timestamp_verbatim"


def _derive_outcome(parsed: ParsedReceipt) -> Tuple[EpisodeOutcome, Tuple[str, ...]]:
    """Explicit-marker-only outcome mapping; everything else is typed UNKNOWN.

    Returns (outcome, residual additions).  Never interprets prose.
    """

    statuses = tuple(
        value
        for value in (parsed.promotion_status, parsed.status, parsed.research_status)
        if value is not None
    )
    for value in statuses:
        if value == "PROMOTED" or value.startswith("PROMOTED_"):
            return EpisodeOutcome.SUCCESS, ()
    for value in statuses:
        if value == "REFUTED":
            return EpisodeOutcome.FAILURE, (f"receipt_status:{value}",)
        if value == "BLOCKED":
            return EpisodeOutcome.BLOCKED, (f"receipt_status:{value}",)
    return EpisodeOutcome.UNKNOWN, ()


def episode_from_receipt(parsed: ParsedReceipt) -> TaskEpisode | SkipEntry:
    """Map one parsed receipt to a proposal/shadow TaskEpisode.

    NO_RECOVERABLE_DATE is a typed skip: the store schema requires a valid
    episode timestamp, so an UNKNOWN date cannot be represented as a stored
    episode without fabricating a time - the raw receipt simply remains an
    un-migrated evidence root.
    """

    derived = _derive_timestamp(parsed)
    if derived is None:
        return SkipEntry(
            parsed.relative_path,
            REASON_NO_RECOVERABLE_DATE,
            "no_dedicated_date_field_or_Date_line;"
            "store_episode_timestamp_is_mandatory_so_UNKNOWN_date_is_unrepresentable",
        )
    timestamp, timestamp_source = derived

    task_id = f"SELF_RAKL_RESEARCH_{parsed.task_number}"
    signature: list[str] = [f"study:{task_id}", f"source_kind:{parsed.role}"]
    if parsed.doc_id is not None:
        signature.append(f"doc_id:{parsed.doc_id}")
    if parsed.object_name is not None:
        signature.append(f"object:{parsed.object_name}")
    if parsed.status is not None:
        signature.append(f"status:{parsed.status}")
    if parsed.research_status is not None:
        signature.append(f"research_status:{parsed.research_status}")
    if parsed.promotion_status is not None:
        signature.append(f"promotion_status:{parsed.promotion_status}")

    outcome, outcome_residuals = _derive_outcome(parsed)
    residual_signature = parsed.residual_ids + outcome_residuals

    episode = TaskEpisode(
        episode_id=parsed.path.stem,
        task_id=task_id,
        atom_id=parsed.role,
        context_hash=UNKNOWN_CONTEXT_HASH,
        problem_signature=tuple(signature),
        fibre_snapshot_hash=UNKNOWN_FIBRE_SNAPSHOT_HASH,
        operator_ids=(UNKNOWN_OPERATOR_IDS,),
        action_trace=(UNKNOWN_ACTION_TRACE,),
        observation_ids=(UNKNOWN_OBSERVATION_IDS,),
        verification_ids=parsed.verification_ids or (UNKNOWN_VERIFICATION_IDS,),
        outcome=outcome,
        residual_signature=residual_signature,
        evidence_pointers=(
            parsed.relative_path,
            f"sha256:{parsed.content_sha256}",
            f"timestamp_source:{timestamp_source}",
        ),
        artifact_hash="0" * 64,
        timestamp=timestamp,
        cost=0.0,
        storage_admission=EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED,
    )
    episode = replace(
        episode, artifact_hash=sha256(episode_content_bytes(episode)).hexdigest()
    )
    reasons = validate_episode(episode)
    if reasons:
        return SkipEntry(
            parsed.relative_path,
            REASON_CANNOT_PARSE,
            "mapped_episode_failed_substrate_validation:" + ",".join(reasons),
        )
    return episode


def _registered_at_utc(timestamp: str) -> str:
    """Deterministic UTC 'Z' rendering of a content-derived episode timestamp."""

    if timestamp.endswith("Z"):
        return timestamp
    parsed = datetime.fromisoformat(timestamp)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def shadow_admission_receipt(episode: TaskEpisode) -> EpisodeAdmissionReceipt:
    """Proposal-only (shadow) admission receipt; never canonical."""

    return EpisodeAdmissionReceipt(
        receipt_id=f"seed-admission:{episode.episode_id}",
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        inventory_registry_id=SHADOW_REGISTRY_ID,
        registered_at_utc=_registered_at_utc(episode.timestamp),
        registration_evidence_pointers=episode.evidence_pointers,
        reverification_triggers=(
            "source_file_content_change",
            "episode_store_chain_invalid",
        ),
    )


def run_migration(research_dir: Path, out_dir: Path) -> MigrationResult:
    """Execute the full deterministic migration into ``out_dir``.

    Refuses to run over an existing store file: the store is append-only, and
    the seed corpus is regenerated from the immutable roots, never edited.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    store_path = out_dir / STORE_FILENAME
    if store_path.exists():
        raise FileExistsError(
            f"refusing to migrate over existing store: {store_path} "
            "(delete the derived store explicitly to regenerate; "
            "raw receipts are never touched)"
        )

    files = inventory(research_dir)
    skips: list[SkipEntry] = []
    episodes: list[TaskEpisode] = []
    for path in files:
        parsed = parse_receipt_file(path, research_dir)
        if isinstance(parsed, SkipEntry):
            skips.append(parsed)
            continue
        episode = episode_from_receipt(parsed)
        if isinstance(episode, SkipEntry):
            skips.append(episode)
            continue
        episodes.append(episode)

    if len(episodes) + len(skips) != len(files):
        raise AssertionError(
            f"count invariant broken: {len(episodes)} ingested + {len(skips)} skipped "
            f"!= {len(files)} inventory"
        )

    # Proposal-only admission through the existing episode_admission flow.
    admission_verdicts: dict[str, str] = {}
    receipts: list[EpisodeAdmissionReceipt] = []
    for episode in episodes:
        receipt = shadow_admission_receipt(episode)
        report = retain_proposal_shadow_episode(episode, receipt)
        if report.verdict is not AdmissionVerdict.SHADOW_RETAINED:
            raise AssertionError(
                f"proposal-only admission violated for {episode.episode_id}: "
                f"{report.verdict.value}"
            )
        if report.satisfies_canonical_inventory:
            raise AssertionError(
                f"shadow episode must not satisfy canonical inventory: {episode.episode_id}"
            )
        admission_verdicts[episode.episode_id] = report.verdict.value
        receipts.append(receipt)

    store = EpisodeStore(store_path)
    for episode in episodes:
        store.append_episode(episode)
    head_hash = store.head_hash

    verification = verify_episode_store(store_path, expected_head_hash=head_hash)

    skip_document = {
        "inventory_count": len(files),
        "ingested_count": len(episodes),
        "skipped_count": len(skips),
        "skips": [
            {"file": entry.file, "reason": entry.reason, "detail": entry.detail}
            for entry in skips
        ],
    }
    (out_dir / SKIP_LIST_FILENAME).write_text(
        json.dumps(skip_document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / ADMISSION_RECEIPTS_FILENAME).write_text(
        json.dumps(
            {
                "authority_disclaimer": (
                    "Proposal-only shadow admission. Ingestion grants nothing: "
                    "no canonical inventory membership, no promotion, no review "
                    "independence, no scientific authority. The raw "
                    "SELF_RAKL_RESEARCH_* files remain the canonical evidence roots."
                ),
                "receipts": [dict(receipt.document()) for receipt in receipts],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return MigrationResult(
        inventory_count=len(files),
        ingested_count=len(episodes),
        skipped=tuple(skips),
        head_hash=head_hash,
        verification=verification,
        admission_verdicts=admission_verdicts,
        store_path=store_path,
    )


def main() -> int:
    research_dir = _REPO_ROOT / "research"
    out_dir = Path(__file__).resolve().parent
    result = run_migration(research_dir, out_dir)
    print(f"inventory: {result.inventory_count}")
    print(f"ingested:  {result.ingested_count}")
    print(f"skipped:   {len(result.skipped)}")
    for entry in result.skipped:
        print(f"  SKIP {entry.reason} {entry.file} ({entry.detail})")
    print(f"head_hash: {result.head_hash}")
    print(f"verify:    {result.verification.verdict.value}")
    return 0 if result.verification.verdict.value == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
