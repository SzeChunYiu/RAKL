"""Thin adapter binding GLM52 mechanism suite v1.1 to canonical RAKL."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from rakl.epistemic_search import (
    EvidenceStance,
    SearchCandidate,
    SearchIndexKind,
    SearchRankVector,
    SearchVertical,
    ScientificSearchQuestion,
    build_interaction_space,
    compile_search_intents,
    detect_epistemic_spam,
    diversify_candidates,
)
from rakl.epistemic_trajectory import EpistemicStepFamily, ObservedEpistemicStep
from rakl.experience_substrate import ExperienceLedger, TaskEpisode
from rakl.problem_fibre import ProblemAtom, compile_problem_fibre
from rakl.v3_authority import canonical_sha256

from common import file_sha256, stable_hash

PROTOCOL_ID = "GLM52-MECHANISM-SUITE-V1.1"
PROTOCOL_VERSION = "1.1.0"
ADAPTER_VERSION = "1.1.0"

GOLD_BEARING_TASK_KEYS = frozenset(
    {
        "verdict",
        "support_ids",
        "refute_ids",
        "gold_ids",
        "hidden_truth",
        "oracle_action",
        "gold_steps",
        "licensed_action",
        "finding_label",
        "is_gold",
    }
)

GOLD_BEARING_DOC_KEYS = frozenset({"is_gold", "finding_label", "gold_role", "verdict"})

BOUND_MODULES = (
    "src/rakl/epistemic_search.py",
    "src/rakl/problem_fibre.py",
    "src/rakl/epistemic_trajectory.py",
    "src/rakl/v3_authority.py",
    "src/rakl/experience_substrate.py",
)


@dataclass(frozen=True)
class RetrievalReceipt:
    protocol_id: str
    protocol_version: str
    framework_sha: str
    method_version: str
    adapter_version: str
    adapter_code_hash: str
    framework_module_hashes: tuple[tuple[str, str], ...]
    selected_candidate_ids: tuple[str, ...]
    interaction_space_id: str | None
    rejected_spam_flags: tuple[tuple[str, str], ...]
    state_hash: str
    task_manifest_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class MaterializationReceipt:
    protocol_id: str
    protocol_version: str
    framework_sha: str
    method_version: str
    adapter_version: str
    adapter_code_hash: str
    framework_module_hashes: tuple[tuple[str, str], ...]
    fibre_snapshot_hash: str
    episode_ids: tuple[str, ...]
    lesson_ids: tuple[str, ...]
    failure_ids: tuple[str, ...]
    state_hash: str
    task_manifest_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


class FrameworkAdapter(Protocol):
    framework_sha: str
    method_version: str
    adapter_version: str

    def retrieve(self, task: Mapping[str, Any], budget: int) -> RetrievalReceipt: ...
    def materialize_experience(
        self, task: Mapping[str, Any], state: Mapping[str, Any], budget: int
    ) -> MaterializationReceipt: ...
    def govern_trajectory(
        self, proposal: Mapping[str, Any], case: Mapping[str, Any]
    ) -> ObservedEpistemicStep: ...


def _git_head(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_FRAMEWORK_SHA"


def _read_method_version(repo_root: Path) -> str:
    manifest = repo_root / "RAKL_VERSION.json"
    if not manifest.is_file():
        return "UNKNOWN"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return str(data.get("incumbent", {}).get("method_version", "UNKNOWN"))


def _module_hashes(repo_root: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for rel in BOUND_MODULES:
        path = repo_root / rel
        if path.is_file():
            rows.append((rel, file_sha256(path)))
    return tuple(sorted(rows))


def strip_gold_fields(task: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of task metadata with gold-bearing keys removed."""
    return {key: value for key, value in task.items() if key not in GOLD_BEARING_TASK_KEYS}


def visible_doc(doc: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in doc.items() if key not in GOLD_BEARING_DOC_KEYS}


def _stance_from_kind(kind: str) -> EvidenceStance:
    normalized = kind.lower()
    if normalized == "correction":
        return EvidenceStance.RETRACTION_CORRECTION
    if normalized in {"measurement", "review"}:
        return EvidenceStance.CONTEXT
    if normalized == "commentary":
        return EvidenceStance.NEUTRAL
    return EvidenceStance.CONTEXT


def _doc_to_candidate(
    doc: Mapping[str, Any],
    *,
    task: Mapping[str, Any],
    question: ScientificSearchQuestion,
) -> SearchCandidate:
    visible = visible_doc(doc)
    doc_id = str(visible["doc_id"])
    entity = str(visible.get("entity", ""))
    qoi = str(visible.get("qoi", ""))
    context = str(visible.get("context", ""))
    root = str(visible.get("root", doc_id))
    kind = str(visible.get("kind", "measurement"))
    summary = str(visible.get("summary", ""))
    exact = entity == task.get("entity") and qoi == task.get("qoi") and context == task.get("context")
    context_alignment = 1.0 if exact else 0.35 if entity == task.get("entity") and qoi == task.get("qoi") else 0.1
    structural_fit = 1.0 if exact else 0.4
    query_terms = set(str(task.get("question", "")).lower().split())
    summary_terms = set(summary.lower().split())
    overlap = len(query_terms & summary_terms) / max(1, len(query_terms))
    rank = SearchRankVector(
        query_relevance=overlap,
        root_obligation_relevance=0.5,
        expected_information_gain=0.4,
        structural_fit=structural_fit,
        context_alignment=context_alignment,
        source_authenticity=0.8,
        freshness=float(visible.get("date", 0)) / 10000.0,
        independent_root_contribution=0.5,
        contradiction_value=0.2 if kind == "correction" else 0.0,
        negative_result_value=0.0,
        novel_route_value=0.1,
        graph_centrality=0.0,
        retrieval_cost=0.1,
        verification_cost=0.2,
        failure_risk=0.1,
    )
    leak = any(token in summary.lower() for token in ("gold_answer", "hidden_verdict", "oracle_only"))
    return SearchCandidate(
        candidate_id=doc_id,
        vertical=SearchVertical.LITERATURE,
        index_kinds=(SearchIndexKind.CLAIM_EVIDENCE, SearchIndexKind.STRUCTURAL),
        rank=rank,
        evidence_root_id=root,
        canonical_content_id=canonical_sha256(visible),
        mechanism_family=kind,
        stance=_stance_from_kind(kind),
        benchmark_target_leak=leak,
        keyword_overlap_ratio=min(1.0, overlap),
        substantive_match_score=structural_fit,
    )


class CanonicalFrameworkAdapter:
    """Current-framework adapter for GLM52 mechanism suite v1.1."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path(__file__).resolve().parents[2]
        self.framework_sha = _git_head(self._repo_root)
        self.method_version = _read_method_version(self._repo_root)
        self.adapter_version = ADAPTER_VERSION
        self.adapter_code_hash = file_sha256(Path(__file__))
        self.framework_module_hashes = _module_hashes(self._repo_root)

    def subject_manifest(self) -> dict[str, Any]:
        return {
            "protocol_id": PROTOCOL_ID,
            "protocol_version": PROTOCOL_VERSION,
            "framework_sha": self.framework_sha,
            "method_version": self.method_version,
            "adapter_version": self.adapter_version,
            "adapter_code_hash": self.adapter_code_hash,
            "framework_module_hashes": dict(self.framework_module_hashes),
            "outcome_access_status": "NO_NEW_GLM_OUTCOME",
            "provider_profile": "claude-cn / Z.AI Anthropic-compatible gateway (env-only)",
        }

    def retrieve(self, task: Mapping[str, Any], budget: int) -> RetrievalReceipt:
        if budget < 1:
            raise ValueError("retrieval budget must be positive")
        visible_task = strip_gold_fields(task)
        task_manifest_hash = stable_hash(visible_task)
        question = ScientificSearchQuestion(
            question_id=str(visible_task.get("task_id", "task-unknown")),
            root_goal=str(visible_task.get("question", "")),
            atom_id=str(visible_task.get("entity", "atom")),
            residual_terms=tuple(str(visible_task.get("qoi", "qoi")).split()),
            structural_coordinates=(
                str(visible_task.get("entity", "")),
                str(visible_task.get("qoi", "")),
                str(visible_task.get("context", "")),
            ),
        )
        intents = compile_search_intents(question)
        docs = visible_task.get("docs", ())
        candidates = tuple(
            _doc_to_candidate(doc, task=visible_task, question=question)
            for doc in docs
            if isinstance(doc, Mapping)
        )
        spam = detect_epistemic_spam(candidates)
        rejected = tuple(
            (item.candidate_id, flag.value)
            for item in spam
            for flag in item.flags
        )
        blocked_ids = {
            item.candidate_id
            for item in spam
            if any(flag.value == "BENCHMARK_TARGET_LEAK" for flag in item.flags)
        }
        eligible = tuple(item for item in candidates if item.candidate_id not in blocked_ids)
        selected = diversify_candidates(eligible, limit=budget)
        space = build_interaction_space(
            question,
            intents,
            eligible,
            space_id=f"ris-{question.question_id}",
            max_candidates=budget,
        )
        state_hash = stable_hash(
            {
                "selected": [item.candidate_id for item in selected],
                "space": space.snapshot_hash,
            }
        )
        return RetrievalReceipt(
            protocol_id=PROTOCOL_ID,
            protocol_version=PROTOCOL_VERSION,
            framework_sha=self.framework_sha,
            method_version=self.method_version,
            adapter_version=self.adapter_version,
            adapter_code_hash=self.adapter_code_hash,
            framework_module_hashes=self.framework_module_hashes,
            selected_candidate_ids=tuple(item.candidate_id for item in selected),
            interaction_space_id=space.space_id,
            rejected_spam_flags=rejected,
            state_hash=state_hash,
            task_manifest_hash=task_manifest_hash,
        )

    def materialize_experience(
        self,
        task: Mapping[str, Any],
        state: Mapping[str, Any],
        budget: int,
    ) -> MaterializationReceipt:
        if budget < 1:
            raise ValueError("materialization budget must be positive")
        visible_task = strip_gold_fields(task)
        task_manifest_hash = stable_hash(visible_task)
        atom = ProblemAtom(
            atom_id=str(visible_task.get("task_id", "atom")),
            goal=str(visible_task.get("question", "")),
            context_hash=stable_hash(
                (
                    visible_task.get("entity"),
                    visible_task.get("qoi"),
                    visible_task.get("context"),
                )
            ),
            structural_coordinates=tuple(
                str(visible_task.get(key, ""))
                for key in ("entity", "qoi", "context", "family")
                if visible_task.get(key)
            )
            or ("unspecified",),
            desired_effects=("scoped_experience_materialization",),
        )
        ledger: ExperienceLedger | None = None
        raw_episodes = state.get("episodes")
        if isinstance(raw_episodes, Sequence):
            episodes = tuple(item for item in raw_episodes if isinstance(item, TaskEpisode))
            if episodes:
                ledger = ExperienceLedger(episodes=episodes)
        fibre = compile_problem_fibre(atom, experience_ledger=ledger, top_k_each=budget)
        state_hash = stable_hash(
            {
                "fibre": fibre.snapshot_hash,
                "budget": budget,
            }
        )
        return MaterializationReceipt(
            protocol_id=PROTOCOL_ID,
            protocol_version=PROTOCOL_VERSION,
            framework_sha=self.framework_sha,
            method_version=self.method_version,
            adapter_version=self.adapter_version,
            adapter_code_hash=self.adapter_code_hash,
            framework_module_hashes=self.framework_module_hashes,
            fibre_snapshot_hash=fibre.snapshot_hash,
            episode_ids=tuple(ep.episode_id for ep in fibre.episodes[:budget]),
            lesson_ids=(),
            failure_ids=tuple(item.failure_id for item in fibre.failures[:budget]),
            state_hash=state_hash,
            task_manifest_hash=task_manifest_hash,
        )

    def govern_trajectory(
        self,
        proposal: Mapping[str, Any],
        case: Mapping[str, Any],
    ) -> ObservedEpistemicStep:
        visible_case = strip_gold_fields(case)
        step_id = str(proposal.get("step_id", visible_case.get("step_id", "step-1")))
        family_name = str(proposal.get("family", "CLAIM_EVIDENCE_BINDING"))
        family = EpistemicStepFamily(family_name)
        action = str(proposal.get("action", "CANNOT_CHECK"))
        evidence_ids = tuple(str(x) for x in proposal.get("evidence_ids", ()))
        root_ids = tuple(str(x) for x in proposal.get("root_ids", ()))
        negative_history_ids = tuple(str(x) for x in proposal.get("negative_history_ids", ()))
        authority_before = str(
            proposal.get("authority_before", visible_case.get("initial_authority_fingerprint", "auth-0"))
        )
        sequence_index = int(proposal.get("sequence_index", 1))
        reviewed_ids = {
            str(item.get("evidence_id"))
            for item in visible_case.get("evidence", ())
            if isinstance(item, Mapping) and item.get("reviewed")
        }
        target_scope = str(visible_case.get("target_scope", ""))
        target_axis = str(visible_case.get("target_axis", ""))
        exact_reviewed = [
            item
            for item in visible_case.get("evidence", ())
            if isinstance(item, Mapping)
            and item.get("reviewed")
            and str(item.get("scope", "")) == target_scope
            and str(item.get("axis", "")) == target_axis
        ]
        support_roots = {
            str(item.get("root"))
            for item in exact_reviewed
            if str(item.get("polarity", "")) == "SUPPORT"
        }
        refute_roots = {
            str(item.get("root"))
            for item in exact_reviewed
            if str(item.get("polarity", "")) == "REFUTE"
        }
        cited_reviewed = all(eid in reviewed_ids for eid in evidence_ids)
        safe_action = action
        if action in {"COMMIT_SUPPORT", "COMMIT_REFUTATION"} and not cited_reviewed:
            safe_action = "CANNOT_CHECK"
        if action == "COMMIT_SUPPORT" and (len(support_roots) < 2 or refute_roots):
            safe_action = "CANNOT_CHECK"
        if action == "COMMIT_REFUTATION" and (len(refute_roots) < 2 or support_roots):
            safe_action = "CANNOT_CHECK"
        authority_after = authority_before
        if safe_action in {"COMMIT_SUPPORT", "COMMIT_REFUTATION"} and safe_action == action:
            authority_after = f"{authority_before}:licensed:{safe_action.lower()}"
        return ObservedEpistemicStep(
            step_id=step_id,
            family=family,
            action=safe_action,
            evidence_ids=evidence_ids,
            root_ids=root_ids or tuple(sorted(support_roots | refute_roots)),
            negative_history_ids=negative_history_ids,
            authority_before=authority_before,
            authority_after=authority_after,
            sequence_index=sequence_index,
        )
