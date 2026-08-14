from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
from pathlib import Path

SEED = 202608140901
FAMILIES = (
    "STRAIGHT_SUPPORT",
    "STRAIGHT_REFUTATION",
    "SUPPORT_WITH_IRRELEVANT_DISTRACTORS",
    "REFUTATION_WITH_IRRELEVANT_DISTRACTORS",
    "CONTEXT_QOI_NEAR_MISS",
    "SCOPE_RESTRICTION",
    "CONFLICTING_EVIDENCE",
    "MISSING_DECISIVE_EVIDENCE_CANNOT_CHECK",
    "SAME_ROOT_PSEUDO_CORROBORATION",
    "INDEPENDENT_CORROBORATION",
    "CORRECT_VERDICT_WRONG_EVIDENCE_ID_TRAP",
)
CASES_PER_FAMILY = 12


def _oid(kind: str, i: int, j: int = 0) -> str:
    digest = hashlib.sha256(f"{SEED}:{kind}:{i}:{j}".encode()).hexdigest()[:12].upper()
    return f"{kind.upper()}-{digest}"


def _make_task(family: str, i: int) -> dict:
    family_index = FAMILIES.index(family)
    rng = random.Random(SEED ^ (i * 1009) ^ sum(map(ord, family)))
    context = f"CTX-{rng.randrange(10000):04d}"
    other_context = f"CTX-{(rng.randrange(10000) + 5000) % 10000:04d}"
    qoi = f"QOI-{rng.randrange(1000):03d}"
    other_qoi = f"QOI-{(rng.randrange(1000) + 500) % 1000:03d}"
    threshold = round(rng.uniform(4.0, 7.0), 2)
    high = round(threshold + rng.uniform(1.0, 3.0), 2)
    low = round(max(0.0, threshold - rng.uniform(1.0, 3.0)), 2)
    claim = (
        f"For context {context} and quantity {qoi}, the registered signal "
        f"exceeds threshold {threshold:.2f}."
    )

    evidence: list[dict] = []

    def add(ev_context: str, ev_qoi: str, root: str, text: str) -> str:
        evidence_id = _oid("E", family_index, i * 10 + len(evidence))
        evidence.append(
            {
                "id": evidence_id,
                "context": ev_context,
                "qoi": ev_qoi,
                "source_root": root,
                "text": text,
            }
        )
        return evidence_id

    selected: list[str]
    verdict: str
    if family == "STRAIGHT_SUPPORT":
        a = add(
            context,
            qoi,
            _oid("ROOT", i),
            f"Independent measurement reports signal {high:.2f} under the registered context and quantity.",
        )
        selected, verdict = [a], "SUPPORT"
    elif family == "STRAIGHT_REFUTATION":
        a = add(
            context,
            qoi,
            _oid("ROOT", i),
            f"Independent measurement reports signal {low:.2f} under the registered context and quantity.",
        )
        selected, verdict = [a], "REFUTE"
    elif family == "SUPPORT_WITH_IRRELEVANT_DISTRACTORS":
        a = add(context, qoi, _oid("ROOT", i), f"Registered measurement gives signal {high:.2f}.")
        add(context, other_qoi, _oid("ROOT2", i), f"Auxiliary measurement gives signal {low:.2f} for another quantity.")
        add(other_context, qoi, _oid("ROOT3", i), f"A different-context study gives signal {low:.2f}.")
        selected, verdict = [a], "SUPPORT"
    elif family == "REFUTATION_WITH_IRRELEVANT_DISTRACTORS":
        a = add(context, qoi, _oid("ROOT", i), f"Registered measurement gives signal {low:.2f}.")
        add(context, other_qoi, _oid("ROOT2", i), f"Auxiliary quantity is high at {high:.2f}.")
        add(other_context, qoi, _oid("ROOT3", i), f"Another context reports signal {high:.2f}.")
        selected, verdict = [a], "REFUTE"
    elif family == "CONTEXT_QOI_NEAR_MISS":
        a = add(other_context, qoi, _oid("ROOT", i), f"Near-miss context reports signal {high:.2f}.")
        b = add(context, other_qoi, _oid("ROOT2", i), f"Registered context but different quantity reports {high:.2f}.")
        selected, verdict = [a, b], "CONTEXT_MISALIGNED"
    elif family == "SCOPE_RESTRICTION":
        claim = (
            f"Within registered sub-scope {context}/SUB-A for quantity {qoi}, "
            f"signal exceeds threshold {threshold:.2f}."
        )
        a = add(context + "/SUB-A", qoi, _oid("ROOT", i), f"Sub-scope A measurement reports signal {high:.2f}.")
        add(context + "/SUB-B", qoi, _oid("ROOT2", i), f"Sub-scope B measurement reports signal {low:.2f}; it is outside the claim scope.")
        selected, verdict = [a], "SUPPORT"
    elif family == "CONFLICTING_EVIDENCE":
        a = add(context, qoi, _oid("ROOT", i), f"Independent measurement A reports {high:.2f}.")
        b = add(context, qoi, _oid("ROOT2", i), f"Independent measurement B reports {low:.2f}.")
        selected, verdict = [a, b], "CANNOT_CHECK"
    elif family == "MISSING_DECISIVE_EVIDENCE_CANNOT_CHECK":
        a = add(context, other_qoi, _oid("ROOT", i), f"Auxiliary quantity measurement reports {high:.2f}.")
        b = add(other_context, qoi, _oid("ROOT2", i), f"Different-context measurement reports {low:.2f}.")
        selected, verdict = [a, b], "CANNOT_CHECK"
    elif family == "SAME_ROOT_PSEUDO_CORROBORATION":
        root = _oid("ROOT", i)
        claim = (
            f"For {context}/{qoi}, the signal exceeds {threshold:.2f} with independent corroboration."
        )
        a = add(context, qoi, root, f"Report A from one experiment gives {high:.2f}.")
        b = add(context, qoi, root, f"Derived report B from the same experiment repeats {high:.2f}.")
        selected, verdict = [a, b], "REFUTE"
    elif family == "INDEPENDENT_CORROBORATION":
        claim = (
            f"For {context}/{qoi}, the signal exceeds {threshold:.2f} with independent corroboration."
        )
        a = add(context, qoi, _oid("ROOT", i), f"Independent experiment A reports {high:.2f}.")
        b = add(context, qoi, _oid("ROOT2", i), f"Independent experiment B reports {high + 0.2:.2f}.")
        selected, verdict = [a, b], "SUPPORT"
    elif family == "CORRECT_VERDICT_WRONG_EVIDENCE_ID_TRAP":
        a = add(context, qoi, _oid("ROOT", i), f"Registered evidence reports signal {high:.2f}.")
        add(other_context, qoi, _oid("ROOT2", i), f"Lexically similar but wrong-context evidence reports signal {high:.2f}.")
        add(context, other_qoi, _oid("ROOT3", i), f"Correct-context auxiliary quantity equals {high:.2f}.")
        selected, verdict = [a], "SUPPORT"
    else:  # pragma: no cover
        raise KeyError(family)

    all_ids = [item["id"] for item in evidence]
    rejected = [item for item in all_ids if item not in selected]
    prompt_lines = [
        f"Claim: {claim}",
        f"Registered context: {context}",
        f"Registered quantity of interest: {qoi}",
        "Evidence inventory:",
    ]
    for item in evidence:
        prompt_lines.append(
            f"- {item['id']} | context={item['context']} | qoi={item['qoi']} | "
            f"source_root={item['source_root']} | {item['text']}"
        )
    prompt_lines.append(
        "Classify the claim using only this evidence and the registered context/QoI."
    )
    return {
        "task_id": _oid("TASK", family_index, i),
        "family": family,
        "prompt": "\n".join(prompt_lines),
        "gold": {
            "verdict": verdict,
            "selected_evidence_ids": selected,
            "rejected_evidence_ids": rejected,
        },
    }


def build() -> list[dict]:
    tasks = [
        _make_task(family, i)
        for family in FAMILIES
        for i in range(CASES_PER_FAMILY)
    ]
    random.Random(SEED).shuffle(tasks)
    return tasks


def serialize(tasks: list[dict]) -> bytes:
    return "".join(
        json.dumps(task, sort_keys=True, separators=(",", ":")) + "\n"
        for task in tasks
    ).encode("utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    dest = root / "research" / "empirical_10_of_10_v1" / "CAPABILITY_QUALIFICATION"
    tasks = build()
    body = serialize(tasks)
    panel_sha = hashlib.sha256(body).hexdigest()
    verdicts = Counter(task["gold"]["verdict"] for task in tasks)
    forbidden = ("SUPPORT", "REFUTE", "CONTEXT_MISALIGNED", "CANNOT_CHECK")
    manifest = {
        "schema_version": "rakl-capability-stage4-panel-manifest-v1",
        "seed": SEED,
        "n": len(tasks),
        "families": list(FAMILIES),
        "cases_per_family": CASES_PER_FAMILY,
        "verdict_counts": dict(sorted(verdicts.items())),
        "panel_sha256": panel_sha,
        "opaque_ids": True,
        "task_ids_unique": len({task["task_id"] for task in tasks}) == len(tasks),
        "prompt_contains_gold_verdict_tokens": any(
            token in task["prompt"] for task in tasks for token in forbidden
        ),
        "diagnostic_overlap_forbidden": True,
        "stage2_development_overlap_forbidden": True,
        "grants_scientific_authority": False,
    }
    (dest / "FRESH_TASKS_V1.jsonl").write_bytes(body)
    (dest / "FRESH_TASK_MANIFEST_V1.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
