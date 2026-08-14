"""Shared identity/receipt plumbing for the BENEFIT-L0-FCR-V1 execution run.

Run-local harness code (NOT part of the frozen protocol; the frozen artifacts are
PROTOCOL.json / EVALUATOR.py / CORPUS_PLAN.md, whose hashes this module verifies).

Epoch identity is a pure function of the frozen artifact hashes plus the harness
content hashes, so every step of the run reconstructs the identical
EvaluationEpoch deterministically. Receipts are serialized after construction at
the chronological point required by the protocol (corpus freeze BEFORE arms) and
re-materialized bit-identically for the final ledger.
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
FROZEN_EVALUATOR_SHA256 = "536ba0e21899207449de8333446fa9c67ed50b51f048f93ac68f2ba8d4afb273"
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


def build_run_epoch():
    """Deterministic epoch bound to the frozen protocol + evaluator + harness identity.

    model_tool_harness_hash covers the corpus generator and the arm harness (the
    code that produces candidate declarations); decision_policy_hash is the frozen
    PROTOCOL.json (the decision thresholds live there); observatory hash is a fixed
    binding label so later steps rebuild the identical epoch.
    """
    protocol_sha = sha256_file(PROTOCOL_PATH)
    evaluator_sha = verify_frozen_evaluator()
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
        observatory_instrumentation_hash="benefit-l0-fcr-v1-rshea-binding-v1",
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
