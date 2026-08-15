"""Is the discriminator's null a finding, or the dataset's adversarial design?

The ARN corpus carries a `distractor_similarity` column. If distractors were
selected FOR high surface similarity, a lexical null is guaranteed a priori and
the probe is a gate no signal can pass — the mirror image of the non-falsifiable
gate defect this programme has already recorded.

The check: does per-feature accuracy move with the distractor-similarity band?
If low-similarity rows also show nothing, the probe measures information
availability. If accuracy rises where the dataset permits surface signal, the
null is a design artifact and the discriminator is not probative.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "research/arn_local_vs_parent_discriminator_v1")

from run_discriminator import (  # noqa: E402
    FEATURES,
    build_idf,
    content_words,
    dev_rows,
)

CORPUS = Path("research/paper2_external_corpus_v1/data/arn.csv")
OUT = Path("research/arn_local_vs_parent_discriminator_v1/PROBE_VALIDITY.json")


def main() -> int:
    with CORPUS.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    dev = dev_rows(rows, 0.25)

    docs: list[list[str]] = []
    for row in dev:
        docs.extend(
            [
                content_words(row["query_narrative"]),
                content_words(row["first_choice"]),
                content_words(row["second_choice"]),
            ]
        )
    idf = build_idf(docs)

    bands = Counter(r.get("distractor_similarity", "") for r in dev)
    levels = Counter(r.get("analogy_level", "") for r in dev)

    by_band: dict[str, dict[str, object]] = {}
    for band in sorted(bands):
        subset = [r for r in dev if r.get("distractor_similarity", "") == band]
        scores: dict[str, float] = {}
        for name, fn in FEATURES.items():
            hits = 0.0
            for row in subset:
                gold = row["correct_answer"].strip()
                if gold not in {"1", "2"}:
                    continue
                q = content_words(row["query_narrative"])
                s1 = fn(q, content_words(row["first_choice"]), idf)
                s2 = fn(q, content_words(row["second_choice"]), idf)
                if s1 == s2:
                    hits += 0.5
                else:
                    pick = 1 if s1 > s2 else 2
                    hits += 1.0 if str(pick) == gold else 0.0
            scores[name] = round(hits / len(subset), 4) if subset else None
        by_band[band] = {"n": len(subset), "accuracy": scores}

    spread = {}
    for name in FEATURES:
        values = [b["accuracy"][name] for b in by_band.values() if b["accuracy"][name] is not None]
        spread[name] = round(max(values) - min(values), 4) if values else None

    max_spread = max(v for v in spread.values() if v is not None)
    verdict = (
        "PROBE_NOT_PROBATIVE__DESIGN_ARTIFACT"
        if max_spread >= 0.10
        else "PROBE_PROBATIVE__NULL_HOLDS_ACROSS_BANDS"
    )

    result = {
        "schema_version": "rakl-arn-discriminator-probe-validity-v1",
        "grants_scientific_authority": False,
        "question": (
            "Does the discriminator's null reflect information availability, or the corpus's "
            "adversarial distractor design?"
        ),
        "dev_band_counts": dict(bands),
        "dev_analogy_levels": dict(levels),
        "accuracy_by_distractor_band": by_band,
        "accuracy_spread_across_bands": spread,
        "max_spread": max_spread,
        "threshold": 0.10,
        "verdict": verdict,
        "reading": (
            "A spread at or above the threshold means surface signal appears wherever the corpus "
            "permits it, so the overall null is a property of the distractor construction rather "
            "than of the licensed prose, and the discriminator cannot separate parent from child."
            if verdict.startswith("PROBE_NOT_PROBATIVE")
            else "Accuracy stays at chance even where distractors are least similar, so the null "
            "is not produced by adversarial distractor selection alone."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("distractor bands:", dict(bands))
    for band, data in by_band.items():
        print(f"  band={band!r:10s} n={data['n']:<4} {data['accuracy']}")
    print("spread:", spread)
    print("VERDICT:", verdict)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
