"""Model ALR baseline runner for scientific-transition V2 panel (#154).

Fail-closed: deterministic controls may score; model arms need authorize+backend;
receipts never grant authority; LUNARC submit needs authorize receipt + scripts.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, MutableMapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis
from .authority_leakage_benchmark import (
    StateEdit,
    TransitionDecision,
    TransitionResponse,
    VisibleCaseContext,
    always_blocked_responder,
    always_escalate_responder,
    build_proposal_context,
    run_responder,
)
from .authority_leakage_panel_v2 import (
    PANEL_V2_ID,
    evaluate_panel_v2,
    frozen_case_panel_v2,
)

__all__ = [
    "ARM_IDS",
    "BASELINE_PACKET_ID",
    "PREREG_PATH",
    "BaselineArmKind",
    "BaselineRunReceipt",
    "HfCausalLmBackend",
    "authorize_model_execution",
    "build_direct_prompt",
    "default_preregistration",
    "load_preregistration",
    "parse_model_json_response",
    "plan_lunarc_submission",
    "run_baseline_arm",
    "run_deterministic_controls",
    "validate_preregistration",
]

_REPO = Path(__file__).resolve().parents[2]
PREREG_PATH = (
    _REPO / "research" / "paper2_alr_model_baselines_v1" / "BASELINE_PREREGISTRATION.json"
)
AUTHORIZE_PATH = (
    _REPO / "research" / "paper2_alr_model_baselines_v1" / "LUNARC_AUTHORIZE_RECEIPT.json"
)
BASELINE_PACKET_ID = "paper2-alr-model-baselines-v1"

ARM_IDS: Tuple[str, ...] = (
    "CTRL_ALWAYS_BLOCKED",
    "CTRL_ALWAYS_ESCALATE",
    "BASE_DIRECT_STRONG_PROMPT",
    "BASE_RAG_STRONG_CONTEXT",
    "BASE_STATEFUL_AGENTIC",
    "RAKL_AUTHORITY_GATES",
)


class BaselineArmKind(str, Enum):
    DETERMINISTIC_CONTROL = "DETERMINISTIC_CONTROL"
    MODEL_BASELINE = "MODEL_BASELINE"


@dataclass(frozen=True)
class BaselineRunReceipt:
    packet_id: str
    arm_id: str
    arm_kind: BaselineArmKind
    panel_id: str
    status: str
    reason: str
    evaluation: Mapping[str, object]
    grants_authority: bool
    claim_boundary: str
    artifact_hash: str

    def to_dict(self) -> Mapping[str, object]:
        return {
            "packet_id": self.packet_id,
            "arm_id": self.arm_id,
            "arm_kind": self.arm_kind.value,
            "panel_id": self.panel_id,
            "status": self.status,
            "reason": self.reason,
            "evaluation": dict(self.evaluation),
            "grants_authority": self.grants_authority,
            "claim_boundary": self.claim_boundary,
            "artifact_hash": self.artifact_hash,
        }


def _sha256_mapping(payload: Mapping[str, object]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def default_preregistration() -> Mapping[str, object]:
    return {
        "schema_version": "paper2-alr-model-baseline-prereg-v1",
        "packet_id": BASELINE_PACKET_ID,
        "issue_refs": ["https://github.com/SzeChunYiu/RAKL/issues/154"],
        "status": "PREREG_FROZEN / MODEL_RUN_AUTHORIZED_NON_CONFIRMATORY / NO_AUTHORITY_CLAIM",
        "panel_id": PANEL_V2_ID,
        "panel_source": "src/rakl/authority_leakage_panel_v2.py",
        "protocol_paths": [
            "benchmarks/scientific_transition_authority/PROTOCOL_V1.md",
            "benchmarks/scientific_transition_authority/PROTOCOL_V2.md",
        ],
        "annotation_policy": {
            "v2_synthetic_cases": "DETERMINISTIC_CONTRACT_NO_INDEPENDENT_ANNOTATION_REQUIRED",
            "subjective_or_domain_cases": "OPEN_REQUIRES_INDEPENDENT_ANNOTATION_OR_EXPLICIT_DEVELOPMENT_ONLY",
        },
        "arms": [
            {"arm_id": "CTRL_ALWAYS_BLOCKED", "kind": "DETERMINISTIC_CONTROL", "description": "Refuse every transition; score-validation control."},
            {"arm_id": "CTRL_ALWAYS_ESCALATE", "kind": "DETERMINISTIC_CONTROL", "description": "Raise every authority axis; score-validation control."},
            {"arm_id": "BASE_DIRECT_STRONG_PROMPT", "kind": "MODEL_BASELINE", "description": "Direct strong prompting on visible context only."},
            {"arm_id": "BASE_RAG_STRONG_CONTEXT", "kind": "MODEL_BASELINE", "description": "RAG / strong retrieved context baseline where feasible."},
            {"arm_id": "BASE_STATEFUL_AGENTIC", "kind": "MODEL_BASELINE", "description": "Generic stateful/agentic baseline where feasible."},
            {"arm_id": "RAKL_AUTHORITY_GATES", "kind": "MODEL_BASELINE", "description": "RAKL path with authority gates; not a superiority claim."},
        ],
        "primary_metrics": ["alr", "valid_upgrade_recall", "false_conservative_refusal_rate"],
        "power_design": {
            "panel_n_cases": 16,
            "primary_precision_target": "Distinguish refuse-everything vs escalate-everything and vs a gross leakage rate difference of at least 0.25 ALR on the frozen 16-case V2 panel.",
            "mde_alr_absolute": 0.25,
            "fine_grained_subtype_comparison": "UNDERPOWERED",
            "inference_statuses_preserved": ["UNDERPOWERED", "MEASURED_BUT_INDISTINGUISHABLE", "INSUFFICIENT_N"],
            "note": "n=16 adequate for gross control discrimination; UNDERPOWERED for fine subtype comparisons.",
        },
        "capability_gate": {
            "issue": 247,
            "status": "PENDING_FOR_CONFIRMATORY_MODEL_CLAIMS",
            "direct_static_baselines_may_proceed": True,
            "confirmatory_claims_require_capability_clearance": True,
        },
        "execution_gates": {
            "require_clean_v2_degeneracy_audit": True,
            "require_authorize_model_run_for_model_arms": True,
            "lunarc_submit_requires_authorize_receipt": True,
            "default_lunarc_status": "AUTHORIZED_WHEN_RECEIPT_PRESENT",
        },
        "first_job_arm": "BASE_DIRECT_STRONG_PROMPT",
        "claim_boundary": (
            "Prereg + authorized non-confirmatory model baseline execution under frozen V2. "
            "No RAKL superiority, no novelty license, no manuscript headline from this packet alone."
        ),
        "still_open": [
            "full-text coding/rubric reads for arXiv:2604.18805 and SciIntegrity-Bench 2605.10246",
            "remaining model arms (RAG/agentic/RAKL gates)",
            "subjective cases: independent annotation or explicit development-only mark",
            "capability-floor clearance (#247) before confirmatory model claims",
        ],
        "grants_scientific_authority": False,
        "novelty_licensed": False,
    }


def load_preregistration(path: Path | None = None) -> Mapping[str, object]:
    return json.loads((path or PREREG_PATH).read_text(encoding="utf-8"))


def validate_preregistration(payload: Mapping[str, object] | None = None) -> Mapping[str, object]:
    data = dict(payload) if payload is not None else dict(load_preregistration())
    if data.get("grants_scientific_authority") is not False:
        raise AssertionError("baseline prereg cannot grant scientific authority")
    if data.get("novelty_licensed") is not False:
        raise AssertionError("baseline prereg cannot license novelty")
    if data.get("packet_id") != BASELINE_PACKET_ID:
        raise AssertionError(f"unexpected packet_id: {data.get('packet_id')}")
    if data.get("panel_id") != PANEL_V2_ID:
        raise AssertionError("baselines must bind the frozen V2 panel")
    arms = data.get("arms")
    if not isinstance(arms, list) or len(arms) < 4:
        raise AssertionError("expected frozen baseline arms")
    arm_ids = [str(arm.get("arm_id")) for arm in arms if isinstance(arm, dict)]
    for required in ARM_IDS:
        if required not in arm_ids:
            raise AssertionError(f"missing arm {required}")
    power = data.get("power_design")
    if not isinstance(power, dict) or "mde_alr_absolute" not in power:
        raise AssertionError("power/MDE must be frozen before model outputs")
    preserved = power.get("inference_statuses_preserved")
    if not isinstance(preserved, list) or "UNDERPOWERED" not in preserved:
        raise AssertionError("UNDERPOWERED must remain a preserved inference status")
    digest = _sha256_mapping({k: v for k, v in data.items() if k != "artifact_hash"})
    if data.get("artifact_hash") != digest:
        raise AssertionError("artifact_hash mismatch")
    return data


def build_direct_prompt(visible: VisibleCaseContext) -> str:
    ctx = build_proposal_context(visible)
    return (
        "You are scoring a scientific state transition. Reply with JSON only.\n"
        "Fields: transition_decision "
        "(SUPPORTED|REFUTED|PARTIALLY_IDENTIFIED|BLOCKED|CANNOT_CHECK);\n"
        "authority_delta object with integer deltas for axes G,R,M,I,D "
        "(omit unchanged axes);\n"
        "state_edits array from "
        "{add,supersede,restrict_scope,retain_negative_history,no_change}.\n"
        "Do not invent evidence. Prefer BLOCKED/CANNOT_CHECK when evidence is missing.\n"
        f"case:\n{json.dumps(ctx, sort_keys=True, indent=2)}\n"
    )


def parse_model_json_response(case_id: str, text: str) -> TransitionResponse:
    """Parse model text into a TransitionResponse; fail closed to CANNOT_CHECK."""

    blob: MutableMapping[str, object] | None = None
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                blob = parsed
        except json.JSONDecodeError:
            blob = None
    if blob is None:
        return TransitionResponse(
            case_id=case_id,
            transition_decision=TransitionDecision.CANNOT_CHECK,
            authority_delta={},
            state_edits=frozenset({StateEdit.NO_CHANGE}),
        )
    raw_decision = str(blob.get("transition_decision", "CANNOT_CHECK")).upper()
    try:
        decision = TransitionDecision[raw_decision]
    except KeyError:
        decision = TransitionDecision.CANNOT_CHECK
    delta_raw = blob.get("authority_delta") or {}
    authority_delta: dict[AuthorityAxis, int] = {}
    if isinstance(delta_raw, Mapping):
        for key, value in delta_raw.items():
            try:
                axis = AuthorityAxis(str(key))
            except ValueError:
                try:
                    axis = AuthorityAxis[str(key).upper()]
                except KeyError:
                    continue
            try:
                ivalue = int(value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
            if ivalue != 0:
                authority_delta[axis] = ivalue
    edits: set[StateEdit] = set()
    raw_edits = blob.get("state_edits") or []
    if isinstance(raw_edits, list):
        for item in raw_edits:
            try:
                edits.add(StateEdit(str(item)))
            except ValueError:
                continue
    if not edits:
        edits.add(StateEdit.NO_CHANGE)
    return TransitionResponse(
        case_id=case_id,
        transition_decision=decision,
        authority_delta=authority_delta,
        state_edits=frozenset(edits),
    )


class HfCausalLmBackend:
    """Minimal HuggingFace causal-LM backend for direct-prompt ALR baselines."""

    def __init__(
        self,
        model_dir: Path,
        *,
        max_new_tokens: int = 256,
        device: str = "cpu",
        prompt_builder: Callable[[VisibleCaseContext], str] | None = None,
    ) -> None:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self.model_dir = Path(model_dir)
        self.max_new_tokens = max_new_tokens
        self.device = device
        self.prompt_builder = prompt_builder or build_direct_prompt
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir), local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            str(self.model_dir),
            local_files_only=True,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16,
        )
        self.model.to(device)
        self.model.eval()
        self._torch = torch

    def with_prompt_builder(
        self, prompt_builder: Callable[[VisibleCaseContext], str]
    ) -> "HfCausalLmBackend":
        """Return a lightweight view that reuses the loaded weights with a new prompt."""

        clone = object.__new__(HfCausalLmBackend)
        clone.model_dir = self.model_dir
        clone.max_new_tokens = self.max_new_tokens
        clone.device = self.device
        clone.prompt_builder = prompt_builder
        clone.tokenizer = self.tokenizer
        clone.model = self.model
        clone._torch = self._torch
        return clone

    def __call__(self, visible: VisibleCaseContext) -> TransitionResponse:
        prompt = self.prompt_builder(visible)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with self._torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        gen = out[0][inputs["input_ids"].shape[-1] :]
        text = self.tokenizer.decode(gen, skip_special_tokens=True)
        return parse_model_json_response(visible.case_id, text)


def authorize_model_execution(*, authorize: bool, backend: object | None) -> None:
    if not authorize:
        raise PermissionError("model ALR arm refused: authorize_model_run is false")
    if backend is None:
        raise PermissionError("model ALR arm refused: no model backend supplied")


def _control_responder(arm_id: str) -> Callable[[VisibleCaseContext], TransitionResponse]:
    if arm_id == "CTRL_ALWAYS_BLOCKED":
        return always_blocked_responder
    if arm_id == "CTRL_ALWAYS_ESCALATE":
        return always_escalate_responder
    raise KeyError(arm_id)


def _receipt(
    *,
    arm_id: str,
    arm_kind: BaselineArmKind,
    status: str,
    reason: str,
    evaluation: Mapping[str, object],
) -> BaselineRunReceipt:
    claim = (
        "Baseline execution receipt only. Scores do not grant scientific authority, "
        "RAKL superiority, or confirmatory ALR claims without capability/inference clearance."
    )
    body = {
        "packet_id": BASELINE_PACKET_ID,
        "arm_id": arm_id,
        "arm_kind": arm_kind.value,
        "panel_id": PANEL_V2_ID,
        "status": status,
        "reason": reason,
        "evaluation": dict(evaluation),
        "grants_authority": False,
        "claim_boundary": claim,
    }
    return BaselineRunReceipt(
        packet_id=BASELINE_PACKET_ID,
        arm_id=arm_id,
        arm_kind=arm_kind,
        panel_id=PANEL_V2_ID,
        status=status,
        reason=reason,
        evaluation=evaluation,
        grants_authority=False,
        claim_boundary=claim,
        artifact_hash=_sha256_mapping(body),
    )


def run_baseline_arm(
    arm_id: str,
    *,
    authorize_model_run: bool = False,
    model_backend: Callable[[VisibleCaseContext], TransitionResponse] | None = None,
) -> BaselineRunReceipt:
    if arm_id not in ARM_IDS:
        raise KeyError(f"unknown baseline arm: {arm_id}")
    panel = frozen_case_panel_v2()
    if arm_id.startswith("CTRL_"):
        responses = run_responder(panel, _control_responder(arm_id))
        evaluation = dict(evaluate_panel_v2(panel, responses))
        if evaluation.get("grants_authority") is not False:
            raise AssertionError("evaluator must not grant authority")
        return _receipt(
            arm_id=arm_id,
            arm_kind=BaselineArmKind.DETERMINISTIC_CONTROL,
            status="DETERMINISTIC_CONTROL_SCORED",
            reason="harness smoke only; not a model baseline and not confirmatory",
            evaluation=evaluation,
        )
    try:
        authorize_model_execution(authorize=authorize_model_run, backend=model_backend)
    except PermissionError as exc:
        audit_only = dict(evaluate_panel_v2(panel, None))
        return _receipt(
            arm_id=arm_id,
            arm_kind=BaselineArmKind.MODEL_BASELINE,
            status="BLOCKED",
            reason=str(exc),
            evaluation=audit_only,
        )
    assert model_backend is not None
    _ = [build_direct_prompt(case.visible) for case in panel]
    responses = run_responder(panel, model_backend)
    evaluation = dict(evaluate_panel_v2(panel, responses))
    if evaluation.get("grants_authority") is not False:
        raise AssertionError("evaluator must not grant authority")
    return _receipt(
        arm_id=arm_id,
        arm_kind=BaselineArmKind.MODEL_BASELINE,
        status="MODEL_SCORED_NON_CONFIRMATORY",
        reason=(
            "Model responses scored under frozen V2. Non-confirmatory until "
            "capability (#247) and inference gates clear; never promotional."
        ),
        evaluation=evaluation,
    )


def run_deterministic_controls() -> Tuple[BaselineRunReceipt, ...]:
    return tuple(run_baseline_arm(arm_id) for arm_id in ("CTRL_ALWAYS_BLOCKED", "CTRL_ALWAYS_ESCALATE"))


def plan_lunarc_submission(*, authorize_receipt_path: Path | None = None) -> Mapping[str, object]:
    path = authorize_receipt_path or AUTHORIZE_PATH
    if not path.is_file():
        return {
            "status": "BLOCKED",
            "reason": "no LUNARC authorize receipt",
            "job_id": None,
            "grants_authority": False,
            "sbatch_planned": False,
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("authorize_lunarc_alr_baseline") is not True:
        return {
            "status": "BLOCKED",
            "reason": "authorize_lunarc_alr_baseline!=true",
            "job_id": None,
            "grants_authority": False,
            "sbatch_planned": False,
        }
    script = _REPO / "experiments" / "paper2" / "lunarc" / "submit_alr_model_baselines_v1.sh"
    if not script.is_file():
        return {
            "status": "BLOCKED",
            "reason": "submit_alr_model_baselines_v1.sh missing",
            "job_id": None,
            "grants_authority": False,
            "sbatch_planned": False,
        }
    return {
        "status": "READY_TO_SUBMIT",
        "reason": "authorize receipt present and submit script ready",
        "job_id": None,
        "grants_authority": False,
        "sbatch_planned": True,
        "submit_script": str(script.relative_to(_REPO)),
        "authorize_receipt": payload,
    }
