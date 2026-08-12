#!/usr/bin/env python3
"""EXPLORATORY / DEVELOPMENT-TIER external-LLM comparator (NOT confirmatory).

Question: does forcing an LLM through RAKL's fail-closed applicability-obligation gate
reduce invalid-transfer FALSE-ACCEPTS versus (a) direct judgement and (b) free
chain-of-thought, on a fresh objective transfer benchmark with EXACT-VERIFIER gold?

FROZEN DESIGN (fixed before any model output was scored):
- Benchmark: rakl.objective_transfer_benchmark, FRESH seed=424242 (NOT frozen 2026081202),
  n_per_cell=4 -> 144 balanced tasks; gold from the exact verifier (ACCEPT/REJECT/CANNOT_CHECK).
- Model: glm-5.2 (same model in every condition).
- Candidate-visible info (identical across conditions): source_text, target_text, public facts.
  The hidden 'perturbation' field is never shown.
- Three conditions differ ONLY in the instruction:
    DIRECT      : answer one word, no scaffold (naive baseline).
    FREE_COT    : think step by step, then answer (controls for reasoning compute).
    RAKL_GATE   : check each named applicability obligation; ACCEPT only if all load-bearing
                  obligations satisfied; REJECT on any violation; CANNOT_CHECK if unverifiable.
  All three share the SAME 3-way label space {ACCEPT, REJECT, CANNOT_CHECK}.
- PRIMARY metric: invalid-transfer false-accept rate = P(model=ACCEPT | gold=REJECT). Lower=better.
- SECONDARY: 3-way accuracy; abstention rate; false-accept on hostile SEMANTIC_NEAR_MISS decoys.
- Pre-registered hypothesis: RAKL_GATE < FREE_COT <= DIRECT on false-accept (fail-closed helps),
  with the gate's edge over FREE_COT attributable to the obligation STRUCTURE, not compute.
- Honesty: this is a SYSTEM/method effect (a prompt scaffold + more structured inference), NOT a
  smarter model; report the result whatever it is; N and seed stated; development tier only.
"""
import os, json, re, time, urllib.request, concurrent.futures as cf
from pathlib import Path
import rakl.objective_transfer_benchmark as B

SEED=424242; N_PER_CELL=4; MODEL="glm-5.2"
OUT=Path(__file__).resolve().parent
TOKEN=os.environ["ANTHROPIC_AUTH_TOKEN"]; URL="https://api.z.ai/api/anthropic/v1/messages"
VER={"flow":B.verify_flow,"logic":B.verify_logic,"units":B.verify_units,"state":B.verify_state}

def facts(t): return json.dumps(t.public, sort_keys=True)[:1500]
def base(t):
    return (f"SOURCE (a method/result that worked in one setting):\n{t.source_text}\n\n"
            f"TARGET (a new problem):\n{t.target_text}\n\n"
            f"MACHINE-READABLE TARGET FACTS:\n{facts(t)}\n\n"
            "Question: is it valid to reuse the source for the target?\n")
PROMPTS={
 "DIRECT": lambda t: base(t)+"Answer with exactly one word: ACCEPT, REJECT, or CANNOT_CHECK.",
 "FREE_COT": lambda t: base(t)+"Think step by step. Then, on the FINAL line, output exactly one word: ACCEPT, REJECT, or CANNOT_CHECK.",
 "RAKL_GATE": lambda t: base(t)+
    ("Apply a fail-closed applicability gate. Check EACH obligation against the facts:\n"
     "1. QoI: does the target's quantity of interest match the source's?\n"
     "2. Boundary/regime: does the target regime match the source's assumptions?\n"
     "3. Mapping: is every source role mapped to a target role?\n"
     "4. Relations/invariants: are the load-bearing relations preserved (no reversed direction)?\n"
     "5. Forbidden loss: is any property whose loss invalidates reuse actually lost?\n"
     "ACCEPT only if ALL load-bearing obligations are SATISFIED. REJECT if ANY is VIOLATED. "
     "Answer CANNOT_CHECK if any load-bearing obligation cannot be verified from the facts.\n"
     "Show the obligation checks, then on the FINAL line output exactly one word: ACCEPT, REJECT, or CANNOT_CHECK."),
}
LABELS=("ACCEPT","REJECT","CANNOT_CHECK")
def parse(text):
    up=text.upper()
    for line in reversed([l.strip() for l in up.splitlines() if l.strip()]):
        for lab in LABELS:
            if lab in line: return lab
    for lab in LABELS:
        if lab in up: return lab
    return "PARSE_FAIL"

def call(prompt, max_tokens):
    body=json.dumps({"model":MODEL,"max_tokens":max_tokens,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req=urllib.request.Request(URL,data=body,headers={
        "Authorization":f"Bearer {TOKEN}","anthropic-version":"2023-06-01","content-type":"application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=90) as r:
                d=json.load(r); return "".join(b.get("text","") for b in d.get("content",[]))
        except Exception as e:
            if attempt==2: return f"__ERROR__ {e}"
            time.sleep(2*(attempt+1))

def one(job):
    t,cond=job; mt=12 if cond=="DIRECT" else 900
    txt=call(PROMPTS[cond](t),mt); return (t.item_id,cond,parse(txt or ""))

def main():
    tasks=B.generate(SEED,N_PER_CELL,include_controls=True)
    gold={t.item_id:VER[t.family](t).decision.value for t in tasks}
    meta={t.item_id:(t.family,t.item_type) for t in tasks}
    jobs=[(t,c) for t in tasks for c in PROMPTS]
    print(f"tasks={len(tasks)} jobs={len(jobs)} (seed={SEED})")
    results={}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for i,(iid,cond,lab) in enumerate(ex.map(one,jobs)):
            results[(iid,cond)]=lab
            if (i+1)%40==0: print(f"  {i+1}/{len(jobs)}")
    # score
    rows=[]; summary={}
    for cond in PROMPTS:
        inv=[iid for iid in gold if gold[iid]=="REJECT"]
        hostile=[iid for iid,(f,it) in meta.items() if it=="SEMANTIC_NEAR_MISS_INVALID_TRANSFER"]
        fa=sum(results[(iid,cond)]=="ACCEPT" for iid in inv)/max(1,len(inv))
        fa_h=sum(results[(iid,cond)]=="ACCEPT" for iid in hostile)/max(1,len(hostile))
        acc=sum(results[(iid,cond)]==gold[iid] for iid in gold)/len(gold)
        abst=sum(results[(iid,cond)]=="CANNOT_CHECK" for iid in gold)/len(gold)
        pf=sum(results[(iid,cond)]=="PARSE_FAIL" for iid in gold)
        summary[cond]={"false_accept_on_invalid":round(fa,4),"false_accept_on_hostile_decoys":round(fa_h,4),
                       "three_way_accuracy":round(acc,4),"abstention_rate":round(abst,4),"parse_fail":pf}
    for (iid,cond),lab in results.items():
        f,it=meta[iid]; rows.append({"item_id":iid,"family":f,"item_type":it,"gold":gold[iid],"condition":cond,"model":lab})
    (OUT/"raw_results.jsonl").write_text("\n".join(json.dumps(r) for r in rows)+"\n")
    (OUT/"summary.json").write_text(json.dumps({"seed":SEED,"n":len(tasks),"model":MODEL,
        "gold_dist":{k:sum(1 for v in gold.values() if v==k) for k in LABELS},"by_condition":summary},indent=2))
    print(json.dumps(summary,indent=2))

if __name__=="__main__": main()
