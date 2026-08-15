from rakl.bounded_closure import ClosureVerdict, MechanicClosureRecord, assess_bounded_closure

def _closed(mid): return MechanicClosureRecord(mid,True,True,True,True,True)

def test_closure_is_registry_relative_not_global():
    records=(_closed("epistemic"),_closed("structural")); cert=assess_bounded_closure(records,subject_sha="abc123",cutoff="2026-08-15")
    assert cert.verdict is ClosureVerdict.CLOSED_AT_REGISTERED_CUTOFF
    assert cert.global_completeness_claimed is False and cert.grants_scientific_authority is False
    assert cert.valid_for(records) is True

def test_new_candidate_reopens_current_registry_without_rewriting_history():
    old=(_closed("epistemic"),_closed("structural")); cert=assess_bounded_closure(old,subject_sha="old",cutoff="c1")
    new=MechanicClosureRecord("new_mechanic",False,False,False,True,True); current=old+(new,); current_cert=assess_bounded_closure(current,subject_sha="new",cutoff="c2")
    assert cert.valid_for(current) is False
    assert current_cert.verdict is ClosureVerdict.OPEN_AT_REGISTERED_CUTOFF
    assert current_cert.closed_mechanic_ids == ("epistemic","structural")

def test_negative_terminal_can_close_bookkeeping_coordinate():
    cert=assess_bounded_closure((_closed("negative_net_benefit_mechanic"),),subject_sha="negative",cutoff="c")
    assert cert.verdict is ClosureVerdict.CLOSED_AT_REGISTERED_CUTOFF
