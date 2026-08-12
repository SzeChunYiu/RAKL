from __future__ import annotations

import argparse
import json
import os
import random
import re
from dataclasses import dataclass
from pathlib import Path

from common import mean, paired_normal_summary, stable_hash, write_json
from provider import AnthropicCompatClient, extract_json_object

SYSTEM = """You are solving a fresh scientific evidence task. You may receive prior verified lessons.
Prior lessons are method guidance, not scientific evidence for the current claim.
Use current evidence for the verdict and use a lesson only when its trigger/boundary fits.
Return exactly one JSON object with keys: verdict, applied_lesson_ids.
verdict must be SUPPORT, REFUTE, or CANNOT_CHECK.
Do not invent a lesson id.
"""
TOKEN_RE = re.compile(r"[a-z0-9_\-]+")


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    trigger_terms: tuple[str, ...]
    boundary_terms: tuple[str, ...]
    text: str
    verified: bool = True

    def render(self) -> str:
        return (
            f"LESSON_ID: {self.lesson_id}\nVERIFIED: {str(self.verified).lower()}\n"
            f"TRIGGERS: {', '.join(self.trigger_terms)}\n"
            f"BOUNDARIES: {', '.join(self.boundary_terms) if self.boundary_terms else 'none'}\n"
            f"METHOD: {self.text}"
        )


@dataclass(frozen=True)
class TransferTask:
    task_id: str
    question: str
    evidence: str
    verdict: str
    gold_lesson_id: str

    @property
    def signature(self) -> str:
        return f"{self.question}\n{self.evidence}".lower()


def _tokens(s: str) -> set[str]:
    return set(TOKEN_RE.findall(s.lower()))


def lesson_bank(seed: int) -> tuple[Lesson, ...]:
    core = [
        Lesson("L-ROOT-INDEPENDENCE", ("root", "independent"), (),
               "Count reports by independent evidence ROOT, not by report count. If independent target-context roots materially conflict and no adjudicating correction exists, return CANNOT_CHECK."),
        Lesson("L-SCOPE-ALIGNMENT", ("context", "target"), ("same-context-only",),
               "A result from a neighboring CONTEXT does not refute the TARGET context without an explicit transport/mapping witness. Prefer exact target-context evidence."),
        Lesson("L-CORRECTION", ("correction", "supersedes"), (),
               "A source-issued CORRECTION that explicitly SUPERSEDES an earlier result from the same root replaces that earlier result for the corrected claim."),
        Lesson("L-MISSING-EVIDENCE", ("target-context", "absent"), (),
               "When load-bearing TARGET-CONTEXT evidence is ABSENT, do not infer from neighboring contexts; return CANNOT_CHECK."),
    ]
    near_miss = [
        Lesson("L-NM-ROOT-MAJORITY", ("root", "independent"), ("conflict",),
               "When multiple independent roots all point in the same direction, aggregate them; report count can summarize agreement after independence is established."),
        Lesson("L-NM-SCOPE-TRANSPORT", ("context", "target"), ("no mapping",),
               "A neighboring-context result may be transported to the target only when an explicit mapping witness is present and verified."),
        Lesson("L-NM-CORRECTION-DRAFT", ("correction", "supersedes"), ("source-issued",),
               "A draft or third-party correction does not supersede an original source result without source authorization."),
        Lesson("L-NM-MISSING-EXTRAPOLATE", ("target-context", "absent"), ("no source",),
               "Neighboring-context evidence may fill a target gap only when a source supplies a valid transport theorem."),
    ]
    rng = random.Random(seed)
    decoys: list[Lesson] = []
    topics = ["sample-size", "unit-conversion", "citation-style", "plotting", "rounding", "calibration-window",
              "keyword-recall", "cost-budget", "formatting", "chronology", "parameter-sweep", "baseline"]
    for i in range(36):
        a, b = rng.sample(topics, 2)
        decoys.append(Lesson(
            f"L-DECOY-{i:02d}", (a, b), (),
            f"For tasks explicitly about {a} and {b}, apply the registered local procedure. This lesson has no authority outside those triggers.",
        ))
    return tuple(core + near_miss + decoys)


def make_task(seed: int, family: str) -> TransferTask:
    name = f"case_{seed % 997}"
    if family == "root_independence":
        evidence = (
            "Report R1: target-context SUPPORT, ROOT=alpha.\n"
            "Report R2: target-context SUPPORT, ROOT=alpha (derivative review of R1).\n"
            "Report R3: target-context REFUTE, ROOT=beta, independent of alpha.\n"
            "The independent roots therefore conflict, and no correction or adjudicating discriminator is available."
        )
        return TransferTask(f"EXP-{name}-root", "Assess the claim; root independence is load-bearing.", evidence,
                            "CANNOT_CHECK", "L-ROOT-INDEPENDENCE")
    if family == "scope_alignment":
        evidence = (
            "Target-context measurement: SUPPORT above the registered threshold.\n"
            "Neighboring-context measurement: REFUTE below threshold.\n"
            "No mapping witness transports the neighboring context to the target context."
        )
        return TransferTask(f"EXP-{name}-scope", "Assess the target claim with exact context alignment.", evidence,
                            "SUPPORT", "L-SCOPE-ALIGNMENT")
    if family == "correction":
        evidence = (
            "2021 root=gamma measurement: SUPPORT.\n"
            "2024 root=gamma source-issued correction: REFUTE; correction explicitly supersedes the 2021 result."
        )
        return TransferTask(f"EXP-{name}-corr", "Assess the corrected claim after a source correction supersedes an earlier result.",
                            evidence, "REFUTE", "L-CORRECTION")
    if family == "missing_evidence":
        evidence = (
            "Two neighboring-context reports discuss the same entity, but target-context evidence is absent.\n"
            "No source states a transport theorem from the neighboring regime."
        )
        return TransferTask(f"EXP-{name}-missing", "Assess whether the target-context claim is licensed when target-context evidence is absent.",
                            evidence, "CANNOT_CHECK", "L-MISSING-EVIDENCE")
    raise ValueError(family)


def lexical_memory(task: TransferTask, bank: tuple[Lesson, ...], k: int) -> list[Lesson]:
    q = _tokens(task.signature)
    ranked = sorted(bank, key=lambda l: len(q & _tokens(l.render())) / max(1, len(_tokens(l.render()))) ** 0.5,
                    reverse=True)
    return ranked[:k]


def rakl_memory(task: TransferTask, bank: tuple[Lesson, ...], k: int) -> list[Lesson]:
    sig = task.signature
    q = _tokens(sig)
    scored: list[tuple[float, Lesson]] = []
    for lesson in bank:
        trigger_hits = sum(1 for t in lesson.trigger_terms if t.lower() in sig)
        boundary_violations = sum(1 for b in lesson.boundary_terms if b.lower() in sig)
        lexical = len(q & _tokens(lesson.text)) / max(1, len(_tokens(lesson.text))) ** 0.5
        score = 3.0 * trigger_hits - 4.0 * boundary_violations + lexical
        scored.append((score, lesson))
    return [x[1] for x in sorted(scored, key=lambda z: (z[0], z[1].lesson_id), reverse=True)[:k]]


def gold_memory(task: TransferTask, bank: tuple[Lesson, ...], k: int) -> list[Lesson]:
    gold = next(l for l in bank if l.lesson_id == task.gold_lesson_id)
    decoys = [l for l in bank if l.lesson_id.startswith("L-DECOY-")]
    out = [gold]
    out.extend(decoys[: max(0, k - 1)])
    return out[:k]


def sham_memory(task: TransferTask, bank: tuple[Lesson, ...], k: int) -> list[Lesson]:
    decoys = [l for l in bank if l.lesson_id.startswith("L-DECOY-")]
    start = int(stable_hash(task.task_id)[:8], 16) % len(decoys)
    return [decoys[(start + i) % len(decoys)] for i in range(k)]


def render_prompt(task: TransferTask, lessons: list[Lesson]) -> str:
    memory = "\n\n---\n\n".join(l.render() for l in lessons) if lessons else "(no prior lesson supplied)"
    return f"TASK_ID: {task.task_id}\nQUESTION: {task.question}\nCURRENT EVIDENCE:\n{task.evidence}\n\nPRIOR VERIFIED MEMORY:\n{memory}"


def score(task: TransferTask, obj: dict) -> dict[str, float | bool]:
    verdict = str(obj.get("verdict", "")).upper()
    ids = obj.get("applied_lesson_ids") if isinstance(obj.get("applied_lesson_ids"), list) else []
    return {
        "exact_verdict": verdict == task.verdict,
        "used_gold_lesson": task.gold_lesson_id in {str(x) for x in ids},
        "overtransfer": any(str(x).startswith("L-DECOY-") for x in ids),
    }


def lessons_for_arm(task: TransferTask, bank: tuple[Lesson, ...], arm: str, k: int) -> list[Lesson]:
    if arm == "RESET": return []
    if arm == "SHAM_MEMORY": return sham_memory(task, bank, k)
    if arm == "GENERIC_MEMORY": return lexical_memory(task, bank, k)
    if arm == "RAKL_MEMORY": return rakl_memory(task, bank, k)
    if arm == "GOLD_LESSON_ORACLE": return gold_memory(task, bank, k)
    raise ValueError(arm)


def offline_selftest() -> None:
    bank = lesson_bank(7)
    assert len({l.lesson_id for l in bank}) == len(bank)
    fams = ["root_independence", "scope_alignment", "correction", "missing_evidence"]
    for i, f in enumerate(fams):
        task = make_task(100 + i, f)
        assert next(l for l in bank if l.lesson_id == task.gold_lesson_id)
        assert task.gold_lesson_id in {l.lesson_id for l in gold_memory(task, bank, 2)}
        assert not any(l.lesson_id == task.gold_lesson_id for l in sham_memory(task, bank, 2))
    assert stable_hash([l.render() for l in lesson_bank(7)]) == stable_hash([l.render() for l in lesson_bank(7)])


def run_phase(args: argparse.Namespace) -> dict:
    client = AnthropicCompatClient()
    bank = lesson_bank(args.bank_seed)
    families = ["root_independence", "scope_alignment", "correction", "missing_evidence"]
    seed0 = 21000 if args.phase == "dev" else 121000
    tasks = [make_task(seed0 + i * 13 + j, f) for i in range(args.n_per_family) for j, f in enumerate(families)]
    arms = ["RESET", "SHAM_MEMORY", "GENERIC_MEMORY", "RAKL_MEMORY", "GOLD_LESSON_ORACLE"]
    records: list[dict] = []
    for task in tasks:
        for arm in arms:
            lessons = lessons_for_arm(task, bank, arm, args.memory_objects)
            resp = client.complete(user=render_prompt(task, lessons), system=SYSTEM,
                                   max_tokens=args.max_output_tokens, temperature=args.temperature)
            rec = {"task_id": task.task_id, "arm": arm, "lesson_ids": [l.lesson_id for l in lessons],
                   "transport_error": resp.error, "latency_s": resp.latency_s, "usage": resp.usage, "score": None}
            if resp.text is None:
                rec["status"] = "TRANSPORT_ERROR"
            else:
                try:
                    rec["score"] = score(task, extract_json_object(resp.text)); rec["status"] = "OK"
                except Exception as exc:
                    rec["status"] = "PARSE_ERROR"; rec["parse_error"] = f"{type(exc).__name__}: {exc}"
            records.append(rec)

    by_task: dict[str, dict[str, dict]] = {}
    for r in records:
        if r.get("score") is not None: by_task.setdefault(r["task_id"], {})[r["arm"]] = r
    summary: dict[str, object] = {"phase": args.phase, "model": client.model, "arms": {}, "comparisons": {}}
    for arm in arms:
        rs = [r for r in records if r["arm"] == arm and r.get("score") is not None]
        summary["arms"][arm] = {
            "n_scored": len(rs),
            "exact_verdict": mean([float(r["score"]["exact_verdict"]) for r in rs]),
            "overtransfer_rate": mean([float(r["score"]["overtransfer"]) for r in rs]),
            "failures": sum(1 for r in records if r["arm"] == arm and r.get("score") is None),
        }

    def paired(a: str, b: str, metric: str = "exact_verdict") -> dict:
        xs: list[float] = []; ys: list[float] = []
        for cell in by_task.values():
            if a in cell and b in cell:
                xs.append(float(cell[a]["score"][metric])); ys.append(float(cell[b]["score"][metric]))
        return paired_normal_summary(xs, ys)

    summary["comparisons"] = {
        "oracle_minus_reset": paired("GOLD_LESSON_ORACLE", "RESET"),
        "rakl_minus_reset": paired("RAKL_MEMORY", "RESET"),
        "rakl_minus_sham": paired("RAKL_MEMORY", "SHAM_MEMORY"),
        "rakl_minus_generic": paired("RAKL_MEMORY", "GENERIC_MEMORY"),
    }
    summary["dev_gate"] = {
        "oracle_headroom_required": 0.10,
        "oracle_accuracy_floor": 0.70,
        "passes": (
            summary["comparisons"]["oracle_minus_reset"]["delta"] >= 0.10
            and summary["arms"]["GOLD_LESSON_ORACLE"]["exact_verdict"] >= 0.70
        ),
        "rule": "The gate ignores RAKL_MEMORY outcomes; it tests whether prior verified experience can matter at all.",
    }
    return {"summary": summary, "records": records, "memory_bank_hash": stable_hash([l.render() for l in bank])}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("dev", "confirm"), required=True)
    p.add_argument("--n-per-family", type=int, default=12)
    p.add_argument("--memory-objects", type=int, default=2)
    p.add_argument("--bank-seed", type=int, default=707)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-output-tokens", type=int, default=500)
    p.add_argument("--out", type=Path, default=Path("experience_transfer_result.json"))
    return p.parse_args()


def main() -> int:
    offline_selftest(); args = parse_args(); result = run_phase(args); write_json(args.out, result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
