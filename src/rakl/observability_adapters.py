"""RSHEA Phase 2: pure projection adapters from existing RAKL telemetry types
into the Phase-1 observability data model (:mod:`rakl.evolution_trace`).

These adapters READ existing, already-measured telemetry and PROJECT it into
typed observability objects (EvaluationEpoch / MetricReceipt / HardGateObservation
/ SelfModelSnapshot / EvolutionTrace). They never measure, score, aggregate-away,
or promote. Promotion authority stays with the existing epistemic-evolution /
governance path; the RSHEA v2 invariant holds: this module creates no second
measurement or promotion system.

Invariants (enforced structurally by the data model and by tests in
tests/test_observability_adapters.py):

* authority non-interchangeability — statistical evidence (PairedLiftVerdict,
  EvolutionTrial gains, attribution lift) is tagged EVOLUTION_EVIDENCE and is
  therefore NOT consumable by the controller as control-input or hard-gate
  receipts (rejected by meta_controller._validate_receipt_boundary). Operational
  signals (cost, residual contraction) are CONTROL_INPUT; correctness/identity/
  saturation preconditions are HARD_PROTECTED.
* frozen normalization — control bounds belong to the versioned MetricDefinition,
  never inferred from the candidate set.
* append-only backward lineage — receipts carry strictly increasing sequence_index
  and backward-only source_receipt_ids; MetricLedger rejects violations.
* epoch binding — every receipt references the EvaluationEpoch under which it was
  produced.
* hard gates executed not logged — EvolutionTrial.blocking_failures and
  SaturationVectorReport.bounded_saturated become HardGateObservation over
  HARD_PROTECTED receipts; a FAIL gate can never be compensated by positive utility.
* no absolute completeness — SaturationVectorReport.grants_absolute_completeness is
  always False; the saturation gate asserts only BOUNDED saturation, never absolute.

Sequence contract: each adapter accepts ``sequence_base`` (the next free
sequence_index for its epoch) and assigns sequence_base, sequence_base+1, ... to
its receipts in a stable order. The caller threads ``sequence_base + len(receipts)``
to the next adapter so a single MetricLedger stays globally increasing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .evolution_trace import (
    EvaluationEpoch,
    EvolutionTrace,
    GenomeSnapshot,
    HardGateObservation,
    HardGateStatus,
    MetricAuthority,
    MetricDefinition,
    MetricDirection,
    MetricReceipt,
    MetricRegistry,
    SelfModelSnapshot,
    canonical_hash,
)

# Canonical, frozen, versioned metric registry. Bounds on CONTROL_INPUT metrics
# are predeclared and versioned here, never inferred from a candidate set.
OPERATOR_COST_BOUND = 10_000.0
RESIDUAL_CONTRACTION_BOUND = 1_000.0

rakl_canonical_metrics = MetricRegistry(
    "rakl-canonical-v1",
    (
        MetricDefinition(
            "operator_cost", "v1", "cost_units",
            MetricDirection.MINIMIZE, MetricAuthority.CONTROL_INPUT,
            0.0, OPERATOR_COST_BOUND,
            "operator/episode resource cost; predeclared bound, versioned",
        ),
        MetricDefinition(
            "residual_contraction", "v1", "residuals",
            MetricDirection.MAXIMIZE, MetricAuthority.CONTROL_INPUT,
            0.0, RESIDUAL_CONTRACTION_BOUND,
            "net residuals removed by a process; predeclared bound, versioned",
        ),
        MetricDefinition("process_outcome", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="canonical process outcome precondition"),
        MetricDefinition("paired_lift_estimate", "v1", "lift",
                         MetricDirection.MAXIMIZE, MetricAuthority.EVOLUTION_EVIDENCE,
                         description="paired-difference point estimate (evidence, not control)"),
        MetricDefinition("attribution_lift", "v1", "lift",
                         MetricDirection.MAXIMIZE, MetricAuthority.EVOLUTION_EVIDENCE,
                         description="matched-design attribution lift (evidence, not control)"),
        MetricDefinition("development_gain", "v1", "delta",
                         MetricDirection.MAXIMIZE, MetricAuthority.EVOLUTION_EVIDENCE,
                         description="per-QoI development delta (evidence, not control)"),
        MetricDefinition("transfer_gain", "v1", "delta",
                         MetricDirection.MAXIMIZE, MetricAuthority.EVOLUTION_EVIDENCE,
                         description="per-QoI transfer delta (evidence, not control)"),
        MetricDefinition("authority_leakage", "v1", "leak",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="identity / authority-leak precondition (0 = pass)"),
        MetricDefinition("trial_validity", "v1", "failures",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="count of EvolutionTrial blocking failures"),
        MetricDefinition("candidate_identity", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="candidate identity verification precondition"),
        MetricDefinition("resource_comparability", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="parent/child resource comparability precondition"),
        MetricDefinition("history_preservation", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="append-only history preservation precondition"),
        MetricDefinition("bounded_saturation", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="BOUNDED saturation flag; never asserts absolute completeness"),
        MetricDefinition("attribution_validity", "v1", "flag",
                         MetricDirection.CONSTRAINT, MetricAuthority.HARD_PROTECTED,
                         description="matched-design attribution structural validity"),
    ),
)


def build_evaluation_epoch(
    registry: MetricRegistry,
    *,
    benchmark_protocol_hash: str,
    evaluator_hash: str,
    model_tool_harness_hash: str,
    decision_policy_hash: str,
    observatory_instrumentation_hash: str,
    epoch_id: str | None = None,
) -> EvaluationEpoch:
    """Construct an EvaluationEpoch bound to ``registry`` and the given identities.

    All identity inputs are sha256-stamped (canonical_hash) so the epoch's
    post-init sha256 requirement is satisfied regardless of caller format.
    """
    bh = _sha(benchmark_protocol_hash)
    eh = _sha(evaluator_hash)
    mh = _sha(model_tool_harness_hash)
    dh = _sha(decision_policy_hash)
    oh = _sha(observatory_instrumentation_hash)
    rid = epoch_id or "epoch:" + canonical_hash(
        (registry.registry_hash, bh, eh, mh, dh, oh)
    )[:16]
    return EvaluationEpoch(
        epoch_id=rid,
        metric_registry_hash=registry.registry_hash,
        evaluator_hash=eh,
        benchmark_protocol_hash=bh,
        model_tool_harness_hash=mh,
        decision_policy_hash=dh,
        observatory_instrumentation_hash=oh,
    )


def _sha(value: object) -> str:
    """Return a sha256 hex for any value (pass-through if already 64-hex)."""
    if isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return value
    return canonical_hash(value)


def _receipt(
    registry: MetricRegistry,
    name: str,
    *,
    epoch_id: str,
    value: float,
    candidate_hash: str,
    dataset_hash: str,
    evaluator_hash: str,
    resource_profile_hash: str,
    sequence_index: int,
    metric_id: str,
    sample_n: int = 1,
    ci_low: float | None = None,
    ci_high: float | None = None,
    source_receipt_ids: Tuple[str, ...] = (),
) -> MetricReceipt:
    definition = registry.by_name()[name]
    return MetricReceipt(
        metric_id=metric_id,
        metric_name=name,
        definition_hash=definition.definition_hash,
        epoch_id=epoch_id,
        value=value,
        unit=definition.unit,
        sample_n=sample_n,
        candidate_hash=_sha(candidate_hash),
        dataset_hash=_sha(dataset_hash),
        evaluator_hash=_sha(evaluator_hash),
        resource_profile_hash=_sha(resource_profile_hash),
        authority=definition.authority,
        sequence_index=sequence_index,
        ci_low=ci_low,
        ci_high=ci_high,
        source_receipt_ids=source_receipt_ids,
    )


def _mid(prefix: str, epoch_id: str, sequence_index: int) -> str:
    """Deterministic, ledger-unique metric id (sequence_index is globally unique)."""
    return f"{prefix}:{epoch_id}:{sequence_index}"


# --- ProcessOutcome pass/fail boundary (members confirmed in v3_metrology) -----
_PROCESS_OUTCOME_PASS = frozenset({"SUCCESS", "PARTIAL_SUCCESS"})


def process_telemetry_to_receipts(
    telemetry,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_base: int = 0,
) -> Tuple[MetricReceipt, ...]:
    """Project a ProcessTelemetry into CONTROL_INPUT receipts (cost, residual
    contraction) and a HARD_PROTECTED process_outcome receipt.

    Cost and residual contraction are genuine operational control inputs; the
    process outcome is a hard precondition. Nothing here is statistical evidence.
    """
    cand = telemetry.output_state_hash or telemetry.invocation_id
    ds = telemetry.task_id
    ev = telemetry.process_surface
    rp = telemetry.cost_policy_id
    cost = _receipt(
        registry, "operator_cost", epoch_id=epoch.epoch_id, value=float(telemetry.cost),
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev, resource_profile_hash=rp,
        sequence_index=sequence_base, metric_id=_mid("operator_cost", epoch.epoch_id, sequence_base),
    )
    contraction = _receipt(
        registry, "residual_contraction", epoch_id=epoch.epoch_id,
        value=float(telemetry.raw_residual_contraction),
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev, resource_profile_hash=rp,
        sequence_index=sequence_base + 1, metric_id=_mid("residual_contraction", epoch.epoch_id, sequence_base + 1),
        source_receipt_ids=(cost.metric_id,),
    )
    outcome_value = 0.0 if telemetry.outcome.value in _PROCESS_OUTCOME_PASS else 1.0
    outcome = _receipt(
        registry, "process_outcome", epoch_id=epoch.epoch_id, value=outcome_value,
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev, resource_profile_hash=rp,
        sequence_index=sequence_base + 2, metric_id=_mid("process_outcome", epoch.epoch_id, sequence_base + 2),
        source_receipt_ids=(contraction.metric_id,),
    )
    return (cost, contraction, outcome)


def process_outcome_gate(
    telemetry,
    *,
    process_outcome_receipt_id: str,
    gate_id: str = "process_outcome_gate",
) -> HardGateObservation:
    """Hard gate over the process_outcome receipt; FAIL on failure/blocked/cannot-check."""
    status = HardGateStatus.PASS if telemetry.outcome.value in _PROCESS_OUTCOME_PASS else HardGateStatus.FAIL
    return HardGateObservation(
        gate_id=gate_id,
        status=status,
        metric_receipt_ids=(process_outcome_receipt_id,),
        reason=f"process_outcome={telemetry.outcome.value}",
    )


def task_episode_to_receipts(
    episode,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_base: int = 0,
) -> Tuple[MetricReceipt, ...]:
    """Project a TaskEpisode into a single CONTROL_INPUT operator_cost receipt.

    Episodes are evidence roots; only their declared cost is a control input here.
    The episode's outcome/verification lineage is preserved verbatim via its
    evidence_pointers, not re-summarized.
    """
    return (
        _receipt(
            registry, "operator_cost", epoch_id=epoch.epoch_id, value=float(episode.cost),
            candidate_hash=episode.fibre_snapshot_hash, dataset_hash=episode.context_hash,
            evaluator_hash=("task_episode", episode.episode_id),
            resource_profile_hash=("task_episode", episode.atom_id),
            sequence_index=sequence_base,
            metric_id=_mid("operator_cost", epoch.epoch_id, sequence_base),
        ),
    )


def paired_lift_to_receipt(
    verdict,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_index: int,
    candidate_hash: str,
    dataset_hash: str,
    evaluator_hash: str,
    resource_profile_hash: str,
) -> MetricReceipt:
    """Project a PairedLiftVerdict into an EVOLUTION_EVIDENCE receipt.

    Authority is EVOLUTION_EVIDENCE: this receipt carries the statistical lift
    (point estimate + CI) for governance lineage but CANNOT be consumed by the
    controller as a control-input or hard-gate receipt.
    """
    return _receipt(
        registry, "paired_lift_estimate", epoch_id=epoch.epoch_id,
        value=float(verdict.point_estimate),
        candidate_hash=candidate_hash, dataset_hash=dataset_hash,
        evaluator_hash=evaluator_hash, resource_profile_hash=resource_profile_hash,
        sequence_index=sequence_index,
        metric_id=_mid("paired_lift_estimate", epoch.epoch_id, sequence_index),
        sample_n=int(verdict.n),
        ci_low=float(verdict.ci_lo), ci_high=float(verdict.ci_hi),
    )


def attribution_packet_to_epoch(
    packet,
    registry: MetricRegistry,
    *,
    decision_policy_hash: str,
    observatory_instrumentation_hash: str,
) -> EvaluationEpoch:
    """Bind an AttributionPacket's matched-design identities into an EvaluationEpoch.

    The packet does not itself carry a scalar lift; the lift is a PairedLiftVerdict
    computed over its runs (use paired_lift_to_receipt under this epoch).
    """
    return build_evaluation_epoch(
        registry,
        benchmark_protocol_hash=packet.rakl_protocol_hash,
        evaluator_hash=packet.evaluator_protocol_hash,
        model_tool_harness_hash=(
            packet.model_only_protocol_hash, packet.rakl_protocol_hash, packet.learned_state_hash
        ),
        decision_policy_hash=decision_policy_hash,
        observatory_instrumentation_hash=observatory_instrumentation_hash,
        epoch_id="epoch:attribution:" + _sha(packet.benchmark_id)[:16],
    )


def attribution_validity_artifacts(
    packet,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_index: int,
    gate_id: str = "attribution_validity_gate",
) -> Tuple[MetricReceipt, HardGateObservation]:
    """HARD_PROTECTED receipt + gate for matched-design structural validity.

    FAIL (does not pass) when the packet's before-runs were not frozen, since a
    non-frozen baseline cannot ground a causal attribution.
    """
    receipt = _receipt(
        registry, "attribution_validity", epoch_id=epoch.epoch_id,
        value=0.0 if packet.frozen_before_runs else 1.0,
        candidate_hash=packet.learned_state_hash, dataset_hash=packet.benchmark_id,
        evaluator_hash=packet.evaluator_protocol_hash,
        resource_profile_hash=(packet.model_only_protocol_hash, packet.rakl_protocol_hash),
        sequence_index=sequence_index,
        metric_id=_mid("attribution_validity", epoch.epoch_id, sequence_index),
    )
    gate = HardGateObservation(
        gate_id=gate_id,
        status=HardGateStatus.PASS if packet.frozen_before_runs else HardGateStatus.FAIL,
        metric_receipt_ids=(receipt.metric_id,),
        reason="frozen_before_runs=" + str(packet.frozen_before_runs),
    )
    return receipt, gate


def saturation_to_self_model(
    report,
    *,
    genome_hash: str,
    episode_cutoff_hash: str,
    epoch_id: str,
) -> SelfModelSnapshot:
    """Project a SaturationVectorReport into a SelfModelSnapshot.

    Preserves grants_absolute_completeness=False: the context signature records
    per-axis BOUNDED flatness, never a claim of absolute completeness.
    """
    signature = tuple(
        f"axis:{getattr(ax, 'value', ax)}:bounded_flat={report.flat(ax)}"
        for ax in report.required_axes
    ) + (f"bounded_saturated={report.bounded_saturated}",)
    if not signature:
        signature = ("no_required_axes",)
    return SelfModelSnapshot(
        self_model_hash=_sha((genome_hash, epoch_id, signature)),
        genome_hash=_sha(genome_hash),
        evaluation_epoch_id=epoch_id,
        episode_cutoff_hash=_sha(episode_cutoff_hash),
        context_signature=signature,
    )


def bounded_saturation_artifacts(
    report,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_index: int,
    candidate_hash: str,
    dataset_hash: str,
    evaluator_hash: str,
    resource_profile_hash: str,
    gate_id: str = "bounded_saturation_gate",
) -> Tuple[MetricReceipt, HardGateObservation]:
    """HARD_PROTECTED receipt + gate for BOUNDED saturation only.

    The gate passes iff report.bounded_saturated. Critically, even a PASS asserts
    only bounded saturation — report.grants_absolute_completeness is always False,
    so this never claims absolute completeness (asserted by tests).
    """
    receipt = _receipt(
        registry, "bounded_saturation", epoch_id=epoch.epoch_id,
        value=0.0 if report.bounded_saturated else 1.0,
        candidate_hash=candidate_hash, dataset_hash=dataset_hash,
        evaluator_hash=evaluator_hash, resource_profile_hash=resource_profile_hash,
        sequence_index=sequence_index,
        metric_id=_mid("bounded_saturation", epoch.epoch_id, sequence_index),
    )
    gate = HardGateObservation(
        gate_id=gate_id,
        status=HardGateStatus.PASS if report.bounded_saturated else HardGateStatus.FAIL,
        metric_receipt_ids=(receipt.metric_id,),
        reason="bounded_saturated=" + str(report.bounded_saturated)
        + ";absolute_completeness=" + str(report.grants_absolute_completeness),
    )
    return receipt, gate


def _genome(version: str) -> GenomeSnapshot:
    return GenomeSnapshot(
        variant_id=version,
        genome_hash=_sha(version),
        parent_ids=(),
        surfaces=(),
        resource_profile=(),
    )


def _verification_gate(
    registry: MetricRegistry,
    name: str,
    *,
    verified: bool | None,
    epoch: EvaluationEpoch,
    sequence_index: int,
    candidate_hash: str,
    dataset_hash: str,
    evaluator_hash: str,
    resource_profile_hash: str,
    gate_id: str,
    fail_reason: str,
) -> Tuple[MetricReceipt, HardGateObservation]:
    """HARD_PROTECTED receipt + gate for a True/False/None verification flag.

    None (unverified) maps to UNKNOWN, which the controller treats as blocking
    (non-PASS), so a trial cannot sneak through on an unverified precondition.
    """
    if verified is True:
        value, status = 0.0, HardGateStatus.PASS
    elif verified is False:
        value, status = 1.0, HardGateStatus.FAIL
    else:
        value, status = 0.5, HardGateStatus.UNKNOWN
    receipt = _receipt(
        registry, name, epoch_id=epoch.epoch_id, value=value,
        candidate_hash=candidate_hash, dataset_hash=dataset_hash,
        evaluator_hash=evaluator_hash, resource_profile_hash=resource_profile_hash,
        sequence_index=sequence_index, metric_id=_mid(name, epoch.epoch_id, sequence_index),
    )
    gate = HardGateObservation(
        gate_id=gate_id, status=status, metric_receipt_ids=(receipt.metric_id,),
        reason=fail_reason + "=" + str(verified),
    )
    return receipt, gate


@dataclass(frozen=True)
class EvolutionTrialProjection:
    """Result of projecting an EvolutionTrial: trace + evidence/gate receipts + gates."""

    trace: EvolutionTrace
    receipts: Tuple[MetricReceipt, ...]
    hard_gates: Tuple[HardGateObservation, ...]


def evolution_trial_to_projection(
    trial,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_base: int = 0,
    decision_receipt_id: str = "",
    evaluator_hash: str = "evolution_trial",
) -> EvolutionTrialProjection:
    """Project an EvolutionTrial into evidence receipts + hard gates + an EvolutionTrace.

    Development/transfer gains are EVOLUTION_EVIDENCE (governance-consumable, NOT
    controller-consumable). Blocking failures and verification flags become
    HARD_PROTECTED gates; any FAIL/UNKNOWN blocks regardless of gain magnitude.
    The trace records EVIDENCE ONLY — tournament decision and promotion stay with
    the governance path (P4/P5), never asserted here.
    """
    receipts: list = []
    dev_ids: list = []
    transfer_ids: list = []
    seq = sequence_base
    cand = trial.child_version
    ds = trial.development_benchmark_id
    rp = (trial.parent_version, trial.child_version)

    for qoi in trial.development_gain_qois:
        r = _receipt(
            registry, "development_gain", epoch_id=epoch.epoch_id,
            value=float(trial.development_improvements[qoi]),
            candidate_hash=cand, dataset_hash=(ds, qoi), evaluator_hash=evaluator_hash,
            resource_profile_hash=rp, sequence_index=seq,
            metric_id=_mid("development_gain", epoch.epoch_id, seq),
        )
        receipts.append(r); dev_ids.append(r.metric_id); seq += 1
    if trial.transfer_improvements:
        for qoi in trial.transfer_gain_qois:
            r = _receipt(
                registry, "transfer_gain", epoch_id=epoch.epoch_id,
                value=float(trial.transfer_improvements[qoi]),
                candidate_hash=cand, dataset_hash=(trial.assurance_benchmark_id or ds, qoi),
                evaluator_hash=evaluator_hash, resource_profile_hash=rp, sequence_index=seq,
                metric_id=_mid("transfer_gain", epoch.epoch_id, seq),
            )
            receipts.append(r); transfer_ids.append(r.metric_id); seq += 1

    gates: list = []
    # trial_validity: FAIL on any blocking failure (never compensated by gains).
    tv_value = float(len(trial.blocking_failures))
    tv = _receipt(
        registry, "trial_validity", epoch_id=epoch.epoch_id, value=tv_value,
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=evaluator_hash,
        resource_profile_hash=rp, sequence_index=seq,
        metric_id=_mid("trial_validity", epoch.epoch_id, seq),
    )
    receipts.append(tv); seq += 1
    gates.append(HardGateObservation(
        gate_id="trial_validity_gate",
        status=HardGateStatus.PASS if not trial.blocking_failures else HardGateStatus.FAIL,
        metric_receipt_ids=(tv.metric_id,),
        reason="blocking_failures=" + str(len(trial.blocking_failures)),
    ))
    for name, gid, reason in (
        ("candidate_identity", "candidate_identity_gate", "candidate_identity_verified"),
        ("resource_comparability", "resource_comparability_gate", "resource_comparability_verified"),
        ("history_preservation", "history_preservation_gate", "history_preserved"),
    ):
        flag = getattr(trial, {"candidate_identity": "candidate_identity_verified",
                               "resource_comparability": "resource_comparability_verified",
                               "history_preservation": "history_preserved"}[name])
        r, g = _verification_gate(
            registry, name, verified=flag, epoch=epoch, sequence_index=seq,
            candidate_hash=cand, dataset_hash=ds, evaluator_hash=evaluator_hash,
            resource_profile_hash=rp, gate_id=gid, fail_reason=reason,
        )
        receipts.append(r); gates.append(g); seq += 1

    trace = EvolutionTrace(
        trace_id="trace:" + _sha((epoch.epoch_id, trial.parent_version, trial.child_version, ds))[:24],
        evaluation_epoch_id=epoch.epoch_id,
        parent=_genome(trial.parent_version),
        challenger=_genome(trial.child_version),
        triggering_episode_ids=(),
        root_cause_receipt_ids=tuple(dev_ids),
        changed_surfaces=(),
        prediction_metric_ids=(),
        development_metric_ids=tuple(dev_ids),
        assurance_metric_ids=tuple(transfer_ids),
        attribution_metric_ids=(),
        decision_receipt_id=decision_receipt_id,
        tournament_decision="EVIDENCE_PROJECTED_NO_TOURNAMENT",
        archive_status="projected_not_promoted",
        final_incumbent_id=trial.parent_version,
        rollback_variant_id=trial.parent_version,
        metric_receipt_ids=tuple(r.metric_id for r in receipts),
    )
    return EvolutionTrialProjection(trace, tuple(receipts), tuple(gates))
