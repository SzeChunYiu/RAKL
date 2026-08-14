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

Also computes the per-class FCR/TCR breakdown (reporting only; the typed verdict
comes solely from the frozen evaluator).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    FROZEN_EVALUATOR_SHA256, EVALUATOR_PATH, REGISTERED_SEED, RESULTS_DIR,
    build_run_epoch, receipt_from_dict, receipt_to_dict, sha256_file,
    utc_now_iso, verify_frozen_evaluator, write_json,
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

CLASSES = ("C1", "C2", "C3", "C4", "C5")


def per_class_breakdown(corpus_rows, arm_out_path):
    with open(arm_out_path, "r", encoding="utf-8") as handle:
        decl = {d["pair_id"]: d["declaration"]
                for d in json.load(handle)["declarations"]}
    result = {}
    for klass in CLASSES:
        rows = [r for r in corpus_rows if r["class"] == klass]
        n = len(rows)
        fc = sum(1 for r in rows
                 if decl[r["pair_id"]] == "CONTRADICTION"
                 and r["gold_label"] != "CONTRADICTION")
        gold_pos = [r for r in rows if r["gold_label"] == "CONTRADICTION"]
        tc = sum(1 for r in gold_pos if decl[r["pair_id"]] == "CONTRADICTION")
        result[klass] = {
            "n": n,
            "false_contradictions": fc,
            "fcr_within_class": fc / n,
            "gold_contradictions": len(gold_pos),
            "true_contradictions_declared": tc,
            "tcr_within_class": (tc / len(gold_pos)) if gold_pos else None,
        }
    return result


def main() -> int:
    verify_frozen_evaluator()
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
        invocation_id="benefit-l0-fcr-v1:evaluator",
        process_surface="benchmarking",
        task_id="BENEFIT-L0-FCR-V1",
        input_state_hash=sha256_file(corpus_path),
        output_state_hash=sha256_file(report_path),
        outcome=ProcessOutcome.SUCCESS if evaluator_exit == 0 else ProcessOutcome.CANNOT_CHECK,
        cost=0.0,
        cost_policy_id="wall-clock-seconds",
        residual_before=("L0-benefit-unmeasured",),
        residual_after=() if evaluator_exit == 0 else ("L0-benefit-unmeasured",),
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
    # The status-quo action requires unique component names (one receipt per
    # metric): use the latest (evaluator-step) cost/contraction receipts as the
    # control components; the full receipt chain remains in the ledger.
    control = tuple(receipts_eval[:2])
    policy = DecisionPolicy("policy:benefit-l0-fcr-v1", epoch.epoch_id,
                            (("operator_cost", 1.0), ("residual_contraction", 0.0)))
    self_model = SelfModelSnapshot(
        self_model_hash=canonical_hash(("benefit-l0-fcr-v1", "self-model")),
        genome_hash=canonical_hash(("rakl", "L0", "core.compare_contexts")),
        evaluation_epoch_id=epoch.epoch_id,
        episode_cutoff_hash=canonical_hash(("cutoff", arm_run_started_at)),
        context_signature=("BENEFIT-L0-FCR-V1",),
    )
    decision = shadow_decide(
        epoch=epoch, ledger=ledger, registry=rakl_canonical_metrics,
        policy=policy, self_model=self_model, control_receipts=control,
        gates=gates, decision_id="decision:benefit-l0-fcr-v1-run-1")
    verdict = interpret_controller_for_runtime(decision)
    proposal = surface_governed_proposal(
        verdict, proposal_id="proposal:benefit-l0-fcr-v1-run-1", sign_off=None)

    envelope = serialize_resumable_state(
        epoch=epoch, ledger=ledger, decision_receipt=decision.receipt)
    restored = restore_resumable_state(envelope)
    roundtrip_ok = (restored.epoch == epoch and restored.ledger == ledger)

    with open(report_path, "r", encoding="utf-8") as handle:
        evaluator_report = json.load(handle)

    with open(corpus_path, "r", encoding="utf-8") as handle:
        corpus_rows = json.load(handle)["pairs"]

    pipeline = {
        "epoch_id": epoch.epoch_id,
        "ledger_receipt_count": len(ledger.receipts),
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
        "arm_A": per_class_breakdown(corpus_rows, arm_a_path),
        "arm_B": per_class_breakdown(corpus_rows, arm_b_path),
    })
    print(json.dumps({
        "verdict": evaluator_report.get("verdict"),
        "delta_fcr": evaluator_report.get("delta_fcr"),
        "shadow_status": decision.receipt.status.value,
        "bridge": verdict.runtime_decision.name,
        "roundtrip_ok": roundtrip_ok,
    }, indent=2))
    return 0 if evaluator_exit == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
