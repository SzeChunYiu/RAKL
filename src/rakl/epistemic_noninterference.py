"""Executable EPISTEMIC_NONINTERFERENCE invariant for RAKL scientific authority.

The property under test is *not* "state never changes". Persistent experience is
supposed to change what RAKL tries next. The claim is narrower:

    behaviour-changing state and authority-changing state have a protected
    interface, and only an explicitly registered evidence-bearing promotion may
    move the authority projection.

Formally, for a transition sequence ``tau`` composed only of experience-side,
retrieval-side, workspace-side, strategy-side, reflection-side or routing-side
operations::

    pi_auth(tau(X_t)) == pi_auth(X_t)

``pi_auth`` projects only the scientific-authority-bearing coordinates, which in
this repository are the :class:`~rakl.authority_ledger.AuthorityAxis` values
(G/R/M/I/D) carried by *active* certificates in an
:class:`~rakl.authority_ledger.AuthorityLedger`.

Scope and honesty note
----------------------
On the current framework revision the v3 experience state
(:class:`~rakl.v3_runtime.RAKLV3State`) does **not** compose an
``AuthorityLedger``: the two families are unreachable from one another. This
module therefore reports :data:`NoninterferenceStatus.NO_INTEGRATION_SURFACE`
for that state rather than ``PASS``. An accidental absence of a channel is not
an enforced invariant, and reporting it as a pass would manufacture the result.
The invariant is consequently a *prospective* guard on integration code that
composes the two families. See ``docs/EPISTEMIC_NONINTERFERENCE.md``.

This module is proposal-only. It is wired into no promotion gate and mints no
authority of its own.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
from typing import Iterable, Mapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis, AuthorityLedger
from .experience_substrate import ExperienceLedger, LessonAuthority

__all__ = [
    "AuthorityGrant",
    "ComposedResearchState",
    "EvidenceRoot",
    "EvidenceRootKind",
    "IntegrationSurfaceReport",
    "LeakFamily",
    "NoninterferenceFinding",
    "NoninterferenceReport",
    "NoninterferenceStatus",
    "NonAuthorityCoordinate",
    "StateFamily",
    "Transition",
    "TransitionKind",
    "check_epistemic_noninterference",
    "describe_integration_surface",
    "pi_auth",
    "pi_non_authority",
]


# --------------------------------------------------------------------------
# State decomposition
# --------------------------------------------------------------------------


class StateFamily(str, Enum):
    """The conceptual ``X_t = (K_t, E_t, R_t, G_t)`` decomposition.

    Mapped onto current framework projections in
    ``docs/EPISTEMIC_NONINTERFERENCE.md``. ``ROUTING`` is *derived*, not stored:
    the framework recomputes it from experience on demand.
    """

    CANONICAL_KNOWLEDGE = "K"
    EXPERIENCE = "E"
    ROUTING = "R"
    AUTHORITY = "G"


class NonAuthorityCoordinate(str, Enum):
    """Coordinates that must stay distinguishable from scientific authority.

    These are the required distinctions the invariant refuses to collapse.
    Every one of them is allowed to move under experience-only transitions;
    none of them may flow *into* :func:`pi_auth`.
    """

    COMPUTATIONAL_ACCESS = "COMPUTATIONAL_ACCESS"
    RETRIEVAL_PRIORITY = "RETRIEVAL_PRIORITY"
    PROPOSAL_PROBABILITY = "PROPOSAL_PROBABILITY"
    STRATEGY_PREFERENCE = "STRATEGY_PREFERENCE"
    LESSON_REUSE = "LESSON_REUSE"
    SCIENTIFIC_EVIDENCE = "SCIENTIFIC_EVIDENCE"


class EvidenceRootKind(str, Enum):
    """Registered provenance class of one evidence root.

    These labels are supplied by the frozen case/registration, never inferred
    from text by this module. ``TASK_EPISODE``, ``LESSON`` and
    ``ROUTING_STATISTIC`` are experience objects: they may license routing and
    proposal changes but can never be counted as evidence about nature.
    """

    EXTERNAL_OBSERVATION = "EXTERNAL_OBSERVATION"
    TASK_EPISODE = "TASK_EPISODE"
    LESSON = "LESSON"
    DERIVED_REPORT = "DERIVED_REPORT"
    ROUTING_STATISTIC = "ROUTING_STATISTIC"


#: Evidence-root kinds that may back a scientific-authority grant at all.
_SCIENTIFIC_ROOT_KINDS = frozenset(
    {EvidenceRootKind.EXTERNAL_OBSERVATION, EvidenceRootKind.DERIVED_REPORT}
)

#: Evidence-root kinds that are experience, not evidence about nature.
_EXPERIENCE_ROOT_KINDS = frozenset(
    {
        EvidenceRootKind.TASK_EPISODE,
        EvidenceRootKind.LESSON,
        EvidenceRootKind.ROUTING_STATISTIC,
    }
)


@dataclass(frozen=True)
class EvidenceRoot:
    """One registered evidence root with explicit lineage and axis support.

    ``supports_axes`` is a frozen property of the registered evidence, not a
    judgement made here; the invariant needs no hidden semantic oracle.
    ``upstream_root_id`` makes derivative lineage explicit so that many
    descendants of one experiment cannot be counted as independent.
    """

    root_id: str
    kind: EvidenceRootKind
    supports_axes: frozenset[AuthorityAxis] = frozenset()
    upstream_root_id: str | None = None

    def __post_init__(self) -> None:
        if not self.root_id.strip():
            raise ValueError("evidence root requires a non-empty id")
        if self.upstream_root_id is not None and not self.upstream_root_id.strip():
            raise ValueError("upstream_root_id must be omitted or non-empty")
        if self.upstream_root_id == self.root_id:
            raise ValueError("evidence root cannot be its own upstream root")


@dataclass(frozen=True)
class AuthorityGrant:
    """One element of the authority projection ``pi_auth``."""

    claim_id: str
    axis: AuthorityAxis
    scope_id: str
    partial: bool = False


@dataclass(frozen=True)
class ComposedResearchState:
    """The composed ``X_t`` an integration would have to build.

    Nothing in the current framework constructs this. It exists so the
    invariant can be stated over a state where the leak channel is *reachable*;
    otherwise the property would be trivially true by unreachability.
    """

    experience: ExperienceLedger = ExperienceLedger()
    authority: AuthorityLedger | None = None
    evidence_roots: Tuple[EvidenceRoot, ...] = ()
    #: Non-authority coordinates an integration may freely move.
    routing_scores: Tuple[Tuple[str, float], ...] = ()
    access_counts: Tuple[Tuple[str, int], ...] = ()

    def root_by_id(self) -> Mapping[str, EvidenceRoot]:
        return {root.root_id: root for root in self.evidence_roots}


def pi_auth(state: ComposedResearchState) -> frozenset[AuthorityGrant]:
    """Project only the scientific-authority-bearing coordinates.

    Returns the set of *active* authority grants. Revoked and superseded
    certificates leave the projection even though their history is retained,
    which is what makes the projection non-monotone rather than append-only.
    """

    ledger = state.authority
    if ledger is None:
        return frozenset()
    return frozenset(
        AuthorityGrant(
            claim_id=certificate.claim_id,
            axis=certificate.axis,
            scope_id=certificate.scope_id,
            partial=certificate.partial,
        )
        for certificate_id in ledger.active_ids
        for certificate in (ledger.certificates[certificate_id],)
    )


def pi_non_authority(state: ComposedResearchState) -> Mapping[NonAuthorityCoordinate, object]:
    """Project the coordinates that experience *is* allowed to move.

    Used by the benign controls: a world in which this projection changes while
    :func:`pi_auth` does not is exactly the intended behaviour, and a test that
    only asserts ``pi_auth`` invariance would also pass for an implementation
    that learns nothing at all.
    """

    lesson_reuse = tuple(
        sorted(
            (lesson.lesson_id, lesson.authority.value)
            for lesson in state.experience.lessons
        )
    )
    return {
        NonAuthorityCoordinate.COMPUTATIONAL_ACCESS: tuple(sorted(state.access_counts)),
        NonAuthorityCoordinate.RETRIEVAL_PRIORITY: tuple(sorted(state.routing_scores)),
        NonAuthorityCoordinate.PROPOSAL_PROBABILITY: tuple(sorted(state.routing_scores)),
        NonAuthorityCoordinate.STRATEGY_PREFERENCE: tuple(
            sorted(episode.episode_id for episode in state.experience.episodes)
        ),
        NonAuthorityCoordinate.LESSON_REUSE: lesson_reuse,
        NonAuthorityCoordinate.SCIENTIFIC_EVIDENCE: tuple(
            sorted(root.root_id for root in state.evidence_roots)
        ),
    }


# --------------------------------------------------------------------------
# Transitions
# --------------------------------------------------------------------------


class TransitionKind(str, Enum):
    """Registered transition families.

    Everything except :data:`EVIDENCE_BEARING_PROMOTION` is authority-inert by
    contract; the invariant is the executable statement of that contract.
    """

    RECORD_EPISODE = "RECORD_EPISODE"
    RECORD_FAILURE = "RECORD_FAILURE"
    CONSOLIDATE_LESSON = "CONSOLIDATE_LESSON"
    PROJECT_TOOL = "PROJECT_TOOL"
    REUSE_LESSON = "REUSE_LESSON"
    RETRIEVE = "RETRIEVE"
    UPDATE_ROUTING_POLICY = "UPDATE_ROUTING_POLICY"
    WORKSPACE_LOAD = "WORKSPACE_LOAD"
    WORKSPACE_EVICT = "WORKSPACE_EVICT"
    REFLECT = "REFLECT"
    SELF_EVOLUTION_WIN = "SELF_EVOLUTION_WIN"
    EVIDENCE_BEARING_PROMOTION = "EVIDENCE_BEARING_PROMOTION"


class LeakFamily(str, Enum):
    """Threat families. Each planted leak world must fail with its own reason."""

    EXPERIENCE_TO_EVIDENCE = "EXPERIENCE_TO_EVIDENCE"
    REPETITION_TO_AUTHORITY = "REPETITION_TO_AUTHORITY"
    ROUTING_TO_AUTHORITY = "ROUTING_TO_AUTHORITY"
    REFLECTION_TO_AUTHORITY = "REFLECTION_TO_AUTHORITY"
    FAILURE_TO_IMPOSSIBILITY = "FAILURE_TO_IMPOSSIBILITY"
    PROVENANCE_TO_INDEPENDENCE = "PROVENANCE_TO_INDEPENDENCE"
    PREDICTION_TO_MECHANISM = "PREDICTION_TO_MECHANISM"
    MECHANISM_TO_IDENTIFICATION = "MECHANISM_TO_IDENTIFICATION"
    WORKSPACE_TO_AUTHORITY = "WORKSPACE_TO_AUTHORITY"
    SELF_EVOLUTION_TO_AUTHORITY = "SELF_EVOLUTION_TO_AUTHORITY"


#: Which threat family an authority change under a non-promotion transition is.
#: Attribution follows the *transition family that produced the change*, so the
#: diagnosis cannot be supplied (or suppressed) by the caller.
_LEAK_FAMILY_BY_KIND: Mapping[TransitionKind, LeakFamily] = {
    TransitionKind.RECORD_EPISODE: LeakFamily.EXPERIENCE_TO_EVIDENCE,
    TransitionKind.CONSOLIDATE_LESSON: LeakFamily.EXPERIENCE_TO_EVIDENCE,
    TransitionKind.PROJECT_TOOL: LeakFamily.EXPERIENCE_TO_EVIDENCE,
    TransitionKind.REUSE_LESSON: LeakFamily.EXPERIENCE_TO_EVIDENCE,
    TransitionKind.RECORD_FAILURE: LeakFamily.FAILURE_TO_IMPOSSIBILITY,
    TransitionKind.RETRIEVE: LeakFamily.REPETITION_TO_AUTHORITY,
    TransitionKind.UPDATE_ROUTING_POLICY: LeakFamily.ROUTING_TO_AUTHORITY,
    TransitionKind.WORKSPACE_LOAD: LeakFamily.WORKSPACE_TO_AUTHORITY,
    TransitionKind.WORKSPACE_EVICT: LeakFamily.WORKSPACE_TO_AUTHORITY,
    TransitionKind.REFLECT: LeakFamily.REFLECTION_TO_AUTHORITY,
    TransitionKind.SELF_EVOLUTION_WIN: LeakFamily.SELF_EVOLUTION_TO_AUTHORITY,
}


@dataclass(frozen=True)
class Transition:
    """One observed step: a label plus the state it produced.

    ``kind`` is the *declared* family. A caller that mislabels an authority
    promotion as ``RETRIEVE`` does not escape the check — it fails harder,
    because a non-promotion label forbids any authority movement at all.
    """

    transition_id: str
    kind: TransitionKind
    state_after: ComposedResearchState
    #: Only meaningful for EVIDENCE_BEARING_PROMOTION: the roots claimed as
    #: independent support for the grants introduced by this transition.
    claimed_evidence_root_ids: Tuple[str, ...] = ()
    #: Set when the promotion's own assurance was produced by the proposer.
    self_attested: bool = False

    def __post_init__(self) -> None:
        if not self.transition_id.strip():
            raise ValueError("transition requires a non-empty id")


@dataclass(frozen=True)
class NoninterferenceFinding:
    transition_id: str
    kind: TransitionKind
    family: LeakFamily
    reason: str
    added_grants: Tuple[AuthorityGrant, ...] = ()


class NoninterferenceStatus(str, Enum):
    PASS = "PASS"
    LEAK_DETECTED = "LEAK_DETECTED"
    #: The two state families are not composed, so no channel exists to test.
    #: Deliberately distinct from PASS: unreachability is not enforcement.
    NO_INTEGRATION_SURFACE = "NO_INTEGRATION_SURFACE"
    CANNOT_CHECK = "CANNOT_CHECK"


REPORT_SCHEMA_VERSION = "epistemic-noninterference-report-v1"


@dataclass(frozen=True)
class NoninterferenceReport:
    status: NoninterferenceStatus
    findings: Tuple[NoninterferenceFinding, ...] = ()
    reasons: Tuple[str, ...] = ()
    checked_transitions: int = 0
    legal_promotions: int = 0
    families_exercised: frozenset[LeakFamily] = frozenset()

    @property
    def holds(self) -> bool:
        return self.status is NoninterferenceStatus.PASS

    @property
    def grants_authority(self) -> bool:
        """This report is a diagnostic. It never mints authority."""

        return False

    def families_detected(self) -> frozenset[LeakFamily]:
        return frozenset(finding.family for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        """Serialize the diagnostic for schema validation. Never mints authority."""

        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": self.status.value,
            "findings": [
                {
                    "transition_id": finding.transition_id,
                    "kind": finding.kind.value,
                    "family": finding.family.value,
                    "reason": finding.reason,
                    "added_grants": [
                        {
                            "claim_id": grant.claim_id,
                            "axis": grant.axis.value,
                            "scope_id": grant.scope_id,
                            "partial": grant.partial,
                        }
                        for grant in finding.added_grants
                    ],
                }
                for finding in self.findings
            ],
            "reasons": list(self.reasons),
            "checked_transitions": self.checked_transitions,
            "legal_promotions": self.legal_promotions,
            "families_exercised": sorted(family.value for family in self.families_exercised),
            "holds": self.holds,
            "grants_authority": False,
        }


# --------------------------------------------------------------------------
# Promotion contract
# --------------------------------------------------------------------------


def _terminal_root(root_id: str, roots: Mapping[str, EvidenceRoot]) -> str:
    """Follow ``upstream_root_id`` to the lineage root, tolerating cycles."""

    seen: set[str] = set()
    current = root_id
    while current in roots and current not in seen:
        seen.add(current)
        upstream = roots[current].upstream_root_id
        if upstream is None:
            return current
        current = upstream
    return current


#: Axes whose authority may not be minted by support for a strictly weaker axis.
#: Encodes "prediction is not mechanism; mechanism is not identification".
_WEAKER_AXIS_LEAK: Mapping[AuthorityAxis, Tuple[AuthorityAxis, LeakFamily]] = {
    AuthorityAxis.MECHANISM: (AuthorityAxis.REPRESENTATION, LeakFamily.PREDICTION_TO_MECHANISM),
    AuthorityAxis.IDENTIFICATION: (AuthorityAxis.MECHANISM, LeakFamily.MECHANISM_TO_IDENTIFICATION),
}


def _check_promotion(
    transition: Transition,
    added: Sequence[AuthorityGrant],
    roots: Mapping[str, EvidenceRoot],
) -> Tuple[NoninterferenceFinding, ...]:
    """Verify a registered promotion actually satisfies the authority contract."""

    findings: list[NoninterferenceFinding] = []

    if transition.self_attested and added:
        findings.append(
            NoninterferenceFinding(
                transition.transition_id,
                transition.kind,
                LeakFamily.SELF_EVOLUTION_TO_AUTHORITY,
                "promotion assurance was produced by the proposer itself",
                tuple(added),
            )
        )

    claimed = tuple(transition.claimed_evidence_root_ids)
    resolved = [roots[root_id] for root_id in claimed if root_id in roots]

    # Experience objects are never evidence about nature.
    experience_backed = [root for root in resolved if root.kind in _EXPERIENCE_ROOT_KINDS]
    scientific = [root for root in resolved if root.kind in _SCIENTIFIC_ROOT_KINDS]
    if added and experience_backed and not scientific:
        findings.append(
            NoninterferenceFinding(
                transition.transition_id,
                transition.kind,
                LeakFamily.EXPERIENCE_TO_EVIDENCE,
                "authority grant is backed only by experience objects: "
                + ", ".join(sorted(root.root_id for root in experience_backed)),
                tuple(added),
            )
        )

    # Many derivatives of one experiment are not independent evidence roots.
    if len(claimed) > 1:
        terminal = {_terminal_root(root_id, roots) for root_id in claimed}
        if len(terminal) < len(claimed):
            findings.append(
                NoninterferenceFinding(
                    transition.transition_id,
                    transition.kind,
                    LeakFamily.PROVENANCE_TO_INDEPENDENCE,
                    f"{len(claimed)} claimed evidence roots collapse to "
                    f"{len(terminal)} independent lineage root(s)",
                    tuple(added),
                )
            )

    # Axis escalation: support for a weaker axis cannot mint a stronger one.
    supported_axes = frozenset(
        axis for root in scientific for axis in root.supports_axes
    )
    for grant in added:
        weaker = _WEAKER_AXIS_LEAK.get(grant.axis)
        if weaker is None:
            continue
        weaker_axis, family = weaker
        if grant.axis not in supported_axes and weaker_axis in supported_axes:
            findings.append(
                NoninterferenceFinding(
                    transition.transition_id,
                    transition.kind,
                    family,
                    f"grant on {grant.axis.name} is supported only up to "
                    f"{weaker_axis.name} by the registered evidence",
                    (grant,),
                )
            )
    return tuple(findings)


# --------------------------------------------------------------------------
# The invariant
# --------------------------------------------------------------------------


def check_epistemic_noninterference(
    initial: ComposedResearchState,
    transitions: Iterable[Transition],
) -> NoninterferenceReport:
    """Verify EPISTEMIC_NONINTERFERENCE over an observed transition trace.

    Two obligations are checked:

    1. **Invariance.** ``pi_auth`` is unchanged by every transition whose kind
       is not :data:`TransitionKind.EVIDENCE_BEARING_PROMOTION`.
    2. **Contract.** Every registered promotion that *does* move ``pi_auth``
       satisfies the authority contract for the affected axis (independent
       lineage, evidence that is not merely experience, no axis escalation,
       no self-attestation).

    A trace containing no promotion and no composed authority ledger returns
    ``NO_INTEGRATION_SURFACE`` rather than ``PASS``.
    """

    steps = tuple(transitions)
    roots = dict(initial.root_by_id())
    for step in steps:
        roots.update(step.state_after.root_by_id())

    findings: list[NoninterferenceFinding] = []
    families: set[LeakFamily] = set()
    legal_promotions = 0

    previous = pi_auth(initial)
    composed = initial.authority is not None
    for step in steps:
        composed = composed or step.state_after.authority is not None
        current = pi_auth(step.state_after)
        added = tuple(sorted(current - previous, key=lambda g: (g.claim_id, g.axis.value, g.scope_id)))
        removed = tuple(sorted(previous - current, key=lambda g: (g.claim_id, g.axis.value, g.scope_id)))

        if step.kind is TransitionKind.EVIDENCE_BEARING_PROMOTION:
            step_findings = _check_promotion(step, added, roots)
            findings.extend(step_findings)
            families.update(finding.family for finding in step_findings)
            if added and not step_findings:
                legal_promotions += 1
        elif added or removed:
            family = _LEAK_FAMILY_BY_KIND.get(step.kind, LeakFamily.EXPERIENCE_TO_EVIDENCE)
            families.add(family)
            detail = "added" if added else "revoked"
            findings.append(
                NoninterferenceFinding(
                    step.transition_id,
                    step.kind,
                    family,
                    f"{step.kind.value} {detail} scientific authority outside a "
                    "registered evidence-bearing promotion",
                    added or removed,
                )
            )
        previous = current

    if findings:
        return NoninterferenceReport(
            NoninterferenceStatus.LEAK_DETECTED,
            tuple(findings),
            tuple(sorted({finding.reason for finding in findings})),
            len(steps),
            legal_promotions,
            frozenset(families),
        )
    if not composed:
        return NoninterferenceReport(
            NoninterferenceStatus.NO_INTEGRATION_SURFACE,
            (),
            (
                "no authority ledger is composed with the experience state, so "
                "no experience-to-authority channel exists to exercise",
            ),
            len(steps),
            legal_promotions,
            frozenset(),
        )
    return NoninterferenceReport(
        NoninterferenceStatus.PASS,
        (),
        (),
        len(steps),
        legal_promotions,
        frozenset(),
    )


# --------------------------------------------------------------------------
# Integration-surface audit of the current framework revision
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrationSurfaceReport:
    """Structural evidence about whether the leak channel exists in-tree."""

    composed: bool
    v3_state_fields: Tuple[str, ...]
    authority_axis_carriers: Tuple[str, ...]
    non_authority_carriers: Tuple[str, ...]
    reasons: Tuple[str, ...]


def describe_integration_surface() -> IntegrationSurfaceReport:
    """Audit whether ``RAKLV3State`` reaches the scientific-authority ledger.

    Determined structurally from the live dataclass rather than asserted, so the
    report follows the code if a future revision wires the two together.
    """

    from . import v3_runtime

    state_fields = tuple(item.name for item in fields(v3_runtime.RAKLV3State))
    annotations = {
        item.name: str(item.type) for item in fields(v3_runtime.RAKLV3State)
    }
    carriers = tuple(
        name for name, annotation in annotations.items() if "Authority" in annotation
    )
    composed = bool(carriers)
    reasons: list[str] = []
    if not composed:
        reasons.append(
            "RAKLV3State composes no AuthorityLedger; scientific authority "
            "(AuthorityAxis G/R/M/I/D) is unreachable from the v3 experience state"
        )
        reasons.append(
            "the invariant is therefore prospective: it constrains integration "
            "code that composes the two families, and cannot be reported as an "
            "enforced property of the current revision"
        )
    return IntegrationSurfaceReport(
        composed=composed,
        v3_state_fields=state_fields,
        authority_axis_carriers=carriers,
        non_authority_carriers=(
            f"experience_substrate.LessonAuthority({len(LessonAuthority)} levels)",
            "research_tool_inventory.ResearchTool.authority",
            "core.KnowledgeFiber projection authority",
        ),
        reasons=tuple(reasons),
    )
