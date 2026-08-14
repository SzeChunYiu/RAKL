"""Can this gate fail?

A gate that cannot fail is worse than no gate. It consumes a confirmatory budget,
emits a PASS, and licenses a claim the evidence never supported — while looking
exactly like a successful result.

This module generalizes the probe battery that caught such a gate in the Paper II
six-family lane, where the registered gate passed 6/6 at p=0.03125 and was then
shown to be structurally incapable of failing: scrambling every source and target
text left all coordinates unchanged 810/810, one arm of the "paired" statistic had
variance 1.2e-37, and 12/12 arbitrary seeds passed.

The battery is deliberately **black-box**. It perturbs the evidence a gate is fed
and observes whether the verdict ever moves. That catches non-falsifiability
arising from any cause — degenerate statistics, gold leakage, coordinates computed
from the wrong fields — without needing to model the gate internally, and without
the gate's author having anticipated the failure mode.

Self-RAKL note: this audits *our own* evidence apparatus. It grants no scientific
authority and makes no claim true; a FALSIFIABLE verdict means only that the gate
is capable of failing, never that its PASS is correct.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import random
import statistics


class ProbeOutcome(str, Enum):
    #: The perturbation moved the verdict — the gate depends on what was perturbed.
    SENSITIVE = "SENSITIVE"
    #: The perturbation never moved the verdict across every trial.
    INSENSITIVE = "INSENSITIVE"
    #: The probe could not be evaluated.
    CANNOT_CHECK = "CANNOT_CHECK"


class GateFalsifiability(str, Enum):
    FALSIFIABLE = "FALSIFIABLE"
    NON_FALSIFIABLE = "NON_FALSIFIABLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    outcome: ProbeOutcome
    trials: int
    flips: int
    detail: str


@dataclass(frozen=True)
class FalsifiabilityReport:
    gate_id: str
    baseline_pass: bool
    probes: tuple[ProbeResult, ...]
    verdict: GateFalsifiability
    reasons: tuple[str, ...]

    @property
    def sensitive_probes(self) -> tuple[str, ...]:
        return tuple(p.probe_id for p in self.probes if p.outcome is ProbeOutcome.SENSITIVE)

    @property
    def supports_confirmatory_use(self) -> bool:
        """A gate may back a confirmatory claim only if it could have failed."""
        return self.verdict is GateFalsifiability.FALSIFIABLE


def zero_variance_arms(
    arms: Mapping[str, Sequence[float]], *, tolerance: float = 1e-12
) -> tuple[str, ...]:
    """Arms whose values are effectively constant.

    A paired statistic with a constant arm is not a comparison. In the Paper II
    lane the ``full`` arm was bound to the verifier and carried variance 1.2e-37,
    which no conventional power analysis flags — the confidence intervals looked
    healthy precisely because one side never moved.
    """
    degenerate: list[str] = []
    for name, values in arms.items():
        if len(values) < 2:
            degenerate.append(name)
            continue
        if statistics.pvariance(values) <= tolerance:
            degenerate.append(name)
    return tuple(degenerate)


def audit_gate(
    gate: Callable[[Sequence[object]], bool],
    evidence: Sequence[object],
    *,
    gate_id: str,
    perturbations: Mapping[str, Callable[[Sequence[object], random.Random], Sequence[object]]],
    trials: int = 32,
    seed: int = 20260814,
) -> FalsifiabilityReport:
    """Probe whether ``gate`` can ever return False.

    ``gate`` maps evidence to True (pass) or False (fail). Each perturbation
    receives the evidence and a seeded RNG and returns perturbed evidence. A gate
    that passes under *every* perturbation of *every* kind is reported
    NON_FALSIFIABLE.

    The perturbations are supplied by the caller because what counts as
    signal-destroying is domain knowledge: scrambling text is decisive for an
    extraction benchmark and meaningless for a numeric one. Supplying none is an
    error rather than a silent pass.
    """
    if not perturbations:
        raise ValueError("at least one perturbation is required; an unprobed gate is unaudited")
    if trials < 1:
        raise ValueError("trials must be positive")

    try:
        baseline = bool(gate(evidence))
    except Exception as exc:
        return FalsifiabilityReport(
            gate_id=gate_id,
            baseline_pass=False,
            probes=(),
            verdict=GateFalsifiability.CANNOT_CHECK,
            reasons=(f"gate raised on unperturbed evidence: {exc!r}",),
        )

    if not baseline:
        # The gate already fails on the real evidence, so it is trivially capable
        # of failing. Report that rather than probing for a flip that is moot.
        return FalsifiabilityReport(
            gate_id=gate_id,
            baseline_pass=False,
            probes=(),
            verdict=GateFalsifiability.FALSIFIABLE,
            reasons=("gate fails on unperturbed evidence",),
        )

    results: list[ProbeResult] = []
    for probe_id, perturb in sorted(perturbations.items()):
        flips = 0
        errors = 0
        for trial in range(trials):
            rng = random.Random(f"{seed}:{probe_id}:{trial}")
            try:
                perturbed = perturb(evidence, rng)
                if not bool(gate(perturbed)):
                    flips += 1
            except Exception:
                errors += 1
        if errors == trials:
            outcome, detail = ProbeOutcome.CANNOT_CHECK, f"all {trials} trials raised"
        elif flips:
            outcome = ProbeOutcome.SENSITIVE
            detail = f"verdict moved in {flips}/{trials} trials"
        else:
            outcome = ProbeOutcome.INSENSITIVE
            detail = (
                f"verdict unchanged in all {trials} trials — the gate does not "
                f"depend on what '{probe_id}' perturbs"
            )
        results.append(ProbeResult(probe_id, outcome, trials, flips, detail))

    probes = tuple(results)
    if any(p.outcome is ProbeOutcome.SENSITIVE for p in probes):
        return FalsifiabilityReport(
            gate_id=gate_id,
            baseline_pass=True,
            probes=probes,
            verdict=GateFalsifiability.FALSIFIABLE,
            reasons=(),
        )

    if all(p.outcome is ProbeOutcome.CANNOT_CHECK for p in probes):
        return FalsifiabilityReport(
            gate_id=gate_id,
            baseline_pass=True,
            probes=probes,
            verdict=GateFalsifiability.CANNOT_CHECK,
            reasons=("every probe failed to execute",),
        )

    insensitive = tuple(p.probe_id for p in probes if p.outcome is ProbeOutcome.INSENSITIVE)
    return FalsifiabilityReport(
        gate_id=gate_id,
        baseline_pass=True,
        probes=probes,
        verdict=GateFalsifiability.NON_FALSIFIABLE,
        reasons=(
            "no perturbation moved the verdict",
            f"insensitive to: {', '.join(insensitive)}",
        ),
    )


# --- reusable perturbations --------------------------------------------------------


def shuffle_field(field: str) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Permute one mapping field across records, breaking its row alignment.

    This is the generalized form of the probe that proved decisive for Paper II:
    if realigning a field at random never changes the verdict, the gate is not
    reading that field.
    """

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = [dict(row) for row in evidence]  # type: ignore[arg-type]
        values = [row.get(field) for row in rows]
        rng.shuffle(values)
        for row, value in zip(rows, values):
            row[field] = value
        return rows

    return perturb


def scramble_text_field(field: str) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Scramble the characters of a text field, destroying its content but not its shape."""

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = [dict(row) for row in evidence]  # type: ignore[arg-type]
        for row in rows:
            text = row.get(field)
            if isinstance(text, str):
                chars = list(text)
                rng.shuffle(chars)
                row[field] = "".join(chars)
        return rows

    return perturb


def drop_fraction(fraction: float) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Drop a random fraction of records, testing sensitivity to sample size."""
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must lie strictly between 0 and 1")

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        keep = max(1, int(len(evidence) * (1.0 - fraction)))
        return rng.sample(list(evidence), keep)

    return perturb
