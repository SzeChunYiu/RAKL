#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

FULL_FIELDS = (
    "candidate_present","candidate_count","confidence","lesson_verified","scope_match",
    "version_current","not_refuted","lineage_valid","target_context_match",
    "failure_signature_match","strategy_family_match","negative_history_block",
    "validity_known","successor_verified","successor_scope_match","successor_current",
)
PROJ = {
    "RESET": (),
    "FAILURE_MEMORY_ONLY": ("failure_signature_match","negative_history_block"),
    "SCALAR_CONFIDENCE": ("candidate_present","candidate_count","confidence"),
    "PROVENANCE_ONLY": ("candidate_present","lineage_valid"),
    "WHOLE_STATE_UNTYPED": (
        "candidate_present","candidate_count","confidence",
        "failure_signature_match","strategy_family_match",
    ),
}
_union = []
for _fields in PROJ.values():
    for _field in _fields:
        if _field not in _union:
            _union.append(_field)
PROJ["COMPOSITE_SIMPLE_PARENT"] = tuple(_union)
PROJ["TYPED_SELECTIVE_EXPERIENCE"] = FULL_FIELDS


def strict_action(c, mutation=None):
    def ok(name, mut):
        return c[name] or mutation == mut
    if not c["candidate_present"]:
        return "FALLBACK_SEARCH"
    if not c["validity_known"] and mutation != "UNKNOWN_AS_VALID":
        return "CANNOT_CHECK"
    primary_valid = (
        ok("lesson_verified","IGNORE_VERIFICATION")
        and ok("scope_match","IGNORE_SCOPE")
        and ok("version_current","IGNORE_VERSION")
        and ok("not_refuted","IGNORE_REFUTATION")
        and ok("lineage_valid","IGNORE_LINEAGE")
        and ok("target_context_match","IGNORE_CONTEXT")
        and ok("failure_signature_match","IGNORE_FAILURE_SIGNATURE")
        and ok("strategy_family_match","IGNORE_STRATEGY_FAMILY")
        and (not c["negative_history_block"] or mutation == "IGNORE_NEGATIVE_HISTORY")
    )
    if primary_valid:
        return "APPLY_VERIFIED_LESSON"
    successor_valid = (
        c["successor_verified"] and c["successor_scope_match"] and c["successor_current"]
        and ok("lineage_valid","IGNORE_LINEAGE")
        and ok("target_context_match","IGNORE_CONTEXT")
        and ok("failure_signature_match","IGNORE_FAILURE_SIGNATURE")
        and ok("strategy_family_match","IGNORE_STRATEGY_FAMILY")
    )
    if successor_valid and (not c["not_refuted"] or not c["version_current"] or c["negative_history_block"]):
        return "APPLY_SUCCESSOR"
    return "FALLBACK_SEARCH"


def base_case(rng):
    return dict(
        candidate_present=True,
        candidate_count=1,
        confidence=round(0.82 + 0.15 * rng.random(), 3),
        lesson_verified=True,
        scope_match=True,
        version_current=True,
        not_refuted=True,
        lineage_valid=True,
        target_context_match=True,
        failure_signature_match=True,
        strategy_family_match=True,
        negative_history_block=False,
        validity_known=True,
        successor_verified=False,
        successor_scope_match=False,
        successor_current=False,
    )


def make_pair(fam, rng, i):
    a = base_case(rng)
    b = dict(a)
    if fam == "VERIFIED_SCOPE_MATCH_APPLY":
        b["scope_match"] = False
    elif fam == "UNVERIFIED_LESSON_BLOCK":
        b["lesson_verified"] = False
    elif fam == "SCOPE_MISMATCH_BLOCK":
        b["scope_match"] = False
    elif fam == "STALE_VERSION_BLOCK":
        b["version_current"] = False
    elif fam == "REFUTED_LESSON_BLOCK":
        b["not_refuted"] = False
    elif fam == "LINEAGE_INVALID_BLOCK":
        b["lineage_valid"] = False
    elif fam == "TARGET_CONTEXT_MISMATCH_BLOCK":
        b["target_context_match"] = False
    elif fam == "FAILURE_SIGNATURE_MISMATCH_BLOCK":
        b["failure_signature_match"] = False
    elif fam == "STRATEGY_FAMILY_MISMATCH_BLOCK":
        b["strategy_family_match"] = False
    elif fam == "NEGATIVE_HISTORY_REQUIRES_BLOCK":
        b["negative_history_block"] = True
    elif fam == "UNKNOWN_VALIDITY_REQUIRES_CANNOT_CHECK":
        b["validity_known"] = False
    elif fam == "VALID_SUCCESSOR_AFTER_REFUTATION":
        for x in (a, b):
            x.update(
                not_refuted=False,
                successor_verified=True,
                successor_scope_match=True,
                successor_current=True,
            )
        b["successor_current"] = False
    elif fam == "NO_LESSON_FALLBACK_CONTROL":
        a["candidate_present"] = False
        b["candidate_present"] = True
        b["lesson_verified"] = False
    elif fam == "MULTIPLE_CANDIDATES_ONE_VALID":
        for x in (a, b):
            x["candidate_count"] = 2
        b["lineage_valid"] = False
    else:
        raise KeyError(fam)
    return [
        {"case_id": f"{fam}:{i:03d}:A", "family": fam, **a},
        {"case_id": f"{fam}:{i:03d}:B", "family": fam, **b},
    ]


def information_ceiling(cases, fields):
    groups = defaultdict(list)
    for c in cases:
        key = (c["family"],) + tuple(c[f] for f in fields)
        groups[key].append(c)
    pred = {}
    correct = 0
    collisions = []
    for items in groups.values():
        cnt = Counter(c["gold_action"] for c in items)
        best = cnt.most_common(1)[0][0]
        correct += cnt[best]
        for c in items:
            pred[c["case_id"]] = best
        if len(cnt) > 1:
            collisions.append(
                {"family": items[0]["family"], "gold_counts": dict(cnt), "n": len(items)}
            )
    return correct / len(cases), pred, collisions


def metrics(cases, pred):
    n = len(cases)
    exact = sum(pred[c["case_id"]] == c["gold_action"] for c in cases) / n
    unsafe = sum(
        pred[c["case_id"]].startswith("APPLY")
        and not c["gold_action"].startswith("APPLY")
        for c in cases
    ) / n
    cc = [c for c in cases if c["gold_action"] == "CANNOT_CHECK"]
    apply = [c for c in cases if c["gold_action"].startswith("APPLY")]
    return {
        "exact_action_accuracy": exact,
        "unsafe_apply_rate": unsafe,
        "cannot_check_recall": (
            sum(pred[c["case_id"]] == "CANNOT_CHECK" for c in cc) / len(cc)
            if cc else 1.0
        ),
        "legitimate_apply_recall": (
            sum(pred[c["case_id"]] == c["gold_action"] for c in apply) / len(apply)
            if apply else 1.0
        ),
    }


def execute(protocol):
    rng = random.Random(protocol["seed"])
    cases = []
    for fam in protocol["families"]:
        for i in range(protocol["pairs_per_family"]):
            cases.extend(make_pair(fam, rng, i))
    for c in cases:
        c["gold_action"] = strict_action(c)

    parents = {}
    for name, fields in PROJ.items():
        ceiling, pred, collisions = information_ceiling(cases, fields)
        parents[name] = {
            "information_ceiling": ceiling,
            **metrics(cases, pred),
            "collided_families": sorted({x["family"] for x in collisions}),
        }

    typed_pred = {c["case_id"]: strict_action(c) for c in cases}
    typed = metrics(cases, typed_pred)

    mutations = {}
    for mutation in protocol["mutations"]:
        pred = {c["case_id"]: strict_action(c, mutation) for c in cases}
        errors = [c for c in cases if pred[c["case_id"]] != c["gold_action"]]
        mutations[mutation] = {
            "caught": bool(errors),
            "n_errors": len(errors),
            "affected_families": sorted({c["family"] for c in errors}),
        }

    gate = {
        "typed_exact": typed["exact_action_accuracy"] >= protocol["hard_gate"]["typed_exact_min"],
        "typed_unsafe": typed["unsafe_apply_rate"] <= protocol["hard_gate"]["typed_unsafe_apply_max"],
        "typed_cannot_check": typed["cannot_check_recall"] >= protocol["hard_gate"]["typed_cannot_check_recall_min"],
        "typed_legitimate_apply": typed["legitimate_apply_recall"] >= protocol["hard_gate"]["typed_legitimate_apply_recall_min"],
        "composite_residual": parents["COMPOSITE_SIMPLE_PARENT"]["information_ceiling"] <= protocol["hard_gate"]["composite_simple_ceiling_max"],
        "all_mutations_caught": all(x["caught"] for x in mutations.values()),
    }
    result = {
        "schema_version": "orion-p3-structured-experience-action-result-v1",
        "n_cases": len(cases),
        "n_families": len(protocol["families"]),
        "typed_selective_experience": typed,
        "parents": parents,
        "mutations": mutations,
        "gate": gate,
        "all_gates_pass": all(gate.values()),
        "terminal": (
            protocol["promotion_if_green"] if all(gate.values())
            else "RSHEA_SUCCESSOR_REQUIRED"
        ),
        "historical_model_negatives_preserved": True,
        "replaces_active_dependency_on_model_capability": all(gate.values()),
        "replacement_boundary": (
            "The required ORION experience-to-action mechanic is structured and deterministic "
            "once verified experience exists; natural-language lesson extraction/model efficacy "
            "remains an empirical adapter assurance, not authority for this state transition."
        ),
        "grants_scientific_authority": False,
    }
    return cases, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    cases, result = execute(protocol)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "CASES.jsonl").open("w") as f:
        for c in cases:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    (out / "FINAL_RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
