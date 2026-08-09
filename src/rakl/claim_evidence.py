from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class EvidenceRelation(str, Enum):
    """The relation proposed between one atomic claim and one evidence span."""

    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    QUALIFIES = "QUALIFIES"


class EvidenceReviewVerdict(str, Enum):
    """An externally supplied semantic review outcome.

    RAKL does not infer these labels from text in this support layer.
    """

    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    CONTEXT_ONLY = "CONTEXT_ONLY"
    INSUFFICIENT = "INSUFFICIENT"


class ClaimEvidenceVerdict(str, Enum):
    LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED = "LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED"
    REVIEWED_SUPPORT_PROPOSAL_ONLY = "REVIEWED_SUPPORT_PROPOSAL_ONLY"
    REVIEWED_REFUTATION_PROPOSAL_ONLY = "REVIEWED_REFUTATION_PROPOSAL_ONLY"
    REVIEWED_CONTEXT_PROPOSAL_ONLY = "REVIEWED_CONTEXT_PROPOSAL_ONLY"
    REVIEWED_INSUFFICIENT_EVIDENCE = "REVIEWED_INSUFFICIENT_EVIDENCE"
    REVIEW_CONTRADICTION = "REVIEW_CONTRADICTION"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class ClaimAtom:
    claim_id: str
    text: str
    scope: str


@dataclass(frozen=True)
class EvidenceSourceSnapshot:
    """One exact textual source snapshot.

    The SHA-256 is over the UTF-8 bytes of ``text`` exactly as stored. No hidden
    normalization or relocation is performed by this module.
    """

    source_id: str
    source_locator: str
    text: str
    sha256: str


@dataclass(frozen=True)
class TextSpanSelector:
    """A code-point indexed exact span with optional immediate context anchors."""

    start: int
    end: int
    exact: str
    prefix: str = ""
    suffix: str = ""


@dataclass(frozen=True)
class ClaimEvidenceLink:
    link_id: str
    claim_id: str
    source_id: str
    source_sha256: str
    selector: TextSpanSelector
    proposed_relation: EvidenceRelation
    selector_frozen_before_review: Optional[bool]


@dataclass(frozen=True)
class EvidenceJudgment:
    """A pre-existing semantic review record, not a model inference by this module."""

    judgment_id: str
    link_id: str
    claim_id: str
    scope: str
    verdict: EvidenceReviewVerdict
    known_answer_validated: Optional[bool]
    frozen_before_synthesis: Optional[bool]


@dataclass(frozen=True)
class ClaimEvidenceReport:
    verdict: ClaimEvidenceVerdict
    claim_id: str
    link_id: str
    source_id: str
    locator_verified: bool
    semantic_review_verified: bool
    proposed_relation: EvidenceRelation
    reviewed_relation: Optional[EvidenceReviewVerdict]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def activates_canonical_knowledge(self) -> bool:
        return False

    @property
    def locator_fidelity_establishes_semantic_support(self) -> bool:
        return False


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def freeze_source_snapshot(
    source_id: str,
    source_locator: str,
    text: str,
) -> EvidenceSourceSnapshot:
    """Create an exact immutable identity record for a supplied textual snapshot."""

    return EvidenceSourceSnapshot(
        source_id=source_id,
        source_locator=source_locator,
        text=text,
        sha256=sha256_text(text),
    )


def _report(
    verdict: ClaimEvidenceVerdict,
    claim: ClaimAtom,
    link: ClaimEvidenceLink,
    *,
    locator_verified: bool = False,
    semantic_review_verified: bool = False,
    reviewed_relation: Optional[EvidenceReviewVerdict] = None,
    reasons: Tuple[str, ...],
) -> ClaimEvidenceReport:
    return ClaimEvidenceReport(
        verdict=verdict,
        claim_id=claim.claim_id,
        link_id=link.link_id,
        source_id=link.source_id,
        locator_verified=locator_verified,
        semantic_review_verified=semantic_review_verified,
        proposed_relation=link.proposed_relation,
        reviewed_relation=reviewed_relation,
        reasons=reasons,
    )


def _valid_sha256(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def validate_claim_evidence_link(
    claim: ClaimAtom,
    source: EvidenceSourceSnapshot,
    link: ClaimEvidenceLink,
    judgment: EvidenceJudgment | None = None,
) -> ClaimEvidenceReport:
    """Validate exact claim-to-span provenance without inferring semantic truth.

    The function validates three layers separately:

    1. source and span identity;
    2. consistency of an externally supplied semantic review record;
    3. authority, which is deliberately never granted here.
    """

    if not claim.claim_id or not claim.text or not claim.scope:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("claim_identity_or_scope_missing",),
        )
    if not source.source_id or not source.source_locator:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            reasons=("source_identity_or_locator_missing",),
        )
    if not link.link_id:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("link_id_missing",),
        )
    if link.claim_id != claim.claim_id:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("link_claim_identity_mismatch",),
        )
    if link.source_id != source.source_id:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("link_source_identity_mismatch",),
        )
    if not _valid_sha256(source.sha256):
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            reasons=("source_sha256_invalid_or_missing",),
        )

    actual_sha = sha256_text(source.text)
    if actual_sha != source.sha256:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            reasons=("source_snapshot_hash_mismatch",),
        )
    if link.source_sha256 != source.sha256:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("link_source_hash_mismatch",),
        )

    if link.selector_frozen_before_review is None:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            reasons=("selector_freeze_chronology_unknown",),
        )
    if link.selector_frozen_before_review is False:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("posthoc_selector_definition",),
        )

    selector = link.selector
    if (
        isinstance(selector.start, bool)
        or isinstance(selector.end, bool)
        or not isinstance(selector.start, int)
        or not isinstance(selector.end, int)
        or selector.start < 0
        or selector.end <= selector.start
        or selector.end > len(source.text)
    ):
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("selector_bounds_invalid",),
        )
    if not selector.exact:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("selector_exact_missing",),
        )
    selected = source.text[selector.start : selector.end]
    if selected != selector.exact:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            reasons=("selector_exact_mismatch",),
        )
    if selector.prefix:
        prefix_start = selector.start - len(selector.prefix)
        if prefix_start < 0 or source.text[prefix_start : selector.start] != selector.prefix:
            return _report(
                ClaimEvidenceVerdict.TRIAL_INVALID,
                claim,
                link,
                reasons=("selector_prefix_mismatch",),
            )
    if selector.suffix:
        suffix_end = selector.end + len(selector.suffix)
        if source.text[selector.end : suffix_end] != selector.suffix:
            return _report(
                ClaimEvidenceVerdict.TRIAL_INVALID,
                claim,
                link,
                reasons=("selector_suffix_mismatch",),
            )

    if judgment is None:
        return _report(
            ClaimEvidenceVerdict.LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED,
            claim,
            link,
            locator_verified=True,
            reasons=("exact_locator_verified", "semantic_relation_not_reviewed"),
        )

    if (
        not judgment.judgment_id
        or judgment.link_id != link.link_id
        or judgment.claim_id != claim.claim_id
    ):
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_judgment_identity_mismatch",),
        )
    if judgment.scope != claim.scope:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_judgment_scope_mismatch",),
        )
    if judgment.known_answer_validated is None:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_review_known_answer_validation_unknown",),
        )
    if judgment.known_answer_validated is False:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_review_not_known_answer_validated",),
        )
    if judgment.frozen_before_synthesis is None:
        return _report(
            ClaimEvidenceVerdict.CANNOT_CHECK,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_review_freeze_chronology_unknown",),
        )
    if judgment.frozen_before_synthesis is False:
        return _report(
            ClaimEvidenceVerdict.TRIAL_INVALID,
            claim,
            link,
            locator_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("posthoc_semantic_review",),
        )

    if judgment.verdict == EvidenceReviewVerdict.INSUFFICIENT:
        return _report(
            ClaimEvidenceVerdict.REVIEWED_INSUFFICIENT_EVIDENCE,
            claim,
            link,
            locator_verified=True,
            semantic_review_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=("semantic_review_insufficient_evidence",),
        )

    aligned = {
        EvidenceRelation.SUPPORTS: EvidenceReviewVerdict.SUPPORTS,
        EvidenceRelation.REFUTES: EvidenceReviewVerdict.REFUTES,
        EvidenceRelation.QUALIFIES: EvidenceReviewVerdict.CONTEXT_ONLY,
    }
    if judgment.verdict != aligned[link.proposed_relation]:
        return _report(
            ClaimEvidenceVerdict.REVIEW_CONTRADICTION,
            claim,
            link,
            locator_verified=True,
            semantic_review_verified=True,
            reviewed_relation=judgment.verdict,
            reasons=(
                "proposed_relation_conflicts_with_semantic_review",
                f"proposed:{link.proposed_relation.value}",
                f"reviewed:{judgment.verdict.value}",
            ),
        )

    verdict_by_relation = {
        EvidenceReviewVerdict.SUPPORTS: ClaimEvidenceVerdict.REVIEWED_SUPPORT_PROPOSAL_ONLY,
        EvidenceReviewVerdict.REFUTES: ClaimEvidenceVerdict.REVIEWED_REFUTATION_PROPOSAL_ONLY,
        EvidenceReviewVerdict.CONTEXT_ONLY: ClaimEvidenceVerdict.REVIEWED_CONTEXT_PROPOSAL_ONLY,
    }
    return _report(
        verdict_by_relation[judgment.verdict],
        claim,
        link,
        locator_verified=True,
        semantic_review_verified=True,
        reviewed_relation=judgment.verdict,
        reasons=("exact_locator_verified", "semantic_review_record_verified"),
    )
