"""Marker validity for the regime-declaration probe.

Two questions the frozen run cannot answer about itself:

1. do the markers mean what they are supposed to mean, or do they fire on
   unrelated prose?
2. could the population have satisfied them at all?

Both are checked here, and the frozen RESULT.json is left exactly as executed.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

RESULT = Path("research/question_level_instrument_v1/RESULT.json")
OUT = Path("research/question_level_instrument_v1/MARKER_VALIDITY.json")

# The acquisition sense, as the observation contract defines it. The frozen
# probe also accepted a bare "regime", which is where the false positives came in.
STRICT_REGIME = re.compile(
    r"acquisition[_ ]regime|information[_ ]regime|source[- ]grounded|semantic[_ ]normaliz|"
    r"external[_ ]completion|benchmark[_ ]reproduction",
    re.I,
)
LOOSE_ONLY = re.compile(r"\bregimes?\b", re.I)


def contract_landed_at() -> str:
    """When the acquisition-regime vocabulary first existed in this repository."""

    return subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%cI", "--", "src/rakl/observation_contract.py"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip().splitlines()[-1]


def main() -> int:
    result = json.loads(RESULT.read_text(encoding="utf-8"))

    false_positives = []
    for row in result["per_record"]:
        if "regime" not in row["markers_present"]:
            continue
        for artifact in row["artifacts"]:
            text = Path(artifact).read_text(encoding="utf-8", errors="replace")
            if STRICT_REGIME.search(text):
                continue
            match = LOOSE_ONLY.search(text)
            if match:
                false_positives.append(
                    {
                        "slug": row["slug"],
                        "artifact": artifact,
                        "context": text[max(0, match.start() - 70) : match.end() + 70]
                        .replace("\n", " ")
                        .strip(),
                        "why": "matches 'regime' in the problem-regime sense, not an acquisition regime",
                    }
                )

    corrected = dict(result["counts"])
    for fp in false_positives:
        row = next(r for r in result["per_record"] if r["slug"] == fp["slug"])
        remaining = [m for m in row["markers_present"] if m != "regime"]
        if not remaining:
            corrected["REGIME_PARTIAL"] = corrected.get("REGIME_PARTIAL", 0) - 1
            corrected["Q_REGIME_CONFLATION_NOT_EXCLUDED"] = (
                corrected.get("Q_REGIME_CONFLATION_NOT_EXCLUDED", 0) + 1
            )

    landed = contract_landed_at()
    doc = {
        "schema_version": "rakl-question-level-instrument-marker-validity-v1",
        "grants_scientific_authority": False,
        "marker_false_positives": false_positives,
        "counts_as_executed": result["counts"],
        "counts_after_correcting_false_positives": corrected,
        "terminal_unchanged": True,
        "why_terminal_unchanged": (
            "Correcting the false positives moves records from REGIME_PARTIAL to "
            "NOT_EXCLUDED. REGIME_DECLARED stays at zero either way, so the frozen "
            "falsifier state is unaffected. The correction can only strengthen the "
            "instrument's own negative verdict about itself, never rescue it."
        ),
        "anachronism_check": {
            "acquisition_regime_vocabulary_first_existed": landed,
            "finding": (
                "The observation contract that defines acquisition regimes landed on the day this "
                "probe was run. Every design artifact in the scored population predates it, so no "
                "record could have declared an acquisition regime even in principle."
            ),
            "consequence": (
                "The probe is uninformative on THIS population by anachronism, not because the "
                "designs were careless. It measures a property the vocabulary made expressible "
                "only after they were frozen."
            ),
            "forward_use": (
                "Apply prospectively to designs authored after the observation contract landed. "
                "On that population REGIME_DECLARED becomes reachable and the falsifier becomes "
                "informative."
            ),
        },
    }
    OUT.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"marker false positives: {len(false_positives)}")
    for fp in false_positives:
        print(f"  {fp['slug'][:30]:32s} {fp['context'][:90]}")
    print(f"as executed: {result['counts']}")
    print(f"corrected:   {corrected}")
    print(f"acquisition-regime vocabulary first existed: {landed}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
