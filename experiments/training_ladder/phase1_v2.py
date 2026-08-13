#!/usr/bin/env python3
"""Phase-1 v2 exposure runner (corrected instrument).

Fixes the two v1 defects found in root-cause analysis
(research/paper4_phase1_results/ROOT_CAUSE.md):
  1. generator degeneracy (only 2 unique inputs/family) -> generator_v2 draws varied
     instances so the task is rule GENERALIZATION from train to disjoint held-out probes;
  2. training collapse (BPE merged the answer-token space, masking the gold token so no
     gradient reached the answer) -> uses the patched exposure_executor.lora_finetune,
     which concatenates token ids and trains the gold token.

It also adds a LEARNABILITY POSITIVE-CONTROL GATE: a "no state-dependent residual" verdict
is only permitted for a model that first clears the base task (SAME_STRUCTURE) above a
learnability floor; otherwise the honest terminal is MODEL_FLOOR. Emits outcomes bound to
the frozen packet hash; grants no scientific authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import generator_v2 as G  # noqa: E402
from exposure_executor import (  # noqa: E402
    Example,
    ExposureProbeKind,
    PROBE_TO_COORDINATE,
    REGISTERED_EXPOSURE_COUNTS,
    FROZEN_SEED,
    _evaluate,
    _now,
    lora_finetune,
    load_frozen_packet,
    DEFAULT_PACKET_DIR,
    DEFAULT_MODEL,
)

LEARNABILITY_FLOOR = 0.65   # SAME_STRUCTURE acc a model must clear before a residual verdict.
GAIN_FLOOR = 0.02
MASTERY_THRESHOLD = 0.90


def _to_ex(cases):
    return [Example(c.case_id, c.family, c.prompt, c.gold) for c in cases]


def build_v2_pool_and_probes(family: str, *, seed: int, max_exposure: int, probe_n: int = 16):
    """Varied train pool + 6 disjoint probe sets (rule generalization, not memorization)."""
    pool = _to_ex(G.generate(family, max_exposure, seed=seed, regime="base", tag="train"))
    other = G.FAMILIES[(G.FAMILIES.index(family) + 1) % len(G.FAMILIES)]
    probes = {
        ExposureProbeKind.SAME_STRUCTURE: _to_ex(G.generate(family, probe_n, seed=seed, regime="base", tag="probe")),
        ExposureProbeKind.NEW_COMPOSITION: _to_ex(G.generate(family, probe_n, seed=seed, regime="composition", tag="probe")),
        ExposureProbeKind.NEW_BOUNDARY: _to_ex(G.generate(family, probe_n, seed=seed, regime="boundary", tag="probe")),
        ExposureProbeKind.NEW_REPRESENTATION: _to_ex(G.generate(family, probe_n, seed=seed, regime="base", style="alt", tag="probe_alt")),
        ExposureProbeKind.NEW_DOMAIN: _to_ex(G.generate(other, probe_n, seed=seed, regime="base", tag="probe_other")),
        ExposureProbeKind.HOSTILE_NEAR_MISS: _to_ex(G.generate(family, probe_n, seed=seed, regime="hostile", tag="probe_hostile")),
    }
    train_ids = {e.case_id for e in pool}
    train_prompts = {e.prompt for e in pool}
    for kind, exs in list(probes.items()):
        overlap = train_ids & {e.case_id for e in exs}
        if overlap:
            raise ValueError(f"train/probe leakage {family}/{kind.value}: {sorted(overlap)}")
        # PROMPT-level disjointness: distinct ids can still render identical prompts
        # (small sampled ranges). Filter colliding probe items; refuse if too few remain.
        kept = [e for e in exs if e.prompt not in train_prompts]
        dropped = len(exs) - len(kept)
        if dropped:
            print(f"[disjoint] {family}/{kind.value}: dropped {dropped} probe item(s) with train-identical prompts")
        if len(kept) < max(4, len(exs) // 2):
            raise ValueError(f"probe set {family}/{kind.value} too small after prompt-disjoint filter: {len(kept)}")
        probes[kind] = kept
    return pool, probes


def classify_family_terminal(same_series, coord_series):
    """Learnability-gated per-family terminal.

    ``same_series``: list of (exposure, accuracy) for SAME_STRUCTURE.
    ``coord_series``: dict[probe_kind]-> list of (exposure, accuracy) for the other coords.
    """
    same_max = max((a for _, a in same_series), default=0.0)
    if same_max < LEARNABILITY_FLOOR:
        return "MODEL_FLOOR", {"reason": "did_not_clear_learnability_floor", "same_structure_max": round(same_max, 3), "floor": LEARNABILITY_FLOOR}
    # principle mastered at first exposure whose SAME_STRUCTURE acc >= threshold
    mastered_at = next((e for e, a in same_series if a >= MASTERY_THRESHOLD), None)
    late = same_series[len(same_series) // 2:]
    same_late_gain = (late[-1][1] - late[0][1]) if len(late) >= 2 else 0.0
    unsat = []
    for kind, series in coord_series.items():
        ls = series[len(series) // 2:]
        if len(ls) >= 2:
            unsat.append(ls[-1][1] - ls[0][1])
    unsat_late_gain = max(unsat, default=0.0)
    if mastered_at is not None and same_late_gain <= GAIN_FLOOR and unsat_late_gain > GAIN_FLOOR:
        term = "MECHANISM_SIGNAL_PRESENT"
        reason = "same_structure_saturated_after_mastery_while_other_coords_still_gain"
    elif same_late_gain > GAIN_FLOOR:
        term = "REPETITION_REMAINS_VALUABLE"
        reason = "same_structure_repetition_still_paying"
    else:
        term = "NO_STATE_DEPENDENT_RESIDUAL"
        reason = "no_differential_state_dependent_gain"
    return term, {
        "reason": reason,
        "same_structure_max": round(same_max, 3),
        "principle_mastered_at_exposure": mastered_at,
        "same_structure_late_gain": round(same_late_gain, 4),
        "unsaturated_coord_late_gain": round(unsat_late_gain, 4),
    }


def run(*, model_id, families, exposure_counts, out_dir, device, seed, epochs, lr, packet_dir, smoke):
    packet, packet_hash = load_frozen_packet(packet_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = _now()
    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(HERE)).decode().strip()
    rows, family_terminals = [], {}
    for family in families:
        pool, probes = build_v2_pool_and_probes(family, seed=seed, max_exposure=max(exposure_counts))
        same_series, coord_series = [], {k: [] for k in probes if k != ExposureProbeKind.SAME_STRUCTURE}
        prev = {}
        for n in sorted(exposure_counts):
            train = pool[:n]
            if not train:
                continue
            ckpt = out_dir / "checkpoints" / f"{family}_exp{n}"
            model, tok, ckpt_hash = lora_finetune(train, model_id=model_id, device=device, seed=seed, epochs=epochs, lr=lr, checkpoint_dir=ckpt)
            for kind, exs in probes.items():
                acc, cnt = _evaluate(model, tok, exs, device)
                coord = PROBE_TO_COORDINATE[kind]
                pe = prev.get(kind)
                mg = None if pe is None or cnt == 0 else round(acc - pe[1], 4)
                rows.append({
                    "family": family, "exposure_count": n, "probe_kind": kind.value,
                    "coordinate": coord.value, "accuracy": round(acc, 4), "n": cnt,
                    "checkpoint_hash": ckpt_hash, "marginal_gain": mg,
                    "prev_exposure_count": None if pe is None else pe[0],
                    "protocol_subject_hash": packet_hash, "generator": "v2", "smoke": smoke,
                })
                if cnt:
                    prev[kind] = (n, acc)
                    if kind == ExposureProbeKind.SAME_STRUCTURE:
                        same_series.append((n, acc))
                    else:
                        coord_series[kind].append((n, acc))
            del model
        term, evidence = classify_family_terminal(same_series, coord_series)
        family_terminals[family] = {"terminal": term, "evidence": evidence}
    (out_dir / "exposure_outcomes_v2.jsonl").write_text("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n")
    manifest = {
        "schema_version": "orion-training-ladder-phase1-v2-manifest-v1",
        "generator": "v2", "issue": 461, "phase": "0/1", "seed": seed, "smoke": smoke,
        "model_id": model_id, "epochs": epochs, "lr": lr, "git_sha": git_sha,
        "protocol_subject_hash": packet_hash, "grants_scientific_authority": False,
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "learnability_floor": LEARNABILITY_FLOOR,
        "family_terminals": family_terminals,
        "started_at": started, "finished_at": _now(),
        "note": "v2 corrected instrument (varied generator + fixed answer-token training + learnability gate). "
                "v1 is retracted as an instrument artifact (no training signal; degenerate generator).",
    }
    (out_dir / "run_manifest_v2.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--families", default=",".join(G.FAMILIES))
    p.add_argument("--max-exposure", type=int, default=64)
    p.add_argument("--out", default=str(HERE / "phase1_v2_out"))
    p.add_argument("--packet-dir", default=str(DEFAULT_PACKET_DIR))
    p.add_argument("--device", default="cuda")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--smoke", action="store_true")
    a = p.parse_args()
    fams = [f for f in a.families.split(",") if f]
    counts = [c for c in REGISTERED_EXPOSURE_COUNTS if c <= a.max_exposure]
    if a.smoke:
        fams, counts = fams[:1], [1, 2, 4]  # device honored as passed (GPU smoke allowed)
    m = run(model_id=a.model, families=fams, exposure_counts=counts, out_dir=Path(a.out),
            device=a.device, seed=FROZEN_SEED, epochs=a.epochs, lr=a.lr,
            packet_dir=Path(a.packet_dir), smoke=a.smoke)
    print(json.dumps({f: t["terminal"] for f, t in m["family_terminals"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
