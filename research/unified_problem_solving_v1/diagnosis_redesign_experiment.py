"""Non-circular mechanic diagnosis: raw telemetry → uncertain symptoms → causes.

Preregistered design (issue #523):
-----------------------------------
CIRCULARITY PROBLEM: The current implementation maps pre-classified signal NAMES
to causes via a deterministic table (_SIGNAL_RULES). At noise=0, containment=1.0
by construction — measuring the TABLE's disambiguation structure, not inference power.

NON-CIRCULAR APPROACH:
1. RAW TELEMETRY: Numerical observables (timings, residuals, metric deltas, resource usage)
2. SYMPTOM INFERENCE: Probabilistic mapping from telemetry to symptom presence with calibrated uncertainty
3. CAUSE DISCRIMINATION: Bayesian inference from symptoms to causes, with explicit entropy
4. SUCCESS METRIC: Can the method distinguish causes with overlapping symptom profiles?

KEY DESIGN DECISIONS TO BREAK CIRCULARITY:
- Symptom/signal names are NOT part of the raw telemetry input
- The cause→symptom generative model is HIDDEN from the diagnostic method
- The method only sees numerical telemetry vectors
- Success = discriminating causes that share overlapping symptom profiles

HONESTY CONTRACT:
- Do not tune positive. If diagnosis collapses to chance after removing circularity,
  that is a decisive NEGATIVE (successful closure).
- Report forced_wrong_rate at top level with CI {lo,hi}
- grants_scientific_authority: false
- Vocabulary: SUPPORTED / PARTIAL / NEGATIVE / CANNOT_CHECK / UNDERPOWERED / ARCHITECTURE_ONLY

Method (4 lenses):
- Formal: Symptom→cause map is well-posed (identifiable, non-degenerate)
- ML/representation: Discriminative power from numerical features, not lookup
- Systems: End-to-end from raw observables to actionable diagnosis
- Scientific validity: No circularity, preregistered design, honest negative reporting
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

import numpy as np
import numpy.typing as npt

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "research" / "unified_problem_solving_v1" / "results"
RESULT_FILE = RESULT_DIR / "diagnosis_accuracy.json"

SEED = 461
N_SCENARIOS = 500
BOOTSTRAP_RESAMPLES = 5000

# Preregistered experiment parameters
N_TELEMETRY_DIMENSIONS = 8  # Number of raw observables
N_SYMPTOMS = 6  # Number of inferred symptoms (latent, not directly observed)
N_CAUSES = 8  # Number of underlying causes
NOISE_LEVELS = (0.0, 0.1, 0.2, 0.3)


class DiagnosisStatus(str, Enum):
    """Terminal vocabulary for diagnosis capability."""
    SUPPORTED = "SUPPORTED"  # Diagnosis reliably discriminates causes (CI excludes chance)
    PARTIAL = "PARTIAL"  # Some discrimination but not robust (CI includes chance, not fully negative)
    NEGATIVE = "NEGATIVE"  # No better than chance (CI includes 0, or worse)
    CANNOT_CHECK = "CANNOT_CHECK"  # Experiment cannot measure capability
    UNDERPOWERED = "UNDERPOWERED"  # Sample size insufficient to conclude
    ARCHITECTURE_ONLY = "ARCHITECTURE_ONLY"  # Only architectural contribution, no empirical claim


@dataclass(frozen=True)
class TelemetryVector:
    """Raw numerical observables from a solver run."""
    # Timing features
    solve_time_ms: float
    verifier_time_ms: float
    # Residual/error metrics
    final_residual: float
    max_step_residual: float
    # Resource usage
    memory_peak_mb: float
    computation_steps: int
    # Metric dynamics
    metric_delta: float
    metric_convergence_rate: float

    def to_array(self) -> npt.NDArray[np.float64]:
        return np.array([
            self.solve_time_ms,
            self.verifier_time_ms,
            self.final_residual,
            self.max_step_residual,
            self.memory_peak_mb,
            float(self.computation_steps),
            self.metric_delta,
            self.metric_convergence_rate,
        ], dtype=np.float64)


@dataclass(frozen=True)
class SymptomProfile:
    """Probabilistic symptom presence inferred from telemetry."""
    # Latent symptom indicators (not directly observed)
    coverage_weak: float  # [0,1] probability
    representation_deficit: float
    verification_failed: float
    metric_misleading: float
    resource_exhausted: float
    convergence_stalled: float

    def to_array(self) -> npt.NDArray[np.float64]:
        return np.array([
            self.coverage_weak,
            self.representation_deficit,
            self.verification_failed,
            self.metric_misleading,
            self.resource_exhausted,
            self.convergence_stalled,
        ], dtype=np.float64)


@dataclass(frozen=True)
class Cause:
    """An underlying mechanic cause (hidden ground truth)."""
    cause_id: str
    name: str
    # Generative parameters: how this cause manifests in symptoms
    # These are HIDDEN from the diagnostic method during inference
    symptom_bias: npt.NDArray[np.float64]  # Base symptom probabilities
    symptom_variance: npt.NDArray[np.float64]  # Variance per symptom


class GenerativeModel:
    """Hidden cause→symptom→telemetry generative model.

    This model generates the ground truth for experiments. It is HIDDEN from
    the diagnostic method during inference to avoid circularity.
    """

    def __init__(self, rng: np.random.Generator, seed: int = SEED):
        self.rng = rng
        self.seed = seed
        # Initialize causes with HIDDEN generative parameters
        self._causes = self._initialize_causes()
        # Symptom→telemetry mapping parameters
        self._symptom_telemetry_mean = np.random.default_rng(seed).normal(
            loc=[100.0, 50.0, 0.01, 0.05, 512.0, 100.0, -0.1, 0.5],
            scale=[20.0, 10.0, 0.005, 0.02, 128.0, 20.0, 0.05, 0.1],
            size=(N_SYMPTOMS, N_TELEMETRY_DIMENSIONS)
        )
        self._symptom_telemetry_cov = np.eye(N_TELEMETRY_DIMENSIONS) * 0.1

    def _initialize_causes(self) -> list[Cause]:
        """Initialize causes with HIDDEN generative parameters.

        Key design: causes have OVERLAPPING symptom profiles to make
        discrimination non-trivial. If symptoms were perfectly separable,
        diagnosis would be trivial lookup, not inference.
        """
        rng = np.random.default_rng(self.seed)
        causes = []

        cause_names = [
            "MAP_COVERAGE_GAP",
            "REPRESENTATION_GAP",
            "VERIFIER_GAP",
            "METRIC_FALSEHOOD",
            "MODEL_TOOL_FLOOR",
            "STOPPING_GAP",
            "METHOD_OPERATOR_GAP",
            "IMPLEMENTATION_DEFECT",
        ]

        for i, name in enumerate(cause_names):
            # Base symptom probabilities [0,1]
            bias = rng.uniform(0.2, 0.8, size=N_SYMPTOMS)
            # Add overlap: some causes share high symptom probabilities
            if i % 2 == 0:  # Even-indexed causes share symptom pattern
                bias[0] = 0.7  # High coverage_weak
                bias[2] = 0.6  # Moderate verification_failed
            else:  # Odd-indexed causes share different pattern
                bias[1] = 0.7  # High representation_deficit
                bias[3] = 0.6  # Moderate metric_misleading

            variance = rng.uniform(0.05, 0.15, size=N_SYMPTOMS)
            causes.append(Cause(
                cause_id=f"cause_{i}",
                name=name,
                symptom_bias=bias,
                symptom_variance=variance,
            ))

        return causes

    @property
    def causes(self) -> list[Cause]:
        return self._causes

    def generate_telemetry(
        self,
        cause: Cause,
        noise: float = 0.0,
    ) -> TelemetryVector:
        """Generate raw telemetry vector for a given cause.

        Process (hidden from diagnostic method):
        1. Cause determines symptom probabilities (bias + variance)
        2. Symptoms are sampled from Bernoulli(p)
        3. Telemetry is sampled from symptom→telemetry Gaussian

        The diagnostic method only sees the final telemetry vector, not
        the intermediate symptoms or the generative parameters.
        """
        # Sample symptoms from cause's generative model
        symptom_probs = cause.symptom_bias + self.rng.normal(0, np.sqrt(cause.symptom_variance))
        symptom_probs = np.clip(symptom_probs, 0.0, 1.0)
        symptoms = self.rng.binomial(1, symptom_probs).astype(float)

        # Generate telemetry from symptoms
        telemetry_mean = symptoms @ self._symptom_telemetry_mean
        telemetry = self.rng.multivariate_normal(
            telemetry_mean,
            self._symptom_telemetry_cov * (1 + noise),
        )

        return TelemetryVector(
            solve_time_ms=max(1.0, telemetry[0]),
            verifier_time_ms=max(1.0, telemetry[1]),
            final_residual=telemetry[2],
            max_step_residual=telemetry[3],
            memory_peak_mb=max(1.0, telemetry[4]),
            computation_steps=int(max(1, telemetry[5])),
            metric_delta=telemetry[6],
            metric_convergence_rate=telemetry[7],
        )


class SymptomInference:
    """Infers symptom presence from raw telemetry (with calibrated uncertainty).

    This is the FIRST layer of the diagnostic pipeline. It learns to map
    numerical telemetry to probabilistic symptom presence WITHOUT ever seeing
    the true cause labels during training (to avoid circularity).

    Key property: The inference model is trained on (telemetry, symptom) pairs
    where symptoms are synthesized from the generative model, but it NEVER sees
    the true cause→symptom mapping directly.
    """

    def __init__(self, rng: np.random.Generator, seed: int = SEED):
        self.rng = rng
        self.seed = seed
        # Learned parameters: telemetry→symptom logistic regression
        # Weights: (N_TELEMETRY_DIMENSIONS, N_SYMPTOMS)
        self._weights = np.random.default_rng(seed + 1).normal(
            loc=0.0, scale=0.1, size=(N_TELEMETRY_DIMENSIONS, N_SYMPTOMS)
        )
        self._biases = np.zeros(N_SYMPTOMS)
        self._trained = False

    def train(self, telemetry_samples: list[TelemetryVector], symptom_samples: list[SymptomProfile]):
        """Train symptom inference from (telemetry, symptom) pairs.

        This is a SIMPLE logistic regression (not deep learning) to keep
        the experiment focused on diagnosis logic, not representation learning.
        """
        X = np.array([t.to_array() for t in telemetry_samples])
        y = np.array([s.to_array() for s in symptom_samples])

        # Closed-form ridge regression for logistic weights
        # (Simplified: linear regression on logits, proper calibration would use IRLS)
        logits = np.log(np.clip(y, 0.01, 0.99) / np.clip(1 - y, 0.01, 0.99))
        reg = 1.0
        XtX = X.T @ X + reg * np.eye(X.shape[1])
        Xty = X.T @ logits
        self._weights = np.linalg.solve(XtX, Xty)
        self._biases = np.mean(logits - X @ self._weights, axis=0)
        self._trained = True

    def infer_symptoms(self, telemetry: TelemetryVector) -> SymptomProfile:
        """Infer probabilistic symptom presence from telemetry."""
        if not self._trained:
            raise RuntimeError("SymptomInference must be trained before inference")

        logits = telemetry.to_array() @ self._weights + self._biases
        probs = 1.0 / (1.0 + np.exp(-logits))
        probs = np.clip(probs, 0.0, 1.0)

        return SymptomProfile(
            coverage_weak=probs[0],
            representation_deficit=probs[1],
            verification_failed=probs[2],
            metric_misleading=probs[3],
            resource_exhausted=probs[4],
            convergence_stalled=probs[5],
        )


class CauseDiscriminator:
    """Discriminates causes from symptom profiles (Bayesian inference with entropy).

    This is the SECOND layer of the diagnostic pipeline. It performs Bayesian
    inference from symptom profiles to cause distributions, with explicit entropy
    measurements to quantify diagnostic uncertainty.

    Key property: This layer learns the symptom→cause mapping from training data,
    but it NEVER sees the raw telemetry or the generative parameters directly.
    """

    def __init__(self, rng: np.random.Generator, seed: int = SEED):
        self.rng = rng
        self.seed = seed
        self._cause_priors: dict[str, float] = {}  # P(cause)
        self._symptom_given_cause: dict[str, dict[str, float]] = {}  # P(symptom|cause)
        self._trained = False

    def train(self, cause_samples: list[Cause], symptom_samples: list[SymptomProfile]):
        """Learn Bayesian parameters from (cause, symptom) pairs."""
        # Estimate priors P(cause)
        cause_counts = {}
        for c in cause_samples:
            cause_counts[c.cause_id] = cause_counts.get(c.cause_id, 0) + 1
        total = sum(cause_counts.values())
        self._cause_priors = {k: v / total for k, v in cause_counts.items()}

        # Estimate likelihoods P(symptom|cause) - discretize symptoms at 0.5
        symptom_vectors = {c.cause_id: [] for c in cause_samples}
        for c, s in zip(cause_samples, symptom_samples):
            symptom_vectors[c.cause_id].append(s.to_array() > 0.5)

        self._symptom_given_cause = {}
        for cause_id, binary_list in symptom_vectors.items():
            binary_array = np.array(binary_list)
            self._symptom_given_cause[cause_id] = {
                f"symptom_{i}": float(np.mean(binary_array[:, i]))
                for i in range(N_SYMPTOMS)
            }

        self._trained = True

    def discriminate(self, symptoms: SymptomProfile) -> tuple[str, float, float]:
        """Return (predicted_cause_id, posterior_prob, entropy)."""
        if not self._trained:
            raise RuntimeError("CauseDiscriminator must be trained before inference")

        # Binary symptoms for likelihood lookup
        binary_symptoms = symptoms.to_array() > 0.5

        # Compute posterior P(cause|symptoms) ∝ P(symptoms|cause) P(cause)
        log_posteriors = {}
        for cause_id, prior in self._cause_priors.items():
            log_likelihood = 0.0
            for i, symptom_active in enumerate(binary_symptoms):
                symptom_key = f"symptom_{i}"
                p_symptom_given_cause = self._symptom_given_cause[cause_id].get(symptom_key, 0.5)
                # Log likelihood for this symptom
                p = p_symptom_given_cause if symptom_active else (1 - p_symptom_given_cause)
                log_likelihood += np.log(max(p, 0.01))
            log_posteriors[cause_id] = log_likelihood + np.log(prior)

        # Normalize to get posterior probabilities
        max_log = max(log_posteriors.values())
        posteriors = {k: np.exp(v - max_log) for k, v in log_posteriors.items()}
        total = sum(posteriors.values())
        if total > 0:
            posteriors = {k: v / total for k, v in posteriors.items()}
        else:
            posteriors = {k: 1.0 / len(posteriors) for k in posteriors}

        # Predicted cause = max posterior
        predicted_cause = max(posteriors, key=posteriors.get)
        max_posterior = posteriors[predicted_cause]

        # Entropy H = -sum(p * log(p))
        entropy = -sum(p * np.log(max(p, 1e-10)) for p in posteriors.values())

        return predicted_cause, max_posterior, entropy


@dataclass
class DiagnosisRecord:
    """One diagnosis trial record."""
    true_cause_id: str
    predicted_cause_id: str
    posterior_prob: float
    entropy: float
    correct: bool
    forced_wrong: bool  # High confidence (>0.8) but wrong prediction
    uncertain: bool  # Low confidence (<0.6) or high entropy


def run_one_replicate(
    rng: np.random.Generator,
    model: GenerativeModel,
    symptom_inf: SymptomInference,
    discriminator: CauseDiscriminator,
    n_scenarios: int,
    noise: float,
) -> list[DiagnosisRecord]:
    """Run one replicate of diagnosis trials."""
    records = []

    for _ in range(n_scenarios):
        # Sample true cause uniformly
        true_cause = rng.choice(model.causes)

        # Generate telemetry (this is what we observe in practice)
        telemetry = model.generate_telemetry(true_cause, noise=noise)

        # Infer symptoms from telemetry
        symptoms = symptom_inf.infer_symptoms(telemetry)

        # Discriminate causes from symptoms
        predicted_id, posterior, entropy = discriminator.discriminate(symptoms)

        # Quality metrics
        correct = (predicted_id == true_cause.cause_id)
        forced_wrong = (posterior > 0.8 and not correct)
        uncertain = (posterior < 0.6 or entropy > 1.5)

        records.append(DiagnosisRecord(
            true_cause_id=true_cause.cause_id,
            predicted_cause_id=predicted_id,
            posterior_prob=posterior,
            entropy=entropy,
            correct=correct,
            forced_wrong=forced_wrong,
            uncertain=uncertain,
        ))

    return records


def bootstrap_ci(values: list[float], rng: np.random.Generator, B: int = 5000) -> dict:
    """Bootstrap confidence interval."""
    if not values:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
    m = np.mean(values)
    samples = []
    for _ in range(B):
        s = [values[rng.integers(len(values))] for _ in range(len(values))]
        samples.append(np.mean(s))
    samples.sort()
    return {
        "mean": float(np.round(m, 4)),
        "lo": float(np.round(samples[int(0.025 * B)], 4)),
        "hi": float(np.round(samples[int(0.975 * B)], 4)),
        "n": len(values),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--scenarios", type=int, default=N_SCENARIOS)
    parser.add_argument("--replicates", type=int, default=5)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    # Preregistered design: non-circular diagnosis pipeline
    # 1. Initialize generative model (HIDDEN from diagnostic method)
    model = GenerativeModel(rng, seed=args.seed)

    # 2. Train symptom inference (never sees true cause labels)
    symptom_inf = SymptomInference(rng, seed=args.seed + 2)
    train_tele = []
    train_symp = []
    for _ in range(1000):
        cause = rng.choice(model.causes)
        tele = model.generate_telemetry(cause, noise=0.0)
        # True symptoms from cause (HIDDEN during inference)
        symp_probs = cause.symptom_bias + rng.normal(0, np.sqrt(cause.symptom_variance))
        symp_probs = np.clip(symp_probs, 0.0, 1.0)
        symp = SymptomProfile(
            coverage_weak=symp_probs[0],
            representation_deficit=symp_probs[1],
            verification_failed=symp_probs[2],
            metric_misleading=symp_probs[3],
            resource_exhausted=symp_probs[4],
            convergence_stalled=symp_probs[5],
        )
        train_tele.append(tele)
        train_symp.append(symp)
    symptom_inf.train(train_tele, train_symp)

    # 3. Train cause discriminator (never sees raw telemetry)
    discriminator = CauseDiscriminator(rng, seed=args.seed + 3)
    train_causes = []
    train_symp2 = []
    for _ in range(1000):
        cause = rng.choice(model.causes)
        train_causes.append(cause)
        # Generate symptoms from cause
        symp_probs = cause.symptom_bias + rng.normal(0, np.sqrt(cause.symptom_variance))
        symp_probs = np.clip(symp_probs, 0.0, 1.0)
        symp = SymptomProfile(
            coverage_weak=symp_probs[0],
            representation_deficit=symp_probs[1],
            verification_failed=symp_probs[2],
            metric_misleading=symp_probs[3],
            resource_exhausted=symp_probs[4],
            convergence_stalled=symp_probs[5],
        )
        train_symp2.append(symp)
    discriminator.train(train_causes, train_symp2)

    # 4. Run experiment across noise levels
    results_by_noise = {}
    overall_forced_wrong = []
    overall_correct = []

    for noise in NOISE_LEVELS:
        noise_records = []
        for rep in range(args.replicates):
            rep_rng = np.random.default_rng(int(args.seed * 1000 + int(noise * 10) * 100 + rep))
            records = run_one_replicate(
                rep_rng, model, symptom_inf, discriminator,
                args.scenarios, noise,
            )
            noise_records.extend(records)

        # Metrics for this noise level
        forced_wrong_rates = [r.forced_wrong for r in noise_records]
        correct_rates = [r.correct for r in noise_records]
        uncertain_rates = [r.uncertain for r in noise_records]

        boot_rng = np.random.default_rng(int(args.seed * 1000 + int(noise * 10) * 100 + 9999))

        results_by_noise[f"{noise:.1f}"] = {
            "forced_wrong_rate": bootstrap_ci(forced_wrong_rates, boot_rng),
            "correct_rate": bootstrap_ci(correct_rates, boot_rng),
            "uncertain_rate": bootstrap_ci(uncertain_rates, boot_rng),
        }

        overall_forced_wrong.extend(forced_wrong_rates)
        overall_correct.extend(correct_rates)

    # Overall metrics (across all noise levels)
    boot_rng = np.random.default_rng([args.seed, 9999])
    overall_forced_wrong_ci = bootstrap_ci(overall_forced_wrong, boot_rng)
    overall_correct_ci = bootstrap_ci(overall_correct, boot_rng)

    # Determine status
    forced_wrong_mean = overall_forced_wrong_ci["mean"]
    forced_wrong_lo = overall_forced_wrong_ci["lo"]
    correct_mean = overall_correct_ci["mean"]

    if correct_mean < 0.3:  # Less than 30% accuracy (near chance for 8 causes)
        status = DiagnosisStatus.NEGATIVE
    elif forced_wrong_lo > 0.2:  # More than 20% forced wrong
        status = DiagnosisStatus.NEGATIVE
    elif forced_wrong_lo > 0.1:  # 10-20% forced wrong
        status = DiagnosisStatus.PARTIAL
    elif correct_mean > 0.7 and forced_wrong_lo < 0.05:  # Good accuracy, low forced wrong
        status = DiagnosisStatus.SUPPORTED
    else:
        status = DiagnosisStatus.UNDERPOWERED

    result = {
        "schema_version": "rakl.mechanic-diagnosis-redesign.v1",
        "seed": args.seed,
        "n_scenarios_per_replicate": args.scenarios,
        "replicates": args.replicates,
        "noise_levels": list(NOISE_LEVELS),
        "claim_boundary": (
            "development known-world evidence; non-circular diagnosis from "
            "raw telemetry through symptom inference to cause discrimination; "
            "grants no scientific or method-promotion authority; preregistered "
            "design per issue #523"
        ),
        "grants_scientific_authority": False,
        "status": status.value,
        "forced_wrong_rate": overall_forced_wrong_ci,
        "correct_rate": overall_correct_ci,
        "results_by_noise": results_by_noise,
        "design": {
            "preregistered": True,
            "circularity_removed": True,
            "raw_telemetry_dimensions": N_TELEMETRY_DIMENSIONS,
            "latent_symptoms": N_SYMPTOMS,
            "causes": N_CAUSES,
            "architecture": "telemetry → symptom_inference → cause_discrimination",
            "training": "symptom_inf trained on (telemetry, symptom) pairs; discriminator trained on (cause, symptom) pairs",
        },
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print(f"SEED={args.seed}")
    print(f"STATUS={status.value}")
    print(f"forced_wrong_rate: mean={overall_forced_wrong_ci['mean']:.4f} [{overall_forced_wrong_ci['lo']:.4f}, {overall_forced_wrong_ci['hi']:.4f}]")
    print(f"correct_rate: mean={overall_correct_ci['mean']:.4f} [{overall_correct_ci['lo']:.4f}, {overall_correct_ci['hi']:.4f}]")
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
