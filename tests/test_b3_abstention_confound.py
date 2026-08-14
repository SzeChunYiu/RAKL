"""Known-answer tests for the B3 shuffled-gold confound and its repair.

Two-sided by construction. A probe that only ever alarms is not validated by an
alarm, so the no-alarm case is asserted first and at every swept rate:

  * an arm with provably zero label dependence must never fire the repaired
    probe, however often it abstains -- and must fire the original probe once it
    abstains enough, which is the defect being demonstrated;
  * a planted leak must fire both probes, including when it is accompanied by
    heavy abstention, because a repair that loses the leak is a different bug.

The arms are deterministic functions of a hash, so no seed management is needed
and the known answers are exact under re-execution.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from rakl.battery_probes import (
    ABSTAIN,
    abstention_confound,
    b3_prime,
    paired_advantage,
)

MDE = 0.05
N = 1542  # the executed CONFIRM size of the ARN epoch


def _u(*parts: str) -> tuple[float, int]:
    h = hashlib.sha256("|".join(parts).encode()).digest()
    return int.from_bytes(h[:8], "big") / 2**64, h[8]


def _golds() -> list[str]:
    """Balanced gold, as the ARN pair construction guarantees per row."""
    return ["ACCEPT" if i % 2 == 0 else "REJECT" for i in range(N)]


def _shuffled(golds: list[str], seed: int = 20260815) -> list[str]:
    out = list(golds)
    random.Random(seed).shuffle(out)
    return out


def _never_abstains() -> list[str]:
    """Stand-in for the frozen band control: decisive on every pair."""
    return ["ACCEPT" if _u("control", str(i))[1] % 2 else "REJECT" for i in range(N)]


def _no_leak_arm(r: float) -> list[str]:
    """Zero label dependence: the decision is a hash of the pair identity only.

    It cannot read gold because gold is never an input.
    """
    out = []
    for i in range(N):
        u, byte = _u("arm", str(i))
        out.append(ABSTAIN if u < r else ("ACCEPT" if byte % 2 else "REJECT"))
    return out


def _leaky_arm(q: float, handed_gold: list[str], r: float = 0.0) -> list[str]:
    """Copies the gold field it is handed with probability q; abstains at rate r."""
    out = []
    for i in range(N):
        u, byte = _u("leak", str(i))
        if u < r:
            out.append(ABSTAIN)
        elif u < r + q * (1.0 - r):
            out.append(handed_gold[i])
        else:
            out.append("ACCEPT" if byte % 2 else "REJECT")
    return out


def test_decisive_expected_brier_is_accept_rate_independent():
    """The constant the whole derivation rests on, asserted directly."""
    assert abstention_confound(0.0, 0.0) == 0.0
    # 0.4804 - 0.25, exact in binary floating point to within a rounding step.
    assert abstention_confound(1.0, 0.0) == pytest.approx(0.2304, abs=1e-12)
    assert abstention_confound(0.3, 0.3) == 0.0
    assert abstention_confound(0.4, 0.1) == pytest.approx(0.2304 * 0.3, abs=1e-12)


@pytest.mark.parametrize("r", [0.0, 0.1, 0.2, 0.4, 0.6])
def test_no_leak_arm_tracks_the_confound_and_survives_the_repair(r):
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()
    witness = _no_leak_arm(r)

    original = paired_advantage(control, witness, shuffled)
    assert original == pytest.approx(abstention_confound(r, 0.0), abs=0.02), (
        "the original B3 statistic should track 0.2304*r on an arm that cannot "
        "read gold at all"
    )

    report = b3_prime(control, witness, shuffled, mde=MDE)
    assert not report.fires, (
        f"the repaired probe alarmed at abstention rate {r} on an arm with "
        "provably zero label dependence"
    )
    assert abs(report.advantage) < MDE
    assert report.abstention_witness == pytest.approx(r, abs=0.03)


def test_original_probe_false_alarms_on_heavy_abstention():
    """The defect itself: no leak, yet B3 declares the instrument non-probative."""
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()

    quiet = paired_advantage(control, _no_leak_arm(0.1), shuffled)
    assert quiet < MDE, "control assertion: B3 must be silent at low abstention"

    for r in (0.4, 0.6):
        loud = paired_advantage(control, _no_leak_arm(r), shuffled)
        assert loud >= MDE, (
            f"expected the documented false alarm at abstention rate {r}"
        )


@pytest.mark.parametrize("q", [0.3, 0.6, 1.0])
def test_planted_leak_still_fires_the_repaired_probe(q):
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()
    witness = _leaky_arm(q, shuffled)

    report = b3_prime(control, witness, shuffled, mde=MDE)
    assert report.fires, f"the repair lost a planted leak at q={q}"
    assert report.n_scored == N, "no abstention was planted, so nothing may be dropped"


@pytest.mark.parametrize("q,r", [(0.6, 0.4), (0.3, 0.6)])
def test_leak_masked_by_abstention_still_fires_the_repaired_probe(q, r):
    """The hard case: a leak accompanied by the abstention that confounds B3."""
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()
    witness = _leaky_arm(q, shuffled, r)

    report = b3_prime(control, witness, shuffled, mde=MDE)
    assert report.fires, f"the repair lost a leak masked by abstention (q={q}, r={r})"
    assert report.n_scored < N


def test_repair_is_identity_when_no_arm_abstains():
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()
    witness = _no_leak_arm(0.0)

    assert b3_prime(control, witness, shuffled, mde=MDE).advantage == pytest.approx(
        paired_advantage(control, witness, shuffled)
    )


def test_total_abstention_is_cannot_check_not_a_pass():
    golds = _golds()
    shuffled = _shuffled(golds)
    control = _never_abstains()
    report = b3_prime(control, [ABSTAIN] * N, shuffled, mde=MDE)
    assert report.fires, "an arm that abstains everywhere must not pass by absence"
    assert report.n_scored == 0
    assert report.reasons and "CANNOT_CHECK" in report.reasons[0]
