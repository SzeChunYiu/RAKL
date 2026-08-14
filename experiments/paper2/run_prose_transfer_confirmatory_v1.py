#!/usr/bin/env python3
"""Execute the frozen Paper II prose-transfer confirmatory.

Protocol: `research/paper2_prose_transfer_v1/PROTOCOL.json` (frozen at commit
`bf925375`, before any instrument, extractor or runner code existed).

Runs, in order:

  probe G   acceptance test — scramble every source_text/target_text and require
            the full arm to COLLAPSE. If it does not, the instrument is still
            not measuring extraction and nothing else here means anything.
  G1..G7    the registered gates
  NC1..NC3  the registered negative controls, which must FAIL the gate

The lexical parent's threshold is fitted on the DEV bank only. Every reported
confirmatory number comes from the HELDOUT bank, whose qualitative, hedge,
distractor and filler lexicons are disjoint from DEV.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Callable, Sequence

from rakl.objective_transfer_benchmark import Decision
from rakl.prose_transfer_extractor_v1 import (
    extract_coordinates,
    full_prose_extractor,
    keyword_polarity_parent,
    lexical_overlap,
)
from rakl.prose_transfer_instrument_v1 import (
    COORDINATES,
    LatentSpec,
    ProseTask,
    generate,
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = ROOT / "research" / "paper2_prose_transfer_v1" / "PROTOCOL.json"

NOISE_WORDS = ("zqx", "vpl", "mtr", "kbd", "wfn", "hgs", "yjc", "roa", "ludo", "esk")


def _noise_like(text: str, rng: random.Random) -> str:
    return " ".join(rng.choice(NOISE_WORDS) for _ in range(len(text.split())))


def _exact(gold: Sequence[Decision], pred: Sequence[Decision]) -> float:
    return sum(g is p for g, p in zip(gold, pred)) / len(gold)


def _joint(gold: Sequence[Decision], pred: Sequence[Decision]) -> dict[str, float]:
    valid = [i for i, g in enumerate(gold) if g is Decision.ACCEPT]
    invalid = [i for i, g in enumerate(gold) if g is Decision.REJECT]
    unknown = [i for i, g in enumerate(gold) if g is Decision.CANNOT_CHECK]
    return {
        "exact": _exact(gold, pred),
        "valid_accept": sum(pred[i] is Decision.ACCEPT for i in valid) / len(valid),
        "invalid_false_accept": sum(pred[i] is Decision.ACCEPT for i in invalid) / len(invalid),
        "cannot_check_recall": (
            sum(pred[i] is Decision.CANNOT_CHECK for i in unknown) / len(unknown)
            if unknown
            else float("nan")
        ),
    }


def _mcnemar_exact(gold, a, b) -> tuple[int, int, float]:
    """Two-sided exact McNemar on per-item correctness of arms a and b."""
    n01 = sum(1 for g, x, y in zip(gold, a, b) if (x is g) and not (y is g))
    n10 = sum(1 for g, x, y in zip(gold, a, b) if not (x is g) and (y is g))
    n = n01 + n10
    if n == 0:
        return n01, n10, 1.0
    k = min(n01, n10)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return n01, n10, min(1.0, 2.0 * tail)


def _bootstrap_paired(gold, a, b, reps: int, seed: int) -> tuple[float, float]:
    rng = random.Random(seed)
    n = len(gold)
    diffs = [(1.0 if x is g else 0.0) - (1.0 if y is g else 0.0) for g, x, y in zip(gold, a, b)]
    out = []
    for _ in range(reps):
        out.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    out.sort()
    return out[int(0.025 * reps)], out[min(reps - 1, int(0.975 * reps))]


def _shuffle_null(gold, pred, reps: int, seed: int) -> dict[str, float]:
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        permuted = list(gold)
        rng.shuffle(permuted)
        vals.append(_exact(permuted, pred))
    vals.sort()
    return {
        "mean": statistics.fmean(vals),
        "lo95": vals[int(0.025 * reps)],
        "hi95": vals[min(reps - 1, int(0.975 * reps))],
    }


def _fit_lexical_threshold(dev_seed: int, n_per_cell: int) -> float:
    tasks, specs = generate(dev_seed, n_per_cell=n_per_cell, bank="dev")
    gold = [s.gold for s in specs]
    best, best_exact = 0.5, -1.0
    for step in range(1, 100):
        thr = step / 100.0
        pred = [
            Decision.ACCEPT if lexical_overlap(t) >= thr else Decision.REJECT for t in tasks
        ]
        score = _exact(gold, pred)
        if score > best_exact:
            best, best_exact = thr, score
    return best


def _arms(tasks: Sequence[ProseTask], lex_thr: float, dev_majority: Decision):
    return {
        "FULL_PROSE_EXTRACTOR": [full_prose_extractor(t) for t in tasks],
        "P_KEYWORD_POLARITY": [keyword_polarity_parent(t) for t in tasks],
        "P_LEXICAL": [
            Decision.ACCEPT if lexical_overlap(t) >= lex_thr else Decision.REJECT for t in tasks
        ],
        "P_PRIOR_MAJORITY": [dev_majority] * len(tasks),
        "P_ALWAYS_REJECT": [Decision.REJECT] * len(tasks),
        "P_ALWAYS_ACCEPT": [Decision.ACCEPT] * len(tasks),
        "P_ALWAYS_CANNOT_CHECK": [Decision.CANNOT_CHECK] * len(tasks),
    }


PARENTS = (
    "P_KEYWORD_POLARITY",
    "P_LEXICAL",
    "P_PRIOR_MAJORITY",
    "P_ALWAYS_REJECT",
    "P_ALWAYS_ACCEPT",
    "P_ALWAYS_CANNOT_CHECK",
)


def _g1(gold, full, parent_pred, boot_seed) -> dict:
    adv = _exact(gold, full) - _exact(gold, parent_pred)
    n01, n10, p = _mcnemar_exact(gold, full, parent_pred)
    lo, hi = _bootstrap_paired(gold, full, parent_pred, 2000, boot_seed)
    return {
        "advantage": adv,
        "mcnemar_n01": n01,
        "mcnemar_n10": n10,
        "mcnemar_p": p,
        "bootstrap95": [lo, hi],
        "passes": bool(adv >= 0.10 and p < 0.01 and lo > 0.0),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "research" / "paper2_prose_transfer_v1" / "results"))
    ap.add_argument("--n-per-cell", type=int, default=24)
    ap.add_argument("--seeds", type=int, default=12)
    args = ap.parse_args()
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    protocol = json.loads(PROTOCOL_PATH.read_text())
    dev_seed = int(protocol["development_confirmatory_separation"]["dev_seed"])
    conf_seed = int(protocol["development_confirmatory_separation"]["confirmatory_seed"])
    null_reps = int(protocol["shuffle_equal_n_null"]["reps"])

    lex_thr = _fit_lexical_threshold(dev_seed, args.n_per_cell)
    _, dev_specs = generate(dev_seed, n_per_cell=args.n_per_cell, bank="dev")
    dev_majority = Counter(s.gold for s in dev_specs).most_common(1)[0][0]

    tasks, specs = generate(conf_seed, n_per_cell=args.n_per_cell, bank="heldout")
    gold = [s.gold for s in specs]
    arms = _arms(tasks, lex_thr, dev_majority)
    full = arms["FULL_PROSE_EXTRACTOR"]

    scores = {name: _joint(gold, pred) for name, pred in arms.items()}
    strongest = max(PARENTS, key=lambda p: scores[p]["exact"])

    null = _shuffle_null(gold, full, null_reps, 77)

    # ---- probe G: the acceptance test -------------------------------------
    rng = random.Random(20260814)
    scrambled_tasks = [
        replace(
            t,
            source_text=_noise_like(t.source_text, rng),
            target_text=_noise_like(t.target_text, rng),
        )
        for t in tasks
    ]
    scrambled_full = [full_prose_extractor(t) for t in scrambled_tasks]
    scrambled_exact = _exact(gold, scrambled_full)
    arm_changed = sum(a is not b for a, b in zip(full, scrambled_full))
    probe_g = {
        "surface_changed": f"{sum(a.target_text != b.target_text for a, b in zip(tasks, scrambled_tasks))}/{len(tasks)}",
        "gold_unchanged_by_construction": True,
        "full_arm_changed_by_scramble": f"{arm_changed}/{len(tasks)}",
        "clean_full_exact": scores["FULL_PROSE_EXTRACTOR"]["exact"],
        "scrambled_full_exact": scrambled_exact,
        "collapsed_into_null_95": bool(null["lo95"] <= scrambled_exact <= null["hi95"]),
        "scrambling_destroys_performance": bool(
            scrambled_exact < scores["FULL_PROSE_EXTRACTOR"]["exact"] - 0.10
        ),
    }

    # ---- error attribution by registered ambiguity class -------------------
    class_errors: Counter[str] = Counter()
    class_totals: Counter[str] = Counter()
    coord_mode_errors: Counter[str] = Counter()
    for task, spec in zip(tasks, specs):
        coords = extract_coordinates(task)
        for name in COORDINATES:
            cs = spec.coords[name]
            class_totals[cs.mode] += 1
            if coords[name] is not cs.decision:
                class_errors[cs.mode] += 1
                coord_mode_errors[f"{name}:{cs.mode}"] += 1

    # ---- gates -------------------------------------------------------------
    g1 = _g1(gold, full, arms[strongest], 1234)
    full_exact = scores["FULL_PROSE_EXTRACTOR"]["exact"]
    g2 = {"full_exact": full_exact, "passes": bool(full_exact < 1.0)}
    g3 = {
        "classes_with_errors": sorted(class_errors),
        "errors_by_class": dict(class_errors),
        "totals_by_class": dict(class_totals),
        "passes": bool(len(class_errors) >= 3),
    }
    fs = scores["FULL_PROSE_EXTRACTOR"]
    trivial_joint = {
        name: bool(
            scores[name]["valid_accept"] >= 0.80 and scores[name]["invalid_false_accept"] <= 0.10
        )
        for name in ("P_ALWAYS_REJECT", "P_ALWAYS_ACCEPT", "P_ALWAYS_CANNOT_CHECK")
    }
    g4 = {
        "full_valid_accept": fs["valid_accept"],
        "full_invalid_false_accept": fs["invalid_false_accept"],
        "trivial_arms_attaining_both": trivial_joint,
        "passes": bool(
            fs["valid_accept"] >= 0.80
            and fs["invalid_false_accept"] <= 0.10
            and not any(trivial_joint.values())
        ),
    }
    full_loss = [0.0 if p is g else 1.0 for g, p in zip(gold, full)]
    parent_loss = [0.0 if p is g else 1.0 for g, p in zip(gold, arms[strongest])]
    g5 = {
        "full_loss_variance": statistics.pvariance(full_loss),
        "parent_loss_variance": statistics.pvariance(parent_loss),
        "passes": bool(statistics.pvariance(full_loss) > 0 and statistics.pvariance(parent_loss) > 0),
    }

    # ---- G6: seed spread ---------------------------------------------------
    per_seed = []
    for offset in range(args.seeds):
        s = conf_seed + offset
        st, sp = generate(s, n_per_cell=args.n_per_cell, bank="heldout")
        sg = [x.gold for x in sp]
        sa = _arms(st, lex_thr, dev_majority)
        sstrong = max(PARENTS, key=lambda p: _exact(sg, sa[p]))
        per_seed.append(
            {
                "seed": s,
                "full_exact": _exact(sg, sa["FULL_PROSE_EXTRACTOR"]),
                "strongest_parent": sstrong,
                "advantage": _exact(sg, sa["FULL_PROSE_EXTRACTOR"]) - _exact(sg, sa[sstrong]),
            }
        )
    distinct = {round(r["advantage"], 6) for r in per_seed}
    g6 = {
        "seeds": args.seeds,
        "distinct_advantage_values": len(distinct),
        "min_advantage": min(r["advantage"] for r in per_seed),
        "max_advantage": max(r["advantage"] for r in per_seed),
        "passes": bool(args.seeds >= 12 and len(distinct) >= 3),
    }

    # ---- G7: negative controls must FAIL G1 --------------------------------
    nc1 = _g1(gold, scrambled_full, arms[strongest], 5)
    permuted_gold = list(gold)
    random.Random(99).shuffle(permuted_gold)
    nc2 = _g1(permuted_gold, full, arms[strongest], 6)
    nc3 = {
        name: bool(
            scores[name]["valid_accept"] >= 0.80 and scores[name]["invalid_false_accept"] <= 0.10
        )
        for name in ("P_ALWAYS_REJECT", "P_ALWAYS_ACCEPT", "P_ALWAYS_CANNOT_CHECK")
    }
    g7 = {
        "NC1_SCRAMBLED_TEXT_fails_G1": not nc1["passes"],
        "NC1_detail": nc1,
        "NC2_SHUFFLED_GOLD_fails_G1": not nc2["passes"],
        "NC2_detail": nc2,
        "NC3_TRIVIAL_ARMS_fail_G4": not any(nc3.values()),
        "NC3_detail": nc3,
        "passes": bool(
            (not nc1["passes"]) and (not nc2["passes"]) and (not any(nc3.values()))
        ),
    }

    gates = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6, "G7": g7}
    all_pass = all(g["passes"] for g in gates.values())

    if not probe_g["scrambling_destroys_performance"]:
        terminal = "INSTRUMENT_STILL_NOT_MEASURING_EXTRACTION"
    elif not (g6["passes"] and g7["passes"]):
        terminal = "GATE_NOT_FALSIFIABLE"
    elif not g1["passes"]:
        terminal = "EXTRACTION_NEGATIVE__ARM_DOES_NOT_BEAT_PARENT"
    elif not (g2["passes"] and g3["passes"]):
        terminal = "INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION"
    elif all_pass:
        terminal = "PROSE_EXTRACTION_INSTRUMENT_PROBATIVE__SCOPED"
    else:
        terminal = "INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION"

    # sole-discriminator coverage (registered under probe_f_repair)
    sole = Counter(s.sole_discriminator for s in specs if s.sole_discriminator)

    receipt = {
        "schema_version": "paper2-prose-transfer-confirmatory-result-v1",
        "protocol": "research/paper2_prose_transfer_v1/PROTOCOL.json",
        "confirmatory_outcomes_accessed": True,
        "grants_scientific_authority": False,
        "authority": "same-context analysis; not independent review",
        "config": {
            "confirmatory_seed": conf_seed,
            "bank": "heldout",
            "n_per_cell": args.n_per_cell,
            "n": len(tasks),
            "dev_seed": dev_seed,
            "lexical_threshold_fitted_on_dev": lex_thr,
            "dev_majority_class": dev_majority.value,
        },
        "gold_counts": dict(Counter(g.value for g in gold)),
        "sole_discriminator_coverage": dict(sole),
        "arm_scores": scores,
        "strongest_non_extraction_parent": strongest,
        "shuffle_equal_n_null": null,
        "probe_g_acceptance_test": probe_g,
        "gates": gates,
        "coordinate_errors_by_coord_and_mode": dict(coord_mode_errors),
        "all_gates_pass": all_pass,
        "terminal": terminal,
        "nonclaims": protocol["nonclaims"],
        "residual_left_open": protocol["residual_left_open"],
    }

    path = outdir / "CONFIRMATORY_RESULT.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"terminal": terminal, "probe_g": probe_g}, indent=2))
    print(json.dumps({k: v["passes"] for k, v in gates.items()}, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
