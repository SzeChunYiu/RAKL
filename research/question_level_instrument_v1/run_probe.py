"""Execute the frozen question-level instrument (regime-declaration probe).

Reads PROTOCOL.json and does exactly what it registers: for each frontier
record, inspect its pre-execution design artifacts for the four regime markers
and apply the frozen verdicts. No outcome field is ever read.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path("research/question_level_instrument_v1")
PROTOCOL = HERE / "PROTOCOL.json"
INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = HERE / "RESULT.json"

PRE_EXECUTION = re.compile(r"(PROTOCOL|CONTRACT|FROZEN|FREEZE|REGISTRATION|SPEC|PREREGISTRATION)", re.I)

MARKERS = {
    "regime": re.compile(
        r"acquisition[_ ]regime|information[_ ]regime|source[- ]grounded|semantic[_ ]normaliz|"
        r"external[_ ]completion|world[_ ]knowledge|benchmark[_ ]reproduction|regime",
        re.I,
    ),
    "sources": re.compile(
        r"input[_ ]sources?|licensed[_ ]sources?|\"columns?\"|column[_ ]map|"
        r"query[_ ]narrative|supplied[_ ]background|mapping\"\s*:|fields?[_ ]used",
        re.I,
    ),
    "normalizer": re.compile(
        r"normaliz|paraphrase|synonym|lemma|semantic[_ ]equivalen|stemming",
        re.I,
    ),
    "external": re.compile(
        r"external[_ ]knowledge|world[_ ]knowledge|outside[_ ]knowledge|external[_ ]support|"
        r"benchmark[_ ]knowledge|contamination|leakage",
        re.I,
    ),
}


def artifacts_for(record: dict) -> list[Path]:
    candidates = [record.get("receipt_path")] + list(record.get("supporting_receipts") or [])
    out = []
    for raw in candidates:
        if not raw or not PRE_EXECUTION.search(raw):
            continue
        path = Path(raw)
        if path.is_file():
            out.append(path)
    return out


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_EXECUTION"

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    rows = []
    for record in inventory["records"]:
        paths = artifacts_for(record)
        if not paths:
            rows.append(
                {
                    "slug": record["slug"],
                    "verdict": "CANNOT_CHECK__NO_DESIGN_ARTIFACT",
                    "artifacts": [],
                    "markers_present": [],
                    "markers_missing": sorted(MARKERS),
                }
            )
            continue

        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in paths)
        present = sorted(name for name, pattern in MARKERS.items() if pattern.search(text))
        missing = sorted(set(MARKERS) - set(present))

        if "regime" in present and "sources" in present:
            verdict = "REGIME_DECLARED"
        elif present:
            verdict = "REGIME_PARTIAL"
        else:
            verdict = "Q_REGIME_CONFLATION_NOT_EXCLUDED"

        rows.append(
            {
                "slug": record["slug"],
                "verdict": verdict,
                "artifacts": [str(p) for p in paths],
                "markers_present": present,
                "markers_missing": missing,
            }
        )

    counts = Counter(r["verdict"] for r in rows)
    scored = [r for r in rows if r["verdict"] != "CANNOT_CHECK__NO_DESIGN_ARTIFACT"]
    excluded = counts["REGIME_DECLARED"]
    not_excluded = counts["Q_REGIME_CONFLATION_NOT_EXCLUDED"] + counts["REGIME_PARTIAL"]

    # Two-sided falsifier from the frozen protocol.
    if scored and excluded == len(scored):
        falsifier = "INSTRUMENT_VACUOUS__EVERY_SCORED_RECORD_DECLARES"
    elif scored and not_excluded == len(scored):
        falsifier = "INSTRUMENT_UNINFORMATIVE__NO_SCORED_RECORD_DECLARES"
    else:
        falsifier = "INSTRUMENT_DISCRIMINATES"

    result = {
        "schema_version": "rakl-question-level-instrument-result-v1",
        "protocol": str(PROTOCOL),
        "protocol_status_at_execution": protocol["status"],
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "scope": protocol["scope"],
        "records": len(rows),
        "scored": len(scored),
        "counts": dict(counts.most_common()),
        "q_subtype_excluded_for": excluded,
        "q_subtype_open_for": not_excluded,
        "falsifier_state": falsifier,
        "reading": (
            "Each REGIME_DECLARED record has ONE question-level subtype excluded — regime "
            "conflation — not the QUESTION coordinate cleared. Each open record leaves that "
            "subtype live, which is weaker than evidence that its question was malformed and "
            "stronger than the blanket CANNOT_CHECK the audit had to return."
        ),
        "non_claims": protocol["non_claims"],
        "per_record": rows,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for verdict, n in counts.most_common():
        print(f"  {verdict:38s} {n}")
    print(f"\nscored {len(scored)}/{len(rows)}   subtype excluded for {excluded}, open for {not_excluded}")
    print(f"falsifier state: {falsifier}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
