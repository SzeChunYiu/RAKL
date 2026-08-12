"""Paper 5 fresh replay twin generator (#446 lane 7).

Generates untouched structural twins from registered failure families for a
prospective causal bridge:

    naturalistic history -> mechanism hypothesis -> fresh controlled causal test

This module freezes generator identity and emits deterministic known-answer
twins. It does **not** authorize confirmatory model execution, access outcomes,
or grant scientific authority. Historical RAKL_math cases motivate families but
are never copied into solver-facing text.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = ROOT / "research" / "paper5_fresh_twin_v1" / "FAILURE_FAMILY_REGISTRY.json"
TASK_SCHEMA_PATH = ROOT / "schemas" / "paper5-fresh-twin-v1.schema.json"
FAMILY_SCHEMA_PATH = ROOT / "schemas" / "paper5-fresh-twin-family-v1.schema.json"

GENERATOR_VERSION = "paper5-fresh-twin-generator-v1"
PROTOCOL_VERSION = "paper5-fresh-twin-protocol-v1"
SCHEMA_VERSION = "paper5-fresh-twin-v1"

REGISTERED_ACTIONS = (
    "ACCEPT_VALID_GLUE",
    "REJECT_FALSE_TRANSFER",
    "ABSTAIN_CANNOT_CHECK",
)

TwinKind = Literal["VALID", "INVALID"]
CorrectAction = Literal["ACCEPT_VALID_GLUE", "REJECT_FALSE_TRANSFER", "ABSTAIN_CANNOT_CHECK"]

CLAIM_BOUNDARY = (
    "Fresh twin generator + deterministic verifier only. Does not execute causal "
    "arms, authorize confirmatory runs, or convert development twins into "
    "framework-promotion evidence."
)

ANSWER_FIELD_NAMES = frozenset(
    {
        "correct_action",
        "hidden_gold_hash",
        "structural_signature_id",
        "family_id_internal",
        "sealed_answer",
        "gold_answer",
        "target_answer",
    }
)


@dataclass(frozen=True)
class LeakageFinding:
    task_id: str
    field_path: str
    forbidden_token: str


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(path: Path) -> Draft202012Validator:
    schema = load_json(path)
    return Draft202012Validator(schema)


def load_failure_family_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY_PATH
    registry = load_json(registry_path)
    family_validator = _validator(FAMILY_SCHEMA_PATH)
    for family in registry["families"]:
        family_validator.validate(family)
    return registry


def task_id_for(*, family_id: str, seed: int, twin_kind: TwinKind) -> str:
    digest = sha256_hex(f"{family_id}:{seed}:{twin_kind}".encode("utf-8"))
    return f"FT-{digest[:16]}"


def _rng(seed: int) -> int:
    state = seed & 0xFFFFFFFF
    state = (1103515245 * state + 12345) & 0x7FFFFFFF
    return state


def _world_quantifier_scope(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    base = 3 + (_rng(seed) % 5)
    samples = [base + i for i in range(4)]
    local_max = max(samples)
    if twin_kind == "VALID":
        global_bound = local_max
        correct: CorrectAction = "ACCEPT_VALID_GLUE"
    else:
        global_bound = local_max - 1
        correct = "REJECT_FALSE_TRANSFER"
    local = {
        "sample_indices": list(range(len(samples))),
        "observed_values": samples,
        "local_bound": local_max,
        "local_certificate": "each sampled slot is at or below the local bound",
    }
    claim = {
        "aggregate_kind": "max-over-samples",
        "claimed_bound": global_bound,
        "claim_text": "the aggregate over all sampled slots is at or below the claimed bound",
    }
    return local, claim, correct


def _world_pointwise_uniform(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    offset = 1 + (_rng(seed + 1) % 4)
    per_index = [offset + (i % 2) for i in range(6)]
    pointwise_max = max(per_index)
    if twin_kind == "VALID":
        envelope = pointwise_max
        correct: CorrectAction = "ACCEPT_VALID_GLUE"
    else:
        envelope = pointwise_max - 1
        correct = "REJECT_FALSE_TRANSFER"
    local = {
        "index_values": per_index,
        "per_slot_ceiling": pointwise_max,
        "slot_certificate": "every listed index satisfies its slot ceiling",
    }
    claim = {
        "family_kind": "shared-envelope",
        "claimed_envelope": envelope,
        "claim_text": "one envelope bound covers every listed index simultaneously",
    }
    return local, claim, correct


def _world_norm_conorm(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    norm_budget = 5 + (_rng(seed + 2) % 3)
    consumer_limit = norm_budget if twin_kind == "VALID" else norm_budget + 2
    correct: CorrectAction = "ACCEPT_VALID_GLUE" if twin_kind == "VALID" else "REJECT_FALSE_TRANSFER"
    local = {
        "artifact_kind": "forward-bound",
        "bound_value": norm_budget,
        "certificate_text": "forward-bound certificate within registered budget",
    }
    claim = {
        "sink_kind": "reverse-bound",
        "required_limit": consumer_limit,
        "claim_text": "reverse-bound sink accepts the forwarded certificate without repair",
    }
    return local, claim, correct


def _world_producer_consumer(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    ambient = 10 + (_rng(seed + 3) % 4)
    restricted = ambient if twin_kind == "VALID" else ambient - 2
    correct: CorrectAction = "ACCEPT_VALID_GLUE" if twin_kind == "VALID" else "REJECT_FALSE_TRANSFER"
    local = {
        "source_domain": "wide",
        "observed_magnitude": ambient,
        "source_certificate": "observation within wide source range",
    }
    claim = {
        "sink_domain": "narrow",
        "sink_capacity": restricted,
        "claim_text": "narrow sink can absorb source output without re-embedding",
    }
    return local, claim, correct


def _world_same_root(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    root = f"root-{_rng(seed + 4) % 1000}"
    duplicates = [
        {"evidence_id": "E1", "root_id": root, "value": 7},
        {"evidence_id": "E2", "root_id": root, "value": 7},
    ]
    independent = {"evidence_id": "E3", "root_id": f"root-{_rng(seed + 5) % 1000}", "value": 7}
    if twin_kind == "VALID":
        support = duplicates + [independent]
        required_roots = 2
        correct: CorrectAction = "ACCEPT_VALID_GLUE"
    else:
        support = duplicates
        required_roots = 2
        correct = "REJECT_FALSE_TRANSFER"
    local = {
        "support_items": support,
        "independent_root_requirement": required_roots,
        "local_certificate": "support items listed with lineage ids",
    }
    claim = {
        "target_strength": "global",
        "claim_text": "listed support meets the independent-root requirement for a global claim",
    }
    return local, claim, correct


def _world_local_consumer(seed: int, twin_kind: TwinKind) -> tuple[dict[str, Any], dict[str, Any], CorrectAction]:
    patch_value = 4 + (_rng(seed + 6) % 3)
    if twin_kind == "VALID":
        sink_interface = "type-A"
        patch_interface = "type-A"
        correct: CorrectAction = "ACCEPT_VALID_GLUE"
    else:
        sink_interface = "type-B"
        patch_interface = "type-A"
        correct = "REJECT_FALSE_TRANSFER"
    local = {
        "patch_scope": "local",
        "patch_interface": patch_interface,
        "patch_certificate": f"local patch valid within {patch_interface} interface",
        "patch_value": patch_value,
    }
    claim = {
        "downstream_sink": sink_interface,
        "claim_text": "local patch may be glued directly into downstream sink unchanged",
    }
    return local, claim, correct


_WORLD_BUILDERS = {
    "QUANTIFIER_SCOPE_LOCAL_GLOBAL": _world_quantifier_scope,
    "POINTWISE_UNIFORM_FAMILY": _world_pointwise_uniform,
    "NORM_CONORM_MISMATCH": _world_norm_conorm,
    "PRODUCER_CONSUMER_SCOPE": _world_producer_consumer,
    "SAME_ROOT_CORROBORATION": _world_same_root,
    "LOCAL_CORRECT_WRONG_CONSUMER": _world_local_consumer,
}


def _prompt_text(*, local: Mapping[str, Any], claim: Mapping[str, Any]) -> str:
    return (
        "Structural gluing decision.\n"
        "Local certificate:\n"
        f"{json.dumps(local, sort_keys=True)}\n"
        "Proposed global/downstream claim:\n"
        f"{json.dumps(claim, sort_keys=True)}\n"
        "Choose one registered action."
    )


def generate_twin_task(
    *,
    family_id: str,
    seed: int,
    twin_kind: TwinKind,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_failure_family_registry()
    family = next(f for f in registry["families"] if f["family_id"] == family_id)
    builder = _WORLD_BUILDERS[family_id]
    local, claim, correct = builder(seed, twin_kind)
    task_id = task_id_for(family_id=family_id, seed=seed, twin_kind=twin_kind)
    hidden_gold = {
        "correct_action": correct,
        "local": local,
        "claim": claim,
        "family_id": family_id,
        "seed": seed,
        "twin_kind": twin_kind,
    }
    hidden_hash = sha256_hex(canonical_json_bytes(hidden_gold))
    solver_bundle = {
        "task_id": task_id,
        "prompt": _prompt_text(local=local, claim=claim),
        "local_evidence": local,
        "global_claim": claim,
        "registered_actions": list(REGISTERED_ACTIONS),
    }
    task = {
        "schema_version": SCHEMA_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "generator_version": GENERATOR_VERSION,
        "task_id": task_id,
        "twin_kind": twin_kind,
        "family_id_internal": family_id,
        "seed": seed,
        "solver_bundle": solver_bundle,
        "evaluator_bundle": {
            "task_id": task_id,
            "correct_action": correct,
            "deterministic_verifier": f"{GENERATOR_VERSION}:{family_id}",
            "structural_signature_id": family_id,
            "hidden_gold_hash": hidden_hash,
        },
        "grants_scientific_authority": False,
        "outcome_access_status": "NO_OUTCOME_ACCESSED",
    }
    _validator(TASK_SCHEMA_PATH).validate(task)
    return task


def generate_dev_universe(
    *,
    seeds_per_family: int = 2,
    registry: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    registry = registry or load_failure_family_registry()
    tasks: list[dict[str, Any]] = []
    for family in registry["families"]:
        family_id = family["family_id"]
        for seed in range(seeds_per_family):
            for twin_kind in ("VALID", "INVALID"):
                tasks.append(
                    generate_twin_task(
                        family_id=family_id,
                        seed=seed,
                        twin_kind=twin_kind,  # type: ignore[arg-type]
                        registry=registry,
                    )
                )
    return tasks


def split_solver_evaluator(task: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    return dict(task["solver_bundle"]), dict(task["evaluator_bundle"])


def verify_action(
    submitted_action: str,
    evaluator_bundle: Mapping[str, Any],
) -> dict[str, Any]:
    correct = evaluator_bundle["correct_action"]
    return {
        "task_id": evaluator_bundle["task_id"],
        "submitted_action": submitted_action,
        "correct_action": correct,
        "is_correct": submitted_action == correct,
        "grants_scientific_authority": False,
    }


def _collect_solver_text(task: Mapping[str, Any]) -> str:
    solver = task["solver_bundle"]
    return json.dumps(solver, sort_keys=True)


def sweep_leakage(
    tasks: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_failure_family_registry()
    forbidden_by_family = {f["family_id"]: f["forbidden_solver_tokens"] for f in registry["families"]}
    findings: list[LeakageFinding] = []
    for task in tasks:
        family_id = task["family_id_internal"]
        text = _collect_solver_text(task)
        for token in forbidden_by_family[family_id]:
            if token.lower() in text.lower():
                findings.append(
                    LeakageFinding(task_id=task["task_id"], field_path="solver_bundle", forbidden_token=token)
                )
        for field in ANSWER_FIELD_NAMES:
            if field in text:
                findings.append(
                    LeakageFinding(task_id=task["task_id"], field_path="solver_bundle", forbidden_token=field)
                )
        if re.search(r"\bNS-[A-Za-z0-9]", text):
            findings.append(
                LeakageFinding(task_id=task["task_id"], field_path="solver_bundle", forbidden_token="NS-*")
            )
    return {
        "task_count": len(tasks),
        "finding_count": len(findings),
        "passed": len(findings) == 0,
        "findings": [finding.__dict__ for finding in findings],
        "grants_scientific_authority": False,
    }


def build_freeze_stub(
    *,
    registry_path: Path | None = None,
    seeds_per_family: int = 2,
) -> dict[str, Any]:
    registry_path = registry_path or DEFAULT_REGISTRY_PATH
    registry = load_failure_family_registry(registry_path)
    tasks = generate_dev_universe(seeds_per_family=seeds_per_family, registry=registry)
    leakage = sweep_leakage(tasks, registry=registry)
    manifest_bytes = canonical_json_bytes([task["task_id"] for task in tasks])
    return {
        "schema_version": "paper5-fresh-twin-freeze-stub-v1",
        "protocol_version": PROTOCOL_VERSION,
        "generator_version": GENERATOR_VERSION,
        "issue": 446,
        "status": "DESIGN_FROZEN_NO_OUTCOME_ACCESSED",
        "registry_path": str(registry_path.relative_to(ROOT)),
        "registry_sha256": sha256_hex(registry_path.read_bytes()),
        "task_manifest_sha256": sha256_hex(manifest_bytes),
        "family_count": len(registry["families"]),
        "task_count": len(tasks),
        "seeds_per_family": seeds_per_family,
        "leakage_sweep_passed": leakage["passed"],
        "registered_causal_arms": [
            "MODEL_ONLY_RESET",
            "GENERIC_RETRIEVAL",
            "CURRENT_RAKL_NO_CROSS_CYCLE_MEMORY",
            "CURRENT_RAKL_FULL_EXPERIENCE",
            "SHAM_MEMORY_OPTIONAL",
        ],
        "primary_outcomes": [
            "correct_next_action",
            "invalid_glue_or_false_transfer",
            "valid_transfer_retention",
            "residual_contraction",
            "CANNOT_CHECK_correctness",
            "cost_to_first_valid_scoped_result",
        ],
        "grants_scientific_authority": False,
        "outcome_access_status": "NO_OUTCOME_ACCESSED",
        "claim_boundary": CLAIM_BOUNDARY,
        "next_phase_blockers": [
            "confirmatory packet hash not frozen",
            "framework/model subject not bound",
            "causal arms not executed",
            "capability gate from #443 may block four-arm bridge",
        ],
    }
