"""Repaired probes for the transfer-instrument falsifiability battery.

The battery of Paper II asks, of every instrument, whether it *could* have
failed. This module holds a repair to one of its probes, and the repair exists
because the probe was measured firing on an instrument that has no defect.

**The B3 confound.** B3 shuffles the gold labels and re-runs the primary paired
statistic; the instrument is declared non-probative if the statistic still
clears the minimum detectable effect. The intent is a negative control on label
leakage. Under the frozen scoring map it does not measure that.

Write the map as ``p(ACCEPT)=0.98``, ``p(REJECT)=0.02``, ``p(CANNOT_CHECK)=0.5``.
Take the shuffle to preserve the 50/50 class balance, which the ARN pair
construction guarantees per row: every row contributes exactly one gold-ACCEPT
and one gold-REJECT pair, so any permutation of the gold column leaves the
balance exact. Then for a pair on which an arm answers ACCEPT, the gold it is
scored against is ACCEPT or REJECT with probability 1/2 each:

    E[Brier | answered ACCEPT] = 0.5*(0.98-1)^2 + 0.5*(0.98-0)^2 = 0.4804

and for a pair on which it answers REJECT:

    E[Brier | answered REJECT] = 0.5*(0.02-1)^2 + 0.5*(0.02-0)^2 = 0.4804

The two are equal, so an arm that is decisive on a fraction ``1-r`` of pairs and
abstains on the rest has, whatever its accept rate and whatever its accuracy,

    E[Brier | shuffled gold] = (1-r)*0.4804 + r*0.25 = 0.4804 - 0.2304*r

because ``(0.5-1)^2 = (0.5-0)^2 = 0.25``. The B3 statistic, being the control's
mean Brier minus the witness's, therefore has expectation

    E[B3 advantage] = 0.2304 * (r_witness - r_control)

plus sampling noise from the single realized shuffle. It is a measurement of
*differential abstention*. It is neither sound nor complete for label leakage: an
arm with provably zero label dependence fails B3 by abstaining often enough, and
a leak smaller than ``0.2304*(r_w - r_c)`` is masked by the abstention term.

**The repair.** Restrict the paired statistic to the pairs on which both arms
are decisive. The abstention term vanishes identically, because on those pairs
no arm contributes the 0.25 constant, while a leaking arm keeps leaking on every
pair it answers, so the leak signal is untouched. Both halves are checked
two-sided in ``tests/test_b3_abstention_confound.py``: a no-leak arm swept over
abstention rates must clear the repaired probe at every rate, and a planted leak
must still fire it.

The repair narrows the probe's population; it does not lower its threshold. When
both arms are decisive everywhere the repaired probe is numerically identical to
the original, which is the degenerate case the tests assert first.

Proposal-only. This module grants no scientific authority: it reports a
measurement and a verdict, and a verdict here licenses reading an instrument's
outcome, never the outcome itself.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

#: The frozen scoring map of the external-corpus protocol. Duplicated here as a
#: default rather than imported so that a change to a runner cannot silently
#: change the probe; a caller with a different map must pass it explicitly.
BINARY_P: dict[str, float] = {"ACCEPT": 0.98, "REJECT": 0.02, "CANNOT_CHECK": 0.5}

ABSTAIN = "CANNOT_CHECK"


@dataclass(frozen=True)
class B3Report:
    """Outcome of the repaired shuffled-gold negative control.

    ``fires`` is True when the instrument is declared NOT probative, matching the
    orientation of the registered battery: B3 is a control that must *fail*.
    """

    advantage: float
    n_scored: int
    n_total: int
    fires: bool
    abstention_witness: float
    abstention_control: float
    predicted_confound: float
    reasons: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def brier(decision: str, gold: str, scoring: dict[str, float] = BINARY_P) -> float:
    if decision not in scoring:
        raise KeyError(f"decision {decision!r} is not in the scoring map")
    y = 1.0 if gold == "ACCEPT" else 0.0
    return (scoring[decision] - y) ** 2


def paired_advantage(
    control: Sequence[str],
    witness: Sequence[str],
    golds: Sequence[str],
    scoring: dict[str, float] = BINARY_P,
) -> float:
    """Mean control Brier minus mean witness Brier, over every supplied pair."""
    if not (len(control) == len(witness) == len(golds)):
        raise ValueError("control, witness and golds must be the same length")
    if not golds:
        raise ValueError("no pairs supplied; an unexercised probe is unaudited")
    n = len(golds)
    c = sum(brier(d, g, scoring) for d, g in zip(control, golds)) / n
    w = sum(brier(d, g, scoring) for d, g in zip(witness, golds)) / n
    return c - w


def abstention_confound(
    r_witness: float, r_control: float, scoring: dict[str, float] = BINARY_P
) -> float:
    """The expected B3 advantage attributable to differential abstention alone.

    Derived above: ``(E[Brier | decisive] - E[Brier | abstain]) * (r_w - r_c)``,
    with both expectations taken under a balanced shuffle.
    """
    decisive = 0.5 * (scoring["ACCEPT"] - 1.0) ** 2 + 0.5 * (scoring["ACCEPT"] - 0.0) ** 2
    abstain = 0.5 * (scoring[ABSTAIN] - 1.0) ** 2 + 0.5 * (scoring[ABSTAIN] - 0.0) ** 2
    return (decisive - abstain) * (r_witness - r_control)


def b3_prime(
    control: Sequence[str],
    witness: Sequence[str],
    shuffled_golds: Sequence[str],
    *,
    mde: float,
    scoring: dict[str, float] = BINARY_P,
) -> B3Report:
    """The repaired shuffled-gold negative control.

    Scores only the pairs on which both arms are decisive, which removes the
    abstention term identically while leaving any label dependence intact.

    Fail-closed: if no pair is jointly decisive the probe cannot be evaluated and
    reports ``fires=True`` with a CANNOT_CHECK reason, because an instrument that
    abstains everywhere has not been shown capable of failing.
    """
    if not (len(control) == len(witness) == len(shuffled_golds)):
        raise ValueError("control, witness and golds must be the same length")
    n_total = len(shuffled_golds)
    if n_total == 0:
        raise ValueError("no pairs supplied; an unexercised probe is unaudited")

    r_w = sum(1 for d in witness if d == ABSTAIN) / n_total
    r_c = sum(1 for d in control if d == ABSTAIN) / n_total
    predicted = abstention_confound(r_w, r_c, scoring)

    keep = [
        i
        for i in range(n_total)
        if witness[i] != ABSTAIN and control[i] != ABSTAIN
    ]
    if not keep:
        return B3Report(
            advantage=float("nan"),
            n_scored=0,
            n_total=n_total,
            fires=True,
            abstention_witness=r_w,
            abstention_control=r_c,
            predicted_confound=predicted,
            reasons=(
                "CANNOT_CHECK: no pair is decisive in both arms, so the negative "
                "control has no population; an instrument that abstains "
                "everywhere has not been shown capable of failing",
            ),
        )

    advantage = paired_advantage(
        [control[i] for i in keep],
        [witness[i] for i in keep],
        [shuffled_golds[i] for i in keep],
        scoring,
    )
    return B3Report(
        advantage=advantage,
        n_scored=len(keep),
        n_total=n_total,
        fires=advantage >= mde,
        abstention_witness=r_w,
        abstention_control=r_c,
        predicted_confound=predicted,
    )
