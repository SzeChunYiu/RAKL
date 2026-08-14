"""Tests for the gate-falsifiability battery.

Both directions are covered deliberately. A battery that always said
NON_FALSIFIABLE would catch the Paper II gate and be useless; one that always said
FALSIFIABLE would be worse, because it would look like reassurance.

The central test reconstructs the actual Paper II failure shape — coordinates
computed from a pre-parsed field while the text the benchmark claims to measure is
ignored — and requires the battery to catch it.
"""

from __future__ import annotations

import pytest

from rakl.gate_falsifiability import (
    GateFalsifiability,
    ProbeOutcome,
    audit_gate,
    drop_fraction,
    scramble_text_field,
    shuffle_field,
    zero_variance_arms,
)

# A benchmark row: `text` is what the gate CLAIMS to read, `parsed` is what it
# actually reads. In the Paper II lane these agreed by construction, which is why
# the defect was invisible until the text was scrambled independently.
EVIDENCE = [
    {"text": f"source span number {i} describing a transfer", "parsed": i % 3, "gold": i % 3}
    for i in range(60)
]


def _gate_reading_parsed(rows) -> bool:
    """The Paper II defect: scores against a pre-parsed field, never the text."""
    correct = sum(1 for row in rows if row["parsed"] == row["gold"])
    return correct / max(1, len(rows)) >= 0.9


def _gate_reading_text(rows) -> bool:
    """An honest gate: extracts from the text, so scrambling it must hurt."""
    correct = 0
    for row in rows:
        text = row["text"]
        # crude but genuine extraction: recover the index token from the span
        tokens = [t for t in text.split() if t.isdigit()]
        predicted = int(tokens[0]) % 3 if tokens else -1
        if predicted == row["gold"]:
            correct += 1
    return correct / max(1, len(rows)) >= 0.9


PERTURBATIONS = {
    "scramble_text": scramble_text_field("text"),
    "shuffle_gold": shuffle_field("gold"),
    "drop_half": drop_fraction(0.5),
}


def test_paper2_failure_shape_is_caught():
    """The decisive case: a gate that ignores the text it claims to measure."""
    report = audit_gate(
        _gate_reading_parsed, EVIDENCE, gate_id="parsed-field-gate", perturbations={
            "scramble_text": PERTURBATIONS["scramble_text"],
        },
    )
    assert report.verdict is GateFalsifiability.NON_FALSIFIABLE
    assert report.supports_confirmatory_use is False
    assert "scramble_text" in report.reasons[1]


def test_honest_gate_is_falsifiable():
    """The no-alarm case: a gate that really reads the text must pass the audit."""
    report = audit_gate(
        _gate_reading_text, EVIDENCE, gate_id="text-gate", perturbations={
            "scramble_text": PERTURBATIONS["scramble_text"],
        },
    )
    assert report.verdict is GateFalsifiability.FALSIFIABLE
    assert report.supports_confirmatory_use is True
    assert "scramble_text" in report.sensitive_probes


def test_gold_shuffle_separates_the_two_gates():
    """Shuffling labels must break an honest gate and is a second independent probe."""
    honest = audit_gate(_gate_reading_text, EVIDENCE, gate_id="text",
                        perturbations={"shuffle_gold": PERTURBATIONS["shuffle_gold"]})
    assert honest.verdict is GateFalsifiability.FALSIFIABLE


def test_always_pass_gate_is_non_falsifiable():
    report = audit_gate(lambda rows: True, EVIDENCE, gate_id="always",
                        perturbations=PERTURBATIONS)
    assert report.verdict is GateFalsifiability.NON_FALSIFIABLE
    assert report.sensitive_probes == ()
    assert all(p.outcome is ProbeOutcome.INSENSITIVE for p in report.probes)


def test_gate_already_failing_is_trivially_falsifiable():
    report = audit_gate(lambda rows: False, EVIDENCE, gate_id="fails",
                        perturbations=PERTURBATIONS)
    assert report.verdict is GateFalsifiability.FALSIFIABLE
    assert report.baseline_pass is False
    assert "fails on unperturbed evidence" in report.reasons[0]


def test_unprobed_gate_is_an_error_not_a_pass():
    """Supplying no perturbation must raise; an unprobed gate is unaudited."""
    with pytest.raises(ValueError, match="unprobed gate is unaudited"):
        audit_gate(lambda rows: True, EVIDENCE, gate_id="x", perturbations={})


def test_raising_gate_is_cannot_check_not_falsifiable():
    def boom(rows):
        raise RuntimeError("gate exploded")

    report = audit_gate(boom, EVIDENCE, gate_id="boom", perturbations=PERTURBATIONS)
    assert report.verdict is GateFalsifiability.CANNOT_CHECK
    assert report.supports_confirmatory_use is False


def test_probe_that_always_raises_is_cannot_check():
    def bad_perturb(evidence, rng):
        raise RuntimeError("perturbation exploded")

    report = audit_gate(lambda rows: True, EVIDENCE, gate_id="x",
                        perturbations={"broken": bad_perturb})
    assert report.verdict is GateFalsifiability.CANNOT_CHECK
    assert report.probes[0].outcome is ProbeOutcome.CANNOT_CHECK


def test_audit_is_deterministic():
    """Same seed, same verdict — an audit that drifts cannot be cited."""
    kwargs = dict(gate_id="always", perturbations=PERTURBATIONS, seed=7)
    first = audit_gate(lambda rows: True, EVIDENCE, **kwargs)
    second = audit_gate(lambda rows: True, EVIDENCE, **kwargs)
    assert [(p.probe_id, p.flips) for p in first.probes] == [
        (p.probe_id, p.flips) for p in second.probes
    ]


# --- degenerate-arm detection ------------------------------------------------------


def test_zero_variance_arm_is_detected():
    """The Paper II `full` arm had variance 1.2e-37 and healthy-looking CIs."""
    arms = {"full": [0.0004] * 50, "mechanism": [0.1, 0.4, 0.25, 0.9, 0.33]}
    assert zero_variance_arms(arms) == ("full",)


def test_varying_arms_are_not_flagged():
    """No-alarm case: genuinely varying arms must not be reported degenerate."""
    arms = {"a": [0.1, 0.2, 0.3], "b": [0.9, 0.4, 0.6]}
    assert zero_variance_arms(arms) == ()


def test_single_observation_arm_is_degenerate():
    """One observation has no variance to speak of and cannot support a pairing."""
    assert zero_variance_arms({"solo": [0.5]}) == ("solo",)


# --- validation against a real repository gate -------------------------------------


def test_real_saturation_gate_is_falsifiable():
    """Validate the battery on live repo machinery, not only on reconstructions.

    A checker validated purely against its own fixtures can miss whole classes of
    defect. `audit_bounded_epistemic_saturation` is a real, shipped gate, and it
    SHOULD be falsifiable — one substantive-growth round must be able to reopen a
    saturated state. If this ever reports NON_FALSIFIABLE, either the saturation
    gate regressed into a rubber stamp or this battery stopped working.
    """
    from rakl.epistemic_saturation import (
        EpistemicGrowthVector,
        OperatorOrderAudit,
        SaturationBasis,
        SaturationRound,
        SaturationStatus,
        audit_bounded_epistemic_saturation,
    )

    basis = SaturationBasis(
        basis_id="falsifiability-probe",
        scope="probe",
        identity_policy_id="idp",
        route_family_version="rf",
        novelty_policy_id="nov",
        evidence_policy_id="evp",
    )
    order_audit = OperatorOrderAudit(
        audit_id="probe",
        expand_then_consolidate_digest="a" * 64,
        consolidate_then_expand_digest="b" * 64,
        substantive_difference=EpistemicGrowthVector(),
        evidence_ids=("probe",),
    )

    def make_round(round_id: str, mechanisms: int) -> SaturationRound:
        return SaturationRound(
            round_id=round_id,
            basis_fingerprint=basis.fingerprint,
            growth=EpistemicGrowthVector(mechanisms_added=mechanisms),
            bounded_discovery_closed=True,
            route_coverage_stable=True,
            omission_audit_passed=True,
            nearest_work_audit_passed=True,
            operator_order_audit=order_audit,
            freshness_cutoff="2030-01-01",
        )

    # Evidence is a saturated sequence: three fully flat, fully audited rounds.
    evidence = [{"round_id": f"flat-{i}", "mechanisms": 0} for i in range(3)]

    def gate(rows) -> bool:
        rounds = [make_round(r["round_id"], r["mechanisms"]) for r in rows]
        report = audit_bounded_epistemic_saturation(rounds, basis=basis)
        return report.status is SaturationStatus.BOUNDED_SATURATED

    assert gate(evidence) is True, "control sequence must saturate, else the probe is vacuous"

    def inject_growth(rows, rng):
        mutated = [dict(r) for r in rows]
        mutated[rng.randrange(len(mutated))]["mechanisms"] = 1
        return mutated

    report = audit_gate(
        gate, evidence, gate_id="audit_bounded_epistemic_saturation",
        perturbations={"inject_substantive_growth": inject_growth},
    )
    assert report.verdict is GateFalsifiability.FALSIFIABLE
    assert report.supports_confirmatory_use is True
