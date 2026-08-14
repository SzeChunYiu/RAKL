from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
import time
from typing import Any, Iterable

from experiments.paper3.build_capability_stage4_panel_v1 import build, serialize

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "research" / "empirical_10_of_10_v1" / "CAPABILITY_QUALIFICATION"
FREEZE = PACKET / "STAGE3_5_FREEZE_V1.json"
MANIFEST = PACKET / "FRESH_TASK_MANIFEST_V1.json"
SYSTEM = PACKET / "protocol_stage2" / "SYSTEM_PROMPT.txt"
RUNNER = PACKET / "protocol_stage2" / "RUNNER_INSTRUCTION_BLOCK.txt"
EXPECTED_KEYS = {"verdict", "selected_evidence_ids", "rejected_evidence_ids", "rationale_tags"}
VERDICTS = {"SUPPORT", "REFUTE", "CONTEXT_MISALIGNED", "CANNOT_CHECK"}


def _wilson(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    margin = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _materialize_and_verify_panel() -> tuple[list[dict], dict, dict]:
    freeze = json.loads(FREEZE.read_text())
    manifest = json.loads(MANIFEST.read_text())
    tasks = build()
    body = serialize(tasks)
    digest = hashlib.sha256(body).hexdigest()
    if digest != manifest["panel_sha256"]:
        raise RuntimeError(f"panel_sha256_mismatch:{digest}")
    if len(tasks) != freeze["fresh_panel"]["n_total"] or len(tasks) != manifest["n"]:
        raise RuntimeError("fresh_panel_count_mismatch")
    if len({task["task_id"] for task in tasks}) != len(tasks):
        raise RuntimeError("fresh_panel_duplicate_task_id")
    forbidden = ("SUPPORT", "REFUTE", "CONTEXT_MISALIGNED", "CANNOT_CHECK")
    if any(token in task["prompt"] for task in tasks for token in forbidden):
        raise RuntimeError("fresh_panel_gold_verdict_leak")
    return tasks, freeze, manifest


def _parse(raw: str) -> tuple[dict | None, list[str]]:
    reasons: list[str] = []
    try:
        value = json.loads(raw.strip())
    except json.JSONDecodeError:
        return None, ["invalid_json"]
    if not isinstance(value, dict):
        return None, ["root_not_object"]
    if set(value) != EXPECTED_KEYS:
        reasons.append("wrong_key_set")
    if value.get("verdict") not in VERDICTS:
        reasons.append("invalid_verdict")
    for key in ("selected_evidence_ids", "rejected_evidence_ids", "rationale_tags"):
        if not isinstance(value.get(key), list) or any(not isinstance(x, str) for x in value.get(key, [])):
            reasons.append(f"invalid_array:{key}")
    if reasons:
        return None, reasons
    selected = value["selected_evidence_ids"]
    rejected = value["rejected_evidence_ids"]
    if len(set(selected)) != len(selected) or len(set(rejected)) != len(rejected):
        return None, ["duplicate_evidence_ids"]
    if set(selected) & set(rejected):
        return None, ["selected_rejected_overlap"]
    return value, []


def _evidence_ids(prompt: str) -> set[str]:
    ids = set()
    for line in prompt.splitlines():
        if line.startswith("- E-") and " | " in line:
            ids.add(line[2:].split(" | ", 1)[0])
    return ids


def _score(tasks: list[dict], records: list[dict], freeze: dict) -> dict:
    by_task = {record["task_id"]: record for record in records}
    parsed_n = exact_n = 0
    support_num = support_den = reject_num = reject_den = 0
    cc_tp = cc_gold = cc_pred = 0
    context_errors = context_total = 0
    family_exact: dict[str, list[int]] = defaultdict(list)

    for task in tasks:
        record = by_task[task["task_id"]]
        parsed = record.get("parsed")
        if parsed is not None:
            parsed_n += 1
        gold = task["gold"]
        exact = False
        if parsed is not None:
            supplied = _evidence_ids(task["prompt"])
            if set(parsed["selected_evidence_ids"]) | set(parsed["rejected_evidence_ids"]) != supplied:
                record.setdefault("parse_reasons", []).append("evidence_partition_not_total")
            else:
                exact = (
                    parsed["verdict"] == gold["verdict"]
                    and set(parsed["selected_evidence_ids"]) == set(gold["selected_evidence_ids"])
                    and set(parsed["rejected_evidence_ids"]) == set(gold["rejected_evidence_ids"])
                )
                pred_sel = set(parsed["selected_evidence_ids"])
                pred_rej = set(parsed["rejected_evidence_ids"])
                gold_sel = set(gold["selected_evidence_ids"])
                gold_rej = set(gold["rejected_evidence_ids"])
                support_num += len(pred_sel & gold_sel)
                support_den += len(gold_sel)
                reject_num += len(pred_rej & gold_rej)
                reject_den += len(gold_rej)
                if gold["verdict"] == "CANNOT_CHECK":
                    cc_gold += 1
                    cc_tp += parsed["verdict"] == "CANNOT_CHECK"
                if parsed["verdict"] == "CANNOT_CHECK":
                    cc_pred += 1
                if task["family"] == "CONTEXT_QOI_NEAR_MISS":
                    context_total += 1
                    context_errors += parsed["verdict"] != "CONTEXT_MISALIGNED"
        exact_n += exact
        family_exact[task["family"]].append(int(exact))
        record["joint_exact"] = exact

    n = len(tasks)
    metrics = {
        "n": n,
        "parse_validity": parsed_n / n,
        "parse_validity_ci95": _wilson(parsed_n, n),
        "exact_joint_verdict_and_binding": exact_n / n,
        "exact_joint_ci95": _wilson(exact_n, n),
        "support_id_recall": support_num / max(1, support_den),
        "reject_id_recall": reject_num / max(1, reject_den),
        "context_qoi_error_rate": context_errors / max(1, context_total),
        "cannot_check_recall": cc_tp / max(1, cc_gold),
        "cannot_check_precision": cc_tp / max(1, cc_pred),
        "family_exact": {family: sum(rows) / len(rows) for family, rows in sorted(family_exact.items())},
    }
    gate = freeze["vector_gate"]
    metrics["all_vector_gates_pass"] = (
        metrics["parse_validity"] >= gate["parse_validity_min"]
        and metrics["exact_joint_verdict_and_binding"] >= gate["exact_joint_verdict_and_binding_min"]
        and metrics["support_id_recall"] >= gate["support_id_recall_min"]
        and metrics["reject_id_recall"] >= gate["reject_id_recall_min"]
        and metrics["context_qoi_error_rate"] <= gate["context_qoi_error_max"]
        and metrics["cannot_check_recall"] >= gate["cannot_check_recall_min"]
        and metrics["cannot_check_precision"] >= gate["cannot_check_precision_min"]
        and min(metrics["family_exact"].values()) >= gate["family_min_exact"]
    )
    return metrics


def _shortcut_audit(tasks: list[dict], freeze: dict) -> dict:
    responders = {}
    for verdict in ("SUPPORT", "REFUTE", "CANNOT_CHECK", "CONTEXT_MISALIGNED"):
        records=[]
        for task in tasks:
            ids=sorted(_evidence_ids(task["prompt"]))
            parsed={"verdict":verdict,"selected_evidence_ids":ids[:1],"rejected_evidence_ids":ids[1:],"rationale_tags":[]}
            records.append({"task_id":task["task_id"],"parsed":parsed})
        responders[f"ALWAYS_{verdict}"]=_score(tasks,records,freeze)["all_vector_gates_pass"]
    return {
        "responders": responders,
        "clean": not any(responders.values()),
    }


def _resource_blocked(outdir: Path, reason: str, freeze: dict, manifest: dict) -> int:
    receipt={
        "schema_version":"rakl-capability-qualification-stage5-result-v1",
        "terminal":freeze["decision"]["resource"],
        "reason":reason,
        "model":freeze["model_candidates"][0],
        "panel_sha256":manifest["panel_sha256"],
        "model_substitution_performed":False,
        "grants_scientific_authority":False,
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"FINAL_CAPABILITY_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    return 2


def run(outdir: Path, *, model_path: str | None, dry_run: bool=False) -> int:
    try:
        tasks, freeze, manifest = _materialize_and_verify_panel()
    except RuntimeError as exc:
        outdir.mkdir(parents=True,exist_ok=True)
        receipt={"schema_version":"rakl-capability-qualification-stage5-result-v1","terminal":"QUALIFICATION_BENCHMARK_DEGENERATE","reason":str(exc),"grants_scientific_authority":False}
        (outdir/"FINAL_CAPABILITY_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
        return 3

    outdir.mkdir(parents=True, exist_ok=True)
    materialized = serialize(tasks)
    (outdir/"FRESH_TASKS_MATERIALIZED.jsonl").write_bytes(materialized)
    shortcut = _shortcut_audit(tasks, freeze)
    if not shortcut["clean"]:
        receipt={"schema_version":"rakl-capability-qualification-stage5-result-v1","terminal":freeze["decision"]["degenerate"],"shortcut_audit":shortcut,"grants_scientific_authority":False}
        (outdir/"FINAL_CAPABILITY_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
        return 3
    if dry_run:
        print(json.dumps({"dry_run":True,"n":len(tasks),"panel_sha256":manifest["panel_sha256"],"shortcut_audit":shortcut},indent=2))
        return 0
    if not model_path:
        return _resource_blocked(outdir,"model_path_missing",freeze,manifest)

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        return _resource_blocked(outdir,f"required_runtime_import_failed:{type(exc).__name__}:{exc}",freeze,manifest)
    if not torch.cuda.is_available():
        return _resource_blocked(outdir,"cuda_unavailable",freeze,manifest)

    model_root=Path(model_path)
    if not (model_root/"config.json").exists():
        matches=list(model_root.glob("**/config.json"))
        if len(matches)!=1:
            return _resource_blocked(outdir,f"exact_model_config_resolution_count:{len(matches)}",freeze,manifest)
        model_root=matches[0].parent

    t0=time.perf_counter()
    try:
        tokenizer=AutoTokenizer.from_pretrained(str(model_root),local_files_only=True)
        model=AutoModelForCausalLM.from_pretrained(
            str(model_root), local_files_only=True, torch_dtype=torch.bfloat16
        ).to("cuda").eval()
    except Exception as exc:
        return _resource_blocked(outdir,f"exact_model_load_failed:{type(exc).__name__}:{exc}",freeze,manifest)

    system=SYSTEM.read_text()
    instruction=RUNNER.read_text()
    records=[]
    for task in tasks:
        user=instruction+"\n\n"+task["prompt"]
        if getattr(tokenizer,"chat_template",None):
            input_ids=tokenizer.apply_chat_template(
                [{"role":"system","content":system},{"role":"user","content":user}],
                tokenize=True, add_generation_prompt=True, return_tensors="pt"
            ).to("cuda")
        else:
            input_ids=tokenizer(system+"\n\n"+user,return_tensors="pt").input_ids.to("cuda")
        with torch.no_grad():
            generated=model.generate(
                input_ids,
                max_new_tokens=int(freeze["interface"]["max_new_tokens"]),
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        raw=tokenizer.decode(generated[0,input_ids.shape[1]:],skip_special_tokens=True)
        parsed,reasons=_parse(raw)
        record={"task_id":task["task_id"],"family":task["family"],"raw":raw,"parsed":parsed,"parse_reasons":reasons}
        records.append(record)
        with (outdir/"RAW_OUTPUTS.jsonl").open("a") as handle:
            handle.write(json.dumps(record,sort_keys=True)+"\n")

    metrics=_score(tasks,records,freeze)
    metrics["shortcut_audit_clean"]=shortcut["clean"]
    pass_all=metrics["all_vector_gates_pass"] and shortcut["clean"]
    terminal=freeze["decision"]["pass"] if pass_all else freeze["decision"]["fail"]
    receipt={
        "schema_version":"rakl-capability-qualification-stage5-result-v1",
        "terminal":terminal,
        "model":freeze["model_candidates"][0],
        "interface":freeze["interface"],
        "panel_sha256":manifest["panel_sha256"],
        "metrics":metrics,
        "shortcut_audit":shortcut,
        "wall_seconds":time.perf_counter()-t0,
        "all_132_cases_completed":len(records)==132,
        "model_substitution_performed":False,
        "unlocks_treatment_result":False,
        "grants_scientific_authority":False,
    }
    (outdir/"qualification_results.json").write_text(json.dumps(metrics,indent=2)+"\n")
    (outdir/"FINAL_CAPABILITY_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    return 0 if pass_all else 1


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--outdir",type=Path,required=True)
    ap.add_argument("--model-path")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    raise SystemExit(run(args.outdir,model_path=args.model_path,dry_run=args.dry_run))


if __name__=="__main__":
    main()
