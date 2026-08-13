"""Injected-deficiency accuracy experiment for the mechanic_diagnosis mechanic.

Design (read before trusting any number)
----------------------------------------
`rakl.mechanic_diagnosis.diagnose_mechanic_signals` is a DETERMINISTIC LOOKUP:
each recognised signal *name* maps to a fixed tuple of candidate causes
(`_SIGNAL_RULES`); candidates are unioned across signals; the verdict is pure
set-cardinality logic (1 surviving cause -> MECHANIC_GAP_IDENTIFIED, >1 with
registered discriminators -> DISCRIMINATOR_REQUIRED, >1 without ->
PARTIALLY_IDENTIFIED, only-UNKNOWN/empty -> CANNOT_CHECK). The API cannot
consume raw observations (timings, residual payloads, verifier transcripts):
any unmapped string collapses to the UNKNOWN cause. The caller must therefore
pre-classify observations into the 20 recognised signal names, which is where
most real diagnostic work would live.

Consequently a naive experiment ("inject cause X, emit the signal whose table
entry is X, ask the API") is CIRCULAR and its noise-0 accuracy is 1.0 by
construction, measuring nothing. This experiment does NOT claim otherwise.
What it honestly measures instead:

1. Structural identifiability of the signal->cause table: several causes
   (e.g. STOPPING_GAP, METRIC_FALSEHOOD, LOCAL_MINIMUM_OR_DYNAMICS_GAP,
   VERIFIER_GAP) manifest ONLY through signals shared with other causes, so
   they can never be uniquely identified from signals alone -- the correct
   API behaviour for them is ambiguity + discriminator request, not top-1.
2. A generative scenario model in which the injected deficiency emits its
   characteristic signal(s) PLUS probabilistic downstream co-symptoms (fixed
   per scenario at generation), so multi-candidate sets arise even without
   noise, as they would in a real solver trace.
3. Verdict honesty under signal corruption: with noise r, emitted signals are
   dropped, spurious recognised signals are added, and unrecognised raw
   observation strings are injected. We measure whether corruption produces
   FORCED-WRONG single diagnoses (MECHANIC_GAP_IDENTIFIED with the wrong sole
   cause) or HONEST ambiguity (PARTIALLY_IDENTIFIED / DISCRIMINATOR_REQUIRED /
   CANNOT_CHECK).

No accuracy value is hardcoded anywhere; every number comes from running the
real API on generated scenarios.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from rakl.mechanic_diagnosis import (
    _SIGNAL_RULES,
    MechanicCause,
    MechanicDiagnosisVerdict,
    diagnose_mechanic_signals,
)

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "research" / "unified_problem_solving_v1" / "results"
RESULT_FILE = RESULT_DIR / "diagnosis_accuracy.json"

SEED = 461
N_SCENARIOS = 300
NOISE_LEVELS = (0.0, 0.1, 0.2, 0.3)
BOOTSTRAP_RESAMPLES = 5000
CLAIM_BOUNDARY = (
    "development known-world evidence; injected-deficiency scenarios; "
    "grants no scientific or method-promotion authority"
)

# Injected deficiency -> (always-emitted core signals, probabilistic downstream
# co-symptoms fixed at scenario generation). Core signals are the table's own
# manifestation of the cause; co-symptoms are plausible downstream consequences
# that are ALSO recognised signals of other causes, so they widen the candidate
# set the way a real trace would.
EMISSION_PROFILES: dict[MechanicCause, tuple[tuple[str, ...], tuple[tuple[str, float], ...]]] = {
    MechanicCause.REPRESENTATION_GAP: (
        ("representation_preservation_failed",),
        (("coverage_incomplete", 0.3),),
    ),
    MechanicCause.METHOD_OPERATOR_GAP: (
        ("target_unreachable_current_operator_basis",),
        (("coverage_incomplete", 0.3),),
    ),
    MechanicCause.MAP_COVERAGE_GAP: (
        ("unknown_map_edge",),
        (("coverage_incomplete", 0.5),),
    ),
    MechanicCause.VERIFIER_GAP: (
        # Only manifestation in the table is shared with IMPLEMENTATION_DEFECT:
        # structurally never uniquely identifiable from signals alone.
        ("verifier_inconsistent_replay",),
        (("missing_measurement", 0.3),),
    ),
    MechanicCause.IMPLEMENTATION_DEFECT: (
        ("implementation_contract_failed",),
        (("verifier_inconsistent_replay", 0.4),),
    ),
    MechanicCause.MODEL_TOOL_FLOOR: (
        ("model_capability_floor",),
        (("budget_spent_on_wrong_mechanic", 0.3),),
    ),
    MechanicCause.STOPPING_GAP: (
        # Only manifestation is 'coverage_incomplete', shared with
        # MAP_COVERAGE_GAP: structurally never uniquely identifiable.
        ("coverage_incomplete",),
        (),
    ),
    MechanicCause.METRIC_FALSEHOOD: (
        # Only manifestation shared with LOCAL_MINIMUM_OR_DYNAMICS_GAP.
        ("local_metric_descends_root_stalls",),
        (),
    ),
}

INJECTED_CAUSES = tuple(EMISSION_PROFILES)
SIGNAL_VOCABULARY = tuple(_SIGNAL_RULES)
DISCRIMINATOR_IDS = ("disc_independent_replay", "disc_alternate_map_probe")
HONEST_AMBIGUOUS_VERDICTS = frozenset(
    {
        MechanicDiagnosisVerdict.PARTIALLY_IDENTIFIED,
        MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED,
        MechanicDiagnosisVerdict.CANNOT_CHECK,
    }
)


def structural_identifiability() -> dict[str, bool]:
    """A cause is uniquely identifiable iff some signal maps to it alone."""
    unique_for: set[MechanicCause] = {
        causes[0] for causes in _SIGNAL_RULES.values() if len(causes) == 1
    }
    return {cause.value: cause in unique_for for cause in INJECTED_CAUSES}


def generate_scenarios(rng: np.random.Generator) -> list[dict]:
    scenarios: list[dict] = []
    for index in range(N_SCENARIOS):
        true_cause = INJECTED_CAUSES[int(rng.integers(len(INJECTED_CAUSES)))]
        core, co_symptoms = EMISSION_PROFILES[true_cause]
        signals = list(core)
        for signal, probability in co_symptoms:
            if rng.random() < probability:
                signals.append(signal)
        discriminators = DISCRIMINATOR_IDS if rng.random() < 0.5 else ()
        scenarios.append(
            {
                "index": index,
                "true_cause": true_cause,
                "base_signals": tuple(signals),
                "discriminator_ids": discriminators,
            }
        )
    return scenarios


def perturb_signals(base_signals: tuple[str, ...], noise: float, rng: np.random.Generator) -> tuple[str, ...]:
    """Corrupt the observable signal set.

    - each emitted signal is DROPPED with probability `noise`;
    - with probability `noise` one SPURIOUS recognised signal (uniform over the
      vocabulary minus the emitted set) is added;
    - with probability `noise / 2` one UNRECOGNISED raw-observation string is
      added (the API maps it to the UNKNOWN cause).
    """
    kept = [signal for signal in base_signals if rng.random() >= noise]
    if rng.random() < noise:
        others = [signal for signal in SIGNAL_VOCABULARY if signal not in base_signals]
        kept.append(others[int(rng.integers(len(others)))])
    if rng.random() < noise / 2.0:
        kept.append(f"raw_wallclock_spike_ms_{int(rng.integers(10, 5000))}")
    return tuple(kept)


def run_noise_level(scenarios: list[dict], noise: float, level_index: int) -> list[dict]:
    rng = np.random.default_rng([SEED, level_index])
    records: list[dict] = []
    for scenario in scenarios:
        observed = perturb_signals(scenario["base_signals"], noise, rng)
        receipt = diagnose_mechanic_signals(
            diagnosis_id=f"diag-{level_index}-{scenario['index']}",
            problem_state_id=f"p-{scenario['index']}",
            atom_id="injected-deficiency-atom",
            fibre_snapshot_hash=f"fibre-{SEED}",
            residual_ids=(f"r-{scenario['index']}",),
            signals=observed,
            discriminator_ids=scenario["discriminator_ids"],
        )
        true_cause = scenario["true_cause"]
        candidates = receipt.candidate_causes
        identified = receipt.verdict is MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
        records.append(
            {
                "true_cause": true_cause.value,
                "verdict": receipt.verdict.value,
                "n_candidates": len(candidates),
                "containment": true_cause in candidates,
                # The API does NOT rank candidates; order is signal-processing
                # insertion order. 'top-1' here means first-listed candidate.
                "top1_first_listed": bool(candidates) and candidates[0] is true_cause,
                "identified_correct": identified and candidates[0] is true_cause,
                "forced_wrong": identified and candidates[0] is not true_cause,
                "honest_ambiguous": receipt.verdict in HONEST_AMBIGUOUS_VERDICTS,
                "cannot_check": receipt.verdict is MechanicDiagnosisVerdict.CANNOT_CHECK,
            }
        )
    return records


def bootstrap_rate(flags: np.ndarray, rng: np.random.Generator) -> dict:
    n = flags.size
    if n == 0:
        return {"rate": None, "ci95": [None, None], "n": 0}
    resample_idx = rng.integers(0, n, size=(BOOTSTRAP_RESAMPLES, n))
    means = flags[resample_idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"rate": float(flags.mean()), "ci95": [float(lo), float(hi)], "n": int(n)}


METRICS = (
    "containment",
    "top1_first_listed",
    "identified_correct",
    "forced_wrong",
    "honest_ambiguous",
    "cannot_check",
)


def summarise_level(records: list[dict], boot_rng: np.random.Generator) -> dict:
    overall = {
        metric: bootstrap_rate(np.array([r[metric] for r in records], dtype=float), boot_rng)
        for metric in METRICS
    }
    per_cause: dict[str, dict] = {}
    for cause in INJECTED_CAUSES:
        rows = [r for r in records if r["true_cause"] == cause.value]
        per_cause[cause.value] = {
            metric: bootstrap_rate(np.array([r[metric] for r in rows], dtype=float), boot_rng)
            for metric in METRICS
        }
    verdicts = sorted({r["verdict"] for r in records})
    verdict_counts = {v: sum(1 for r in records if r["verdict"] == v) for v in verdicts}
    return {"overall": overall, "per_cause": per_cause, "verdict_counts": verdict_counts}


def main() -> int:
    scenario_rng = np.random.default_rng(SEED)
    scenarios = generate_scenarios(scenario_rng)
    boot_rng = np.random.default_rng([SEED, 9999])

    by_noise: dict[str, dict] = {}
    for level_index, noise in enumerate(NOISE_LEVELS):
        records = run_noise_level(scenarios, noise, level_index)
        by_noise[f"{noise:.1f}"] = summarise_level(records, boot_rng)

    result = {
        "schema_version": "orion-mechanic-diagnosis-accuracy-v1",
        "status": "DEVELOPMENT_KNOWN_WORLD_MECHANISM_EVIDENCE_ONLY",
        "seed": SEED,
        "n_scenarios_per_noise_level": N_SCENARIOS,
        "noise_levels": list(NOISE_LEVELS),
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "claim_boundary": CLAIM_BOUNDARY,
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        "api_characterization": {
            "mechanism": (
                "diagnose_mechanic_signals is a deterministic lookup from 20 "
                "recognised signal NAMES to fixed candidate-cause tuples, "
                "unioned across signals; the verdict is set-cardinality logic "
                "plus discriminator availability. It performs no statistical "
                "inference and cannot consume raw observations: any unmapped "
                "string collapses to the UNKNOWN cause."
            ),
            "circularity_warning": (
                "Noise-0 containment is 1.0 by construction whenever the core "
                "signal survives: the experiment feeds pre-classified signal "
                "names, so noise-0 numbers measure the TABLE'S disambiguation "
                "structure and the emission model, not inference power. The "
                "non-circular content is (a) structural identifiability of "
                "each cause and (b) verdict honesty under signal corruption."
            ),
            "finding_needed": (
                "A richer signal model (raw telemetry -> signal classification "
                "inside the mechanic, with calibrated uncertainty) is required "
                "before diagnosis accuracy can be claimed as a capability."
            ),
        },
        "generative_model": {
            "injected_causes": [c.value for c in INJECTED_CAUSES],
            "emission_profiles": {
                cause.value: {
                    "core_signals": list(core),
                    "co_symptoms": [
                        {"signal": s, "probability": p} for s, p in co
                    ],
                }
                for cause, (core, co) in EMISSION_PROFILES.items()
            },
            "noise_model": (
                "per emitted signal: dropped w.p. noise; per scenario: one "
                "spurious recognised signal added w.p. noise; one unrecognised "
                "raw-observation string added w.p. noise/2"
            ),
            "discriminator_availability": 0.5,
            "top1_definition": (
                "first-listed candidate; the API does not rank candidates "
                "(insertion order of signal processing), so top-1 is only "
                "well-defined as a claim when verdict == "
                "MECHANIC_GAP_IDENTIFIED (see identified_correct/forced_wrong)"
            ),
        },
        "structural_identifiability": structural_identifiability(),
        "results_by_noise": by_noise,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    for noise in NOISE_LEVELS:
        row = by_noise[f"{noise:.1f}"]["overall"]
        print(
            f"noise={noise:.1f} containment={row['containment']['rate']:.3f} "
            f"top1_first_listed={row['top1_first_listed']['rate']:.3f} "
            f"identified_correct={row['identified_correct']['rate']:.3f} "
            f"forced_wrong={row['forced_wrong']['rate']:.3f} "
            f"honest_ambiguous={row['honest_ambiguous']['rate']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
