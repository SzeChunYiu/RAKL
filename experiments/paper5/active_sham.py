#!/usr/bin/env python3
"""Paper 5 active sham-memory construction matcher and validator.

Implements ATTRIBUTION_PREREGISTRATION_V1 §4 for the ``RAKL_SHAM_MEMORY`` arm:

* match learned-memory object count / type histogram / token budget;
* select structurally incompatible, disjoint-family controls;
* preserve source/evidence-lineage identities as sham controls rather than
  copying relevant content;
* fail closed on target-answer leakage, eligible structural true-matches,
  solution-artifact ids, or gibberish-only controls.

This module freezes an algorithm identity only. It does **not** authorize
confirmatory four-arm execution, bind confirmatory outcomes, or grant
scientific authority. Construction must not inspect target answers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
POLICY_SCHEMA_PATH = ROOT / "schemas" / "paper5-sham-policy-v1.schema.json"
DEFAULT_POLICY_PATH = ROOT / "research" / "paper5_sham_policy_v1" / "SHAM_POLICY.json"

OBJECT_TYPES = ("episode", "failure", "lesson", "tool", "motif")
ANSWER_FIELD_NAMES = frozenset(
    {
        "target_answer",
        "hidden_answer",
        "gold_answer",
        "solution",
        "solution_artifact_id",
        "evaluator_private_target",
        "answer_key",
    }
)

CLAIM_BOUNDARY = (
    "Active sham construction algorithm + leakage validator only. "
    "Does not freeze a confirmatory four-arm packet, authorize model execution, "
    "or grant scientific authority. Sham policy hash may be supplied to "
    "build_executor_contract.py but confirmatory runs remain unauthorized until "
    "CAPABLE_MODEL + full packet freeze."
)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tokenize(text: str) -> list[str]:
    return [tok for tok in re.findall(r"[A-Za-z0-9_]+", text.lower()) if tok]


def estimate_token_count(text: str) -> int:
    tokens = tokenize(text)
    return max(len(tokens), 1 if text.strip() else 0)


@dataclass(frozen=True)
class MemoryObject:
    """Normalized memory unit for sham construction / audit.

    Construction sees content and structural metadata but must not carry target
    answer fields. Lineage ids are preserved as sham-control identities.
    """

    object_id: str
    object_type: str
    family_id: str
    structural_signature: tuple[str, ...]
    content_text: str
    token_count: int
    recency_rank: int
    authority_level: str
    source_lineage_id: str
    content_hash: str
    solution_artifact_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.object_type not in OBJECT_TYPES:
            raise ValueError(f"unsupported object_type: {self.object_type!r}")
        if self.token_count < 0:
            raise ValueError("token_count must be >= 0")
        if not self.object_id or not self.family_id or not self.source_lineage_id:
            raise ValueError("object_id, family_id and source_lineage_id are required")
        if not self.structural_signature:
            raise ValueError("structural_signature must be non-empty")
        if not self.content_hash or len(self.content_hash) != 64:
            raise ValueError("content_hash must be a 64-char hex digest")


@dataclass(frozen=True)
class TargetExclusion:
    """Hidden-target constraints the matcher may use without seeing answers.

    Answer strings and solution artifact ids are reserved for the validator's
    post-construction leakage audit. The matcher only receives structural
    exclusion signatures and forbidden artifact ids that must not appear.
    """

    eligible_true_match_signatures: frozenset[str]
    forbidden_solution_artifact_ids: frozenset[str] = frozenset()
    # Present only for validator audits; matcher construction ignores these.
    hidden_answer_strings: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ShamConstructionResult:
    policy_id: str
    policy_hash: str
    construction_seed: int
    sham_objects: tuple[MemoryObject, ...]
    learned_object_ids: tuple[str, ...]
    selected_control_ids: tuple[str, ...]
    type_histogram: Mapping[str, int]
    total_tokens: int
    mean_recency_rank: float
    construction_receipt_sha256: str
    grants_scientific_authority: bool = False
    authorizes_confirmatory_execution: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_hash": self.policy_hash,
            "construction_seed": self.construction_seed,
            "sham_objects": [memory_object_to_dict(obj) for obj in self.sham_objects],
            "learned_object_ids": list(self.learned_object_ids),
            "selected_control_ids": list(self.selected_control_ids),
            "type_histogram": dict(self.type_histogram),
            "total_tokens": self.total_tokens,
            "mean_recency_rank": self.mean_recency_rank,
            "construction_receipt_sha256": self.construction_receipt_sha256,
            "grants_scientific_authority": False,
            "authorizes_confirmatory_execution": False,
        }


@dataclass(frozen=True)
class ShamValidationReport:
    status: str  # PASS | FAIL | CANNOT_CHECK
    blockers: tuple[str, ...]
    limitations: tuple[str, ...]
    checks: Mapping[str, bool]
    policy_hash: str
    sham_state_hash: str
    grants_scientific_authority: bool = False
    authorizes_confirmatory_execution: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "blockers": list(self.blockers),
            "limitations": list(self.limitations),
            "checks": dict(self.checks),
            "policy_hash": self.policy_hash,
            "sham_state_hash": self.sham_state_hash,
            "grants_scientific_authority": False,
            "authorizes_confirmatory_execution": False,
        }


@dataclass
class _RNG:
    """Deterministic xorshift64* for reproducible construction without importing random state."""

    state: int

    def next_u64(self) -> int:
        x = self.state & ((1 << 64) - 1)
        x ^= (x >> 12) & ((1 << 64) - 1)
        x ^= (x << 25) & ((1 << 64) - 1)
        x ^= (x >> 27) & ((1 << 64) - 1)
        self.state = x
        return (x * 0x2545F4914F6CDD1D) & ((1 << 64) - 1)

    def shuffle(self, items: list[Any]) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.next_u64() % (i + 1)
            items[i], items[j] = items[j], items[i]


def memory_object_from_dict(payload: Mapping[str, Any]) -> MemoryObject:
    leaked = sorted(ANSWER_FIELD_NAMES.intersection(payload))
    if leaked:
        raise ValueError(f"memory object carries forbidden answer fields: {leaked}")
    content_text = str(payload["content_text"])
    token_count = int(payload.get("token_count", estimate_token_count(content_text)))
    signature = tuple(str(x) for x in payload["structural_signature"])
    solution_ids = tuple(str(x) for x in (payload.get("solution_artifact_ids") or ()))
    content_hash = str(payload.get("content_hash") or canonical_sha256({"content_text": content_text}))
    return MemoryObject(
        object_id=str(payload["object_id"]),
        object_type=str(payload["object_type"]),
        family_id=str(payload["family_id"]),
        structural_signature=signature,
        content_text=content_text,
        token_count=token_count,
        recency_rank=int(payload["recency_rank"]),
        authority_level=str(payload["authority_level"]),
        source_lineage_id=str(payload["source_lineage_id"]),
        content_hash=content_hash,
        solution_artifact_ids=solution_ids,
    )


def memory_object_to_dict(obj: MemoryObject) -> dict[str, Any]:
    return {
        "object_id": obj.object_id,
        "object_type": obj.object_type,
        "family_id": obj.family_id,
        "structural_signature": list(obj.structural_signature),
        "content_text": obj.content_text,
        "token_count": obj.token_count,
        "recency_rank": obj.recency_rank,
        "authority_level": obj.authority_level,
        "source_lineage_id": obj.source_lineage_id,
        "content_hash": obj.content_hash,
        "solution_artifact_ids": list(obj.solution_artifact_ids),
    }


def load_policy(path: Path | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path is not None else DEFAULT_POLICY_PATH
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"policy root must be an object: {policy_path}")
    validate_policy_document(payload)
    return payload


def validate_policy_document(policy: Mapping[str, Any]) -> None:
    if not POLICY_SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"missing sham policy schema: {POLICY_SCHEMA_PATH}")
    schema = json.loads(POLICY_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(policy), key=lambda err: list(err.path))
    if errors:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in err.path) or '<root>'}: {err.message}" for err in errors[:5]
        )
        raise ValueError(f"sham policy violates paper5-sham-policy-v1: {detail}")
    if policy.get("grants_scientific_authority") is not False:
        raise ValueError("sham policy must not grant scientific authority")
    if policy.get("authorizes_confirmatory_execution") is not False:
        raise ValueError("sham policy must not authorize confirmatory execution")
    if policy.get("evaluated_results_accessed") is not False:
        raise ValueError("sham policy must record evaluated_results_accessed=false")
    expected = policy_canonical_sha256(policy)
    observed = policy.get("policy_canonical_sha256")
    if observed != expected:
        raise ValueError(
            f"policy_canonical_sha256 mismatch: observed={observed} expected={expected}"
        )


def policy_canonical_sha256(policy: Mapping[str, Any]) -> str:
    body = dict(policy)
    body["policy_canonical_sha256"] = ""
    return canonical_sha256(body)


def build_policy_document(
    *,
    construction_seed: int = 20260812,
    token_budget_rel_tolerance: float = 0.15,
    token_budget_abs_tolerance: int = 32,
    recency_rank_abs_tolerance: int = 2,
    min_content_token_length: int = 4,
    notes: str | None = None,
) -> dict[str, Any]:
    """Assemble the frozen algorithm identity (no confirmatory outcomes)."""

    policy: dict[str, Any] = {
        "schema_version": "paper5-sham-policy-v1",
        "policy_id": "paper5-active-sham-policy-v1",
        "algorithm_id": "matched_irrelevant_disjoint_family_v1",
        "algorithm_version": "1",
        "construction_seed": int(construction_seed),
        "object_types": list(OBJECT_TYPES),
        "selection_rule": {
            "mechanism": "matched_irrelevant_disjoint_family",
            "require_disjoint_family": True,
            "require_structural_incompatibility": True,
            "preserve_source_lineage_ids": True,
            "forbid_target_answer_fields": True,
            "forbid_eligible_true_match_signatures": True,
        },
        "budget_matching": {
            "match_object_count": True,
            "match_type_histogram": True,
            "token_budget_rel_tolerance": float(token_budget_rel_tolerance),
            "token_budget_abs_tolerance": int(token_budget_abs_tolerance),
            "recency_rank_abs_tolerance": int(recency_rank_abs_tolerance),
            "report_mismatch_as_limitation": True,
        },
        "leakage_audit": {
            "reject_answer_substring_overlap": True,
            "reject_solution_artifact_ids": True,
            "reject_eligible_structural_signature_overlap": True,
            "reject_gibberish_only_controls": True,
            "min_content_token_length": int(min_content_token_length),
        },
        "forbidden_mechanisms": [
            "gibberish_only_controls",
            "copy_learned_relevant_content",
            "inspect_target_answers_during_construction",
            "post_outcome_policy_edit",
        ],
        "claim_boundary": CLAIM_BOUNDARY,
        "grants_scientific_authority": False,
        "authorizes_confirmatory_execution": False,
        "evaluated_results_accessed": False,
        "preregistration_path": "experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md",
        "matcher_module": "experiments/paper5/active_sham.py",
        "notes": notes,
        "policy_canonical_sha256": "",
    }
    policy["policy_canonical_sha256"] = policy_canonical_sha256(policy)
    validate_policy_document(policy)
    return policy


def _type_histogram(objects: Sequence[MemoryObject]) -> Counter[str]:
    return Counter(obj.object_type for obj in objects)


def _signature_set(obj: MemoryObject) -> frozenset[str]:
    return frozenset(obj.structural_signature)


def _is_structurally_compatible(obj: MemoryObject, exclusion: TargetExclusion) -> bool:
    return bool(_signature_set(obj) & exclusion.eligible_true_match_signatures)


def _is_gibberish(obj: MemoryObject, min_content_token_length: int) -> bool:
    tokens = tokenize(obj.content_text)
    if len(tokens) < min_content_token_length:
        return True
    # Repeated single-character / placeholder spam is not a valid sham control.
    unique = {tok for tok in tokens if tok not in {"the", "a", "an", "of", "to", "and"}}
    if len(unique) <= 1:
        return True
    if re.fullmatch(r"(?:[xX0-9\s]+|lorem|ipsum|asdf|qwerty|zzzz)+", obj.content_text.strip()):
        return True
    return False


def _eligible_controls(
    *,
    control_pool: Sequence[MemoryObject],
    learned: Sequence[MemoryObject],
    exclusion: TargetExclusion,
    min_content_token_length: int,
) -> list[MemoryObject]:
    learned_families = {obj.family_id for obj in learned}
    learned_ids = {obj.object_id for obj in learned}
    learned_content = {obj.content_hash for obj in learned}
    out: list[MemoryObject] = []
    for obj in control_pool:
        if obj.object_id in learned_ids:
            continue
        if obj.content_hash in learned_content:
            continue
        if obj.family_id in learned_families:
            continue
        if _is_structurally_compatible(obj, exclusion):
            continue
        if obj.solution_artifact_ids and set(obj.solution_artifact_ids) & exclusion.forbidden_solution_artifact_ids:
            continue
        if _is_gibberish(obj, min_content_token_length):
            continue
        out.append(obj)
    return out


def construct_active_sham(
    *,
    policy: Mapping[str, Any],
    learned_objects: Sequence[MemoryObject],
    control_pool: Sequence[MemoryObject],
    exclusion: TargetExclusion,
) -> ShamConstructionResult:
    """Construct a sham memory state under the frozen policy.

    Raises ``ValueError`` when construction is impossible under fail-closed rules.
    Does not inspect ``exclusion.hidden_answer_strings``.
    """

    validate_policy_document(policy)
    if not learned_objects:
        raise ValueError("learned_objects must be non-empty for active sham matching")

    min_tokens = int(policy["leakage_audit"]["min_content_token_length"])
    for obj in learned_objects:
        leaked = ANSWER_FIELD_NAMES.intersection(asdict(obj))
        if leaked:
            raise ValueError(f"learned object exposes answer fields: {sorted(leaked)}")
        if _is_gibberish(obj, min_tokens):
            raise ValueError(f"learned object looks empty/gibberish: {obj.object_id}")

    candidates = _eligible_controls(
        control_pool=control_pool,
        learned=learned_objects,
        exclusion=exclusion,
        min_content_token_length=min_tokens,
    )
    if not candidates:
        raise ValueError("CANNOT_CHECK: no eligible disjoint-family sham controls in pool")

    rng = _RNG(state=(int(policy["construction_seed"]) ^ 0xA5A5_5A5A_C3C3_3C3C) or 1)
    by_type: dict[str, list[MemoryObject]] = {t: [] for t in OBJECT_TYPES}
    for obj in candidates:
        by_type[obj.object_type].append(obj)
    for bucket in by_type.values():
        rng.shuffle(bucket)

    needed = _type_histogram(learned_objects)
    selected: list[MemoryObject] = []
    for object_type, count in sorted(needed.items()):
        bucket = by_type.get(object_type, [])
        if len(bucket) < count:
            raise ValueError(
                f"CANNOT_CHECK: insufficient {object_type} controls: need {count}, have {len(bucket)}"
            )
        # Prefer token-budget proximity while remaining deterministic via pre-shuffle order.
        target_tokens = [obj.token_count for obj in learned_objects if obj.object_type == object_type]
        chosen: list[MemoryObject] = []
        remaining = list(bucket)
        for target in target_tokens:
            remaining.sort(key=lambda obj: (abs(obj.token_count - target), obj.object_id))
            pick = remaining.pop(0)
            chosen.append(pick)
        selected.extend(chosen)
        # Remove chosen from type bucket for subsequent types (already removed locally).

    # Preserve learned order of types by sorting selected to mirror learned sequence positions.
    selected_sorted: list[MemoryObject] = []
    pools = {t: [o for o in selected if o.object_type == t] for t in OBJECT_TYPES}
    for learned in learned_objects:
        bucket = pools[learned.object_type]
        if not bucket:
            raise ValueError(f"internal selection shortfall for type {learned.object_type}")
        # Choose nearest remaining recency/token match.
        bucket.sort(
            key=lambda obj: (
                abs(obj.recency_rank - learned.recency_rank),
                abs(obj.token_count - learned.token_count),
                obj.object_id,
            )
        )
        selected_sorted.append(bucket.pop(0))

    hist = _type_histogram(selected_sorted)
    if hist != needed:
        raise ValueError(f"type histogram mismatch after selection: {dict(hist)} != {dict(needed)}")

    total_tokens = sum(obj.token_count for obj in selected_sorted)
    mean_recency = sum(obj.recency_rank for obj in selected_sorted) / len(selected_sorted)
    policy_hash = str(policy["policy_canonical_sha256"])
    receipt_body = {
        "policy_hash": policy_hash,
        "construction_seed": int(policy["construction_seed"]),
        "learned_object_ids": [obj.object_id for obj in learned_objects],
        "selected_control_ids": [obj.object_id for obj in selected_sorted],
        "sham_content_hashes": [obj.content_hash for obj in selected_sorted],
        "type_histogram": dict(hist),
        "total_tokens": total_tokens,
    }
    return ShamConstructionResult(
        policy_id=str(policy["policy_id"]),
        policy_hash=policy_hash,
        construction_seed=int(policy["construction_seed"]),
        sham_objects=tuple(selected_sorted),
        learned_object_ids=tuple(obj.object_id for obj in learned_objects),
        selected_control_ids=tuple(obj.object_id for obj in selected_sorted),
        type_histogram=dict(hist),
        total_tokens=total_tokens,
        mean_recency_rank=mean_recency,
        construction_receipt_sha256=canonical_sha256(receipt_body),
    )


def validate_active_sham(
    *,
    policy: Mapping[str, Any],
    learned_objects: Sequence[MemoryObject],
    sham_objects: Sequence[MemoryObject],
    exclusion: TargetExclusion,
) -> ShamValidationReport:
    """Hostile leakage + budget validator for a constructed sham state."""

    validate_policy_document(policy)
    blockers: list[str] = []
    limitations: list[str] = []
    checks: dict[str, bool] = {}

    policy_hash = str(policy["policy_canonical_sha256"])
    sham_state_hash = canonical_sha256([memory_object_to_dict(obj) for obj in sham_objects])

    # --- structural / answer leakage ---
    eligible_hits: list[str] = []
    for obj in sham_objects:
        overlap = sorted(_signature_set(obj) & exclusion.eligible_true_match_signatures)
        if overlap:
            eligible_hits.append(f"{obj.object_id}:{','.join(overlap)}")
    checks["no_eligible_true_match_signatures"] = not eligible_hits
    if eligible_hits:
        blockers.append("sham_eligible_structural_true_match:" + "|".join(eligible_hits))

    answer_hits: list[str] = []
    single_token_answers = {
        tokenize(a)[0]
        for a in exclusion.hidden_answer_strings
        if len(tokenize(a)) == 1
    }
    for obj in sham_objects:
        content_l = obj.content_text.lower()
        content_tokens = set(tokenize(obj.content_text))
        for answer in exclusion.hidden_answer_strings:
            ans = answer.strip()
            if not ans:
                continue
            if ans.lower() in content_l:
                answer_hits.append(f"{obj.object_id}:substring:{ans}")
        for tok in sorted(content_tokens & single_token_answers):
            answer_hits.append(f"{obj.object_id}:token:{tok}")
    seen_ans: set[str] = set()
    answer_hits_unique = []
    for item in answer_hits:
        if item not in seen_ans:
            seen_ans.add(item)
            answer_hits_unique.append(item)
    checks["no_answer_substring_overlap"] = not answer_hits_unique
    if answer_hits_unique:
        blockers.append("sham_memory_answer_leakage:" + "|".join(answer_hits_unique))

    artifact_hits: list[str] = []
    for obj in sham_objects:
        bad = sorted(set(obj.solution_artifact_ids) & exclusion.forbidden_solution_artifact_ids)
        if bad:
            artifact_hits.append(f"{obj.object_id}:{','.join(bad)}")
    checks["no_solution_artifact_ids"] = not artifact_hits
    if artifact_hits:
        blockers.append("sham_solution_artifact_leakage:" + "|".join(artifact_hits))

    # --- budget / type matching ---
    learned_hist = _type_histogram(learned_objects)
    sham_hist = _type_histogram(sham_objects)
    checks["object_count_matched"] = len(sham_objects) == len(learned_objects)
    if not checks["object_count_matched"]:
        blockers.append(
            f"sham_object_count_mismatch:learned={len(learned_objects)} sham={len(sham_objects)}"
        )
    checks["type_histogram_matched"] = sham_hist == learned_hist
    if not checks["type_histogram_matched"]:
        blockers.append(
            f"sham_type_histogram_mismatch:learned={dict(learned_hist)} sham={dict(sham_hist)}"
        )

    learned_tokens = sum(obj.token_count for obj in learned_objects)
    sham_tokens = sum(obj.token_count for obj in sham_objects)
    rel_tol = float(policy["budget_matching"]["token_budget_rel_tolerance"])
    abs_tol = int(policy["budget_matching"]["token_budget_abs_tolerance"])
    token_delta = abs(sham_tokens - learned_tokens)
    allowed = max(abs_tol, int(rel_tol * max(learned_tokens, 1)))
    checks["token_budget_within_tolerance"] = token_delta <= allowed
    if not checks["token_budget_within_tolerance"]:
        blockers.append(
            f"sham_token_budget_mismatch:learned={learned_tokens} sham={sham_tokens} "
            f"delta={token_delta} allowed={allowed}"
        )
    elif token_delta > 0:
        limitations.append(
            f"token_budget_residual_delta={token_delta}; reported as sensitivity limitation"
        )

    if learned_objects and sham_objects and len(learned_objects) == len(sham_objects):
        recency_delta = sum(
            abs(a.recency_rank - b.recency_rank) for a, b in zip(learned_objects, sham_objects)
        ) / len(learned_objects)
        rec_tol = int(policy["budget_matching"]["recency_rank_abs_tolerance"])
        checks["recency_within_tolerance"] = recency_delta <= rec_tol
        if not checks["recency_within_tolerance"]:
            # Recency mismatch is a limitation/sensitivity variable, not always blocking.
            limitations.append(
                f"recency_rank_mean_abs_delta={recency_delta:.3f} exceeds tolerance={rec_tol}"
            )
            checks["recency_within_tolerance"] = False
    else:
        checks["recency_within_tolerance"] = False
        limitations.append("recency_check_skipped_due_to_count_mismatch")

    # --- family / content / gibberish ---
    learned_families = {obj.family_id for obj in learned_objects}
    family_hits = [obj.object_id for obj in sham_objects if obj.family_id in learned_families]
    checks["disjoint_family"] = not family_hits
    if family_hits:
        blockers.append("sham_family_not_disjoint:" + ",".join(family_hits))

    learned_content = {obj.content_hash for obj in learned_objects}
    content_hits = [obj.object_id for obj in sham_objects if obj.content_hash in learned_content]
    checks["no_copied_learned_content"] = not content_hits
    if content_hits:
        blockers.append("sham_copied_learned_content:" + ",".join(content_hits))

    min_tokens = int(policy["leakage_audit"]["min_content_token_length"])
    gibberish = [obj.object_id for obj in sham_objects if _is_gibberish(obj, min_tokens)]
    checks["no_gibberish_only_controls"] = not gibberish
    if gibberish:
        blockers.append("sham_gibberish_only_controls:" + ",".join(gibberish))

    lineage_ids = [obj.source_lineage_id for obj in sham_objects]
    checks["source_lineage_ids_present"] = all(bool(x) for x in lineage_ids)
    if not checks["source_lineage_ids_present"]:
        blockers.append("sham_missing_source_lineage_ids")

    if blockers:
        status = "FAIL"
    elif not sham_objects:
        status = "CANNOT_CHECK"
        blockers.append("empty_sham_state")
    else:
        status = "PASS"

    return ShamValidationReport(
        status=status,
        blockers=tuple(blockers),
        limitations=tuple(limitations),
        checks=checks,
        policy_hash=policy_hash,
        sham_state_hash=sham_state_hash,
    )


def freeze_policy_artifact(
    out_dir: Path,
    *,
    construction_seed: int = 20260812,
    notes: str | None = None,
) -> dict[str, Any]:
    """Write SHAM_POLICY.json + freeze receipt. Refuses overwrite."""

    out_dir = Path(out_dir).expanduser().resolve()
    policy_path = out_dir / "SHAM_POLICY.json"
    receipt_path = out_dir / "SHAM_POLICY_FREEZE_RECEIPT.json"
    if policy_path.exists() or receipt_path.exists():
        raise FileExistsError(
            f"refusing to overwrite frozen sham policy artifacts under {out_dir}"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    policy = build_policy_document(construction_seed=construction_seed, notes=notes)
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    file_hash = sha256_file(policy_path)
    try:
        policy_rel = str(policy_path.relative_to(ROOT))
    except ValueError:
        policy_rel = str(policy_path)
    receipt = {
        "schema_version": "paper5-sham-policy-freeze-receipt-v1",
        "policy_path": policy_rel,
        "policy_id": policy["policy_id"],
        "policy_canonical_sha256": policy["policy_canonical_sha256"],
        "policy_file_sha256": file_hash,
        "matcher_module": policy["matcher_module"],
        "matcher_module_sha256": sha256_file(ROOT / policy["matcher_module"]),
        "schema_path": "schemas/paper5-sham-policy-v1.schema.json",
        "schema_sha256": sha256_file(POLICY_SCHEMA_PATH),
        "preregistration_path": policy["preregistration_path"],
        "preregistration_sha256": sha256_file(ROOT / policy["preregistration_path"]),
        "claim_boundary": CLAIM_BOUNDARY,
        "grants_scientific_authority": False,
        "authorizes_confirmatory_execution": False,
        "evaluated_results_accessed": False,
        "confirmatory_four_arm_status": "UNAUTHORIZED_UNTIL_CAPABLE_MODEL_AND_FULL_PACKET_FREEZE",
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser("freeze-policy", help="freeze SHAM_POLICY.json without confirmatory binding")
    freeze.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_POLICY_PATH.parent,
        help="directory for SHAM_POLICY.json + freeze receipt",
    )
    freeze.add_argument("--construction-seed", type=int, default=20260812)
    freeze.add_argument("--notes", default=None)

    validate = sub.add_parser("validate-policy", help="validate a frozen sham policy document")
    validate.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)

    args = parser.parse_args(argv)
    if args.command == "freeze-policy":
        receipt = freeze_policy_artifact(
            args.out_dir,
            construction_seed=args.construction_seed,
            notes=args.notes,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    if args.command == "validate-policy":
        policy = load_policy(args.policy)
        print(args.policy)
        print(policy["policy_canonical_sha256"])
        return 0
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
