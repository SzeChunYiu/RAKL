"""Root-cause helpers for the adaptive Paper-II ExperienceBenchmark successor.

This module is intentionally separate from the frozen v1/v1.1/v1.2 runner.
It fixes one design error exposed by job 3476548: a failed development episode
must not automatically become a reusable Lesson.  Verified development feedback
may create a scoped procedural lesson only after the development output is frozen
and bound to an evaluator receipt.

All objects here are method/search state only.  They never grant scientific
authority over claims about nature.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping, Tuple


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EVIDENCE_ID_RE = re.compile(r"\bE\d+\b")
_TRANSFER_TASK_RE = re.compile(r"\bT\d+\b", re.IGNORECASE)


class RootCauseDiagnosticArm(str, Enum):
    RESET = "RESET"
    FAILURE_MEMORY_ONLY = "FAILURE_MEMORY_ONLY"
    VERIFIED_DEVELOPMENT_LESSONS = "VERIFIED_DEVELOPMENT_LESSONS"
    ORACLE_PROCEDURE_UPPER_BOUND = "ORACLE_PROCEDURE_UPPER_BOUND"
    FULL_RAKL_SELECTIVE = "FULL_RAKL_SELECTIVE"


#: Frozen arm execution order for the root-cause ladder.
#:
#: ORACLE_PROCEDURE_UPPER_BOUND runs first: if the base model cannot execute the
#: correct generic procedure when it is handed to it directly, a null in any later
#: arm cannot be attributed to RAKL rather than to the model, so those runs are
#: uninterpretable.  See research/PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md.
#:
#: This is a contract lock over execution order only.  It asserts no result and
#: grants no scientific authority.
CONDITION_LADDER: Tuple[RootCauseDiagnosticArm, ...] = (
    RootCauseDiagnosticArm.ORACLE_PROCEDURE_UPPER_BOUND,
    RootCauseDiagnosticArm.RESET,
    RootCauseDiagnosticArm.FAILURE_MEMORY_ONLY,
    RootCauseDiagnosticArm.VERIFIED_DEVELOPMENT_LESSONS,
    RootCauseDiagnosticArm.FULL_RAKL_SELECTIVE,
)

#: Frozen ORACLE gate: >= 2 of 3 fresh-transfer tasks registered as successes.
#: Frozen before execution so it cannot be re-tuned after seeing the result.
ORACLE_PASS_MIN_SUCCESS_RATE: float = 2.0 / 3.0


@dataclass(frozen=True)
class VerifiedDevelopmentFeedback:
    source_task_id: str
    source_output_hash: str
    evaluator_receipt_hash: str
    principle: str
    stratum: str
    output_frozen: bool
    evaluator_verified: bool

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SelectiveExperienceView:
    lesson_ids: Tuple[str, ...]
    failure_task_ids: Tuple[str, ...]
    rendered_state: Mapping[str, Any]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _lesson_id(feedback: VerifiedDevelopmentFeedback) -> str:
    payload = (
        feedback.source_task_id
        + "|"
        + feedback.source_output_hash
        + "|"
        + feedback.evaluator_receipt_hash
        + "|"
        + feedback.principle
        + "|"
        + feedback.stratum
    ).encode("utf-8")
    return "verified-dev-lesson-" + sha256(payload).hexdigest()[:16]


def append_failed_episode_without_lesson(
    state: Mapping[str, Any],
    *,
    task: Mapping[str, Any],
    predicted: Mapping[str, Any] | None,
    score: float,
    failure_signature: Tuple[str, ...],
    output_hash: str,
) -> dict[str, Any]:
    """Persist a failed episode and negative history, but mint no Lesson."""

    if not failure_signature:
        raise ValueError("failure_signature_required")
    if not _SHA256_RE.match(output_hash):
        raise ValueError("invalid_output_hash")

    next_state = copy.deepcopy(dict(state))
    next_state["state_kind"] = "LEARNING_EXTERNAL_RAKL_STATE"
    episode = {
        "task_id": str(task["task_id"]),
        "phase": str(task["phase"]),
        "stratum": str(task["stratum"]),
        "title": str(task["title"]),
        "success": False,
        "score": float(score),
        "failure_signature": list(failure_signature),
        "model_verdict": None if predicted is None else predicted.get("verdict"),
        "model_selected_evidence_ids": [] if predicted is None else list(predicted.get("selected_evidence_ids", [])),
        "model_rejected_evidence_ids": [] if predicted is None else list(predicted.get("rejected_evidence_ids", [])),
        "model_rationale_tags": [] if predicted is None else list(predicted.get("rationale_tags", [])),
        "output_hash": output_hash,
        "sealed_answer_included": False,
    }
    next_state.setdefault("episodes", []).append(episode)
    next_state.setdefault("failure_lattice_entries", []).append(
        {
            "task_id": str(task["task_id"]),
            "failure_signature": list(failure_signature),
        }
    )
    # Deliberately no next_state["lessons"].append(...).
    return next_state


def admit_verified_development_lesson(
    state: Mapping[str, Any],
    feedback: VerifiedDevelopmentFeedback,
) -> dict[str, Any]:
    """Admit a scoped method lesson only from frozen verified development feedback."""

    if not feedback.source_task_id.startswith("D"):
        raise ValueError("feedback_must_come_from_development_task")
    if not feedback.output_frozen:
        raise ValueError("development_output_not_frozen")
    if not feedback.evaluator_verified:
        raise ValueError("development_feedback_not_verified")
    if not _SHA256_RE.match(feedback.source_output_hash):
        raise ValueError("invalid_source_output_hash")
    if not _SHA256_RE.match(feedback.evaluator_receipt_hash):
        raise ValueError("invalid_evaluator_receipt_hash")
    principle = feedback.principle.strip()
    if not principle:
        raise ValueError("empty_principle")
    # A transferable method lesson may not carry task-local evidence IDs or
    # transfer-task identifiers into T prompts.
    if _EVIDENCE_ID_RE.search(principle):
        raise ValueError("task_local_evidence_id_in_transferable_lesson")
    if _TRANSFER_TASK_RE.search(principle):
        raise ValueError("transfer_task_identifier_in_development_lesson")

    next_state = copy.deepcopy(dict(state))
    lesson = {
        "lesson_id": _lesson_id(feedback),
        "source_task_id": feedback.source_task_id,
        "source_output_hash": feedback.source_output_hash,
        "evaluator_receipt_hash": feedback.evaluator_receipt_hash,
        "stratum": feedback.stratum,
        "principle": principle,
        "authority": "VERIFIED_DEVELOPMENT_METHOD_ONLY",
        "grants_scientific_authority": False,
    }
    next_state.setdefault("lessons", []).append(lesson)
    return next_state


def selective_experience_view(
    state: Mapping[str, Any],
    *,
    target_stratum: str,
    max_lessons: int = 3,
    max_failures: int = 3,
) -> SelectiveExperienceView:
    """Materialize a bounded task-conditioned view instead of dumping all state.

    This is a diagnostic selector, not a replacement for the full problem-fibre
    compiler.  It makes the root-cause experiment distinguish selective method
    memory from the v1.2 whole-state prompt dump.
    """

    if max_lessons < 0 or max_failures < 0:
        raise ValueError("negative_selection_budget")

    lessons = [
        item
        for item in state.get("lessons", [])
        if item.get("authority") == "VERIFIED_DEVELOPMENT_METHOD_ONLY"
        and item.get("stratum") in {target_stratum, "GENERAL"}
    ][:max_lessons]
    failures = [
        item for item in state.get("failure_lattice_entries", [])
    ][-max_failures:]

    rendered = {
        "state_kind": state.get("state_kind"),
        "verified_development_lessons": lessons,
        "recent_failure_history": failures,
    }
    return SelectiveExperienceView(
        lesson_ids=tuple(str(item["lesson_id"]) for item in lessons),
        failure_task_ids=tuple(str(item["task_id"]) for item in failures),
        rendered_state=rendered,
    )


def oracle_procedure_upper_bound() -> Tuple[str, ...]:
    """Frozen family-general method checklist; contains no transfer labels/IDs."""

    return (
        "Prefer evidence from the currently calibrated instrument measuring the registered quantity of interest; reject expired-calibration and wrong-instrument readings.",
        "An exact registered unit transformation preserves the underlying measurement; calibration authority does not transfer to uncalibrated alternatives.",
        "Before declaring contradiction, align object, regime, time or aggregation, measurement operator, and quantity of interest; mismatched contexts do not directly refute each other.",
    )
