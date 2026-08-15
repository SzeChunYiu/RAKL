#!/usr/bin/env python3
"""Reconstruct and execute the frozen 21-family / 2,688-case router validation.

The numbers this protocol's result was quoted with
(``research/paper3_publication_closeout_v1/FINAL_RECEIPT.json :: structured_validation``)
were never produced by any artifact; the repository audit
``research/paper3_gate_falsifiability_audit_v1/UNREPRODUCIBLE_V2_RESULT.json``
recorded that as terminal CANNOT_CHECK. This is the missing harness.

Nothing here can *re*-produce anything --- the original instrument never
existed. What this measures is what a faithful reconstruction under the frozen
protocol yields. Agreement with the quoted prose would be corroboration of the
values, not a receipt for a run that never happened.

Three things are audited that the predicted-defective ancestor did not do:

1.  **Severance.** Gold is committed by the generator from design intent and is
    structurally invisible to the candidate (AST scan + projected record +
    probe-target assertion). The sibling harness assigned
    ``gold_action = strict_action(c)`` and then predicted ``strict_action(c)``,
    so four of six gate conditions were satisfied by identity.
2.  **Per-condition falsifiability.** Each of the six registered gate
    conditions is probed on its own; auditing the conjunction would let live
    conditions mask dead ones.
3.  **Mutant separation.** Candidate mutants are chosen to move the four strict
    conditions *independently* where that is possible, and conditions no mutant
    can move are reported NON_FALSIFIABLE rather than passing.

Run: ``python3 experiments/paper3/router_v2/run_router_v2_reconstruction.py \
        --outdir research/paper3_router_v2_reproduction_v1``
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable, Iterable, Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from rakl.gate_falsifiability import (  # noqa: E402
    GateFalsifiability,
    audit_gate,
    drop_fraction,
    shuffle_field,
)

import route_case_generator as GEN  # noqa: E402
import strict_typed_router as CAND  # noqa: E402

PROTOCOL_PATH = ROOT / "research" / "paper3_publication_validation_v2" / "PROTOCOL_FREEZE.json"
QUOTED_PATH = ROOT / "research" / "paper3_publication_closeout_v1" / "FINAL_RECEIPT.json"

CONCRETE = ("SEARCH", "JUMP", "GLUE", "LIFT")
CANNOT_CHECK = "CANNOT_CHECK"

#: Names whose presence in the candidate module would mean gold could reach it.
FORBIDDEN_IN_CANDIDATE = ("gold_route", "gold_trace", "gold_source", "family", "pair_index")


# --- 1. static severance audit ------------------------------------------------------


def _module_names(path: Path) -> tuple[set[str], set[str]]:
    """Imports, and every identifier or literal key the module's *code* references.

    Docstrings are excluded: this file's own prose names the forbidden fields in
    order to explain the contract, and prose is not a data path.
    """
    tree = ast.parse(path.read_text())
    docstrings = {
        ast.get_docstring(n, clean=False)
        for n in ast.walk(tree)
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    imports: set[str] = set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value not in docstrings:
                names.add(node.value)
    return imports, names


def severance_audit() -> dict[str, Any]:
    """Prove, statically, that gold cannot reach the candidate."""
    cand_imports, cand_names = _module_names(HERE / "strict_typed_router.py")
    gen_imports, _ = _module_names(HERE / "route_case_generator.py")

    leaked = sorted(n for n in FORBIDDEN_IN_CANDIDATE if n in cand_names)
    candidate_imports_generator = any("route_case_generator" in i for i in cand_imports)
    generator_imports_candidate = any("strict_typed_router" in i for i in gen_imports)

    result = {
        "method": "ast scan of both modules plus a runtime projection assertion",
        "candidate_module": "experiments/paper3/router_v2/strict_typed_router.py",
        "gold_module": "experiments/paper3/router_v2/route_case_generator.py",
        "gold_source": "GENERATOR_DESIGN_INTENT (committed at construction, never recomputed)",
        "candidate_imports_generator": candidate_imports_generator,
        "generator_imports_candidate": generator_imports_candidate,
        "forbidden_names_found_in_candidate": leaked,
        "candidate_visible_field_count": len(GEN.CANDIDATE_VISIBLE_FIELDS),
        "severed": (
            not candidate_imports_generator and not generator_imports_candidate and not leaked
        ),
    }
    if not result["severed"]:
        raise SystemExit(f"SEVERANCE AUDIT FAILED: {json.dumps(result, indent=2)}")
    return result


# --- 2. arms and metrics ------------------------------------------------------------


def candidate_predictions(
    cases: Sequence[dict], mutation: str | None = None
) -> dict[str, tuple[str, tuple[str, ...]]]:
    out = {}
    for case in cases:
        view = GEN.candidate_view(case)
        # Runtime severance assertion: the candidate is handed nothing else.
        assert set(view) == set(GEN.CANDIDATE_VISIBLE_FIELDS)
        out[case["case_id"]] = CAND.strict_route(view, mutation)
    return out


def metrics(cases: Sequence[dict], pred: dict[str, tuple[str, tuple[str, ...]]]) -> dict[str, float]:
    n = len(cases)
    exact = 0
    unsafe = 0
    cc_total = cc_hit = 0
    viable_total = viable_hit = 0
    for case in cases:
        route, trace = pred[case["case_id"]]
        gold_route = case["gold_route"]
        gold_trace = tuple(case["gold_trace"])
        if route == gold_route and trace == gold_trace:
            exact += 1
        if route != CANNOT_CHECK and route != gold_route:
            unsafe += 1
        if gold_route == CANNOT_CHECK:
            cc_total += 1
            cc_hit += route == CANNOT_CHECK
        else:
            viable_total += 1
            viable_hit += route == gold_route
    if not cc_total or not viable_total:
        # A subset with no CANNOT_CHECK gold (or no viable gold) makes the
        # corresponding recall undefined. Raising makes the probe CANNOT_CHECK
        # instead of silently manufacturing a gate flip out of a nan comparison.
        raise ValueError("undefined recall: perturbed evidence lacks one gold class")
    return {
        "route_plus_negative_trace_exact": exact / n,
        "unsafe_route_rate": unsafe / n,
        "cannot_check_recall": cc_hit / cc_total,
        "viable_route_recall": viable_hit / viable_total,
    }


def _bucket(value: float) -> int:
    return min(3, int(float(value) * 4))


def _stage_signature(r: dict, s: str) -> str:
    return r[f"{s}_audit"] if r[f"{s}_candidate_present"] else "ABSENT"


PROJECTIONS: dict[str, Callable[[dict], tuple]] = {
    # what a similarity-only method sees
    "SEMANTIC_ONLY": lambda r: (_bucket(r["semantic_similarity"]), bool(r["domain_match"])),
    # what a structural-rank method sees: which stages offer candidates at all
    "STRUCTURAL_RANK_ONLY": lambda r: tuple(
        bool(r[f"{s}_candidate_present"]) for s in GEN.STAGES
    ),
    # a method that reads canonical audit verdicts but has no typed rejection
    # certificates, bindings, vetoes or lift preconditions
    "FAIL_MEANS_FALLTHROUGH": lambda r: tuple(_stage_signature(r, s) for s in GEN.STAGES)
    + (bool(r["exhaustion_witness_present"]),),
}
PROJECTIONS["COMPOSITE_SIMPLE_PARENT"] = lambda r: (
    PROJECTIONS["SEMANTIC_ONLY"](r)
    + PROJECTIONS["STRUCTURAL_RANK_ONLY"](r)
    + PROJECTIONS["FAIL_MEANS_FALLTHROUGH"](r)
)


def _best_label(counts: dict[str, int]) -> str:
    """Majority gold, ties broken fail-closed toward CANNOT_CHECK.

    Fail-closed tie-breaking is the *strongest fair* form of the parent: it
    minimises the parent's unsafe rate, so the residual reported against it is
    not an artifact of a hostile tie rule.
    """
    best = max(counts.values())
    tied = sorted(k for k, v in counts.items() if v == best)
    return CANNOT_CHECK if CANNOT_CHECK in tied else tied[0]


def parent_arm(cases: Sequence[dict], projection: Callable[[dict], tuple]) -> dict[str, Any]:
    """Information ceiling of a projection, resubstitution and leave-one-out.

    Resubstitution rewards singleton signature groups, so it inflates the
    parent's ceiling on high-cardinality projections. Leave-one-out does not,
    and is the value the gate uses. Both are reported.
    """
    groups: dict[tuple, dict[str, int]] = {}
    for case in cases:
        groups.setdefault(projection(case), {}).setdefault(case["gold_route"], 0)
        groups[projection(case)][case["gold_route"]] += 1

    resub_hit = loo_hit = unsafe = 0
    for case in cases:
        counts = groups[projection(case)]
        gold = case["gold_route"]
        resub_hit += _best_label(counts) == gold
        held = dict(counts)
        held[gold] -= 1
        if held[gold] == 0:
            del held[gold]
        pred = _best_label(held) if held else CANNOT_CHECK
        loo_hit += pred == gold
        if pred != CANNOT_CHECK and pred != gold:
            unsafe += 1
    n = len(cases)
    return {
        "n_signature_groups": len(groups),
        "information_ceiling_resubstitution": resub_hit / n,
        "information_ceiling_leave_one_out": loo_hit / n,
        "unsafe_route_rate_leave_one_out": unsafe / n,
    }


def mutation_catches(cases: Sequence[dict], mutations: Iterable[str]) -> dict[str, dict[str, Any]]:
    """A mutation is caught iff its predictions differ from gold somewhere."""
    out: dict[str, dict[str, Any]] = {}
    for mutation in mutations:
        pred = candidate_predictions(cases, mutation)
        families: set[str] = set()
        n_diff = 0
        for case in cases:
            route, trace = pred[case["case_id"]]
            if route != case["gold_route"] or trace != tuple(case["gold_trace"]):
                n_diff += 1
                families.add(case["family"])
        out[mutation] = {
            "caught": n_diff > 0,
            "n_cases_diverging_from_gold": n_diff,
            "catching_families": sorted(families),
        }
    return out


# --- 3. the six registered gate conditions ------------------------------------------


def evaluate(cases: Sequence[dict]) -> dict[str, Any]:
    pred = candidate_predictions(cases)
    m = metrics(cases, pred)
    composite = parent_arm(cases, PROJECTIONS["COMPOSITE_SIMPLE_PARENT"])
    catches = mutation_catches(cases, CAND.REGISTERED_MUTATIONS)
    return {"strict": m, "composite": composite, "mutation_catches": catches}


def gate_conditions(gate: dict) -> dict[str, Callable[[Sequence[object]], bool]]:
    """Each condition computes only what it needs; the conjunction is never probed."""

    def _strict(cases):  # noqa: ANN001
        return metrics(cases, candidate_predictions(cases))

    def c1(cases):  # noqa: ANN001
        return _strict(cases)["route_plus_negative_trace_exact"] >= gate["strict_exact_min"]

    def c2(cases):  # noqa: ANN001
        return _strict(cases)["unsafe_route_rate"] <= gate["strict_unsafe_max"]

    def c3(cases):  # noqa: ANN001
        return _strict(cases)["cannot_check_recall"] >= gate["strict_cannot_check_recall_min"]

    def c4(cases):  # noqa: ANN001
        return _strict(cases)["viable_route_recall"] >= gate["strict_legal_route_recall_min"]

    def c5(cases):  # noqa: ANN001
        ceiling = parent_arm(cases, PROJECTIONS["COMPOSITE_SIMPLE_PARENT"])[
            "information_ceiling_leave_one_out"
        ]
        return ceiling <= gate["composite_information_ceiling_max"]

    def c6(cases):  # noqa: ANN001
        return all(
            v["caught"] for v in mutation_catches(cases, CAND.REGISTERED_MUTATIONS).values()
        )

    return {
        "strict_exact": c1,
        "strict_unsafe": c2,
        "strict_cannot_check_recall": c3,
        "strict_legal_route_recall": c4,
        "composite_information_ceiling": c5,
        "all_mutations_caught": c6,
    }


# --- 4. evidence perturbations ------------------------------------------------------


def randomize_decision_fields(evidence, rng):  # noqa: ANN001
    rows = [dict(r) for r in evidence]
    for row in rows:
        for field in GEN.CANDIDATE_VISIBLE_FIELDS:
            current = row[field]
            if isinstance(current, bool):
                row[field] = rng.random() < 0.5
            elif field == "repeated_residual_count":
                row[field] = rng.randrange(0, 4)
    return rows


def drop_families(fraction: float):
    def perturb(evidence, rng):  # noqa: ANN001
        families = sorted({r["family"] for r in evidence})
        keep = set(rng.sample(families, max(2, int(len(families) * (1.0 - fraction)))))
        return [r for r in evidence if r["family"] in keep]

    return perturb


def keep_only(family: str):
    def perturb(evidence, rng):  # noqa: ANN001, ARG001
        return [r for r in evidence if r["family"] == family]

    return perturb


def drop_family(family: str):
    def perturb(evidence, rng):  # noqa: ANN001, ARG001
        return [r for r in evidence if r["family"] != family]

    return perturb


def build_perturbations(unique_catchers: dict[str, str]) -> dict[str, Any]:
    probes: dict[str, Any] = {
        "shuffle_search_audit": shuffle_field("search_audit"),
        "shuffle_jump_mapping_valid": shuffle_field("jump_mapping_valid"),
        "shuffle_negative_history_retained": shuffle_field("negative_history_retained"),
        "shuffle_repeated_residual_count": shuffle_field("repeated_residual_count"),
        "randomize_all_candidate_visible_fields": randomize_decision_fields,
        "drop_one_third_of_families": drop_families(0.34),
        "drop_half_the_cases": drop_fraction(0.5),
        # collapses family diversity: the composite projection may become
        # sufficient on a single family, which is the only way its ceiling
        # condition can be pushed past its threshold.
        "keep_only_DIRECT_SEARCH_VALID": keep_only("DIRECT_SEARCH_VALID"),
        "keep_only_ALL_STRUCTURAL_REJECTED_LIFT": keep_only("ALL_STRUCTURAL_REJECTED_LIFT"),
        # declared decorative: no rule reads these
        "shuffle_semantic_similarity": shuffle_field("semantic_similarity"),
        "shuffle_candidate_count": shuffle_field("candidate_count"),
    }
    # Re-test the recorded v1 failure mode directly: remove the only family that
    # makes a registered mutation load-bearing and the mutation goes uncaught.
    for mutation, family in sorted(unique_catchers.items()):
        probes[f"drop_sole_catcher_of_{mutation}"] = drop_family(family)
    return probes


DECORATIVE_PROBES = frozenset({"shuffle_semantic_similarity", "shuffle_candidate_count"})


def assert_probes_never_touch_gold(probes: dict[str, Any]) -> list[str]:
    """A probe that perturbs gold would manufacture falsifiability."""
    offenders = [p for p in probes if "gold" in p]
    if offenders:
        raise SystemExit(f"PROBE AUDIT FAILED: probes target gold: {offenders}")
    return sorted(probes)


# --- 5. candidate-mutant separation table -------------------------------------------


def mutant_condition_table(cases: Sequence[dict], gate: dict) -> dict[str, Any]:
    """Which registered gate conditions each candidate mutant actually moves."""
    baseline_composite = parent_arm(cases, PROJECTIONS["COMPOSITE_SIMPLE_PARENT"])[
        "information_ceiling_leave_one_out"
    ]
    table: dict[str, Any] = {}
    for mutant in CAND.ALL_MUTANTS:
        pred = candidate_predictions(cases, mutant)
        m = metrics(cases, pred)
        table[mutant] = {
            "registered": mutant in CAND.REGISTERED_MUTATIONS,
            "metrics": m,
            "breaks": {
                "strict_exact": m["route_plus_negative_trace_exact"] < gate["strict_exact_min"],
                "strict_unsafe": m["unsafe_route_rate"] > gate["strict_unsafe_max"],
                "strict_cannot_check_recall": m["cannot_check_recall"]
                < gate["strict_cannot_check_recall_min"],
                "strict_legal_route_recall": m["viable_route_recall"]
                < gate["strict_legal_route_recall_min"],
                # a candidate mutant cannot move a parent-projection property
                "composite_information_ceiling": baseline_composite
                > gate["composite_information_ceiling_max"],
            },
        }
    return table


# --- main ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--trials", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260815)
    args = ap.parse_args()

    severance = severance_audit()

    protocol = json.loads(PROTOCOL_PATH.read_text())
    gate = protocol["gate"]
    quoted = json.loads(QUOTED_PATH.read_text())["structured_validation"]

    if sorted(GEN.FAMILIES) != sorted(protocol["families"]):
        raise SystemExit(
            "FAMILY SET MISMATCH vs frozen protocol: "
            f"missing={sorted(set(protocol['families']) - set(GEN.FAMILIES))} "
            f"extra={sorted(set(GEN.FAMILIES) - set(protocol['families']))}"
        )
    if sorted(CAND.REGISTERED_MUTATIONS) != sorted(protocol["registered_mutations"]):
        raise SystemExit("MUTATION SET MISMATCH vs frozen protocol")

    cases = GEN.build_cases(protocol["seed"], protocol["pairs_per_family"])
    n_cases = len(cases)
    n_families = len({c["family"] for c in cases})

    baseline = evaluate(cases)
    parents = {name: parent_arm(cases, proj) for name, proj in PROJECTIONS.items()}
    baseline_conditions = {name: bool(fn(cases)) for name, fn in gate_conditions(gate).items()}

    catches = baseline["mutation_catches"]
    unique_catchers = {
        mutation: info["catching_families"][0]
        for mutation, info in catches.items()
        if len(info["catching_families"]) == 1
    }
    probes = build_perturbations(unique_catchers)
    probe_ids = assert_probes_never_touch_gold(probes)

    reports = {
        name: audit_gate(
            fn,
            cases,
            gate_id=f"router_v2_reconstruction::{name}",
            perturbations=probes,
            trials=args.trials,
            seed=args.seed,
        )
        for name, fn in gate_conditions(gate).items()
    }

    live = sorted(n for n, r in reports.items() if r.verdict is GateFalsifiability.FALSIFIABLE)
    dead = sorted(n for n, r in reports.items() if r.verdict is GateFalsifiability.NON_FALSIFIABLE)
    unknown = sorted(n for n, r in reports.items() if r.verdict is GateFalsifiability.CANNOT_CHECK)
    if not live:
        raise SystemExit(
            "CONTROL FAILED: no gate condition was falsifiable under this probe set; "
            "no NON_FALSIFIABLE verdict would be reportable"
        )

    mutants = mutant_condition_table(cases, gate)
    moved_by_mutant = {
        cond: sorted(m for m, info in mutants.items() if info["breaks"][cond])
        for cond in (
            "strict_exact",
            "strict_unsafe",
            "strict_cannot_check_recall",
            "strict_legal_route_recall",
            "composite_information_ceiling",
        )
    }

    measured = {
        "n_cases": n_cases,
        "n_families": n_families,
        "route_plus_negative_trace_exact": baseline["strict"]["route_plus_negative_trace_exact"],
        "unsafe_route_rate": baseline["strict"]["unsafe_route_rate"],
        "cannot_check_recall": baseline["strict"]["cannot_check_recall"],
        "viable_route_recall": baseline["strict"]["viable_route_recall"],
        "strongest_composite_parent_information_ceiling": parents["COMPOSITE_SIMPLE_PARENT"][
            "information_ceiling_leave_one_out"
        ],
        "strongest_composite_parent_unsafe_rate": parents["COMPOSITE_SIMPLE_PARENT"][
            "unsafe_route_rate_leave_one_out"
        ],
        "hostile_mutations_caught": sum(1 for v in catches.values() if v["caught"]),
        "hostile_mutations_total": len(catches),
    }
    prose_vs_measured = {
        key: {
            "prose": quoted.get(key),
            "measured": measured.get(key),
            "agrees": (
                quoted.get(key) == measured.get(key)
                if not isinstance(quoted.get(key), float)
                else abs(float(quoted[key]) - float(measured[key])) < 1e-9
            ),
        }
        for key in quoted
        if key in measured
    }

    disagreements = sorted(k for k, v in prose_vs_measured.items() if not v["agrees"])
    terminal = "CORROBORATED" if not disagreements else "PARTIALLY_CORROBORATED"

    result = {
        "schema_version": "rakl-p3-router-v2-reconstruction-v1",
        "date": "2026-08-15",
        "terminal": terminal,
        "prose_quantities_not_corroborated": disagreements,
        "manuscript_correction_required": True,
        "manuscript_correction_target": (
            "publication/papers/paper-03-method-evolution-mechanics/sections/"
            "04b_obstruction_transformation_memory.tex"
        ),
        "paper": "Paper III — Method-Evolution Mechanics",
        "negative_addressed": "research/negative_frontier_v1/NEG-p3-router-v2-unreproducible.md",
        "frozen_protocol": "research/paper3_publication_validation_v2/PROTOCOL_FREEZE.json",
        "quoted_source": "research/paper3_publication_closeout_v1/FINAL_RECEIPT.json :: structured_validation",
        "reconstruction_not_reproduction": (
            "No artifact ever generated the quoted numbers, so nothing here re-produces them. "
            "This is what a faithful reconstruction under the frozen protocol measures."
        ),
        "severance_audit": severance,
        "protocol_conformance": {
            "families_match_freeze": True,
            "registered_mutations_match_freeze": True,
            "seed": protocol["seed"],
            "pairs_per_family": protocol["pairs_per_family"],
            "n_cases": n_cases,
        },
        "measured": measured,
        "prose_vs_measured": prose_vs_measured,
        "parent_arms": parents,
        "gate": gate,
        "gate_conditions_baseline": baseline_conditions,
        "gate_pass": all(baseline_conditions.values()),
        "registered_mutation_catches": catches,
        "candidate_mutant_table": mutants,
        "gate_condition_moved_by_candidate_mutant": moved_by_mutant,
        "evidence_perturbation_falsifiability": {
            name: {
                "verdict": report.verdict.value,
                "supports_confirmatory_use": report.supports_confirmatory_use,
                "sensitive_probes": list(report.sensitive_probes),
                "probes": {
                    p.probe_id: {"outcome": p.outcome.value, "flips": p.flips, "trials": p.trials}
                    for p in report.probes
                },
            }
            for name, report in reports.items()
        },
        "falsifiable_conditions": live,
        "non_falsifiable_conditions": dead,
        "cannot_check_conditions": unknown,
        "controls": {
            "severance_statically_audited": severance["severed"],
            "no_probe_targets_gold": True,
            "probe_ids": probe_ids,
            "at_least_one_condition_falsifiable": bool(live),
            "decorative_probes": sorted(DECORATIVE_PROBES),
        },
        "grants_scientific_authority": False,
        "authority": "instrument reconstruction only; proposal/routing scope, no scientific claim",
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "RECONSTRUCTION_RECEIPT.json").write_text(json.dumps(result, indent=2) + "\n")
    with (outdir / "CASES.jsonl").open("w") as fh:
        for case in cases:
            fh.write(json.dumps(case, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("measured", "prose_vs_measured",
                                             "gate_conditions_baseline", "gate_pass",
                                             "falsifiable_conditions",
                                             "non_falsifiable_conditions",
                                             "gate_condition_moved_by_candidate_mutant")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
