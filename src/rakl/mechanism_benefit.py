"""Does the mechanism actually buy anything?

Papers I–V establish that ORION's mechanics are *sound*: authority does not
escalate, saturation is well defined, refusals are fail-closed. Soundness is not
benefit. A system that refuses everything satisfies every non-interference
theorem in the programme and is useless.

That gap is not hypothetical. It showed up twice already:

* In the Lean development, non-escalation is satisfied by a system that never
  updates anything, which is why ``certified_operator_may_change_canon`` had to be
  added as a non-vacuity witness.
* In the Paper VI scoped-utility packet, the headline benefit claim ("executing
  the gate contract cuts false promotion 3.31x") was self-retracted as
  tautological: the contrast arm read the same gate observations in which the
  defect was planted, so it admitted an unsound candidate exactly when the gate's
  evidence was unavailable. The closed-form prediction matched the "measurement"
  to three decimals.

This module makes the distinction enforceable. A mechanic may claim
BENEFIT_DEMONSTRATED only when its outcome measure is independent of the
mechanism being credited. Anything else is a soundness result, a cost result, or a
tautology — all legitimate, none a benefit.

Proposal-only. Nothing here grants scientific or promotion authority, and a
BENEFIT_DEMONSTRATED verdict records that a claim is *structurally eligible* to be
a benefit claim, never that the effect is real.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
import json

_REPO = Path(__file__).resolve().parents[2]
LEDGER_PATH = _REPO / "research" / "mechanism_benefit_ledger" / "ledger.json"


class SoundnessStatus(str, Enum):
    MECHANIZED = "MECHANIZED"
    PROVED_ON_PAPER = "PROVED_ON_PAPER"
    ASSERTED = "ASSERTED"
    NOT_ESTABLISHED = "NOT_ESTABLISHED"


class BenefitStatus(str, Enum):
    #: Beats a matched ablation on an outcome the mechanism does not define.
    DEMONSTRATED = "DEMONSTRATED"
    #: Ran, and the mechanism did not help (or lost).
    REFUTED = "REFUTED"
    #: The contrast is determined by the mechanism's own definitions.
    CIRCULAR = "CIRCULAR"
    #: A cost or operating-regime constraint, not a benefit.
    COST_ONLY = "COST_ONLY"
    #: Not attempted, or attempted and blocked.
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class OutcomeProvenance(str, Enum):
    #: Measured by something outside the ORION apparatus entirely.
    EXTERNAL = "EXTERNAL"
    #: Inside the repo but demonstrably not defined by the mechanism under test.
    INDEPENDENT_OF_MECHANISM = "INDEPENDENT_OF_MECHANISM"
    #: Defined by the same artifact as the mechanism. Cannot support a benefit claim.
    SELF_AUTHORED = "SELF_AUTHORED"
    UNKNOWN = "UNKNOWN"


#: Only these provenances can carry a benefit claim. SELF_AUTHORED is precisely the
#: Paper VI retraction pattern and is never sufficient.
BENEFIT_ELIGIBLE_PROVENANCE = frozenset(
    {OutcomeProvenance.EXTERNAL, OutcomeProvenance.INDEPENDENT_OF_MECHANISM}
)


class LedgerError(RuntimeError):
    """Raised when the ledger claims more than its own fields support."""


@dataclass(frozen=True)
class MechanicRow:
    mechanic_id: str
    paper: str
    soundness: SoundnessStatus
    benefit: BenefitStatus
    outcome_provenance: OutcomeProvenance
    ablation_arm: str | None
    non_vacuity_witness: str | None
    detail: str

    @property
    def benefit_claim_is_structurally_eligible(self) -> bool:
        """Whether this row is *allowed* to assert a benefit, before asking if it did."""
        return (
            self.outcome_provenance in BENEFIT_ELIGIBLE_PROVENANCE
            and self.ablation_arm is not None
        )


def load_ledger(path: Path | None = None) -> dict[str, Any]:
    with (path or LEDGER_PATH).open(encoding="utf-8") as handle:
        return json.load(handle)


def rows(ledger: dict[str, Any] | None = None) -> tuple[MechanicRow, ...]:
    payload = ledger if ledger is not None else load_ledger()
    out: list[MechanicRow] = []
    for entry in payload["mechanics"]:
        out.append(
            MechanicRow(
                mechanic_id=entry["mechanic_id"],
                paper=entry["paper"],
                soundness=SoundnessStatus(entry["soundness"]),
                benefit=BenefitStatus(entry["benefit"]),
                outcome_provenance=OutcomeProvenance(entry["outcome_provenance"]),
                ablation_arm=entry.get("ablation_arm"),
                non_vacuity_witness=entry.get("non_vacuity_witness"),
                detail=entry.get("detail", ""),
            )
        )
    return tuple(out)


def integrity_problems(ledger: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Ways the ledger could claim more than it has earned.

    These are not stylistic. Each corresponds to a mistake already made once in
    this programme.
    """
    problems: list[str] = []
    for row in rows(ledger):
        # The Paper VI retraction pattern: a benefit credited to a mechanism whose
        # own definitions determine the outcome.
        if row.benefit is BenefitStatus.DEMONSTRATED and not row.benefit_claim_is_structurally_eligible:
            problems.append(
                f"{row.mechanic_id}: claims DEMONSTRATED but outcome_provenance="
                f"{row.outcome_provenance.value} / ablation_arm={row.ablation_arm!r}; "
                "a benefit needs a matched ablation and an outcome the mechanism does not define"
            )
        # A sound mechanic that provably never acts is vacuously sound.
        if row.soundness is SoundnessStatus.MECHANIZED and row.non_vacuity_witness is None:
            problems.append(
                f"{row.mechanic_id}: MECHANIZED with no non-vacuity witness; a "
                "non-interference result is satisfied by a system that never acts"
            )
        # A cost is not a benefit, however good the arithmetic.
        if row.benefit is BenefitStatus.COST_ONLY and row.outcome_provenance is OutcomeProvenance.UNKNOWN:
            problems.append(
                f"{row.mechanic_id}: COST_ONLY with UNKNOWN provenance; name what "
                "anchors the cost or the number is unfalsifiable"
            )
    return tuple(problems)


def programme_summary(ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    """The headline the capstone needs: how much of ORION is shown to *help*."""
    all_rows = rows(ledger)
    demonstrated = [r for r in all_rows if r.benefit is BenefitStatus.DEMONSTRATED]
    return {
        "mechanics_total": len(all_rows),
        "soundness_mechanized": sum(1 for r in all_rows if r.soundness is SoundnessStatus.MECHANIZED),
        "benefit_demonstrated": len(demonstrated),
        "benefit_circular": sum(1 for r in all_rows if r.benefit is BenefitStatus.CIRCULAR),
        "benefit_cost_only": sum(1 for r in all_rows if r.benefit is BenefitStatus.COST_ONLY),
        "benefit_refuted": sum(1 for r in all_rows if r.benefit is BenefitStatus.REFUTED),
        "benefit_not_attempted": sum(1 for r in all_rows if r.benefit is BenefitStatus.NOT_ATTEMPTED),
        "supports_working_mechanism_claim": bool(demonstrated),
        "demonstrated_ids": [r.mechanic_id for r in demonstrated],
    }


def main() -> int:  # pragma: no cover - thin CLI
    ledger = load_ledger()
    for row in rows(ledger):
        print(f"{row.benefit.value:<16} {row.soundness.value:<18} {row.paper:<10} {row.mechanic_id}")
    problems = integrity_problems(ledger)
    summary = programme_summary(ledger)
    print()
    print(json.dumps(summary, indent=2))
    if problems:
        print("\nINTEGRITY PROBLEMS:")
        for item in problems:
            print(f"  - {item}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
