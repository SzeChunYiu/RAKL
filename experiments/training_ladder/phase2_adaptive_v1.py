#!/usr/bin/env python3
"""Paper IV Phase-2 (#466): frozen Adaptive-vs-Static structural allocation.

The outcome-authorizing protocol is research/paper4_phase2_v1/PROTOCOL_V3.json.
This runner refuses model/algorithm substitutions.  If CUDA cannot execute the
exact pinned 7B subject under the frozen semantics it emits RESOURCE_BLOCKED.

The run separates selection from assurance:
- development pools: arm-specific training candidates only;
- selection probes: visible only to learner-aware arms C/E;
- fresh assurance: never used for selection, identical across all arms.

No output here grants theorem/scientific authority.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from experiments.training_ladder import generator_v2 as G  # noqa: E402

PROTOCOL_PATH = ROOT / "research" / "paper4_phase2_v1" / "PROTOCOL_V3.json"
INFERENCE_PATH = ROOT / "research" / "paper4_phase2_v1" / "INFERENCE_PLAN.json"

EXPOSURES = (
    "SAME_STRUCTURE",
    "NEW_COMPOSITION",
    "NEW_BOUNDARY",
    "NEW_REPRESENTATION",
    "NEW_DOMAIN",
    "HOSTILE_NEAR_MISS",
)
ARMS = (
    "A_UNIFORM_RANDOM",
    "B_SEMANTIC_DIVERSITY",
    "C_STRONGEST_MODEL_AWARE_PARENT",
    "D_STATIC_RAKL_STRUCTURAL",
    "E_ADAPTIVE_RAKL_STRUCTURAL",
)


@dataclass(frozen=True)
class Example:
    case_id: str
    exposure: str
    prompt: str
    gold: str


@dataclass
class ResourceCounter:
    model_loads: int = 0
    training_example_presentations: int = 0
    training_token_presentations: int = 0
    selection_examples_scored: int = 0
    selection_forward_calls: int = 0
    assurance_examples_scored: int = 0
    assurance_forward_calls: int = 0
    training_seconds: float = 0.0
    selection_seconds: float = 0.0
    assurance_seconds: float = 0.0
    cpu_selection_seconds: float = 0.0
    peak_gpu_memory_bytes: int = 0

    def as_dict(self) -> dict:
        total = self.training_seconds + self.selection_seconds + self.assurance_seconds + self.cpu_selection_seconds
        return {
            "model_loads": self.model_loads,
            "training_example_presentations": self.training_example_presentations,
            "training_token_presentations": self.training_token_presentations,
            "selection_examples_scored": self.selection_examples_scored,
            "selection_forward_calls": self.selection_forward_calls,
            "assurance_examples_scored": self.assurance_examples_scored,
            "assurance_forward_calls": self.assurance_forward_calls,
            "training_wall_seconds": self.training_seconds,
            "selection_wall_seconds": self.selection_seconds,
            "assurance_wall_seconds": self.assurance_seconds,
            "cpu_selection_seconds": self.cpu_selection_seconds,
            "total_accounted_seconds": total,
            "gpu_seconds": self.training_seconds + self.selection_seconds + self.assurance_seconds,
            "peak_gpu_memory_bytes": self.peak_gpu_memory_bytes,
        }


def _sha(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_freeze() -> tuple[dict, dict]:
    protocol = _load_json(PROTOCOL_PATH)
    inference = _load_json(INFERENCE_PATH)
    assert protocol["schema_version"] == "rakl-paper4-phase2-freeze-v3"
    assert protocol["outcomes_accessed_before_v3_freeze"] is False
    assert protocol["authorizing_phase1"]["terminal"] == "MECHANISM_SIGNAL_PRESENT"
    assert protocol["training"]["model_revision"] == "a09a35458c702b33eeacc393d103063234e8bc28"
    assert protocol["training"]["epochs"] == 12
    assert protocol["training"]["learning_rate"] == 0.0003
    assert protocol["data"]["final_examples_per_arm"] == 48
    assert protocol["data"]["rounds"] == 6
    assert inference["outcomes_accessed_before_freeze"] is False
    return protocol, inference


def _to_examples(cases: Iterable[G.V2Case], exposure: str) -> list[Example]:
    return [Example(c.case_id, exposure, c.prompt, c.gold) for c in cases]


def _pool(exposure: str, *, n: int, seed: int, tag: str) -> list[Example]:
    if exposure == "SAME_STRUCTURE":
        cases = G.generate("state_reachability", n, seed=seed, regime="base", style="default", tag=tag)
    elif exposure == "NEW_COMPOSITION":
        cases = G.generate("state_reachability", n, seed=seed, regime="composition", style="default", tag=tag)
    elif exposure == "NEW_BOUNDARY":
        cases = G.generate("state_reachability", n, seed=seed, regime="boundary", style="default", tag=tag)
    elif exposure == "NEW_REPRESENTATION":
        cases = G.generate("state_reachability", n, seed=seed, regime="base", style="alt", tag=tag)
    elif exposure == "NEW_DOMAIN":
        cases = G.generate("balance_conservation", n, seed=seed, regime="base", style="default", tag=tag)
    elif exposure == "HOSTILE_NEAR_MISS":
        cases = G.generate("state_reachability", n, seed=seed, regime="hostile", style="default", tag=tag)
    else:
        raise KeyError(exposure)
    return _to_examples(cases, exposure)


def _build_data(protocol: Mapping[str, object]) -> tuple[dict[str, list[Example]], dict[str, list[Example]], dict[str, list[Example]]]:
    data = protocol["data"]
    train = {
        exp: _pool(exp, n=int(data["candidate_pool_per_coordinate"]), seed=int(data["development_seed"]), tag="phase2-train-" + exp.lower())
        for exp in EXPOSURES
    }
    selection = {
        exp: _pool(exp, n=int(data["selection_probe_n_per_coordinate"]), seed=int(data["selection_probe_seed"]), tag="phase2-select-" + exp.lower())
        for exp in EXPOSURES
    }
    assurance = {
        exp: _pool(exp, n=int(data["fresh_assurance_n_per_coordinate"]), seed=int(data["fresh_assurance_seed"]), tag="phase2-assure-" + exp.lower())
        for exp in EXPOSURES
    }
    train_ids = {x.case_id for rows in train.values() for x in rows}
    select_ids = {x.case_id for rows in selection.values() for x in rows}
    assure_ids = {x.case_id for rows in assurance.values() for x in rows}
    if train_ids & select_ids or train_ids & assure_ids or select_ids & assure_ids:
        raise RuntimeError("phase2 case-id overlap across train/selection/assurance")
    train_prompts = {x.prompt for rows in train.values() for x in rows}
    select_prompts = {x.prompt for rows in selection.values() for x in rows}
    assure_prompts = {x.prompt for rows in assurance.values() for x in rows}
    if train_prompts & select_prompts or train_prompts & assure_prompts or select_prompts & assure_prompts:
        raise RuntimeError("phase2 prompt overlap across train/selection/assurance")
    return train, selection, assurance


def _shuffled_queues(train: Mapping[str, Sequence[Example]], seed: int) -> dict[str, list[Example]]:
    out: dict[str, list[Example]] = {}
    for exposure in EXPOSURES:
        rows = list(train[exposure])
        salt = int.from_bytes(hashlib.sha256(exposure.encode()).digest()[:8], "big")
        random.Random(seed ^ salt).shuffle(rows)
        out[exposure] = rows
    return out


def _take(queues: dict[str, list[Example]], exposure: str, n: int) -> list[Example]:
    if len(queues[exposure]) < n:
        raise RuntimeError(f"candidate pool exhausted for {exposure}")
    rows = queues[exposure][:n]
    del queues[exposure][:n]
    return rows


def _balanced_seed_batch(queues: dict[str, list[Example]], seed: int) -> tuple[list[Example], list[str]]:
    selected = [_take(queues, exposure, 1)[0] for exposure in EXPOSURES]
    extras = random.Random(seed).sample(list(EXPOSURES), 2)
    for exposure in extras:
        selected.extend(_take(queues, exposure, 1))
    return selected, list(EXPOSURES) + extras


def _uniform_random(train: Mapping[str, Sequence[Example]], seed: int, n: int) -> tuple[list[Example], list[str]]:
    rows = [x for exposure in EXPOSURES for x in train[exposure]]
    rng = random.Random(seed)
    chosen = rng.sample(rows, n)
    return chosen, [x.exposure for x in chosen]


def _tokens(text: str) -> frozenset[str]:
    return frozenset(text.lower().split())


def _jaccard_distance(a: frozenset[str], b: frozenset[str]) -> float:
    union = a | b
    return 0.0 if not union else 1.0 - len(a & b) / len(union)


def _semantic_diversity(train: Mapping[str, Sequence[Example]], seed: int, n: int) -> tuple[list[Example], list[str]]:
    start = time.perf_counter()
    rows = [x for exposure in EXPOSURES for x in train[exposure]]
    toks = {x.case_id: _tokens(x.prompt) for x in rows}
    rng = random.Random(seed)
    first = rows[rng.randrange(len(rows))]
    chosen = [first]
    remaining = {x.case_id: x for x in rows if x.case_id != first.case_id}
    while len(chosen) < n:
        best = None
        best_key = None
        for case_id, row in remaining.items():
            min_dist = min(_jaccard_distance(toks[case_id], toks[c.case_id]) for c in chosen)
            key = (min_dist, -len(toks[case_id]), case_id)
            if best_key is None or key > best_key:
                best_key = key
                best = row
        assert best is not None
        chosen.append(best)
        remaining.pop(best.case_id)
    return chosen, [x.exposure for x in chosen]


def _static_mix(train: Mapping[str, Sequence[Example]], protocol: Mapping[str, object], seed: int) -> tuple[list[Example], list[str]]:
    queues = _shuffled_queues(train, seed)
    selected: list[Example] = []
    trace: list[str] = []
    counts = protocol["data"]["static_counts"]
    for exposure in EXPOSURES:
        rows = _take(queues, exposure, int(counts[exposure]))
        selected.extend(rows)
        trace.extend([exposure] * len(rows))
    return selected, trace


def _cleanup_model(model=None, tokenizer=None) -> None:
    try:
        del model
    except Exception:
        pass
    try:
        del tokenizer
    except Exception:
        pass
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


def _adapter_hash(model) -> str:
    import torch
    h = hashlib.sha256()
    for key, tensor in sorted(model.state_dict().items()):
        if "lora" in key.lower() and isinstance(tensor, torch.Tensor):
            h.update(key.encode())
            h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def _train(
    examples: Sequence[Example],
    *,
    model_path: str,
    device: str,
    protocol: Mapping[str, object],
    seed: int,
    resources: ResourceCounter,
):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    cfg = protocol["training"]
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    t0 = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(model_path)
    lora_cfg = LoraConfig(
        r=int(cfg["lora"]["r"]),
        lora_alpha=int(cfg["lora"]["alpha"]),
        lora_dropout=float(cfg["lora"]["dropout"]),
        bias=str(cfg["lora"]["bias"]),
        task_type=str(cfg["lora"]["task_type"]),
        target_modules=list(cfg["lora"]["target_modules"]),
    )
    model = get_peft_model(base, lora_cfg)
    model.to(device)
    model.train()
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=float(cfg["learning_rate"]))
    eos = torch.tensor([[tokenizer.eos_token_id]], device=device)
    token_presentations = 0
    epochs = int(cfg["epochs"])
    for _ in range(epochs):
        for ex in examples:
            prompt_ids = tokenizer(ex.prompt, return_tensors="pt").input_ids.to(device)
            gold_ids = tokenizer(" " + ex.gold, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
            input_ids = torch.cat([prompt_ids, gold_ids, eos], dim=1)
            token_presentations += int(input_ids.numel())
            labels = input_ids.clone()
            labels[:, : prompt_ids.shape[1]] = -100
            optimizer.zero_grad()
            out = model(input_ids=input_ids, labels=labels)
            out.loss.backward()
            optimizer.step()
    model.eval()
    elapsed = time.perf_counter() - t0
    resources.model_loads += 1
    resources.training_example_presentations += epochs * len(examples)
    resources.training_token_presentations += token_presentations
    resources.training_seconds += elapsed
    if torch.cuda.is_available():
        resources.peak_gpu_memory_bytes = max(resources.peak_gpu_memory_bytes, int(torch.cuda.max_memory_allocated()))
    return model, tokenizer, _adapter_hash(model)


def _predict(model, tokenizer, prompt: str, device: str) -> str:
    import torch
    prompt_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    best = None
    best_lp = None
    for label in ("VALID", "INVALID"):
        target = tokenizer(" " + label, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
        full = torch.cat([prompt_ids, target], dim=1)
        with torch.no_grad():
            logits = model(full).logits
        logp = torch.log_softmax(logits, dim=-1)
        total = 0.0
        n_prompt = prompt_ids.shape[1]
        for i in range(target.shape[1]):
            total += float(logp[0, n_prompt + i - 1, target[0, i]])
        if best_lp is None or total > best_lp:
            best_lp = total
            best = label
    assert best is not None
    return best


def _accuracy_by_exposure(model, tokenizer, probes: Mapping[str, Sequence[Example]], device: str, resources: ResourceCounter) -> dict[str, float]:
    t0 = time.perf_counter()
    out: dict[str, float] = {}
    for exposure in EXPOSURES:
        rows = probes[exposure]
        correct = 0
        for ex in rows:
            correct += int(_predict(model, tokenizer, ex.prompt, device) == ex.gold)
        out[exposure] = correct / len(rows)
        resources.selection_examples_scored += len(rows)
        resources.selection_forward_calls += 2 * len(rows)
    resources.selection_seconds += time.perf_counter() - t0
    return out


def _gold_nll(model, tokenizer, ex: Example, device: str) -> float:
    import torch
    prompt = tokenizer(ex.prompt, return_tensors="pt").input_ids.to(device)
    target = tokenizer(" " + ex.gold, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
    full = torch.cat([prompt, target], dim=1)
    with torch.no_grad():
        logits = model(full).logits
    logp = torch.log_softmax(logits, dim=-1)
    n = prompt.shape[1]
    vals = [-float(logp[0, n + i - 1, target[0, i]]) for i in range(target.shape[1])]
    return sum(vals) / len(vals)


def _nll_by_exposure(model, tokenizer, probes: Mapping[str, Sequence[Example]], device: str, resources: ResourceCounter) -> dict[str, float]:
    t0 = time.perf_counter()
    out = {}
    for exposure in EXPOSURES:
        vals = [_gold_nll(model, tokenizer, ex, device) for ex in probes[exposure]]
        out[exposure] = statistics.mean(vals)
        resources.selection_examples_scored += len(vals)
        resources.selection_forward_calls += len(vals)
    resources.selection_seconds += time.perf_counter() - t0
    return out


def _model_aware_select(
    train: Mapping[str, Sequence[Example]],
    probes: Mapping[str, Sequence[Example]],
    *,
    model_path: str,
    device: str,
    protocol: Mapping[str, object],
    seed: int,
    resources: ResourceCounter,
) -> tuple[list[Example], list[dict]]:
    queues = _shuffled_queues(train, seed)
    selected, seed_trace = _balanced_seed_batch(queues, seed)
    log = [{"round": 1, "selected_exposures": seed_trace, "rule": "balanced_seed"}]
    rounds = int(protocol["data"]["rounds"])
    batch = int(protocol["data"]["batch_size"])
    tie_order = list(protocol["exposure_order_for_ties"])
    for round_idx in range(1, rounds):
        model, tok, ckpt = _train(selected, model_path=model_path, device=device, protocol=protocol, seed=seed + round_idx, resources=resources)
        nll = _nll_by_exposure(model, tok, probes, device, resources)
        target = max(tie_order, key=lambda x: (nll[x], -tie_order.index(x)))
        _cleanup_model(model, tok)
        new_rows = _take(queues, target, batch)
        selected.extend(new_rows)
        log.append({"round": round_idx + 1, "target": target, "selection_nll": nll, "checkpoint_hash": ckpt, "selected_exposures": [target] * batch})
    return selected, log


def _adaptive_select(
    train: Mapping[str, Sequence[Example]],
    probes: Mapping[str, Sequence[Example]],
    *,
    model_path: str,
    device: str,
    protocol: Mapping[str, object],
    seed: int,
    resources: ResourceCounter,
) -> tuple[list[Example], list[dict], str | None]:
    queues = _shuffled_queues(train, seed)
    selected, seed_trace = _balanced_seed_batch(queues, seed)
    log = [{"round": 1, "selected_exposures": seed_trace, "rule": "balanced_seed"}]
    rounds = int(protocol["data"]["rounds"])
    batch = int(protocol["data"]["batch_size"])
    tie_order = list(protocol["exposure_order_for_ties"])
    blocked: set[str] = set()
    prev_metrics = None
    prev_target = None
    for round_idx in range(1, rounds):
        model, tok, ckpt = _train(selected, model_path=model_path, device=device, protocol=protocol, seed=seed + 100 + round_idx, resources=resources)
        acc = _accuracy_by_exposure(model, tok, probes, device, resources)
        _cleanup_model(model, tok)
        if prev_metrics is not None and prev_target is not None:
            same_drop = prev_metrics["SAME_STRUCTURE"] - acc["SAME_STRUCTURE"]
            hostile_drop = prev_metrics["HOSTILE_NEAR_MISS"] - acc["HOSTILE_NEAR_MISS"]
            if same_drop > 0.10 or hostile_drop > 0.10:
                blocked.add(prev_target)
        if acc["SAME_STRUCTURE"] < 0.90 and "SAME_STRUCTURE" not in blocked:
            target = "SAME_STRUCTURE"
        elif acc["HOSTILE_NEAR_MISS"] < 0.80 and "HOSTILE_NEAR_MISS" not in blocked:
            target = "HOSTILE_NEAR_MISS"
        else:
            eligible = [x for x in tie_order if x != "SAME_STRUCTURE" and x not in blocked]
            if not eligible:
                return selected, log, "no_safe_unsaturated_coordinate"
            target = min(eligible, key=lambda x: (acc[x], tie_order.index(x)))
        batch_rows: list[Example] = []
        if target == "SAME_STRUCTURE":
            batch_rows.extend(_take(queues, "SAME_STRUCTURE", batch))
            exposures = ["SAME_STRUCTURE"] * batch
        else:
            batch_rows.extend(_take(queues, "SAME_STRUCTURE", 1))
            batch_rows.extend(_take(queues, target, batch - 1))
            exposures = ["SAME_STRUCTURE"] + [target] * (batch - 1)
        selected.extend(batch_rows)
        log.append({"round": round_idx + 1, "target": target, "mastery_accuracy": acc, "blocked_after_previous_round": sorted(blocked), "checkpoint_hash": ckpt, "selected_exposures": exposures})
        prev_metrics = acc
        prev_target = target
    return selected, log, None


def _final_score(model, tokenizer, assurance: Mapping[str, Sequence[Example]], device: str, resources: ResourceCounter) -> list[dict]:
    t0 = time.perf_counter()
    rows = []
    for exposure in EXPOSURES:
        for ex in assurance[exposure]:
            pred = _predict(model, tokenizer, ex.prompt, device)
            rows.append({"case_id": ex.case_id, "exposure": exposure, "gold": ex.gold, "prediction": pred, "correct": int(pred == ex.gold)})
            resources.assurance_examples_scored += 1
            resources.assurance_forward_calls += 2
    resources.assurance_seconds += time.perf_counter() - t0
    return rows


def _accuracy(rows: Sequence[Mapping[str, object]], exposure: str | None = None) -> float:
    use = [r for r in rows if exposure is None or r["exposure"] == exposure]
    return sum(int(r["correct"]) for r in use) / len(use)


def _paired_diffs(rows_a: Sequence[Mapping[str, object]], rows_b: Sequence[Mapping[str, object]], exposure: str | None = None) -> list[tuple[str, str, int]]:
    a = {str(r["case_id"]): r for r in rows_a if exposure is None or r["exposure"] == exposure}
    b = {str(r["case_id"]): r for r in rows_b if exposure is None or r["exposure"] == exposure}
    if set(a) != set(b):
        raise RuntimeError("paired assurance case sets differ across arms")
    return [(cid, str(a[cid]["exposure"]), int(a[cid]["correct"]) - int(b[cid]["correct"])) for cid in sorted(a)]


def _bootstrap_ci(diffs: Sequence[tuple[str, str, int]], *, reps: int, seed: int, stratified: bool = True) -> tuple[float, float, float]:
    rng = random.Random(seed)
    mean = statistics.mean(d for _, _, d in diffs)
    samples = []
    if stratified:
        strata = {e: [d for _, ex, d in diffs if ex == e] for e in EXPOSURES}
        for _ in range(reps):
            vals = []
            for exposure in EXPOSURES:
                src = strata[exposure]
                vals.extend(src[rng.randrange(len(src))] for _ in range(len(src)))
            samples.append(statistics.mean(vals))
    else:
        vals0 = [d for _, _, d in diffs]
        for _ in range(reps):
            samples.append(statistics.mean(vals0[rng.randrange(len(vals0))] for _ in range(len(vals0))))
    samples.sort()
    lo = samples[int(0.025 * reps)]
    hi = samples[min(reps - 1, int(0.975 * reps) - 1)]
    return mean, lo, hi


def _signflip_p(diffs: Sequence[tuple[str, str, int]], *, reps: int, seed: int) -> float:
    vals = [d for _, _, d in diffs if d != 0]
    if not vals:
        return 1.0
    obs = abs(statistics.mean(vals))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        stat = abs(statistics.mean(d * (-1 if rng.random() < 0.5 else 1) for d in vals))
        extreme += stat >= obs - 1e-15
    return (extreme + 1) / (reps + 1)


def _holm(pvals: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvals, key=pvals.get)
    m = len(ordered)
    adjusted = {}
    running = 0.0
    for i, key in enumerate(ordered):
        value = min(1.0, (m - i) * pvals[key])
        running = max(running, value)
        adjusted[key] = running
    return adjusted


def _analyze(results: Mapping[str, Sequence[Mapping[str, object]]], resources: Mapping[str, ResourceCounter], inference: Mapping[str, object]) -> dict:
    contrasts = {"E-D": ("E_ADAPTIVE_RAKL_STRUCTURAL", "D_STATIC_RAKL_STRUCTURAL"), "E-C": ("E_ADAPTIVE_RAKL_STRUCTURAL", "C_STRONGEST_MODEL_AWARE_PARENT"), "D-B": ("D_STATIC_RAKL_STRUCTURAL", "B_SEMANTIC_DIVERSITY")}
    contrast_out = {}
    raw_p = {}
    for i, (name, (a, b)) in enumerate(contrasts.items()):
        diffs = _paired_diffs(results[a], results[b])
        mean, lo, hi = _bootstrap_ci(diffs, reps=int(inference["confidence_interval"]["repetitions"]), seed=int(inference["confidence_interval"]["seed"]) + i)
        p = _signflip_p(diffs, reps=int(inference["significance"]["repetitions"]), seed=int(inference["significance"]["seed"]) + i)
        raw_p[name] = p
        contrast_out[name] = {"mean": mean, "ci95": [lo, hi], "raw_p": p}
    adjusted = _holm(raw_p)
    for name in contrast_out:
        contrast_out[name]["holm_p"] = adjusted[name]

    hard = {}
    for i, exposure in enumerate(inference["hard_harm"]["coordinates"]):
        diffs = _paired_diffs(results["E_ADAPTIVE_RAKL_STRUCTURAL"], results["D_STATIC_RAKL_STRUCTURAL"], exposure=exposure)
        mean, lo, hi = _bootstrap_ci(diffs, reps=int(inference["confidence_interval"]["repetitions"]), seed=int(inference["confidence_interval"]["seed"]) + 100 + i, stratified=False)
        hard[exposure] = {"mean": mean, "ci95": [lo, hi], "passes": lo > float(inference["hard_harm"]["boundary"])}

    ed = contrast_out["E-D"]
    ec = contrast_out["E-C"]
    hard_ok = all(v["passes"] for v in hard.values())
    positive = ed["mean"] >= float(inference["mde"]["material_gain"]) and ed["ci95"][0] > 0 and ed["holm_p"] < 0.05 and ec["ci95"][0] >= float(inference["parent_noninferiority"]["boundary"]) and hard_ok
    precise_null = ed["ci95"][0] <= 0 <= ed["ci95"][1] and ed["ci95"][1] < float(inference["mde"]["material_gain"]) and hard_ok
    if not hard_ok:
        terminal = "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION"
    elif ec["ci95"][1] < float(inference["parent_noninferiority"]["boundary"]):
        terminal = "PARENT_MATCHES_OR_BEATS"
    elif positive:
        e_gpu = resources["E_ADAPTIVE_RAKL_STRUCTURAL"].as_dict()["gpu_seconds"]
        d_gpu = max(1e-9, resources["D_STATIC_RAKL_STRUCTURAL"].as_dict()["gpu_seconds"])
        terminal = "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST" if e_gpu / d_gpu > 2.0 else "ADAPTIVE_RESIDUAL_SUPPORTED"
    elif precise_null:
        terminal = "STATIC_EQUALS_ADAPTIVE"
    else:
        terminal = "UNDERPOWERED"
    return {"contrasts": contrast_out, "hard_harm": hard, "terminal": terminal}


def _resource_blocked(outdir: Path, reason: str, protocol: Mapping[str, object]) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "terminal": "RESOURCE_BLOCKED",
        "reason": reason,
        "model_id": protocol["training"]["model_id"],
        "model_revision": protocol["training"]["revision"],
        "model_substitution_performed": False,
        "grants_scientific_authority": False,
    }
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 2


def run(outdir: Path, *, dry_run: bool = False) -> int:
    protocol, inference = _check_freeze()
    train, selection, assurance = _build_data(protocol)
    data_manifest = {
        "train": {k: [x.case_id for x in v] for k, v in train.items()},
        "selection": {k: [x.case_id for x in v] for k, v in selection.items()},
        "assurance": {k: [x.case_id for x in v] for k, v in assurance.items()},
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "DATA_MANIFEST.json").write_text(json.dumps({"sha256": _sha(data_manifest), **data_manifest}, indent=2) + "\n")
    if dry_run:
        print(json.dumps({"dry_run": True, "data_manifest_sha": _sha(data_manifest), "n_train": sum(map(len, train.values())), "n_selection": sum(map(len, selection.values())), "n_assurance": sum(map(len, assurance.values()))}, indent=2))
        return 0

    try:
        import torch
        from huggingface_hub import snapshot_download
    except Exception as exc:
        return _resource_blocked(outdir, f"required_runtime_import_failed:{type(exc).__name__}:{exc}", protocol)
    if not torch.cuda.is_available():
        return _resource_blocked(outdir, "cuda_unavailable_for_exact_7b_protocol", protocol)
    device = "cuda"
    try:
        model_path = snapshot_download(repo_id=protocol["training"]["model_id"], revision=protocol["training"]["revision"])
    except Exception as exc:
        return _resource_blocked(outdir, f"exact_model_snapshot_unavailable:{type(exc).__name__}:{exc}", protocol)

    seed = int(protocol["training"]["training_seed"])
    selected: dict[str, list[Example]] = {}
    selection_logs: dict[str, object] = {}
    resources = {arm: ResourceCounter() for arm in ARMS}

    t0 = time.perf_counter()
    a_rows, a_trace = _uniform_random(train, seed, 48)
    selected["A_UNIFORM_RANDOM"] = a_rows
    selection_logs["A_UNIFORM_RANDOM"] = a_trace
    b_start = time.perf_counter()
    b_rows, b_trace = _semantic_diversity(train, seed, 48)
    resources["B_SEMANTIC_DIVERSITY"].cpu_selection_seconds += time.perf_counter() - b_start
    selected["B_SEMANTIC_DIVERSITY"] = b_rows
    selection_logs["B_SEMANTIC_DIVERSITY"] = b_trace
    d_rows, d_trace = _static_mix(train, protocol, seed)
    selected["D_STATIC_RAKL_STRUCTURAL"] = d_rows
    selection_logs["D_STATIC_RAKL_STRUCTURAL"] = d_trace

    c_rows, c_log = _model_aware_select(train, selection, model_path=model_path, device=device, protocol=protocol, seed=seed, resources=resources["C_STRONGEST_MODEL_AWARE_PARENT"])
    selected["C_STRONGEST_MODEL_AWARE_PARENT"] = c_rows
    selection_logs["C_STRONGEST_MODEL_AWARE_PARENT"] = c_log
    e_rows, e_log, e_block = _adaptive_select(train, selection, model_path=model_path, device=device, protocol=protocol, seed=seed, resources=resources["E_ADAPTIVE_RAKL_STRUCTURAL"])
    if e_block is not None or len(e_rows) != 48:
        receipt = {"schema_version":"rakl-paper4-phase2-result-v1","terminal":"ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION","reason":e_block or "adaptive_allocation_incomplete","selected_n":len(e_rows),"grants_scientific_authority":False}
        (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(json.dumps(receipt, indent=2))
        return 1
    selected["E_ADAPTIVE_RAKL_STRUCTURAL"] = e_rows
    selection_logs["E_ADAPTIVE_RAKL_STRUCTURAL"] = e_log

    (outdir / "SELECTION_LOGS.json").write_text(json.dumps(selection_logs, indent=2) + "\n")
    (outdir / "SELECTED_TRAINING_CASES.json").write_text(json.dumps({arm:[{"case_id":x.case_id,"exposure":x.exposure} for x in rows] for arm,rows in selected.items()}, indent=2) + "\n")

    results: dict[str, list[dict]] = {}
    checkpoints = {}
    for arm in ARMS:
        model, tok, ckpt = _train(selected[arm], model_path=model_path, device=device, protocol=protocol, seed=seed + 1000 + ARMS.index(arm), resources=resources[arm])
        checkpoints[arm] = ckpt
        results[arm] = _final_score(model, tok, assurance, device, resources[arm])
        _cleanup_model(model, tok)

    analysis = _analyze(results, resources, inference)
    arm_summary = {}
    for arm in ARMS:
        arm_summary[arm] = {
            "overall_accuracy": _accuracy(results[arm]),
            "by_exposure": {exposure: _accuracy(results[arm], exposure) for exposure in EXPOSURES},
            "checkpoint_hash": checkpoints[arm],
            "resources": resources[arm].as_dict(),
        }
    for arm, rows in results.items():
        path = outdir / f"ASSURANCE_{arm}.jsonl"
        with path.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    receipt = {
        "schema_version": "rakl-paper4-phase2-result-v1",
        "protocol": "PROTOCOL_V3.json",
        "inference_plan": "INFERENCE_PLAN.json",
        "model_id": protocol["training"]["model_id"],
        "model_revision": protocol["training"]["revision"],
        "data_manifest_hash": _sha(data_manifest),
        "arms": arm_summary,
        "analysis": analysis,
        "terminal": analysis["terminal"],
        "total_wall_seconds": time.perf_counter() - t0,
        "grants_scientific_authority": False,
        "paper4_standalone_authorized": analysis["terminal"] in {"ADAPTIVE_RESIDUAL_SUPPORTED", "ADAPTIVE_RESIDUAL_SUPPORTED_HIGH_COST"},
    }
    (outdir / "FINAL_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    raise SystemExit(run(args.outdir, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
