"""Construct-independence admission gate — does an instrument read its own target?

The negative frontier's dominant failure shape is one instrument defect in eight
variants: the instrument reads something other than its target, because the
target signal and whatever generated or graded it share a channel or an author.
Eighteen of thirty-eight recorded terminals died that way — a template whose
renderer and extractor shared an author, an answer travelling alongside its own
input, gold computed from the candidate, a statistic that survived label
shuffling, a comparator that was an oracle rather than a weaker parent.

The programme already gates two other admissibility questions. Falsifiability
asks whether a gate *can* fail. ``instrument_admissibility`` asks whether it can
express an effect above the MDE. Neither asks whether the instrument reads its
target through an independent channel, and a census of registered designs found
that check written down in roughly a sixth of them — with author separation
declared by none.

This is that third gate. It is **pursuit-side**: an admissible instrument is one
whose construct claims are checkable, not one whose results are true. Admission
grants no authority, and refusing admission is not a scientific verdict about
the hypothesis under test.

Fail-closed by construction: an obligation that was not declared yields
``CANNOT_CHECK``, never a pass. An unrun check is an unrun check.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .recursive_framework_audit import AuditCoordinate, AuditNode, AuditResidual, RecursiveAuditDecision, decide


class ConstructObligation(str, Enum):
    """The four ways an instrument can be shown not to read its own construction."""

    CHANNEL_SEPARATION = "CHANNEL_SEPARATION"
    AUTHOR_SEPARATION = "AUTHOR_SEPARATION"
    GOLD_INDEPENDENCE = "GOLD_INDEPENDENCE"
    PERMUTATION_NULL = "PERMUTATION_NULL"


class ConstructVerdict(str, Enum):
    """Admission verdicts.  None is a scientific judgement about the hypothesis."""

    ADMISSIBLE = "ADMISSIBLE"
    INADMISSIBLE = "INADMISSIBLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class PermutationNullWitness:
    """Evidence that the reported statistic dies when the labels are shuffled.

    The failure this encodes is concrete: two reducer batteries on this
    programme's frontier reported statistics built from label-independent
    marginals, which survived gold shuffling and therefore measured band
    similarity rather than correspondence.

    ``chance_level`` is the value the statistic takes when the labels carry no
    information — 0.5 for a two-alternative forced choice, 0.0 for a centred
    advantage. ``tolerance`` is how far the shuffled statistic may sit from it
    before the instrument is judged to be reading something other than the
    labels.
    """

    statistic_id: str
    observed: float
    shuffled_mean: float
    chance_level: float
    tolerance: float = 0.02
    permutations: int = 0

    def __post_init__(self) -> None:
        if self.permutations <= 0:
            raise ValueError("a permutation witness must record how many permutations were run")
        if self.tolerance < 0:
            raise ValueError("tolerance cannot be negative")

    @property
    def survives_shuffling(self) -> bool:
        """True when the shuffled statistic stays away from chance — a defect."""

        return abs(self.shuffled_mean - self.chance_level) > self.tolerance

    @property
    def separates_from_null(self) -> bool:
        """True when the observed statistic is distinguishable from its own null."""

        return abs(self.observed - self.shuffled_mean) > self.tolerance


@dataclass(frozen=True)
class ObligationDeclaration:
    """One obligation, as declared in the instrument's frozen design.

    ``satisfied`` is the design's own claim. It is not taken on trust for
    ``PERMUTATION_NULL``, which additionally requires a witness.
    """

    obligation: ConstructObligation
    satisfied: bool
    evidence: str = ""
    witness: PermutationNullWitness | None = None

    def __post_init__(self) -> None:
        if self.satisfied and not self.evidence:
            raise ValueError(
                f"{self.obligation.value} claims satisfaction without evidence; "
                "an undocumented claim is not a declaration"
            )


@dataclass(frozen=True)
class InstrumentDesign:
    """A frozen instrument design presented for admission, before its epoch is spent."""

    instrument_id: str
    declarations: tuple[ObligationDeclaration, ...] = ()
    observation_contract_digest: str = ""

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise ValueError("an instrument design requires an id")
        seen = [d.obligation for d in self.declarations]
        if len(set(seen)) != len(seen):
            raise ValueError("each obligation may be declared at most once")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    def declaration_for(self, obligation: ConstructObligation) -> ObligationDeclaration | None:
        for declaration in self.declarations:
            if declaration.obligation is obligation:
                return declaration
        return None


@dataclass(frozen=True)
class ConstructIndependenceDecision:
    """Admission verdict plus exactly why, carrying no authority."""

    instrument_id: str
    verdict: ConstructVerdict
    undeclared: tuple[str, ...] = ()
    violated: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def admissible(self) -> bool:
        return self.verdict is ConstructVerdict.ADMISSIBLE


def assess_construct_independence(design: InstrumentDesign) -> ConstructIndependenceDecision:
    """Decide whether an instrument may be spent.

    Order is fail-closed and deliberate. A *violated* obligation outranks a
    missing one: an instrument shown to read its own construction is
    inadmissible whether or not its other checks were run, and reporting it as
    merely unchecked would understate what is known.
    """

    undeclared: list[str] = []
    violated: list[str] = []
    reasons: list[str] = []

    for obligation in ConstructObligation:
        declaration = design.declaration_for(obligation)
        if declaration is None:
            undeclared.append(obligation.value)
            continue
        if not declaration.satisfied:
            violated.append(obligation.value)
            reasons.append(f"{obligation.value} declared unsatisfied: {declaration.evidence or 'no detail'}")
            continue
        if obligation is ConstructObligation.PERMUTATION_NULL:
            witness = declaration.witness
            if witness is None:
                undeclared.append(obligation.value)
                reasons.append("PERMUTATION_NULL claims satisfaction with no witness; treated as unrun")
                continue
            if witness.survives_shuffling:
                violated.append(obligation.value)
                reasons.append(
                    f"statistic {witness.statistic_id!r} survives label shuffling "
                    f"(shuffled {witness.shuffled_mean} vs chance {witness.chance_level}); "
                    "it is reading something other than the labels"
                )
            elif not witness.separates_from_null:
                violated.append(obligation.value)
                reasons.append(
                    f"statistic {witness.statistic_id!r} is indistinguishable from its own null; "
                    "the instrument cannot express the effect it reports"
                )

    if violated:
        return ConstructIndependenceDecision(
            design.instrument_id,
            ConstructVerdict.INADMISSIBLE,
            tuple(undeclared),
            tuple(violated),
            tuple(reasons),
        )
    if undeclared:
        return ConstructIndependenceDecision(
            design.instrument_id,
            ConstructVerdict.CANNOT_CHECK,
            tuple(undeclared),
            (),
            tuple(reasons) + (f"undeclared obligations are unrun checks, not passes: {undeclared}",),
        )
    return ConstructIndependenceDecision(
        design.instrument_id,
        ConstructVerdict.ADMISSIBLE,
        (),
        (),
        ("every construct-independence obligation is declared and witnessed",),
    )


# ---------------------------------------------------------------------------
# Integration with the recursive framework audit
# ---------------------------------------------------------------------------


def to_audit_residual(decision: ConstructIndependenceDecision) -> AuditResidual:
    """Project an admission verdict into the recursive audit's residual type.

    An inadmissible instrument is a MEASUREMENT defect: the observation operator
    does not measure the target. An unchecked one is a resource bound, because
    the audit did not run rather than failing.
    """

    if decision.verdict is ConstructVerdict.INADMISSIBLE:
        return AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,))
    if decision.verdict is ConstructVerdict.CANNOT_CHECK:
        return AuditResidual(resource_bound=True)
    return AuditResidual()


def decide_from_construct_verdict(
    decision: ConstructIndependenceDecision,
    *,
    closure_coordinates_pass: bool = False,
    material_open_residual: bool = True,
) -> RecursiveAuditDecision:
    """Run the frozen decision chain on an admission verdict.

    No second chain is introduced: the gate only builds the residual the
    existing ``decide`` already accepts, so admission inherits the frozen
    priority ordering.
    """

    node = AuditNode(
        closure_coordinates_pass=closure_coordinates_pass,
        material_open_residual=material_open_residual,
    )
    return decide(node, to_audit_residual(decision))


__all__ = [
    "ConstructIndependenceDecision",
    "ConstructObligation",
    "ConstructVerdict",
    "InstrumentDesign",
    "ObligationDeclaration",
    "PermutationNullWitness",
    "assess_construct_independence",
    "decide_from_construct_verdict",
    "to_audit_residual",
]
