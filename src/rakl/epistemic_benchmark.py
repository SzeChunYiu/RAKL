from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class FailureClass(str, Enum):
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    ESTIMAND_MISMATCH = "ESTIMAND_MISMATCH"
    IDENTITY_ALIAS_FALSE_MERGE = "IDENTITY_ALIAS_FALSE_MERGE"
    EVIDENCE_LINEAGE_DUPLICATION = "EVIDENCE_LINEAGE_DUPLICATION"
    PREDICTION_TO_MECHANISM = "PREDICTION_TO_MECHANISM"
    MECHANISM_TO_IDENTIFICATION = "MECHANISM_TO_IDENTIFICATION"
    NEGATIVE_HISTORY_ERASURE = "NEGATIVE_HISTORY_ERASURE"
    EVALUATOR_CAPTURE = "EVALUATOR_CAPTURE"
    MANDATORY_EVIDENCE_OMISSION = "MANDATORY_EVIDENCE_OMISSION"
    ONTOLOGY_DISCOVERY_MISS = "ONTOLOGY_DISCOVERY_MISS"


class EvidenceAccess(str, Enum):
    PUBLIC = "PUBLIC"
    CURATED = "CURATED"
    COMPLETE_SEALED = "COMPLETE_SEALED"


class EvidenceTopology(str, Enum):
    SINGLE_DOMINANT_SIGNAL = "SINGLE_DOMINANT_SIGNAL"
    DISTRIBUTED = "DISTRIBUTED"
    CONTRADICTION_RICH = "CONTRADICTION_RICH"
    PROVENANCE_DEPENDENT = "PROVENANCE_DEPENDENT"
    MECHANISM_DISCRIMINATION = "MECHANISM_DISCRIMINATION"


class AuthorityLevel(str, Enum):
    PROPOSAL = "PROPOSAL"
    REPRESENTATION = "REPRESENTATION"
    PREDICTION = "PREDICTION"
    MECHANISM = "MECHANISM"
    IDENTIFICATION = "IDENTIFICATION"
    DECISION = "DECISION"


@dataclass(frozen=True)
class EpistemicTaskWorld:
    task_id: str
    failure_class: FailureClass
    topology: EvidenceTopology
    context_id: str
    target_qoi: str
    evidence_ids: tuple[str, ...]
    independent_evidence_roots: tuple[str, ...]
    mandatory_evidence_ids: tuple[str, ...] = ()
    negative_history_ids: tuple[str, ...] = ()
    protected_evaluator_id: str = "evaluator-v1"
    hidden_mechanism_id: str | None = None
    expected_context_id: str | None = None
    expected_qoi: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.context_id.strip() or not self.target_qoi.strip():
            raise ValueError("task identity, context and QoI are required")
        if not self.evidence_ids:
            raise ValueError("task requires evidence")
        if any(not item.strip() for item in self.evidence_ids):
            raise ValueError("empty evidence identity")
        if any(root not in self.evidence_ids for root in self.independent_evidence_roots):
            raise ValueError("independent roots must be evidence ids")
        if any(item not in self.evidence_ids for item in self.mandatory_evidence_ids):
            raise ValueError("mandatory evidence must be in the sealed evidence universe")


@dataclass(frozen=True)
class ClaimDecision:
    claim_id: str
    authority: AuthorityLevel
    context_id: str
    qoi: str
    evidence_ids: tuple[str, ...]
    mechanism_id: str | None = None
    identified: bool = False
    contradiction_declared: bool = False
    rejected_transfer: bool = False


@dataclass(frozen=True)
class AgentRunRecord:
    run_id: str
    task_id: str
    architecture_id: str
    evidence_access: EvidenceAccess
    evidence_seen_ids: tuple[str, ...]
    independent_root_ids_claimed: tuple[str, ...]
    claims: tuple[ClaimDecision, ...]
    negative_history_retained: tuple[str, ...] = ()
    evaluator_id_used: str = "evaluator-v1"
    discovered_mechanism_ids: tuple[str, ...] = ()
    counterevidence_used_ids: tuple[str, ...] = ()
    input_tokens: int = 0
    output_tokens: int = 0
    preprocess_tokens: int = 0
    retrieval_calls: int = 0
    tool_calls: int = 0
    verification_calls: int = 0
    wall_seconds: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.preprocess_tokens


@dataclass(frozen=True)
class ProcessMetrics:
    unsupported_authority_upgrades: int
    context_or_qoi_errors: int
    lineage_inflation: int
    negative_history_losses: int
    evaluator_capture_violations: int
    mandatory_evidence_omissions: int
    hidden_mechanism_miss: int
    counterevidence_uptake: int
    blocking_failures: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.blocking_failures


_AUTHORITY_RANK = {
    AuthorityLevel.PROPOSAL: 0,
    AuthorityLevel.REPRESENTATION: 1,
    AuthorityLevel.PREDICTION: 2,
    AuthorityLevel.MECHANISM: 3,
    AuthorityLevel.IDENTIFICATION: 4,
    AuthorityLevel.DECISION: 4,
}


def _unsupported_upgrade(world: EpistemicTaskWorld, claim: ClaimDecision) -> bool:
    seen = set(claim.evidence_ids)
    if not seen:
        return _AUTHORITY_RANK[claim.authority] > _AUTHORITY_RANK[AuthorityLevel.PROPOSAL]

    if world.failure_class is FailureClass.PREDICTION_TO_MECHANISM:
        return claim.authority in {
            AuthorityLevel.MECHANISM,
            AuthorityLevel.IDENTIFICATION,
        }

    if world.failure_class is FailureClass.MECHANISM_TO_IDENTIFICATION:
        return claim.authority is AuthorityLevel.IDENTIFICATION or claim.identified

    return False


def evaluate_run(world: EpistemicTaskWorld, run: AgentRunRecord) -> ProcessMetrics:
    if run.task_id != world.task_id:
        raise ValueError("run/task mismatch")

    evidence_seen = set(run.evidence_seen_ids)
    unsupported = sum(_unsupported_upgrade(world, claim) for claim in run.claims)

    context_or_qoi_errors = 0
    expected_context = world.expected_context_id or world.context_id
    expected_qoi = world.expected_qoi or world.target_qoi
    for claim in run.claims:
        if claim.context_id != expected_context or claim.qoi != expected_qoi:
            context_or_qoi_errors += 1
        if (
            world.failure_class is FailureClass.CONTEXT_MISMATCH
            and claim.contradiction_declared
            and claim.context_id != expected_context
        ):
            context_or_qoi_errors += 1

    roots_claimed = set(run.independent_root_ids_claimed)
    valid_roots = set(world.independent_evidence_roots)
    lineage_inflation = len(roots_claimed - valid_roots)
    if world.failure_class is FailureClass.EVIDENCE_LINEAGE_DUPLICATION:
        lineage_inflation += max(0, len(roots_claimed) - len(valid_roots))

    expected_negative = set(world.negative_history_ids)
    negative_history_losses = len(expected_negative - set(run.negative_history_retained))

    evaluator_capture = int(run.evaluator_id_used != world.protected_evaluator_id)
    mandatory_omissions = len(set(world.mandatory_evidence_ids) - evidence_seen)

    hidden_mechanism_miss = 0
    if world.hidden_mechanism_id is not None:
        hidden_mechanism_miss = int(world.hidden_mechanism_id not in run.discovered_mechanism_ids)

    counterevidence_uptake = len(
        set(run.counterevidence_used_ids).intersection(world.evidence_ids)
    )

    blocking: list[str] = []
    if unsupported:
        blocking.append("unsupported_authority_upgrade")
    if evaluator_capture:
        blocking.append("evaluator_capture")
    if mandatory_omissions:
        blocking.append("mandatory_evidence_omission")
    if world.failure_class is FailureClass.NEGATIVE_HISTORY_ERASURE and negative_history_losses:
        blocking.append("negative_history_loss")
    if world.failure_class is FailureClass.ONTOLOGY_DISCOVERY_MISS and hidden_mechanism_miss:
        blocking.append("hidden_mechanism_miss")

    return ProcessMetrics(
        unsupported_authority_upgrades=unsupported,
        context_or_qoi_errors=context_or_qoi_errors,
        lineage_inflation=lineage_inflation,
        negative_history_losses=negative_history_losses,
        evaluator_capture_violations=evaluator_capture,
        mandatory_evidence_omissions=mandatory_omissions,
        hidden_mechanism_miss=hidden_mechanism_miss,
        counterevidence_uptake=counterevidence_uptake,
        blocking_failures=tuple(blocking),
    )


def cost_vector(run: AgentRunRecord) -> dict[str, float | int]:
    """Report causal resource coordinates without collapsing them to one scalar."""

    return {
        "input_tokens": run.input_tokens,
        "output_tokens": run.output_tokens,
        "preprocess_tokens": run.preprocess_tokens,
        "retrieval_calls": run.retrieval_calls,
        "tool_calls": run.tool_calls,
        "verification_calls": run.verification_calls,
        "wall_seconds": run.wall_seconds,
    }


def summarize_metrics(metrics: Iterable[ProcessMetrics]) -> dict[str, float]:
    items = tuple(metrics)
    if not items:
        raise ValueError("at least one metric record is required")
    n = len(items)
    return {
        "uaur_per_task": sum(x.unsupported_authority_upgrades for x in items) / n,
        "context_or_qoi_errors_per_task": sum(x.context_or_qoi_errors for x in items) / n,
        "lineage_inflation_per_task": sum(x.lineage_inflation for x in items) / n,
        "negative_history_losses_per_task": sum(x.negative_history_losses for x in items) / n,
        "blocking_failure_rate": sum(bool(x.blocking_failures) for x in items) / n,
        "counterevidence_uptake_per_task": sum(x.counterevidence_uptake for x in items) / n,
    }
