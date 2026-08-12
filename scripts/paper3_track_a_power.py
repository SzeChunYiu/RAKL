#!/usr/bin/env python3
"""Reproduce the Paper III Track A sample-size table (refs #444, #248).

Every number in section 4 of ``research/paper3/PAPER3_TRACK_A_REGISTRATION_V1.md``
comes from here, so the registration's arithmetic is checkable rather than
asserted. Computes nothing about outcomes and reads no benchmark.

    python scripts/paper3_track_a_power.py
"""

from __future__ import annotations

import argparse
import json
import math

#: alpha = 0.05 two-sided, power = 0.80.
Z_ALPHA_HALF = 1.959963984540054
Z_POWER = 0.8416212335729143
K = (Z_ALPHA_HALF + Z_POWER) ** 2

#: Registered minimum detectable effect on paired Brier (#444).
MDE = 0.05

#: The figure inherited from the prior power study, recorded as an assumption.
INHERITED_N = 48


def required_n(sigma_d: float, mde: float = MDE) -> int:
    """Paired-difference sample size for a two-sided test at 80% power."""

    if sigma_d <= 0 or mde <= 0:
        raise ValueError("sigma_d and mde must be positive")
    return math.ceil(K * sigma_d**2 / mde**2)


def implied_sigma(n: int, mde: float = MDE) -> float:
    """The largest per-item difference SD for which ``n`` is adequate."""

    if n <= 0:
        raise ValueError("n must be positive")
    return math.sqrt(n * mde**2 / K)


def items_for_discriminating(target: int, q: float) -> int:
    """Total items needed to obtain ``target`` items on which the arms diverge.

    Items where both arms predict identically contribute ``d_i = 0``: they
    dilute the mean paired difference without adding information, so total
    count overstates power whenever ``q < 1``.
    """

    if not 0 < q <= 1:
        raise ValueError("q must be in (0, 1]")
    return math.ceil(target / q)


def build_report() -> dict[str, object]:
    sigmas = [0.10, round(implied_sigma(INHERITED_N), 4), 0.15, 0.20, 0.25, 0.30]
    fractions = [1.0, 0.5, 0.3, 0.188]
    return {
        "design": {
            "test": "paired difference, two-sided",
            "alpha": 0.05,
            "power": 0.80,
            "mde_paired_brier": MDE,
            "k_constant": round(K, 6),
        },
        "sample_size_by_sigma_d": [
            {"sigma_d": s, "required_n": required_n(s)} for s in sigmas
        ],
        "inherited_assumption": {
            "inherited_n": INHERITED_N,
            "adequate_only_if_sigma_d_at_most": round(implied_sigma(INHERITED_N), 4),
            "status": "UNVERIFIED_ASSUMPTION",
            "note": (
                "the prior ~n=48 figure was inherited, not derived here; it holds "
                "only under this sigma_d ceiling, which is tight for a paired "
                "Brier difference on binary outcomes"
            ),
        },
        "discriminating_fraction": {
            "definition": (
                "q = fraction of items on which the semantic and structural arms "
                "diverge; NOT the v2.1 decoupling rate, which compares the label "
                "to AND(witnesses) rather than one arm to another"
            ),
            "table": [
                {"q": q, "total_items_for_48_discriminating": items_for_discriminating(48, q)}
                for q in fractions
            ],
            "estimation_rule": (
                "q and sigma_d are estimated on a disjoint development set before "
                "the confirmatory set is generated and before any confirmatory "
                "outcome is accessed; n is then recomputed and recorded in an "
                "amendment"
            ),
        },
        "per_stratum_minima": {
            "min_items_per_family_x_item_type": 4,
            "min_discriminating_items_per_family": 4,
            "rationale": (
                "#449 found the matching_allocation family contributed zero "
                "decoupled items, making one leave-one-family-out fold "
                "uninformative by construction; a packet-level count hides that"
            ),
        },
        "claims": [],
        "grants_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="write the machine-readable report here")
    args = parser.parse_args()

    report = build_report()
    print("Paper III Track A — paired-difference sample size")
    print(f"  n = (z_a+z_b)^2 * sigma_d^2 / MDE^2   K={K:.4f}  MDE={MDE}")
    print("\n  sigma_d   required n")
    for row in report["sample_size_by_sigma_d"]:
        print(f"   {row['sigma_d']:.4f}   {row['required_n']:>6d}")

    inherited = report["inherited_assumption"]
    print(
        f"\n  n={INHERITED_N} is adequate ONLY IF sigma_d <= "
        f"{inherited['adequate_only_if_sigma_d_at_most']}  "
        f"[{inherited['status']}]"
    )

    print("\n  q       total items for 48 discriminating")
    for row in report["discriminating_fraction"]["table"]:
        print(f"   {row['q']:.3f}   {row['total_items_for_48_discriminating']:>5d}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
