"""Shared identity/receipt plumbing for the BENEFIT-L2-GLUING-V1 execution run.

Run-local harness code (NOT part of the frozen protocol; the frozen artifacts are
PROTOCOL.json / EVALUATOR.py / CORPUS_PLAN.md, whose hashes this module verifies).

Epoch identity is a pure function of the frozen artifact hashes plus the harness
content hashes, so every step of the run reconstructs the identical
EvaluationEpoch deterministically.

Module pin (PROTOCOL.json arms.B_obstruction_retaining_gluing.module_pins) is
verified here at every step, INCLUDING the repaired-semantics precondition
(_recompute_cover_topology present); drift is CANNOT_CHECK, never adapted around.
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
FROZEN_EVALUATOR_SHA256 = "b237ca0c5d75d51571b6aa272e1b8dfa43e35e60b4ceda74bd035dfdabfb33dc"
MODULE_PINS = {
    "src/rakl/atlas_gluing.py": "f6f00fceda0628422d597bce06679baf872c207b922e5acac1aea86f2ca12aac",
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
    """PIN_DRIFT check for the repaired atlas module; CANNOT_CHECK on drift.

    Also verifies the semantic precondition of the pin rule: the run-environment
    module must contain _recompute_cover_topology (repaired declared-topology
    semantics from PR #649); the pre-repair module is CANNOT_CHECK."""
    observed: dict[str, str] = {}
    for rel_path, frozen in MODULE_PINS.items():
        full = os.path.join(REPO_ROOT, rel_path)
        actual = sha256_file(full)
        observed[rel_path] = actual
        if actual != frozen:
            raise SystemExit(
                f"CANNOT_CHECK(PIN_DRIFT): {rel_path} sha256 {actual} != pinned {frozen}"
            )
        with open(full, "r", encoding="utf-8") as handle:
            if "_recompute_cover_topology" not in handle.read():
                raise SystemExit(
                    f"CANNOT_CHECK(PIN_DRIFT): {rel_path} lacks _recompute_cover_topology; "
                    "pre-repair semantics"
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
        observatory_instrumentation_hash="benefit-l2-gluing-v1-rshea-binding-v1",
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
