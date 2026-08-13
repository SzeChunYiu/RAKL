"""RSHEA Phase 6: observability reports — a pure, frozen, content-hashed
projection of the RSHEA artifacts an operator/governance layer needs to SEE.

An :class:`ObservabilityReport` is a read-only summary derived from the
evaluation epoch, the metric ledger, a meta-controller ``MetaDecisionReceipt``
(if the controller ran this epoch), and an ``EvolutionTrace`` (if evolution was
attempted). It is:

* **frozen** — a ``@dataclass(frozen=True)``; built once, never mutated;
* **tamper-evident** — ``source_content_hash`` seals the exact raw source
  artifacts (epoch, ledger receipt ids + authorities, the decision receipt, the
  evolution trace); ``content_hash`` seals the whole report. Re-deriving from
  the same sources reproduces both hashes bit-for-bit; changing any source
  field diverges them;
* **pure** — building a report never mutates its inputs and performs no I/O,
  and this module never imports or calls the live ``self_hosting_runtime``;
* **non-actionable** — a report is DESCRIPTIVE. It is an *observation of* the
  system, never a *signal to act on*, and it is not a metric receipt: it cannot
  be entered into a ledger, cannot be fed to the controller as a control input,
  and cannot back evolution evidence. The only place a SELECTED decision may
  become action is the governed bridge (P4/P5). ``is_actable`` is ``False`` by
  construction.

Reports exist so a human/governance layer can observe, at a glance, what epoch
the system is bound to, what the controller decided (and why, and which hard
gates gated it), and how evidence vs control inputs were kept separate —
without that observation feeding back into control. The v2 authority
non-interchangeability invariant holds throughout.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Optional, Tuple

from .evolution_trace import (
    EvaluationEpoch,
    EvolutionTrace,
    HardGateStatus,
    MetaDecisionReceipt,
    MetricLedger,
    canonical_hash,
)

_REPORT_SCHEMA_VERSION = "rakl-observability-report-v1"


@dataclass(frozen=True)
class ObservabilityReport:
    """Frozen, content-hashed projection of one evaluation epoch for an observer.

    Every field is derived from the source artifacts by
    :func:`build_observability_report`; nothing here is asserted, decided, or
    acted upon. ``decision_*`` / ``tournament_*`` fields are ``None``/empty when
    the controller did not run / no evolution was attempted this epoch.
    """

    schema_version: str
    evaluation_epoch_id: str
    # decision projection (None when the controller did not run this epoch)
    decision_id: Optional[str]
    decision_status: Optional[str]
    selected_action: Optional[str]
    runner_up_action: Optional[str]
    candidate_actions: Tuple[str, ...]
    decision_reasons: Tuple[str, ...]
    total_expected_utility: Optional[float]
    decision_component_summary: Tuple[Tuple[str, float, float], ...]
    # gate projection
    hard_gate_summary: Tuple[Tuple[str, str], ...]
    failed_gate_ids: Tuple[str, ...]
    # authority-separation projection (receipt counts by authority in the ledger)
    control_input_count: int
    evolution_evidence_count: int
    hard_protected_count: int
    descriptive_count: int
    # evolution projection (None when no trace this epoch)
    tournament_decision: Optional[str]
    archive_status: Optional[str]
    final_incumbent_id: Optional[str]
    changed_surfaces: Tuple[str, ...]
    trace_metric_receipt_count: int
    # integrity seal of the raw source artifacts
    source_content_hash: str

    @property
    def is_actable(self) -> bool:
        """Reports are DESCRIPTIVE — never a control input or evolution evidence."""
        return False

    @property
    def content_hash(self) -> str:
        """Tamper-evident seal of the whole report (re-derivable from sources)."""
        return canonical_hash(asdict(self))


def _authority_tallies(ledger: MetricLedger) -> Mapping[str, int]:
    tallies = {
        "CONTROL_INPUT": 0,
        "EVOLUTION_EVIDENCE": 0,
        "HARD_PROTECTED": 0,
        "DESCRIPTIVE": 0,
    }
    for receipt in ledger.receipts:
        tallies[receipt.authority.name] += 1
    return tallies


def build_observability_report(
    *,
    epoch: EvaluationEpoch,
    ledger: MetricLedger,
    decision_receipt: Optional[MetaDecisionReceipt] = None,
    evolution_trace: Optional[EvolutionTrace] = None,
) -> ObservabilityReport:
    """Project the RSHEA artifacts of one epoch into a frozen observability report.

    Pure: no mutation, no I/O. The decision receipt and evolution trace, when
    supplied, MUST be bound to ``epoch`` (same ``evaluation_epoch_id``); a report
    never silently crosses epochs. Every field is read off the inputs — the
    report decides nothing and acts on nothing.
    """
    if decision_receipt is not None and decision_receipt.evaluation_epoch_id != epoch.epoch_id:
        raise ValueError("observability report requires decision receipt bound to the epoch")
    if evolution_trace is not None and evolution_trace.evaluation_epoch_id != epoch.epoch_id:
        raise ValueError("observability report requires evolution trace bound to the epoch")

    tallies = _authority_tallies(ledger)

    if decision_receipt is not None:
        hard_gate_summary = tuple(
            (g.gate_id, g.status.name) for g in decision_receipt.hard_gate_observations
        )
        failed_gate_ids = tuple(
            g.gate_id
            for g in decision_receipt.hard_gate_observations
            if g.status is HardGateStatus.FAIL
        )
        decision_component_summary = tuple(
            (c.name, c.normalized_desirability, c.contribution) for c in decision_receipt.components
        )
        decision_id = decision_receipt.decision_id
        decision_status = decision_receipt.status.name
        selected_action = decision_receipt.selected_action
        runner_up_action = decision_receipt.runner_up_action
        candidate_actions = decision_receipt.candidate_actions
        decision_reasons = decision_receipt.reasons
        total_expected_utility = decision_receipt.total_expected_utility
    else:
        hard_gate_summary = ()
        failed_gate_ids = ()
        decision_component_summary = ()
        decision_id = None
        decision_status = None
        selected_action = None
        runner_up_action = None
        candidate_actions = ()
        decision_reasons = ()
        total_expected_utility = None

    if evolution_trace is not None:
        tournament_decision = evolution_trace.tournament_decision
        archive_status = evolution_trace.archive_status
        final_incumbent_id = evolution_trace.final_incumbent_id
        changed_surfaces = evolution_trace.changed_surfaces
        trace_metric_receipt_count = len(evolution_trace.metric_receipt_ids)
    else:
        tournament_decision = None
        archive_status = None
        final_incumbent_id = None
        changed_surfaces = ()
        trace_metric_receipt_count = 0

    # Seal the FULL sources — epoch, every ledger receipt (values included, not
    # just ids/authorities, so a changed value cannot slip past the seal), the
    # decision receipt, and the evolution trace. Any field change diverges this.
    source_content_hash = canonical_hash({
        "epoch": asdict(epoch),
        "ledger": tuple(asdict(r) for r in ledger.receipts),
        "decision_receipt": asdict(decision_receipt) if decision_receipt is not None else None,
        "evolution_trace": asdict(evolution_trace) if evolution_trace is not None else None,
    })

    return ObservabilityReport(
        schema_version=_REPORT_SCHEMA_VERSION,
        evaluation_epoch_id=epoch.epoch_id,
        decision_id=decision_id,
        decision_status=decision_status,
        selected_action=selected_action,
        runner_up_action=runner_up_action,
        candidate_actions=candidate_actions,
        decision_reasons=decision_reasons,
        total_expected_utility=total_expected_utility,
        decision_component_summary=decision_component_summary,
        hard_gate_summary=hard_gate_summary,
        failed_gate_ids=failed_gate_ids,
        control_input_count=tallies["CONTROL_INPUT"],
        evolution_evidence_count=tallies["EVOLUTION_EVIDENCE"],
        hard_protected_count=tallies["HARD_PROTECTED"],
        descriptive_count=tallies["DESCRIPTIVE"],
        tournament_decision=tournament_decision,
        archive_status=archive_status,
        final_incumbent_id=final_incumbent_id,
        changed_surfaces=changed_surfaces,
        trace_metric_receipt_count=trace_metric_receipt_count,
        source_content_hash=source_content_hash,
    )
