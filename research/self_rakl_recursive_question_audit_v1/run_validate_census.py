"""Two validations the census needs before its numbers can be reported.

1. Denominator: are the in-scope artifacts actually instruments-with-a-target,
   or does the filename pattern sweep in round freezes and goal contracts that
   could not carry a construct-independence control in the first place?
2. Author separation: is the zero a real absence, or a false negative from a
   narrow regex?
"""

from __future__ import annotations

import json
import re
from pathlib import Path

CENSUS = Path("research/self_rakl_recursive_question_audit_v1/CONSTRUCT_INDEPENDENCE_CENSUS.json")

# An instrument-with-a-target reads some subject through a channel and grades
# it. These markers indicate such a design; their absence indicates a freeze,
# roadmap, contract or ledger that no construct control could apply to.
INSTRUMENT_MARKERS = re.compile(
    r"\barms?\b|\bgold\b|\bgrader?\b|annotat|\bextract|\bprobe\b|\bMDE\b|"
    r"accuracy|precision|recall|\bAUC\b|held-?out|\bbaseline\b|\bcondition\b|"
    r"\bresponder|\bscoring\b|\bscore[sd]?\b|\bpredict",
    re.I,
)

# Broader author-separation phrasings the tight pattern would miss.
AUTHOR_WIDE = re.compile(
    r"arm.s.length|disjoint (author|team|person)|built by (a )?different|"
    r"written by (a )?different|not the same person|independently (constructed|written|built)|"
    r"separate (person|team|constructor)|blind to the (generator|renderer)|"
    r"generator and (grader|evaluator|extractor) are",
    re.I,
)


def main() -> int:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    per_file = census["per_file"]
    non_declaring = [f for f in per_file if not f["declares_control"]]

    # --- 1. denominator ----------------------------------------------------
    # Deterministic sample: every 14th non-declaring artifact, so the selection
    # cannot be steered toward a convenient answer.
    sample = non_declaring[:: max(1, len(non_declaring) // 15)][:15]
    classified = []
    for entry in sample:
        try:
            text = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        markers = sorted({m.group(0).lower() for m in INSTRUMENT_MARKERS.finditer(text)})
        classified.append(
            {
                "path": entry["path"],
                "instrument_like": bool(markers),
                "markers": markers[:6],
            }
        )

    # Full-population version of the same test, for the applicable-subset rate.
    applicable = 0
    for entry in per_file:
        try:
            text = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if INSTRUMENT_MARKERS.search(text):
            applicable += 1
            entry["_applicable"] = True
        else:
            entry["_applicable"] = False
    applicable_declaring = sum(
        1 for e in per_file if e.get("_applicable") and e["declares_control"]
    )

    # --- 2. author-separation false-negative sweep -------------------------
    wide_hits = []
    for entry in per_file:
        try:
            text = Path(entry["path"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = AUTHOR_WIDE.search(text)
        if match:
            start = max(0, match.start() - 70)
            wide_hits.append(
                {
                    "path": entry["path"],
                    "phrase": match.group(0),
                    "context": text[start : match.end() + 70].replace("\n", " ").strip(),
                }
            )

    print(f"non-declaring artifacts: {len(non_declaring)}")
    print(f"sampled: {len(classified)}")
    not_instrument = [c for c in classified if not c["instrument_like"]]
    print(f"  instrument-like: {len(classified) - len(not_instrument)}")
    print(f"  NOT instrument-like: {len(not_instrument)}")
    for c in not_instrument:
        print(f"     - {c['path'][-70:]}")
    print()
    print(f"applicable subset (whole population): {applicable}/{len(per_file)}")
    print(f"  declaring a control within it: {applicable_declaring}/{applicable}")
    print()
    print(f"author-separation wide sweep hits: {len(wide_hits)}")
    for hit in wide_hits[:8]:
        print(f"  [{hit['phrase']}] {hit['path'][-60:]}")
        print(f"      {hit['context'][:150]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
