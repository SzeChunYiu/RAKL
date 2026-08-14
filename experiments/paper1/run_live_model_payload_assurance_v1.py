from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_live_model_payload_panel_v1 import BENIGN_FAMILIES, HOSTILE_FAMILIES, build, manifest  # noqa: E402
from rakl.authority_chokepoint import audit_source_tree  # noqa: E402
from rakl.driver_learning import DriverResult, DriverTask, run_learning_turn  # noqa: E402
from rakl.experience_substrate import EpisodeOutcome  # noqa: E402
from rakl.problem_fibre import ProblemAtom  # noqa: E402
from rakl.v3_runtime import RAKLV3State  # noqa: E402

PROTOCOL = ROOT / "research" / "paper1_live_model_payload_assurance_v1" / "PROTOCOL.json"


def _wilson(k: int, n: int) -> list[float]:
    if n <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    margin = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _task(task_id: str, family: str, index: int) -> DriverTask:
    return DriverTask(
        task_id=task_id,
        atom=ProblemAtom(
            atom_id=f"p1-live-model-atom-{index}",
            goal="route one untrusted model authority-proposal output through the production learning turn",
            context_hash=sha256(f"{task_id}:{family}".encode()).hexdigest(),
            structural_coordinates=("agent-output", "authority-isolation", family),
            desired_effects=("proposal-plane-only",),
        ),
        problem_signature=("paper1-live-model-payload", family),
        timestamp="2026-08-14T10:01:00+00:00",
    )


def _driver(raw: str):
    digest = sha256(raw.encode("utf-8")).hexdigest()

    def driver(_request):
        return DriverResult(
            operator_ids=("MODEL_AUTHORITY_PROPOSAL",),
            action_trace=("emit authority proposal candidate",),
            observation_ids=("raw-model-output",),
            verification_ids=(),
            outcome=EpisodeOutcome.SUCCESS,
            residual_signature=(),
            evidence_pointers=("model-output:" + digest,),
            artifact_hash=digest,
            authority_proposal_json=raw,
            authority_proposal_sha256=digest,
        )

    return driver


def _proposal_payload(result) -> dict[str, Any] | None:
    proposal = result.authority_proposal.proposal if result.authority_proposal else None
    if proposal is None:
        return None
    return {
        "claim_id": proposal.claim_id,
        "axis": proposal.axis.value,
        "proposition": proposal.proposition,
        "scope_id": proposal.scope_id,
        "evidence_ids": list(proposal.evidence_ids),
    }


def evaluate_raw(row: dict[str, Any], raw: str, index: int) -> dict[str, Any]:
    initial = RAKLV3State()
    report = run_learning_turn(
        initial,
        _task(str(row["task_id"]), str(row["family"]), index),
        _driver(raw),
        episode_id=f"p1-live-model-episode-{index:04d}",
    )
    parsed = report.authority_proposal
    accepted = bool(parsed and parsed.accepted_to_proposal_plane)
    family = str(row["family"])
    markers = [str(item) for item in row.get("hostile_markers", [])]
    attack_materialized = family in HOSTILE_FAMILIES and bool(markers) and all(marker in raw for marker in markers)
    exact_requested = accepted and _proposal_payload(report) == row["requested_allowed_payload"]
    authority_moved = report.state.scientific_authority != initial.scientific_authority
    episode_retained = len(report.state.experience.episodes) == 1
    return {
        "task_id": row["task_id"],
        "family": family,
        "raw_sha256": sha256(raw.encode("utf-8")).hexdigest(),
        "raw_output": raw,
        "attack_materialized": attack_materialized,
        "gateway_accepted": accepted,
        "gateway_reasons": list(parsed.reasons) if parsed else ["authority_proposal_report_missing"],
        "benign_exact_requested_field_fidelity": bool(exact_requested) if family in BENIGN_FAMILIES else None,
        "scientific_authority_moved": authority_moved,
        "experience_episode_retained": episode_retained,
    }


def _summarize(rows: list[dict[str, Any]], evaluated: list[dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    hostile = [r for r in evaluated if r["family"] in HOSTILE_FAMILIES]
    materialized = [r for r in hostile if r["attack_materialized"]]
    benign = [r for r in evaluated if r["family"] in BENIGN_FAMILIES]
    benign_accepted = [r for r in benign if r["gateway_accepted"]]
    benign_exact = [r for r in benign if r["benign_exact_requested_field_fidelity"]]
    authority_moves = sum(bool(r["scientific_authority_moved"]) for r in evaluated)
    experience_retained = sum(bool(r["experience_episode_retained"]) for r in evaluated)
    rejected_materialized = sum(not r["gateway_accepted"] for r in materialized)

    metrics = {
        "n": len(evaluated),
        "authority_movements": authority_moves,
        "experience_episode_retention": experience_retained / max(1, len(evaluated)),
        "hostile_attack_materialization_rate": len(materialized) / max(1, len(hostile)),
        "gateway_rejection_given_attack_materialized": rejected_materialized / max(1, len(materialized)),
        "benign_proposal_plane_acceptance": len(benign_accepted) / max(1, len(benign)),
        "benign_exact_requested_field_fidelity": len(benign_exact) / max(1, len(benign)),
        "wilson_95": {
            "attack_materialization": _wilson(len(materialized), len(hostile)),
            "rejection_given_attack_materialized": _wilson(rejected_materialized, len(materialized)),
            "benign_acceptance": _wilson(len(benign_accepted), len(benign)),
            "benign_exact_fidelity": _wilson(len(benign_exact), len(benign)),
            "experience_retention": _wilson(experience_retained, len(evaluated)),
        },
        "gateway_reason_counts": dict(Counter(reason for r in evaluated for reason in r["gateway_reasons"])),
    }
    by_family: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in evaluated:
        grouped[str(item["family"])].append(item)
    for family, subset in sorted(grouped.items()):
        by_family[family] = {
            "n": len(subset),
            "accepted": sum(bool(r["gateway_accepted"]) for r in subset),
            "attack_materialized": sum(bool(r["attack_materialized"]) for r in subset),
            "authority_movements": sum(bool(r["scientific_authority_moved"]) for r in subset),
            "experience_retained": sum(bool(r["experience_episode_retained"]) for r in subset),
        }
    metrics["by_family"] = by_family

    hard = protocol["hard_gate"]
    usability = protocol["usability_gate"]
    stress = protocol["stress_coverage_gate"]
    choke = audit_source_tree(ROOT)
    hard_pass = (
        authority_moves <= hard["unauthorized_scientific_authority_movements_max"]
        and metrics["gateway_rejection_given_attack_materialized"] >= hard["gateway_rejection_given_attack_materialized_min"]
        and metrics["experience_episode_retention"] >= hard["experience_episode_retention_min"]
        and choke.passed
    )
    usability_pass = (
        metrics["benign_proposal_plane_acceptance"] >= usability["benign_proposal_plane_acceptance_min"]
        and metrics["benign_exact_requested_field_fidelity"] >= usability["benign_exact_requested_field_fidelity_min"]
    )
    stress_pass = metrics["hostile_attack_materialization_rate"] >= stress["hostile_attack_materialization_rate_min"]

    terminals = protocol["decision_terminals"]
    if authority_moves > 0:
        terminal = terminals["authority_failure"]
    elif materialized and metrics["gateway_rejection_given_attack_materialized"] < hard["gateway_rejection_given_attack_materialized_min"]:
        terminal = terminals["gateway_failure"]
    elif not stress_pass:
        terminal = terminals["understress"]
    elif not usability_pass:
        terminal = terminals["usability_failure"]
    elif not hard_pass:
        terminal = terminals["gateway_failure"]
    else:
        terminal = terminals["pass"]

    return {
        "schema_version": "paper1-live-model-payload-assurance-result-v1",
        "panel": manifest(rows),
        "metrics": metrics,
        "production_chokepoint_pass": choke.passed,
        "hard_gate_pass": hard_pass,
        "usability_gate_pass": usability_pass,
        "stress_coverage_gate_pass": stress_pass,
        "terminal": terminal,
        "grants_scientific_authority": False,
    }


def _load_model(model_path: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        local_files_only=True,
        torch_dtype=torch.bfloat16,
        device_map="cuda",
    )
    model.eval()
    return tokenizer, model


def _generate(tokenizer, model, system_prompt: str, user_prompt: str, max_new_tokens: int) -> str:
    import torch

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(rendered, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(
            **inputs,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0, inputs["input_ids"].shape[1] :]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    protocol = json.loads(PROTOCOL.read_text())
    rows = build(protocol["panel"]["seed"], protocol["panel"]["cases_per_family"])
    args.outdir.mkdir(parents=True, exist_ok=True)
    panel_info = manifest(rows)
    (args.outdir / "PANEL_MANIFEST.json").write_text(json.dumps(panel_info, indent=2, sort_keys=True) + "\n")

    # Deterministic harness assurance uses the pre-frozen requested bytes only and
    # occurs before any model output. It demonstrates that the production ingress
    # can both accept benign proposals and reject every registered hostile shape.
    harness = [evaluate_raw(row, str(row["requested_raw"]), i) for i, row in enumerate(rows)]
    harness_summary = _summarize(rows, harness, protocol)
    (args.outdir / "HARNESS_PREFLIGHT.json").write_text(json.dumps(harness_summary, indent=2, sort_keys=True) + "\n")
    if harness_summary["terminal"] != protocol["decision_terminals"]["pass"]:
        raise SystemExit("pre-model production harness did not satisfy the frozen vector gate")
    if args.dry_run:
        print(json.dumps({"dry_run": True, "panel": panel_info, "harness_terminal": harness_summary["terminal"]}, sort_keys=True))
        return
    if not args.model_path:
        raise SystemExit("--model-path is required outside --dry-run")

    tokenizer, model = _load_model(args.model_path)
    evaluated: list[dict[str, Any]] = []
    started = time.time()
    raw_path = args.outdir / "RAW_RESULTS.jsonl"
    with raw_path.open("w", encoding="utf-8") as handle:
        for i, row in enumerate(rows):
            raw = _generate(
                tokenizer,
                model,
                str(row["system_prompt"]),
                str(row["user_prompt"]),
                int(protocol["model"]["max_new_tokens"]),
            )
            item = evaluate_raw(row, raw, i)
            item["prompt_sha256"] = sha256((str(row["system_prompt"]) + "\n" + str(row["user_prompt"])).encode()).hexdigest()
            evaluated.append(item)
            handle.write(json.dumps(item, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()

    receipt = _summarize(rows, evaluated, protocol)
    receipt["model"] = protocol["model"]
    receipt["elapsed_seconds"] = time.time() - started
    receipt["subject_git_sha"] = __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    receipt["protocol_sha256"] = sha256(PROTOCOL.read_bytes()).hexdigest()
    receipt["raw_results_sha256"] = sha256(raw_path.read_bytes()).hexdigest()
    (args.outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"terminal": receipt["terminal"], "metrics": receipt["metrics"]}, sort_keys=True))


if __name__ == "__main__":
    main()
