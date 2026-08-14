"""Shared identity/receipt plumbing for the BENEFIT-L1-COMPOSITION-V1 execution run.

Run-local harness code (NOT part of the frozen protocol; the frozen artifacts are
PROTOCOL.json / EVALUATOR.py / CORPUS_PLAN.md, whose hashes this module verifies).

Epoch identity is a pure function of the frozen artifact hashes plus the harness
content hashes, so every step of the run reconstructs the identical
EvaluationEpoch deterministically. Receipts are serialized after construction at
the chronological point required by the protocol (corpus freeze BEFORE arms) and
re-materialized bit-identically for the final ledger.

Module pins (PROTOCOL.json arms.B_typed_transition_algebra.module_pins) are
verified here at every step; drift is CANNOT_CHECK, never adapted around.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone

RESULTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTO_DIR = os.path.dirname(RESULTS_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(PROTO_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from rakl.evolution_trace import MetricAuthority, MetricReceipt  # noqa: E402
from rakl.observability_adapters import (  # noqa: E402
    build_evaluation_epoch,
    rakl_canonical_metrics,
)

REGISTERED_SEED = 20260814
FROZEN_EVALUATOR_SHA256 = "f206d15610afc7fbd0cbc86e1d131f477fa4d02f638a783607b2afe45e3f580c"
MODULE_PINS = {
    "src/rakl/bridge_composition.py": "11a5368dccbdf10dac505915193e7c3f0e830d71cd514aa40889383ffbd47302",
    "src/rakl/similarity.py": "97dedb16784866649ff01e80075b32d65593788d0455e2179728062e0aeb546e",
}
PROTOCOL_PATH = os.path.join(PROTO_DIR, "PROTOCOL.json")
EVALUATOR_PATH = os.path.join(PROTO_DIR, "EVALUATOR.py")
HARNESS_DIR = os.path.join(RESULTS_DIR, "harness")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now_iso() -> str:
    """Seconds-precision UTC ISO with Z — one fixed format everywhere so the
    evaluator's lexicographic label-before-arm comparison is well defined."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_frozen_evaluator() -> str:
    actual = sha256_file(EVALUATOR_PATH)
    if actual != FROZEN_EVALUATOR_SHA256:
        raise SystemExit(
            f"CANNOT_CHECK: EVALUATOR.py sha256 {actual} != frozen "
            f"{FROZEN_EVALUATOR_SHA256}; protocol hash binding broken"
        )
    return actual


def verify_module_pins() -> dict[str, str]:
    """PIN_DRIFT check for the exact bound framework modules; CANNOT_CHECK on drift."""
    observed: dict[str, str] = {}
    for rel_path, frozen in MODULE_PINS.items():
        actual = sha256_file(os.path.join(REPO_ROOT, rel_path))
        observed[rel_path] = actual
        if actual != frozen:
            raise SystemExit(
                f"CANNOT_CHECK(PIN_DRIFT): {rel_path} sha256 {actual} != pinned {frozen}"
            )
    return observed


def build_run_epoch():
    """Deterministic epoch bound to the frozen protocol + evaluator + harness identity."""
    protocol_sha = sha256_file(PROTOCOL_PATH)
    evaluator_sha = verify_frozen_evaluator()
    verify_module_pins()
    harness_sha = hashlib.sha256(
        (
            sha256_file(os.path.join(HARNESS_DIR, "generate_corpus.py"))
            + sha256_file(os.path.join(HARNESS_DIR, "arm_harness.py"))
        ).encode()
    ).hexdigest()
    return build_evaluation_epoch(
        rakl_canonical_metrics,
        benchmark_protocol_hash=protocol_sha,
        evaluator_hash=evaluator_sha,
        model_tool_harness_hash=harness_sha,
        decision_policy_hash=protocol_sha,
        observatory_instrumentation_hash="benefit-l1-composition-v1-rshea-binding-v1",
    )


def receipt_to_dict(receipt: MetricReceipt) -> dict:
    payload = asdict(receipt)
    payload["authority"] = receipt.authority.value
    return payload


def receipt_from_dict(payload: dict) -> MetricReceipt:
    data = dict(payload)
    data["authority"] = MetricAuthority(data["authority"])
    data["source_receipt_ids"] = tuple(data.get("source_receipt_ids") or ())
    return MetricReceipt(**data)


def write_json(path: str, payload: object) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
    return sha256_file(path)
