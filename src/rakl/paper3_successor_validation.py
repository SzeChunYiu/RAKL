"""Paper III powered non-circular successor freeze (#326).

Closes the pre-label redesign window with an explicit terminal state. Demoted
AI_OPERATOR payloads do not count as the first real independent human label.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paper3_annotation import canonical_sha256
from .paper3_power_design import (
    CONFIG_PATH,
    DECISION_PATH,
    RESULTS_PATH,
    ZERO_LABELS_PATH,
    build_zero_labels_at_power_design,
    evaluate_power_decision,
    git_head_sha,
)

SUCCESSOR_DIR = Path("research/paper3_successor_validation_v1")
MACHINE_WITNESS_PROTOCOL_PATH = SUCCESSOR_DIR / "MACHINE_WITNESS_PROTOCOL.json"
ANTI_CIRCULARITY_PROTOCOL_PATH = SUCCESSOR_DIR / "ANTI_CIRCULARITY_PROTOCOL.json"
SEMANTIC_CONTROL_MANIFEST_PATH = SUCCESSOR_DIR / "SEMANTIC_CONTROL_MANIFEST.json"
ZERO_LABELS_REPO_WIDE_PATH = SUCCESSOR_DIR / "ZERO_LABELS_REPO_WIDE_RECEIPT.json"
DECISION_RECEIPT_PATH = SUCCESSOR_DIR / "DECISION_RECEIPT.json"
PACKET_FREEZE_RECEIPT_PATH = SUCCESSOR_DIR / "PACKET_FREEZE_RECEIPT.json"
TERMINAL_RECEIPT_PATH = SUCCESSOR_DIR / "ISSUE_326_TERMINAL_RECEIPT.json"

_TERMINAL_STATES = frozenset(
    {
        "POWERED_SUCCESSOR_FROZEN_ZERO_LABELS",
        "POWER_LIMITED_RETAIN_V2_1",
        "WINDOW_CLOSED_USE_V2_1_POWER_LIMITED",
        "CANNOT_ESTABLISH_ZERO_LABELS",
    }
)


def build_machine_witness_protocol() -> dict[str, Any]:
    return {
        "schema_version": "paper3-machine-witness-protocol-v1",
        "protocol_id": "paper3-machine-witness-v2-1-prelabel",
        "issue": 326,
        "status": "FROZEN_BEFORE_INDEPENDENT_LABELS",
        "extractor": {
            "kind": "DETERMINISTIC_COORDINATE_RENDER_PLUS_REGISTERED_MODEL_OR_RULE",
            "module_hooks": [
                "src/rakl/paper3_confirmatory_gate.py",
                "src/rakl/paper3_witness_decoupling.py",
            ],
            "forbidden_inputs": [
                "human_transfer_valid_label",
                "human_witness_subcoordinates",
                "adjudication_output",
                "other_annotator_output",
                "expected_outcome_metadata",
            ],
            "output_contract": [
                "role_mapping",
                "preserved_invariants",
                "non_preserved_properties",
                "target_boundary_compatibility",
                "qoi_alignment",
                "directionality_completeness",
                "licensed_transfer_state_or_CANNOT_CHECK",
            ],
        },
        "failures_preserved": True,
        "human_labels_may_enter_extractor": False,
        "claim_boundary": (
            "Protocol freeze only. No machine-witness scores are claimed here; "
            "extractor outputs must be frozen in MACHINE_WITNESS_OUTPUTS.jsonl "
            "before independent labels are unsealed."
        ),
        "grants_scientific_authority": False,
    }


def build_anti_circularity_protocol() -> dict[str, Any]:
    return {
        "schema_version": "paper3-anti-circularity-protocol-v1",
        "protocol_id": "paper3-anti-circularity-v2-1-prelabel",
        "issue": 326,
        "binds": [
            "research/receipts/PAPER3_WITNESS_LABEL_DECOUPLING_FREEZE_20260811.json",
            "src/rakl/paper3_witness_decoupling.py",
        ],
        "diagnostics_before_labels": [
            "decoupling_rate_human = mean(transfer_valid != AND(human witness coordinates))",
            "machine_witness_predicts_human_transfer_valid",
        ],
        "minimum_informative_decoupled_count": 4,
        "if_definitionally_coupled": "NOT_INFORMATIVE_DEFINITIONAL_COUPLING",
        "claim_boundary": (
            "Diagnostic freeze only. Does not authorize confirmatory PASS or training."
        ),
        "grants_scientific_authority": False,
    }


def build_semantic_control_manifest(repo_root: Path) -> dict[str, Any]:
    provenance_path = repo_root / "research/PAPER3_BGE_MODEL_PROVENANCE_20260811.json"
    strong_control_path = (
        repo_root / "research/receipts/PAPER3_STRONG_CONTROL_FREEZE_20260811.json"
    )
    provenance = (
        json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance_path.is_file()
        else {}
    )
    strong = (
        json.loads(strong_control_path.read_text(encoding="utf-8"))
        if strong_control_path.is_file()
        else {}
    )
    return {
        "schema_version": "paper3-semantic-control-manifest-v1",
        "manifest_id": "paper3-semantic-control-v2-1-prelabel",
        "issue": 326,
        "comparator": {
            "model_id": provenance.get("model_id", "BAAI/bge-reranker-v2-m3"),
            "revision_binding": provenance_path.as_posix() if provenance_path.is_file() else None,
            "strong_control_freeze": strong_control_path.as_posix()
            if strong_control_path.is_file()
            else None,
            "strong_control_status": strong.get("status"),
        },
        "rules": [
            "deterministic source/target render",
            "no structural labels/outcomes in render",
            "hash render bytes before scoring",
            "compute descriptor/score before human labels",
            "preserve inconvenient semantic scores",
        ],
        "shopping_after_labels_forbidden": True,
        "claim_boundary": (
            "Manifest freeze only. Does not claim descriptor completeness if model "
            "assets remain unavailable."
        ),
        "grants_scientific_authority": False,
    }


def decide_successor_terminal(
    *,
    zero_labels: dict[str, Any],
    power_evaluation: dict[str, Any],
) -> dict[str, Any]:
    issue_scan = zero_labels.get("issue_217_scan") or {}
    if issue_scan.get("first_real_independent_label_present"):
        terminal = "WINDOW_CLOSED_USE_V2_1_POWER_LIMITED"
        rationale = (
            "Independent external label payloads are already present; the powered "
            "successor redesign window is closed. Retain v2.1 as power-limited."
        )
    elif zero_labels.get("state") != "ZERO_LABELS_OBSERVED":
        terminal = "CANNOT_ESTABLISH_ZERO_LABELS"
        rationale = "Repo-wide independent zero-label status could not be established."
    elif power_evaluation.get("path") == "B" and power_evaluation.get(
        "expansion_feasible_within_ceiling"
    ):
        terminal = "POWERED_SUCCESSOR_FROZEN_ZERO_LABELS"
        rationale = (
            "Adequate powered expansion is feasible and a label-blind successor packet "
            "would be required; this receipt alone is insufficient without freezing "
            "SOURCE_ITEM_SET / PUBLIC_ANNOTATION_PACKET successors."
        )
    else:
        terminal = "POWER_LIMITED_RETAIN_V2_1"
        rationale = (
            "Independent zero-label window remains open, but n=16 stays underpowered "
            "for the registered paired-Brier MDE and no label-blind expansion packet "
            "is frozen in-repo. Retain v2.1 as CONFIRMATORY_PACKET_POWER_LIMITED."
        )
    if terminal not in _TERMINAL_STATES:
        raise AssertionError(f"unknown terminal state: {terminal}")
    return {
        "terminal_status": terminal,
        "rationale": rationale,
        "power_path": power_evaluation.get("path"),
        "power_decision": power_evaluation.get("decision"),
        "minimum_n_for_adequacy_all_sigmas": power_evaluation.get(
            "minimum_n_for_adequacy_all_sigmas"
        ),
        "expansion_feasible_within_ceiling": power_evaluation.get(
            "expansion_feasible_within_ceiling"
        ),
        "demoted_ai_operator_label_count": issue_scan.get("demoted_ai_operator_label_count", 0),
        "independent_external_label_count": issue_scan.get(
            "independent_external_label_count", 0
        ),
    }


def build_successor_packet(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    zero_labels = build_zero_labels_at_power_design(repo_root, created_at_utc=created)
    # Re-stamp as the #326 repo-wide successor observation while preserving scan facts.
    zero_labels = {
        **zero_labels,
        "schema_version": "paper3-zero-labels-repo-wide-v1",
        "observation": "ZERO_LABELS_REPO_WIDE",
        "authority_source": {
            "repository": "SzeChunYiu/RAKL",
            "issue_number": 326,
            "blocked_annotation_issue": 217,
            "prior_power_issue": 248,
        },
        "claim_boundary": (
            "Repo-wide independent zero-label observation for the #326 successor window. "
            "Demoted AI_OPERATOR payloads are not independent external human labels and "
            "do not close this redesign window by themselves."
        ),
    }
    config = json.loads((repo_root / CONFIG_PATH).read_text(encoding="utf-8"))
    results = json.loads((repo_root / RESULTS_PATH).read_text(encoding="utf-8"))
    power_evaluation = evaluate_power_decision(config, results)
    prior_decision = json.loads((repo_root / DECISION_PATH).read_text(encoding="utf-8"))
    prior_zero = json.loads((repo_root / ZERO_LABELS_PATH).read_text(encoding="utf-8"))
    decision = decide_successor_terminal(
        zero_labels=zero_labels, power_evaluation=power_evaluation
    )
    machine = build_machine_witness_protocol()
    anti = build_anti_circularity_protocol()
    semantic = build_semantic_control_manifest(repo_root)
    decision_receipt = {
        "schema_version": "paper3-successor-validation-decision-v1",
        "receipt_id": "paper3-successor-validation-326",
        "issue": 326,
        "created_at_utc": created,
        "git_subject_sha256": git_head_sha(repo_root),
        **decision,
        "retains_packet": {
            "version": "v2.1",
            "source_set": "research/paper3/annotation/SOURCE_ITEM_SET_V2_1_20260810.json",
            "public_packet": (
                "research/paper3/annotation/EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json"
            ),
            "prior_power_decision": prior_decision.get("decision"),
            "prior_power_path": prior_decision.get("decision_path"),
        },
        "handoff": {
            "issue_217": (
                "Continue independent human annotation on exact v2.1 packet hashes; "
                "AI_OPERATOR demoted path remains NON_INDEPENDENT."
            ),
            "issue_249": (
                "Consume v2.1 power-limited confirmatory design; do not treat demoted "
                "AI_OPERATOR gate receipts as confirmatory independent evidence."
            ),
        },
        "frozen_artifact_sha256": {
            "zero_labels_repo_wide": canonical_sha256(zero_labels),
            "machine_witness_protocol": canonical_sha256(machine),
            "anti_circularity_protocol": canonical_sha256(anti),
            "semantic_control_manifest": canonical_sha256(semantic),
            "prior_power_decision": canonical_sha256(prior_decision),
            "prior_zero_labels_at_power_design": canonical_sha256(prior_zero),
            "power_results": canonical_sha256(results),
        },
        "claim_boundary": (
            "Successor-window terminal decision only. No confirmatory gate pass, no "
            "independent-review claim, no training authorization."
        ),
        "grants_scientific_authority": False,
    }
    packet_freeze = {
        "schema_version": "paper3-successor-packet-freeze-v1",
        "issue": 326,
        "created_at_utc": created,
        "terminal_status": decision["terminal_status"],
        "successor_source_set_created": False,
        "successor_public_packet_created": False,
        "retained_confirmatory_packet_version": "v2.1",
        "machine_witness_outputs_frozen": False,
        "semantic_control_scores_frozen": False,
        "reason": decision["rationale"],
        "grants_scientific_authority": False,
    }
    terminal = {
        "schema_version": "rakl-issue-terminal-receipt-v1",
        "issue": 326,
        "terminal_status": decision["terminal_status"],
        "scientific_verdict": decision["terminal_status"],
        "claim_boundary": (
            "Terminal pre-label redesign receipt. Retains v2.1 as power-limited unless a "
            "separately frozen powered successor exists. Demoted AI_OPERATOR labels are "
            "not independent human evidence."
        ),
        "acceptance_assessment": {
            "repo_wide_zero_independent_labels": zero_labels.get("state")
            == "ZERO_LABELS_OBSERVED"
            and not issue_scan_first_real(zero_labels),
            "power_design_reaffirmed": True,
            "machine_witness_protocol_frozen": True,
            "anti_circularity_protocol_frozen": True,
            "semantic_control_manifest_frozen": True,
            "powered_successor_packet_frozen": False,
            "independent_human_labels_present": issue_scan_first_real(zero_labels),
        },
        "evidence_pointers": {
            "zero_labels_repo_wide": str(ZERO_LABELS_REPO_WIDE_PATH),
            "decision_receipt": str(DECISION_RECEIPT_PATH),
            "packet_freeze_receipt": str(PACKET_FREEZE_RECEIPT_PATH),
            "machine_witness_protocol": str(MACHINE_WITNESS_PROTOCOL_PATH),
            "anti_circularity_protocol": str(ANTI_CIRCULARITY_PROTOCOL_PATH),
            "semantic_control_manifest": str(SEMANTIC_CONTROL_MANIFEST_PATH),
            "prior_power_decision": str(DECISION_PATH),
        },
        "grants_scientific_authority": False,
        "promotional_lift_claim_allowed": False,
        "evaluated_results_accessed": False,
        "created_at_utc": created,
    }
    return {
        "zero_labels": zero_labels,
        "machine_witness_protocol": machine,
        "anti_circularity_protocol": anti,
        "semantic_control_manifest": semantic,
        "decision_receipt": decision_receipt,
        "packet_freeze_receipt": packet_freeze,
        "terminal_receipt": terminal,
    }


def issue_scan_first_real(zero_labels: dict[str, Any]) -> bool:
    scan = zero_labels.get("issue_217_scan") or {}
    return bool(scan.get("first_real_independent_label_present"))


def write_successor_packet(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    packet = build_successor_packet(repo_root, created_at_utc=created_at_utc)
    out_dir = repo_root / SUCCESSOR_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        ZERO_LABELS_REPO_WIDE_PATH: packet["zero_labels"],
        MACHINE_WITNESS_PROTOCOL_PATH: packet["machine_witness_protocol"],
        ANTI_CIRCULARITY_PROTOCOL_PATH: packet["anti_circularity_protocol"],
        SEMANTIC_CONTROL_MANIFEST_PATH: packet["semantic_control_manifest"],
        DECISION_RECEIPT_PATH: packet["decision_receipt"],
        PACKET_FREEZE_RECEIPT_PATH: packet["packet_freeze_receipt"],
        TERMINAL_RECEIPT_PATH: packet["terminal_receipt"],
    }
    for rel, payload in mapping.items():
        path = repo_root / rel
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Paper III successor validation v1 (#326)",
                "",
                f"**Terminal:** `{packet['terminal_receipt']['terminal_status']}`",
                "",
                "Pre-label redesign window closeout. Independent external human labels remain",
                "absent; demoted AI_OPERATOR payloads are inventoried and non-authoritative.",
                "No powered expansion packet is frozen; confirmatory design retains v2.1 as",
                "`CONFIRMATORY_PACKET_POWER_LIMITED`.",
                "",
                "Reproduce:",
                "",
                "```bash",
                "PYTHONPATH=src python scripts/paper3_successor_validation_finalize.py",
                "pytest tests/test_paper3_successor_validation.py -q",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return packet
