"""Host pre-scratch fibre freeze hook and chronology QoI stub (#464).

Unit tests exercise hook materialization and the prospective fraction stub.
They do **not** validate chronology improvement — validation_status remains
NOT_VALIDATED_STUB until a fresh prospective discriminator is executed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rakl.pre_action_receipt import RetrievalAuthority, SelectedRetrieval
from rakl.pre_scratch_fibre_freeze import (
    ChronologyQoIVerdict,
    HookMaterializationStatus,
    PreScratchChronologyObservation,
    compute_pre_scratch_chronology_qoi,
    run_pre_scratch_fibre_freeze_hook,
)

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
FRAMEWORK_COMMIT = "1fe6477aac2299a210e99e1624e9f7e795a2a6d4"
APPLICATION_COMMIT = "6557b1b25fa839fe71aba8047c958d5da892edd8"
PAYLOAD_HASH = "b" * 64


def _hook_kwargs(**overrides: object) -> dict[str, object]:
    base = dict(
        hook_id="hook-1",
        hook_invoked_at_utc="2026-08-12T07:00:00Z",
        consequential_turn=True,
        receipt_id="R-pre-scratch-1",
        framework_repository="SzeChunYiu/RAKL",
        framework_commit=FRAMEWORK_COMMIT,
        application_repository="SzeChunYiu/RAKL_math",
        application_commit=APPLICATION_COMMIT,
        task_id="T-1",
        atom_id="A-1",
        context_hash="ctx-1",
        fibre_snapshot_hash="fibre-1",
        operator_ids=("op.freeze_before_exposure",),
        selected_retrievals=(
            SelectedRetrieval(
                retrieval_id="K-canonical-1",
                authority=RetrievalAuthority.CANONICAL,
                payload_hash=PAYLOAD_HASH,
            ),
        ),
        predeclared_discriminator="F=1: scaling branch separates before hypothesis scratch",
        allowed_outcome_branches=("SUCCESS", "FAILURE"),
    )
    base.update(overrides)
    return base


def test_hook_materializes_durable_receipt_before_exposure() -> None:
    result = run_pre_scratch_fibre_freeze_hook(**_hook_kwargs())
    assert result.materialization_status is HookMaterializationStatus.MATERIALIZED
    assert result.receipt is not None
    assert result.durable_receipt_pointer is not None
    assert result.receipt.frozen_at_utc == "2026-08-12T07:00:00Z"
    assert result.receipt.episode_pointer == result.durable_receipt_pointer


def test_hook_reuses_prior_materialized_receipt() -> None:
    first = run_pre_scratch_fibre_freeze_hook(**_hook_kwargs())
    second = run_pre_scratch_fibre_freeze_hook(
        **_hook_kwargs(
            hook_invoked_at_utc="2026-08-12T07:01:00Z",
            prior_materialized_receipt=first.receipt,
        )
    )
    assert second.materialization_status is HookMaterializationStatus.ALREADY_MATERIALIZED
    assert second.receipt is first.receipt
    assert second.durable_receipt_pointer == first.durable_receipt_pointer


def test_non_consequential_turn_skips_materialization() -> None:
    result = run_pre_scratch_fibre_freeze_hook(**_hook_kwargs(consequential_turn=False))
    assert result.materialization_status is HookMaterializationStatus.SKIPPED_NOT_CONSEQUENTIAL
    assert result.receipt is None


def test_incomplete_binding_cannot_check() -> None:
    result = run_pre_scratch_fibre_freeze_hook(
        hook_id="hook-incomplete",
        hook_invoked_at_utc="2026-08-12T07:02:00Z",
        consequential_turn=True,
    )
    assert result.materialization_status is HookMaterializationStatus.CANNOT_CHECK
    assert "receipt_binding_incomplete" in result.reasons


def test_qoi_fraction_counts_receipt_before_exposure_only() -> None:
    report = compute_pre_scratch_chronology_qoi(
        [
            PreScratchChronologyObservation(
                hypothesis_id="H-1",
                consequential=True,
                first_exposed_at_utc="2026-08-12T07:05:00Z",
                receipt_frozen_at_utc="2026-08-12T07:00:00Z",
            ),
            PreScratchChronologyObservation(
                hypothesis_id="H-2",
                consequential=True,
                first_exposed_at_utc="2026-08-12T07:03:00Z",
                receipt_frozen_at_utc="2026-08-12T07:04:00Z",
            ),
            PreScratchChronologyObservation(
                hypothesis_id="H-3",
                consequential=False,
                first_exposed_at_utc="2026-08-12T07:06:00Z",
                receipt_frozen_at_utc="2026-08-12T07:00:00Z",
            ),
        ]
    )
    assert report.verdict is ChronologyQoIVerdict.COMPUTED
    assert report.consequential_hypothesis_count == 2
    assert report.prospective_pre_exposure_count == 1
    assert report.prospective_pre_exposure_fraction == 0.5
    assert report.validation_status == "NOT_VALIDATED_STUB"
    assert report.validated is False
    assert "receipt_not_strictly_before_exposure:H-2" in report.reasons


def test_qoi_cannot_check_without_consequential_observations() -> None:
    report = compute_pre_scratch_chronology_qoi(
        [
            PreScratchChronologyObservation(
                hypothesis_id="H-cheap",
                consequential=False,
                first_exposed_at_utc="2026-08-12T07:05:00Z",
                receipt_frozen_at_utc="2026-08-12T07:00:00Z",
            ),
        ]
    )
    assert report.verdict is ChronologyQoIVerdict.CANNOT_CHECK
    assert report.prospective_pre_exposure_fraction is None


def test_hook_and_qoi_documents_validate_against_schemas() -> None:
    import json

    import jsonschema

    hook_schema = json.loads(
        (SCHEMAS / "pre-scratch-fibre-freeze-hook-result-v1.schema.json").read_text()
    )
    qoi_schema = json.loads((SCHEMAS / "pre-scratch-chronology-qoi-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(hook_schema)
    jsonschema.Draft202012Validator.check_schema(qoi_schema)

    hook_doc = run_pre_scratch_fibre_freeze_hook(**_hook_kwargs()).document()
    jsonschema.validate(hook_doc, hook_schema)

    qoi_doc = compute_pre_scratch_chronology_qoi(
        [
            PreScratchChronologyObservation(
                hypothesis_id="H-1",
                consequential=True,
                first_exposed_at_utc="2026-08-12T07:05:00Z",
                receipt_frozen_at_utc="2026-08-12T07:00:00Z",
            ),
        ]
    ).document()
    jsonschema.validate(qoi_doc, qoi_schema)
