from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence
import hashlib, json

class GovernanceDecision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; RESTRICT="RESTRICT"; CANNOT_CHECK="CANNOT_CHECK"
class TransitionRequest(str, Enum):
    PROMOTE_CLAIM="PROMOTE_CLAIM"; PROMOTE_MECHANISM="PROMOTE_MECHANISM"; PROMOTE_IDENTIFICATION="PROMOTE_IDENTIFICATION"; PROMOTE_NOVELTY="PROMOTE_NOVELTY"; REACTIVATE_CLAIM="REACTIVATE_CLAIM"; SUPERSEDE_CLAIM="SUPERSEDE_CLAIM"; RESOLVE_CONTRADICTION="RESOLVE_CONTRADICTION"
class CaseKind(str, Enum):
    INVARIANCE="INVARIANCE"; DECISION_TWIN="DECISION_TWIN"; LEGITIMATE_UPDATE="LEGITIMATE_UPDATE"
class Architecture(str, Enum):
    TEXT_MEMORY_ONLY="TEXT_MEMORY_ONLY"; PROVENANCE_ONLY="PROVENANCE_ONLY"; SCALAR_CONFIDENCE="SCALAR_CONFIDENCE"; PAIRWISE_COMPATIBILITY_ONLY="PAIRWISE_COMPATIBILITY_ONLY"; MAJORITY_OR_REVIEWER_VOTE="MAJORITY_OR_REVIEWER_VOTE"; SIMPLE_TRANSACTIONAL_STATE="SIMPLE_TRANSACTIONAL_STATE"; ATMS_PROV_REVISION="ATMS_PROV_REVISION"; RAKL_TYPED_AUTHORITY="RAKL_TYPED_AUTHORITY"

BASE: Mapping[str,Any]={"retrieval_count":4,"text_salience":.82,"scalar_confidence":.78,"provenance_clean":True,"independent_roots":2,"pairwise_compatible":True,"global_gluing":True,"review_votes_for":4,"review_votes_against":1,"claim_active":True,"version":3,"evidence_support":"DIRECT","context_match":True,"qoi_match":True,"prediction_support":True,"mechanism_support":True,"identification_support":True,"workspace_only":False,"experience_only":False,"superseded":False,"truth_proved":True,"novelty_checked":True,"cannot_check":False,"negative_history_retained":True,"evidence_independence":"INDEPENDENT","superseding_evidence":True}
@dataclass(frozen=True)
class BenchmarkCase:
    case_id:str; family:str; kind:CaseKind; request:TransitionRequest; changes:tuple[tuple[str,Any],...]; gold:GovernanceDecision
    def state(self):
        out=dict(BASE); out.update(dict(self.changes)); out["request"]=self.request.value; return out

def C(i,f,k,r,c,g): return BenchmarkCase(i,f,k,r,tuple(c.items()),g)
I=CaseKind.INVARIANCE; D=CaseKind.DECISION_TWIN; L=CaseKind.LEGITIMATE_UPDATE
P=TransitionRequest.PROMOTE_CLAIM
ALLOW=GovernanceDecision.ALLOW; DENY=GovernanceDecision.DENY; RESTRICT=GovernanceDecision.RESTRICT; CC=GovernanceDecision.CANNOT_CHECK
CASES=(
C("I01_LOW_RETRIEVAL","RETRIEVAL_NONAUTHORITY",I,P,{"evidence_support":"NONE","retrieval_count":1},DENY),C("I01_HIGH_RETRIEVAL","RETRIEVAL_NONAUTHORITY",I,P,{"evidence_support":"NONE","retrieval_count":20},DENY),
C("I08_CANONICAL","WORKSPACE_NONAUTHORITY",I,P,{"evidence_support":"NONE","workspace_only":False},DENY),C("I08_WORKSPACE","WORKSPACE_NONAUTHORITY",I,P,{"evidence_support":"NONE","workspace_only":True},DENY),
C("I09_CANONICAL","EXPERIENCE_NONAUTHORITY",I,P,{"evidence_support":"NONE","experience_only":False},DENY),C("I09_EXPERIENCE","EXPERIENCE_NONAUTHORITY",I,P,{"evidence_support":"NONE","experience_only":True},DENY),
C("I10_STALE_ONCE","STALE_REACTIVATION",I,TransitionRequest.REACTIVATE_CLAIM,{"superseded":True,"retrieval_count":1},DENY),C("I10_STALE_REPEATED","STALE_REACTIVATION",I,TransitionRequest.REACTIVATE_CLAIM,{"superseded":True,"retrieval_count":20},DENY),
C("D02_WEAK","EVIDENCE_STRENGTH",D,P,{"evidence_support":"INDIRECT"},DENY),C("D02_DIRECT","EVIDENCE_STRENGTH",D,P,{"evidence_support":"DIRECT"},ALLOW),
C("D03_LOCAL_ONLY","HIGHER_ORDER_GLUING",D,P,{"global_gluing":False},DENY),C("D03_GLOBAL","HIGHER_ORDER_GLUING",D,P,{"global_gluing":True},ALLOW),
C("D04_MISMATCH","CONTEXT_MATCH",D,P,{"context_match":False},RESTRICT),C("D04_MATCH","CONTEXT_MATCH",D,P,{"context_match":True},ALLOW),
C("D05_CORRELATED","EVIDENCE_INDEPENDENCE",D,P,{"evidence_independence":"CORRELATED"},DENY),C("D05_INDEPENDENT","EVIDENCE_INDEPENDENCE",D,P,{"evidence_independence":"INDEPENDENT"},ALLOW),
C("D06_PREDICTION_ONLY","PREDICTION_VS_MECHANISM",D,TransitionRequest.PROMOTE_MECHANISM,{"mechanism_support":False},DENY),C("D06_MECHANISM","PREDICTION_VS_MECHANISM",D,TransitionRequest.PROMOTE_MECHANISM,{"mechanism_support":True},ALLOW),
C("D07_NONIDENTIFYING","MECHANISM_VS_IDENTIFICATION",D,TransitionRequest.PROMOTE_IDENTIFICATION,{"identification_support":False},RESTRICT),C("D07_IDENTIFYING","MECHANISM_VS_IDENTIFICATION",D,TransitionRequest.PROMOTE_IDENTIFICATION,{"identification_support":True},ALLOW),
C("D11_UNCHECKED_NOVELTY","TRUTH_VS_NOVELTY",D,TransitionRequest.PROMOTE_NOVELTY,{"novelty_checked":False},CC),C("D11_CHECKED_NOVELTY","TRUTH_VS_NOVELTY",D,TransitionRequest.PROMOTE_NOVELTY,{"novelty_checked":True},ALLOW),
C("D12_UNKNOWN","CANNOT_CHECK",D,P,{"cannot_check":True},CC),C("D12_RESOLVED","CANNOT_CHECK",D,P,{"cannot_check":False},ALLOW),
C("D13_HISTORY_DROPPED","NEGATIVE_HISTORY",D,TransitionRequest.RESOLVE_CONTRADICTION,{"negative_history_retained":False},DENY),C("D13_HISTORY_RETAINED","NEGATIVE_HISTORY",D,TransitionRequest.RESOLVE_CONTRADICTION,{"negative_history_retained":True},ALLOW),
C("D15_NO_SUPERSEDING_EVIDENCE","LEGITIMATE_SUPERSESSION",L,TransitionRequest.SUPERSEDE_CLAIM,{"superseding_evidence":False},DENY),C("D15_SUPERSEDING_EVIDENCE","LEGITIMATE_SUPERSESSION",L,TransitionRequest.SUPERSEDE_CLAIM,{"superseding_evidence":True},ALLOW))

VISIBILITY={
Architecture.TEXT_MEMORY_ONLY:frozenset({"request","retrieval_count","text_salience","scalar_confidence","claim_active","version"}),Architecture.PROVENANCE_ONLY:frozenset({"request","provenance_clean","independent_roots","evidence_independence","claim_active","version"}),Architecture.SCALAR_CONFIDENCE:frozenset({"request","scalar_confidence","claim_active","version"}),Architecture.PAIRWISE_COMPATIBILITY_ONLY:frozenset({"request","pairwise_compatible","claim_active","version"}),Architecture.MAJORITY_OR_REVIEWER_VOTE:frozenset({"request","review_votes_for","review_votes_against","claim_active","version"}),Architecture.SIMPLE_TRANSACTIONAL_STATE:frozenset({"request","claim_active","version","provenance_clean","independent_roots","superseded"}),Architecture.ATMS_PROV_REVISION:frozenset({"request","provenance_clean","independent_roots","evidence_independence","pairwise_compatible","global_gluing","context_match","claim_active","version","superseded","negative_history_retained","superseding_evidence"}),Architecture.RAKL_TYPED_AUTHORITY:frozenset(set(BASE)|{"request"})}
REGISTERED_AUTHORITY_BASIS=frozenset({"evidence_support","global_gluing","context_match","evidence_independence","mechanism_support","identification_support","novelty_checked","cannot_check","negative_history_retained","superseding_evidence"})

def _state(c,visible):
    s=c.state(); return tuple(sorted((k,json.dumps(s[k],sort_keys=True)) for k in visible))
def assert_gold_is_state_function(cases:Sequence[BenchmarkCase]=CASES):
    b=defaultdict(set)
    for c in cases: b[json.dumps(c.state(),sort_keys=True,separators=(",",":"))].add(c.gold)
    bad=[k for k,v in b.items() if len(v)>1]
    if bad: raise AssertionError(f"gold is not a function of substantive state+request for {len(bad)} state(s)")
def assert_no_family_label_visibility():
    for a,v in VISIBILITY.items():
        leak={"family","family_id","case_id","gold","answer"}&set(v)
        if leak: raise AssertionError(f"{a.value} sees answer-semantic labels: {sorted(leak)}")
@dataclass(frozen=True)
class Audit:
    architecture:Architecture; n_cases:int; distinct_projected_states:int; ambiguous_projected_states:int; identifiable_accuracy_upper_bound:float; unavoidable_error_lower_bound:float
def audit_architecture(a:Architecture,cases:Sequence[BenchmarkCase]=CASES):
    b=defaultdict(list)
    for c in cases:b[_state(c,VISIBILITY[a])].append(c)
    correct=0; amb=0
    for bucket in b.values():
        counts=Counter(c.gold for c in bucket); correct+=max(counts.values()); amb+=int(len(counts)>1)
    u=correct/len(cases); return Audit(a,len(cases),len(b),amb,u,1-u)
def _sufficient(basis):
    b=defaultdict(set); visible=frozenset(basis|{"request"})
    for c in CASES:b[_state(c,visible)].add(c.gold)
    return all(len(v)==1 for v in b.values())
def authority_basis_certificate():
    if not _sufficient(REGISTERED_AUTHORITY_BASIS):raise AssertionError("registered authority basis is not sufficient")
    n={c:not _sufficient(REGISTERED_AUTHORITY_BASIS-{c}) for c in sorted(REGISTERED_AUTHORITY_BASIS)}
    return {"basis":sorted(REGISTERED_AUTHORITY_BASIS),"size":len(REGISTERED_AUTHORITY_BASIS),"sufficient":True,"individually_necessary":n,"minimal_by_registered_twin_witnesses":all(n.values())}
def audit_all():
    assert_gold_is_state_function(); assert_no_family_label_visibility()
    audits={a.value:asdict(audit_architecture(a)) for a in Architecture}
    raw="\n".join(json.dumps({"case_id":c.case_id,"family":c.family,"kind":c.kind.value,"state":c.state(),"gold":c.gold.value},sort_keys=True,separators=(",",":")) for c in CASES)
    return {"schema":"paper1-epistemic-projection-v2","status":"DEVELOPMENT_KNOWN_WORLD_REPAIR","n_cases":len(CASES),"n_families":len({c.family for c in CASES}),"architectures":audits,"authority_basis":authority_basis_certificate(),"world_digest":hashlib.sha256(raw.encode()).hexdigest(),"v1_repair":{"family_id_removed_from_candidate_state":True,"transition_request_separated_from_governance_decision":True,"gold_is_function_of_substantive_state_and_request":True,"duplicate_evidence_twin_removed":True,"invariance_and_decision_twin_families_separated":True,"strong_parent_added":"ATMS_PROV_REVISION"},"claim_boundary":"Constructed representational result only. Behavioural and natural-domain evidence remain separate.","grants_scientific_authority":False}
