from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PromotionAttestationVerdict(str, Enum):
    """Post-promotion repository-state conclusions.

    The values deliberately distinguish an unexecuted promotion from a candidate
    that merely is not active, a positively refuted validation claim, and a
    state that cannot be checked with the observations supplied.
    """

    ACTIVE_PROMOTION_CONFIRMED = "ACTIVE_PROMOTION_CONFIRMED"
    NOT_PROMOTED = "NOT_PROMOTED"
    NOT_ACTIVE = "NOT_ACTIVE"
    REFUTED_CLAIM = "REFUTED_CLAIM"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class PromotionAttestationPacket:
    """Externally observed facts used to attest a completed promotion.

    This packet is intentionally downstream of :class:`PromotionGate`.  A gate
    may authorize a ref update, but authorization is not evidence that the ref
    actually moved.  Repository/API observations must establish that separately.

    ``main_descends_from_candidate`` permits a later documentation or validation
    commit on top of the promoted candidate; exact equality is therefore not
    required forever.  ``required_active_paths_match`` is a content/manifest
    witness for the behavior whose promotion is being claimed.
    """

    candidate_sha: str
    claimed_promoted_sha: str
    observed_main_sha: str
    candidate_exists: bool | None
    claimed_promoted_exists: bool | None
    main_descends_from_candidate: bool | None
    required_active_paths_match: bool | None
    candidate_ci_exact_sha: bool | None
    postpromotion_ci_exact_active_main: bool | None
    history_preserved: bool = True
    ref_observation_stable: bool = True
    validation_doc_present: bool = False
    pr_merged: bool | None = None
    explicit_supersession: bool = False

    @property
    def claimed_matches_candidate(self) -> bool:
        return self.claimed_promoted_sha == self.candidate_sha


@dataclass(frozen=True)
class PromotionAttestationReport:
    verdict: PromotionAttestationVerdict
    reasons: tuple[str, ...]

    @property
    def active_confirmed(self) -> bool:
        return self.verdict == PromotionAttestationVerdict.ACTIVE_PROMOTION_CONFIRMED


def attest_promotion_state(
    packet: PromotionAttestationPacket,
) -> PromotionAttestationReport:
    """Fail closed on the difference between *authorized* and *active* state.

    The function performs no network access.  Its booleans must come from an
    independent repository/ref observer.  A green candidate check, a closed PR,
    or a validation document cannot substitute for an ancestry/content witness.
    """

    if not packet.history_preserved:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("negative/supersession history was not preserved",),
        )

    if not packet.ref_observation_stable:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("active ref changed or could not be held stable during attestation",),
        )

    if packet.candidate_exists is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("candidate object existence was not observed",),
        )
    if not packet.candidate_exists:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("claimed candidate object does not exist in the repository",),
        )

    if packet.claimed_promoted_exists is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("claimed promoted object existence was not observed",),
        )
    if not packet.claimed_promoted_exists:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("claimed promoted SHA does not resolve in the repository",),
        )

    if not packet.claimed_matches_candidate and not packet.explicit_supersession:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            (
                "claimed promoted SHA differs from candidate without explicit supersession",
                f"candidate={packet.candidate_sha}",
                f"claimed={packet.claimed_promoted_sha}",
            ),
        )

    if packet.main_descends_from_candidate is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("active-main ancestry relative to candidate was not observed",),
        )

    if not packet.main_descends_from_candidate:
        if packet.validation_doc_present or packet.pr_merged is True:
            return PromotionAttestationReport(
                PromotionAttestationVerdict.REFUTED_CLAIM,
                (
                    "promotion/validation evidence is asserted but active main does not descend from candidate",
                    f"observed_main={packet.observed_main_sha}",
                    f"candidate={packet.candidate_sha}",
                ),
            )
        if packet.pr_merged is False or packet.candidate_ci_exact_sha is True:
            return PromotionAttestationReport(
                PromotionAttestationVerdict.NOT_PROMOTED,
                (
                    "candidate may have been validated, but active main does not contain it",
                ),
            )
        return PromotionAttestationReport(
            PromotionAttestationVerdict.NOT_ACTIVE,
            ("candidate is not an ancestor of the observed active main",),
        )

    if packet.required_active_paths_match is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("active candidate content/manifest witness was not observed",),
        )
    if not packet.required_active_paths_match:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("active main ancestry and required promoted content disagree",),
        )

    if packet.candidate_ci_exact_sha is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("exact-candidate validation was not observed",),
        )
    if not packet.candidate_ci_exact_sha:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("candidate did not have a successful exact-SHA validation",),
        )

    if packet.postpromotion_ci_exact_active_main is None:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.CANNOT_CHECK,
            ("post-promotion exact-active-main validation was not observed",),
        )
    if not packet.postpromotion_ci_exact_active_main:
        return PromotionAttestationReport(
            PromotionAttestationVerdict.REFUTED_CLAIM,
            ("active promoted state lacks a successful exact-main post-promotion validation",),
        )

    return PromotionAttestationReport(
        PromotionAttestationVerdict.ACTIVE_PROMOTION_CONFIRMED,
        (
            "candidate exists and is reachable from active main",
            "required active content matches",
            "candidate and active-main validation are exact and positive",
        ),
    )
