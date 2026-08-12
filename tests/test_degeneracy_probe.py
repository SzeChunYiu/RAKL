"""Validation for the degeneracy probe harness.

A probe that fires on everything gets switched off; a probe that fires on
nothing is the very defect it hunts. Both directions are therefore asserted, and
the no-alarm cases are checked against a **real** surface, not only synthetic
fixtures.

Planted-degenerate cases reproduce the shapes actually found in this repository:
a label that is an exact boolean AND of its own features (Paper 3 v1 gate,
44/44), an identifier that restates its answer (authority-leakage V1 panel), and
a treatment prompt carrying the gold answer key (Paper 2 microtrial).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.degeneracy_probe import (
    EXIT_CODES,
    ArmPair,
    CouplingKind,
    DegeneracyStatus,
    LabeledRecord,
    probe_arm_answer_leak,
    probe_blind_responder,
    probe_boolean_combination,
    probe_decoupling,
    probe_records,
    probe_single_feature,
)

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "research/paper2_microtrial_v1"


# --------------------------------------------------------------------------
# Type A — planted degenerate shapes must be caught
# --------------------------------------------------------------------------


def _and_gate_records(n: int = 44) -> list[LabeledRecord]:
    """The Paper 3 v1 gate shape: label == AND(four witness features)."""

    records = []
    for index in range(n):
        bits = [bool(index & (1 << k)) for k in range(4)]
        records.append(
            LabeledRecord(
                f"case-{index:02d}",
                {
                    "invariant": bits[0],
                    "boundary": bits[1],
                    "qoi": bits[2],
                    "directional": bits[3],
                },
                all(bits),
            )
        )
    return records


def test_boolean_and_of_features_is_caught() -> None:
    findings = probe_boolean_combination(_and_gate_records(), surface="paper3-shape")
    assert findings, "an exact AND of the graded features must be reported"
    finding = findings[0]
    assert finding.status is DegeneracyStatus.DEGENERATE
    assert finding.coupling is CouplingKind.AUTHORED_FROM_LABEL
    assert "label ==" in finding.detail and "AND(" in finding.detail
    assert finding.coverage == 1.0


def test_identifier_restating_the_answer_is_caught() -> None:
    """The authority-leakage V1 shape: ``case_id`` names its own verdict."""

    records = [
        LabeledRecord("r1", {"case_id": "ALR-01-prediction-not-mechanism"},
                      "PREDICTION_NOT_MECHANISM"),
        LabeledRecord("r2", {"case_id": "ALR-07-legitimate-mechanism-upgrade"},
                      "LEGITIMATE_MECHANISM_UPGRADE"),
        LabeledRecord("r3", {"case_id": "ALR-02-prediction-not-mechanism"},
                      "PREDICTION_NOT_MECHANISM"),
        LabeledRecord("r4", {"case_id": "ALR-08-legitimate-mechanism-upgrade"},
                      "LEGITIMATE_MECHANISM_UPGRADE"),
    ]
    findings = probe_single_feature(records, surface="alr-v1-shape")
    assert findings
    assert findings[0].probe == "identifier_restates_label"
    assert findings[0].status is DegeneracyStatus.DEGENERATE
    assert findings[0].coupling is CouplingKind.AUTHORED_FROM_LABEL


def test_opaque_identifier_does_not_alarm() -> None:
    """A neutral id must not be flagged merely for being an id.

    This is the repair c154 applied to the V2 twin, so the probe has to agree
    that the repaired shape is clean — otherwise it would condemn the fix.
    """

    records = [
        LabeledRecord("r1", {"case_id": "ALR-01-a3f9"}, "PREDICTION_NOT_MECHANISM"),
        LabeledRecord("r2", {"case_id": "ALR-07-7b21"}, "LEGITIMATE_MECHANISM_UPGRADE"),
        LabeledRecord("r3", {"case_id": "ALR-02-c04e"}, "PREDICTION_NOT_MECHANISM"),
        LabeledRecord("r4", {"case_id": "ALR-08-1d55"}, "LEGITIMATE_MECHANISM_UPGRADE"),
    ]
    assert probe_single_feature(records, surface="alr-v2-shape") == ()


def test_semantic_restatement_is_a_documented_blind_spot() -> None:
    """Stated limitation, asserted so it cannot be forgotten.

    Token overlap catches an identifier that *literally* restates its answer. An
    identifier that restates it only semantically — ``prediction-not-mechanism``
    against a ``REFUSE`` verdict — shares no tokens and is NOT auto-detected.
    Catching that requires a domain responder, which is exactly why c154 had to
    hand-write ``case_id_exploit_responder``. Claiming otherwise would make this
    module overstate its own coverage.
    """

    records = [
        LabeledRecord("r1", {"case_id": "ALR-01-prediction-not-mechanism"}, "REFUSE"),
        LabeledRecord("r2", {"case_id": "ALR-07-legitimate-mechanism-upgrade"}, "GRANT"),
        LabeledRecord("r3", {"case_id": "ALR-02-prediction-not-mechanism"}, "REFUSE"),
        LabeledRecord("r4", {"case_id": "ALR-08-legitimate-mechanism-upgrade"}, "GRANT"),
    ]
    assert probe_single_feature(records, surface="semantic-shape") == ()

    # A supplied domain responder does catch it, which is the required workflow.
    def exploit(record: LabeledRecord) -> str:
        case_id = str(record.features["case_id"])
        return "REFUSE" if "not-mechanism" in case_id else "GRANT"

    findings = probe_blind_responder(
        records, exploit, responder_name="case_id_exploit", surface="semantic-shape"
    )
    assert findings and findings[0].status is DegeneracyStatus.DEGENERATE


def test_blind_responder_beating_chance_is_caught() -> None:
    """A responder reading only the identifier must not be able to score."""

    records = [
        LabeledRecord("r1", {"case_id": "x-REFUSE-1"}, "REFUSE"),
        LabeledRecord("r2", {"case_id": "x-GRANT-1"}, "GRANT"),
        LabeledRecord("r3", {"case_id": "x-REFUSE-2"}, "REFUSE"),
        LabeledRecord("r4", {"case_id": "x-GRANT-2"}, "GRANT"),
    ]

    def exploit(record: LabeledRecord) -> str:
        return "REFUSE" if "REFUSE" in str(record.features["case_id"]) else "GRANT"

    findings = probe_blind_responder(
        records, exploit, responder_name="case_id_exploit", surface="blind-shape"
    )
    assert findings
    assert findings[0].status is DegeneracyStatus.DEGENERATE
    assert findings[0].coverage == 1.0
    assert findings[0].baseline == 0.5


# --------------------------------------------------------------------------
# Type A — the no-alarm case. A feature correlated with a label is what a
# feature IS; only authorship from the label is a validity defect.
# --------------------------------------------------------------------------


def test_correlated_but_non_determining_features_do_not_alarm() -> None:
    """Signal without determination must stay silent, or the probe is useless."""

    records = [
        LabeledRecord("r1", {"score": 0.9, "family": "a"}, True),
        LabeledRecord("r2", {"score": 0.8, "family": "a"}, True),
        LabeledRecord("r3", {"score": 0.7, "family": "a"}, False),
        LabeledRecord("r4", {"score": 0.2, "family": "b"}, False),
        LabeledRecord("r5", {"score": 0.1, "family": "b"}, False),
        LabeledRecord("r6", {"score": 0.3, "family": "b"}, True),
    ]
    report = probe_records(records, surface="clean-shape")
    assert report.status is DegeneracyStatus.CLEAN, [f.detail for f in report.findings]
    assert report.findings == ()
    assert report.exit_code == 0


def test_deterministic_non_identifier_feature_is_escalated_not_condemned() -> None:
    """A real feature that happens to separate perfectly needs a human, not a verdict.

    Reporting this as DEGENERATE would make the probe cry wolf on any strongly
    predictive measurement, which is how a checker gets switched off.
    """

    records = [
        LabeledRecord("r1", {"threshold_exceeded": "yes"}, True),
        LabeledRecord("r2", {"threshold_exceeded": "yes"}, True),
        LabeledRecord("r3", {"threshold_exceeded": "no"}, False),
        LabeledRecord("r4", {"threshold_exceeded": "no"}, False),
    ]
    findings = probe_single_feature(records, surface="suspect-shape")
    assert findings
    assert findings[0].status is DegeneracyStatus.SUSPECT
    assert findings[0].coupling is CouplingKind.DETERMINISTIC


def test_majority_responder_does_not_alarm_on_a_balanced_panel() -> None:
    records = [
        LabeledRecord("r1", {"a": 1}, True),
        LabeledRecord("r2", {"a": 2}, False),
        LabeledRecord("r3", {"a": 3}, True),
        LabeledRecord("r4", {"a": 4}, False),
    ]
    findings = probe_blind_responder(
        records, lambda _r: True, responder_name="always_true", surface="balanced"
    )
    assert findings == ()


# --------------------------------------------------------------------------
# CANNOT_CHECK is not a pass
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "records,reason_fragment",
    [
        ([], "nothing was probed"),
        (
            [LabeledRecord("r1", {"a": 1}), LabeledRecord("r2", {"a": 2})],
            "no machine-extractable label",
        ),
        (
            [
                LabeledRecord("r1", {"a": 1}, True),
                LabeledRecord("r2", {"a": 2}, True),
            ],
            "same label",
        ),
    ],
    ids=["empty", "unlabelled", "constant-label"],
)
def test_unprobeable_surfaces_report_cannot_check(records, reason_fragment) -> None:
    report = probe_records(records, surface="unprobeable")
    assert report.status is DegeneracyStatus.CANNOT_CHECK
    assert any(reason_fragment in reason for reason in report.reasons)
    assert report.exit_code == 3


def test_every_status_has_a_distinct_exit_code() -> None:
    assert len(set(EXIT_CODES.values())) == len(DegeneracyStatus)
    assert EXIT_CODES[DegeneracyStatus.CLEAN] == 0
    assert EXIT_CODES[DegeneracyStatus.CANNOT_CHECK] != EXIT_CODES[DegeneracyStatus.CLEAN]


# --------------------------------------------------------------------------
# Type B — the dangerous class, checked against the real arm pair
# --------------------------------------------------------------------------


def _v1_gold() -> dict[str, frozenset[str]]:
    payload = json.loads((V1 / "EVALUATOR_PROTOCOL.json").read_text(encoding="utf-8"))
    return {
        "misaligned_source_ids": frozenset(payload["misaligned_source_ids"]),
        "required_refuted_source_ids": frozenset(payload["required_refuted_source_ids"]),
    }


@pytest.mark.skipif(not V1.is_dir(), reason="microtrial v1 corpus absent")
def test_real_v1_treatment_arm_leaks_the_gold_answer_key() -> None:
    """Regression pin on a verified live finding.

    Two leaking lines, hand-checked: the S4/S5 pair tagged
    ``CONTEXT_MISALIGNED_FOR_DIRECT_CONTRADICTION`` (gold ``misaligned_source_ids``)
    and the S6 line "retained as negative history" (gold
    ``required_refuted_source_ids``). Neither string occurs in the control arm.
    """

    report = probe_arm_answer_leak(
        ArmPair(
            "paper2_microtrial_v1",
            (V1 / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
            (V1 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
            _v1_gold(),
        )
    )
    assert report.status is DegeneracyStatus.DEGENERATE
    assert report.exit_code == 1
    # Two leak SITES, not one per marker: several markers on one line are one leak.
    assert len(report.findings) == 2
    fields = {f.detail.split("graded field ")[1].split(";")[0] for f in report.findings}
    assert fields == {"'misaligned_source_ids'", "'required_refuted_source_ids'"}
    assert all(f.coupling is CouplingKind.AUTHORED_FROM_LABEL for f in report.findings)


@pytest.mark.skipif(not V1.is_dir(), reason="microtrial v1 corpus absent")
def test_probe_ignores_the_legitimate_differential_vocabulary() -> None:
    """The precision case, on real data.

    The treatment arm has dozens of tokens the control arm lacks — RAKL framing
    that is supposed to differ between arms. The probe must fire only on markers
    whose co-occurrence set reproduces a gold answer, and stay silent on the rest.
    Hard-coding the known marker strings would pass this trivially and find
    nothing else, so the vocabulary is derived from the arm diff.
    """

    report = probe_arm_answer_leak(
        ArmPair(
            "paper2_microtrial_v1",
            (V1 / "RAKL_CONTEXT_PROMPT.txt").read_text(encoding="utf-8"),
            (V1 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8"),
            _v1_gold(),
        )
    )
    differential = int(report.reasons[0].split()[0])
    assert differential >= 20, "expected a substantial differential vocabulary"
    implicated = sum(len(f.evidence) for f in report.findings)
    assert implicated <= 4, "probe should implicate a handful of lines, not the corpus"


@pytest.mark.skipif(not V1.is_dir(), reason="microtrial v1 corpus absent")
def test_identical_arms_produce_no_finding() -> None:
    """No differential vocabulary means no leak channel to report."""

    direct = (V1 / "DIRECT_CORPUS_PROMPT.txt").read_text(encoding="utf-8")
    report = probe_arm_answer_leak(
        ArmPair("self-comparison", direct, direct, _v1_gold())
    )
    assert report.status is DegeneracyStatus.CLEAN
    assert report.findings == ()


def test_synthetic_clean_arm_pair_with_rich_differential_does_not_alarm() -> None:
    """Treatment-only vocabulary that carries no answer must not be reported."""

    treatment = "\n".join(
        [
            "STRUCTURED CONTEXT MAP",
            '{"source_id": "S1", "projection": "supports the target"}',
            '{"source_id": "S2", "projection": "supports the target"}',
            '{"source_id": "S3", "projection": "supports the target"}',
            '{"source_id": "S4", "projection": "supports the target"}',
        ]
    )
    control = "S1 S2 S3 S4 raw corpus"
    report = probe_arm_answer_leak(
        ArmPair(
            "synthetic-clean",
            treatment,
            control,
            {"misaligned_source_ids": frozenset({"S4"})},
        )
    )
    assert report.status is DegeneracyStatus.CLEAN, [
        f.detail for f in report.findings
    ]


def test_synthetic_planted_leak_is_caught() -> None:
    """The same corpus, with one line that tags exactly the gold answer."""

    treatment = "\n".join(
        [
            "STRUCTURED CONTEXT MAP",
            '{"source_id": "S1", "projection": "supports the target"}',
            '{"source_id": "S2", "projection": "supports the target"}',
            '{"source_id": "S3", "projection": "supports the target"}',
            '{"source_id": "S4", "relation": "CONTEXT_MISALIGNED"}',
        ]
    )
    control = "S1 S2 S3 S4 raw corpus"
    report = probe_arm_answer_leak(
        ArmPair(
            "synthetic-planted",
            treatment,
            control,
            {"misaligned_source_ids": frozenset({"S4"})},
        )
    )
    assert report.status is DegeneracyStatus.DEGENERATE
    assert len(report.findings) == 1
    assert "CONTEXT_MISALIGNED" in report.findings[0].detail


def test_missing_gold_reports_cannot_check_not_clean() -> None:
    report = probe_arm_answer_leak(ArmPair("no-gold", "S1 S2 marker", "S1 S2", {}))
    assert report.status is DegeneracyStatus.CANNOT_CHECK
    assert report.exit_code == 3


# --------------------------------------------------------------------------
# Decoupling rate: near-determinism, which exact-match probes miss
# --------------------------------------------------------------------------

W = ("invariant", "boundary", "qoi", "directional")


def _decoupling_records(n_decoupled: int, n_total: int = 16) -> list[LabeledRecord]:
    records = []
    for index in range(n_total):
        witnesses = {name: True for name in W}
        label = index >= n_decoupled  # first n_decoupled break AND == label
        records.append(LabeledRecord(f"c{index:02d}", witnesses, label))
    return records


def test_exact_and_is_degenerate() -> None:
    findings = probe_decoupling(_decoupling_records(0), W, surface="exact-and")
    assert findings[0].status is DegeneracyStatus.DEGENERATE
    assert findings[0].coupling is CouplingKind.AUTHORED_FROM_LABEL
    assert findings[0].coverage == 0.0


def test_few_decoupled_records_are_suspect_not_clean() -> None:
    """The gap this probe exists to close.

    ``probe_boolean_combination`` fires only on exact reproduction, so a label
    agreeing with AND on 13 of 16 records passes as CLEAN — even though the
    panel's informativeness rests entirely on the 3 that decouple.
    """

    records = _decoupling_records(3)
    assert probe_boolean_combination(records, surface="near") == ()
    findings = probe_decoupling(records, W, surface="near", min_decoupled=4)
    assert findings[0].status is DegeneracyStatus.SUSPECT
    assert abs(findings[0].coverage - 3 / 16) < 1e-9


def test_enough_decoupled_records_is_clean() -> None:
    findings = probe_decoupling(_decoupling_records(8), W, surface="ok", min_decoupled=4)
    assert findings[0].status is DegeneracyStatus.CLEAN


def test_stratum_with_zero_decoupled_records_is_flagged() -> None:
    """A fold tested on such a stratum cannot distinguish judgement from the AND."""

    records = _decoupling_records(6)
    strata = {r.record_id: ("A" if i < 8 else "B") for i, r in enumerate(records)}
    findings = probe_decoupling(
        records, W, surface="strata", strata=strata, min_decoupled=4
    )
    assert findings[0].status is DegeneracyStatus.SUSPECT
    assert any("ZERO decoupled" in item for item in findings[0].evidence)


def test_missing_witness_fields_report_cannot_check() -> None:
    records = [LabeledRecord("c0", {"other": True}, True)]
    findings = probe_decoupling(records, W, surface="missing")
    assert findings[0].status is DegeneracyStatus.CANNOT_CHECK
