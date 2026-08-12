"""Graded evidence-integration battery for Paper II.

Why this exists: the single pendulum task is at floor for Qwen 0.5B-7B and at
ceiling for GLM-5.2 (30/30 both arms), so it cannot register a RAKL effect of
either sign. This generates a difficulty gradient stressing the ONE coordinate
that was not saturated -- evidence-ID binding (required_support_recall stuck at
5/7 in both arms).

Ground truth is computed by a verifier from generator structure. It is never
read off "which thing I perturbed", and no verdict is ever placed in either
prompt. The RAKL arm receives NORMALIZED STRUCTURE (context tags + typed
relations); it does not receive misaligned/refuted/support dispositions.

Leak controls, run before any delta is reported:
  * MECHANICAL baseline -- a tag-only set-comparison program, no LLM. If it
    solves the task, the RAKL arm is being handed the answer and the comparison
    is void.
  * disposition scan -- assert no gold verdict term appears in either prompt.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

DIMS = ["locale", "regime", "idealization", "instrument", "timescale"]
PHYSICAL_DIMS = {"locale", "regime", "idealization"}   # setup; load-bearing
PROCEDURAL_DIMS = {"instrument", "timescale"}          # recording; not load-bearing

VALS = {
    "locale": ["earth", "moon", "orbit", "lab"],
    "regime": ["small_amplitude", "moderate_amplitude", "large_amplitude"],
    "idealization": ["ideal", "damped", "driven"],
    "instrument": ["optical", "mechanical", "digital"],
    "timescale": ["short", "medium", "long"],
}


@dataclass
class Source:
    sid: str
    claim: str
    context: dict
    polarity: bool          # asserts the effect / denies it
    topic: str


@dataclass
class Task:
    task_id: str
    sources: list
    target_context: dict
    target_topic: str
    relevant_dims: list = field(default_factory=list)
    hide_relevance: bool = False
    gold_support: list = field(default_factory=list)
    gold_misaligned: list = field(default_factory=list)
    gold_refuted: list = field(default_factory=list)


def generate(rng: random.Random, *, n_sources: int, n_dims: int, n_near_miss: int, idx: int,
             multi_dim: bool = False, hide_relevance: bool = False) -> Task:
    dims = DIMS[:n_dims]
    # Only some dimensions are load-bearing for the target QoI. Differing on an
    # IRRELEVANT dimension does not misalign a source. This is what makes the
    # task require reasoning rather than tag set-equality.
    if hide_relevance:
        # Load-bearing = dimensions describing the PHYSICAL SETUP. Which dimension
        # is physical vs procedural is never enumerated; the model must classify.
        relevant = [d for d in dims if d in PHYSICAL_DIMS]
        if not relevant:
            relevant = dims[:1]
    else:
        n_rel = max(1, n_dims // 2)
        relevant = dims[:n_rel]
    target_ctx = {d: rng.choice(VALS[d]) for d in dims}
    topic = "period_response"
    sources, i = [], 1

    def mk(ctx, pol, kind):
        nonlocal i
        s = Source(
            sid=f"E{i}",
            claim=f"under {', '.join(f'{k}={v}' for k, v in ctx.items())} the {topic} "
                  f"{'increases' if pol else 'does not increase'} ({kind})",
            context=dict(ctx), polarity=pol, topic=topic,
        )
        sources.append(s); i += 1
        return s

    # aligned supporters: identical context, asserting the effect
    for _ in range(max(2, n_sources // 3)):
        mk(target_ctx, True, "direct measurement")
    # near misses: differ in exactly ONE dimension. Half differ on a RELEVANT
    # dimension (-> genuinely misaligned); half on an IRRELEVANT one (-> still
    # aligned). A naive all-dimension comparison misclassifies the second half.
    irrelevant = [d for d in dims if d not in relevant]
    for j in range(n_near_miss):
        c = dict(target_ctx)
        if multi_dim and irrelevant and j % 3 == 2:
            # differs on SEVERAL irrelevant dims but no relevant one -> still ALIGNED.
            # "any difference" heuristics fail hardest here.
            for d in rng.sample(irrelevant, min(len(irrelevant), 2)):
                c[d] = rng.choice([v for v in VALS[d] if v != target_ctx[d]])
        elif multi_dim and irrelevant and j % 3 == 1:
            # differs on one relevant AND one irrelevant -> MISALIGNED
            for d in (rng.choice(relevant), rng.choice(irrelevant)):
                c[d] = rng.choice([v for v in VALS[d] if v != target_ctx[d]])
        else:
            pool = relevant if (j % 2 == 0 or not irrelevant) else irrelevant
            d = rng.choice(pool)
            c[d] = rng.choice([v for v in VALS[d] if v != target_ctx[d]])
        mk(c, rng.choice([True, False]), "adjacent-context study")
    # refuted: same context, denies the effect, contradicted by the aligned supporters
    for _ in range(max(1, n_sources // 6)):
        mk(target_ctx, False, "contested report")
    # filler aligned supporters up to n_sources
    while len(sources) < n_sources:
        mk(target_ctx, True, "replication")

    rng.shuffle(sources)
    for k, s in enumerate(sources, 1):
        s.sid = f"E{k}"

    t = Task(f"EVID-{n_sources}s{n_dims}d{n_near_miss}x-{idx:03d}", sources, target_ctx, topic,
             relevant_dims=list(relevant))
    t.hide_relevance = hide_relevance
    # VERIFIER: ground truth from structure, not from what was perturbed
    for s in sources:
        if any(s.context.get(d) != target_ctx[d] for d in relevant):
            t.gold_misaligned.append(s.sid)
        elif s.polarity:
            t.gold_support.append(s.sid)
        else:
            t.gold_refuted.append(s.sid)
    return t


SCHEMA = ('{"supporting_source_ids": [<string>, ...], '
          '"context_misaligned_source_ids": [<string>, ...], '
          '"refuted_source_ids": [<string>, ...]}')

DISCIPLINE = (
    "OUTPUT DISCIPLINE: Return exactly one flat JSON object matching the shape. "
    "Prefer a bare JSON object. No prose before or after.\nTOOLS: disabled\nRETRIEVAL: disabled\n"
)


def _common(t: Task) -> str:
    tgt = ", ".join(f"{k}={v}" for k, v in t.target_context.items())
    return (
        f"TARGET QUESTION\nFor the target context ({tgt}), which sources support the conclusion that "
        f"the {t.target_topic} increases; which are informative but context-misaligned for this target; "
        f"and which are refuted by the aligned evidence?\n\n"
        + (
            "LOAD-BEARING RULE: a context dimension is load-bearing if it describes the PHYSICAL SETUP "
            "under which the quantity arises; it is NOT load-bearing if it describes the RECORDING "
            "PROCEDURE used to observe it. Decide for yourself which of the dimensions present are "
            "which; they are not listed for you.\n"
            if t.hide_relevance else
            f"LOAD-BEARING DIMENSIONS for this question: {', '.join(t.relevant_dims)}. The remaining "
            f"context dimensions are recording conventions and do not affect whether a source applies.\n"
        ) + 
        f"A source is context-misaligned ONLY IF it differs from the target on a load-bearing "
        f"dimension; differing on a non-load-bearing dimension does NOT misalign it. Among "
        f"context-aligned sources, one that denies what the aligned majority establishes is refuted.\n\n"
        f"OUTPUT SHAPE\n{SCHEMA}\n\n{DISCIPLINE}"
    )


def direct_prompt(t: Task) -> str:
    body = "\n".join(f"[{s.sid}] {s.claim}" for s in t.sources)
    return f"RAW EVIDENCE CORPUS\n\n{body}\n\n{_common(t)}"


def rakl_prompt(t: Task) -> str:
    body = "\n".join(f"[{s.sid}] {s.claim}" for s in t.sources)
    # NORMALIZED STRUCTURE ONLY -- context coordinates and typed relations.
    # No support/misaligned/refuted disposition appears here.
    cmap = "\n".join(
        json.dumps({"source_id": s.sid, "context": s.context,
                    "asserts_increase": s.polarity, "topic": s.topic}, sort_keys=True)
        for s in t.sources
    )
    # Normalized coordinates ONLY. No target comparison, no relevance filtering,
    # no disposition: the model must still decide which dimensions bind and apply them.
    tgt = json.dumps({"target_context": t.target_context}, sort_keys=True)
    return (f"RAW EVIDENCE CORPUS\n\n{body}\n\nRAKL CONTEXT MAP (normalized coordinates)\n{cmap}\n"
            f"{tgt}\n\n{_common(t)}")


def mechanical_baseline(t: Task) -> dict:
    """Tag-only set comparison, NO LLM. If this solves the task, the RAKL arm is
    being handed the answer and the arm comparison is void."""
    sup, mis, ref = [], [], []
    for s in t.sources:
        if s.context != t.target_context:   # naive: compares ALL dimensions
            mis.append(s.sid)
        elif s.polarity:
            sup.append(s.sid)
        else:
            ref.append(s.sid)
    return {"supporting_source_ids": sup, "context_misaligned_source_ids": mis,
            "refuted_source_ids": ref}


def score(pred: dict, t: Task) -> dict:
    def f1(p, g):
        p, g = set(p or []), set(g)
        if not p and not g:
            return 1.0
        tp = len(p & g)
        prec = tp / len(p) if p else 0.0
        rec = tp / len(g) if g else 0.0
        return 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)
    s = f1(pred.get("supporting_source_ids"), t.gold_support)
    m = f1(pred.get("context_misaligned_source_ids"), t.gold_misaligned)
    r = f1(pred.get("refuted_source_ids"), t.gold_refuted)
    exact = (set(pred.get("supporting_source_ids") or []) == set(t.gold_support)
             and set(pred.get("context_misaligned_source_ids") or []) == set(t.gold_misaligned)
             and set(pred.get("refuted_source_ids") or []) == set(t.gold_refuted))
    return {"support_f1": s, "misaligned_f1": m, "refuted_f1": r,
            "mean_f1": (s + m + r) / 3, "exact_pass": exact}


DISPOSITION_TERMS = ["CONTEXT_MISALIGNED", "ALIGNED_REFUTATION", "negative history",
                     "misaligned_for", "refuted_by", "disposition", "verdict"]


def disposition_scan(t: Task) -> dict:
    """Assert no gold verdict is stated in either prompt (beyond the shared schema)."""
    out = {}
    for name, p in (("DIRECT", direct_prompt(t)), ("RAKL", rakl_prompt(t))):
        # exclude the shared OUTPUT SHAPE line, present identically in both arms
        body = p.split("TARGET QUESTION")[0]   # per-source content only
        out[name] = [term for term in DISPOSITION_TERMS if term.lower() in body.lower()]
    return out


def retrieval_prompt(t: Task, *, keep_frac: float = 0.6) -> str:
    """RAKL selective-retrieval arm: prefilter by structural proximity to the target.

    Ranks by count of matching context dimensions across ALL dimensions, so the
    retriever cannot see which dimensions are load-bearing and therefore cannot
    see the label. Retrieved set deliberately still contains misaligned sources.
    """
    k = max(3, int(round(len(t.sources) * keep_frac)))
    ranked = sorted(
        t.sources,
        key=lambda s: (-sum(1 for d in t.target_context if s.context.get(d) == t.target_context[d]), s.sid),
    )
    kept = sorted(ranked[:k], key=lambda s: int(s.sid[1:]))
    body = "\n".join(f"[{s.sid}] {s.claim}" for s in kept)
    cmap = "\n".join(
        json.dumps({"source_id": s.sid, "context": s.context,
                    "asserts_increase": s.polarity, "topic": s.topic}, sort_keys=True)
        for s in kept
    )
    tgt = json.dumps({"target_context": t.target_context}, sort_keys=True)
    return (f"RAKL-RETRIEVED EVIDENCE (structural proximity to target; {k} of {len(t.sources)} sources; "
            f"the retriever is blind to which dimensions are load-bearing)\n\n{body}\n\n"
            f"RAKL CONTEXT MAP (normalized coordinates)\n{cmap}\n{tgt}\n\n{_common(t)}")


def retrieval_recall(t: Task, *, keep_frac: float = 0.6) -> dict:
    """How much gold the prefilter discards -- a retrieval arm that drops gold
    sources is handicapped, and that must be reported, not hidden."""
    k = max(3, int(round(len(t.sources) * keep_frac)))
    ranked = sorted(
        t.sources,
        key=lambda s: (-sum(1 for d in t.target_context if s.context.get(d) == t.target_context[d]), s.sid),
    )
    kept = {s.sid for s in ranked[:k]}
    def rec(g):
        return 1.0 if not g else len(kept & set(g)) / len(g)
    return {"support": rec(t.gold_support), "misaligned": rec(t.gold_misaligned),
            "refuted": rec(t.gold_refuted)}
