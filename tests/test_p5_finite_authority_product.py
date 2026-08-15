"""Exhaustive Boolean conformance test for Paper V's authority product."""
from itertools import product

COORDS = ("specification", "truth", "novelty", "value", "verifier_trust")

def _state(bits): return dict(zip(COORDS, bits, strict=True))
def _product_candidate_gate(s): return all(s[k] for k in ("specification","truth","novelty","verifier_trust"))
def _intended_claim_is_assured(s): return all(s[k] for k in ("specification","truth","verifier_trust"))
def _four_of_five_scalar_gate(s): return sum(s.values()) >= 4

def test_product_gate_never_promotes_missing_spec_truth_or_trust():
    promoted=[]; false_promotions=[]
    for bits in product((False,True), repeat=len(COORDS)):
        s=_state(bits)
        if _product_candidate_gate(s):
            promoted.append(s)
            if not _intended_claim_is_assured(s): false_promotions.append(s)
    assert len(promoted)==2
    assert false_promotions==[]

def test_four_of_five_scalarization_has_three_load_bearing_false_promotions():
    promoted=[]; false_promotions=[]
    for bits in product((False,True), repeat=len(COORDS)):
        s=_state(bits)
        if _four_of_five_scalar_gate(s):
            promoted.append(s)
            if not _intended_claim_is_assured(s): false_promotions.append(s)
    assert len(promoted)==6 and len(false_promotions)==3
    assert {k for s in false_promotions for k in COORDS if not s[k]} == {"specification","truth","verifier_trust"}

def test_truth_can_stay_fixed_while_novelty_decreases():
    before={k:True for k in COORDS}; after=dict(before, novelty=False)
    assert before["truth"] is after["truth"] is True
    assert before["novelty"] is True and after["novelty"] is False
    assert _product_candidate_gate(before) is True and _product_candidate_gate(after) is False
