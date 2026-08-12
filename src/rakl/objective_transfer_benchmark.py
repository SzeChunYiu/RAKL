from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Mapping, Sequence
from collections import Counter, defaultdict, deque
import hashlib, json, math, random, re, statistics

class Decision(str, Enum):
    ACCEPT="ACCEPT"
    REJECT="REJECT"
    CANNOT_CHECK="CANNOT_CHECK"

FAMILIES=("flow","logic","units","state")
PRIMARY_ITEM_TYPES=(
    "VALID_DISTANT_TRANSFER",
    "SEMANTIC_NEAR_MISS_INVALID_TRANSFER",
    "DIRECTION_REVERSED_INVALID",
    "BOUNDARY_QOI_MISMATCH",
    "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK",
)
CONTROL_ITEM_TYPES=("VALID_NEAR_CONTROL","INVALID_DISTANT_CONTROL")
ALL_ITEM_TYPES=PRIMARY_ITEM_TYPES+CONTROL_ITEM_TYPES

@dataclass(frozen=True)
class Task:
    item_id: str
    family: str
    item_type: str
    source_text: str
    target_text: str
    public: Mapping[str, Any]
    perturbation: str  # kept in hidden packet only; never candidate-visible

@dataclass(frozen=True)
class Verification:
    decision: Decision
    trace: tuple[str,...]

@dataclass(frozen=True)
class Witness:
    decision: Decision
    obligations: tuple[tuple[str,str], ...] # (name,status)
    reasons: tuple[str,...]

TOKEN_RE=re.compile(r"[a-z0-9_]+")

def tokens(s:str)->set[str]:
    return set(TOKEN_RE.findall(s.lower()))

def jaccard(a:str,b:str)->float:
    A,B=tokens(a),tokens(b)
    if not A and not B: return 1.0
    return len(A&B)/max(1,len(A|B))

SEM_NEAR = {
    "flow": ("packet router queue capacity network service", "frame switch queue capacity network service"),
    "logic": ("clinical rule symptom evidence diagnosis", "medical rule symptom evidence diagnosis"),
    "units": ("physical rate distance time conversion", "engineering rate distance time conversion"),
    "state": ("workflow state action transition goal", "process state action transition goal"),
}
SEM_FAR = {
    "flow": ("packet router queue capacity network", "hospital patient triage service demand"),
    "logic": ("clinical rule symptom evidence", "software permission dependency authorization"),
    "units": ("physical speed distance time", "financial price quantity currency"),
    "state": ("workflow state action transition", "robot navigation mode command waypoint"),
}

def _semantic_text(family:str, near:bool, rng:random.Random, salt:int)->tuple[str,str]:
    src,tgt=(SEM_NEAR if near else SEM_FAR)[family]
    shared = ["analysis","transfer","case"] if rng.random()<0.5 else ["study","candidate","case"]
    src_extra=[f"s{salt%17}", f"k{rng.randrange(11)}"]
    tgt_extra=[f"t{salt%19}", f"k{rng.randrange(11)}"]
    return " ".join(src.split()+shared+src_extra), " ".join(tgt.split()+shared+tgt_extra)

def _id(seed:int,index:int)->str:
    h=hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:16]
    return f"obj-{h}"

def _flow_task(seed:int,index:int,item_type:str,near:bool,rng:random.Random)->Task:
    src_edges={(0,1):5,(1,2):4,(2,3):6}
    demand=3
    target_edges={(10,11):5,(11,12):4,(12,13):6}
    qoi="throughput"; mode="directed"
    mapping={"0":10,"1":11,"2":12,"3":13}; perturb="none"
    if item_type in ("SEMANTIC_NEAR_MISS_INVALID_TRANSFER","INVALID_DISTANT_CONTROL"):
        target_edges[(11,12)]=2; perturb="capacity"
    elif item_type=="DIRECTION_REVERSED_INVALID":
        mapping={"0":13,"1":12,"2":11,"3":10}; perturb="direction"
    elif item_type=="BOUNDARY_QOI_MISMATCH":
        qoi="latency" if index%2 else "throughput"
        mode="undirected" if qoi=="throughput" else "directed"
        perturb="qoi" if qoi!="throughput" else "boundary"
    elif item_type=="PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index%2: mapping.pop("2"); perturb="mapping_missing"
        else: target_edges[(11,12)]=None; perturb="capacity_unknown"
    stext,ttext=_semantic_text("flow",near,rng,index)
    public={
        "source":{"edges":[[a,b,c] for (a,b),c in src_edges.items()],"path":[0,1,2,3],"demand":demand,"qoi":"throughput","mode":"directed"},
        "target":{"edges":[[a,b,c] for (a,b),c in target_edges.items()],"qoi":qoi,"mode":mode},
        "mapping":mapping,
    }
    return Task(_id(seed,index),"flow",item_type,stext,ttext,public,perturb)

def _logic_closure(facts:set[str], rules:list[tuple[tuple[str,...],str]])->set[str]:
    out=set(facts); changed=True
    while changed:
        changed=False
        for ants,con in rules:
            if all(a in out for a in ants) and con not in out:
                out.add(con); changed=True
    return out

def _logic_task(seed,index,item_type,near,rng):
    source={"facts":["A","B"],"rules":[[["A","B"],"C"]],"query":"C"}
    mapping={"A":"p","B":"q","C":"r"}; target_facts=["p","q"]
    target_rules=[(["p","q"],"r")]; qoi="entailment"; boundary="horn"; perturb="none"
    if item_type in ("SEMANTIC_NEAR_MISS_INVALID_TRANSFER","INVALID_DISTANT_CONTROL"):
        target_rules=[(["p","q"],"s")]; perturb="wrong_conclusion"
    elif item_type=="DIRECTION_REVERSED_INVALID":
        target_rules=[(["r"],"p"),(["r"],"q")]; perturb="direction"
    elif item_type=="BOUNDARY_QOI_MISMATCH":
        qoi="consistency" if index%2 else "entailment"
        boundary="closed_world" if qoi=="entailment" else "horn"
        perturb="qoi" if qoi!="entailment" else "boundary"
    elif item_type=="PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index%2: mapping.pop("C"); perturb="mapping_missing"
        else: target_rules=[(["p","q"],None)]; perturb="rule_unknown"
    stext,ttext=_semantic_text("logic",near,rng,index)
    public={"source":source,"target":{"facts":target_facts,"rules":target_rules,"qoi":qoi,"boundary":boundary},"mapping":mapping}
    return Task(_id(seed,index),"logic",item_type,stext,ttext,public,perturb)

def _dim_add(a,b): return tuple(x+y for x,y in zip(a,b))
def _dim_sub(a,b): return tuple(x-y for x,y in zip(a,b))
def _units_task(seed,index,item_type,near,rng):
    source={"input_dims":[(1,0,0),(0,0,1)],"operation":"divide","output_dim":(1,0,-1),"qoi":"rate","boundary":"multiplicative"}
    target_in=[(1,0,0),(0,0,1)]; target_out=(1,0,-1); operation="divide"
    qoi="rate"; boundary="multiplicative"; denominator_known_nonzero=True; perturb="none"
    if item_type in ("SEMANTIC_NEAR_MISS_INVALID_TRANSFER","INVALID_DISTANT_CONTROL"):
        target_out=(1,0,1); perturb="dimension"
    elif item_type=="DIRECTION_REVERSED_INVALID":
        operation="reverse_divide"; perturb="direction"
    elif item_type=="BOUNDARY_QOI_MISMATCH":
        if index%2: qoi="acceleration"; perturb="qoi"
        else: boundary="affine"; perturb="boundary"
    elif item_type=="PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index%2: target_in=[(1,0,0),None]; perturb="dimension_unknown"
        else: denominator_known_nonzero=None; perturb="precondition_unknown"
    stext,ttext=_semantic_text("units",near,rng,index)
    public={"source":source,"target":{"input_dims":target_in,"operation":operation,"output_dim":target_out,"qoi":qoi,"boundary":boundary,"denominator_nonzero":denominator_known_nonzero}}
    return Task(_id(seed,index),"units",item_type,stext,ttext,public,perturb)

def _state_task(seed,index,item_type,near,rng):
    source={"start":"s0","goal":"s3","actions":["a","b","c"],"qoi":"reach_goal","boundary":"deterministic"}
    target_trans={("t0","a"):"t1",("t1","b"):"t2",("t2","c"):"t3"}
    mapping={"s0":"t0","s1":"t1","s2":"t2","s3":"t3"}
    actions=["a","b","c"]; goal="t3"; qoi="reach_goal"; boundary="deterministic"; perturb="none"
    if item_type in ("SEMANTIC_NEAR_MISS_INVALID_TRANSFER","INVALID_DISTANT_CONTROL"):
        target_trans[("t1","b")]="tx"; perturb="transition"
    elif item_type=="DIRECTION_REVERSED_INVALID":
        actions=["c","b","a"]; perturb="direction"
    elif item_type=="BOUNDARY_QOI_MISMATCH":
        if index%2: qoi="avoid_state"; perturb="qoi"
        else: boundary="nondeterministic"; perturb="boundary"
    elif item_type=="PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index%2: mapping.pop("s2"); perturb="mapping_missing"
        else: target_trans[("t1","b")]=None; perturb="transition_unknown"
    stext,ttext=_semantic_text("state",near,rng,index)
    public={"source":source,"target":{"transitions":[[s,a,n] for (s,a),n in target_trans.items()],"start":"t0","goal":goal,"qoi":qoi,"boundary":boundary},"mapping":mapping,"candidate_actions":actions}
    return Task(_id(seed,index),"state",item_type,stext,ttext,public,perturb)

GEN={"flow":_flow_task,"logic":_logic_task,"units":_units_task,"state":_state_task}

def generate(seed:int,n_per_cell:int=20, include_controls:bool=True)->list[Task]:
    rng=random.Random(seed)
    item_types=list(PRIMARY_ITEM_TYPES)+(list(CONTROL_ITEM_TYPES) if include_controls else [])
    tasks=[]; index=0
    multipliers={"VALID_DISTANT_TRANSFER":2,"VALID_NEAR_CONTROL":2}
    for fam in FAMILIES:
        for typ in item_types:
            count=n_per_cell*multipliers.get(typ,1)
            for k in range(count):
                if typ=="SEMANTIC_NEAR_MISS_INVALID_TRANSFER": near=True
                elif typ=="INVALID_DISTANT_CONTROL": near=False
                elif typ=="VALID_NEAR_CONTROL": near=True
                elif typ=="VALID_DISTANT_TRANSFER": near=False
                else: near=(k%2==0)
                tasks.append(GEN[fam](seed,index,typ,near,rng)); index+=1
    rng.shuffle(tasks)
    return tasks

def verify_flow(t:Task)->Verification:
    p=t.public; src=p["source"]; tgt=p["target"]; mp=p["mapping"]
    if tgt["qoi"]!="throughput": return Verification(Decision.REJECT,("qoi_mismatch",))
    if tgt["mode"]!="directed": return Verification(Decision.REJECT,("boundary_mismatch",))
    if any(str(node) not in mp for node in src["path"]): return Verification(Decision.CANNOT_CHECK,("mapping_incomplete",))
    path=[mp[str(node)] for node in src["path"]]; edge_map={(a,b):cap for a,b,cap in tgt["edges"]}
    for a,b in zip(path,path[1:]):
        if (a,b) not in edge_map: return Verification(Decision.REJECT,(f"edge_missing:{a}->{b}",))
        cap=edge_map[(a,b)]
        if cap is None: return Verification(Decision.CANNOT_CHECK,(f"capacity_unknown:{a}->{b}",))
        if cap<src["demand"]: return Verification(Decision.REJECT,(f"capacity_insufficient:{a}->{b}",))
    return Verification(Decision.ACCEPT,("mapped_path_feasible",))

def verify_logic(t:Task)->Verification:
    p=t.public; src=p["source"]; tgt=p["target"]; mp=p["mapping"]
    if tgt["qoi"]!="entailment": return Verification(Decision.REJECT,("qoi_mismatch",))
    if tgt["boundary"]!="horn": return Verification(Decision.REJECT,("boundary_mismatch",))
    needed=set(src["facts"]+[src["query"]])
    if not needed.issubset(mp): return Verification(Decision.CANNOT_CHECK,("mapping_incomplete",))
    if any(con is None for _,con in tgt["rules"]): return Verification(Decision.CANNOT_CHECK,("rule_unknown",))
    rules=[(tuple(ants),con) for ants,con in tgt["rules"]]; closure=_logic_closure(set(tgt["facts"]),rules); query=mp[src["query"]]
    return Verification(Decision.ACCEPT if query in closure else Decision.REJECT,(f"closure_contains_query:{query in closure}",))

def verify_units(t:Task)->Verification:
    src=t.public["source"]; tgt=t.public["target"]
    if tgt["qoi"]!="rate": return Verification(Decision.REJECT,("qoi_mismatch",))
    if tgt["boundary"]!="multiplicative": return Verification(Decision.REJECT,("boundary_mismatch",))
    if any(x is None for x in tgt["input_dims"]): return Verification(Decision.CANNOT_CHECK,("dimension_unknown",))
    if tgt["denominator_nonzero"] is None: return Verification(Decision.CANNOT_CHECK,("precondition_unknown",))
    if tgt["denominator_nonzero"] is False: return Verification(Decision.REJECT,("zero_denominator",))
    a,b=tgt["input_dims"]
    if tgt["operation"]=="divide": derived=_dim_sub(tuple(a),tuple(b))
    elif tgt["operation"]=="reverse_divide": derived=_dim_sub(tuple(b),tuple(a))
    else: return Verification(Decision.CANNOT_CHECK,("operation_unknown",))
    return Verification(Decision.ACCEPT if tuple(tgt["output_dim"])==derived else Decision.REJECT,(f"derived_dim:{derived}",))

def verify_state(t:Task)->Verification:
    tgt=t.public["target"]; actions=t.public["candidate_actions"]; mp=t.public["mapping"]
    if not {"s0","s1","s2","s3"}.issubset(mp): return Verification(Decision.CANNOT_CHECK,("mapping_incomplete",))
    if tgt["qoi"]!="reach_goal": return Verification(Decision.REJECT,("qoi_mismatch",))
    if tgt["boundary"]!="deterministic": return Verification(Decision.REJECT,("boundary_mismatch",))
    trans={(s,a):n for s,a,n in tgt["transitions"]}; state=tgt["start"]
    for a in actions:
        if (state,a) not in trans: return Verification(Decision.REJECT,(f"transition_missing:{state}:{a}",))
        nxt=trans[(state,a)]
        if nxt is None: return Verification(Decision.CANNOT_CHECK,(f"transition_unknown:{state}:{a}",))
        state=nxt
    return Verification(Decision.ACCEPT if state==tgt["goal"] else Decision.REJECT,(f"final:{state}",))

VER={"flow":verify_flow,"logic":verify_logic,"units":verify_units,"state":verify_state}
def verify(t:Task)->Verification: return VER[t.family](t)

def _merge_statuses(statuses:Sequence[Decision])->Decision:
    if Decision.REJECT in statuses: return Decision.REJECT
    if Decision.CANNOT_CHECK in statuses: return Decision.CANNOT_CHECK
    return Decision.ACCEPT

def extract_flow(t:Task, ablate=frozenset())->Witness:
    p=t.public; src=p["source"]; tgt=p["target"]; mp=p["mapping"]; obs=[]; sts=[]
    if "qoi" not in ablate:
        st=Decision.ACCEPT if tgt["qoi"]==src["qoi"] else Decision.REJECT; obs.append(("qoi",st.value)); sts.append(st)
    if "boundary" not in ablate:
        st=Decision.ACCEPT if tgt["mode"]==src["mode"] else Decision.REJECT; obs.append(("boundary",st.value)); sts.append(st)
    path=src["path"]
    if "mapping" not in ablate:
        st=Decision.ACCEPT if all(str(x) in mp for x in path) else Decision.CANNOT_CHECK; obs.append(("mapping",st.value)); sts.append(st)
    if all(str(x) in mp for x in path):
        mapped=[mp[str(x)] for x in path]; edges={(a,b):c for a,b,c in tgt["edges"]}
        if "relations" not in ablate:
            for a,b in zip(mapped,mapped[1:]):
                if (a,b) not in edges: st=Decision.REJECT
                elif edges[(a,b)] is None: st=Decision.CANNOT_CHECK
                else: st=Decision.ACCEPT
                obs.append((f"relation:{a}->{b}",st.value)); sts.append(st)
        if "precondition" not in ablate:
            caps=[]
            for a,b in zip(mapped,mapped[1:]):
                if (a,b) not in edges: caps.append(Decision.REJECT)
                elif edges[(a,b)] is None: caps.append(Decision.CANNOT_CHECK)
                else: caps.append(Decision.ACCEPT if edges[(a,b)]>=src["demand"] else Decision.REJECT)
            st=_merge_statuses(caps); obs.append(("capacity_precondition",st.value)); sts.append(st)
        if "effect" not in ablate:
            vals=[]
            for a,b in zip(mapped,mapped[1:]):
                if (a,b) not in edges: vals.append(Decision.REJECT)
                elif edges[(a,b)] is None: vals.append(Decision.CANNOT_CHECK)
                else: vals.append(Decision.ACCEPT)
            if _merge_statuses(vals)==Decision.ACCEPT:
                bottleneck=min(edges[(a,b)] for a,b in zip(mapped,mapped[1:])); st=Decision.ACCEPT if bottleneck>=src["demand"] else Decision.REJECT
            else: st=_merge_statuses(vals)
            obs.append(("derived_throughput_effect",st.value)); sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,tuple(obs),tuple(x for x,s in obs if s!="ACCEPT"))

def extract_logic(t:Task,ablate=frozenset())->Witness:
    p=t.public; src=p["source"]; tgt=p["target"]; mp=p["mapping"]; obs=[]; sts=[]
    if "qoi" not in ablate:
        st=Decision.ACCEPT if tgt["qoi"]=="entailment" else Decision.REJECT; obs.append(("qoi",st.value));sts.append(st)
    if "boundary" not in ablate:
        st=Decision.ACCEPT if tgt["boundary"]=="horn" else Decision.REJECT;obs.append(("boundary",st.value));sts.append(st)
    needed=set(src["facts"]+[src["query"]])
    if "mapping" not in ablate:
        st=Decision.ACCEPT if needed.issubset(mp) else Decision.CANNOT_CHECK;obs.append(("mapping",st.value));sts.append(st)
    if needed.issubset(mp):
        if any(con is None for _,con in tgt["rules"]): st=Decision.CANNOT_CHECK
        else:
            active=set(tgt["facts"]); changed=True
            while changed:
                changed=False
                for ants,con in tgt["rules"]:
                    if all(a in active for a in ants) and con not in active: active.add(con); changed=True
            st=Decision.ACCEPT if mp[src["query"]] in active else Decision.REJECT
        if "relations" not in ablate: obs.append(("logical_relation",st.value));sts.append(st)
        if "effect" not in ablate: obs.append(("derived_entailment_effect",st.value));sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,tuple(obs),tuple(x for x,s in obs if s!="ACCEPT"))

def extract_units(t:Task,ablate=frozenset())->Witness:
    src=t.public["source"]; tgt=t.public["target"];obs=[];sts=[]
    if "qoi" not in ablate:
        st=Decision.ACCEPT if tgt["qoi"]==src["qoi"] else Decision.REJECT;obs.append(("qoi",st.value));sts.append(st)
    if "boundary" not in ablate:
        st=Decision.ACCEPT if tgt["boundary"]==src["boundary"] else Decision.REJECT;obs.append(("boundary",st.value));sts.append(st)
    if "precondition" not in ablate:
        nz=tgt["denominator_nonzero"]; st=Decision.CANNOT_CHECK if nz is None else Decision.ACCEPT if nz else Decision.REJECT
        obs.append(("nonzero_precondition",st.value));sts.append(st)
    if "invariant" not in ablate:
        if any(x is None for x in tgt["input_dims"]): st=Decision.CANNOT_CHECK
        else:
            a,b=tgt["input_dims"]
            derived=_dim_sub(tuple(a),tuple(b)) if tgt["operation"]=="divide" else _dim_sub(tuple(b),tuple(a)) if tgt["operation"]=="reverse_divide" else None
            st=Decision.CANNOT_CHECK if derived is None else Decision.ACCEPT if derived==tuple(tgt["output_dim"]) else Decision.REJECT
        obs.append(("dimension_invariant",st.value));sts.append(st)
    if "effect" not in ablate:
        if any(x is None for x in tgt["input_dims"]) or tgt["denominator_nonzero"] is None: st=Decision.CANNOT_CHECK
        elif tgt["denominator_nonzero"] is False: st=Decision.REJECT
        else:
            a,b=tgt["input_dims"]
            derived=_dim_sub(tuple(a),tuple(b)) if tgt["operation"]=="divide" else _dim_sub(tuple(b),tuple(a)) if tgt["operation"]=="reverse_divide" else None
            st=Decision.CANNOT_CHECK if derived is None else Decision.ACCEPT if derived==tuple(tgt["output_dim"]) else Decision.REJECT
        obs.append(("derived_dimensional_effect",st.value));sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,tuple(obs),tuple(x for x,s in obs if s!="ACCEPT"))

def extract_state(t:Task,ablate=frozenset())->Witness:
    tgt=t.public["target"]; mp=t.public["mapping"]; obs=[];sts=[]
    if "mapping" not in ablate:
        st=Decision.ACCEPT if {"s0","s1","s2","s3"}.issubset(mp) else Decision.CANNOT_CHECK; obs.append(("mapping",st.value)); sts.append(st)
    if "qoi" not in ablate:
        st=Decision.ACCEPT if tgt["qoi"]=="reach_goal" else Decision.REJECT;obs.append(("qoi",st.value));sts.append(st)
    if "boundary" not in ablate:
        st=Decision.ACCEPT if tgt["boundary"]=="deterministic" else Decision.REJECT;obs.append(("boundary",st.value));sts.append(st)
    trans={(s,a):n for s,a,n in tgt["transitions"]};state=tgt["start"]; statuses=[]
    for a in t.public["candidate_actions"]:
        if (state,a) not in trans: statuses.append(Decision.REJECT); break
        nxt=trans[(state,a)]
        if nxt is None: statuses.append(Decision.CANNOT_CHECK); break
        statuses.append(Decision.ACCEPT); state=nxt
    if statuses and _merge_statuses(statuses)==Decision.ACCEPT and state!=tgt["goal"]: statuses.append(Decision.REJECT)
    st=_merge_statuses(statuses) if statuses else Decision.CANNOT_CHECK
    if "relations" not in ablate: obs.append(("transition_path",st.value));sts.append(st)
    if "effect" not in ablate: obs.append(("derived_terminal_effect",st.value));sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,tuple(obs),tuple(x for x,s in obs if s!="ACCEPT"))

EXT={"flow":extract_flow,"logic":extract_logic,"units":extract_units,"state":extract_state}
def extract(t:Task,ablate=frozenset())->Witness: return EXT[t.family](t,ablate)

def lexical_score(t:Task)->float: return jaccard(t.source_text,t.target_text)

def fit_threshold(tasks:Sequence[Task], gold:Mapping[str,Decision])->float:
    rows=[(lexical_score(t),gold[t.item_id]) for t in tasks if gold[t.item_id]!=Decision.CANNOT_CHECK]
    vals=sorted(set(s for s,_ in rows)); candidates=[0.0]+[(a+b)/2 for a,b in zip(vals,vals[1:])]+[1.0]; scored=[]
    for th in candidates:
        acc=sum((Decision.ACCEPT if s>=th else Decision.REJECT)==g for s,g in rows)/max(1,len(rows)); scored.append((acc,-abs(th-statistics.median(vals)),th))
    return max(scored)[2]

def lexical_predict(t:Task,threshold:float)->Decision: return Decision.ACCEPT if lexical_score(t)>=threshold else Decision.REJECT

def class_probs_from_lexical(t:Task,threshold:float,temperature:float=0.08)->dict[Decision,float]:
    x=(lexical_score(t)-threshold)/temperature; p=1/(1+math.exp(-max(-20,min(20,x))))
    return {Decision.ACCEPT:0.96*p, Decision.REJECT:0.96*(1-p), Decision.CANNOT_CHECK:0.04}

def class_probs_from_witness(w:Witness)->dict[Decision,float]:
    if w.decision==Decision.ACCEPT: return {Decision.ACCEPT:.96,Decision.REJECT:.02,Decision.CANNOT_CHECK:.02}
    if w.decision==Decision.REJECT: return {Decision.ACCEPT:.02,Decision.REJECT:.96,Decision.CANNOT_CHECK:.02}
    return {Decision.ACCEPT:.02,Decision.REJECT:.02,Decision.CANNOT_CHECK:.96}

def multiclass_brier(prob:Mapping[Decision,float],gold:Decision)->float:
    return sum((prob[d]-(1.0 if d==gold else 0.0))**2 for d in Decision)

def evaluate(tasks:Sequence[Task],threshold:float,ablate=frozenset())->dict[str,Any]:
    gold={t.item_id:verify(t).decision for t in tasks}; wpred={t.item_id:extract(t,ablate).decision for t in tasks}; lpred={t.item_id:lexical_predict(t,threshold) for t in tasks}
    n=len(tasks); known=[t for t in tasks if gold[t.item_id]!=Decision.CANNOT_CHECK]; accept=[t for t in tasks if gold[t.item_id]==Decision.ACCEPT]; reject=[t for t in tasks if gold[t.item_id]==Decision.REJECT]; unknown=[t for t in tasks if gold[t.item_id]==Decision.CANNOT_CHECK]
    hard_q2=[t for t in tasks if t.item_type=="VALID_DISTANT_TRANSFER"]; hard_q3=[t for t in tasks if t.item_type=="SEMANTIC_NEAR_MISS_INVALID_TRANSFER"]
    lb=[multiclass_brier(class_probs_from_lexical(t,threshold),gold[t.item_id]) for t in tasks]; wb=[multiclass_brier(class_probs_from_witness(extract(t,ablate)),gold[t.item_id]) for t in tasks]; diffs=[a-b for a,b in zip(lb,wb)]
    byfam={}
    for fam in FAMILIES:
        subset=[t for t in tasks if t.family==fam]; byfam[fam]=sum(wpred[t.item_id]==gold[t.item_id] for t in subset)/len(subset)
    return {
        "n":n,"gold_counts":dict(Counter(g.value for g in gold.values())),
        "lexical_accuracy_known":sum(lpred[t.item_id]==gold[t.item_id] for t in known)/len(known),
        "witness_exact3":sum(wpred[t.item_id]==gold[t.item_id] for t in tasks)/n,"lexical_exact3":sum(lpred[t.item_id]==gold[t.item_id] for t in tasks)/n,
        "witness_valid_accept":sum(wpred[t.item_id]==Decision.ACCEPT for t in accept)/max(1,len(accept)),"witness_false_accept":sum(wpred[t.item_id]==Decision.ACCEPT for t in reject)/max(1,len(reject)),"witness_unknown_abstain":sum(wpred[t.item_id]==Decision.CANNOT_CHECK for t in unknown)/max(1,len(unknown)),
        "lexical_valid_accept":sum(lpred[t.item_id]==Decision.ACCEPT for t in accept)/max(1,len(accept)),"lexical_false_accept":sum(lpred[t.item_id]==Decision.ACCEPT for t in reject)/max(1,len(reject)),
        "q2_witness_accept":sum(wpred[t.item_id]==Decision.ACCEPT for t in hard_q2)/len(hard_q2),"q3_witness_false_accept":sum(wpred[t.item_id]==Decision.ACCEPT for t in hard_q3)/len(hard_q3),"q2_lexical_accept":sum(lpred[t.item_id]==Decision.ACCEPT for t in hard_q2)/len(hard_q2),"q3_lexical_false_accept":sum(lpred[t.item_id]==Decision.ACCEPT for t in hard_q3)/len(hard_q3),
        "lexical_brier_mean":statistics.mean(lb),"witness_brier_mean":statistics.mean(wb),"delta_brier_mean":statistics.mean(diffs),"delta_brier_sd":statistics.stdev(diffs) if len(diffs)>1 else 0.0,"family_witness_exact3":byfam,
    }

def semantic_decorrelation(tasks:Sequence[Task])->dict[str,Any]:
    out={}
    for fam in FAMILIES:
        rows=[(lexical_score(t),verify(t).decision) for t in tasks if t.family==fam and verify(t).decision!=Decision.CANNOT_CHECK]
        A=[s for s,g in rows if g==Decision.ACCEPT]; R=[s for s,g in rows if g==Decision.REJECT]
        out[fam]={"accept_mean":statistics.mean(A),"reject_mean":statistics.mean(R),"mean_diff":statistics.mean(A)-statistics.mean(R),"accept_n":len(A),"reject_n":len(R)}
    return out

def blind_attacks(tasks:Sequence[Task])->dict[str,float]:
    gold=[verify(t).decision for t in tasks]
    def acc(pred): return sum(p==g for p,g in zip(pred,gold))/len(gold)
    majority=Counter(gold).most_common(1)[0][0]; family_rule={}
    for fam in FAMILIES:
        vals=[verify(t).decision for t in tasks if t.family==fam]; family_rule[fam]=Counter(vals).most_common(1)[0][0]
    return {"always_accept":acc([Decision.ACCEPT]*len(tasks)),"always_reject":acc([Decision.REJECT]*len(tasks)),"always_cannot_check":acc([Decision.CANNOT_CHECK]*len(tasks)),"majority":acc([majority]*len(tasks)),"family_majority":acc([family_rule[t.family] for t in tasks])}

def paired_bootstrap_delta(tasks:Sequence[Task],threshold:float,seed:int=7,reps:int=5000)->dict[str,float]:
    rng=random.Random(seed); diffs=[]
    for t in tasks:
        g=verify(t).decision; diffs.append(multiclass_brier(class_probs_from_lexical(t,threshold),g)-multiclass_brier(class_probs_from_witness(extract(t)),g))
    n=len(diffs); means=[]
    for _ in range(reps): means.append(sum(diffs[rng.randrange(n)] for _ in range(n))/n)
    means.sort(); return {"mean":statistics.mean(diffs),"ci95_low":means[int(.025*reps)],"ci95_high":means[int(.975*reps)]}

@dataclass(frozen=True)
class RoutingEpisode:
    episode_id:str
    candidates:tuple[Task,...]

def make_routing_episodes(seed:int,n:int=1000)->list[RoutingEpisode]:
    rng=random.Random(seed); eps=[]; idx=0
    for e in range(n):
        fam=FAMILIES[e%len(FAMILIES)]; candidates=[]
        specs=[("VALID_DISTANT_TRANSFER",False),("SEMANTIC_NEAR_MISS_INVALID_TRANSFER",True),("PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK", bool(e%2))]
        for typ,near in specs:
            t=GEN[fam](seed,100000+idx,typ,near,rng);idx+=1;candidates.append(t)
        rng.shuffle(candidates); eps.append(RoutingEpisode(f"route-{e:05d}",tuple(candidates)))
    return eps

def route_semantic(ep:RoutingEpisode,threshold:float)->Task|None: return max(ep.candidates,key=lexical_score)
def route_witness(ep:RoutingEpisode)->Task|None:
    licensed=[t for t in ep.candidates if extract(t).decision==Decision.ACCEPT]
    if not licensed: return None
    return max(licensed,key=lexical_score)
def route_hybrid(ep:RoutingEpisode,threshold:float)->Task|None:
    ranked=sorted(ep.candidates,key=lexical_score,reverse=True)
    for t in ranked:
        if extract(t).decision==Decision.ACCEPT:return t
    return None

def eval_routing(eps:Sequence[RoutingEpisode],threshold:float)->dict[str,Any]:
    arms={"semantic":lambda e:route_semantic(e,threshold),"witness_gate":route_witness,"hybrid":lambda e:route_hybrid(e,threshold)}; out={}
    for name,fn in arms.items():
        success=invalid=abstain=attempts=0
        for ep in eps:
            choice=fn(ep)
            if choice is None: abstain+=1; continue
            attempts+=1; d=verify(choice).decision; success+=d==Decision.ACCEPT; invalid+=d==Decision.REJECT
        out[name]={"success_rate":success/len(eps),"invalid_transfer_rate":invalid/len(eps),"abstain_rate":abstain/len(eps),"attempts":attempts}
    return out

def twin_ablation(t:Task)->frozenset[str]:
    mapping={"capacity":"precondition","capacity_unknown":"precondition","wrong_conclusion":"relations","rule_unknown":"relations","dimension":"invariant","dimension_unknown":"invariant","transition":"relations","transition_unknown":"relations","direction":"relations" if t.family!="units" else "invariant","boundary":"boundary","qoi":"qoi","mapping_missing":"mapping","precondition_unknown":"precondition"}
    key=mapping.get(t.perturbation); return frozenset({key}) if key else frozenset()

def evaluate_twin(tasks:Sequence[Task],threshold:float)->dict[str,Any]:
    gold={t.item_id:verify(t).decision for t in tasks}; pred={t.item_id:extract(t,twin_ablation(t)).decision for t in tasks}
    accept=[t for t in tasks if gold[t.item_id]==Decision.ACCEPT]; reject=[t for t in tasks if gold[t.item_id]==Decision.REJECT]; unknown=[t for t in tasks if gold[t.item_id]==Decision.CANNOT_CHECK]
    brier=[]; lex_brier=[]
    for t in tasks:
        w=extract(t,twin_ablation(t)); brier.append(multiclass_brier(class_probs_from_witness(w),gold[t.item_id])); lex_brier.append(multiclass_brier(class_probs_from_lexical(t,threshold),gold[t.item_id]))
    return {"exact3":sum(pred[t.item_id]==gold[t.item_id] for t in tasks)/len(tasks),"valid_accept":sum(pred[t.item_id]==Decision.ACCEPT for t in accept)/max(1,len(accept)),"false_accept":sum(pred[t.item_id]==Decision.ACCEPT for t in reject)/max(1,len(reject)),"unknown_abstain":sum(pred[t.item_id]==Decision.CANNOT_CHECK for t in unknown)/max(1,len(unknown)),"brier_mean":statistics.mean(brier),"delta_brier_vs_lexical":statistics.mean(a-b for a,b in zip(lex_brier,brier)),"by_perturbation":{p:sum(pred[t.item_id]==gold[t.item_id] for t in tasks if t.perturbation==p)/sum(1 for t in tasks if t.perturbation==p) for p in sorted(set(t.perturbation for t in tasks))}}

MECHANISM_ALIGNMENT_ABLATION=frozenset({"qoi","boundary","mapping","relations","precondition","invariant"})
RELATIONAL_BASELINE_ABLATION=frozenset({"qoi","boundary","precondition","effect"})
def mechanism_predict(t:Task)->Decision: return extract(t,MECHANISM_ALIGNMENT_ABLATION).decision
def relational_predict(t:Task)->Decision: return extract(t,RELATIONAL_BASELINE_ABLATION).decision

def binary_accept_probability_lexical(t:Task,threshold:float,temperature:float=0.08)->float:
    x=(lexical_score(t)-threshold)/temperature; return 1/(1+math.exp(-max(-20,min(20,x))))
def binary_accept_probability_decision(d:Decision)->float: return 0.98 if d is Decision.ACCEPT else 0.02 if d is Decision.REJECT else 0.50

def binary_brier_development(tasks:Sequence[Task],threshold:float,extractor=extract)->dict[str,float]:
    diffs=[]; lex=[]; arm=[]
    for t in tasks:
        g=verify(t).decision
        if g is Decision.CANNOT_CHECK: continue
        y=1.0 if g is Decision.ACCEPT else 0.0; pl=binary_accept_probability_lexical(t,threshold); pw=binary_accept_probability_decision(extractor(t).decision); lb=(pl-y)**2; wb=(pw-y)**2
        lex.append(lb); arm.append(wb); diffs.append(lb-wb)
    return {"n_decidable":len(diffs),"lexical_brier":statistics.mean(lex),"arm_brier":statistics.mean(arm),"delta_brier":statistics.mean(diffs),"sigma_d":statistics.stdev(diffs) if len(diffs)>1 else 0.0}

def required_n_for_mde(sigma_d:float,mde:float=0.05,z_alpha:float=1.95996398454,z_power:float=0.84162123357)->int:
    return math.ceil((z_alpha+z_power)**2*sigma_d**2/(mde**2))
def arm_disagreement_fraction(tasks:Sequence[Task],threshold:float,extractor=extract)->float:
    rows=[t for t in tasks if verify(t).decision is not Decision.CANNOT_CHECK]; return sum(lexical_predict(t,threshold)!=extractor(t).decision for t in rows)/max(1,len(rows))

def permutation_semantic_decorrelation(tasks:Sequence[Task],seed:int=20260812,reps:int=4000)->dict[str,dict[str,float]]:
    out={}
    for j,fam in enumerate(FAMILIES):
        A=[lexical_score(t) for t in tasks if t.family==fam and verify(t).decision is Decision.ACCEPT]; R=[lexical_score(t) for t in tasks if t.family==fam and verify(t).decision is Decision.REJECT]
        obs=abs(statistics.mean(A)-statistics.mean(R)); vals=A+R; n=len(A); rng=random.Random(seed+j); exceed=0
        for _ in range(reps):
            arr=vals[:]; rng.shuffle(arr); d=abs(statistics.mean(arr[:n])-statistics.mean(arr[n:])); exceed += d >= obs - 1e-15
        out[fam]={"accept_mean":statistics.mean(A),"reject_mean":statistics.mean(R),"mean_diff":statistics.mean(A)-statistics.mean(R),"permutation_p":(exceed+1)/(reps+1)}
    return out

def public_record(t:Task)->dict[str,Any]: return {"item_id":t.item_id,"source_text":t.source_text,"target_text":t.target_text,"public":t.public}
def hidden_record(t:Task)->dict[str,Any]:
    v=verify(t); return {"item_id":t.item_id,"family":t.family,"item_type":t.item_type,"perturbation":t.perturbation,"decision":v.decision.value,"verifier_trace":list(v.trace)}
def canonical_digest(records:Sequence[Mapping[str,Any]])->str:
    raw="\n".join(json.dumps(r,sort_keys=True,separators=(",",":")) for r in records)+"\n"; return hashlib.sha256(raw.encode()).hexdigest()

def development_receipt(seed:int=2026081201,n_per_cell:int=30)->dict[str,Any]:
    tasks=generate(seed,n_per_cell,True); gold={t.item_id:verify(t).decision for t in tasks}; threshold=fit_threshold(tasks,gold)
    primary=evaluate(tasks,threshold); twin=evaluate_twin(tasks,threshold); mechanism=evaluate(tasks,threshold,MECHANISM_ALIGNMENT_ABLATION); relational=evaluate(tasks,threshold,RELATIONAL_BASELINE_ABLATION)
    binary=binary_brier_development(tasks,threshold); q=arm_disagreement_fraction(tasks,threshold); required_decidable=required_n_for_mde(binary["sigma_d"],0.05); known_fraction=binary["n_decidable"]/len(tasks); required_total=math.ceil(required_decidable/max(known_fraction,1e-12))
    confirmatory_base=math.ceil(required_total/36); confirmatory_base=max(confirmatory_base+1,16); confirmatory_total=36*confirmatory_base
    return {"schema":"paper2-objective-track-a-dev-v1","seed":seed,"n":len(tasks),"n_per_cell":n_per_cell,"lexical_threshold":threshold,"primary":primary,"coordinate_ablated_twin":twin,"mechanism_alignment_control":mechanism,"relational_control":relational,"binary_brier_power":binary,"arm_disagreement_fraction_q":q,"required_decidable_n_mde_0_05":required_decidable,"required_total_n_from_observed_known_fraction":required_total,"confirmatory_n_per_cell_frozen":confirmatory_base,"confirmatory_total_n_frozen":confirmatory_total,"semantic_decorrelation":permutation_semantic_decorrelation(tasks,seed=seed+77,reps=4000),"blind_attacks":blind_attacks(tasks),"public_packet_sha256":canonical_digest([public_record(t) for t in tasks]),"hidden_packet_sha256":canonical_digest([hidden_record(t) for t in tasks]),"claim_boundary":"DEVELOPMENT_ONLY__CONFIRMATORY_OUTCOMES_NOT_ACCESSED"}
