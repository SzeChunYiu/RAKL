#!/usr/bin/env python3
"""Per-condition black-box falsifiability audit of the REPAIRED Paper III gate.

Subject: the independent-oracle experience-to-action gate
  harness:  experiments/paper3/run_independent_oracle_action_v1.py
  oracle:   experiments/paper3/independent_action_oracle_v1.py
  protocol: research/paper3_independent_oracle_action_v1/PROTOCOL.json

This is the successor to research/paper3_gate_falsifiability_audit_v1/
GATE_FALSIFIABILITY_AUDIT.json, which convicted the historical self-grading
harness (gold := strict_action(c) at generation, prediction := strict_action(c)
at scoring) of NON_FALSIFIABLE verdicts on 4/6 registered conditions.

Design decisions, frozen before execution:

1.  EVIDENCE MODEL (primary, "FROZEN_GOLD"): the evidence object of the
    confirmatory receipt is the frozen (case, gold) panel — gold is assigned
    once, post-freeze, by the independent oracle, and is thereafter DATA.
    Probes perturb that panel (field shuffles break the coordinate<->gold
    alignment; class drops remove outcome support; a projection world rewrites
    gold as a function of the composite-parent fields). The gate re-runs the
    candidate on the perturbed coordinates and scores against the attached
    gold, exactly as the shipped harness scores against its assigned gold.

2.  KNOWN LIMIT, registered in advance: a black-box battery that REGENERATES
    gold from perturbed inputs cannot distinguish two extensionally-agreeing
    independent implementations from a single self-grading one. That mode is
    therefore run only as a PLANTED-DEFECT CONTROL: a wrapper that regenerates
    gold from the candidate (the historical defect, planted here) must
    reproduce the NON_FALSIFIABLE signature under the identical probe set.
    The discriminator between "self-identity" and "independent agreement" is
    (a) the frozen-gold sensitivity measured here, (b) the harness's own
    per-metric planted-mutant witnesses, and (c) the source-independence
    audit — never input perturbation alone.

3.  CONTROLS FIRST. The audit refuses to emit per-condition verdicts unless:
      C1 baseline reproduction — run() reproduces the committed FINAL_RECEIPT
         numbers exactly (n, outcome counts, four metrics, ceiling, terminal);
      C2 planted self-grading control — the regenerated-gold wrapper is
         NON_FALSIFIABLE on all four candidate conditions under the full
         probe set (the battery still catches the historical defect class);
      C3 known-answer source world — a doctored oracle containing a forbidden
         candidate token must fail the independence audit.

4.  NO CONJUNCTION AUDIT. Each gate condition is audited separately with
    src/rakl/gate_falsifiability.py::audit_gate. A conjunction can look
    falsifiable because one live leg moves while dead legs hide behind it.

Registered per-condition expectations (frozen now, before any execution;
an expectation miss is a reported finding, never a thing to tune away):

    candidate_exact                                  SENSITIVE
    candidate_unsafe                                 SENSITIVE
    candidate_cannot_check                           SENSITIVE
    candidate_legitimate_apply                       SENSITIVE
    all_outcomes_present                             SENSITIVE
    composite_parent_residual                        SENSITIVE
    all_mutants_change_candidate_metric              SENSITIVE
    all_candidate_metric_gates_demonstrably_falsifiable  SENSITIVE

grants_scientific_authority: false. A FALSIFIABLE verdict means only that the
condition is capable of failing; it never certifies that its PASS is correct.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rakl.gate_falsifiability import (  # noqa: E402
    GateFalsifiability,
    audit_gate,
    drop_fraction,
    shuffle_field,
)

RUNNER_PATH = ROOT / "experiments" / "paper3" / "run_independent_oracle_action_v1.py"
ORACLE_PATH = ROOT / "experiments" / "paper3" / "independent_action_oracle_v1.py"
CANDIDATE_PATH = ROOT / "experiments" / "orion_closure" / "run_p3_structured_experience_action.py"
PROTOCOL_PATH = ROOT / "research" / "paper3_independent_oracle_action_v1" / "PROTOCOL.json"
RECEIPT_PATH = ROOT / "research" / "paper3_independent_oracle_action_v1" / "FINAL_RECEIPT.json"

SEED = 20260814
TRIALS = 32

REGISTERED_EXPECTATIONS: dict[str, str] = {
    "candidate_exact": "SENSITIVE",
    "candidate_unsafe": "SENSITIVE",
    "candidate_cannot_check": "SENSITIVE",
    "candidate_legitimate_apply": "SENSITIVE",
    "all_outcomes_present": "SENSITIVE",
    "composite_parent_residual": "SENSITIVE",
    "all_mutants_change_candidate_metric": "SENSITIVE",
    "all_candidate_metric_gates_demonstrably_falsifiable": "SENSITIVE",
}


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- evidence construction ---------------------------------------------------------


def frozen_panel(runner: Any, oracle: Any, protocol: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The confirmatory evidence object: cases with post-freeze oracle gold attached."""
    cases = runner.build_cases(protocol)
    rows = []
    for row in cases:
        payload = {f: row[f] for f in runner.VISIBLE_FIELDS}
        rows.append({**row, "gold_action": oracle.oracle_action(payload)})
    return rows


# --- perturbations -----------------------------------------------------------------


def randomize_all_decision_fields(fields: Sequence[str]) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = [dict(r) for r in evidence]  # type: ignore[arg-type]
        for row in rows:
            for f in fields:
                row[f] = rng.random() < 0.5
        return rows

    return perturb


def drop_one_gold_outcome_class(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
    rows = [dict(r) for r in evidence]  # type: ignore[arg-type]
    outcomes = sorted({r["gold_action"] for r in rows})
    victim = rng.choice(outcomes)
    return [r for r in rows if r["gold_action"] != victim]


def gold_from_composite_projection(composite_fields: Sequence[str]) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Hostile world in which gold IS determined by the composite-parent fields.

    In this world the typed coordinates carry no information beyond the
    composite projection, so composite_parent_residual must be able to fail.
    """

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = [dict(r) for r in evidence]  # type: ignore[arg-type]
        for row in rows:
            favorable = (
                row["candidate_present"]
                and row["failure_signature_match"]
                and row["lineage_valid"]
                and row["strategy_family_match"]
                and not row["negative_history_block"]
            )
            row["gold_action"] = "APPLY_VERIFIED_LESSON" if favorable else "FALLBACK_SEARCH"
        return rows

    return perturb


def build_perturbations(runner: Any) -> dict[str, Callable[[Sequence[object], random.Random], Sequence[object]]]:
    probes: dict[str, Callable[[Sequence[object], random.Random], Sequence[object]]] = {}
    for f in runner.VISIBLE_FIELDS:
        probes[f"shuffle_{f}"] = shuffle_field(f)
    probes["shuffle_gold_action"] = shuffle_field("gold_action")
    probes["drop_half_the_cases"] = drop_fraction(0.5)
    probes["randomize_all_decision_fields"] = randomize_all_decision_fields(runner.VISIBLE_FIELDS)
    probes["drop_one_gold_outcome_class"] = drop_one_gold_outcome_class
    probes["gold_from_composite_projection"] = gold_from_composite_projection(runner.COMPOSITE_PARENT_FIELDS)
    return probes


# --- per-condition gate functions (FROZEN_GOLD evidence model) ---------------------


def make_condition_gates(
    runner: Any, candidate: Any, protocol: Mapping[str, Any]
) -> dict[str, Callable[[Sequence[object]], bool]]:
    thresholds = protocol["primary_metrics"]
    mutants = list(protocol["registered_candidate_mutants"])
    outcomes = runner.OUTCOMES

    def gold_of(rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
        return {str(r["case_id"]): str(r["gold_action"]) for r in rows}

    def base_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        pred = runner.candidate_prediction(candidate, rows)
        return runner.metrics(rows, gold_of(rows), pred)

    def candidate_exact(rows: Sequence[Mapping[str, Any]]) -> bool:
        return base_metrics(rows)["exact_action_accuracy"] >= thresholds["exact_action_accuracy_min"]

    def candidate_unsafe(rows: Sequence[Mapping[str, Any]]) -> bool:
        return base_metrics(rows)["unsafe_apply_rate"] <= thresholds["unsafe_apply_rate_max"]

    def candidate_cannot_check(rows: Sequence[Mapping[str, Any]]) -> bool:
        return base_metrics(rows)["cannot_check_recall"] >= thresholds["cannot_check_recall_min"]

    def candidate_legitimate_apply(rows: Sequence[Mapping[str, Any]]) -> bool:
        return base_metrics(rows)["legitimate_apply_recall"] >= thresholds["legitimate_apply_recall_min"]

    def all_outcomes_present(rows: Sequence[Mapping[str, Any]]) -> bool:
        present = {r["gold_action"] for r in rows}
        return all(o in present for o in outcomes)

    def composite_parent_residual(rows: Sequence[Mapping[str, Any]]) -> bool:
        ceiling = runner.information_ceiling(rows, gold_of(rows), runner.COMPOSITE_PARENT_FIELDS)
        return ceiling <= thresholds["composite_simple_information_ceiling_max"]

    def _mutant_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
        gold = gold_of(rows)
        base = runner.metrics(rows, gold, runner.candidate_prediction(candidate, rows))
        out: dict[str, dict[str, Any]] = {}
        for mutant in mutants:
            m = runner.metrics(rows, gold, runner.candidate_prediction(candidate, rows, mutant))
            out[mutant] = {
                "metrics": m,
                "changed_metrics": [k for k, v in m.items() if v != base[k]],
            }
        return out

    def all_mutants_change_candidate_metric(rows: Sequence[Mapping[str, Any]]) -> bool:
        return all(r["changed_metrics"] for r in _mutant_rows(rows).values())

    def all_candidate_metric_gates_demonstrably_falsifiable(rows: Sequence[Mapping[str, Any]]) -> bool:
        mr = _mutant_rows(rows)
        witnesses = {
            "exact_action_accuracy": [
                n for n, r in mr.items()
                if r["metrics"]["exact_action_accuracy"] < thresholds["exact_action_accuracy_min"]
            ],
            "unsafe_apply_rate": [
                n for n, r in mr.items()
                if r["metrics"]["unsafe_apply_rate"] > thresholds["unsafe_apply_rate_max"]
            ],
            "cannot_check_recall": [
                n for n, r in mr.items()
                if r["metrics"]["cannot_check_recall"] < thresholds["cannot_check_recall_min"]
            ],
            "legitimate_apply_recall": [
                n for n, r in mr.items()
                if r["metrics"]["legitimate_apply_recall"] < thresholds["legitimate_apply_recall_min"]
            ],
        }
        return all(witnesses.values())

    return {
        "candidate_exact": candidate_exact,
        "candidate_unsafe": candidate_unsafe,
        "candidate_cannot_check": candidate_cannot_check,
        "candidate_legitimate_apply": candidate_legitimate_apply,
        "all_outcomes_present": all_outcomes_present,
        "composite_parent_residual": composite_parent_residual,
        "all_mutants_change_candidate_metric": all_mutants_change_candidate_metric,
        "all_candidate_metric_gates_demonstrably_falsifiable": all_candidate_metric_gates_demonstrably_falsifiable,
    }


# --- planted self-grading control (the historical defect, replanted) ---------------


def make_self_grading_gates(
    runner: Any, candidate: Any, protocol: Mapping[str, Any]
) -> dict[str, Callable[[Sequence[object]], bool]]:
    """Gold is REGENERATED from the candidate after perturbation — the exact
    historical defect class. The battery must find these NON_FALSIFIABLE."""
    thresholds = protocol["primary_metrics"]

    def regen(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
        gold: dict[str, str] = {}
        pred: dict[str, str] = {}
        for r in rows:
            payload = {f: r[f] for f in runner.VISIBLE_FIELDS}
            action = candidate.strict_action(payload)
            gold[str(r["case_id"])] = action
            pred[str(r["case_id"])] = action
        return gold, pred

    def metrics_of(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        gold, pred = regen(rows)
        return runner.metrics(rows, gold, pred)

    return {
        "candidate_exact": lambda rows: metrics_of(rows)["exact_action_accuracy"] >= thresholds["exact_action_accuracy_min"],
        "candidate_unsafe": lambda rows: metrics_of(rows)["unsafe_apply_rate"] <= thresholds["unsafe_apply_rate_max"],
        "candidate_cannot_check": lambda rows: metrics_of(rows)["cannot_check_recall"] >= thresholds["cannot_check_recall_min"],
        "candidate_legitimate_apply": lambda rows: metrics_of(rows)["legitimate_apply_recall"] >= thresholds["legitimate_apply_recall_min"],
    }


# --- controls ----------------------------------------------------------------------


def control_baseline_reproduction(runner: Any, protocol: Mapping[str, Any]) -> dict[str, Any]:
    recorded = json.loads(RECEIPT_PATH.read_text())["fresh_result"]
    _, receipt = runner.run(protocol)
    got = {
        "n_cases": receipt["n_cases"],
        "gold_outcome_counts": receipt["gold_outcome_counts"],
        "exact_action_accuracy": receipt["candidate_metrics"]["exact_action_accuracy"],
        "unsafe_apply_rate": receipt["candidate_metrics"]["unsafe_apply_rate"],
        "cannot_check_recall": receipt["candidate_metrics"]["cannot_check_recall"],
        "legitimate_apply_recall": receipt["candidate_metrics"]["legitimate_apply_recall"],
        "composite_simple_parent_information_ceiling": receipt["composite_simple_parent_information_ceiling"],
        "mutations_caught": f"{sum(1 for r in receipt['registered_mutants'].values() if r['changed_metrics'])}/{len(receipt['registered_mutants'])}",
        "all_gates_pass": receipt["all_gates_pass"],
        "terminal": receipt["terminal"],
    }
    checks = {
        "n_cases": got["n_cases"] == recorded["n_cases"],
        "gold_outcome_counts": got["gold_outcome_counts"] == recorded["gold_outcome_counts"],
        "exact_action_accuracy": got["exact_action_accuracy"] == recorded["exact_action_accuracy"],
        "unsafe_apply_rate": got["unsafe_apply_rate"] == recorded["unsafe_apply_rate"],
        "cannot_check_recall": got["cannot_check_recall"] == recorded["cannot_check_recall"],
        "legitimate_apply_recall": got["legitimate_apply_recall"] == recorded["legitimate_apply_recall"],
        "composite_ceiling": got["composite_simple_parent_information_ceiling"]
        == recorded["composite_simple_parent_information_ceiling"],
        "mutations_caught": got["mutations_caught"] == recorded["registered_mutations_caught"],
        "all_gates_pass": bool(got["all_gates_pass"]),
    }
    return {"pass": all(checks.values()), "checks": checks, "reproduced": got}


def control_doctored_oracle_fails_independence(runner_module_path: Path) -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        doctored = Path(scratch) / "doctored_oracle_v1.py"
        doctored.write_text(
            ORACLE_PATH.read_text()
            + "\n# planted forbidden reference for the known-answer world: strict_action\n"
        )
        module = _load(runner_module_path, "p3_runner_doctored_world")
        module.ORACLE_PATH = doctored
        audit = module.independence_audit()
    return {
        "pass": audit["passes"] is False,
        "doctored_hits": audit["oracle_forbidden_token_hits"],
    }


# --- main --------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--trials", type=int, default=TRIALS)
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    protocol = json.loads(PROTOCOL_PATH.read_text())
    runner = _load(RUNNER_PATH, "p3_independent_runner_for_audit")
    oracle = _load(ORACLE_PATH, "p3_independent_oracle_for_audit")
    candidate = _load(CANDIDATE_PATH, "p3_candidate_for_audit")

    report: dict[str, Any] = {
        "schema_version": "rakl-p3-repaired-gate-falsifiability-audit-v1",
        "audited_subject": {
            "harness": "experiments/paper3/run_independent_oracle_action_v1.py",
            "oracle": "experiments/paper3/independent_action_oracle_v1.py",
            "candidate": "experiments/orion_closure/run_p3_structured_experience_action.py::strict_action",
            "protocol": "research/paper3_independent_oracle_action_v1/PROTOCOL.json",
            "receipt": "research/paper3_independent_oracle_action_v1/FINAL_RECEIPT.json",
            "battery": "src/rakl/gate_falsifiability.py",
        },
        "predecessor_audit": "research/paper3_gate_falsifiability_audit_v1/GATE_FALSIFIABILITY_AUDIT.json",
        "evidence_model": {
            "primary": "FROZEN_GOLD — the confirmatory evidence object is the frozen (case, gold) panel; gold is post-freeze oracle-assigned data and probes may break coordinate<->gold alignment.",
            "registered_limit": "Input perturbation with REGENERATED gold cannot distinguish extensionally-agreeing independent implementations from self-grading; that mode is used only as the planted-defect control below.",
        },
        "registered_expectations": REGISTERED_EXPECTATIONS,
        "seed": SEED,
        "trials_per_probe": args.trials,
    }

    # ---- controls first ----
    c1 = control_baseline_reproduction(runner, protocol)
    c3 = control_doctored_oracle_fails_independence(RUNNER_PATH)

    self_grading_reports = {}
    probes = build_perturbations(runner)
    evidence = frozen_panel(runner, oracle, protocol)
    for name, gate in make_self_grading_gates(runner, candidate, protocol).items():
        r = audit_gate(gate, evidence, gate_id=f"planted_self_grading::{name}",
                       perturbations=probes, trials=args.trials, seed=SEED)
        self_grading_reports[name] = r.verdict.value
    c2 = {
        "pass": all(v == GateFalsifiability.NON_FALSIFIABLE.value for v in self_grading_reports.values()),
        "per_condition": self_grading_reports,
    }

    report["controls"] = {
        "C1_baseline_reproduces_recorded_receipt": c1,
        "C2_planted_self_grading_is_NON_FALSIFIABLE": c2,
        "C3_doctored_oracle_fails_independence_audit": c3,
    }
    controls_pass = c1["pass"] and c2["pass"] and c3["pass"]
    report["controls_pass"] = controls_pass

    if not controls_pass:
        report["verdicts"] = "CANNOT_CHECK"
        report["reason"] = "control assertions failed; per-condition verdicts are not emitted"
        (outdir / "REPAIRED_GATE_FALSIFIABILITY_AUDIT.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(report["controls"], indent=2, sort_keys=True))
        return 3

    # ---- per-condition audit (never the conjunction) ----
    per_condition: dict[str, Any] = {}
    for name, gate in make_condition_gates(runner, candidate, protocol).items():
        r = audit_gate(gate, evidence, gate_id=name, perturbations=probes,
                       trials=args.trials, seed=SEED)
        per_condition[name] = {
            "verdict": r.verdict.value,
            "supports_confirmatory_use": r.supports_confirmatory_use,
            "sensitive_probes": list(r.sensitive_probes),
            "matches_registered_expectation": (
                ("SENSITIVE" if r.verdict is GateFalsifiability.FALSIFIABLE else "INSENSITIVE")
                == REGISTERED_EXPECTATIONS[name]
            ),
            "probes": {
                p.probe_id: {"outcome": p.outcome.value, "flips": p.flips, "trials": p.trials}
                for p in r.probes
            },
        }

    report["per_condition"] = per_condition
    report["falsifiable_conditions"] = sorted(
        n for n, v in per_condition.items() if v["verdict"] == "FALSIFIABLE"
    )
    report["non_falsifiable_conditions"] = sorted(
        n for n, v in per_condition.items() if v["verdict"] == "NON_FALSIFIABLE"
    )
    report["cannot_check_conditions"] = sorted(
        n for n, v in per_condition.items() if v["verdict"] == "CANNOT_CHECK"
    )
    report["expectation_misses"] = sorted(
        n for n, v in per_condition.items() if not v["matches_registered_expectation"]
    )
    report["independence_condition_note"] = (
        "The 'independent_oracle' gate condition consumes source code, not the case panel; "
        "its falsifiability is demonstrated by control C3 (doctored-source known-answer FAIL world), "
        "not by case-panel perturbation."
    )
    report["grants_scientific_authority"] = False

    (outdir / "REPAIRED_GATE_FALSIFIABILITY_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: v["verdict"] for k, v in per_condition.items()}, indent=2, sort_keys=True))
    print("expectation_misses:", report["expectation_misses"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
