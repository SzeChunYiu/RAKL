"""Can this session build the successor prose instrument p2-template-inversion needs?

The lever is explicit:

    successor prose instrument: renderer author != extractor author;
    held-out realization per ambiguity class; ceiling must not rise

Before building it, the proposed design is put through the construct-independence
gate merged in #731 — the gate this session built for exactly this class of
instrument. If the gate refuses the design, building it anyway would be spending
an instrument the programme's own admission rule rejects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from rakl.construct_independence import (  # noqa: E402
    ConstructObligation,
    ConstructVerdict,
    InstrumentDesign,
    ObligationDeclaration,
    PermutationNullWitness,
    assess_construct_independence,
    decide_from_construct_verdict,
)
from rakl.research_session import (  # noqa: E402
    SupportDeclaration,
    next_step,
    render_step,
)
from rakl.recursive_framework_audit import (  # noqa: E402
    AuditCoordinate,
    AuditNode,
    AuditResidual,
)

OUT = Path("research/p2_template_successor_admission_v1/RESULT.json")

# The design this session could actually produce: one author writes both the
# renderer that generates the prose and the extractor that reads it back.
design = InstrumentDesign(
    instrument_id="p2-prose-successor-v2-single-author",
    declarations=(
        ObligationDeclaration(
            ConstructObligation.CHANNEL_SEPARATION,
            True,
            "gold coordinates are never present in the rendered surface the extractor reads",
        ),
        ObligationDeclaration(
            ConstructObligation.AUTHOR_SEPARATION,
            False,
            "this session would author both the renderer and the extractor; the lever requires "
            "renderer author != extractor author and a single agent cannot satisfy it",
        ),
        ObligationDeclaration(
            ConstructObligation.GOLD_INDEPENDENCE,
            True,
            "gold is a function of the registered structural task, not of the rendered text",
        ),
        ObligationDeclaration(
            ConstructObligation.PERMUTATION_NULL,
            True,
            "scrambling the surface collapses exact accuracy, as in the predecessor",
            witness=PermutationNullWitness(
                statistic_id="coordinate-exact-accuracy",
                observed=0.9722,
                shuffled_mean=0.25,
                chance_level=0.25,
                permutations=12,
            ),
        ),
    ),
)

decision = assess_construct_independence(design)
chain = decide_from_construct_verdict(decision)

support = SupportDeclaration(
    population="576 held-out confirmatory pairs, prose-transfer instrument",
    predicate_in_domain=True,
    conditioning_variables=("ambiguity_class",),
    reachable_ceiling=0.9722222222222222,
    ceiling_basis="G2 full_exact on the executed predecessor run; the lever requires the "
    "successor's ceiling not to rise",
)

step = next_step(
    target_id="p2-template-inversion",
    node=AuditNode(closure_coordinates_pass=False, material_open_residual=True),
    residual=AuditResidual(plausible_causes=(AuditCoordinate.MEASUREMENT,)),
    support=support,
    instrument=decision,
)

print(render_step(step))
print()
print(f"gate verdict : {decision.verdict.value}")
print(f"violated     : {list(decision.violated)}")
print(f"chain action : {chain.action.value}")

result = {
    "schema_version": "rakl-p2-template-successor-admission-v1",
    "status": "ADMISSION_REFUSED_BEFORE_CONSTRUCTION",
    "grants_scientific_authority": False,
    "question": "Can this session build the successor prose instrument the lever requires?",
    "answer": "No. The lever requires renderer author != extractor author, and one agent "
    "authoring both cannot satisfy AUTHOR_SEPARATION.",
    "gate": {
        "instrument_id": design.instrument_id,
        "verdict": decision.verdict.value,
        "violated": list(decision.violated),
        "undeclared": list(decision.undeclared),
        "reasons": list(decision.reasons),
    },
    "session_step": {
        "proposed": step.proposed_action.value,
        "licensed": step.licensed_action.value,
        "blocked": step.blocked,
        "reasons": list(step.reasons),
        "digest": step.digest(),
    },
    "support": {
        "population": support.population,
        "conditioning_variables": list(support.conditioning_variables),
        "reachable_ceiling": support.reachable_ceiling,
        "ceiling_basis": support.ceiling_basis,
    },
    "reclassification_proposed": {
        "from": "REVIVABLE_LOCAL",
        "to": "REVIVABLE_EXTERNAL",
        "reason": "author separation is a resource this session does not have, in the same sense "
        "as an A100 or a third-party annotator. It is not a budget question and no amount of "
        "local effort supplies it.",
    },
    "what_would_change_it": [
        "a second author — human or a separate agent with no access to the renderer — writing the "
        "extractor against the rendered surface alone",
        "or a third-party corpus whose surfaces this programme did not render, which converts the "
        "obligation from author separation to provenance",
    ],
    "not_claimed": [
        "This does not show a successor instrument is impossible, only that this session cannot "
        "build an admissible one.",
        "The predecessor's INSTRUMENT_NOT_PROBATIVE__TEMPLATE_INVERSION terminal is unchanged.",
        "The 0.9722 ceiling is recorded as the constraint a successor must not exceed, not as a "
        "target to reach.",
    ],
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"\nwrote {OUT}")
