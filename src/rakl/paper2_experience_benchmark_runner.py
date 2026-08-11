"""Execute Paper-II ExperienceBenchmark RESET vs LEARNING under a frozen protocol.

Issue #138 §B2 runner. Bound to ``protocol_subject_hash`` from
``research/paper2_experience_benchmark_v1_1/`` (v1 preserved as negative history). Does **not** reuse V4.1/V4.2
pendulum scores or Paper-III (#217) paths.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping

from .experience_benchmark import (
    ExperienceBenchmarkArm,
    ExperienceBenchmarkPhase,
)
from .paper2_pendulum_microtrial import BackendGeneration
from .v3_authority import canonical_json_bytes

PACKET_REL_V1 = Path("research/paper2_experience_benchmark_v1")
PROTOCOL_SUBJECT_HASH_V1 = "1248dd101ff2cda94f2dfd91f990350dc46a59d169b4db36f2e64a596bf30b56"
PACKET_REL_V1_1 = Path("research/paper2_experience_benchmark_v1_1")
# Bound after v1.1 protocol freeze; submit scripts require exact match.
PROTOCOL_SUBJECT_HASH_V1_1 = "c7b1a04007e237f54acd2d0efd1c90870ad20718dec9392216ce49b169f7bedb"
# Default execution subject is the repaired verdict-enum packet (v1.1).
PACKET_REL = PACKET_REL_V1_1
PROTOCOL_SUBJECT_HASH = PROTOCOL_SUBJECT_HASH_V1_1
FORBIDDEN_JOBS = frozenset({3476520, 3476521, 3476524})
ALLOWED_VERDICTS = ("SUPPORT", "REFUTE", "CONTEXT_MISALIGNED", "CANNOT_CHECK")
VERDICT_ENUM_MARKER = "SUPPORT | REFUTE | CONTEXT_MISALIGNED | CANNOT_CHECK"
FORBIDDEN_VERDICT_SYNONYM_MARKER = "Do not emit REJECT, FAIL"
JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def require_verdict_enum_prompt(text: str, *, label: str) -> None:
    """Fail closed if the prompt interface omits the frozen verdict vocabulary."""
    for marker in (VERDICT_ENUM_MARKER, FORBIDDEN_VERDICT_SYNONYM_MARKER, "selected_evidence_ids"):
        if marker not in text:
            raise RuntimeError(f"experience prompt missing verdict-enum marker:{label}:{marker}")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(payload: bytes) -> str:
    return sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _state_hash(state: Mapping[str, Any]) -> str:
    return _sha256_bytes(canonical_json_bytes(dict(state)) + b"\n")


def _parse_model_json(raw_text: str) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    text = raw_text.strip()
    if not text:
        return None, ("empty_model_output",)
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = JSON_OBJECT_RE.search(text)
        if match is None:
            return None, ("unparseable_model_output",)
        try:
            obj = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None, ("unparseable_model_output",)
    if not isinstance(obj, dict):
        return None, ("model_output_not_object",)
    required = ("verdict", "selected_evidence_ids", "rejected_evidence_ids", "rationale_tags")
    missing = tuple(key for key in required if key not in obj)
    if missing:
        return None, ("missing_required_fields",) + missing
    return obj, ()


def _recall(predicted: list[str], required: list[str]) -> float:
    if not required:
        return 1.0
    predicted_set = set(predicted)
    hits = sum(1 for item in required if item in predicted_set)
    return hits / len(required)


def score_structured_answer(
    predicted: Mapping[str, Any] | None,
    sealed: Mapping[str, Any],
    evaluator: Mapping[str, Any],
    *,
    known_evidence_ids: set[str],
) -> tuple[float, bool, tuple[str, ...]]:
    scoring = evaluator["scoring"]
    if predicted is None:
        return 0.0, False, ("schema_violation",)

    failures: list[str] = []
    selected = predicted.get("selected_evidence_ids")
    rejected = predicted.get("rejected_evidence_ids")
    tags = predicted.get("rationale_tags")
    verdict = predicted.get("verdict")
    if not isinstance(selected, list) or not isinstance(rejected, list) or not isinstance(tags, list):
        return 0.0, False, ("schema_violation",)
    if any(not isinstance(item, str) for item in selected + rejected + tags):
        return 0.0, False, ("schema_violation",)
    if verdict not in ALLOWED_VERDICTS:
        return 0.0, False, ("schema_violation",)
    unknown = [item for item in selected + rejected if item not in known_evidence_ids]
    if unknown:
        failures.append("unknown_evidence_id")

    verdict_score = float(scoring["exact_verdict_match"]) if verdict == sealed["verdict"] else 0.0
    support_score = float(scoring["required_support_recall"]) * _recall(
        list(selected), list(sealed["selected_evidence_ids"])
    )
    reject_score = float(scoring["required_reject_recall"]) * _recall(
        list(rejected), list(sealed["rejected_evidence_ids"])
    )
    score = round(verdict_score + support_score + reject_score, 6)
    if verdict != sealed["verdict"]:
        failures.append("verdict_mismatch")
    if support_score < float(scoring["required_support_recall"]):
        failures.append("support_recall_incomplete")
    if reject_score < float(scoring["required_reject_recall"]):
        failures.append("reject_recall_incomplete")
    success = score >= float(scoring["success_threshold"]) and not failures
    if not success and not failures:
        failures.append("below_success_threshold")
    return score, success, tuple(failures)


def _render_state_for_prompt(state: Mapping[str, Any]) -> str:
    safe = {
        "state_kind": state.get("state_kind"),
        "episodes": state.get("episodes", []),
        "lessons": state.get("lessons", []),
        "failure_lattice_entries": state.get("failure_lattice_entries", []),
        "tools": state.get("tools", []),
    }
    return json.dumps(safe, indent=2, sort_keys=True)


def build_user_prompt(
    *,
    arm: ExperienceBenchmarkArm,
    task: Mapping[str, Any],
    state: Mapping[str, Any],
) -> str:
    evidence_lines = "\n".join(f"- {item['id']}: {item['text']}" for item in task["evidence"])
    parts = [
        f"Arm: {arm.value}",
        f"Phase: {task['phase']}",
        f"Task id: {task['task_id']}",
        f"Title: {task['title']}",
        "",
        "Task prompt:",
        str(task["prompt"]),
        "",
        "Sealed evidence (only these ids are valid):",
        evidence_lines,
        "",
        "Return exactly one JSON object with these exact keys and no leading spaces in key names:",
        "verdict, selected_evidence_ids, rejected_evidence_ids, rationale_tags.",
        f"verdict MUST be exactly one of: {VERDICT_ENUM_MARKER}",
        f"{FORBIDDEN_VERDICT_SYNONYM_MARKER}, ACCEPT, TRUE, FALSE, or any other verdict synonym.",
        "Then stop. Do not wrap the JSON in markdown fences.",
    ]
    if arm is ExperienceBenchmarkArm.LEARNING_ENABLED:
        parts = [
            "Registered external RAKL experience state (may be empty at S0):",
            _render_state_for_prompt(state),
            "",
            *parts,
        ]
    else:
        parts = [
            "RESET_BASELINE: ignore any prior task memory; start from registered empty S0.",
            "",
            *parts,
        ]
    prompt = "\n".join(parts)
    require_verdict_enum_prompt(prompt, label=f"user:{task['task_id']}")
    return prompt


def _encode_chat_prompt(tokenizer: object, system_prompt: str, user_prompt: str) -> object:
    return tokenizer.apply_chat_template(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
    )


def _generation_with_system(
    system_prompt: str,
    user_prompt: str,
    *,
    snapshot_path: Path,
    seed: int,
    max_output_tokens: int,
) -> BackendGeneration:
    """Local transformers generation with system+user chat roles."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    started = time.perf_counter()
    import resource
    import sys

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    torch.manual_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot_path,
        local_files_only=True,
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        snapshot_path,
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.float32,
    )
    model.eval()
    encoded = _encode_chat_prompt(tokenizer, system_prompt, user_prompt)
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_output_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = generated[0, encoded["input_ids"].shape[1] :]
    raw_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    after_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_multiplier = 1 if sys.platform == "darwin" else 1024
    return BackendGeneration(
        raw_text=raw_text,
        input_tokens=int(encoded["input_ids"].numel()),
        output_tokens=int(new_tokens.numel()),
        backend_version=f"transformers-{transformers.__version__}/torch-{torch.__version__}",
        wall_time_ms=round((time.perf_counter() - started) * 1000),
        process_high_water_rss_bytes_after_arm=int(max(before_rss, after_rss) * rss_multiplier),
    )


def _append_learning_state(
    state: dict[str, Any],
    *,
    task: Mapping[str, Any],
    predicted: Mapping[str, Any] | None,
    score: float,
    success: bool,
    failure_signature: tuple[str, ...],
    output_hash: str,
) -> dict[str, Any]:
    next_state = copy.deepcopy(state)
    next_state["state_kind"] = "LEARNING_EXTERNAL_RAKL_STATE"
    episode = {
        "task_id": task["task_id"],
        "phase": task["phase"],
        "stratum": task["stratum"],
        "title": task["title"],
        "success": success,
        "score": score,
        "failure_signature": list(failure_signature),
        "model_verdict": None if predicted is None else predicted.get("verdict"),
        "model_selected_evidence_ids": [] if predicted is None else list(predicted.get("selected_evidence_ids", [])),
        "model_rejected_evidence_ids": [] if predicted is None else list(predicted.get("rejected_evidence_ids", [])),
        "model_rationale_tags": [] if predicted is None else list(predicted.get("rationale_tags", [])),
        "output_hash": output_hash,
        # Explicitly exclude sealed_answer to avoid label leakage into transfer prompts.
        "sealed_answer_included": False,
    }
    next_state.setdefault("episodes", []).append(episode)
    if success:
        lesson = {
            "source_task_id": task["task_id"],
            "stratum": task["stratum"],
            "principle": (
                "Prefer evidence whose instrument authority and QoI match the claim; "
                "reject expired calibration, wrong instruments, and QoI mismatches."
            ),
            "observed_verdict": episode["model_verdict"],
        }
    else:
        lesson = {
            "source_task_id": task["task_id"],
            "stratum": task["stratum"],
            "principle": "Do not repeat the same failure signature on a structurally related claim.",
            "failure_signature": list(failure_signature),
        }
    next_state.setdefault("lessons", []).append(lesson)
    if failure_signature:
        next_state.setdefault("failure_lattice_entries", []).append(
            {
                "task_id": task["task_id"],
                "failure_signature": list(failure_signature),
            }
        )
    return next_state


def load_frozen_protocol(repo: Path, *, packet_rel: Path | None = None, protocol_subject_hash: str | None = None) -> dict[str, Any]:
    rel = packet_rel or PACKET_REL
    expected_hash = protocol_subject_hash or PROTOCOL_SUBJECT_HASH
    packet_dir = repo / rel
    freeze = _load_json(packet_dir / "PROTOCOL_FREEZE_PACKET.json")
    if freeze.get("protocol_subject_hash") != expected_hash:
        raise RuntimeError("protocol_subject_hash mismatch versus authorized runner binding")
    if freeze.get("scientific_claim_status") != "NO_EMPIRICAL_RESULT":
        raise RuntimeError("freeze packet is not in pre-execution scientific status")
    if freeze.get("v4_1_pendulum_compatibility", {}).get("score_reuse_allowed") is not False:
        raise RuntimeError("V4.1 score reuse must remain forbidden")
    forbidden = set(freeze.get("v4_1_pendulum_compatibility", {}).get("jobs_explicitly_not_experience_evidence", []))
    if not FORBIDDEN_JOBS.issubset(forbidden):
        raise RuntimeError("freeze packet missing V4.1 forbidden job list")
    return {
        "packet_dir": packet_dir,
        "freeze": freeze,
        "model": _load_json(packet_dir / "protocol" / "MODEL_CONFIG.json"),
        "ceiling": _load_json(packet_dir / "protocol" / "RESOURCE_CEILING.json"),
        "evaluator": _load_json(packet_dir / "protocol" / "EVALUATOR_PROTOCOL.json"),
        "tool_policy": _load_json(packet_dir / "protocol" / "TOOL_POLICY.json"),
        "output_schema": _load_json(packet_dir / "protocol" / "OUTPUT_SCHEMA.json"),
        "s0_path": packet_dir / "protocol" / "INITIAL_STATE_S0.json",
        "s0": _load_json(packet_dir / "protocol" / "INITIAL_STATE_S0.json"),
        "system_prompt": (packet_dir / "protocol" / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8").rstrip("\n"),
        "tasks": {
            task_id: _load_json(packet_dir / "tasks" / f"{task_id}.json")
            for task_id in list(freeze["development_task_ids"]) + list(freeze["transfer_task_ids"])
        },
    }


def execute_experience_benchmark(
    repo: Path,
    output_dir: Path,
    *,
    expected_repo_sha: str,
    scheduler_job_id: str,
    created_at_utc: str | None = None,
    backend: Callable[..., BackendGeneration] | None = None,
    packet_rel: Path | None = None,
    protocol_subject_hash: str | None = None,
) -> dict[str, Any]:
    if not scheduler_job_id.isdigit():
        raise RuntimeError("numeric SLURM job id required")
    if int(scheduler_job_id) in FORBIDDEN_JOBS:
        raise RuntimeError("refusing to bind experience runs to forbidden V4.1 job ids")
    if output_dir.exists():
        raise RuntimeError(f"output directory already exists: {output_dir}")

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    head = _git("rev-parse", "HEAD")
    origin_main = _git("rev-parse", "refs/remotes/origin/main")
    dirty = _git("status", "--porcelain", "--untracked-files=all")
    if head != expected_repo_sha or origin_main != expected_repo_sha:
        raise RuntimeError("checkout is not exact clean origin/main subject")
    if dirty:
        raise RuntimeError("checkout is dirty")

    bound_packet_rel = packet_rel or PACKET_REL
    bound_hash = protocol_subject_hash or PROTOCOL_SUBJECT_HASH
    if bound_hash.startswith("PENDING_"):
        raise RuntimeError("protocol_subject_hash is not frozen yet")
    require_verdict_enum_prompt(
        (repo / bound_packet_rel / "protocol" / "SYSTEM_PROMPT.txt").read_text(encoding="utf-8"),
        label="system_prompt",
    )
    bundle = load_frozen_protocol(repo, packet_rel=bound_packet_rel, protocol_subject_hash=bound_hash)
    freeze = bundle["freeze"]
    model_cfg = bundle["model"]
    ceiling = bundle["ceiling"]
    evaluator = bundle["evaluator"]
    s0 = bundle["s0"]
    initial_state_hash = freeze["initial_state_hash"]
    if _sha256_file(bundle["s0_path"]) != initial_state_hash:
        raise RuntimeError("S0 file hash drift versus freeze packet")
    if model_cfg["system_prompt"] != bundle["system_prompt"]:
        raise RuntimeError("system prompt drift")
    snapshot = Path(str(model_cfg["snapshot_path"]))
    if not snapshot.is_dir():
        raise RuntimeError(f"model snapshot missing: {snapshot}")

    host = socket.gethostname()
    if host.startswith("login"):
        raise RuntimeError("execution forbidden on login host")

    created = created_at_utc or _utc_now()
    output_dir.mkdir(parents=True, exist_ok=False)
    outputs_dir = output_dir / "outputs"
    states_dir = output_dir / "states"
    outputs_dir.mkdir()
    states_dir.mkdir()
    (states_dir / "S0.json").write_bytes(bundle["s0_path"].read_bytes())

    generator = backend or _generation_with_system
    runs: list[dict[str, Any]] = []
    learned_state = copy.deepcopy(s0)
    learned_hash = initial_state_hash

    def run_one(
        *,
        arm: ExperienceBenchmarkArm,
        task_id: str,
        state: dict[str, Any],
        state_before_hash: str,
        mutate_learning: bool,
    ) -> tuple[dict[str, Any], dict[str, Any], str]:
        task = bundle["tasks"][task_id]
        phase = ExperienceBenchmarkPhase(task["phase"])
        user_prompt = build_user_prompt(arm=arm, task=task, state=state)
        if backend is None:
            generation = generator(
                bundle["system_prompt"],
                user_prompt,
                snapshot_path=snapshot,
                seed=int(model_cfg["seed"]),
                max_output_tokens=int(model_cfg["max_output_tokens"]),
            )
        else:
            # Test backend receives a single combined prompt string.
            generation = generator(
                bundle["system_prompt"] + "\n\n" + user_prompt,
                snapshot_path=snapshot,
                seed=int(model_cfg["seed"]),
                max_output_tokens=int(model_cfg["max_output_tokens"]),
            )
        if generation.input_tokens > int(ceiling["max_model_input_tokens"]):
            raise RuntimeError(f"input token ceiling exceeded:{arm.value}:{task_id}")
        if generation.output_tokens > int(ceiling["max_model_output_tokens"]):
            raise RuntimeError(f"output token ceiling exceeded:{arm.value}:{task_id}")
        if generation.wall_time_ms > int(ceiling["max_wall_time_ms"]):
            raise RuntimeError(f"wall time ceiling exceeded:{arm.value}:{task_id}")

        executed_at = _utc_now()
        predicted, parse_failures = _parse_model_json(generation.raw_text)
        known_ids = {item["id"] for item in task["evidence"]}
        score, success, score_failures = score_structured_answer(
            predicted,
            task["sealed_answer"],
            evaluator,
            known_evidence_ids=known_ids,
        )
        failure_signature = parse_failures + score_failures
        raw_payload = {
            "arm": arm.value,
            "task_id": task_id,
            "phase": phase.value,
            "raw_text": generation.raw_text,
            "parsed": predicted,
            "score": score,
            "success": success,
            "failure_signature": list(failure_signature),
            "resource_usage": {
                "model_input_tokens": generation.input_tokens,
                "model_output_tokens": generation.output_tokens,
                "preprocessing_model_tokens": 0,
                "preprocessing_tool_calls": 0,
                "external_retrieval_calls": 0,
                "wall_time_ms": generation.wall_time_ms,
            },
            "backend_version": generation.backend_version,
            "executed_at": executed_at,
        }
        raw_bytes = canonical_json_bytes(raw_payload) + b"\n"
        output_hash = _sha256_bytes(raw_bytes)
        run_id = f"{arm.value}:{task_id}:{scheduler_job_id}"
        output_artifact_id = f"output:{run_id}:{output_hash}"
        (outputs_dir / f"{arm.value}_{task_id}.json").write_bytes(raw_bytes)

        if arm is ExperienceBenchmarkArm.RESET_BASELINE:
            state_after = copy.deepcopy(s0)
            state_after_hash = initial_state_hash
        elif mutate_learning:
            state_after = _append_learning_state(
                state,
                task=task,
                predicted=predicted,
                score=score,
                success=success,
                failure_signature=failure_signature,
                output_hash=output_hash,
            )
            state_after_hash = _state_hash(state_after)
            _write_json(states_dir / f"{arm.value}_{task_id}_after.json", state_after)
        else:
            # Fresh-transfer LEARNING: each Ti starts from frozen Sn; after-hash is
            # a non-retained probe copy and must not feed the next transfer.
            state_after = _append_learning_state(
                state,
                task=task,
                predicted=predicted,
                score=score,
                success=success,
                failure_signature=failure_signature,
                output_hash=output_hash,
            )
            state_after_hash = _state_hash(state_after)
            _write_json(states_dir / f"{arm.value}_{task_id}_probe_after.json", state_after)

        run_record = {
            "run_id": run_id,
            "task_id": task_id,
            "arm": arm.value,
            "phase": phase.value,
            "state_before_hash": state_before_hash,
            "state_after_hash": state_after_hash,
            "success": success,
            "score": score,
            "failure_signature": list(failure_signature),
            "resource_usage": raw_payload["resource_usage"],
            "output_hash": output_hash,
            "output_artifact_id": output_artifact_id,
            "executed_at": executed_at,
        }
        return run_record, state_after, state_after_hash

    # RESET development + transfer: every task from S0, remain S0.
    for task_id in list(freeze["development_task_ids"]) + list(freeze["transfer_task_ids"]):
        run_record, _, _ = run_one(
            arm=ExperienceBenchmarkArm.RESET_BASELINE,
            task_id=task_id,
            state=copy.deepcopy(s0),
            state_before_hash=initial_state_hash,
            mutate_learning=False,
        )
        runs.append(run_record)

    # LEARNING development: S0 -> S1 -> ... -> Sn
    for task_id in freeze["development_task_ids"]:
        run_record, learned_state, learned_hash = run_one(
            arm=ExperienceBenchmarkArm.LEARNING_ENABLED,
            task_id=task_id,
            state=learned_state,
            state_before_hash=learned_hash,
            mutate_learning=True,
        )
        runs.append(run_record)

    sn_hash = learned_hash
    sn_state = copy.deepcopy(learned_state)
    _write_json(states_dir / "Sn.json", sn_state)
    (states_dir / "Sn.hash").write_text(sn_hash + "\n", encoding="utf-8")

    # LEARNING fresh transfer: each Ti independently from frozen Sn.
    for task_id in freeze["transfer_task_ids"]:
        run_record, _, _ = run_one(
            arm=ExperienceBenchmarkArm.LEARNING_ENABLED,
            task_id=task_id,
            state=copy.deepcopy(sn_state),
            state_before_hash=sn_hash,
            mutate_learning=False,
        )
        runs.append(run_record)

    runs_path = output_dir / "runs.jsonl"
    with runs_path.open("w", encoding="utf-8") as handle:
        for run in runs:
            handle.write(json.dumps(run, sort_keys=True) + "\n")

    manifest = {
        "schema_version": "paper2-experience-benchmark-run-manifest-v1",
        "created_at_utc": created,
        "issue": 138,
        "section": "B2",
        "benchmark_id": freeze["benchmark_id"],
        "protocol_subject_hash": bound_hash,
        "freeze_packet_sha256": _sha256_file(bundle["packet_dir"] / "PROTOCOL_FREEZE_PACKET.json"),
        "expected_repo_sha": expected_repo_sha,
        "scheduler_job_id": scheduler_job_id,
        "execution_host": host,
        "initial_state_hash": initial_state_hash,
        "learned_state_after_development_hash": sn_hash,
        "arms": ["RESET_BASELINE", "LEARNING_ENABLED"],
        "development_task_ids": freeze["development_task_ids"],
        "transfer_task_ids": freeze["transfer_task_ids"],
        "run_count": len(runs),
        "runs_path": "runs.jsonl",
        "v4_1_score_reuse_allowed": False,
        "paper3_issue_217_path": False,
        "claim_boundary": (
            "Native ExperienceBenchmark execution artifacts only. "
            "Not manuscript authority until validate_experience_benchmark + analysis."
        ),
        "scientific_claim_status": "RAW_RUNS_AWAITING_VALIDATION",
    }
    _write_json(output_dir / "run_manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-repo-sha", required=True)
    parser.add_argument("--scheduler-job-id", required=True)
    parser.add_argument("--created-at-utc", default=None)
    parser.add_argument("--packet-rel", type=Path, default=None)
    parser.add_argument("--protocol-subject-hash", default=None)
    args = parser.parse_args(argv)
    manifest = execute_experience_benchmark(
        args.repo.resolve(),
        args.output_dir,
        expected_repo_sha=args.expected_repo_sha,
        scheduler_job_id=args.scheduler_job_id,
        created_at_utc=args.created_at_utc,
        packet_rel=args.packet_rel,
        protocol_subject_hash=args.protocol_subject_hash,
    )
    print(json.dumps({"verdict": "EXECUTED", "learned_state_after_development_hash": manifest["learned_state_after_development_hash"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
