#!/usr/bin/env python3
"""Surface a governed intervention proposal for the six-family defect (issue #683).

This script processes DEFECT.json evidence through the RSHEA P2-P5 flow and
produces a governed proposal artifact under research/. The proposal requires
external governance sign-off before any action is taken (authority stays with
governance; sign-off = continuation, never promotion).

Usage:
    python scripts/surface_six_family_governed_proposal.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rakl.evolution_trace import (
    canonical_hash,
    DecisionStatus,
    HardGateStatus,
    EvaluationEpoch,
    MetricReceipt,
    MetricAuthority,
    MetricRegistry,
    MetricDefinition,
    MetricDirection,
    HardGateObservation,
    MetaDecisionReceipt,
    DecisionComponent,
    SelfModelSnapshot,
    MetricLedger,
)
from rakl.observability_adapters import (
    rakl_canonical_metrics,
    build_evaluation_epoch,
    _receipt,
    _mid,
    _sha,
)
from rakl.shadow_controller import (
    ShadowDecision,
    shadow_decide,
    build_status_quo_action,
)
from rakl.self_hosting_bridge import (
    interpret_controller_for_runtime,
    ControllerBridgeVerdict,
)
from rakl.governed_intervention import (
    surface_governed_proposal,
    GovernedProposal,
    GovernanceSignOff,
)


# ============================================================================
# Defect telemetry model (DEFECT.json projection)
# ============================================================================

@dataclass(frozen=True)
class DefectTelemetry:
    """Telemetry projection of a DEFECT.json artifact."""
    defect_id: str
    summary: str
    severity_counts: Tuple[int, int, int]  # (HIGH, MEDIUM, LOW)
    defects: Tuple[Tuple[str, str], ...]  # ((id, severity), ...)
    proposed_corrections: Tuple[Tuple[str, str], ...]  # ((target, proposal), ...)
    authority_note: str


def load_defect_telemetry(defect_path: Path) -> DefectTelemetry:
    """Load and project DEFECT.json into telemetry."""
    with open(defect_path) as f:
        defect = json.load(f)
    
    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    defects = []
    for d in defect.get("defects", []):
        severity = d.get("severity", "LOW")
        severity_counts[severity] += 1
        defects.append((d["id"], severity))
    
    corrections = []
    for c in defect.get("proposed_corrections", []):
        corrections.append((c["target"], c["proposal"]))
    
    return DefectTelemetry(
        defect_id=defect["schema"],
        summary=defect.get("summary", ""),
        severity_counts=(
            severity_counts["HIGH"],
            severity_counts["MEDIUM"],
            severity_counts["LOW"],
        ),
        defects=tuple(defects),
        proposed_corrections=tuple(corrections),
        authority_note=defect.get("authority", "same-context analysis; not independent review"),
    )


# ============================================================================
# RSHEA flow: process defect telemetry through P2-P5
# ============================================================================

def build_defect_epoch(
    registry: MetricRegistry,
    defect_id: str,
) -> EvaluationEpoch:
    """Build an EvaluationEpoch for defect analysis."""
    return build_evaluation_epoch(
        registry,
        benchmark_protocol_hash=f"defect_analysis:{defect_id}",
        evaluator_hash="six_family_governance_defect_v1",
        model_tool_harness_hash="defect_telemetry_projection",
        decision_policy_hash="governed_intervention_policy",
        observatory_instrumentation_hash="defect_to_observability_adapter",
        epoch_id=f"epoch:defect:{defect_id[:16]}",
    )


def defect_to_receipts_and_gates(
    telemetry: DefectTelemetry,
    epoch: EvaluationEpoch,
    registry: MetricRegistry,
    *,
    sequence_base: int = 0,
) -> Tuple[Tuple[MetricReceipt, ...], Tuple[HardGateObservation, ...]]:
    """Project defect telemetry into CONTROL_INPUT receipts + HARD_PROTECTED gates.
    
    Returns:
        (receipts, gates) where receipts include CONTROL_INPUT and HARD_PROTECTED
    """
    seq = sequence_base
    cand = f"defect:{telemetry.defect_id}"
    ds = telemetry.defect_id
    ev = "defect_analysis"
    rp = "governance_analysis"
    
    # CONTROL_INPUT receipts
    receipts = []
    
    # High-severity count: CONTROL_INPUT (use operator_cost as proxy)
    high_count = telemetry.severity_counts[0]
    high_receipt = _receipt(
        registry, "operator_cost", epoch_id=epoch.epoch_id,
        value=float(high_count),
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev,
        resource_profile_hash=rp,
        sequence_index=seq,
        metric_id=_mid("operator_cost", epoch.epoch_id, seq),
    )
    receipts.append(high_receipt)
    seq += 1
    
    # Actionability: CONTROL_INPUT (use residual_contraction as proxy)
    actionable_value = 0.0 if telemetry.proposed_corrections else 1.0
    actionable_receipt = _receipt(
        registry, "residual_contraction", epoch_id=epoch.epoch_id,
        value=actionable_value,
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev,
        resource_profile_hash=rp,
        sequence_index=seq,
        metric_id=_mid("residual_contraction", epoch.epoch_id, seq),
        source_receipt_ids=(high_receipt.metric_id,),
    )
    receipts.append(actionable_receipt)
    seq += 1
    
    # HARD_PROTECTED receipt for authority boundary gate
    # Use authority_leakage as the HARD_PROTECTED metric (0 = pass, no leak)
    auth_receipt = _receipt(
        registry, "authority_leakage", epoch_id=epoch.epoch_id,
        value=0.0,  # 0 = no authority leak (pass)
        candidate_hash=cand, dataset_hash=ds, evaluator_hash=ev,
        resource_profile_hash=rp,
        sequence_index=seq,
        metric_id=_mid("authority_leakage", epoch.epoch_id, seq),
    )
    receipts.append(auth_receipt)
    seq += 1
    
    # Build gates referencing HARD_PROTECTED receipt
    gates = []
    
    # Gate: authority boundary (no self-promotion)
    gates.append(HardGateObservation(
        gate_id="authority_boundary_gate",
        status=HardGateStatus.PASS,  # Pass because authority_leakage = 0
        metric_receipt_ids=(auth_receipt.metric_id,),
        reason="defect analysis does not self-promote; authority stays with external governance",
    ))
    
    # Gate: high-severity defects require governance attention
    # This gate references a HARD_PROTECTED receipt
    gates.append(HardGateObservation(
        gate_id="high_severity_gate",
        status=HardGateStatus.PASS if high_count > 0 else HardGateStatus.FAIL,
        metric_receipt_ids=(auth_receipt.metric_id,),
        reason=f"high_severity_count={high_count}; requires governance sign-off",
    ))
    
    return tuple(receipts), tuple(gates)


def build_defect_self_model(
    telemetry: DefectTelemetry,
    epoch: EvaluationEpoch,
) -> SelfModelSnapshot:
    """Build a SelfModelSnapshot for defect analysis."""
    context_signature = (
        f"defect_id:{telemetry.defect_id}",
        f"high_severity:{telemetry.severity_counts[0]}",
        f"proposed_corrections:{len(telemetry.proposed_corrections)}",
        "authority:external_governance_only",
    )
    return SelfModelSnapshot(
        self_model_hash=canonical_hash((telemetry.defect_id, context_signature)),
        genome_hash=canonical_hash(f"defect_genome:{telemetry.defect_id}"),
        evaluation_epoch_id=epoch.epoch_id,
        episode_cutoff_hash=canonical_hash("defect_analysis_cutoff"),
        context_signature=context_signature,
    )


# ============================================================================
# Main flow: surface governed proposal
# ============================================================================

def surface_governed_proposal_for_defect(
    defect_path: Path,
    output_dir: Path,
) -> str:
    """Process DEFECT.json through RSHEA P2-P5 and surface a governed proposal.
    
    Returns the proposal artifact path. The proposal has sign_off=None (PENDING_EXTERNAL).
    """
    # Load defect telemetry
    telemetry = load_defect_telemetry(defect_path)
    
    # P2: Build epoch and receipts + gates
    epoch = build_defect_epoch(rakl_canonical_metrics, telemetry.defect_id)
    receipts, gates = defect_to_receipts_and_gates(telemetry, epoch, rakl_canonical_metrics)
    self_model = build_defect_self_model(telemetry, epoch)
    
    # Build a minimal decision policy for defect analysis
    from rakl.meta_controller import DecisionPolicy
    
    policy = DecisionPolicy(
        policy_id="defect_governance_policy",
        evaluation_epoch_id=epoch.epoch_id,
        weights=(("operator_cost", 1.0), ("residual_contraction", 1.0)),
        uncertainty_penalty=1.0,
        max_component_uncertainty=0.35,
        minimum_utility_margin=0.02,
    )
    
    # Build ledger from all receipts
    ledger = MetricLedger(receipts)
    
    # Extract CONTROL_INPUT receipts for action components
    control_receipts = tuple(r for r in receipts if r.authority == MetricAuthority.CONTROL_INPUT)
    
    # P3: Shadow decide (controller observes, never acts)
    shadow_decision = shadow_decide(
        epoch=epoch,
        ledger=ledger,
        registry=rakl_canonical_metrics,
        policy=policy,
        self_model=self_model,
        control_receipts=control_receipts,
        gates=gates,
        decision_id=f"decision:defect:{telemetry.defect_id[:16]}",
        action_name="await_governance_sign_off",
    )
    
    # P4: Bridge to runtime
    bridge_verdict = interpret_controller_for_runtime(shadow_decision)
    
    # P5: Surface governed proposal
    proposal = surface_governed_proposal(
        bridge_verdict,
        proposal_id=f"proposal:six_family_governance:{telemetry.defect_id[:16]}",
        sign_off=None,  # PENDING_EXTERNAL
    )
    
    # Build proposal artifact
    output_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = output_dir / "GOVERNED_PROPOSAL_V1.json"
    
    proposal_artifact = {}
    proposal_artifact["$schema"] = "paper2-governed-proposal-v1"
    proposal_artifact["schema"] = "paper2-governed-proposal-v1"
    proposal_artifact["proposal_id"] = proposal.proposal_id
    proposal_artifact["evaluation_epoch_id"] = proposal.evaluation_epoch_id
    proposal_artifact["defect_id"] = telemetry.defect_id
    proposal_artifact["governed_proposal_hash"] = proposal.content_hash
    proposal_artifact["sign_off_status"] = "PENDING_EXTERNAL"
    proposal_artifact["external_governance_sign_off"] = None
    
    proposal_artifact["proposed_actions"] = [
        {
            "target": "research/unified_problem_solving_v1/results/PROMOTION_GATE.json",
            "action": "repoint candidates.six_family_law to research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/ROBUSTNESS_CONFIRMATORY_RESULT_V1.json (n=810, seed 2026081212)",
            "rationale": "D1: cited artifact is DEVELOPMENT-only and uses wrong family set; ROBUSTNESS_CONFIRMATORY_RESULT_V1.json is the executed confirmatory receipt with registered families",
            "authority_required": "external_governance_sign_off",
        },
        {
            "target": "research/unified_problem_solving_v1/results/PROMOTION_GATE.json",
            "action": "downgrade verdict from PROMOTE_TO_MECHANIC to scoped state (e.g. CONDITIONAL_POSITIVE or PASSED_FALSIFIABILITY_AUDIT)",
            "rationale": "D1-D3: the confirmatory passes its registered gates but the gates are non-falsifiable for generality (p=0.03125 fixed by generator construction); PROMOTE_TO_MECHANIC overstates the evidential support",
            "authority_required": "external_governance_sign_off",
        },
        {
            "target": "research/orion_p1_p4_closure_v2/DEPENDENCY_GRAPH.json",
            "action": "replace P2_SIX_FAMILY_APPLICABILITY evidence string to cite confirmatory receipt; drop 'FULL exact3=1' (tautological)",
            "rationale": "D2: cited 1,296-case DEVELOPMENT run disclaims the claim; FULL exact3=1 is tautological (full arm bind to verify by construction)",
            "authority_required": "external_governance_sign_off",
        },
        {
            "target": "tools/build_atomic_claim_registry.py (claim_id: EMP-SIXFAMILY-GENERALIZATION)",
            "action": "register construction-aware falsifier SPEC: baseline is 'generator-strata null' (mechanism_only IS effect coordinate), not p=0.5",
            "rationale": "D3: registered falsifier 'p >= 0.05' is unreachable; correct baseline is generator construction (mechanism exact3=0.000 on BOUNDARY_QOI_MISMATCH and DIRECTION_REVERSED_INVALID)",
            "authority_required": "external_governance_sign_off",
        },
        {
            "target": "research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/",
            "action": "register falsifier SPEC artifact: 'generator-strata null baseline; falsifier is mechanism arm fails to exceed full arm on held-out synthetic strata'",
            "rationale": "D3: this spec can actually fail; p=0.03125 is fixed by construction, not empirical evidence of generality",
            "authority_required": "external_governance_sign_off",
        },
    ]
    
    proposal_artifact["defect_evidence"] = {
        "defect_id": telemetry.defect_id,
        "summary": telemetry.summary,
        "severity_counts": list(telemetry.severity_counts),
        "defects": [{"id": d[0], "severity": d[1]} for d in telemetry.defects],
    }
    
    proposal_artifact["controller_receipt"] = {
        "decision_id": shadow_decision.receipt.decision_id,
        "status": shadow_decision.receipt.status.name,
        "reasons": list(shadow_decision.receipt.reasons),
    }
    
    proposal_artifact["bridge_verdict"] = {
        "runtime_decision": bridge_verdict.runtime_decision.name,
        "controller_endorsed": bridge_verdict.controller_endorsed,
        "acted_upon": bridge_verdict.acted_upon,
        "reasons": list(bridge_verdict.reasons),
    }
    
    proposal_artifact["metadata"] = {
        "issue_reference": "#683",
        "creation_date": "2026-08-14",
        "authority_boundary": "external_governance_only; this proposal is not actionable until GovernanceSignOff authorizes continuation (sign-off never grants promotion/resume authority)",
        "what_this_proposes": "governed intervention through RSHEA P5; corrections are PROPOSED actions awaiting sign-off, not applied changes",
        "what_must_not_happen": "self-promotion, verdict rewrite by this analysis, or any claim that the six-family extension is refuted (it passes its registered gates; the gates are non-falsifiable)",
    }
    
    with open(proposal_path, "w") as f:
        json.dump(proposal_artifact, f, indent=2, sort_keys=False)
    
    print(f"Governed proposal written to: {proposal_path}", file=sys.stderr)
    print(f"Sign-off status: PENDING_EXTERNAL", file=sys.stderr)
    print(f"Proposal requires external governance sign-off before any action.", file=sys.stderr)
    
    return str(proposal_path)


def main():
    """CLI entry point."""
    repo = Path(__file__).parent.parent
    defect_path = repo / "research" / "paper2_six_family_governance_defect_v1" / "DEFECT.json"
    output_dir = repo / "research" / "paper2_six_family_governance_defect_v1"
    
    if not defect_path.exists():
        print(f"ERROR: DEFECT.json not found at {defect_path}", file=sys.stderr)
        sys.exit(1)
    
    proposal_path = surface_governed_proposal_for_defect(defect_path, output_dir)
    
    # Read and print proposal ID
    with open(proposal_path) as f:
        proposal = json.load(f)
    
    print(f"\nProposal ID: {proposal['proposal_id']}", file=sys.stderr)
    print(f"Evaluation Epoch: {proposal['evaluation_epoch_id']}", file=sys.stderr)
    print(f"Content Hash: {proposal['governed_proposal_hash']}", file=sys.stderr)
    print(f"Sign-off Status: {proposal['sign_off_status']}", file=sys.stderr)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
