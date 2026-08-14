"""Step 1 — generate the known-answer chain corpus and freeze it into the RSHEA
receipt chain BEFORE any arm executes (PROTOCOL.json label_independence_safeguards[0]).

Outputs (all sha256-receipted in freeze_manifest.json):
- corpus_v1.json            full corpus incl. gold labels (evaluator input)
- corpus_v1_stripped.json   arm input: gold_label/class/world stripped
- audit_sample.json         40 seed-sampled chains: surface text + gold ONLY
- worlds_v1.json            hidden-world truth (debug artifact, never arm input)
- rshea/epoch.json          EvaluationEpoch identity
- rshea/receipts_step1.json corpus-freeze telemetry receipts (sequence 0-2)
"""
from __future__ import annotations

import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    REGISTERED_SEED, RESULTS_DIR, build_run_epoch, receipt_to_dict,
    sha256_file, utc_now_iso, verify_module_pins, write_json,
)
from generate_corpus import class_invariant_checks, generate  # noqa: E402

from rakl.observability_adapters import (  # noqa: E402
    process_telemetry_to_receipts, rakl_canonical_metrics,
)
from rakl.v3_metrology import ProcessOutcome, ProcessTelemetry  # noqa: E402
from rakl.evolution_trace import canonical_hash  # noqa: E402

ARM_INPUT_FIELDS = ("chain_id", "skeleton", "contract", "surface_text")


def main() -> int:
    t0 = time.monotonic()
    module_pins_observed = verify_module_pins()
    corpus, worlds_meta = generate()
    errors = class_invariant_checks(corpus["chains"])
    if errors:
        for e in errors[:20]:
            print(f"INVARIANT FAIL: {e}", file=sys.stderr)
        return 2

    corpus_path = os.path.join(RESULTS_DIR, "corpus_v1.json")
    stripped_path = os.path.join(RESULTS_DIR, "corpus_v1_stripped.json")
    audit_path = os.path.join(RESULTS_DIR, "audit_sample.json")
    worlds_path = os.path.join(RESULTS_DIR, "worlds_v1.json")

    corpus_sha = write_json(corpus_path, corpus)
    stripped = {
        "protocol_id": corpus["protocol_id"],
        "note": "arm input; gold_label/class/world stripped per PROTOCOL.json",
        "chains": [{k: row[k] for k in ARM_INPUT_FIELDS} for row in corpus["chains"]],
    }
    stripped_sha = write_json(stripped_path, stripped)

    rng_audit = random.Random(REGISTERED_SEED)
    by_id = {row["chain_id"]: row for row in corpus["chains"]}
    audit_ids = rng_audit.sample(sorted(by_id), 40)
    audit_sample = {
        "note": ("auditor-facing sample: ONLY the rendered chain description and the "
                 "gold label; no machine fields, no class field, no arm outputs exist yet"),
        "sample_seed": REGISTERED_SEED,
        "chains": [
            {
                "chain_id": cid,
                "surface_text": by_id[cid]["surface_text"],
                "gold_label": by_id[cid]["gold_label"],
            }
            for cid in audit_ids
        ],
    }
    audit_sha = write_json(audit_path, audit_sample)
    worlds_sha = write_json(worlds_path, worlds_meta)

    epoch = build_run_epoch()
    elapsed = time.monotonic() - t0
    telemetry = ProcessTelemetry(
        invocation_id="benefit-l1-composition-v1:corpus-freeze",
        process_surface="benchmarking",
        task_id="BENEFIT-L1-COMPOSITION-V1",
        input_state_hash=canonical_hash(("generator", REGISTERED_SEED)),
        output_state_hash=corpus_sha,
        outcome=ProcessOutcome.SUCCESS,
        cost=elapsed,
        cost_policy_id="wall-clock-seconds",
        residual_before=("L1-benefit-unmeasured",),
        residual_after=("L1-benefit-unmeasured",),
        retained_novelty=(),
        evidence_pointers=(corpus_path, stripped_path),
        timestamp=utc_now_iso(),
    )
    receipts = process_telemetry_to_receipts(
        telemetry, epoch, rakl_canonical_metrics, sequence_base=0)

    from dataclasses import asdict
    write_json(os.path.join(RESULTS_DIR, "rshea", "epoch.json"), asdict(epoch))
    write_json(os.path.join(RESULTS_DIR, "rshea", "receipts_step1.json"), {
        "telemetry": {**asdict(telemetry), "outcome": telemetry.outcome.value},
        "receipts": [receipt_to_dict(r) for r in receipts],
    })
    write_json(os.path.join(RESULTS_DIR, "freeze_manifest.json"), {
        "protocol_id": "BENEFIT-L1-COMPOSITION-V1",
        "frozen_at": utc_now_iso(),
        "label_minted_at": corpus["generated_at"],
        "generator_seed": REGISTERED_SEED,
        "epoch_id": epoch.epoch_id,
        "module_pins_observed": module_pins_observed,
        "artifacts": {
            "corpus_v1.json": corpus_sha,
            "corpus_v1_stripped.json": stripped_sha,
            "audit_sample.json": audit_sha,
            "worlds_v1.json": worlds_sha,
            "harness/generate_corpus.py": sha256_file(
                os.path.join(RESULTS_DIR, "harness", "generate_corpus.py")),
            "harness/arm_harness.py": sha256_file(
                os.path.join(RESULTS_DIR, "harness", "arm_harness.py")),
        },
        "arms_executed_yet": False,
    })
    print(f"step1 OK: corpus sha256={corpus_sha} epoch={epoch.epoch_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
