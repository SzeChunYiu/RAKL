from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from common import f1, mean, paired_normal_summary, stable_hash, write_json
from provider import AnthropicCompatClient, extract_json_object

SYSTEM = """You are evaluating a scientific evidence packet. Use only the supplied evidence.
Return exactly one JSON object with keys: verdict, support_ids, refute_ids.
verdict must be SUPPORT, REFUTE, or CANNOT_CHECK.
SUPPORT means target-entity, target-QoI, target-context evidence supports the claim and there is no unresolved independent refutation.
REFUTE means target-context correction or independent target-context evidence overturns the claim.
CANNOT_CHECK means load-bearing target-context evidence is absent or independent target-context evidence conflicts without a licensed resolution.
Never infer independence from report count: reports with the same ROOT are one evidence root.
A correction may supersede an earlier result from the same ROOT.
"""

TOKEN_RE = re.compile(r"[a-z0-9_\-]+")


@dataclass(frozen=True)
class EvidenceDoc:
    doc_id: str
    entity: str
    qoi: str
    context: str
    root: str
    kind: str
    date: int
    summary: str

    def render(self) -> str:
        return (
            f"ID: {self.doc_id}\nENTITY: {self.entity}\nQOI: {self.qoi}\n"
            f"CONTEXT: {self.context}\nROOT: {self.root}\nKIND: {self.kind}\n"
            f"DATE: {self.date}\nSUMMARY: {self.summary}\n"
        )


@dataclass(frozen=True)
class RetrievalTask:
    task_id: str
    family: str
    question: str
    entity: str
    qoi: str
    context: str
    docs: tuple[EvidenceDoc, ...]
    verdict: str
    support_ids: tuple[str, ...]
    refute_ids: tuple[str, ...]

    @property
    def gold_ids(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.support_ids) | set(self.refute_ids)))


def toks(s: str) -> set[str]:
    return set(TOKEN_RE.findall(s.lower()))


def lexical_score(query: str, doc: EvidenceDoc) -> float:
    q, d = toks(query), toks(doc.render())
    if not q:
        return 0.0
    return len(q & d) / math.sqrt(max(1, len(d)))


def generic_hybrid(task: RetrievalTask, k: int) -> list[EvidenceDoc]:
    """Strong non-RAKL baseline: lexical ranking plus light duplicate-root penalty."""
    ranked = sorted(task.docs, key=lambda d: (lexical_score(task.question, d), d.date), reverse=True)
    out: list[EvidenceDoc] = []
    root_counts: dict[str, int] = {}
    while ranked and len(out) < k:
        best_i, best_score = 0, float("-inf")
        for i, d in enumerate(ranked[: max(50, 5 * k)]):
            score = lexical_score(task.question, d) - 0.10 * root_counts.get(d.root, 0)
            if score > best_score:
                best_i, best_score = i, score
        d = ranked.pop(best_i)
        out.append(d)
        root_counts[d.root] = root_counts.get(d.root, 0) + 1
    return out


def rakl_select(task: RetrievalTask, k: int) -> list[EvidenceDoc]:
    """Typed evidence-selection policy using only visible metadata, never gold/finding labels."""
    exact = [d for d in task.docs if d.entity == task.entity and d.qoi == task.qoi and d.context == task.context]
    near = [d for d in task.docs if d.entity == task.entity and d.qoi == task.qoi and d.context != task.context]

    chosen: list[EvidenceDoc] = []
    seen: set[str] = set()

    def add(d: EvidenceDoc) -> None:
        if len(chosen) < k and d.doc_id not in seen:
            chosen.append(d)
            seen.add(d.doc_id)

    for d in sorted((x for x in exact if x.kind == "correction"), key=lambda x: x.date, reverse=True):
        add(d)

    kind_priority = {"correction": 4, "measurement": 3, "review": 2, "commentary": 1}
    best_by_root: dict[str, EvidenceDoc] = {}
    for d in sorted(exact, key=lambda x: (kind_priority.get(x.kind, 0), lexical_score(task.question, x), x.date), reverse=True):
        best_by_root.setdefault(d.root, d)
    for d in sorted(best_by_root.values(), key=lambda x: (kind_priority.get(x.kind, 0), lexical_score(task.question, x), x.date), reverse=True):
        add(d)

    for d in sorted(exact, key=lambda x: (lexical_score(task.question, x), x.date), reverse=True):
        add(d)
    for d in sorted(near, key=lambda x: lexical_score(task.question, x), reverse=True):
        add(d)
    for d in sorted(task.docs, key=lambda x: lexical_score(task.question, x), reverse=True):
        add(d)
    return chosen


def oracle_select(task: RetrievalTask, k: int) -> list[EvidenceDoc]:
    by_id = {d.doc_id: d for d in task.docs}
    out = [by_id[x] for x in task.gold_ids if x in by_id]
    if len(out) < k:
        for d in generic_hybrid(task, k):
            if d.doc_id not in {x.doc_id for x in out}:
                out.append(d)
            if len(out) >= k:
                break
    return out[:k]


def _distractor(rng: random.Random, idx: int, entity: str, qoi: str, context: str) -> EvidenceDoc:
    mode = idx % 4
    if mode == 0:
        ent, qq, ctx = entity, qoi, f"adjacent_{context}_{idx % 13}"
    elif mode == 1:
        ent, qq, ctx = entity, qoi, context
    elif mode == 2:
        ent, qq, ctx = entity, f"aux_{qoi}_{idx % 17}", context
    else:
        ent, qq, ctx = f"other_{entity}_{idx % 19}", qoi, context
    root = f"noise_root_{idx % 97}"
    kind = "commentary" if mode == 1 else "measurement"
    polarity = "positive" if rng.random() < 0.5 else "negative"
    summary = (
        f"A {polarity} observation discussing {entity} {qoi} {context}. "
        f"This record is included for corpus realism and may concern a neighboring scope, derived report, "
        f"or non-load-bearing analysis. Replication note {idx}."
    )
    return EvidenceDoc(f"D{idx:06d}", ent, qq, ctx, root, kind, 2000 + idx % 25, summary)


def make_task(seed: int, family: str, target_est_tokens: int) -> RetrievalTask:
    rng = random.Random(seed)
    entity = f"system_{seed % 101}"
    qoi = f"response_{seed % 17}"
    context = f"regime_{seed % 11}"
    docs: list[EvidenceDoc] = []
    support: list[str] = []
    refute: list[str] = []

    if family == "correction":
        old = EvidenceDoc("G-OLD", entity, qoi, context, "root_A", "measurement", 2021,
                          "The original calibrated measurement reports a positive target effect above the registered threshold.")
        corr = EvidenceDoc("G-CORR", entity, qoi, context, "root_A", "correction", 2024,
                           "A source-issued correction identifies a calibration error and states that the corrected target effect is below threshold, superseding the 2021 result.")
        docs.extend([old, corr]); refute.append(corr.doc_id); verdict = "REFUTE"
    elif family == "independent_conflict":
        a = EvidenceDoc("G-A", entity, qoi, context, "root_A", "measurement", 2023,
                        "A preregistered measurement reports a positive target effect above threshold.")
        echo = EvidenceDoc("G-A-ECHO", entity, qoi, context, "root_A", "review", 2024,
                           "A review repeats the same positive target result and explicitly traces it to root_A.")
        b = EvidenceDoc("G-B", entity, qoi, context, "root_B", "measurement", 2024,
                        "An independent preregistered measurement reports a negative target effect below threshold with no adjudicating correction available.")
        docs.extend([a, echo, b]); support.append(a.doc_id); refute.append(b.doc_id); verdict = "CANNOT_CHECK"
    elif family == "scope":
        target = EvidenceDoc("G-TARGET", entity, qoi, context, "root_T", "measurement", 2024,
                             "The target-context measurement reports a positive effect above the registered threshold.")
        adjacent = EvidenceDoc("G-ADJ", entity, qoi, f"adjacent_{context}", "root_Z", "measurement", 2024,
                               "A high-powered neighboring-context measurement reports a negative effect. Its context differs from the target regime.")
        docs.extend([target, adjacent]); support.append(target.doc_id); verdict = "SUPPORT"
    else:
        raise ValueError(f"unknown family: {family}")

    i = 0
    while True:
        rendered = "\n".join(d.render() for d in docs)
        if len(rendered) // 4 >= target_est_tokens:
            break
        docs.append(_distractor(rng, i, entity, qoi, context)); i += 1
    rng.shuffle(docs)
    question = (
        f"Evaluate whether the registered claim is supported for ENTITY={entity}, QOI={qoi}, "
        f"CONTEXT={context}. Cite the load-bearing evidence IDs."
    )
    return RetrievalTask(
        task_id=f"RET-{family}-{seed}-{target_est_tokens}", family=family, question=question,
        entity=entity, qoi=qoi, context=context, docs=tuple(docs), verdict=verdict,
        support_ids=tuple(support), refute_ids=tuple(refute),
    )


def render_prompt(task: RetrievalTask, docs: Iterable[EvidenceDoc]) -> str:
    evidence = "\n---\n".join(d.render() for d in docs)
    return f"TASK_ID: {task.task_id}\nQUESTION: {task.question}\n\nEVIDENCE:\n{evidence}"


def score_answer(task: RetrievalTask, obj: dict) -> dict[str, float | bool]:
    verdict = str(obj.get("verdict", "")).upper()
    support_ids = obj.get("support_ids") if isinstance(obj.get("support_ids"), list) else []
    refute_ids = obj.get("refute_ids") if isinstance(obj.get("refute_ids"), list) else []
    return {
        "exact_verdict": verdict == task.verdict,
        "support_f1": f1(map(str, support_ids), task.support_ids),
        "refute_f1": f1(map(str, refute_ids), task.refute_ids),
        "evidence_f1": f1(map(str, list(support_ids) + list(refute_ids)), task.gold_ids),
    }


def selected_for_arm(task: RetrievalTask, arm: str, budget_docs: int, native_limit_tokens: int) -> list[EvidenceDoc] | None:
    if arm == "GENERIC_HYBRID":
        return generic_hybrid(task, budget_docs)
    if arm == "RAKL_SELECTIVE":
        return rakl_select(task, budget_docs)
    if arm == "GOLD_ORACLE":
        return oracle_select(task, budget_docs)
    if arm == "NATIVE_LONG":
        est = len("\n".join(d.render() for d in task.docs)) // 4
        return list(task.docs) if est <= native_limit_tokens else None
    raise ValueError(arm)


def run_phase(args: argparse.Namespace) -> dict:
    client = AnthropicCompatClient()
    families = ["correction", "independent_conflict", "scope"]
    pressures = args.pressures
    seed0 = 11000 if args.phase == "dev" else 91000
    tasks = [
        make_task(seed0 + i * 17 + j, fam, pressure)
        for pressure in pressures
        for i in range(args.n_per_cell)
        for j, fam in enumerate(families)
    ]
    arms = ["GENERIC_HYBRID", "RAKL_SELECTIVE", "GOLD_ORACLE", "NATIVE_LONG"]
    records: list[dict] = []
    for task in tasks:
        corpus_est = len("\n".join(d.render() for d in task.docs)) // 4
        for arm in arms:
            selected = selected_for_arm(task, arm, args.budget_docs, args.native_limit_tokens)
            if selected is None:
                records.append({"task_id": task.task_id, "family": task.family, "pressure": corpus_est,
                                "arm": arm, "status": "CAPACITY_EXCEEDED", "score": None})
                continue
            response = client.complete(user=render_prompt(task, selected), system=SYSTEM,
                                       max_tokens=args.max_output_tokens, temperature=args.temperature)
            rec = {
                "task_id": task.task_id, "family": task.family, "pressure": corpus_est, "arm": arm,
                "selected_ids": [d.doc_id for d in selected], "selected_count": len(selected),
                "gold_ids_hash": stable_hash(task.gold_ids), "transport_error": response.error,
                "latency_s": response.latency_s, "usage": response.usage, "score": None,
            }
            if response.text is not None:
                try:
                    obj = extract_json_object(response.text)
                    rec["score"] = score_answer(task, obj)
                    rec["status"] = "OK"
                except Exception as exc:
                    rec["status"] = "PARSE_ERROR"
                    rec["parse_error"] = f"{type(exc).__name__}: {exc}"
            else:
                rec["status"] = "TRANSPORT_ERROR"
            records.append(rec)

    def ok(arm: str) -> list[dict]:
        return [r for r in records if r["arm"] == arm and r.get("score") is not None]

    summary: dict[str, object] = {"phase": args.phase, "model": client.model, "arms": {}, "comparisons": {}}
    for arm in arms:
        rs = ok(arm)
        summary["arms"][arm] = {
            "n_scored": len(rs),
            "exact_verdict": mean([float(r["score"]["exact_verdict"]) for r in rs]),
            "evidence_f1": mean([float(r["score"]["evidence_f1"]) for r in rs]),
            "parse_or_transport_failures": sum(1 for r in records if r["arm"] == arm and r.get("score") is None),
        }

    by_task: dict[str, dict[str, dict]] = {}
    for r in records:
        if r.get("score") is not None:
            by_task.setdefault(r["task_id"], {})[r["arm"]] = r

    def paired(metric: str, a: str, b: str) -> dict:
        xs: list[float] = []; ys: list[float] = []
        for cell in by_task.values():
            if a in cell and b in cell:
                xs.append(float(cell[a]["score"][metric])); ys.append(float(cell[b]["score"][metric]))
        return paired_normal_summary(xs, ys)

    summary["comparisons"] = {
        "oracle_minus_generic_exact": paired("exact_verdict", "GOLD_ORACLE", "GENERIC_HYBRID"),
        "rakl_minus_generic_exact": paired("exact_verdict", "RAKL_SELECTIVE", "GENERIC_HYBRID"),
        "rakl_minus_generic_evidence_f1": paired("evidence_f1", "RAKL_SELECTIVE", "GENERIC_HYBRID"),
        "native_minus_generic_exact": paired("exact_verdict", "NATIVE_LONG", "GENERIC_HYBRID"),
    }
    summary["dev_gate"] = {
        "oracle_headroom_required": 0.10,
        "oracle_accuracy_floor": 0.70,
        "passes": (
            summary["comparisons"]["oracle_minus_generic_exact"]["delta"] >= 0.10
            and summary["arms"]["GOLD_ORACLE"]["exact_verdict"] >= 0.70
        ),
        "rule": "This gate ignores RAKL_SELECTIVE outcomes; it only tests whether evidence selection has measurable headroom.",
    }
    return {"summary": summary, "records": records}


def offline_selftest() -> None:
    for family in ("correction", "independent_conflict", "scope"):
        t = make_task(1234, family, 4000)
        assert set(t.gold_ids).issubset({d.doc_id for d in t.docs})
        assert len(rakl_select(t, 8)) <= 8
        assert len(generic_hybrid(t, 8)) <= 8
        oracle_ids = {d.doc_id for d in oracle_select(t, 8)}
        assert set(t.gold_ids).issubset(oracle_ids)
        assert t.verdict in {"SUPPORT", "REFUTE", "CANNOT_CHECK"}
    a = make_task(99, "correction", 3000)
    b = make_task(99, "correction", 3000)
    assert stable_hash(asdict(a)) == stable_hash(asdict(b))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("dev", "confirm"), required=True)
    p.add_argument("--n-per-cell", type=int, default=10)
    p.add_argument("--pressures", type=int, nargs="+", default=[32000, 256000, 900000])
    p.add_argument("--budget-docs", type=int, default=10)
    p.add_argument("--native-limit-tokens", type=int, default=int(os.environ.get("NATIVE_LONG_CONTEXT_TOKENS", "950000")))
    p.add_argument("--max-output-tokens", type=int, default=800)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--out", type=Path, default=Path("selective_retrieval_result.json"))
    return p.parse_args()


def main() -> int:
    offline_selftest()
    args = parse_args()
    result = run_phase(args)
    write_json(args.out, result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
