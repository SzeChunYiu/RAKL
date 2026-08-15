"""The loop an operator actually runs — one step of governed research.

Every mechanic in this repository has been reachable only by hand-writing a
script around it. The verifiability audit found exactly one with a caller
outside its own tests, and three instruments built in one session failed the
same way: a predicate frozen before anyone characterised the population's
support for it.

This composes what already exists into a single step an operator can run, and
adds the one precondition those failures identified:

    support is declared BEFORE a revision action is licensed

The step is otherwise a thin composition. It introduces no new decision chain,
no authority, and no verdict the underlying mechanics do not already produce:

    recursive_framework_audit.decide   which pursuit coordinate is responsible
    observation_contract               what information the question licenses
    construct_independence             whether a proposed instrument may be spent

What it adds is the ordering. `decide` will happily return `SPLIT` for a
population that cannot express the effect; this refuses to pass that on until
support is on the record, because an honest action against an uncharacterised
population is how three frozen instruments produced nothing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum

from .construct_independence import (
    ConstructIndependenceDecision,
    ConstructVerdict,
)
from .recursive_framework_audit import (
    AuditAction,
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    decide,
)


class SupportVerdict(str, Enum):
    """Whether the population can express what the step proposes to measure."""

    DECLARED = "DECLARED"
    UNDECLARED = "UNDECLARED"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


@dataclass(frozen=True)
class SupportDeclaration:
    """What must be on the record before a revision action is licensed.

    The four fields are the ones whose absence produced this session's three
    self-refuting instruments: an uncharacterised population, a predicate
    outside its domain, an unlisted conditioning variable that cancelled the
    aggregate, and an unstated ceiling.
    """

    population: str = ""
    predicate_in_domain: bool | None = None
    conditioning_variables: tuple[str, ...] = ()
    reachable_ceiling: float | None = None
    ceiling_basis: str = ""
    registered_gate: float | None = None

    @property
    def ceiling_below_gate(self) -> bool:
        """True when the best attainable result cannot clear the registered gate.

        Recorded because p4-adaptive-lost-to-static carried a tier-3 rigorous
        ceiling of 0.0246 against its own frozen 0.05 hard gate: no repair to the
        allocation policy changes a ceiling, so every action on that instrument
        is unable to clear it.
        """

        if self.reachable_ceiling is None or self.registered_gate is None:
            return False
        return self.reachable_ceiling < self.registered_gate

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    def verdict(self) -> SupportVerdict:
        if self.predicate_in_domain is False:
            return SupportVerdict.OUT_OF_DOMAIN
        if not self.population or self.predicate_in_domain is None:
            return SupportVerdict.UNDECLARED
        if self.reachable_ceiling is None or not self.ceiling_basis:
            return SupportVerdict.UNDECLARED
        return SupportVerdict.DECLARED

    def missing(self) -> tuple[str, ...]:
        gaps = []
        if not self.population:
            gaps.append("population")
        if self.predicate_in_domain is None:
            gaps.append("predicate_in_domain")
        if self.reachable_ceiling is None:
            gaps.append("reachable_ceiling")
        if not self.ceiling_basis:
            gaps.append("ceiling_basis")
        return tuple(gaps)


# Actions that change the pursuit object. These are the ones support gates.
REVISION_ACTIONS: frozenset[AuditAction] = frozenset(
    {
        AuditAction.REFRAME_QUESTION,
        AuditAction.CHALLENGE_FRAMEWORK,
        AuditAction.SPLIT,
        AuditAction.MERGE,
        AuditAction.REPAIR_INTERFACE,
        AuditAction.REVISE_MEASUREMENT,
        AuditAction.ASCEND,
    }
)


@dataclass(frozen=True)
class SessionStep:
    """One governed step: what to do next, and everything that gated it."""

    target_id: str
    proposed_action: AuditAction
    licensed_action: AuditAction
    coordinates: tuple[AuditCoordinate, ...] = ()
    support: SupportVerdict = SupportVerdict.UNDECLARED
    support_gaps: tuple[str, ...] = ()
    instrument_verdict: ConstructVerdict | None = None
    reasons: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    @property
    def blocked(self) -> bool:
        return self.licensed_action is not self.proposed_action

    def digest(self) -> str:
        payload = json.dumps(
            {
                "target_id": self.target_id,
                "proposed": self.proposed_action.value,
                "licensed": self.licensed_action.value,
                "coordinates": [c.value for c in self.coordinates],
                "support": self.support.value,
                "support_gaps": list(self.support_gaps),
                "instrument": self.instrument_verdict.value if self.instrument_verdict else None,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def next_step(
    *,
    target_id: str,
    node: AuditNode,
    residual: AuditResidual,
    support: SupportDeclaration | None = None,
    instrument: ConstructIndependenceDecision | None = None,
) -> SessionStep:
    """Decide the next licensed action for one target.

    Order, and why:

    1. ``decide`` proposes. The frozen chain is untouched and still owns the
       question of which coordinate is responsible.
    2. If the proposal is a revision, support must be declared. An undeclared
       population downgrades to ``CANNOT_CHECK`` — the audit did not run, it was
       never runnable.
    3. If an instrument is offered, an inadmissible one downgrades to
       ``REVISE_MEASUREMENT`` and an unchecked one to ``CANNOT_CHECK``. Spending
       an instrument that reads its own construction is the defect this
       repository has recorded eighteen times.

    Nothing here promotes: every downgrade is toward abstention, never toward a
    stronger claim.
    """

    proposed = decide(node, residual)
    reasons = list(proposed.reasons)
    licensed = proposed.action

    support = support or SupportDeclaration()
    support_verdict = support.verdict()

    # Out of domain blocks everything, not only revisions. Solving at the current
    # representation on a population that cannot express the predicate is exactly
    # the L4 tight-floor record: both arms score zero, forever, by construction.
    if support_verdict is SupportVerdict.OUT_OF_DOMAIN:
        licensed = AuditAction.CANNOT_CHECK
        reasons.append(
            "predicate is outside the population's domain: no action on this population "
            "produces evidence"
        )
    elif support.ceiling_below_gate:
        licensed = AuditAction.CANNOT_CHECK
        reasons.append(
            f"reachable ceiling {support.reachable_ceiling} is below the registered gate "
            f"{support.registered_gate}: no action on this instrument can clear it"
        )
    elif proposed.action in REVISION_ACTIONS:
        if support_verdict is SupportVerdict.UNDECLARED:
            licensed = AuditAction.CANNOT_CHECK
            reasons.append(
                "support undeclared "
                f"({', '.join(support.missing())}): a revision against an uncharacterised "
                "population is an unrun check, not a step"
            )

    if instrument is not None and licensed is not AuditAction.CANNOT_CHECK:
        if instrument.verdict is ConstructVerdict.INADMISSIBLE:
            licensed = AuditAction.REVISE_MEASUREMENT
            reasons.append(
                f"instrument {instrument.instrument_id!r} is inadmissible: "
                f"{', '.join(instrument.violated) or 'construct dependence'}"
            )
        elif instrument.verdict is ConstructVerdict.CANNOT_CHECK:
            licensed = AuditAction.CANNOT_CHECK
            reasons.append(
                f"instrument {instrument.instrument_id!r} has undeclared construct "
                f"obligations ({', '.join(instrument.undeclared)}): an unrun check is not a pass"
            )

    return SessionStep(
        target_id=target_id,
        proposed_action=proposed.action,
        licensed_action=licensed,
        coordinates=proposed.coordinates,
        support=support_verdict,
        support_gaps=support.missing(),
        instrument_verdict=instrument.verdict if instrument else None,
        reasons=tuple(reasons),
    )


@dataclass(frozen=True)
class SessionLedger:
    """Append-only record of the steps taken against one target."""

    target_id: str
    steps: tuple[SessionStep, ...] = field(default_factory=tuple)

    def with_step(self, step: SessionStep) -> "SessionLedger":
        if step.target_id != self.target_id:
            raise ValueError(
                f"step targets {step.target_id!r}, ledger targets {self.target_id!r}"
            )
        return SessionLedger(self.target_id, self.steps + (step,))

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def blocked_steps(self) -> tuple[SessionStep, ...]:
        return tuple(s for s in self.steps if s.blocked)

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "steps": [
                {
                    "proposed": s.proposed_action.value,
                    "licensed": s.licensed_action.value,
                    "support": s.support.value,
                    "support_gaps": list(s.support_gaps),
                    "instrument": s.instrument_verdict.value if s.instrument_verdict else None,
                    "blocked": s.blocked,
                    "digest": s.digest(),
                    "reasons": list(s.reasons),
                }
                for s in self.steps
            ],
            "grants_scientific_authority": False,
        }


__all__ = [
    "REVISION_ACTIONS",
    "SessionLedger",
    "SessionStep",
    "SupportDeclaration",
    "SupportVerdict",
    "next_step",
]
