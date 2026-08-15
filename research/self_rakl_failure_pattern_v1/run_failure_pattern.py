"""Why did three instruments in a row refute themselves?

Applies the recursive audit to this session's own failures, then asks whether the
pattern is unique to them or already present, unnamed, on the frontier.

The three failures:

  1. ARN discriminator      chance-level aggregate hiding opposite-signed strata
  2. construct gate         admits that instrument; no obligation sees strata
  3. question-level probe   tests a corpus for a property its era could not express

Proposal-side reclassification: the same records are re-read under a new lens
after their outcomes were known. That is diagnostic, never evidence, and no
terminal is retracted.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")

from rakl.recursive_framework_audit import (  # noqa: E402
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    decide,
)

INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = Path("research/self_rakl_failure_pattern_v1/RESULT.json")

# A support failure: the population could not express the effect the instrument
# was built to detect, whatever the instrument's quality. Distinct from construct
# dependence, where the instrument reads its own construction.
SUPPORT_MARKERS = (
    ("ceiling_below_gate", r"ceiling|cannot EXPRESS|inadmissible"),
    ("designed_floor", r"deliberately (tight|built below)|designed floor|resource floor|by construction"),
    ("below_mde_resolution", r"below the registered MDE|power|underpowered|resolution requirement"),
    ("capability_floor", r"capability floor|cannot clear the task threshold|unidentifiable"),
    ("outside_domain", r"unconstructible|no executable binding point|not reachable under|coverage hole"),
)

# Construct dependence, as already characterised by the cluster research.
CONSTRUCT_MARKERS = (
    r"alongside the text|family label|identifier leakage|answer-correlated|"
    r"single-author coupling|generator's own construction|author templated|"
    r"self-grading|share one pure function|entailed by parse success|shuffl|"
    r"expressiveness oracle|equal-information generic rule engine"
)

OWN_FAILURES = [
    {
        "instrument": "arn-local-vs-parent-discriminator-v1",
        "terminal": "DISCRIMINATOR_NOT_PROBATIVE__DISTRACTOR_DESIGN_ARTIFACT",
        "support_defect": "population heterogeneous by design; the aggregate statistic averaged opposite-signed strata to chance",
        "predicate_frozen_before_support_characterised": True,
        "support_check_available_at_design_time": "yes — per-stratum reporting on a column the corpus already carried",
    },
    {
        "instrument": "construct-independence-gate-v1",
        "terminal": "VALIDATED_WITH_ONE_KNOWN_MISS",
        "support_defect": "obligation set contains only aggregate properties; no obligation conditions on strata, so heterogeneity is invisible to it",
        "predicate_frozen_before_support_characterised": True,
        "support_check_available_at_design_time": "yes — the missed instrument existed before the gate was frozen",
    },
    {
        "instrument": "question-level-instrument-v1",
        "terminal": "INSTRUMENT_UNINFORMATIVE_ON_THIS_POPULATION__VOCABULARY_POSTDATES_THE_CORPUS",
        "support_defect": "predicate outside the population's domain; no design of that era could satisfy it",
        "predicate_frozen_before_support_characterised": True,
        "support_check_available_at_design_time": "yes — one git log on the module that defines the vocabulary",
    },
]


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    records = inventory["records"]

    rows = []
    for record in records:
        blob = " ".join(
            str(record.get(f, ""))
            for f in ("one_stage_attribution", "what_happened", "core_lever", "terminal")
        )
        support_hits = [name for name, pattern in SUPPORT_MARKERS if re.search(pattern, blob, re.I)]
        construct_hit = bool(re.search(CONSTRUCT_MARKERS, blob, re.I))
        rows.append(
            {
                "slug": record["slug"],
                "support_markers": support_hits,
                "construct_marker": construct_hit,
                "family": (
                    "BOTH"
                    if support_hits and construct_hit
                    else "SUPPORT" if support_hits else "CONSTRUCT" if construct_hit else "NEITHER"
                ),
            }
        )

    families = Counter(r["family"] for r in rows)
    support_only = [r["slug"] for r in rows if r["family"] == "SUPPORT"]

    # What does the frozen chain select for a support failure? The population, not
    # the instrument, is the responsible object — EVIDENCE, and with the audit
    # still open it is a resource bound rather than a mechanic verdict.
    support_decision = decide(
        AuditNode(closure_coordinates_pass=False, material_open_residual=True),
        AuditResidual(plausible_causes=(AuditCoordinate.EVIDENCE,), resource_bound=True),
    )

    result = {
        "schema_version": "rakl-self-failure-pattern-v1",
        "status": "PROPOSAL_ONLY_POST_HOC_RECLASSIFICATION",
        "grants_scientific_authority": False,
        "question": "Why did three instruments in a row refute themselves, and is the pattern already on the frontier?",
        "named_pattern": {
            "id": "POPULATION_INSTRUMENT_MISMATCH",
            "definition": (
                "The instrument's predicate was frozen before the population's support for that "
                "predicate was characterised. The population then turned out to be heterogeneous "
                "where the statistic pools, or outside the predicate's domain entirely. The "
                "instrument may be perfectly construct-independent and still learn nothing."
            ),
            "distinct_from": (
                "construct dependence, where the instrument reads its own construction. That is a "
                "property of the instrument; this is a relation between instrument and population."
            ),
            "why_freezing_does_not_prevent_it": (
                "Freezing prevents outcome-tuning, which is a different failure. A predicate frozen "
                "against an uncharacterised population is honest and uninformative at once."
            ),
        },
        "own_failures": OWN_FAILURES,
        "own_failures_sharing_the_pattern": len(OWN_FAILURES),
        "frontier_reclassification": {
            "records": len(rows),
            "families": dict(families.most_common()),
            "support_only_slugs": support_only,
            "caveat": (
                "Post-hoc re-reading of records whose outcomes were already known, using markers "
                "chosen after the pattern was named. Diagnostic only; it retracts nothing and the "
                "audit's own coordinate mapping stands."
            ),
        },
        "chain_selection_for_a_support_failure": {
            "coordinates": ["EVIDENCE"],
            "action": support_decision.action.value,
            "reading": (
                "The frozen chain already routes a support failure away from the mechanic: the "
                "responsible object is the evidence available, and with the audit open it abstains "
                "rather than blaming the instrument. What the framework lacks is not the verdict "
                "but the precondition that would have prevented spending the instrument."
            ),
        },
        "the_framework_gap": {
            "claim": (
                "The programme already owns the mechanic that answers 'what does this population "
                "support?' — the observation contract's recall ceiling, Recall <= |G_omega|/|G|, "
                "computed before an epoch is spent. Nothing requires it to be applied to an "
                "instrument's own population before that instrument is frozen."
            ),
            "evidence": (
                "This session merged that mechanic and then froze three instruments without "
                "applying it to any of them."
            ),
            "proposed_precondition": (
                "SUPPORT_DECLARED — before an instrument is frozen, declare (a) the population it "
                "will run on, (b) whether the predicate is in that population's domain, (c) the "
                "conditioning variables the population is known to carry, and (d) the reachable "
                "ceiling for the statistic. Undeclared support is an unrun check, exactly as an "
                "undeclared construct obligation is."
            ),
            "not_implemented_here": (
                "Naming a precondition after three failures it would have caught is proposal-side. "
                "Implementing it inside the gate whose falsifier is already frozen would be the "
                "post-hoc amendment the invariants forbid; it belongs to a v2 freeze."
            ),
        },
        "is_the_task_correct": {
            "as_run": "which instrument closes this open item?",
            "prior_question_skipped": "does this population admit any instrument for this predicate?",
            "verdict": (
                "The task is right and the ordering was wrong. Every one of the three failures is "
                "the prior question going unasked, and each was answerable cheaply at design time — "
                "a per-stratum split on a column the corpus already carried, an existing instrument "
                "the gate could have been tested against, one git log."
            ),
        },
        "per_record": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"own failures sharing POPULATION_INSTRUMENT_MISMATCH: {len(OWN_FAILURES)}/3")
    print(f"frontier families: {dict(families.most_common())}")
    print(f"support-only records: {len(support_only)}")
    for slug in support_only:
        print(f"    {slug}")
    print(f"chain selects for a support failure: {support_decision.action.value}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
