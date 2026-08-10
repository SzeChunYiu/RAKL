from rakl.structural_benchmark_receipt import RECEIPT_SCHEMA_VERSION, build_receipt


def test_multifamily_receipt_captures_cheap_mechanism_gate() -> None:
    receipt = build_receipt(subject_sha="a" * 40)
    assert receipt["schema_version"] == RECEIPT_SCHEMA_VERSION
    assert receipt["subject_sha"] == "a" * 40
    assert receipt["case_count"] == 8
    assert receipt["hard_case_count"] == 6
    assert receipt["q2_all_licensed"] is True
    assert receipt["q3_all_rejected"] is True
    assert receipt["structural_gate_hard_case_accuracy"] == 1.0
    assert receipt["semantic_only_hard_case_accuracy"] == 0.0
    assert receipt["cheap_mechanism_gate_passed"] is True


def test_receipt_retains_failure_reasons_for_q3_decoys() -> None:
    receipt = build_receipt()
    q3 = [row for row in receipt["cases"] if row["quadrant"] == "Q3_HIGH_SEM_LOW_STRUCT"]
    assert len(q3) == 3
    for row in q3:
        assert row["structural_gate_decision"] == "REJECTED"
        assert row["reasons"]
        assert row["structurally_complete"] is False


def test_receipt_explicitly_denies_empirical_efficiency_claim() -> None:
    boundary = build_receipt()["claim_boundary"]
    assert "not empirical evidence" in boundary
    assert "training efficiency" in boundary
    assert "inference efficiency" in boundary
