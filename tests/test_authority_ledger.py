from rakl.authority_ledger import (
    AuthorityAxis,
    AuthorityCertificate,
    AuthorityLedger,
    AuthorityProposal,
    VerificationOutcome,
)


def proposal(axis: AuthorityAxis = AuthorityAxis.REPRESENTATION) -> AuthorityProposal:
    return AuthorityProposal(
        proposal_id="p-1",
        claim_id="claim-1",
        axis=axis,
        proposition="scoped proposition",
        scope_id="scope-1",
        evidence_ids=("evidence-1",),
    )


def test_proposal_has_no_authority_until_verified_commit() -> None:
    ledger = AuthorityLedger()
    candidate = proposal()
    assert ledger.active_for(candidate.claim_id) == ()

    result = ledger.commit_verified(
        candidate,
        certificate_id="cert-refuted",
        outcome=VerificationOutcome.REFUTED,
    )
    assert result is None
    assert ledger.active_for(candidate.claim_id) == ()


def test_supported_commit_mints_only_the_proposed_axis() -> None:
    ledger = AuthorityLedger()
    ledger.commit_verified(
        proposal(AuthorityAxis.REPRESENTATION),
        certificate_id="cert-r",
        outcome=VerificationOutcome.SUPPORTED,
    )

    assert len(ledger.active_for("claim-1", AuthorityAxis.REPRESENTATION)) == 1
    assert ledger.active_for("claim-1", AuthorityAxis.MECHANISM) == ()


def test_refutation_can_lower_active_authority_without_erasing_history() -> None:
    ledger = AuthorityLedger()
    ledger.commit_verified(
        proposal(),
        certificate_id="cert-1",
        outcome=VerificationOutcome.SUPPORTED,
    )
    assert len(ledger.active_for("claim-1")) == 1

    ledger.revoke("cert-1", reason="counterevidence invalidated the licensed scope")

    assert ledger.active_for("claim-1") == ()
    assert "cert-1" in ledger.certificates
    history = ledger.history_for("cert-1")
    assert [event.kind.value for event in history] == ["ISSUE", "REVOKE"]


def test_supersession_preserves_old_certificate_and_activates_replacement() -> None:
    ledger = AuthorityLedger()
    ledger.commit_verified(
        proposal(),
        certificate_id="cert-old",
        outcome=VerificationOutcome.SUPPORTED,
    )
    replacement = AuthorityCertificate(
        certificate_id="cert-new",
        claim_id="claim-1",
        axis=AuthorityAxis.REPRESENTATION,
        proposition="narrower proposition",
        scope_id="scope-1-narrow",
        evidence_ids=("evidence-2",),
        partial=True,
    )

    ledger.supersede("cert-old", replacement, reason="new evidence narrows the scope")

    assert "cert-old" in ledger.certificates
    assert "cert-old" not in ledger.active_ids
    assert "cert-new" in ledger.active_ids
    history = ledger.history_for("cert-new")
    assert len(history) == 1
    assert history[0].replacement_certificate_id == "cert-new"


def test_evidence_identity_is_required_for_authority_proposal() -> None:
    try:
        AuthorityProposal(
            proposal_id="p",
            claim_id="c",
            axis=AuthorityAxis.GROUNDING,
            proposition="claim",
            scope_id="scope",
            evidence_ids=(),
        )
    except ValueError as exc:
        assert "evidence" in str(exc)
    else:
        raise AssertionError("proposal without evidence should fail closed")
