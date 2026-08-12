"""Host hook materializing durable pre-action receipt before hypothesis exposure (#464).

Repeated chronology failures in autonomous runs motivated a host-level hook that
freezes the problem fibre and predeclared discriminator **before** the first
free-form hypothesis is exposed to the actor. This module provides that hook and
a **QoI instrumentation stub** for the prospective process metric:

```text
fraction of consequential hypotheses where
durable pre-action receipt timestamp < first hypothesis exposure
```

Scope, stated as narrowly as the artifact supports:

* **Hook only.** Not wired into :func:`rakl.driver_learning.run_learning_turn` by
  default. Host runners invoke :func:`run_pre_scratch_fibre_freeze_hook` before
  exposing hypotheses.
* **QoI stub is not validated.** :func:`compute_pre_scratch_chronology_qoi`
  records the fraction mechanically. Passing unit tests or landing this module
  does **not** establish chronology improvement. A fresh prospective
  discriminator comparing hook-enabled vs baseline runners is required.
* **No authority.** Emits no proof, lesson, tool, gluing, theorem, prospective
  credit, or review-independence authority.

This module performs no network access, no git access and no writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence, Tuple

from .pre_action_receipt import (
    PreActionFibreReceipt,
    RejectedRetrieval,
    SelectedRetrieval,
    canonical_json_sha256,
)

HOOK_RESULT_SCHEMA_VERSION = "pre-scratch-fibre-freeze-hook-result-v1"
QOI_SCHEMA_VERSION = "pre-scratch-chronology-qoi-v1"
QOI_VALIDATION_STATUS = "NOT_VALIDATED_STUB"

_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")


class HookMaterializationStatus(str, Enum):
    MATERIALIZED = "MATERIALIZED"
    ALREADY_MATERIALIZED = "ALREADY_MATERIALIZED"
    SKIPPED_NOT_CONSEQUENTIAL = "SKIPPED_NOT_CONSEQUENTIAL"
    CANNOT_CHECK = "CANNOT_CHECK"


class ChronologyQoIVerdict(str, Enum):
  COMPUTED = "COMPUTED"
  CANNOT_CHECK = "CANNOT_CHECK"


def _parse_utc(value: str) -> datetime | None:
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


@dataclass(frozen=True)
class PreScratchFibreFreezeHookResult:
    """Outcome of invoking the host hook before first hypothesis exposure."""

    hook_id: str
    materialization_status: HookMaterializationStatus
    hook_invoked_at_utc: str
    receipt: PreActionFibreReceipt | None
    durable_receipt_pointer: str | None
    reasons: Tuple[str, ...]
    schema_version: str = HOOK_RESULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.hook_id:
            raise ValueError("hook_id is required")
        if not _ISO_UTC_RE.match(self.hook_invoked_at_utc):
            raise ValueError("hook_invoked_at_utc must be ISO-8601 UTC ending in 'Z'")
        if self.materialization_status is HookMaterializationStatus.MATERIALIZED:
            if self.receipt is None or self.durable_receipt_pointer is None:
                raise ValueError("MATERIALIZED hook requires receipt and durable pointer")
        if self.materialization_status is HookMaterializationStatus.ALREADY_MATERIALIZED:
            if self.receipt is None or self.durable_receipt_pointer is None:
                raise ValueError("ALREADY_MATERIALIZED hook requires receipt and durable pointer")

    def content(self) -> Mapping[str, Any]:
        document: dict[str, Any] = {
            "schema_version": self.schema_version,
            "hook_id": self.hook_id,
            "materialization_status": self.materialization_status.value,
            "hook_invoked_at_utc": self.hook_invoked_at_utc,
            "durable_receipt_pointer": self.durable_receipt_pointer,
            "reasons": list(self.reasons),
        }
        if self.receipt is not None:
            document["receipt_canonical_sha256"] = self.receipt.receipt_canonical_sha256
        return document

    @property
    def result_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        payload = dict(self.content())
        payload["result_canonical_sha256"] = self.result_canonical_sha256
        if self.receipt is not None:
            payload["receipt"] = dict(self.receipt.document())
        return payload


@dataclass(frozen=True)
class HypothesisExposureRecord:
    """First exposure of a hypothesis to the actor."""

    hypothesis_id: str
    first_exposed_at_utc: str
    consequential: bool

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id is required")
        if not _ISO_UTC_RE.match(self.first_exposed_at_utc):
            raise ValueError("first_exposed_at_utc must be ISO-8601 UTC ending in 'Z'")


@dataclass(frozen=True)
class PreScratchChronologyObservation:
    """One hypothesis exposure paired with the durable receipt that should precede it."""

    hypothesis_id: str
    consequential: bool
    first_exposed_at_utc: str
    receipt_frozen_at_utc: str | None
    durable_receipt_pointer: str | None = None

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id is required")
        if not _ISO_UTC_RE.match(self.first_exposed_at_utc):
            raise ValueError("first_exposed_at_utc must be ISO-8601 UTC ending in 'Z'")
        if self.receipt_frozen_at_utc is not None and not _ISO_UTC_RE.match(self.receipt_frozen_at_utc):
            raise ValueError("receipt_frozen_at_utc must be ISO-8601 UTC ending in 'Z'")


@dataclass(frozen=True)
class PreScratchChronologyQoIReport:
    """Prospective chronology QoI instrumentation stub — not validated."""

    verdict: ChronologyQoIVerdict
    consequential_hypothesis_count: int
    prospective_pre_exposure_count: int
    prospective_pre_exposure_fraction: float | None
    validation_status: str
    reasons: Tuple[str, ...]
    schema_version: str = QOI_SCHEMA_VERSION

    @property
    def validated(self) -> bool:
        return False

    def content(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "verdict": self.verdict.value,
            "consequential_hypothesis_count": self.consequential_hypothesis_count,
            "prospective_pre_exposure_count": self.prospective_pre_exposure_count,
            "prospective_pre_exposure_fraction": self.prospective_pre_exposure_fraction,
            "validation_status": self.validation_status,
            "reasons": list(self.reasons),
        }

    @property
    def report_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        payload = dict(self.content())
        payload["report_canonical_sha256"] = self.report_canonical_sha256
        return payload


def materialize_pre_scratch_fibre_receipt(
    *,
    receipt_id: str,
    framework_repository: str,
    framework_commit: str,
    application_repository: str,
    application_commit: str,
    task_id: str,
    atom_id: str,
    context_hash: str,
    fibre_snapshot_hash: str,
    operator_ids: Tuple[str, ...],
    selected_retrievals: Tuple[SelectedRetrieval, ...],
    rejected_retrievals: Tuple[RejectedRetrieval, ...],
    predeclared_discriminator: str,
    allowed_outcome_branches: Tuple[str, ...],
    frozen_at_utc: str,
    sequence_index: int = 0,
) -> PreActionFibreReceipt:
    """Build the durable pre-action receipt the hook materializes."""

    return PreActionFibreReceipt(
        receipt_id=receipt_id,
        framework_repository=framework_repository,
        framework_commit=framework_commit,
        application_repository=application_repository,
        application_commit=application_commit,
        task_id=task_id,
        atom_id=atom_id,
        context_hash=context_hash,
        fibre_snapshot_hash=fibre_snapshot_hash,
        operator_ids=operator_ids,
        selected_retrievals=selected_retrievals,
        rejected_retrievals=rejected_retrievals,
        predeclared_discriminator=predeclared_discriminator,
        allowed_outcome_branches=allowed_outcome_branches,
        frozen_at_utc=frozen_at_utc,
        sequence_index=sequence_index,
    )


def run_pre_scratch_fibre_freeze_hook(
    *,
    hook_id: str,
    hook_invoked_at_utc: str,
    consequential_turn: bool,
    prior_materialized_receipt: PreActionFibreReceipt | None = None,
    receipt_id: str | None = None,
    framework_repository: str | None = None,
    framework_commit: str | None = None,
    application_repository: str | None = None,
    application_commit: str | None = None,
    task_id: str | None = None,
    atom_id: str | None = None,
    context_hash: str | None = None,
    fibre_snapshot_hash: str | None = None,
    operator_ids: Tuple[str, ...] = (),
    selected_retrievals: Tuple[SelectedRetrieval, ...] = (),
    rejected_retrievals: Tuple[RejectedRetrieval, ...] = (),
    predeclared_discriminator: str | None = None,
    allowed_outcome_branches: Tuple[str, ...] = (),
    sequence_index: int = 0,
) -> PreScratchFibreFreezeHookResult:
    """Materialize or reuse a durable receipt before first hypothesis exposure."""

    if not hook_id:
        raise ValueError("hook_id is required")
    if not _ISO_UTC_RE.match(hook_invoked_at_utc):
        raise ValueError("hook_invoked_at_utc must be ISO-8601 UTC ending in 'Z'")

    if not consequential_turn:
        return PreScratchFibreFreezeHookResult(
            hook_id=hook_id,
            materialization_status=HookMaterializationStatus.SKIPPED_NOT_CONSEQUENTIAL,
            hook_invoked_at_utc=hook_invoked_at_utc,
            receipt=None,
            durable_receipt_pointer=None,
            reasons=("turn_not_consequential",),
        )

    if prior_materialized_receipt is not None:
        return PreScratchFibreFreezeHookResult(
            hook_id=hook_id,
            materialization_status=HookMaterializationStatus.ALREADY_MATERIALIZED,
            hook_invoked_at_utc=hook_invoked_at_utc,
            receipt=prior_materialized_receipt,
            durable_receipt_pointer=prior_materialized_receipt.episode_pointer,
            reasons=("durable_receipt_already_materialized",),
        )

    required = (
        receipt_id,
        framework_repository,
        framework_commit,
        application_repository,
        application_commit,
        task_id,
        atom_id,
        context_hash,
        fibre_snapshot_hash,
        predeclared_discriminator,
    )
    if any(value is None or (isinstance(value, str) and not value.strip()) for value in required):
        return PreScratchFibreFreezeHookResult(
            hook_id=hook_id,
            materialization_status=HookMaterializationStatus.CANNOT_CHECK,
            hook_invoked_at_utc=hook_invoked_at_utc,
            receipt=None,
            durable_receipt_pointer=None,
            reasons=("receipt_binding_incomplete",),
        )
    if not operator_ids or not allowed_outcome_branches:
        return PreScratchFibreFreezeHookResult(
            hook_id=hook_id,
            materialization_status=HookMaterializationStatus.CANNOT_CHECK,
            hook_invoked_at_utc=hook_invoked_at_utc,
            receipt=None,
            durable_receipt_pointer=None,
            reasons=("operator_or_outcome_branches_missing",),
        )

    receipt = materialize_pre_scratch_fibre_receipt(
        receipt_id=receipt_id,
        framework_repository=framework_repository,
        framework_commit=framework_commit,
        application_repository=application_repository,
        application_commit=application_commit,
        task_id=task_id,
        atom_id=atom_id,
        context_hash=context_hash,
        fibre_snapshot_hash=fibre_snapshot_hash,
        operator_ids=operator_ids,
        selected_retrievals=selected_retrievals,
        rejected_retrievals=rejected_retrievals,
        predeclared_discriminator=predeclared_discriminator,
        allowed_outcome_branches=allowed_outcome_branches,
        frozen_at_utc=hook_invoked_at_utc,
        sequence_index=sequence_index,
    )
    return PreScratchFibreFreezeHookResult(
        hook_id=hook_id,
        materialization_status=HookMaterializationStatus.MATERIALIZED,
        hook_invoked_at_utc=hook_invoked_at_utc,
        receipt=receipt,
        durable_receipt_pointer=receipt.episode_pointer,
        reasons=("durable_pre_action_receipt_materialized_before_hypothesis_exposure",),
    )


def compute_pre_scratch_chronology_qoi(
    observations: Sequence[PreScratchChronologyObservation],
) -> PreScratchChronologyQoIReport:
    """Compute the prospective chronology fraction stub. Not validated."""

    consequential = [item for item in observations if item.consequential]
    if not consequential:
        return PreScratchChronologyQoIReport(
            verdict=ChronologyQoIVerdict.CANNOT_CHECK,
            consequential_hypothesis_count=0,
            prospective_pre_exposure_count=0,
            prospective_pre_exposure_fraction=None,
            validation_status=QOI_VALIDATION_STATUS,
            reasons=("no_consequential_hypothesis_observations",),
        )

    prospective_count = 0
    reasons: list[str] = []
    for item in consequential:
        if item.receipt_frozen_at_utc is None:
            reasons.append(f"missing_receipt_timestamp:{item.hypothesis_id}")
            continue
        exposure_time = _parse_utc(item.first_exposed_at_utc)
        receipt_time = _parse_utc(item.receipt_frozen_at_utc)
        if exposure_time is None or receipt_time is None:
            reasons.append(f"timestamp_unparseable:{item.hypothesis_id}")
            continue
        if receipt_time < exposure_time:
            prospective_count += 1
        else:
            reasons.append(f"receipt_not_strictly_before_exposure:{item.hypothesis_id}")

    fraction = prospective_count / len(consequential)
    return PreScratchChronologyQoIReport(
        verdict=ChronologyQoIVerdict.COMPUTED,
        consequential_hypothesis_count=len(consequential),
        prospective_pre_exposure_count=prospective_count,
        prospective_pre_exposure_fraction=fraction,
        validation_status=QOI_VALIDATION_STATUS,
        reasons=tuple(reasons),
    )
