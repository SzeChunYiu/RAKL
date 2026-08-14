#!/usr/bin/env python3
"""STALE memory-system-mode matched-arm harness (Paper III external-surface lane).

Frozen by research/paper3_stale_memory_mode_v1/PROTOCOL_FREEZE.json. The freeze,
prompts and split rule are committed before any probe execution; the confirmatory
subset is read only after (a) the admissibility probe passes and (b) every
registered confirmatory gate condition is audited FALSIFIABLE per condition.

Phases:
  --phase probe    admissibility probe (SKYLINE vs FLOOR + judge known-answer
                   control) on the 8-scenario probe subset. Never touches the
                   confirmatory subset.
  --phase audit    per-condition falsifiability battery over the probe-phase
                   evidence rows for the registered confirmatory gates.
  --phase confirm  matched-arm confirmatory run (TYPED_ON vs NAIVE_OFF) on the
                   40-scenario confirmatory subset. Refuses to run unless the
                   probe receipt is green and the audit receipt has zero
                   NON_FALSIFIABLE conditions.

Claim boundary: ON-vs-OFF governance contrast only, local subject, local judge.
Never comparable to the published 55.2% full-context ceiling.
grants_scientific_authority: false.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

PROTOCOL = ROOT / "research" / "paper3_stale_memory_mode_v1" / "PROTOCOL_FREEZE.json"
OUTDIR_DEFAULT = ROOT / "research" / "paper3_stale_memory_mode_v1"

MODEL = "qwen2.5:3b-instruct-q4_K_M"
OLLAMA = "http://localhost:11434/api/chat"
SEED = 20260814
NUM_CTX = 8192
MAX_ANSWER_TOKENS = 256
RETRIEVAL_K = 8
CHUNK_CHARS = 5000

EXTRACT_PROMPT = (
    "You extract durable user-state facts from a dialogue chunk. Output ONLY lines of the form\n"
    "FACT|<attribute>|<value>\n"
    "Attributes are short snake_case state names about the USER (e.g. home_city, job_title, "
    "dietary_preference, car_model). Extract at most 6 facts. Only facts the USER asserts about "
    "their own current state. If none, output NONE."
)

ANSWER_ON_PROMPT = (
    "You answer using the user-state facts below. These facts are the LATEST VALID user state; "
    "any earlier contradicting state has been invalidated and must not be asserted. If the "
    "question presupposes an outdated state, correct the premise using the current facts. If no "
    "listed fact answers the question, say the information is not known rather than guessing."
)

ANSWER_OFF_PROMPT = (
    "You answer using the user-state facts below, which were extracted from earlier conversations."
)

SKYLINE_PROMPT = (
    "You answer about the user's current state. Ground truth about the most recent state change "
    "is given below; answer consistently with it."
)

FLOOR_PROMPT = (
    "Answer the question about the user. You have no records about this user."
)

JUDGE_PROMPT = (
    "You are scoring an assistant response about a user's CURRENT state.\n"
    "Gold state change (most recent truth): {gold}\n"
    "Question: {query}\n"
    "Response: {response}\n"
    "Score CORRECT only if the response is consistent with the CURRENT (post-change) state and "
    "does not assert the outdated state as current. A response that says the current state is "
    "unknown scores INCORRECT if the gold change answers the question. Output exactly one word: "
    "CORRECT or INCORRECT."
)


def chat(system: str, user: str, max_tokens: int = MAX_ANSWER_TOKENS) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": 0.0, "seed": SEED, "num_ctx": NUM_CTX, "num_predict": max_tokens},
    }).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode())["message"]["content"].strip()


# --- data ----------------------------------------------------------------------


def load_rows(parquet: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    rows = pq.read_table(parquet).to_pylist()
    rows.sort(key=lambda r: sha256(str(r["uid"]).encode()).hexdigest())
    return rows


def split(rows: list[dict[str, Any]]) -> tuple[list, list]:
    return rows[:8], rows[8:48]


def sessions_of(row: dict[str, Any]) -> list[tuple[int, str, str]]:
    hs = row["haystack_session"]
    if isinstance(hs, str):
        hs = json.loads(hs)
    ts = row.get("timestamps") or []
    if isinstance(ts, str):
        try:
            ts = json.loads(ts)
        except Exception:
            ts = []
    out = []
    for i, session in enumerate(hs):
        if not session:
            continue
        text = "\n".join(
            f"{'User' if t.get('role') == 'user' else 'Assistant'}: {t.get('content', '')}"
            for t in session
        )
        out.append((i, str(ts[i]) if i < len(ts) else str(i), text))
    return out


def queries_of(row: dict[str, Any]) -> dict[str, str]:
    pq_ = row["probing_queries"]
    if isinstance(pq_, str):
        pq_ = json.loads(pq_)
    return {"dim1": pq_["dim1_query"], "dim2": pq_["dim2_query"], "dim3": pq_["dim3_query"]}


def gold_of(row: dict[str, Any]) -> str:
    return f"M_new: {row['M_new']} | explanation: {row['explanation']}"


# --- ingestion (shared across arms) --------------------------------------------


def ingest(row: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for idx, ts, text in sessions_of(row):
        for start in range(0, len(text), CHUNK_CHARS):
            chunk = text[start:start + CHUNK_CHARS]
            if "User:" not in chunk:
                continue
            out = chat(EXTRACT_PROMPT, chunk, max_tokens=200)
            for line in out.splitlines():
                m = re.match(r"\s*FACT\|([^|]+)\|(.+)", line)
                if m:
                    facts.append({
                        "attribute": m.group(1).strip().lower().replace(" ", "_")[:60],
                        "value": m.group(2).strip()[:200],
                        "session": idx,
                        "time": ts,
                    })
    return facts


def lexical_score(query: str, fact: dict[str, Any]) -> int:
    qw = set(re.findall(r"[a-z]+", query.lower()))
    fw = set(re.findall(r"[a-z]+", (fact["attribute"] + " " + fact["value"]).lower()))
    return len(qw & fw)


def typed_current(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chains: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for f in facts:
        chains[f["attribute"]].append(f)
    current = []
    for chain in chains.values():
        chain.sort(key=lambda f: f["session"])
        current.append(chain[-1])
    return current


def facts_block(facts: list[dict[str, Any]]) -> str:
    if not facts:
        return "(no facts)"
    return "\n".join(f"- {f['attribute']}: {f['value']} (session {f['session']}, {f['time']})" for f in facts)


def answer(arm: str, facts: list[dict[str, Any]], query: str, gold: str = "") -> str:
    if arm == "TYPED_ON":
        pool = typed_current(facts)
        top = sorted(pool, key=lambda f: -lexical_score(query, f))[:RETRIEVAL_K]
        return chat(ANSWER_ON_PROMPT, f"Current valid user facts:\n{facts_block(top)}\n\nQuestion: {query}")
    if arm == "NAIVE_OFF":
        top = sorted(facts, key=lambda f: -lexical_score(query, f))[:RETRIEVAL_K]
        return chat(ANSWER_OFF_PROMPT, f"User facts:\n{facts_block(top)}\n\nQuestion: {query}")
    if arm == "SKYLINE":
        return chat(SKYLINE_PROMPT, f"Ground truth: {gold}\n\nQuestion: {query}")
    if arm == "FLOOR":
        return chat(FLOOR_PROMPT, f"Question: {query}")
    raise KeyError(arm)


def judge(query: str, gold: str, response: str) -> bool:
    out = chat("You are a strict scorer.", JUDGE_PROMPT.format(gold=gold, query=query, response=response), max_tokens=8)
    return out.strip().upper().startswith("CORRECT")


# --- phases --------------------------------------------------------------------


def phase_probe(rows: list[dict[str, Any]], outdir: Path) -> int:
    records, controls = [], []
    for row in rows:
        gold = gold_of(row)
        for dim, q in queries_of(row).items():
            for arm in ("SKYLINE", "FLOOR"):
                resp = answer(arm, [], q, gold=gold)
                records.append({"uid": row["uid"], "dim": dim, "arm": arm, "query": q,
                                "gold": gold, "response": resp, "verdict": judge(q, gold, resp)})
        # judge known-answer controls on dim1 (v1.1: natural answer phrasing —
        # see PROBE_V1_DIAGNOSIS.json; judge/prompt/threshold unchanged)
        q1 = queries_of(row)["dim1"]
        pro = (
            "Based on the conversation history, that earlier state is no longer current. "
            f"The user recently shared: \"{row['M_new']}\" — so the answer reflects this updated state."
        )
        anti = (
            "Yes, that is still the case. "
            f"The user said: \"{row['M_old']}\" and nothing has changed since."
        )
        controls.append({"uid": row["uid"], "query": q1,
                         "pro_text": pro, "anti_text": anti,
                         "pro_scored_correct": judge(q1, gold, pro),
                         "anti_scored_incorrect": not judge(q1, gold, anti)})

    def acc(arm: str, dim: str) -> float:
        xs = [r["verdict"] for r in records if r["arm"] == arm and r["dim"] == dim]
        return sum(xs) / len(xs) if xs else 0.0

    sky1, floor1 = acc("SKYLINE", "dim1"), acc("FLOOR", "dim1")
    judge_agree = (sum(c["pro_scored_correct"] for c in controls)
                   + sum(c["anti_scored_incorrect"] for c in controls)) / (2 * len(controls))
    admissible = (sky1 - floor1 >= 0.30) and (sky1 >= 0.60)
    judge_ok = judge_agree >= 0.90
    receipt = {
        "schema_version": "rakl-p3-stale-memory-mode-probe-receipt-v1",
        "n_probe_scenarios": len(rows),
        "skyline_dim1": sky1, "floor_dim1": floor1,
        "per_dim": {d: {"SKYLINE": acc("SKYLINE", d), "FLOOR": acc("FLOOR", d)} for d in ("dim1", "dim2", "dim3")},
        "judge_known_answer_agreement": judge_agree,
        "admissibility_gate_pass": admissible,
        "judge_gate_pass": judge_ok,
        "terminal": ("PROBE_GREEN" if admissible and judge_ok
                     else "JUDGE_UNRELIABLE_CANNOT_CHECK" if not judge_ok
                     else "INSTRUMENT_INADMISSIBLE_CEILING_BELOW_GATE"),
        "grants_scientific_authority": False,
    }
    (outdir / "PROBE_ROWS.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
    (outdir / "CONTROLS.jsonl").write_text("\n".join(json.dumps(c) for c in controls) + "\n")
    (outdir / "PROBE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["terminal"] == "PROBE_GREEN" else 4


def gate_conditions(min_per_dim: int):
    def g1_coverage(rows):
        counts = defaultdict(int)
        for r in rows:
            counts[(r["arm"], r["dim"])] += 1
        return all(v >= min_per_dim for v in counts.values())

    def g2_judge(rows):
        xs = [r["verdict"] for r in rows if r["arm"] == "SKYLINE"]
        anti = [not r["verdict"] for r in rows if r["arm"] == "FLOOR" and r["dim"] == "dim1"]
        pool = xs + anti
        return (sum(pool) / len(pool)) >= 0.60 if pool else False

    def g3_positive(rows):
        def overall(arm):
            xs = [r["verdict"] for r in rows if r["arm"] == arm]
            return sum(xs) / len(xs) if xs else 0.0
        a_on = overall("SKYLINE")   # audited on probe rows: SKYLINE plays ON's role
        a_off = overall("FLOOR")
        return (a_on - a_off) >= 0.10

    def g4_no_dim_regression(rows):
        for d in ("dim1", "dim2", "dim3"):
            on = [r["verdict"] for r in rows if r["arm"] == "SKYLINE" and r["dim"] == d]
            off = [r["verdict"] for r in rows if r["arm"] == "FLOOR" and r["dim"] == d]
            if on and off and (sum(on) / len(on)) < (sum(off) / len(off)) - 0.05:
                return False
        return True

    return {"G1_coverage": g1_coverage, "G2_judge_known_answer": g2_judge,
            "G3_primary_contrast_positive": g3_positive, "G4_no_dimension_regression": g4_no_dim_regression}


def phase_audit(outdir: Path) -> int:
    import random as _random

    from rakl.gate_falsifiability import audit_gate, drop_fraction, shuffle_field

    rows = [json.loads(x) for x in (outdir / "PROBE_ROWS.jsonl").read_text().splitlines()]

    def drop_one_dimension(evidence, rng):
        dims = sorted({r["dim"] for r in evidence})
        victim = rng.choice(dims)
        return [dict(r) for r in evidence if r["dim"] != victim]

    def flip_half_verdicts(evidence, rng):
        out = [dict(r) for r in evidence]
        for r in out:
            if rng.random() < 0.5:
                r["verdict"] = not r["verdict"]
        return out

    probes = {
        "shuffle_verdict": shuffle_field("verdict"),
        "shuffle_arm": shuffle_field("arm"),
        "shuffle_dim": shuffle_field("dim"),
        "drop_half_the_rows": drop_fraction(0.5),
        "drop_one_dimension": drop_one_dimension,
        "flip_half_verdicts": flip_half_verdicts,
    }
    report = {"schema_version": "rakl-p3-stale-memory-mode-gate-audit-v1",
              "evidence": "PROBE_ROWS.jsonl", "per_condition": {}, "grants_scientific_authority": False}
    bad = []
    for name, fn in gate_conditions(min_per_dim=6).items():
        r = audit_gate(fn, rows, gate_id=name, perturbations=probes, trials=32, seed=SEED)
        report["per_condition"][name] = {
            "verdict": r.verdict.value, "baseline_pass": r.baseline_pass,
            "sensitive_probes": list(r.sensitive_probes),
        }
        if r.verdict.value == "NON_FALSIFIABLE":
            bad.append(name)
    report["non_falsifiable_conditions"] = bad
    report["gate_audit_pass"] = not bad
    (outdir / "GATE_AUDIT_RECEIPT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if not bad else 5


def phase_confirm(rows: list[dict[str, Any]], outdir: Path) -> int:
    probe = json.loads((outdir / "PROBE_RECEIPT.json").read_text())
    audit = json.loads((outdir / "GATE_AUDIT_RECEIPT.json").read_text())
    if probe["terminal"] != "PROBE_GREEN" or not audit["gate_audit_pass"]:
        print("REFUSED: probe or gate audit not green; confirmatory subset not read")
        return 6

    records = []
    for n, row in enumerate(rows):
        gold = gold_of(row)
        facts = ingest(row)
        for dim, q in queries_of(row).items():
            for arm in ("TYPED_ON", "NAIVE_OFF"):
                resp = answer(arm, facts, q)
                records.append({"uid": row["uid"], "dim": dim, "arm": arm, "query": q,
                                "gold": gold, "response": resp, "verdict": judge(q, gold, resp),
                                "n_facts": len(facts)})
        (outdir / "CONFIRM_ROWS.jsonl").write_text("\n".join(json.dumps(r) for r in records) + "\n")
        print(f"scenario {n + 1}/{len(rows)} done ({len(facts)} facts)", flush=True)

    def overall(arm):
        xs = [r["verdict"] for r in records if r["arm"] == arm]
        return sum(xs) / len(xs)

    import random as _random
    rng = _random.Random(SEED)
    uids = sorted({r["uid"] for r in records})
    diffs = []
    for _ in range(2000):
        sample = [rng.choice(uids) for _ in uids]
        on = [r["verdict"] for u in sample for r in records if r["uid"] == u and r["arm"] == "TYPED_ON"]
        off = [r["verdict"] for u in sample for r in records if r["uid"] == u and r["arm"] == "NAIVE_OFF"]
        diffs.append(sum(on) / len(on) - sum(off) / len(off))
    diffs.sort()
    ci = [diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]]

    per_dim = {}
    for d in ("dim1", "dim2", "dim3"):
        per_dim[d] = {a: (lambda xs: sum(xs) / len(xs) if xs else None)(
            [r["verdict"] for r in records if r["arm"] == a and r["dim"] == d]) for a in ("TYPED_ON", "NAIVE_OFF")}

    contrast = overall("TYPED_ON") - overall("NAIVE_OFF")
    no_reg = all(per_dim[d]["TYPED_ON"] >= per_dim[d]["NAIVE_OFF"] - 0.05 for d in per_dim)
    if contrast >= 0.10 and ci[0] > 0 and no_reg:
        terminal = "TYPED_GOVERNANCE_EXTERNAL_SURFACE_SUPPORTED_IN_ENVELOPE"
    elif ci[0] <= 0 <= ci[1]:
        terminal = "INCONCLUSIVE_IN_ENVELOPE"
    else:
        terminal = "TYPED_GOVERNANCE_EXTERNAL_SURFACE_NOT_SUPPORTED_IN_ENVELOPE"

    receipt = {
        "schema_version": "rakl-p3-stale-memory-mode-confirmatory-receipt-v1",
        "n_scenarios": len(rows), "n_rows": len(records),
        "overall": {"TYPED_ON": overall("TYPED_ON"), "NAIVE_OFF": overall("NAIVE_OFF")},
        "per_dim": per_dim,
        "primary_contrast_ON_minus_OFF": contrast,
        "bootstrap_95ci": ci,
        "terminal": terminal,
        "claim_boundary": "ON_VS_OFF_GOVERNANCE_CONTRAST_ONLY — never comparable to the published 55.2% ceiling",
        "grants_scientific_authority": False,
    }
    (outdir / "CONFIRMATORY_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["probe", "audit", "confirm"])
    ap.add_argument("--parquet", default=str(Path.home() / "stale-feas" / "stale_train.parquet"))
    ap.add_argument("--outdir", default=str(OUTDIR_DEFAULT))
    args = ap.parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if args.phase == "audit":
        return phase_audit(outdir)
    rows = load_rows(Path(args.parquet))
    probe_rows, confirm_rows = split(rows)
    if args.phase == "probe":
        return phase_probe(probe_rows, outdir)
    return phase_confirm(confirm_rows, outdir)


if __name__ == "__main__":
    raise SystemExit(main())
