#!/usr/bin/env python3
"""Can the promoted Paper III experience-to-action gate fail?

Self-RAKL. This audits *our own* evidence apparatus, not any scientific object.
It grants no authority: a FALSIFIABLE verdict means only that a gate condition
*could* have failed, never that its PASS is correct.

Subject
-------
``experiments/orion_closure/run_p3_structured_experience_action.py`` — the
harness whose receipt
``research/orion_p1_p4_closure_v2/P3_STRUCTURED_EXPERIENCE_ACTION_RECEIPT.json``
carries the terminal ``PROMOTE_TO_MECHANIC_STRUCTURED_VERIFIED_EXPERIENCE_TO_ACTION``
and supplies the "verified structured experience-to-action" leg of the Paper III
promotion-grade claim.

The audit is deliberately per-condition. The registered hard gate is a
conjunction of six conditions; auditing the conjunction would let the two live
conditions mask the four dead ones and return a reassuring FALSIFIABLE. The
per-condition table is the finding.

Wiring
------
Evidence is the generated case set *before* gold assignment, because that is the
harness's actual data flow: ``execute()`` receives only the protocol, generates
cases, and then assigns ``gold_action = strict_action(c)`` internally. Any
faithful black-box probe must perturb the evidence upstream of that assignment,
exactly as a differently-seeded protocol would.

Control
-------
Two conditions (``composite_residual``, ``all_mutations_caught``) are exercised
by the identical perturbation set. If they move, the probe machinery is live and
the INSENSITIVE verdicts on the other four are not a broken-probe artifact. The
audit fails loudly if the baseline does not pass, or if no condition is
falsifiable — either would make the whole run vacuous.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import statistics
import sys
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from rakl.gate_falsifiability import (  # noqa: E402
    GateFalsifiability,
    audit_gate,
    drop_fraction,
    shuffle_field,
    zero_variance_arms,
)

HARNESS_PATH = ROOT / "experiments" / "orion_closure" / "run_p3_structured_experience_action.py"
PROTOCOL_PATH = ROOT / "research" / "orion_p1_p4_closure_v2" / "P3_EXPERIENCE_PROTOCOL_FREEZE.json"
RECEIPT_PATH = (
    ROOT / "research" / "orion_p1_p4_closure_v2" / "P3_STRUCTURED_EXPERIENCE_ACTION_RECEIPT.json"
)

#: Boolean coordinates ``strict_action`` actually reads. Kept explicit so the
#: audit states which of the declared ``FULL_FIELDS`` are decision-bearing.
DECISION_FIELDS = (
    "candidate_present",
    "lesson_verified",
    "scope_match",
    "version_current",
    "not_refuted",
    "lineage_valid",
    "target_context_match",
    "failure_signature_match",
    "strategy_family_match",
    "negative_history_block",
    "validity_known",
    "successor_verified",
    "successor_scope_match",
    "successor_current",
)


def _load_harness() -> Any:
    spec = importlib.util.spec_from_file_location("p3_harness", HARNESS_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load harness at {HARNESS_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = _load_harness()


def build_evidence(protocol: dict) -> list[dict]:
    """Generate the raw case set exactly as ``execute`` does, before gold assignment."""
    rng = random.Random(protocol["seed"])
    cases: list[dict] = []
    for family in protocol["families"]:
        for i in range(protocol["pairs_per_family"]):
            cases.extend(H.make_pair(family, rng, i))
    return cases


def pipeline(cases: Sequence[object], mutations: Sequence[str]) -> dict:
    """Replicate the harness's downstream computation on a (possibly perturbed) case set."""
    rows = [dict(c) for c in cases]  # type: ignore[arg-type]
    if not rows:
        raise ValueError("empty case set")
    for row in rows:
        row["gold_action"] = H.strict_action(row)
    typed_pred = {row["case_id"]: H.strict_action(row) for row in rows}
    typed = H.metrics(rows, typed_pred)
    ceiling, _pred, _collisions = H.information_ceiling(rows, H.PROJ["COMPOSITE_SIMPLE_PARENT"])
    caught = {}
    for mutation in mutations:
        pred = {row["case_id"]: H.strict_action(row, mutation) for row in rows}
        caught[mutation] = any(pred[row["case_id"]] != row["gold_action"] for row in rows)
    return {"typed": typed, "composite_ceiling": ceiling, "mutations_caught": caught}


def gate_conditions(
    hard_gate: dict, mutations: Sequence[str]
) -> dict[str, Callable[[Sequence[object]], bool]]:
    """The six registered hard-gate conditions, each as an independent evidence -> bool gate."""

    def typed_exact(cases: Sequence[object]) -> bool:
        return pipeline(cases, mutations)["typed"]["exact_action_accuracy"] >= hard_gate[
            "typed_exact_min"
        ]

    def typed_unsafe(cases: Sequence[object]) -> bool:
        return pipeline(cases, mutations)["typed"]["unsafe_apply_rate"] <= hard_gate[
            "typed_unsafe_apply_max"
        ]

    def typed_cannot_check(cases: Sequence[object]) -> bool:
        return pipeline(cases, mutations)["typed"]["cannot_check_recall"] >= hard_gate[
            "typed_cannot_check_recall_min"
        ]

    def typed_legitimate_apply(cases: Sequence[object]) -> bool:
        return pipeline(cases, mutations)["typed"]["legitimate_apply_recall"] >= hard_gate[
            "typed_legitimate_apply_recall_min"
        ]

    def composite_residual(cases: Sequence[object]) -> bool:
        return pipeline(cases, mutations)["composite_ceiling"] <= hard_gate[
            "composite_simple_ceiling_max"
        ]

    def all_mutations_caught(cases: Sequence[object]) -> bool:
        return all(pipeline(cases, mutations)["mutations_caught"].values())

    return {
        "typed_exact": typed_exact,
        "typed_unsafe": typed_unsafe,
        "typed_cannot_check": typed_cannot_check,
        "typed_legitimate_apply": typed_legitimate_apply,
        "composite_residual": composite_residual,
        "all_mutations_caught": all_mutations_caught,
    }


# --- domain-appropriate perturbations ---------------------------------------------


def randomize_decision_fields(
    evidence: Sequence[object], rng: random.Random
) -> Sequence[object]:
    """Re-draw every decision-bearing boolean independently, destroying all structure."""
    rows = [dict(row) for row in evidence]  # type: ignore[arg-type]
    for row in rows:
        for field in DECISION_FIELDS:
            row[field] = rng.random() < 0.5
    return rows


def drop_families(fraction: float) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Remove a random subset of whole families.

    The registered v1 terminal for the 21-family successor protocol was
    ``INSTRUMENT_DEFECT_TWO_MUTATIONS_NOT_EXERCISED`` — i.e. a case set that
    fails to exercise a mutation is a recorded, real failure mode of this
    instrument, not a hypothetical one.
    """

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        families = sorted({row["family"] for row in evidence})  # type: ignore[index]
        keep_n = max(2, int(len(families) * (1.0 - fraction)))
        keep = set(rng.sample(families, keep_n))
        return [row for row in evidence if row["family"] in keep]  # type: ignore[index]

    return perturb


PERTURBATIONS: dict[str, Callable[[Sequence[object], random.Random], Sequence[object]]] = {
    "shuffle_lesson_verified": shuffle_field("lesson_verified"),
    "shuffle_scope_match": shuffle_field("scope_match"),
    "shuffle_validity_known": shuffle_field("validity_known"),
    "shuffle_negative_history_block": shuffle_field("negative_history_block"),
    "randomize_all_decision_fields": randomize_decision_fields,
    "drop_one_third_of_families": drop_families(0.34),
    "drop_half_the_cases": drop_fraction(0.5),
    "shuffle_confidence": shuffle_field("confidence"),
    "shuffle_candidate_count": shuffle_field("candidate_count"),
}

#: Declared decorative — ``strict_action`` never reads these, so INSENSITIVE is
#: the correct outcome and is not reported as a defect.
DECORATIVE_PROBES = frozenset({"shuffle_confidence", "shuffle_candidate_count"})


def analytic_identity_check(
    evidence: Sequence[object], mutations: Sequence[str], *, trials: int, seed: int
) -> dict:
    """Independent of the battery: does the typed arm ever leave its ceiling?

    ``execute`` sets ``gold_action = strict_action(c)`` and then computes the
    candidate prediction as ``strict_action(c)`` — the same pure function on the
    same argument. The four typed metrics are therefore expected to hold their
    ceiling under *every* perturbation. This measures that directly and exactly,
    rather than against the gate threshold, and feeds the metric series to
    ``zero_variance_arms``.
    """
    series: dict[str, list[float]] = {
        "exact_action_accuracy": [],
        "unsafe_apply_rate": [],
        "cannot_check_recall": [],
        "legitimate_apply_recall": [],
        "composite_ceiling": [],
        "n_mutations_caught": [],
    }
    for probe_id, perturb in sorted(PERTURBATIONS.items()):
        for trial in range(trials):
            rng = random.Random(f"{seed}:{probe_id}:{trial}")
            out = pipeline(perturb(evidence, rng), mutations)
            for key in (
                "exact_action_accuracy",
                "unsafe_apply_rate",
                "cannot_check_recall",
                "legitimate_apply_recall",
            ):
                series[key].append(out["typed"][key])
            series["composite_ceiling"].append(out["composite_ceiling"])
            series["n_mutations_caught"].append(float(sum(out["mutations_caught"].values())))

    degenerate = zero_variance_arms(series)
    return {
        "n_perturbed_case_sets": len(series["exact_action_accuracy"]),
        "exact_action_accuracy_always_exactly_1": all(
            v == 1.0 for v in series["exact_action_accuracy"]
        ),
        "unsafe_apply_rate_always_exactly_0": all(v == 0.0 for v in series["unsafe_apply_rate"]),
        "cannot_check_recall_always_exactly_1": all(
            v == 1.0 for v in series["cannot_check_recall"]
        ),
        "legitimate_apply_recall_always_exactly_1": all(
            v == 1.0 for v in series["legitimate_apply_recall"]
        ),
        "zero_variance_arms": list(degenerate),
        "composite_ceiling_range": [
            min(series["composite_ceiling"]),
            max(series["composite_ceiling"]),
        ],
        "composite_ceiling_stdev": statistics.pstdev(series["composite_ceiling"]),
        "n_mutations_caught_range": [
            min(series["n_mutations_caught"]),
            max(series["n_mutations_caught"]),
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--trials", type=int, default=32)
    ap.add_argument("--seed", type=int, default=20260814)
    args = ap.parse_args()

    protocol = json.loads(PROTOCOL_PATH.read_text())
    hard_gate = protocol["hard_gate"]
    mutations = protocol["mutations"]
    evidence = build_evidence(protocol)

    # Control 1: the audit must run against the real, unperturbed evidence and
    # reproduce the recorded PASS. Probing a gate that does not pass in the
    # first place would make every verdict below meaningless.
    baseline = pipeline(evidence, mutations)
    conditions = gate_conditions(hard_gate, mutations)
    baseline_conditions = {name: bool(fn(evidence)) for name, fn in conditions.items()}
    if not all(baseline_conditions.values()):
        raise SystemExit(
            f"CONTROL FAILED: baseline does not reproduce the recorded PASS: {baseline_conditions}"
        )

    recorded = json.loads(RECEIPT_PATH.read_text())
    reproduces_receipt = (
        len(evidence) == recorded["n_cases"]
        and baseline["typed"] == recorded["typed_selective_experience"]
    )

    reports = {}
    for name, fn in conditions.items():
        report = audit_gate(
            fn,
            evidence,
            gate_id=f"p3_structured_experience_action::{name}",
            perturbations=PERTURBATIONS,
            trials=args.trials,
            seed=args.seed,
        )
        reports[name] = report

    # Control 2: at least one condition must come back FALSIFIABLE under the
    # identical perturbation set, or the probes are not live and no
    # NON_FALSIFIABLE verdict below can be trusted.
    live = [n for n, r in reports.items() if r.verdict is GateFalsifiability.FALSIFIABLE]
    if not live:
        raise SystemExit(
            "CONTROL FAILED: no condition was falsifiable under this perturbation set; "
            "the probes cannot be shown to be live, so no NON_FALSIFIABLE verdict is reportable"
        )

    analytic = analytic_identity_check(
        evidence, mutations, trials=max(4, args.trials // 4), seed=args.seed
    )

    dead = [n for n, r in reports.items() if r.verdict is GateFalsifiability.NON_FALSIFIABLE]
    unknown = [n for n, r in reports.items() if r.verdict is GateFalsifiability.CANNOT_CHECK]

    result = {
        "schema_version": "rakl-p3-gate-falsifiability-audit-v1",
        "audited_subject": {
            "harness": "experiments/orion_closure/run_p3_structured_experience_action.py",
            "protocol": "research/orion_p1_p4_closure_v2/P3_EXPERIENCE_PROTOCOL_FREEZE.json",
            "receipt": "research/orion_p1_p4_closure_v2/P3_STRUCTURED_EXPERIENCE_ACTION_RECEIPT.json",
            "battery": "src/rakl/gate_falsifiability.py",
        },
        "controls": {
            "baseline_reproduces_recorded_pass": True,
            "baseline_reproduces_recorded_metrics": reproduces_receipt,
            "baseline_conditions": baseline_conditions,
            "live_probe_witness": sorted(live),
        },
        "n_cases": len(evidence),
        "trials_per_probe": args.trials,
        "seed": args.seed,
        "per_condition": {
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
        "analytic_identity_check": analytic,
        "decorative_probes": sorted(DECORATIVE_PROBES),
        "falsifiable_conditions": sorted(live),
        "non_falsifiable_conditions": sorted(dead),
        "cannot_check_conditions": sorted(unknown),
        "grants_scientific_authority": False,
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "GATE_FALSIFIABILITY_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
