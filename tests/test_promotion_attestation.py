from rakl.promotion_attestation import (
    PromotionAttestationPacket,
    PromotionAttestationVerdict,
    attest_promotion_state,
)


CANDIDATE = "b" * 40
MAIN = "c" * 40


def packet(**overrides) -> PromotionAttestationPacket:
    values = {
        "candidate_sha": CANDIDATE,
        "claimed_promoted_sha": CANDIDATE,
        "observed_main_sha": MAIN,
        "candidate_exists": True,
        "claimed_promoted_exists": True,
        "main_descends_from_candidate": True,
        "required_active_paths_match": True,
        "candidate_ci_exact_sha": True,
        "postpromotion_ci_exact_active_main": True,
        "history_preserved": True,
        "ref_observation_stable": True,
        "validation_doc_present": False,
        "pr_merged": None,
        "explicit_supersession": False,
    }
    values.update(overrides)
    return PromotionAttestationPacket(**values)


def verdict(**overrides) -> PromotionAttestationVerdict:
    return attest_promotion_state(packet(**overrides)).verdict


def test_green_gate_or_candidate_ci_does_not_prove_ref_moved():
    assert verdict(main_descends_from_candidate=False) == PromotionAttestationVerdict.NOT_PROMOTED


def test_nonexistent_claimed_promoted_sha_refutes_validation_claim():
    assert verdict(claimed_promoted_exists=False) == PromotionAttestationVerdict.REFUTED_CLAIM


def test_closed_unmerged_pr_without_active_ancestry_is_not_promoted():
    assert verdict(main_descends_from_candidate=False, pr_merged=False) == PromotionAttestationVerdict.NOT_PROMOTED


def test_candidate_exists_but_unobserved_as_active_is_not_active():
    assert (
        verdict(
            main_descends_from_candidate=False,
            candidate_ci_exact_sha=False,
            pr_merged=None,
        )
        == PromotionAttestationVerdict.NOT_ACTIVE
    )


def test_exact_candidate_active_main_can_be_confirmed():
    assert (
        verdict(observed_main_sha=CANDIDATE)
        == PromotionAttestationVerdict.ACTIVE_PROMOTION_CONFIRMED
    )


def test_later_validation_commit_may_descend_from_promoted_candidate():
    assert verdict() == PromotionAttestationVerdict.ACTIVE_PROMOTION_CONFIRMED


def test_validation_document_cannot_override_missing_active_ancestry():
    assert (
        verdict(main_descends_from_candidate=False, validation_doc_present=True)
        == PromotionAttestationVerdict.REFUTED_CLAIM
    )


def test_stale_candidate_ci_does_not_prove_active_main():
    assert (
        verdict(main_descends_from_candidate=False, candidate_ci_exact_sha=True)
        == PromotionAttestationVerdict.NOT_PROMOTED
    )


def test_active_ancestry_with_content_mismatch_refutes_claim():
    assert verdict(required_active_paths_match=False) == PromotionAttestationVerdict.REFUTED_CLAIM


def test_missing_ancestry_observation_is_cannot_check():
    assert verdict(main_descends_from_candidate=None) == PromotionAttestationVerdict.CANNOT_CHECK


def test_claimed_promoted_sha_mismatch_requires_explicit_supersession():
    assert (
        verdict(claimed_promoted_sha="d" * 40)
        == PromotionAttestationVerdict.REFUTED_CLAIM
    )
    assert (
        verdict(claimed_promoted_sha="d" * 40, explicit_supersession=True)
        == PromotionAttestationVerdict.ACTIVE_PROMOTION_CONFIRMED
    )


def test_negative_history_must_be_preserved():
    assert verdict(history_preserved=False) == PromotionAttestationVerdict.REFUTED_CLAIM


def test_unstable_ref_observation_is_cannot_check():
    assert verdict(ref_observation_stable=False) == PromotionAttestationVerdict.CANNOT_CHECK


def test_postpromotion_exact_main_validation_is_required():
    assert (
        verdict(postpromotion_ci_exact_active_main=False)
        == PromotionAttestationVerdict.REFUTED_CLAIM
    )
    assert (
        verdict(postpromotion_ci_exact_active_main=None)
        == PromotionAttestationVerdict.CANNOT_CHECK
    )


def test_candidate_existence_is_not_assumed():
    assert verdict(candidate_exists=False) == PromotionAttestationVerdict.REFUTED_CLAIM
    assert verdict(candidate_exists=None) == PromotionAttestationVerdict.CANNOT_CHECK
