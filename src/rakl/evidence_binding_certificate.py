"""Proposal-only claim-level evidence binding for scientific authority (refs #427).

This module bridges two existing RAKL surfaces without replacing either one:

* :mod:`rakl.claim_evidence` validates exact source/span identity plus an
  externally supplied, known-answer-validated semantic review. Its reports are
  intentionally proposal-only and mint no scientific authority.
* :mod:`rakl.v3_scientific_authority` binds scientific promotion to canonical
  claim text, authority axis, scope, evidence-content digests and a protected
  attestation.

The residual checked here is the *bridge*: are the exact reviewed claim-evidence
relations the same exact evidence objects the authority proposal claims, and are
those relations sufficient for the requested scientific-authority coordinate?

A correct-looking terminal answer with the wrong evidence ids therefore fails.
This file is a challenger/development surface only. It is not wired into the
canonical v3 promotion path and every public report/certificate explicitly
returns ``grants_scientific_authority == False``. Canonical promotion requires
fresh assurance and a separately governed integration change.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis, AuthorityProposal
from .claim_evidence import (
    ClaimAtom,
    ClaimEvidenceLink,
    ClaimEvidenceReport,
    ClaimEvidenceVerdict,
    EvidenceReviewVerdict,
    sha256_text,
)
from .epistemic_noninterference import EvidenceRootKind
from .v3_authority import canonical_sha256
from .v3_scientific_authority import ScientificEvidenceBinding

__all__ = [
    "EvidenceBindingAssessment",
    "EvidenceBindingCertificate",
    "EvidenceBindingVerdict",
    "ReviewedEvidenceBinding",
    "evaluate_evidence_binding_for_promotion",
]


class EvidenceBindingVerdict(str, Enum):
    """Typed result of the proposal-only binding gate."""

    VALID_FOR_PROMOTION_CHALLENGER = "VALID_FOR_PROMOTION_CHALLENGER"
    CONFLICT_REQUIRES_RESOLUTION = "CONFLICT_REQUIRES_RESOLUTION"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ReviewedEvidenceBinding:
    """One exact evidence registration paired with its frozen semantic report."""

    evidence_id: str
    link: ClaimEvidenceLink
    report: ClaimEvidenceReport

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("reviewed evidence binding requires a non-empty evidence_id")


@dataclass(frozen=True)
class EvidenceBindingCertificate:
    """Content-addressed proposal that the bound relations can support a promotion.

    The certificate itself never mints authority. ``subject_hash`` exists so a
    future protected evaluator can bind the *exact* claim/evidence relation set
    rather than trusting a caller-supplied boolean.
    """

    certificate_id: str
    claim_id: str
    claim_text_sha256: str
    requested_axis: AuthorityAxis
    scope_id: str
    support_evidence_ids: Tuple[str, ...]
    refutation_evidence_ids: Tuple[str, ...]
    context_evidence_ids: Tuple[str, ...]
    support_link_ids: Tuple[str, ...]
    refutation_link_ids: Tuple[str, ...]
    context_link_ids: Tuple[str, ...]
    terminal_root_ids: Tuple[str, ...]
    missing_obligations: Tuple[str, ...]
    frozen_before_promotion: bool
    subject_hash: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class EvidenceBindingAssessment:
    verdict: EvidenceBindingVerdict
    reasons: Tuple[str, ...] = ()
    certificate: EvidenceBindingCertificate | None = None

    @property
    def valid_for_promotion_challenger(self) -> bool:
        return (
            self.verdict is EvidenceBindingVerdict.VALID_FOR_PROMOTION_CHALLENGER
            and self.certificate is not None
        )

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _terminal_root(
    evidence_id: str,
    registered: Mapping[str, ScientificEvidenceBinding],
) -> str:
    """Resolve a derivation chain to its terminal registered root."""

    current = evidence_id
    seen: set[str] = set()
    while current in registered and current not in seen:
        seen.add(current)
        upstream = registered[current].upstream_evidence_id
        if upstream is None:
            return current
        current = upstream
    return current


def _expected_review_verdict(report: ClaimEvidenceReport) -> EvidenceReviewVerdict | None:
    by_verdict = {
        ClaimEvidenceVerdict.REVIEWED_SUPPORT_PROPOSAL_ONLY: EvidenceReviewVerdict.SUPPORTS,
        ClaimEvidenceVerdict.REVIEWED_REFUTATION_PROPOSAL_ONLY: EvidenceReviewVerdict.REFUTES,
        ClaimEvidenceVerdict.REVIEWED_CONTEXT_PROPOSAL_ONLY: EvidenceReviewVerdict.CONTEXT_ONLY,
    }
    return by_verdict.get(report.verdict)


def _subject_hash(
    *,
    certificate_id: str,
    claim: ClaimAtom,
    proposal: AuthorityProposal,
    bindings: Sequence[ReviewedEvidenceBinding],
    registered: Mapping[str, ScientificEvidenceBinding],
    missing_obligations: Tuple[str, ...],
) -> str:
    rows = []
    for item in sorted(bindings, key=lambda entry: (entry.evidence_id, entry.link.link_id)):
        evidence = registered[item.evidence_id]
        rows.append(
            {
                "evidence_id": item.evidence_id,
                "evidence_sha256": evidence.content_sha256,
                "source_id": item.link.source_id,
                "source_sha256": item.link.source_sha256,
                "link_id": item.link.link_id,
                "reviewed_relation": (
                    item.report.reviewed_relation.value
                    if item.report.reviewed_relation is not None
                    else None
                ),
                "terminal_root_id": _terminal_root(item.evidence_id, registered),
            }
        )
    return canonical_sha256(
        {
            "kind": "EVIDENCE_BINDING_CERTIFICATE_V1",
            "certificate_id": certificate_id,
            "claim_id": claim.claim_id,
            "claim_text_sha256": sha256_text(claim.text),
            "claim_scope": claim.scope,
            "proposal_id": proposal.proposal_id,
            "requested_axis": proposal.axis.value,
            "scope_id": proposal.scope_id,
            "proposal_evidence_ids": sorted(proposal.evidence_ids),
            "bindings": rows,
            "missing_obligations": sorted(missing_obligations),
        }
    )


def evaluate_evidence_binding_for_promotion(
    claim: ClaimAtom,
    proposal: AuthorityProposal,
    bindings: Sequence[ReviewedEvidenceBinding],
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
    *,
    certificate_id: str,
    missing_obligations: Sequence[str] = (),
    frozen_before_promotion: bool | None,
) -> EvidenceBindingAssessment:
    """Check exact reviewed claim/evidence relations before scientific promotion.

    No semantic relation is inferred here. Only ``ClaimEvidenceReport`` values
    already produced by the claim-evidence validator from known-answer-validated
    semantic review can become resolved bindings.

    Version 1 intentionally requires ``proposal.scope_id == claim.scope``. A
    future context-transport witness may relax this under its own verified
    contract; a caller boolean is not accepted as a substitute.
    """

    invalid: list[str] = []
    cannot_check: list[str] = []
    conflicts: list[str] = []
    semantic_resolution_incomplete = False

    if not certificate_id.strip():
        invalid.append("binding_certificate_id_required")
    if not claim.claim_id.strip() or not claim.text.strip() or not claim.scope.strip():
        invalid.append("claim_identity_text_or_scope_missing")
    if proposal.claim_id != claim.claim_id:
        invalid.append("proposal_claim_identity_mismatch")
    if proposal.scope_id != claim.scope:
        invalid.append("proposal_scope_not_exactly_claim_scope")
    if frozen_before_promotion is None:
        cannot_check.append("binding_freeze_chronology_unknown")
    elif frozen_before_promotion is False:
        invalid.append("binding_defined_posthoc_after_promotion")

    obligations = tuple(sorted({item.strip() for item in missing_obligations if item.strip()}))
    if obligations:
        cannot_check.append("unresolved_evidence_obligations:" + ",".join(obligations))

    if not bindings:
        cannot_check.append("no_reviewed_claim_evidence_bindings")
        semantic_resolution_incomplete = True

    evidence_ids = [item.evidence_id for item in bindings]
    link_ids = [item.link.link_id for item in bindings]
    if len(set(evidence_ids)) != len(evidence_ids):
        invalid.append("duplicate_bound_evidence_id")
    if len(set(link_ids)) != len(link_ids):
        invalid.append("duplicate_bound_claim_evidence_link_id")
    if len(set(proposal.evidence_ids)) != len(proposal.evidence_ids):
        invalid.append("duplicate_proposal_evidence_id")

    support_ids: list[str] = []
    refutation_ids: list[str] = []
    context_ids: list[str] = []
    support_links: list[str] = []
    refutation_links: list[str] = []
    context_links: list[str] = []

    for item in bindings:
        link = item.link
        report = item.report
        registered = registered_evidence.get(item.evidence_id)

        if registered is None:
            invalid.append(f"bound_evidence_unregistered:{item.evidence_id}")
            continue
        if link.claim_id != claim.claim_id or report.claim_id != claim.claim_id:
            invalid.append(f"binding_claim_identity_mismatch:{item.evidence_id}")
        if report.link_id != link.link_id:
            invalid.append(f"binding_report_link_identity_mismatch:{item.evidence_id}")
        if report.source_id != link.source_id:
            invalid.append(f"binding_report_source_identity_mismatch:{item.evidence_id}")
        if report.proposed_relation is not link.proposed_relation:
            invalid.append(f"binding_proposed_relation_mismatch:{item.evidence_id}")
        if registered.content_sha256 != link.source_sha256:
            invalid.append(f"registered_evidence_content_not_exact_link_source:{item.evidence_id}")

        if not report.locator_verified:
            cannot_check.append(f"exact_locator_not_verified:{item.evidence_id}")
        if not report.semantic_review_verified:
            cannot_check.append(f"semantic_review_not_verified:{item.evidence_id}")

        if report.verdict is ClaimEvidenceVerdict.REVIEW_CONTRADICTION:
            conflicts.append(f"semantic_review_contradiction:{item.evidence_id}")
            continue
        if report.verdict is ClaimEvidenceVerdict.REVIEWED_INSUFFICIENT_EVIDENCE:
            cannot_check.append(f"reviewed_evidence_insufficient:{item.evidence_id}")
            semantic_resolution_incomplete = True
            continue
        if report.verdict is ClaimEvidenceVerdict.LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED:
            cannot_check.append(f"semantic_relation_unreviewed:{item.evidence_id}")
            semantic_resolution_incomplete = True
            continue
        if report.verdict is ClaimEvidenceVerdict.CANNOT_CHECK:
            cannot_check.append(f"claim_evidence_report_cannot_check:{item.evidence_id}")
            semantic_resolution_incomplete = True
            continue
        if report.verdict is ClaimEvidenceVerdict.TRIAL_INVALID:
            invalid.append(f"claim_evidence_report_invalid:{item.evidence_id}")
            continue

        expected = _expected_review_verdict(report)
        if expected is None or report.reviewed_relation is not expected:
            invalid.append(f"reviewed_relation_not_consistent_with_report:{item.evidence_id}")
            continue

        if expected is EvidenceReviewVerdict.SUPPORTS:
            support_ids.append(item.evidence_id)
            support_links.append(link.link_id)
        elif expected is EvidenceReviewVerdict.REFUTES:
            refutation_ids.append(item.evidence_id)
            refutation_links.append(link.link_id)
        elif expected is EvidenceReviewVerdict.CONTEXT_ONLY:
            context_ids.append(item.evidence_id)
            context_links.append(link.link_id)

    proposal_ids = tuple(sorted(proposal.evidence_ids))
    bound_support_ids = tuple(sorted(support_ids))
    if not bound_support_ids:
        cannot_check.append("promotion_requires_reviewed_support_binding")
    if proposal_ids != bound_support_ids:
        if semantic_resolution_incomplete:
            cannot_check.append(
                "promotion_support_binding_not_fully_resolved_for_proposal_evidence"
            )
        else:
            invalid.append(
                "promotion_evidence_ids_do_not_exactly_match_reviewed_support_bindings"
            )
    if refutation_ids:
        conflicts.append(
            "promotion_has_bound_refuting_evidence:" + ",".join(sorted(refutation_ids))
        )

    scientific_support = []
    experience_support = []
    for evidence_id in support_ids:
        registered = registered_evidence[evidence_id]
        if registered.kind in {
            EvidenceRootKind.EXTERNAL_OBSERVATION,
            EvidenceRootKind.DERIVED_REPORT,
        }:
            scientific_support.append(registered)
        else:
            experience_support.append(registered)
    if experience_support:
        invalid.append(
            "experience_objects_bound_as_scientific_support:"
            + ",".join(sorted(item.evidence_id for item in experience_support))
        )
    if support_ids and not scientific_support:
        invalid.append("promotion_has_no_non_experience_scientific_support")
    if scientific_support and not any(
        proposal.axis in item.supports_axes for item in scientific_support
    ):
        invalid.append(
            f"reviewed_support_does_not_license_requested_axis:{proposal.axis.name}"
        )

    terminal_roots = tuple(
        sorted({_terminal_root(item, registered_evidence) for item in support_ids})
    )
    if len(support_ids) > 1 and len(terminal_roots) < len(support_ids):
        invalid.append(
            f"reviewed_support_collapses_to_{len(terminal_roots)}_independent_lineage_roots"
        )

    if invalid:
        return EvidenceBindingAssessment(
            EvidenceBindingVerdict.INVALID,
            tuple(sorted(set(invalid + cannot_check + conflicts))),
        )
    if conflicts:
        return EvidenceBindingAssessment(
            EvidenceBindingVerdict.CONFLICT_REQUIRES_RESOLUTION,
            tuple(sorted(set(conflicts + cannot_check))),
        )
    if cannot_check:
        return EvidenceBindingAssessment(
            EvidenceBindingVerdict.CANNOT_CHECK,
            tuple(sorted(set(cannot_check))),
        )

    binding_tuple = tuple(bindings)
    subject = _subject_hash(
        certificate_id=certificate_id,
        claim=claim,
        proposal=proposal,
        bindings=binding_tuple,
        registered=registered_evidence,
        missing_obligations=obligations,
    )
    certificate = EvidenceBindingCertificate(
        certificate_id=certificate_id,
        claim_id=claim.claim_id,
        claim_text_sha256=sha256_text(claim.text),
        requested_axis=proposal.axis,
        scope_id=proposal.scope_id,
        support_evidence_ids=tuple(sorted(support_ids)),
        refutation_evidence_ids=tuple(sorted(refutation_ids)),
        context_evidence_ids=tuple(sorted(context_ids)),
        support_link_ids=tuple(sorted(support_links)),
        refutation_link_ids=tuple(sorted(refutation_links)),
        context_link_ids=tuple(sorted(context_links)),
        terminal_root_ids=terminal_roots,
        missing_obligations=obligations,
        frozen_before_promotion=True,
        subject_hash=subject,
    )
    return EvidenceBindingAssessment(
        EvidenceBindingVerdict.VALID_FOR_PROMOTION_CHALLENGER,
        (),
        certificate,
    )
