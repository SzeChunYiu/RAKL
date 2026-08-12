"""Oracle headroom: how much is relevance DETERMINATION worth, at all?

Matched configs, DIRECT arm only, varying exactly one thing: whether the
load-bearing dimensions are stated. The gap is the upper bound on what any
relevance-determination mechanism (RAKL's included) could ever deliver here.
"""
import json, os, random, sys
from concurrent.futures import ThreadPoolExecutor
from math import erfc, sqrt
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main_battery import generate, direct_prompt, score, mechanical_baseline

BASE=os.environ["ANTHROPIC_BASE_URL"].rstrip("/"); TOK=os.environ["ANTHROPIC_AUTH_TOKEN"]
N=int(os.environ.get("RUN_N","30"))
def call(p):
    b=json.dumps({"model":"glm-5.2","max_tokens":1500,"temperature":1.0,
                  "messages":[{"role":"user","content":p}]}).encode()
    r=urllib.request.Request(f"{BASE}/v1/messages",data=b,headers={"x-api-key":TOK,
        "anthropic-version":"2023-06-01","content-type":"application/json"})
    try:
        with urllib.request.urlopen(r,timeout=240) as x: q=json.load(x)
        return "".join(c.get("text","") for c in q.get("content",[]) if c.get("type")=="text")
    except Exception: return None
def parse(s):
    if not s: return None
    i,j=s.find("{"),s.rfind("}")
    try: return json.loads(s[i:j+1])
    except Exception: return None
def welch(a,b):
    ma,mb=sum(a)/len(a),sum(b)/len(b)
    va=sum((x-ma)**2 for x in a)/(len(a)-1); vb=sum((x-mb)**2 for x in b)/(len(b)-1)
    se=sqrt(va/len(a)+vb/len(b))
    if se==0: return ma-mb,1.0,0.0
    t=(ma-mb)/se
    return ma-mb, erfc(abs(t)/sqrt(2)), se

# same_relevance forces an identical load-bearing set in both conditions, so the
# ONLY difference is disclosure. Same seed -> byte-identical task instances.
CFG=dict(n_sources=14,n_dims=5,n_near_miss=6,multi_dim=True,same_relevance=True)
out={}
for label,hide in (("RELEVANCE_STATED",False),("RELEVANCE_HIDDEN",True)):
    rng=random.Random(4242)   # SAME seed -> identical task instances in both conditions
    ts=[generate(rng,idx=i,hide_relevance=hide,**CFG) for i in range(N)]
    mech=[score(mechanical_baseline(t),t)["mean_f1"] for t in ts]
    with ThreadPoolExecutor(max_workers=8) as pool:
        preds=list(pool.map(lambda t: parse(call(direct_prompt(t))), ts))
    sc=[score(p,t) for p,t in zip(preds,ts) if p]
    out[label]={"n":len(sc),"mean_f1":sum(s["mean_f1"] for s in sc)/len(sc),
                "misaligned_f1":sum(s["misaligned_f1"] for s in sc)/len(sc),
                "exact":sum(s["exact_pass"] for s in sc)/len(sc),
                "mech_f1":sum(mech)/len(mech),
                "_f1s":[s["mean_f1"] for s in sc]}
a,b=out["RELEVANCE_STATED"],out["RELEVANCE_HIDDEN"]
d,p,se=welch(a["_f1s"],b["_f1s"])
for k in out: out[k].pop("_f1s")
out["headroom"]={"delta_mean_f1":d,"p":p,"se":se,"ci95":[d-1.96*se,d+1.96*se]}
out["interpretation"]=("Upper bound on what any relevance-determination mechanism could deliver "
                       "on this task family: stating the load-bearing dimensions is worth this much.")
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"main-headroom2-result.json"),"w"),indent=1)
print(json.dumps(out,indent=1))
