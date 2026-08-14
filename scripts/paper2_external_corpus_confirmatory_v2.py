"""Paper II external-corpus confirmatory runner (ARN v2 epoch).

Implements research/paper2_external_corpus_v1/PROTOCOL_V2_REDUCER.json exactly:
    acquisition receipt -> schema binding -> reducer admission ->
    falsifiability battery -> confirmatory gates -> terminal

Uses narrative_reducer_v2.py with typed extraction and typed_mapping.py for
type-preserving partial-credit scoring with principled abstention.

Usage (laptop billy):
    PYTHONPATH=src:. .venv/bin/python scripts/paper2_external_corpus_confirmatory_v2.py \
        --csv <ARN csv> --out research/paper2_external_corpus_v1/results_v2_reducer
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from rakl.narrative_reducer_v2 import reduce_narrative_v2, content_tokens
from rakl.reduction_validation import AdmissionVerdict, ReducerProfile, admit_reducer
from rakl.typed_mapping import typed_match_decision, MappingResult
from rakl.structure_space import MatchVerdict

PROTOCOL = "research/paper2_external_corpus_v1/PROTOCOL_V2_REDUCER.json"
PARENT_PROTOCOL = "research/paper2_external_corpus_v1/PROTOCOL.json"
SPLIT_SALT = "20260814"
PARENT_RESULT = "research/paper2_external_corpus_v1/results/RESULT.json"
SEED_BOOTSTRAP = 20260814
SEED_SCRAMBLE = 20260814
SEED_SHUFFLED_GOLD = 20260815
MDE = 0.05
BINARY_P = {"ACCEPT": 0.98, "REJECT": 0.02, "CANNOT_CHECK": 0.5}
DEV_FRACTION = 0.25
MIN_USABLE_PAIRS = 48

QUERY_KEYS = ("query",)
ANALOGY_KEYS = ("analog",)
DISTRACTOR_KEYS = ("distract", "disanalog")
BAND_KEYS = ("near", "far", "distance", "category", "type")
GROUP_KEYS = ("proverb", "system", "query_id", "source_id")


@dataclass(frozen=True)
class Pair:
    pair_id: str
    group: str
    query_text: str
    candidate_text: str
    band: str  # "near" / "far" / "unknown"
    gold: str  # "ACCEPT" / "REJECT" — never handed to arms


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(header: list[str], keys: tuple[str, ...], *, exclude: tuple[str, ...] = ()) -> list[str]:
    out = []
    for column in header:
        low = column.lower()
        if any(k in low for k in keys) and not any(e in low for e in exclude):
            out.append(column)
    return out


#: AMENDMENT_01: the ARN release is a multiple-choice CSV whose band columns
#: would collide with the M1 keyword table. Exact-name binding, frozen in
#: research/paper2_external_corpus_v1/AMENDMENT_01.json before any arm scoring.
M3_COLUMNS = {
    "query": "query_narrative",
    "first": "first_choice",
    "second": "second_choice",
    "answer": "correct_answer",
    "analogy_band": "analogy_level",
    "distractor_band": "distractor_similarity",
    "group": "proverb",
}


def bind_mapping(header: list[str]) -> dict | None:
    """Frozen resolution: exact M3 binding first, then M1 keywords. None = mismatch."""
    if set(M3_COLUMNS.values()) <= set(header):
        return {"mode": "M3", **M3_COLUMNS}
    query_cols = _resolve(header, QUERY_KEYS, exclude=("id",))
    analogy_cols = _resolve(header, ANALOGY_KEYS, exclude=DISTRACTOR_KEYS + ("id",))
    distractor_cols = _resolve(header, DISTRACTOR_KEYS, exclude=("id",))
    band_cols = _resolve(header, BAND_KEYS, exclude=("id",))
    group_cols = _resolve(header, GROUP_KEYS)
    if len(query_cols) != 1:
        return None
    if analogy_cols and distractor_cols:
        return {
            "mode": "M1",
            "query": query_cols[0],
            "analogy": analogy_cols,
            "distractor": distractor_cols,
            "band": band_cols,
            "group": group_cols[0] if len(group_cols) == 1 else None,
        }
    return None


def _band_of(column_name: str, row: dict) -> str:
    low = column_name.lower()
    if "near" in low:
        return "near"
    if "far" in low:
        return "far"
    value = str(row.get(column_name, "")).lower()
    if "near" in value:
        return "near"
    if "far" in value:
        return "far"
    return "unknown"


def build_pairs_m3(rows: list[dict], mapping: dict) -> tuple[list[Pair], int]:
    """AMENDMENT_01 multiple-choice binding. Returns (pairs, skipped_rows)."""
    band_map = {"high": "near", "low": "far"}
    pairs: list[Pair] = []
    skipped = 0
    for index, row in enumerate(rows):
        answer = str(row.get(mapping["answer"], "")).strip()
        query = str(row.get(mapping["query"], "")).strip()
        first = str(row.get(mapping["first"], "")).strip()
        second = str(row.get(mapping["second"], "")).strip()
        if answer not in {"1", "2"} or not query or not first or not second:
            skipped += 1
            continue
        analogy, distractor = (first, second) if answer == "1" else (second, first)
        group = str(row.get(mapping["group"], "")).strip() or hashlib.sha256(
            query.encode()
        ).hexdigest()
        analogy_band = str(row.get(mapping["analogy_band"], "")).strip().lower()
        distractor_band = band_map.get(
            str(row.get(mapping["distractor_band"], "")).strip().lower(), "unknown"
        )
        pairs.append(
            Pair(
                pair_id=f"r{index}:analogy",
                group=group,
                query_text=query,
                candidate_text=analogy,
                band=analogy_band if analogy_band in {"near", "far"} else "unknown",
                gold="ACCEPT",
            )
        )
        pairs.append(
            Pair(
                pair_id=f"r{index}:distractor",
                group=group,
                query_text=query,
                candidate_text=distractor,
                band=distractor_band,
                gold="REJECT",
            )
        )
    return pairs, skipped


def build_pairs(rows: list[dict], mapping: dict) -> list[Pair]:
    pairs: list[Pair] = []
    for index, row in enumerate(rows):
        query = str(row[mapping["query"]]).strip()
        if not query:
            continue
        group = (
            str(row[mapping["group"]]).strip()
            if mapping["group"]
            else hashlib.sha256(query.encode()).hexdigest()
        )
        for kind, columns, gold in (
            ("analogy", mapping["analogy"], "ACCEPT"),
            ("distractor", mapping["distractor"], "REJECT"),
        ):
            for column in columns:
                text = str(row.get(column, "")).strip()
                if not text:
                    continue
                pairs.append(
                    Pair(
                        pair_id=f"r{index}:{column}",
                        group=group,
                        query_text=query,
                        candidate_text=text,
                        band=_band_of(column, row),
                        gold=gold,
                    )
                )
    return pairs


def split_pairs(pairs: list[Pair]) -> tuple[list[Pair], list[Pair]]:
    groups = sorted(
        {p.group for p in pairs},
        key=lambda g: hashlib.sha256(f"{g}:{SPLIT_SALT}".encode()).hexdigest(),
    )
    n_dev = max(1, int(len(groups) * DEV_FRACTION))
    dev_groups = set(groups[:n_dev])
    dev = [p for p in pairs if p.group in dev_groups]
    confirm = [p for p in pairs if p.group not in dev_groups]
    return dev, confirm


# --- v2 witness decision (typed mapping + abstention) -------------------------


def witness_decision_v2(
    query_text: str,
    candidate_text: str,
    theta_w: float,
) -> tuple[str, tuple, MappingResult | None]:
    """v2 witness decision with typed mapping and abstention.

    Returns (decision, signature, mapping_result).
    """
    query_reduced = reduce_narrative_v2(query_text)
    candidate_reduced = reduce_narrative_v2(candidate_text)

    # Signature for scrambling check
    signature = (
        tuple(sorted(query_reduced.roles)),
        tuple(sorted(candidate_reduced.roles)),
    )

    # Typed mapping decision
    mapping_result = typed_match_decision(query_reduced, candidate_reduced, theta_w)

    return mapping_result.decision, signature, mapping_result


# For compatibility, alias to witness_decision (will be overridden below)
witness_decision = None  # Will use witness_decision_v2 directly


def lexical_decision(query_text: str, candidate_text: str, theta_l: float) -> str:
    a, b = set(content_tokens(query_text)), set(content_tokens(candidate_text))
    union = a | b
    jaccard = (len(a & b) / len(union)) if union else 0.0
    return "ACCEPT" if jaccard >= theta_l else "REJECT"


def band_decision(band: str) -> str:
    return "ACCEPT" if band == "near" else "REJECT"


# --- scoring -------------------------------------------------------------------


def brier(decision: str, gold: str) -> float:
    y = 1.0 if gold == "ACCEPT" else 0.0
    p = BINARY_P[decision]
    return (p - y) ** 2


def exact(decisions: list[str], golds: list[str]) -> float:
    return sum(d == g for d, g in zip(decisions, golds)) / len(golds)


def paired_advantage(control: list[str], witness: list[str], golds: list[str]) -> float:
    return statistics.fmean(brier(c, g) for c, g in zip(control, golds)) - statistics.fmean(
        brier(w, g) for w, g in zip(witness, golds)
    )


def bootstrap_ci(control: list[str], witness: list[str], golds: list[str]) -> tuple[float, float]:
    rng = random.Random(SEED_BOOTSTRAP)
    n = len(golds)
    stats: list[float] = []
    for _ in range(10_000):
        idx = [rng.randrange(n) for _ in range(n)]
        stats.append(
            paired_advantage([control[i] for i in idx], [witness[i] for i in idx], [golds[i] for i in idx])
        )
    stats.sort()
    return stats[int(0.025 * len(stats))], stats[int(0.975 * len(stats)) - 1]


def fit_theta(grid: list[float], score_fn) -> float:
    best_theta, best_score = grid[0], -1.0
    for theta in grid:  # ascending: first max = lowest theta (frozen tie-break)
        score = score_fn(theta)
        if score > best_score:
            best_theta, best_score = theta, score
    return best_theta


def _scramble_text(text: str, rng: random.Random) -> str:
    chars = list(text)
    rng.shuffle(chars)
    return "".join(chars)


# --- main ----------------------------------------------------------------------


def run(csv_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict = {
        "schema_version": "paper2-external-corpus-result-v2",
        "protocol": PROTOCOL,
        "parent_protocol": PARENT_PROTOCOL,
        "grants_scientific_authority": False,
    }

    # 1. Acquisition receipt.
    if not csv_path.exists():
        result["terminal"] = "CANNOT_CHECK__ACQUISITION"
        result["reason"] = f"missing file: {csv_path}"
        return result
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    acquisition = {
        "file": csv_path.name,
        "sha256": sha256_file(csv_path),
        "bytes": csv_path.stat().st_size,
        "header": header,
        "n_rows": len(rows),
        "first_rows_preview": [
            {k: str(v)[:120] for k, v in row.items()} for row in rows[:3]
        ],
    }
    (out_dir / "ACQUISITION_RECEIPT.json").write_text(
        json.dumps(acquisition, indent=2, ensure_ascii=False)
    )
    result["acquisition"] = {k: acquisition[k] for k in ("file", "sha256", "bytes", "n_rows")}

    # 2. Schema binding (frozen keyword resolution; fail closed).
    mapping = bind_mapping(header)
    if mapping is None:
        result["terminal"] = "CANNOT_CHECK__SCHEMA_MISMATCH"
        result["header"] = header
        return result
    (out_dir / "MAPPING.json").write_text(json.dumps(mapping, indent=2))
    result["mapping"] = mapping

    if mapping["mode"] == "M3":
        pairs, skipped = build_pairs_m3(rows, mapping)
        result["skipped_rows"] = skipped
        if rows and skipped / len(rows) > 0.05:
            result["terminal"] = "CANNOT_CHECK__SCHEMA_MISMATCH"
            result["reason"] = f"{skipped}/{len(rows)} rows outside the AMENDMENT_01 domain"
            return result
    else:
        pairs = build_pairs(rows, mapping)
    if len(pairs) < MIN_USABLE_PAIRS:
        result["terminal"] = "CANNOT_CHECK__SCHEMA_MISMATCH"
        result["reason"] = f"only {len(pairs)} usable pairs (< {MIN_USABLE_PAIRS})"
        return result
    dev, confirm = split_pairs(pairs)
    result["pairs"] = {"total": len(pairs), "dev": len(dev), "confirm": len(confirm)}

    # 3. Reducer admission (external labels: the ARN authors).
    sample_groups: list[str] = []
    sample_sources: list[str] = []
    for pair in sorted(dev + confirm, key=lambda p: hashlib.sha256(f"{p.group}:{SPLIT_SALT}".encode()).hexdigest()):
        if pair.group not in sample_groups:
            sample_groups.append(pair.group)
            sample_sources.append(pair.query_text)
        if len(sample_sources) == 8:
            break
    profile = ReducerProfile(
        reducer_id="narrative_reducer_v2",
        author="RAKL programme (same-context; LLM-assisted)",
        external_label_author="Sourati, Ilievski, Sommerauer, Jiang (ARN, TACL 2024)",
    )
    admission = admit_reducer(profile, reduce_narrative_v2, sample_sources, seed=SEED_SCRAMBLE)
    result["admission"] = {
        "verdict": admission.verdict.value,
        "admitted_kind": admission.admitted_kind.value if admission.admitted_kind else None,
        "reasons": list(admission.reasons),
        "n_sample_sources": len(sample_sources),
    }
    if admission.verdict is not AdmissionVerdict.ADMITTED:
        result["terminal"] = "ADMISSION_REJECTED"
        return result

    # 4. DEV threshold fitting (frozen grids; ascending first-max tie-break).
    def witness_dev_score(theta: float) -> float:
        decided = [
            (witness_decision_v2(p.query_text, p.candidate_text, theta)[0], p.gold) for p in dev
        ]
        decidable = [(d, g) for d, g in decided if d != "CANNOT_CHECK"]
        return exact(*zip(*decidable)) if decidable else 0.0

    theta_w = fit_theta([round(0.05 * k, 2) for k in range(1, 20)], witness_dev_score)
    theta_l = fit_theta(
        [round(0.02 * k, 2) for k in range(1, 50)],
        lambda theta: exact(
            [lexical_decision(p.query_text, p.candidate_text, theta) for p in dev],
            [p.gold for p in dev],
        ),
    )
    control_dev = {
        "lexical": [lexical_decision(p.query_text, p.candidate_text, theta_l) for p in dev],
        "band": [band_decision(p.band) for p in dev],
        "always_accept": ["ACCEPT"] * len(dev),
        "always_reject": ["REJECT"] * len(dev),
        "always_cannot_check": ["CANNOT_CHECK"] * len(dev),
    }
    dev_gold = [p.gold for p in dev]
    control_scores = {name: exact(arm, dev_gold) for name, arm in control_dev.items()}
    strongest = max(control_dev, key=lambda name: (control_scores[name], -list(control_dev).index(name)))
    result["dev_fit"] = {"theta_w": theta_w, "theta_l": theta_l,
                        "control_dev_exact": control_scores, "strongest_control": strongest}

    # 5. CONFIRM arm outputs (single outcome access).
    confirm_gold = [p.gold for p in confirm]
    witness_out = [witness_decision_v2(p.query_text, p.candidate_text, theta_w) for p in confirm]
    witness_conf = [d[0] for d in witness_out]
    witness_sigs = [d[1] for d in witness_out]
    witness_results = [d[2] for d in witness_out]  # MappingResult for telemetry
    controls_conf = {
        "lexical": [lexical_decision(p.query_text, p.candidate_text, theta_l) for p in confirm],
        "band": [band_decision(p.band) for p in confirm],
        "always_accept": ["ACCEPT"] * len(confirm),
        "always_reject": ["REJECT"] * len(confirm),
        "always_cannot_check": ["CANNOT_CHECK"] * len(confirm),
    }
    strongest_conf = controls_conf[strongest]

    # 6. Battery.
    battery: dict = {"probe_H": "N/A: no self-authored renderer; third-party surfaces"}
    # B1: structural — arm callables above receive texts/band only (no gold arg).
    battery["B1_gold_arm_distinctness"] = "pass (arms receive texts/band only by signature)"
    # B2: text destruction.
    changed = 0
    scrambled_decisions: list[str] = []
    for pair, signature in zip(confirm, witness_sigs):
        rng = random.Random(f"{SEED_SCRAMBLE}:{pair.pair_id}")
        scrambled_query = _scramble_text(pair.query_text, rng)
        scrambled_candidate = _scramble_text(pair.candidate_text, rng)
        decision_s, signature_s, _ = witness_decision_v2(scrambled_query, scrambled_candidate, theta_w)
        scrambled_decisions.append(decision_s)
        original_decision = witness_conf[len(scrambled_decisions) - 1]
        if (decision_s, signature_s) != (original_decision, signature):
            changed += 1
    null_rng = random.Random(SEED_SHUFFLED_GOLD)
    null_exacts = []
    for _ in range(200):
        shuffled = confirm_gold[:]
        null_rng.shuffle(shuffled)
        null_exacts.append(exact(witness_conf, shuffled))
    null_exacts.sort()
    null_upper = null_exacts[int(0.975 * len(null_exacts)) - 1]
    scrambled_exact = exact(scrambled_decisions, confirm_gold)
    battery["B2_text_destruction"] = {
        "changed_fraction": changed / len(confirm),
        "scrambled_exact": scrambled_exact,
        "null_upper_975": null_upper,
        "pass": (changed / len(confirm)) >= 0.5 and scrambled_exact <= null_upper,
    }
    # B3: shuffled-gold negative control must FAIL G1.
    shuffled_gold = confirm_gold[:]
    random.Random(SEED_SHUFFLED_GOLD).shuffle(shuffled_gold)
    sg_advantage = paired_advantage(strongest_conf, witness_conf, shuffled_gold)
    sg_lo, sg_hi = bootstrap_ci(strongest_conf, witness_conf, shuffled_gold)
    battery["B3_shuffled_gold"] = {
        "advantage": sg_advantage, "ci": [sg_lo, sg_hi],
        "g1_fails_as_required": not (sg_advantage >= MDE and sg_lo > 0),
    }
    # B4: trivial arms must not attain G2.
    def joint(arm: list[str]) -> tuple[float, float]:
        valid = [d for d, g in zip(arm, confirm_gold) if g == "ACCEPT"]
        invalid = [d for d, g in zip(arm, confirm_gold) if g == "REJECT"]
        va = sum(d == "ACCEPT" for d in valid) / len(valid) if valid else 0.0
        fa = sum(d == "ACCEPT" for d in invalid) / len(invalid) if invalid else 0.0
        return va, fa

    trivial_joint = {name: joint(controls_conf[name]) for name in ("always_accept", "always_reject", "always_cannot_check")}
    battery["B4_trivial_floor"] = {
        name: {"valid_accept": va, "invalid_false_accept": fa,
               "attains_G2": va >= 0.60 and fa <= 0.20}
        for name, (va, fa) in trivial_joint.items()
    }
    battery["B4_pass"] = not any(v["attains_G2"] for v in battery["B4_trivial_floor"].values())
    # B5: paired variance.
    witness_losses = [brier(d, g) for d, g in zip(witness_conf, confirm_gold)]
    control_losses = [brier(d, g) for d, g in zip(strongest_conf, confirm_gold)]
    battery["B5_paired_variance"] = {
        "witness_var": statistics.pvariance(witness_losses),
        "control_var": statistics.pvariance(control_losses),
        "pass": statistics.pvariance(witness_losses) > 0 and statistics.pvariance(control_losses) > 0,
    }
    result["battery"] = battery
    battery_pass = (
        battery["B2_text_destruction"]["pass"]
        and battery["B3_shuffled_gold"]["g1_fails_as_required"]
        and battery["B4_pass"]
        and battery["B5_paired_variance"]["pass"]
    )
    if not battery_pass:
        result["terminal"] = "BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE"
        return result

    # 7. Gates.
    advantage = paired_advantage(strongest_conf, witness_conf, confirm_gold)
    lo, hi = bootstrap_ci(strongest_conf, witness_conf, confirm_gold)
    va, fa = joint(witness_conf)
    cc_rate = witness_conf.count("CANNOT_CHECK") / len(confirm)

    # Abstention breakdown (v2 telemetry)
    abstention_breakdown = {
        "insufficient_extraction_evidence": 0,
        "degenerate_type_coverage": 0,
        "low_mapping_confidence": 0,
        "total": cc_rate,
    }
    for wr in witness_results:
        if wr and wr.abstention_reason:
            if "insufficient_extraction_evidence" in wr.abstention_reason:
                abstention_breakdown["insufficient_extraction_evidence"] += 1
            elif "degenerate_type_coverage" in wr.abstention_reason:
                abstention_breakdown["degenerate_type_coverage"] += 1
            elif "low_mapping_confidence" in wr.abstention_reason:
                abstention_breakdown["low_mapping_confidence"] += 1

    def quadrant(band: str, gold: str) -> dict:
        arm = [d for d, p in zip(witness_conf, confirm) if p.band == band and p.gold == gold]
        if not arm:
            return {"n": 0}
        accept_rate = sum(d == "ACCEPT" for d in arm) / len(arm)
        return {"n": len(arm), "accept_rate": accept_rate,
                "cannot_check_rate": sum(d == "CANNOT_CHECK" for d in arm) / len(arm)}

    result["gates"] = {
        "G1_advantage": {"advantage": advantage, "ci": [lo, hi], "mde": MDE,
                          "pass": advantage >= MDE and lo > 0},
        "G2_joint": {"valid_accept": va, "invalid_false_accept": fa,
                      "pass": va >= 0.60 and fa <= 0.20},
        "G3_abstention": {
            "cannot_check_rate": cc_rate,
            "dominant": cc_rate > 0.50,
            "breakdown": abstention_breakdown,
        },
        "quadrants": {
            "far_analogy_Q2_analogue": quadrant("far", "ACCEPT"),
            "near_analogy": quadrant("near", "ACCEPT"),
            "far_distractor": quadrant("far", "REJECT"),
            "near_distractor_Q3_analogue": quadrant("near", "REJECT"),
        },
        "arm_confirm_exact": {
            "witness": exact(witness_conf, confirm_gold),
            **{name: exact(arm, confirm_gold) for name, arm in controls_conf.items()},
        },
    }

    # Parent comparison (v2 telemetry)
    parent_comparison = {}
    try:
        parent_path = Path(PARENT_RESULT)
        if parent_path.exists():
            parent_data = json.loads(parent_path.read_text())
            parent_comparison = {
                "parent_witness_exact": parent_data.get("gates", {}).get("arm_confirm_exact", {}).get("witness"),
                "parent_band_exact": parent_data.get("gates", {}).get("arm_confirm_exact", {}).get("band"),
                "parent_advantage": parent_data.get("gates", {}).get("G1_advantage", {}).get("advantage"),
                "parent_ci": parent_data.get("gates", {}).get("G1_advantage", {}).get("ci"),
            }
    except Exception:
        parent_comparison = {"note": "Could not load parent result"}

    result["parent_comparison"] = parent_comparison

    g1, g2 = result["gates"]["G1_advantage"]["pass"], result["gates"]["G2_joint"]["pass"]
    if g1 and g2 and cc_rate <= 0.50:
        result["terminal"] = "POSITIVE_SCOPED__EXTERNAL_LABEL"
    elif hi < MDE or not g2 or cc_rate > 0.50:
        result["terminal"] = "NEGATIVE__CAPABILITY_ABSENT"
        reasons = []
        if hi < MDE:
            reasons.append("G1 CI upper bound below MDE")
        if not g2:
            reasons.append("G2 joint property failed")
        if cc_rate > 0.50:
            reasons.append("ABSTENTION_DOMINANT")
        result["negative_reasons"] = reasons
    else:
        result["terminal"] = "INDETERMINATE__CI_STRADDLES_MDE"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.csv, args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "RESULT.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps({"terminal": result.get("terminal")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
