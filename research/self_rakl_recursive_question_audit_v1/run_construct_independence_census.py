"""Construct-independence census over the programme's registered instrument designs.

The recursive audit found that 18 of 38 frontier negatives died of construct
dependence -- the instrument read something other than its target because the
target signal and whatever generated or graded it shared a channel or an author
-- and that the checks which catch this exist only as one-off practice.

This measures how often a construct-independence control is declared in the
*pre-execution design artifact* itself. No outcome labels are used, so the
census cannot be circular with the cluster that motivated it.

Emits per-file evidence lines so every hit and non-hit can be checked by hand
rather than taken on the aggregate.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

OUT = Path("research/self_rakl_recursive_question_audit_v1/CONSTRUCT_INDEPENDENCE_CENSUS.json")

# A design artifact is in scope if it registers an instrument/protocol/contract
# a later execution was judged against.
SCOPE = re.compile(r"(PROTOCOL|CONTRACT|FROZEN|FREEZE|REGISTRATION|SPEC)[^/]*\.(json|md)$", re.I)

# Anything that is *not* an instrument design: goal contracts, ledgers, prompts.
OUT_OF_SCOPE = re.compile(r"(POSITIVE_GOAL|GOAL_CONTRACT|LEDGER|PROMPT|MANIFEST)", re.I)

# Declared construct-independence controls, by family. Each family is a
# different way of establishing that the instrument does not read its own
# construction.
CONTROLS: tuple[tuple[str, str], ...] = (
    ("label_permutation", r"shuffl|permut(ation|ed|e)\b|randomiz(ed|ation) label"),
    ("input_corruption", r"scrambl|corrupt(ed|ion) input|ablat(ed|ion) (of )?(the )?(text|input)"),
    ("author_separation", r"authors?\s*!?=|separate authors?\b|different authors?\b|renderer author\b|independent (authors?|constructors?)\b"),
    ("gold_independence", r"gold (is|must be) (a )?function of|gold independen|self-grad|gold-independen"),
    ("negative_control", r"negative control|placebo|sham|null control"),
    ("blind_or_heldout_grader", r"blind(ed)? grader|held-out (grader|annotator)|independent annotat"),
)


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "research", "experiments", "publication"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [p for p in out if SCOPE.search(p) and not OUT_OF_SCOPE.search(p)]


def main() -> int:
    files = tracked_files()
    per_file = []
    family_counts: Counter[str] = Counter()
    declared = 0

    for path in files:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits = []
        evidence = {}
        for family, pattern in CONTROLS:
            match = re.search(pattern, text, re.I)
            if match:
                hits.append(family)
                family_counts[family] += 1
                start = max(0, match.start() - 60)
                evidence[family] = text[start : match.end() + 60].replace("\n", " ").strip()
        if hits:
            declared += 1
        per_file.append(
            {
                "path": path,
                "declares_control": bool(hits),
                "families": hits,
                "evidence": evidence,
            }
        )

    result = {
        "schema_version": "rakl-construct-independence-census-v1",
        "status": "MEASUREMENT_ONLY_NO_OUTCOME_LABELS",
        "grants_scientific_authority": False,
        "question": (
            "How often does a registered instrument-design artifact declare a "
            "construct-independence control before execution?"
        ),
        "non_circularity_note": (
            "No outcome label is read. The census cannot be circular with the negative "
            "cluster that motivated it, because it never looks at how any instrument closed."
        ),
        "scope_rule": SCOPE.pattern,
        "out_of_scope_rule": OUT_OF_SCOPE.pattern,
        "control_families": {name: pattern for name, pattern in CONTROLS},
        "artifacts_in_scope": len(files),
        "artifacts_declaring_a_control": declared,
        "declaration_rate": f"{declared}/{len(files)}",
        "by_family": dict(family_counts.most_common()),
        "per_file": per_file,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"in scope: {len(files)}   declaring a control: {declared}")
    for family, n in family_counts.most_common():
        print(f"  {family:26s} {n}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
