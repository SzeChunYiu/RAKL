"""Execute the frozen ARN local-vs-parent discriminator.

Reads PROTOCOL.json and does exactly what it registers: four label-blind
features over a source-grounded observation contract, DEV split only, label
permutation null, and the frozen decision rule applied without amendment.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")

from rakl.observation_contract import (  # noqa: E402
    InformationRegime,
    ObservationContract,
)

HERE = Path("research/arn_local_vs_parent_discriminator_v1")
PROTOCOL = HERE / "PROTOCOL.json"
CORPUS = Path("research/paper2_external_corpus_v1/data/arn.csv")
OUT = HERE / "RESULT.json"

STOPWORDS = {
    "a", "об", "the", "and", "or", "but", "if", "then", "than", "so", "to", "of", "in", "on",
    "at", "by", "for", "with", "as", "is", "was", "were", "are", "be", "been", "being", "am",
    "he", "she", "it", "they", "them", "his", "her", "its", "their", "him", "we", "us", "our",
    "you", "your", "i", "me", "my", "this", "that", "these", "those", "there", "here", "not",
    "no", "yes", "do", "did", "does", "done", "have", "has", "had", "will", "would", "could",
    "should", "can", "may", "might", "must", "from", "up", "down", "out", "off", "over",
    "under", "again", "very", "too", "all", "any", "some", "more", "most", "other", "into",
    "about", "after", "before", "when", "while", "who", "whom", "what", "which", "how", "why",
    "one", "two", "also", "just", "only", "now", "even", "still", "back", "get", "got", "go",
    "went", "make", "made", "like", "s", "t", "d", "ll", "re", "ve", "m",
}

TOKEN = re.compile(r"[a-z']+")


def content_words(text: str) -> list[str]:
    return [w for w in TOKEN.findall(text.lower()) if w not in STOPWORDS and len(w) > 2]


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def bigrams(words: list[str]) -> set[str]:
    return {f"{x}_{y}" for x, y in zip(words, words[1:])}


def thirds(words: list[str]) -> tuple[set[str], set[str]]:
    if not words:
        return set(), set()
    cut = max(1, len(words) // 3)
    return set(words[:cut]), set(words[-cut:])


def build_idf(docs: list[list[str]]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    n = len(docs)
    return {w: math.log(n / (1 + c)) for w, c in df.items()}


def f1(q: list[str], c: list[str], _idf: dict[str, float]) -> float:
    return jaccard(set(q), set(c))


def f2(q: list[str], c: list[str], idf: dict[str, float]) -> float:
    qs, cs = set(q), set(c)
    mass = sum(idf.get(w, 0.0) for w in qs)
    if mass <= 0:
        return 0.0
    return sum(idf.get(w, 0.0) for w in qs & cs) / mass


def f3(q: list[str], c: list[str], _idf: dict[str, float]) -> float:
    return jaccard(bigrams(q), bigrams(c))


def f4(q: list[str], c: list[str], _idf: dict[str, float]) -> float:
    qh, qt = thirds(q)
    ch, ct = thirds(c)
    return (jaccard(qh, ch) + jaccard(qt, ct)) / 2.0


FEATURES = {
    "F1_content_jaccard": f1,
    "F2_idf_overlap": f2,
    "F3_bigram_jaccard": f3,
    "F4_positional_overlap": f4,
}


def dev_rows(rows: list[dict[str, str]], dev_fraction: float) -> list[dict[str, str]]:
    """Group by proverb, order by sha256(group + ':20260814'), take the first quarter."""

    groups = sorted(
        {r["proverb"] for r in rows},
        key=lambda g: hashlib.sha256(f"{g}:20260814".encode("utf-8")).hexdigest(),
    )
    take = groups[: max(1, int(round(len(groups) * dev_fraction)))]
    keep = set(take)
    return [r for r in rows if r["proverb"] in keep]


def main() -> int:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_EXECUTION"

    spec = protocol["observation_contract"]
    contract = ObservationContract(
        contract_id=spec["contract_id"],
        version=spec["version"],
        regime=InformationRegime(spec["regime"]),
        input_sources=tuple(spec["input_sources"]),
        allowed_normalizers=tuple(spec["allowed_normalizers"]),
        external_knowledge_policy=spec["external_knowledge_policy"],
        provenance_required=spec["provenance_required"],
        abstention_allowed=spec["abstention_allowed"],
        evaluator_policy=spec["evaluator_policy"],
        evaluator_epoch=spec["evaluator_epoch"],
    )

    with CORPUS.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    dev = dev_rows(rows, protocol["split"]["dev_fraction"])

    # IDF is fitted on DEV text only, so no CONFIRM information reaches the probe.
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

    prepared = []
    for row in dev:
        gold = row["correct_answer"].strip()
        if gold not in {"1", "2"}:
            continue
        prepared.append(
            {
                "q": content_words(row["query_narrative"]),
                "c1": content_words(row["first_choice"]),
                "c2": content_words(row["second_choice"]),
                "gold": 1 if gold == "1" else 2,
                "analogy_level": row.get("analogy_level", ""),
                "distractor_similarity": row.get("distractor_similarity", ""),
            }
        )

    rng = random.Random(protocol["null"]["seed"])
    permutations = protocol["null"]["permutations"]
    alpha = protocol["frozen_decision_rule"]["alpha"] / len(FEATURES)
    floor = protocol["frozen_decision_rule"]["accuracy_floor"]

    per_feature = {}
    for name, fn in FEATURES.items():
        scores = []
        ties = 0
        for item in prepared:
            s1 = fn(item["q"], item["c1"], idf)
            s2 = fn(item["q"], item["c2"], idf)
            if s1 == s2:
                ties += 1
                scores.append((0.5, item["gold"]))
            else:
                pick = 1 if s1 > s2 else 2
                scores.append((1.0 if pick == item["gold"] else 0.0, item["gold"]))
        observed = sum(s for s, _ in scores) / len(scores)

        # Permutation null: shuffle which choice is gold, keep the feature values.
        ge = 0
        for _ in range(permutations):
            total = 0.0
            for value, gold in scores:
                flipped = rng.random() < 0.5
                if value == 0.5:
                    total += 0.5
                elif flipped:
                    total += 1.0 - value
                else:
                    total += value
            if total / len(scores) >= observed:
                ge += 1
        p_value = (ge + 1) / (permutations + 1)
        per_feature[name] = {
            "accuracy": round(observed, 6),
            "ties": ties,
            "p_value": round(p_value, 6),
            "significant_at_corrected_alpha": p_value < alpha,
            "reaches_accuracy_floor": observed >= floor,
        }

    significant = [n for n, r in per_feature.items() if r["significant_at_corrected_alpha"]]
    strong = [n for n in significant if per_feature[n]["reaches_accuracy_floor"]]

    if not significant:
        terminal = "PARENT_RESPONSIBLE_SUPPORTED"
        reading = (
            "No frozen label-blind feature separates analogue from distractor above chance under "
            "the registered source-grounded contract. The obstruction sits above the reducer "
            "family, and the ancestor challenge's discriminator requirement is discharged in "
            "favour of ascent."
        )
    elif strong:
        terminal = "LOCAL_RESPONSIBLE_SUPPORTED"
        reading = (
            "At least one simple label-blind feature both beats chance and reaches the accuracy "
            "floor, so separating information is present under the contract. Three failed reducer "
            "families are therefore a local failure, and ASCEND is not licensed."
        )
    else:
        terminal = "INDETERMINATE__WEAK_SIGNAL"
        reading = (
            "Signal is detectable but no feature reaches the registered accuracy floor. The "
            "discriminator did not separate the levels; the ancestor challenge stays inadmissible."
        )

    result = {
        "schema_version": "rakl-arn-local-vs-parent-discriminator-result-v1",
        "protocol": str(PROTOCOL),
        "protocol_status_at_execution": protocol["status"],
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "observation_contract_digest": contract.digest(),
        "corpus": {
            "path": str(CORPUS),
            "sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
            "rows_total": len(rows),
            "rows_dev": len(dev),
            "items_scored": len(prepared),
        },
        "corrected_alpha": alpha,
        "accuracy_floor": floor,
        "per_feature": per_feature,
        "terminal": terminal,
        "reading": reading,
        "non_claims": protocol["non_claims"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"dev rows={len(dev)}  items={len(prepared)}  corrected alpha={alpha}")
    for name, r in per_feature.items():
        print(
            f"  {name:24s} acc={r['accuracy']:.4f}  p={r['p_value']:.4f}  "
            f"sig={r['significant_at_corrected_alpha']}  >=floor={r['reaches_accuracy_floor']}"
        )
    print(f"\nTERMINAL: {terminal}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
