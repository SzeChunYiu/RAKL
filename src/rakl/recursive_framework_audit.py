"""Recursive Framework Audit v1 (RFA) — proposal-side recursive formulation control.

Implements the RAKL Recursive Formulation Principle: one recursive audit
operator governs (1) a new problem's formulation, (2) every descendant fiber,
and (3) RAKL's own method evolution (escalation only).  RFA is a *vertical
controller* over the existing L0–L7 mechanics — it does not add a layer, does
not mint authority, does not create a second authority architecture, and
cannot bypass ``CURRENT_SELF_EVOLUTION_CONTROLLER``.

Decision semantics are frozen against the vendored handoff reference
``research/recursive_framework_audit_v1/reference/recursive_framework_audit_reference.py``
(audited repo head ``4ef389360af3ea035817057da931267b7844e133``) and the
known-world freeze
``research/recursive_framework_audit_v1/RFA_V1_FROZEN_BENCHMARK.json``.

Claim boundary: ``research/recursive_framework_audit_v1/RFA_V1_CLAIM_BOUNDARY.md``.
Known-world conformance is not utility evidence.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum

from .metacognition import MetacognitiveAuditVerdict, formulation_gap_candidate
from .self_evolution_controller import CURRENT_SELF_EVOLUTION_CONTROLLER


class AuditCoordinate(str, Enum):
    """Coordinates of the audited pursuit object that can carry responsibility."""

    QUESTION = "QUESTION"
    FRAMEWORK = "FRAMEWORK"
    DECOMPOSITION = "DECOMPOSITION"
    INTERFACE = "INTERFACE"
    ATOM = "ATOM"
    MEASUREMENT = "MEASUREMENT"
    EVALUATOR = "EVALUATOR"
    EVIDENCE = "EVIDENCE"
    METHOD = "METHOD"


class AuditAction(str, Enum):
    """Pursuit actions an audit may select.  None mints authority.

    ``DESCEND`` is licensed by existing routing mechanics (the audit may hand
    control to a chosen child fiber); the frozen ``decide`` chain itself never
    needs to emit it, mirroring the reference semantics.
    """

    SOLVE_CURRENT = "SOLVE_CURRENT"
    REFRAME_QUESTION = "REFRAME_QUESTION"
    CHALLENGE_FRAMEWORK = "CHALLENGE_FRAMEWORK"
    SPLIT = "SPLIT"
    MERGE = "MERGE"
    REPAIR_INTERFACE = "REPAIR_INTERFACE"
    REVISE_MEASUREMENT = "REVISE_MEASUREMENT"
    AUDIT_EVALUATOR = "AUDIT_EVALUATOR"
    RUN_DISCRIMINATOR = "RUN_DISCRIMINATOR"
    DESCEND = "DESCEND"
    ASCEND = "ASCEND"
    EXTERNAL_TRUST_ROOT = "EXTERNAL_TRUST_ROOT"
    STOP_BOUNDED = "STOP_BOUNDED"
    CANNOT_CHECK = "CANNOT_CHECK"


_SINGLE_CAUSE_ACTION: dict[AuditCoordinate, AuditAction] = {
    AuditCoordinate.QUESTION: AuditAction.REFRAME_QUESTION,
    AuditCoordinate.FRAMEWORK: AuditAction.CHALLENGE_FRAMEWORK,
    AuditCoordinate.DECOMPOSITION: AuditAction.SPLIT,
    AuditCoordinate.INTERFACE: AuditAction.REPAIR_INTERFACE,
    AuditCoordinate.ATOM: AuditAction.SPLIT,
    AuditCoordinate.MEASUREMENT: AuditAction.REVISE_MEASUREMENT,
    AuditCoordinate.EVALUATOR: AuditAction.AUDIT_EVALUATOR,
    AuditCoordinate.EVIDENCE: AuditAction.SOLVE_CURRENT,
    AuditCoordinate.METHOD: AuditAction.SOLVE_CURRENT,
}


def _digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Phase 1 — proposal-side pursuit objects (versioned, non-sovereign)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestionFormulationCandidate:
    """One candidate statement of the research question.

    A candidate guides search only.  Committing it changes pursuit state,
    never scientific authority.
    """

    question_id: str
    statement: str
    well_posed_receipt_digest: str | None = None
    decision_consumer: str = ""
    superseded_by: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def well_posed_checked(self) -> bool:
        return self.well_posed_receipt_digest is not None

    def __post_init__(self) -> None:
        if not self.question_id or not self.statement:
            raise ValueError("question candidates require an id and a statement")


@dataclass(frozen=True)
class FrameworkCandidate:
    """One candidate representation/framework with its licensed scope."""

    framework_id: str
    assumptions: tuple[str, ...] = ()
    licensed_scope: str = ""
    superseded_by: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class DecompositionCandidate:
    """One candidate split of a fiber into child fibers."""

    decomposition_id: str
    child_fiber_ids: tuple[str, ...] = ()
    split_family: str = ""

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    def __post_init__(self) -> None:
        if len(set(self.child_fiber_ids)) != len(self.child_fiber_ids):
            raise ValueError("child fiber ids must be distinct")


@dataclass(frozen=True)
class InterfaceContract:
    """Parent-child interface: exchanged obligations, erasure map and transport license.

    The handoff packet requires an interface to bind ten things, not three:
    the discharged parent obligation, inherited inputs, returned outputs,
    assumptions, scope/context, units/representation, the authority that may
    and may not transport across the boundary, uncertainty composition and
    failure/``CANNOT_CHECK`` semantics.  The additional bindings default to
    empty so existing contracts stay constructible, but ``complete`` is false
    until all of them are supplied, and authority transport is **fail closed**:
    anything not explicitly licensed is unlicensed.
    """

    parent_fiber_id: str
    child_fiber_id: str
    child_obligations: tuple[str, ...] = ()
    parent_consumables: tuple[str, ...] = ()
    erasure_map: tuple[tuple[str, str], ...] = ()
    parent_obligation_discharged: str = ""
    inherited_inputs: tuple[str, ...] = ()
    returned_outputs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    scope: str = ""
    units: str = ""
    authority_transportable: tuple[str, ...] = ()
    authority_forbidden: tuple[str, ...] = ()
    uncertainty_composition: str = ""
    failure_semantics: str = ""

    def __post_init__(self) -> None:
        contradictory = set(self.authority_transportable) & set(self.authority_forbidden)
        if contradictory:
            raise ValueError(
                "authority cannot be both transportable and forbidden across one "
                f"interface: {sorted(contradictory)}"
            )

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def complete(self) -> bool:
        """True only when every binding the packet requires is present."""

        return all(
            (
                self.child_obligations,
                self.parent_obligation_discharged,
                self.inherited_inputs,
                self.returned_outputs,
                self.assumptions,
                self.scope,
                self.units,
                self.authority_transportable or self.authority_forbidden,
                self.uncertainty_composition,
                self.failure_semantics,
            )
        )

    def licenses(self, authority_kind: str) -> bool:
        """Fail closed: only explicitly transportable authority is licensed."""

        return (
            authority_kind in self.authority_transportable
            and authority_kind not in self.authority_forbidden
        )

    def unlicensed_transports(self, claimed: "Iterable[str]") -> tuple[str, ...]:
        """Claimed transports this interface does not license.

        A child cannot silently update its parent: every claim outside the
        licensed set is returned here rather than quietly allowed through.
        """

        return tuple(kind for kind in dict.fromkeys(claimed) if not self.licenses(kind))


@dataclass(frozen=True)
class AtomicityReceipt:
    """Provisional atomicity, indexed by target/split-family/evaluator/cutoff.

    Atomicity is *scoped*: a fiber is provisionally atomic only relative to a
    registered target, split family, evaluator epoch, evidence cutoff and
    decision consumer.  There is deliberately no ``ATOM_PROVEN_FOREVER``
    terminal — requesting it is a defect, not an upgrade.
    """

    target_id: str
    split_family: str
    evaluator_epoch: str
    evidence_cutoff: str
    decision_consumer: str = ""
    terminal: str = "PROVISIONALLY_ATOMIC_AT_REGISTERED_CUTOFF"

    def __post_init__(self) -> None:
        if self.terminal == "ATOM_PROVEN_FOREVER":
            raise ValueError(
                "ATOM_PROVEN_FOREVER is not a legal terminal: atomicity is "
                "target/split-family/evaluator/cutoff relative"
            )
        if self.terminal != "PROVISIONALLY_ATOMIC_AT_REGISTERED_CUTOFF":
            raise ValueError(f"unknown atomicity terminal: {self.terminal!r}")
        if not (self.target_id and self.split_family and self.evaluator_epoch and self.evidence_cutoff):
            raise ValueError("atomicity receipts must be fully indexed")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def index(self) -> tuple[str, str, str, str]:
        return (self.target_id, self.split_family, self.evaluator_epoch, self.evidence_cutoff)

    def valid_for(self, target_id: str, split_family: str, evaluator_epoch: str, evidence_cutoff: str) -> bool:
        """A receipt never subsumes a different index; exact match only."""

        return self.index == (target_id, split_family, evaluator_epoch, evidence_cutoff)


@dataclass(frozen=True)
class AncestorChallenge:
    """Evidence-backed challenge of an ancestor abstraction by descendants.

    Requires a supported parent challenge and at least two distinct failed
    local repair families.  Supersession *stales* dependent descendant closure
    certificates; it never deletes them or their evidence (negative history
    remains addressable under the superseded parent identity).
    """

    ancestor_fiber_id: str
    challenge_evidence_digest: str
    failed_local_repair_families: tuple[str, ...] = ()
    dependent_descendant_ids: tuple[str, ...] = ()
    supersession_registered: bool = False
    child_fiber_id: str = ""
    residual_id: str = ""
    local_causes_tested: tuple[AuditCoordinate, ...] = ()
    fresh_evidence_epochs: tuple[str, ...] = ()
    parent_coordinate_implicated: AuditCoordinate | None = None
    local_vs_parent_discriminator_id: str = ""
    cost: int = 0

    def __post_init__(self) -> None:
        if len(set(self.failed_local_repair_families)) != len(self.failed_local_repair_families):
            raise ValueError("failed local repair families must be distinct")
        if not self.challenge_evidence_digest:
            raise ValueError("an ancestor challenge requires evidence")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def distinct_local_repair_families_failed(self) -> int:
        return len(self.failed_local_repair_families)

    @property
    def admissible_for_ascent(self) -> bool:
        return self.supersession_registered is False and self.distinct_local_repair_families_failed >= 2

    @property
    def packet_complete(self) -> bool:
        """True when the challenge carries every field the packet requires.

        Child identity, residual identity, local causes tested, distinct failed
        repair families, fresh evidence epochs, the implicated parent
        coordinate, the local-vs-parent discriminator and cost.  Repeated raw
        failures are not a packet.
        """

        return all(
            (
                self.child_fiber_id,
                self.residual_id,
                self.local_causes_tested,
                self.failed_local_repair_families,
                self.fresh_evidence_epochs,
                self.parent_coordinate_implicated is not None,
                self.local_vs_parent_discriminator_id,
                self.cost >= 0,
            )
        )

    @property
    def escalation_admissible(self) -> bool:
        """Ascent needs a complete packet *and* a parent-discriminating witness.

        Stricter than ``admissible_for_ascent``, which encodes only the frozen
        two-failed-families rule the decision chain reads.  Distinct failed
        local repairs establish that the local level is not responsible; only
        the discriminator separates parent from child.
        """

        return self.admissible_for_ascent and self.packet_complete

    def with_supersession(self) -> "AncestorChallenge":
        """Register supersession: descendant closure certificates go stale.

        Every field is carried forward; supersession never drops the packet
        that justified it, and never deletes descendants or their evidence.
        """

        return replace(self, supersession_registered=True)

    def descendant_closure_stale(self, descendant_fiber_id: str) -> bool:
        if not self.supersession_registered:
            return False
        return descendant_fiber_id in self.dependent_descendant_ids


@dataclass(frozen=True)
class RecursiveAuditProjection:
    """pi_audit(f): audit projection of an existing recursive fiber.

    A projection of the existing research state — not a second authority
    architecture.  The evaluator epoch identity closes the evaluation epoch:
    changing it yields a new epoch id and no cross-epoch comparison is offered.
    """

    fiber_id: str
    question_candidates: tuple[QuestionFormulationCandidate, ...] = ()
    framework_candidates: tuple[FrameworkCandidate, ...] = ()
    decomposition_candidates: tuple[DecompositionCandidate, ...] = ()
    interface_contracts: tuple[InterfaceContract, ...] = ()
    measurement_contracts: tuple[str, ...] = ()
    evaluator_epoch: str = ""
    responsibility_hypotheses: tuple[AuditCoordinate, ...] = ()
    closure_coordinates_pass: bool = False
    material_open_residual: bool = True
    preserved_evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.fiber_id:
            raise ValueError("projections require a fiber id")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def epoch_id(self) -> str:
        """Epoch identity is a digest of the evaluator epoch only."""

        return _digest(f"rfa-epoch:{self.evaluator_epoch}")

    def same_epoch(self, other: "RecursiveAuditProjection") -> bool | None:
        """``True``/``False`` within a comparable lineage, ``None`` = not comparable.

        No cross-epoch comparison is offered beyond the boolean fact of epoch
        identity: an epoch change closes the evaluation epoch, and nothing in
        this module bridges the two.
        """

        return None if not self.evaluator_epoch or not other.evaluator_epoch else self.epoch_id == other.epoch_id


@dataclass(frozen=True)
class RecursiveAuditDecision:
    """The selected pursuit action.  Structurally incapable of carrying authority."""

    action: AuditAction
    reasons: tuple[str, ...] = ()
    coordinates: tuple[AuditCoordinate, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Frozen decision semantics (differential-conformant to the vendored reference)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditResidual:
    """Material residual on a fiber, as localized by existing diagnosis mechanics.

    ``plausible_causes`` lists the audit coordinates that remain plausible
    responsibility hypotheses.  More than one distinct cause requires a
    discriminator before any revision (no post-hoc selection of the winning
    level).
    """

    plausible_causes: tuple[AuditCoordinate, ...] = ()
    split_required: bool = False
    merge_required: bool = False
    parent_challenge_supported: bool = False
    distinct_local_repair_families_failed: int = 0
    evaluator_invalid: bool = False
    external_trust_root: bool = False
    resource_bound: bool = False

    def __post_init__(self) -> None:
        if self.distinct_local_repair_families_failed < 0:
            raise ValueError("failed local repair families cannot be negative")
        if len(set(self.plausible_causes)) != len(self.plausible_causes):
            # Canonicalize: plausible_causes is a set of responsibility
            # hypotheses — a repeated coordinate is the same hypothesis, not a
            # second level (benchmark H07).  The vendored reference checks
            # ``len(causes) == 1`` literally, so a duplicated coordinate would
            # bypass its single-cause branch; canonicalization removes the
            # ambiguity at the type boundary instead of inside decide().
            object.__setattr__(self, "plausible_causes", tuple(dict.fromkeys(self.plausible_causes)))


@dataclass(frozen=True)
class AuditNode:
    """Audited closure state of one fiber at decision time."""

    closure_coordinates_pass: bool = False
    material_open_residual: bool = True


def decide(node: AuditNode, residual: AuditResidual) -> RecursiveAuditDecision:
    """Select the pursuit action.  Pure function of ``(node, residual)``.

    Priority chain (frozen; mirrors the vendored reference exactly):

    1. evaluator invalid          -> ``AUDIT_EVALUATOR``
    2. external trust root        -> ``EXTERNAL_TRUST_ROOT``
    3. resource bound with material open audit -> ``CANNOT_CHECK``
    4. supported ancestor challenge with >= 2 failed local repair families
                                  -> ``ASCEND``
    5. > 1 distinct plausible causes -> ``RUN_DISCRIMINATOR``
    6. split required             -> ``SPLIT``
    7. merge required             -> ``MERGE``
    8. single cause               -> coordinate-mapped revision
    9. closure passing, no open residual -> ``STOP_BOUNDED``
    10. otherwise                 -> ``SOLVE_CURRENT``
    """

    if residual.evaluator_invalid:
        return RecursiveAuditDecision(
            AuditAction.AUDIT_EVALUATOR,
            ("evaluator invalid: audit the evaluator before any pursuit revision",),
        )
    if residual.external_trust_root:
        return RecursiveAuditDecision(
            AuditAction.EXTERNAL_TRUST_ROOT,
            ("external identity ungrounded: local receipts cannot close this",),
        )
    if residual.resource_bound and (node.material_open_residual or residual.plausible_causes):
        return RecursiveAuditDecision(
            AuditAction.CANNOT_CHECK,
            ("resource bound with material open audit: abstain rather than guess",),
        )
    if residual.parent_challenge_supported and residual.distinct_local_repair_families_failed >= 2:
        return RecursiveAuditDecision(
            AuditAction.ASCEND,
            (
                "ancestor challenge supported with "
                f"{residual.distinct_local_repair_families_failed} distinct failed local repair families",
            ),
            tuple(residual.plausible_causes),
        )
    if len(set(residual.plausible_causes)) > 1:
        return RecursiveAuditDecision(
            AuditAction.RUN_DISCRIMINATOR,
            ("multiple plausible responsibility levels: discriminator before revision",),
            tuple(residual.plausible_causes),
        )
    if residual.split_required:
        return RecursiveAuditDecision(AuditAction.SPLIT, ("split required: atom hides distinct regimes",))
    if residual.merge_required:
        return RecursiveAuditDecision(AuditAction.MERGE, ("merge required: children decision-equivalent",))
    if residual.plausible_causes:
        cause = residual.plausible_causes[0]
        return RecursiveAuditDecision(
            _SINGLE_CAUSE_ACTION[cause],
            (f"single responsible coordinate: {cause.value}",),
            (cause,),
        )
    if node.closure_coordinates_pass and not node.material_open_residual:
        return RecursiveAuditDecision(
            AuditAction.STOP_BOUNDED,
            ("closure coordinates pass with no material open residual at the registered cutoff",),
        )
    return RecursiveAuditDecision(AuditAction.SOLVE_CURRENT, ("no formulation-level defect indicated",))


# ---------------------------------------------------------------------------
# Phase 3 — general-problem entrypoints
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProblemStatement:
    """A problem request *before* formulation commitment.

    Carries the registered alternatives and the governance inputs the
    pre-commit audit needs.  The first textual statement of an unfamiliar
    problem is not assumed to supply the correct scientific question.
    """

    problem_id: str
    question_candidates: tuple[QuestionFormulationCandidate, ...] = ()
    framework_candidates: tuple[FrameworkCandidate, ...] = ()
    evaluator_epoch: str = ""
    evaluator_validated: bool = True
    external_trust_root: bool = False
    resource_bound: bool = False
    material_open_residual: bool = True

    def __post_init__(self) -> None:
        if not self.problem_id:
            raise ValueError("problem statements require an id")
        if not self.question_candidates:
            raise ValueError("a problem must register at least one question candidate")


@dataclass(frozen=True)
class DiscriminatorReceipt:
    """Receipt that a decision-bearing discriminator separated registered alternatives."""

    discriminator_id: str
    separated_candidate_ids: tuple[str, ...] = ()
    winning_candidate_id: str = ""
    evidence_digest: str = ""


def audit_before_commit(
    problem: ProblemStatement,
    discriminator_receipt: DiscriminatorReceipt | None = None,
) -> RecursiveAuditDecision:
    """Audit a problem's formulation before committing to it.

    An invalid evaluator fails closed *before* commit; divergent registered
    alternatives require a discriminator (no post-hoc selection of the winning
    formulation after the fact); a resource bound with material open audit
    abstains.  A single well-posed candidate under a valid evaluator commits
    to ``SOLVE_CURRENT`` — gratuitous reframing on well-posed problems is
    registered harm, not diligence.
    """

    active_questions = tuple(q for q in problem.question_candidates if q.superseded_by is None)
    active_frameworks = tuple(f for f in problem.framework_candidates if f.superseded_by is None)

    if not problem.evaluator_validated:
        return RecursiveAuditDecision(
            AuditAction.AUDIT_EVALUATOR,
            ("evaluator not validated: fail closed before formulation commit",),
            (AuditCoordinate.EVALUATOR,),
        )
    if problem.external_trust_root:
        return RecursiveAuditDecision(
            AuditAction.EXTERNAL_TRUST_ROOT,
            ("external identity ungrounded before commit",),
        )
    if problem.resource_bound and (problem.material_open_residual or active_questions):
        return RecursiveAuditDecision(
            AuditAction.CANNOT_CHECK,
            ("resource bound with the formulation audit open",),
        )

    separated: set[str] = set()
    if discriminator_receipt is not None:
        separated = set(discriminator_receipt.separated_candidate_ids)

    divergent_questions = [q for q in active_questions if q.question_id not in separated]
    if len({q.statement for q in divergent_questions}) > 1:
        return RecursiveAuditDecision(
            AuditAction.RUN_DISCRIMINATOR,
            ("divergent active question candidates without a discriminator",),
            (AuditCoordinate.QUESTION,),
        )
    unseparated_frameworks = [f for f in active_frameworks if f.framework_id not in separated]
    if len(unseparated_frameworks) > 1:
        return RecursiveAuditDecision(
            AuditAction.RUN_DISCRIMINATOR,
            ("divergent active framework candidates without a discriminator",),
            (AuditCoordinate.FRAMEWORK,),
        )

    return RecursiveAuditDecision(
        AuditAction.SOLVE_CURRENT,
        ("formulation committed: solve at the current representation",),
    )


def audit_after_material_residual(
    node: AuditNode,
    residual: AuditResidual,
) -> RecursiveAuditDecision:
    """Audit an existing fiber after a material residual: thin, frozen wrapper."""

    return decide(node, residual)


# ---------------------------------------------------------------------------
# Phase 2 composition — existing mechanics are called, never duplicated
# ---------------------------------------------------------------------------


def metacognitive_gap_candidates(residual: AuditResidual) -> tuple[MetacognitiveAuditVerdict, ...]:
    """Map plausible audit coordinates to metacognition gap-candidate verdicts.

    Uses the proposal-side diagnostics exported by the existing metacognition
    module; the diagnosis remains a candidate only (``metacognition.py`` never
    repairs or promotes anything, and neither does this adapter).
    """

    return tuple(formulation_gap_candidate(cause) for cause in dict.fromkeys(residual.plausible_causes))


@dataclass(frozen=True)
class SelfRaklEscalationRequest:
    """A request to enter the existing Self-RAKL challenger protocol.

    RFA may *request* escalation; it cannot bypass
    ``CURRENT_SELF_EVOLUTION_CONTROLLER``, which remains the only method-
    evolution gate and is itself non-sovereign.
    """

    requesting_action: AuditAction
    controller_version: str
    controller_grants_scientific_authority: bool
    controller_grants_method_promotion_authority: bool
    evidence_digest: str = ""

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def enters_existing_challenger_protocol(self) -> bool:
        return True


def request_self_rakl_escalation(
    decision: RecursiveAuditDecision,
    evidence_digest: str = "",
) -> SelfRaklEscalationRequest:
    """Request (never perform) Self-RAKL escalation through the canonical controller."""

    controller = CURRENT_SELF_EVOLUTION_CONTROLLER
    return SelfRaklEscalationRequest(
        requesting_action=decision.action,
        controller_version=controller.version,
        controller_grants_scientific_authority=controller.grants_scientific_authority,
        controller_grants_method_promotion_authority=controller.grants_method_promotion_authority,
        evidence_digest=evidence_digest,
    )


# ---------------------------------------------------------------------------
# Provisional atomicity — admissibility conditions (packet section 06)
# ---------------------------------------------------------------------------


class AtomicitySplitCondition(str, Enum):
    """The five conditions a registered split family must clear.

    A fiber is provisionally atomic at a registered target, evaluator, split
    family and cutoff only if every one of these holds over that split family.
    """

    NO_MATERIALLY_DIFFERENT_TARGET_PREDICTIONS = "NO_MATERIALLY_DIFFERENT_TARGET_PREDICTIONS"
    NO_DIFFERENT_AUTHORITY_PREREQUISITES = "NO_DIFFERENT_AUTHORITY_PREREQUISITES"
    NO_DIFFERENT_OPTIMAL_DECISION_ACTION = "NO_DIFFERENT_OPTIMAL_DECISION_ACTION"
    NO_CHILD_FALSIFIER_EXPOSING_MIXED_REGIME = "NO_CHILD_FALSIFIER_EXPOSING_MIXED_REGIME"
    NO_OMITTED_STRUCTURE_FROM_INTERFACE_BURDEN = "NO_OMITTED_STRUCTURE_FROM_INTERFACE_BURDEN"


def issue_atomicity_receipt(
    *,
    target_id: str,
    split_family: str,
    evaluator_epoch: str,
    evidence_cutoff: str,
    satisfied_conditions: Iterable[AtomicitySplitCondition],
    decision_consumer: str = "",
) -> AtomicityReceipt:
    """Issue a provisional atomicity receipt only when all five conditions hold.

    ``AtomicityReceipt`` itself stays constructible as a plain record; this is
    the checked constructor.  Missing conditions fail closed rather than
    downgrading to a weaker terminal — an unchecked split family is not
    evidence of atomicity, it is an unrun check.
    """

    satisfied = set(satisfied_conditions)
    missing = tuple(c.value for c in AtomicitySplitCondition if c not in satisfied)
    if missing:
        raise ValueError(f"atomicity conditions not established over the split family: {list(missing)}")
    return AtomicityReceipt(
        target_id=target_id,
        split_family=split_family,
        evaluator_epoch=evaluator_epoch,
        evidence_cutoff=evidence_cutoff,
        decision_consumer=decision_consumer,
    )


# ---------------------------------------------------------------------------
# Stopping law — mandatory triggers, value of audit, bounded node closure
# (packet section 08)
# ---------------------------------------------------------------------------


class AuditTrigger(str, Enum):
    """Conditions under which an audit is mandatory, not optional."""

    EVALUATOR_INVALID = "EVALUATOR_INVALID"
    AUTHORITY_LEAK_RISK = "AUTHORITY_LEAK_RISK"
    UNRESOLVED_CONTRADICTION = "UNRESOLVED_CONTRADICTION"
    TARGET_UNREACHABLE = "TARGET_UNREACHABLE"
    REPEATED_UNCLASSIFIED_RESIDUAL = "REPEATED_UNCLASSIFIED_RESIDUAL"
    DISTINCT_LOCAL_REPAIRS_FAIL = "DISTINCT_LOCAL_REPAIRS_FAIL"
    INTERFACE_GLUE_FAILURE = "INTERFACE_GLUE_FAILURE"
    MEASUREMENT_MODEL_FAILURE = "MEASUREMENT_MODEL_FAILURE"
    HIGH_STAKES_DOMAIN_TRANSFER = "HIGH_STAKES_DOMAIN_TRANSFER"
    CHALLENGER_CHANGES_THE_DECISION = "CHALLENGER_CHANGES_THE_DECISION"


def mandatory_audit_triggered(triggers: Iterable[AuditTrigger]) -> bool:
    """Any registered trigger makes the audit mandatory regardless of its value."""

    return bool(tuple(triggers))


@dataclass(frozen=True)
class OptionalAuditCandidate:
    """One optional audit action, with the inputs the stopping law admits."""

    action: AuditAction
    registered_priority: int
    cost: int
    separates_decision: bool = False
    expected_utility_gain: int | None = None

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("audit cost cannot be negative")
        if self.registered_priority < 0:
            raise ValueError("registered priority cannot be negative")


def select_optional_audit(
    candidates: Iterable[OptionalAuditCandidate],
    *,
    calibrated: bool = False,
) -> OptionalAuditCandidate | None:
    """Choose the next optional audit, or ``None`` to stop.

    With calibrated probabilities the packet's value-of-audit rule applies:
    ``VOA(a) = E[U* after a] - U* now - Cost(a)``, and only a strictly positive
    VOA justifies opening the node.  Without them the fallback is
    ``hard trigger -> worst-case decision separation -> registered priority ->
    cost``; candidates that cannot separate the decision are not opened.

    Priors are never invented: asking for the calibrated rule without supplying
    every expected-utility gain raises instead of substituting a default.
    """

    pool = tuple(candidates)
    if not pool:
        return None
    if calibrated:
        missing = tuple(c.action.value for c in pool if c.expected_utility_gain is None)
        if missing:
            raise ValueError(
                "calibrated value-of-audit requires an expected utility gain for every "
                f"candidate; missing: {list(missing)}"
            )
        scored = [(c.expected_utility_gain - c.cost, c) for c in pool]
        best_value, best = max(scored, key=lambda pair: (pair[0], -pair[1].registered_priority))
        return best if best_value > 0 else None
    separating = [c for c in pool if c.separates_decision]
    if not separating:
        return None
    return min(separating, key=lambda c: (c.registered_priority, c.cost))


class NodeClosureTerminal(str, Enum):
    """Terminals of the bounded node-closure assessment."""

    NODE_CLOSED_AT_REGISTERED_CUTOFF = "NODE_CLOSED_AT_REGISTERED_CUTOFF"
    NODE_OPEN = "NODE_OPEN"
    CANNOT_CHECK_RESOURCE_BOUND = "CANNOT_CHECK_RESOURCE_BOUND"


@dataclass(frozen=True)
class NodeClosureAssessment:
    """Result of the eight-condition bounded closure check.  Carries no authority."""

    terminal: NodeClosureTerminal
    unmet_conditions: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def closed(self) -> bool:
        return self.terminal is NodeClosureTerminal.NODE_CLOSED_AT_REGISTERED_CUTOFF


def assess_bounded_node_closure(
    *,
    question_decision_sufficient: bool,
    framework_not_dominated: bool,
    decomposition_checks_pass: bool,
    interfaces_complete: bool,
    measurement_and_evaluator_valid: bool,
    target_solved_or_blocker_typed: bool,
    no_decision_relevant_residual: bool,
    no_material_optional_audit_value: bool,
    resource_bound: bool = False,
) -> NodeClosureAssessment:
    """Assess ``NODE_CLOSED_AT_REGISTERED_CUTOFF`` against all eight conditions.

    Closure is decision- and cutoff-relative, never global completeness.  A
    resource cap arriving while any condition is still unmet is
    ``CANNOT_CHECK_RESOURCE_BOUND`` — a resource block is not a solver failure
    and not a scientific terminal, so it is never rounded down to ``NODE_OPEN``
    or up to closure.
    """

    conditions = (
        ("question_decision_sufficient", question_decision_sufficient),
        ("framework_not_dominated", framework_not_dominated),
        ("decomposition_checks_pass", decomposition_checks_pass),
        ("interfaces_complete", interfaces_complete),
        ("measurement_and_evaluator_valid", measurement_and_evaluator_valid),
        ("target_solved_or_blocker_typed", target_solved_or_blocker_typed),
        ("no_decision_relevant_residual", no_decision_relevant_residual),
        ("no_material_optional_audit_value", no_material_optional_audit_value),
    )
    unmet = tuple(name for name, met in conditions if not met)
    if unmet:
        terminal = (
            NodeClosureTerminal.CANNOT_CHECK_RESOURCE_BOUND
            if resource_bound
            else NodeClosureTerminal.NODE_OPEN
        )
        return NodeClosureAssessment(terminal, unmet)
    return NodeClosureAssessment(NodeClosureTerminal.NODE_CLOSED_AT_REGISTERED_CUTOFF)


# ---------------------------------------------------------------------------
# Question and framework audit gates (packet section 05)
# ---------------------------------------------------------------------------


class QuestionAdequacyCoordinate(str, Enum):
    """Coordinates of question adequacy.  There is deliberately no scalar score."""

    DECISION_RELEVANCE = "DECISION_RELEVANCE"
    SCOPE_CLARITY = "SCOPE_CLARITY"
    ALTERNATIVE_DISTINGUISHABILITY = "ALTERNATIVE_DISTINGUISHABILITY"
    FALSIFIABILITY_OR_BOUNDABILITY = "FALSIFIABILITY_OR_BOUNDABILITY"
    MEASUREMENT_AVAILABILITY = "MEASUREMENT_AVAILABILITY"
    IDENTIFIABILITY = "IDENTIFIABILITY"
    PARENT_FORMULATION_COVERAGE = "PARENT_FORMULATION_COVERAGE"
    NONDEGENERACY = "NONDEGENERACY"
    RESOURCE_FEASIBILITY = "RESOURCE_FEASIBILITY"


class FrameworkAdequacyCoordinate(str, Enum):
    """Coordinates of framework adequacy *for a target*, never global rightness."""

    TARGET_EXPRESSIBILITY = "TARGET_EXPRESSIBILITY"
    ALTERNATIVE_EXPRESSIBILITY = "ALTERNATIVE_EXPRESSIBILITY"
    DISCRIMINATING_PREDICTIONS = "DISCRIMINATING_PREDICTIONS"
    INTERFACE_VALIDITY = "INTERFACE_VALIDITY"
    MEASUREMENT_GROUNDING = "MEASUREMENT_GROUNDING"
    UNCERTAINTY_SEMANTICS = "UNCERTAINTY_SEMANTICS"
    DECISION_SUFFICIENCY = "DECISION_SUFFICIENCY"
    RESIDUAL_LOCALIZABILITY = "RESIDUAL_LOCALIZABILITY"
    FRESH_TRANSFER = "FRESH_TRANSFER"
    COMPLEXITY_COST = "COMPLEXITY_COST"


class FrameworkParentFamily(str, Enum):
    """The parent families a framework portfolio must register before selection."""

    DIRECT_MINIMAL_REPRESENTATION = "DIRECT_MINIMAL_REPRESENTATION"
    CANONICAL_DOMAIN_FRAMEWORK = "CANONICAL_DOMAIN_FRAMEWORK"
    STRONGEST_RETRIEVED_ALTERNATIVE = "STRONGEST_RETRIEVED_ALTERNATIVE"
    CURRENT_RAKL_COMPILED_FRAMEWORK = "CURRENT_RAKL_COMPILED_FRAMEWORK"
    SYNTHESIZED_CHALLENGER = "SYNTHESIZED_CHALLENGER"


_MINIMUM_FRAMEWORK_PARENTS: tuple[FrameworkParentFamily, ...] = (
    FrameworkParentFamily.DIRECT_MINIMAL_REPRESENTATION,
    FrameworkParentFamily.CANONICAL_DOMAIN_FRAMEWORK,
    FrameworkParentFamily.STRONGEST_RETRIEVED_ALTERNATIVE,
    FrameworkParentFamily.CURRENT_RAKL_COMPILED_FRAMEWORK,
)


def missing_framework_parents(
    registered: Iterable[FrameworkParentFamily],
) -> tuple[FrameworkParentFamily, ...]:
    """Minimum parent families not yet registered in the portfolio.

    ``SYNTHESIZED_CHALLENGER`` is not required: a synthesized framework is
    admissible only if the registered parents leave a residual, so its absence
    is not a gap.
    """

    present = set(registered)
    return tuple(parent for parent in _MINIMUM_FRAMEWORK_PARENTS if parent not in present)


@dataclass(frozen=True)
class AdequacyAssessment:
    """Noncompensatory adequacy verdict over a coordinate vector.

    Deliberately carries no scalar: a strong coordinate never compensates for a
    hard failure, and an unrated coordinate is an unrun check rather than a
    pass.  The assessment is proposal-side and grants nothing.
    """

    hard_failures: tuple[str, ...] = ()
    unrated: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def adequate(self) -> bool:
        return not self.hard_failures and not self.unrated

    @property
    def blocking_reason(self) -> str:
        if self.hard_failures:
            return f"noncompensatory failure: {list(self.hard_failures)}"
        if self.unrated:
            return f"unrated coordinates (unrun check, not a pass): {list(self.unrated)}"
        return ""


def _assess(coordinates: type[Enum], ratings: "Mapping[Enum, bool]") -> AdequacyAssessment:
    hard_failures = tuple(c.value for c in coordinates if ratings.get(c) is False)
    unrated = tuple(c.value for c in coordinates if c not in ratings)
    return AdequacyAssessment(hard_failures=hard_failures, unrated=unrated)


def assess_question_adequacy(
    ratings: "Mapping[QuestionAdequacyCoordinate, bool]",
) -> AdequacyAssessment:
    """Assess a question candidate over the nine adequacy coordinates."""

    return _assess(QuestionAdequacyCoordinate, ratings)


def assess_framework_adequacy(
    ratings: "Mapping[FrameworkAdequacyCoordinate, bool]",
) -> AdequacyAssessment:
    """Assess a framework candidate, for a target, over the ten coordinates."""

    return _assess(FrameworkAdequacyCoordinate, ratings)


__all__ = [
    "AdequacyAssessment",
    "AncestorChallenge",
    "AtomicityReceipt",
    "AtomicitySplitCondition",
    "AuditAction",
    "AuditCoordinate",
    "AuditNode",
    "AuditResidual",
    "AuditTrigger",
    "DecompositionCandidate",
    "DiscriminatorReceipt",
    "FrameworkAdequacyCoordinate",
    "FrameworkCandidate",
    "FrameworkParentFamily",
    "InterfaceContract",
    "NodeClosureAssessment",
    "NodeClosureTerminal",
    "OptionalAuditCandidate",
    "ProblemStatement",
    "QuestionAdequacyCoordinate",
    "QuestionFormulationCandidate",
    "RecursiveAuditDecision",
    "RecursiveAuditProjection",
    "SelfRaklEscalationRequest",
    "assess_bounded_node_closure",
    "assess_framework_adequacy",
    "assess_question_adequacy",
    "audit_after_material_residual",
    "audit_before_commit",
    "decide",
    "issue_atomicity_receipt",
    "mandatory_audit_triggered",
    "metacognitive_gap_candidates",
    "missing_framework_parents",
    "request_self_rakl_escalation",
    "select_optional_audit",
]
