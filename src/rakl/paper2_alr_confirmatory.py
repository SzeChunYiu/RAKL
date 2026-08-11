"""Paper II confirmatory model-level ALR packet (#324).

Freezes the confirmatory protocol and fail-closed execution gate. Non-confirmatory
#154 baselines remain negative/instrument history. Confirmatory claims stay blocked
while the #247 capability floor stands and typed RAKL/A3 arms are unexecuted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .authority_leakage_panel_v2 import PANEL_V2_ID, frozen_case_panel_v2
from .paper3_annotation import canonical_sha256
from .paper3_power_design import git_head_sha

CONFIRMATORY_DIR = Path("research/paper2_alr_confirmatory_v1")
PROTOCOL_PATH = CONFIRMATORY_DIR / "CONFIRMATORY_PROTOCOL.json"
PANEL_MANIFEST_PATH = CONFIRMATORY_DIR / "PANEL_MANIFEST.json"
ARM_TABLE_PATH = CONFIRMATORY_DIR / "ARM_INTERVENTION_TABLE.json"
PROMPT_PARITY_PATH = CONFIRMATORY_DIR / "PROMPT_PARITY_RECEIPT.json"
DEGENERACY_BIND_PATH = CONFIRMATORY_DIR / "DEGENERACY_AUDIT_BINDING.json"
MODEL_CONFIG_PATH = CONFIRMATORY_DIR / "MODEL_CONFIG.json"
INFERENCE_PLAN_PATH = CONFIRMATORY_DIR / "INFERENCE_PLAN.json"
TERMINAL_RECEIPT_PATH = CONFIRMATORY_DIR / "ISSUE_324_TERMINAL_RECEIPT.json"

ORACLE_DECISION_PATH = Path(
    "research/paper2_experience_benchmark_v1_3/ORACLE_DECISION_RECEIPT_V1_3.json"
)
DEGENERACY_AUDIT_PATH = Path("research/AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json")
BASELINE_PREREG_PATH = Path(
    "research/paper2_alr_model_baselines_v1/BASELINE_PREREGISTRATION.json"
)
A3_A4_STATUS_PATH = Path(
    "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_STATUS.json"
)


def _load_json(repo_root: Path, rel: Path) -> dict[str, Any]:
    path = repo_root / rel
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_panel_manifest(repo_root: Path) -> dict[str, Any]:
    cases = frozen_case_panel_v2()
    audit = _load_json(repo_root, DEGENERACY_AUDIT_PATH)
    v2 = (audit.get("panels") or {}).get(PANEL_V2_ID) or {}
    return {
        "schema_version": "paper2-alr-confirmatory-panel-manifest-v1",
        "panel_id": PANEL_V2_ID,
        "n_cases": len(cases),
        "case_ids": [
            getattr(case, "case_id", None) or case.visible.case_id for case in cases
        ],
        "panel_source": "src/rakl/authority_leakage_panel_v2.py",
        "degeneracy_status": v2.get("status"),
        "degeneracy_audit_path": str(DEGENERACY_AUDIT_PATH),
        "v1_retained_as_negative_history": True,
        "claim_boundary": (
            "Panel identity freeze only. No confirmatory ALR score is reported here."
        ),
        "grants_scientific_authority": False,
    }


def build_arm_intervention_table() -> dict[str, Any]:
    return {
        "schema_version": "paper2-alr-confirmatory-arm-table-v1",
        "arms": [
            {
                "arm_id": "A_BASE_DIRECT_STRONG_PROMPT",
                "role": "CONTROL",
                "description": (
                    "Same base model and visible scientific case; strong explicit "
                    "reasoning/output instructions; no RAKL typed authority gate."
                ),
                "status": "NON_CONFIRMATORY_BASELINE_EXECUTED_ON_154",
                "evidence": "research/paper2_alr_model_baselines_v1/",
            },
            {
                "arm_id": "B_A3_TRANSACTIONAL_GOVERNANCE_FUNCTION_MATCHED",
                "role": "PARENT_CONTROL",
                "description": (
                    "Provenance/transaction discipline without RAKL scientific "
                    "claim-type authority coordinates, if fair/executable."
                ),
                "status": "CANNOT_IDENTIFY_OR_NON_CONFIRMATORY_ONLY",
                "evidence": "research/paper2_closest_parent/",
            },
            {
                "arm_id": "C_RAKL_TYPED_AUTHORITY",
                "role": "TREATMENT",
                "description": (
                    "Integrated RAKL scientific authority policy / A4-equivalent on "
                    "the registered transition layer."
                ),
                "status": "UNEXECUTED_CONFIRMATORY",
                "evidence": None,
            },
        ],
        "primary_contrasts": ["C_minus_A", "C_minus_B"],
        "treatment_wording_forbidden": [
            "RAKL arm",
            "ungated arm",
            "safe arm",
        ],
        "grants_scientific_authority": False,
    }


def build_prompt_parity_receipt() -> dict[str, Any]:
    return {
        "schema_version": "paper2-alr-prompt-parity-receipt-v1",
        "status": "PARITY_RULES_FROZEN",
        "rules": [
            "Identical prompt/output instructions where the intervention allows.",
            "Authority-policy difference lives in the registered system transition layer.",
            "No semantic treatment labels in model-visible prompts.",
        ],
        "grants_scientific_authority": False,
    }


def build_degeneracy_binding(repo_root: Path) -> dict[str, Any]:
    audit = _load_json(repo_root, DEGENERACY_AUDIT_PATH)
    v2 = (audit.get("panels") or {}).get(PANEL_V2_ID) or {}
    status = v2.get("status")
    return {
        "schema_version": "paper2-alr-degeneracy-binding-v1",
        "panel_id": PANEL_V2_ID,
        "audit_path": str(DEGENERACY_AUDIT_PATH),
        "v2_status": status,
        "required_status": "CLEAN",
        "clean": status == "CLEAN",
        "grants_scientific_authority": False,
    }


def build_model_config(repo_root: Path) -> dict[str, Any]:
    oracle = _load_json(repo_root, ORACLE_DECISION_PATH)
    baseline = _load_json(repo_root, BASELINE_PREREG_PATH)
    return {
        "schema_version": "paper2-alr-confirmatory-model-config-v1",
        "selection_rule": (
            "Model identity must be chosen by a predeclared capability/format gate, "
            "not by whether RAKL looks good after outcomes."
        ),
        "capability_gate": {
            "issue": 247,
            "oracle_path": str(ORACLE_DECISION_PATH),
            "scientific_verdict": oracle.get("scientific_verdict"),
            "oracle_gate_passed": oracle.get("oracle_gate_passed"),
            "experience_benchmark_1_5B_authorized": oracle.get(
                "experience_benchmark_1_5B_authorized"
            ),
        },
        "non_confirmatory_baseline_prereg": str(BASELINE_PREREG_PATH),
        "baseline_packet_id": baseline.get("packet_id"),
        "confirmatory_model_authorized": False,
        "grants_scientific_authority": False,
    }


def build_inference_plan() -> dict[str, Any]:
    return {
        "schema_version": "paper2-alr-confirmatory-inference-plan-v1",
        "independent_unit": "ScientificTransitionCase twin/panel structure on V2",
        "co_primary_outcomes": [
            "authority_leakage_rate",
            "valid_upgrade_recall",
        ],
        "also_report": [
            "valid_refutation_recall",
            "false_conservative_refusal_rate",
            "BLOCKED_CANNOT_CHECK precision_recall",
            "leakage_subtypes",
            "resource_metrics",
        ],
        "power_note": (
            "n=16 V2 panel is adequate for gross refuse-everything vs escalate-everything "
            "discrimination; fine subtype comparisons remain UNDERPOWERED unless a "
            "pre-outcome expanded successor panel is frozen."
        ),
        "permitted_terminal_states": [
            "SAFETY_BENEFIT_WITH_PRESERVED_UPDATE_RECALL",
            "SAFETY_BENEFIT_BUT_OVERCONSERVATIVE",
            "NO_DISTINGUISHABLE_AUTHORITY_BENEFIT",
            "TRANSACTIONAL_PARENT_MATCHES_TYPED_AUTHORITY",
            "TYPED_AUTHORITY_HARMS_LEGITIMATE_UPDATES",
            "UNDERPOWERED",
            "CANNOT_IDENTIFY_A3_CONTROL",
            "INVALID_CONTAMINATED",
            "CANNOT_EXECUTE_CONFIRMATORY_MODEL_COMPARISON",
        ],
        "grants_scientific_authority": False,
    }


def build_confirmatory_protocol(repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": "paper2-alr-confirmatory-protocol-v1",
        "protocol_id": "paper2-alr-confirmatory-v1",
        "issue": 324,
        "status": "PROTOCOL_FROZEN_EXECUTION_BLOCKED",
        "scientific_question": (
            "Does typed scientific-authority governance reduce unsupported scientific-state "
            "escalation under matched model/context/resources while preserving legitimate "
            "authority upgrades and refutations?"
        ),
        "panel_id": PANEL_V2_ID,
        "depends_on": {
            "authority_ledger_issue": 242,
            "benchmark_issue": 154,
            "capability_gate_issue": 247,
            "a3_a4_issue": 156,
        },
        "non_confirmatory_history": {
            "alr_baselines": "research/paper2_alr_model_baselines_v1/",
            "note": (
                "Jobs 3476736/3476737 and related receipts remain non-confirmatory "
                "instrument/history only."
            ),
        },
        "post_outcome_changes_forbidden": [
            "labels",
            "scoring",
            "case_wording",
            "prompt_visible_fields",
            "thresholds",
            "primary_estimands",
        ],
        "claim_boundary": (
            "Protocol freeze only. Does not mint an empirical Paper-II authority result."
        ),
        "grants_scientific_authority": False,
        "git_subject_sha256": git_head_sha(repo_root),
    }


def assess_confirmatory_readiness(repo_root: Path) -> dict[str, Any]:
    degeneracy = build_degeneracy_binding(repo_root)
    model = build_model_config(repo_root)
    a3a4 = _load_json(repo_root, A3_A4_STATUS_PATH)
    panel = build_panel_manifest(repo_root)
    blockers: list[str] = []
    if not degeneracy.get("clean"):
        blockers.append("V2_DEGENERACY_NOT_CLEAN")
    if model["capability_gate"].get("oracle_gate_passed") is not True:
        blockers.append("CAPABILITY_FLOOR_BLOCKS_CONFIRMATORY_MODEL")
    if model.get("confirmatory_model_authorized") is not True:
        blockers.append("NO_CONFIRMATORY_MODEL_AUTHORIZE_RECEIPT")
    a3_status = str(a3a4.get("status") or a3a4.get("empirical_status") or "")
    if "EMPIRICS" in a3_status.upper() and "COMPLETE" not in a3_status.upper():
        blockers.append("A3_PARENT_CONTROL_NOT_CONFIRMATORY_COMPLETE")
    blockers.append("RAKL_TYPED_AUTHORITY_ARM_UNEXECUTED")
    ready = not blockers
    terminal = (
        "CONFIRMATORY_RESULT_READY"
        if ready
        else "CANNOT_EXECUTE_CONFIRMATORY_MODEL_COMPARISON"
    )
    return {
        "ready": ready,
        "terminal_status": terminal,
        "blockers": blockers,
        "panel_n": panel.get("n_cases"),
        "degeneracy_clean": degeneracy.get("clean"),
        "capability_verdict": model["capability_gate"].get("scientific_verdict"),
        "a3_a4_status": a3_status or None,
    }


def refuse_confirmatory_claim(repo_root: Path) -> None:
    """Fail closed if a caller attempts to treat this packet as confirmatory evidence."""
    readiness = assess_confirmatory_readiness(repo_root)
    if readiness["ready"]:
        return
    raise PermissionError(
        "confirmatory ALR claim refused: " + ", ".join(readiness["blockers"])
    )


def build_confirmatory_packet(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    created = created_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    protocol = build_confirmatory_protocol(repo_root)
    panel = build_panel_manifest(repo_root)
    arms = build_arm_intervention_table()
    parity = build_prompt_parity_receipt()
    degeneracy = build_degeneracy_binding(repo_root)
    model = build_model_config(repo_root)
    inference = build_inference_plan()
    readiness = assess_confirmatory_readiness(repo_root)
    terminal = {
        "schema_version": "rakl-issue-terminal-receipt-v1",
        "issue": 324,
        "terminal_status": readiness["terminal_status"],
        "scientific_verdict": readiness["terminal_status"],
        "claim_boundary": (
            "Terminal confirmatory-ALR ownership receipt. Protocol/panel/arms/parity/"
            "inference plan are frozen. No empirical Paper-II authority-leakage "
            "superiority claim is authorized while capability-floor and unexecuted "
            "typed-authority arm blockers remain."
        ),
        "acceptance_assessment": {
            "canonical_v2_panel_frozen": panel.get("panel_id") == PANEL_V2_ID,
            "degeneracy_clean": bool(degeneracy.get("clean")),
            "co_primary_metrics_registered": True,
            "prompt_parity_rules_frozen": True,
            "strong_direct_baseline_history_present": True,
            "a3_control_confirmatory_complete": False,
            "rakl_typed_authority_arm_executed": False,
            "confirmatory_model_authorized": False,
            "alr_and_valid_upgrade_recall_reported_confirmatory": False,
        },
        "blockers": readiness["blockers"],
        "evidence_pointers": {
            "protocol": str(PROTOCOL_PATH),
            "panel_manifest": str(PANEL_MANIFEST_PATH),
            "arm_table": str(ARM_TABLE_PATH),
            "prompt_parity": str(PROMPT_PARITY_PATH),
            "degeneracy_binding": str(DEGENERACY_BIND_PATH),
            "model_config": str(MODEL_CONFIG_PATH),
            "inference_plan": str(INFERENCE_PLAN_PATH),
            "oracle_capability_gate": str(ORACLE_DECISION_PATH),
            "non_confirmatory_baselines": "research/paper2_alr_model_baselines_v1/",
        },
        "artifact_sha256": {
            "protocol": canonical_sha256(protocol),
            "panel_manifest": canonical_sha256(panel),
            "arm_table": canonical_sha256(arms),
            "prompt_parity": canonical_sha256(parity),
            "degeneracy_binding": canonical_sha256(degeneracy),
            "model_config": canonical_sha256(model),
            "inference_plan": canonical_sha256(inference),
        },
        "grants_scientific_authority": False,
        "promotional_lift_claim_allowed": False,
        "evaluated_results_accessed": False,
        "created_at_utc": created,
    }
    return {
        "protocol": protocol,
        "panel_manifest": panel,
        "arm_table": arms,
        "prompt_parity": parity,
        "degeneracy_binding": degeneracy,
        "model_config": model,
        "inference_plan": inference,
        "terminal_receipt": terminal,
        "readiness": readiness,
    }


def write_confirmatory_packet(
    repo_root: Path,
    *,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    packet = build_confirmatory_packet(repo_root, created_at_utc=created_at_utc)
    out_dir = repo_root / CONFIRMATORY_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        PROTOCOL_PATH: packet["protocol"],
        PANEL_MANIFEST_PATH: packet["panel_manifest"],
        ARM_TABLE_PATH: packet["arm_table"],
        PROMPT_PARITY_PATH: packet["prompt_parity"],
        DEGENERACY_BIND_PATH: packet["degeneracy_binding"],
        MODEL_CONFIG_PATH: packet["model_config"],
        INFERENCE_PLAN_PATH: packet["inference_plan"],
        TERMINAL_RECEIPT_PATH: packet["terminal_receipt"],
    }
    for rel, payload in mapping.items():
        (repo_root / rel).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# Paper II confirmatory ALR v1 (#324)",
                "",
                f"**Terminal:** `{packet['terminal_receipt']['terminal_status']}`",
                "",
                "Freezes confirmatory protocol, V2 panel binding, arms, prompt-parity rules,",
                "and co-primary ALR + valid-upgrade-recall inference plan. Execution remains",
                "fail-closed under the #247 capability floor and unexecuted typed-authority arm.",
                "",
                "Non-confirmatory #154 baselines are retained as instrument history only.",
                "",
                "Reproduce:",
                "",
                "```bash",
                "PYTHONPATH=src python scripts/paper2_alr_confirmatory_finalize.py",
                "pytest tests/test_paper2_alr_confirmatory.py -q",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return packet
