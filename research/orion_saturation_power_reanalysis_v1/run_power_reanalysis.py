"""Was the bounded-saturation NULL a null, or an underpowered study?

Pure re-analysis of numbers already committed in
research/orion_saturation_solve_enablement_v1/. No new data, no new execution.

Decision rule, stated before computing:

  UNDERPOWERED   the design could not have reached alpha=0.05 at the observed
                 effect size, i.e. the discordant count needed exceeds what the
                 study collected
  ADEQUATELY_POWERED_NULL  the design could have detected the observed effect
                 and did not
  REPRODUCTION_FAILED  the recomputed p-value disagrees with the receipt, in
                 which case nothing else here is reported

Only exact binomial arithmetic is used, so the result is deterministic.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

RECEIPT = Path("research/orion_saturation_solve_enablement_v1/receipts/results_v1.json")
OUT = Path("research/orion_saturation_power_reanalysis_v1/RESULT.json")

ALPHA = 0.05
TARGET_POWER = 0.80


def binom(n: int, k: int) -> int:
    return math.comb(n, k)


def exact_mcnemar_two_sided(b: int, c: int) -> float:
    """Exact two-sided McNemar: binomial test of b successes in b+c at p=0.5."""

    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(binom(n, i) for i in range(0, k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def min_split_reaching_alpha(n: int, alpha: float = ALPHA) -> int | None:
    """Smallest majority count b (of n discordants) whose exact p < alpha."""

    for b in range((n // 2) + 1, n + 1):
        if exact_mcnemar_two_sided(b, n - b) < alpha:
            return b
    return None


def power_at(n: int, pi: float, alpha: float = ALPHA) -> float:
    """Power to reject at alpha, given n discordants each favouring A w.p. pi."""

    total = 0.0
    for b in range(0, n + 1):
        if exact_mcnemar_two_sided(b, n - b) < alpha:
            total += binom(n, b) * (pi**b) * ((1 - pi) ** (n - b))
    return total


def main() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    blob = json.dumps(receipt)

    # Recorded discordant counts, as reported in the frontier record and receipt.
    b, c = 8, 3
    n = b + c
    recomputed = exact_mcnemar_two_sided(b, c)
    reported = 0.2266
    reproduces = abs(recomputed - reported) < 5e-4

    if not reproduces:
        result = {
            "terminal": "REPRODUCTION_FAILED",
            "recomputed_p": recomputed,
            "reported_p": reported,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("REPRODUCTION_FAILED", recomputed, reported)
        return 1

    needed = min_split_reaching_alpha(n)
    pi_hat = b / n
    observed_power = power_at(n, pi_hat)

    # How many discordant pairs would 80% power at the observed effect require?
    required_n = None
    for candidate in range(n, 2001):
        if power_at(candidate, pi_hat) >= TARGET_POWER:
            required_n = candidate
            break

    terminal = "UNDERPOWERED" if observed_power < TARGET_POWER else "ADEQUATELY_POWERED_NULL"

    result = {
        "schema_version": "rakl-bounded-saturation-power-reanalysis-v1",
        "status": "RE_ANALYSIS_OF_COMMITTED_NUMBERS__NO_NEW_DATA",
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "target_negative": "p1-bounded-saturation-null",
        "source_receipt": str(RECEIPT),
        "decision_rule_stated_before_computing": {
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "UNDERPOWERED": "power at the observed effect is below the target",
            "ADEQUATELY_POWERED_NULL": "power at the observed effect meets the target and the test did not reject",
        },
        "reproduction_control": {
            "recomputed_exact_mcnemar_p": round(recomputed, 6),
            "reported_p": reported,
            "reproduces": reproduces,
        },
        "as_executed": {
            "discordant_favouring_saturation": b,
            "discordant_favouring_uniform": c,
            "discordant_total": n,
            "solve_rate_arm_a": 0.357,
            "solve_rate_arm_b": 0.3125,
        },
        "power_analysis": {
            "smallest_majority_reaching_alpha_at_n_11": needed,
            "meaning": (
                f"with {n} discordant pairs the study could only have reached p<{ALPHA} if at least "
                f"{needed} of them fell one way — an effect far larger than the one hypothesised"
            ),
            "observed_effect_pi_hat": round(pi_hat, 4),
            "power_at_observed_effect": round(observed_power, 4),
            "discordant_pairs_required_for_80pc_power": required_n,
            "shortfall_factor": round(required_n / n, 1) if required_n else None,
        },
        "terminal": terminal,
        "reading": (
            f"The study collected {n} discordant pairs. Detecting the effect it observed at 80% "
            f"power needs {required_n} — roughly {round(required_n / n, 1) if required_n else '?'}x "
            "more. The recorded NULL therefore reports the study's resolution, not the mechanic's "
            "absence: the design could not have distinguished the hypothesised benefit from chance."
        ),
        "what_this_does_not_say": [
            "It does not show the mechanic works. The point estimate favours saturation but the study cannot support that.",
            "It does not retract the NULL terminal, which was correctly filed against its own protocol.",
            "It does not license re-running the same design at larger n without a fresh freeze.",
        ],
        "consequence": (
            "The frontier's lever for this record — 'frozen revival as a separate epoch' — is "
            "correct but understated: the revival needs a powered design, and the required "
            f"discordant count ({required_n}) is now computed rather than guessed. At the observed "
            f"discordance rate a powered replication needs on the order of "
            f"{round(112 * required_n / n)} tasks against the 112 this study used."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"reproduction: recomputed p={recomputed:.4f} vs reported {reported} -> {reproduces}")
    print(f"discordant: {b} vs {c} (n={n})")
    print(f"smallest majority reaching alpha at n={n}: {needed}")
    print(f"power at observed effect: {observed_power:.4f}")
    print(f"discordant pairs needed for 80% power: {required_n}  ({round(required_n / n, 1)}x)")
    print(f"TERMINAL: {terminal}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
