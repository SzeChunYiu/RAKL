"""Step 3 — run the frozen EVALUATOR.py (registered seed 20260814) and bind the
run through the RSHEA pipeline named in README.md / PROTOCOL.json:

  process_telemetry_to_receipts -> MetricLedger + build_evaluation_epoch +
  process_outcome_gate (hard gates EXECUTED: any FAIL halts with a typed
  non-verdict) -> shadow_decide -> interpret_controller_for_runtime
  (SELECTED -> OBJECT_SEARCH_READY, never authority) ->
  surface_governed_proposal (not actionable without external GovernanceSignOff)
  -> serialize_resumable_state / restore_resumable_state (content-hash
  tamper-evident round trip).

assess_resume_readiness (src/rakl/self_hosting_runtime.py) HOLDS authority; it
is not invoked here because no resume/promotion is attempted by this run and no
EvolutionArchive change is proposed. ladder.json is untouched.

Also computes the per-class and per-budget-class SR/FSR breakdown
(reporting only; the typed verdict comes solely from the frozen evaluator).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util

from common import (  # noqa: E402
    EVALUATOR_PATH, REGISTERED_SEED, RESULTS_DIR,
    build_run_epoch, receipt_from_dict, receipt_to_dict, sha256_file,
    utc_now_iso, verify_frozen_evaluator, verify_module_pins, write_json,
)

from rakl.evolution_trace import (  # noqa: E402
    HardGateStatus, MetricLedger, SelfModelSnapshot, canonical_hash,
)
from rakl.meta_controller import DecisionPolicy  # noqa: E402
from rakl.observability_adapters import (  # noqa: E402
    process_outcome_gate, process_telemetry_to_receipts, rakl_canonical_metrics,
)
from rakl.runtime_resumption import (  # noqa: E402
    restore_resumable_state, serialize_resumable_state,
)
from rakl.self_hosting_bridge import interpret_controller_for_runtime  # noqa: E402
from rakl.shadow_controller import shadow_decide  # noqa: E402
from rakl.governed_intervention import surface_governed_proposal  # noqa: E402
from rakl.v3_metrology import ProcessOutcome, ProcessTelemetry  # noqa: E402

_spec = importlib.util.spec_from_file_location("l4_frozen_evaluator_s3", EVALUATOR_PATH)
_frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frozen)
world_verified = _frozen.world_verified

CLASSES = ("N1", "N2", "N3", "N4", "N5", "N6", "N7")
BUDGET_CLASSES = ("TIGHT", "MEDIUM", "LOOSE")


def _breakdown(rows, decl, world_verified):
    n = len(rows)
    if n == 0:
        return None
    verified = sum(1 for r in rows if world_verified(r, decl[r["world_id"]]))
    declared = sum(1 for r in rows if decl[r["world_id"]]["declaration"] == "SOLVED")
    false_solves = sum(
        1 for r in rows
        if decl[r["world_id"]]["declaration"] == "SOLVED"
        and not world_verified(r, decl[r["world_id"]]))
    return {
        "n": n,
        "declared_solved": declared,
        "verified_solved": verified,
        "sr_within": verified / n,
        "false_solves": false_solves,
    }


def per_class_breakdown(corpus_rows, arm_out_path, world_verified):
    with open(arm_out_path, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["declarations"]
    decl = {d["world_id"]: d for d in rows}
    result = {}
    for klass in CLASSES:
        result[klass] = _breakdown(
            [r for r in corpus_rows if r["class"] == klass], decl, world_verified)
    for bclass in BUDGET_CLASSES:
        result[f"budget_{bclass}"] = _breakdown(
            [r for r in corpus_rows if r["budget_class"] == bclass],
            decl, world_verified)
    result["all_N"] = _breakdown(corpus_rows, decl, world_verified)
    return result


def main() -> int:
    verify_frozen_evaluator()
    module_pins_observed = verify_module_pins()
    with open(os.path.join(RESULTS_DIR, "rshea", "receipts_step2.json")) as handle:
        step2 = json.load(handle)
    arm_run_started_at = step2["arm_run_started_at"]

    corpus_path = os.path.join(RESULTS_DIR, "corpus_v1.json")
    arm_a_path = os.path.join(RESULTS_DIR, "arm_a_output.json")
    arm_b_path = os.path.join(RESULTS_DIR, "arm_b_output.json")
    audit_path = os.path.join(RESULTS_DIR, "AUDIT_RECEIPT.json")
    report_path = os.path.join(RESULTS_DIR, "evaluator_report.json")

    proc = subprocess.run(
        [sys.executable, EVALUATOR_PATH,
         "--corpus", corpus_path, "--arm-a", arm_a_path, "--arm-b", arm_b_path,
         "--audit", audit_path, "--arm-run-started-at", arm_run_started_at,
         "--seed", str(REGISTERED_SEED), "--out", report_path],
        capture_output=True, text=True)
    evaluator_exit = proc.returncode
    print(f"evaluator exit={evaluator_exit}")
    if evaluator_exit not in (0, 3):
        print(f"CANNOT_CHECK: evaluator crashed: {proc.stderr}", file=sys.stderr)
        return 3

    telemetry = ProcessTelemetry(
        invocation_id="benefit-l4-navigation-v1:evaluator",
        process_surface="benchmarking",
        task_id="BENEFIT-L4-NAVIGATION-V1",
        input_state_hash=sha256_file(corpus_path),
        output_state_hash=sha256_file(report_path),
        outcome=ProcessOutcome.SUCCESS if evaluator_exit == 0 else ProcessOutcome.CANNOT_CHECK,
        cost=0.0,
        cost_policy_id="wall-clock-seconds",
        residual_before=("L4-benefit-unmeasured",),
        residual_after=() if evaluator_exit == 0 else ("L4-benefit-unmeasured",),
        retained_novelty=(),
        evidence_pointers=(report_path,),
        timestamp=utc_now_iso(),
    )

    epoch = build_run_epoch()
    receipts_eval = process_telemetry_to_receipts(
        telemetry, epoch, rakl_canonical_metrics, sequence_base=9)
    write_json(os.path.join(RESULTS_DIR, "rshea", "receipts_step3.json"), {
        "telemetry": {**asdict(telemetry), "outcome": telemetry.outcome.value},
        "receipts": [receipt_to_dict(r) for r in receipts_eval],
    })

    # --- rebuild the full receipt chain into one ledger ----------------------
    with open(os.path.join(RESULTS_DIR, "rshea", "receipts_step1.json")) as handle:
        step1 = json.load(handle)
    all_receipt_dicts = (step1["receipts"] + step2["receipts"]
                         + [receipt_to_dict(r) for r in receipts_eval])
    all_receipts = tuple(receipt_from_dict(d) for d in all_receipt_dicts)
    ledger = MetricLedger(all_receipts)

    # --- hard gates: EXECUTED, not logged ------------------------------------
    def _telemetry_from(payload):
        data = dict(payload)
        data["outcome"] = ProcessOutcome(data["outcome"])
        for key in ("residual_before", "residual_after", "retained_novelty",
                    "retrieved_ids", "selected_ids", "rejected_ids",
                    "verification_ids", "evidence_pointers"):
            data[key] = tuple(tuple(x) if isinstance(x, list) else x
                              for x in data.get(key, ()))
        return ProcessTelemetry(**data)

    telemetries = ([_telemetry_from(step1["telemetry"])]
                   + [_telemetry_from(t) for t in step2["telemetry"]]
                   + [telemetry])
    outcome_receipts = [r for r in all_receipts if r.metric_name == "process_outcome"]
    gates = tuple(
        process_outcome_gate(t, process_outcome_receipt_id=r.metric_id,
                             gate_id=f"process_outcome_gate:{t.invocation_id}")
        for t, r in zip(telemetries, outcome_receipts)
    )
    failed = [g for g in gates if g.status is not HardGateStatus.PASS]
    if failed:
        write_json(os.path.join(RESULTS_DIR, "rshea", "pipeline_result.json"), {
            "halted_by_hard_gate": [asdict(g) | {"status": g.status.value} for g in failed],
            "typed_outcome": "CANNOT_CHECK",
        })
        print("HARD GATE FAIL -> run halted as CANNOT_CHECK", file=sys.stderr)
        return 3

    # --- shadow controller over the receipt chain ----------------------------
    control = tuple(receipts_eval[:2])
    policy = DecisionPolicy("policy:benefit-l4-navigation-v1", epoch.epoch_id,
                            (("operator_cost", 1.0), ("residual_contraction", 0.0)))
    self_model = SelfModelSnapshot(
        self_model_hash=canonical_hash(("benefit-l4-navigation-v1", "self-model")),
        genome_hash=canonical_hash(
            ("rakl", "L4", "support_solver.solve")),
        evaluation_epoch_id=epoch.epoch_id,
        episode_cutoff_hash=canonical_hash(("cutoff", arm_run_started_at)),
        context_signature=("BENEFIT-L4-NAVIGATION-V1",),
    )
    decision = shadow_decide(
        epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
        policy=policy, self_model=self_model, control_receipts=control,
        gates=gates, decision_id="decision:benefit-l4-navigation-v1-run-1")
    verdict = interpret_controller_for_runtime(decision)
    proposal = surface_governed_proposal(
        verdict, proposal_id="proposal:benefit-l4-navigation-v1-run-1", sign_off=None)

    envelope = serialize_resumable_state(
        epoch=epoch, ledger=ledger, decision_receipt=decision.receipt)
    restored = restore_resumable_state(envelope)
    roundtrip_ok = (restored.epoch == epoch and restored.ledger == ledger)

    with open(report_path, "r", encoding="utf-8") as handle:
        evaluator_report = json.load(handle)

    with open(corpus_path, "r", encoding="utf-8") as handle:
        corpus_rows = json.load(handle)["worlds"]

    pipeline = {
        "epoch_id": epoch.epoch_id,
        "ledger_receipt_count": len(ledger.receipts),
        "module_pins_observed": module_pins_observed,
        "hard_gates": [{"gate_id": g.gate_id, "status": g.status.value,
                        "reason": g.reason} for g in gates],
        "hard_gates_all_pass": True,
        "shadow_decision": {
            "decision_id": decision.receipt.decision_id,
            "status": decision.receipt.status.value,
            "acted_upon": decision.acted_upon,
            "input_content_hash": decision.input_content_hash,
        },
        "bridge_verdict": {
            "runtime_decision": verdict.runtime_decision.name,
            "controller_endorsed": verdict.controller_endorsed,
            "grants_authority": verdict.grants_authority,
            "governance_required_for_promotion": verdict.governance_required_for_promotion,
            "reasons": list(verdict.reasons),
        },
        "governed_proposal": None if proposal is None else {
            "proposal_id": proposal.proposal_id,
            "is_signed_off": proposal.is_signed_off,
            "is_actionable": proposal.is_actionable,
            "content_hash": proposal.content_hash,
            "note": "no external GovernanceSignOff exists; proposal is NOT actionable",
        },
        "resumable_state": {
            "epoch_content_hash": envelope.epoch_content_hash,
            "ledger_content_hash": envelope.ledger_content_hash,
            "decision_receipt_content_hash": envelope.decision_receipt_content_hash,
            "restore_roundtrip_ok": roundtrip_ok,
        },
        "authority_note": ("assess_resume_readiness (self_hosting_runtime) holds "
                           "resume/promotion authority; not invoked — no resume or "
                           "archive change attempted by this run; ladder.json untouched"),
        "evaluator_exit_code": evaluator_exit,
        "typed_outcome_from_frozen_evaluator": evaluator_report.get("verdict"),
    }
    write_json(os.path.join(RESULTS_DIR, "rshea", "pipeline_result.json"), pipeline)
    write_json(os.path.join(RESULTS_DIR, "per_class_breakdown.json"), {
        "arm_A_budgeted_raw_reading": per_class_breakdown(corpus_rows, arm_a_path, world_verified),
        "arm_B_distil_and_navigate": per_class_breakdown(corpus_rows, arm_b_path, world_verified),
    })
    print(json.dumps({
        "verdict": evaluator_report.get("verdict"),
        "delta_sr": evaluator_report.get("delta_sr"),
        "shadow_status": decision.receipt.status.value,
        "bridge": verdict.runtime_decision.name,
        "roundtrip_ok": roundtrip_ok,
    }, indent=2))
    return 0 if evaluator_exit == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
