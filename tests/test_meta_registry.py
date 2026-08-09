from rakl.meta_registry import *

H1 = "a" * 64
H2 = "b" * 64


def d(fid, q="q", src="s", h=H1, seq=1, sup=()):
    return MetaFiberDefinition(fid, q, src, h, seq, supersedes=sup)


def r(fid, rid="r", src="rs", h=H1, seq=1):
    return MetaFiberReference(rid, fid, src, h, seq)


def a(srcfid, tgtfid, aid="a1", src="as", h=H1, seq=1, frozen=True):
    return FiberAlias(aid, srcfid, tgtfid, src, h, seq, frozen)


def kinds(report):
    return {i.kind for i in report.issues if not i.resolved}


def test_unique_consistent():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA"), d("META_N002_BETA", src="s2")), (r("META_N001_ALPHA"),))
    assert z.verdict == RegistryVerdict.CONSISTENT and z.eligible_for_saturation_bookkeeping


def test_slot_collision():
    z = reconcile_meta_fiber_registry((d("META_N101_OLD"), d("META_N101_NEW", src="s2")))
    assert z.verdict == RegistryVerdict.CONFLICTED and RegistryIssueKind.NAMESPACE_SLOT_COLLISION in kinds(z)


def test_definition_conflict():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA", "q1"), d("META_N001_ALPHA", "q2", src="s2")))
    assert RegistryIssueKind.DEFINITION_CONFLICT in kinds(z)


def test_orphan():
    assert RegistryIssueKind.ORPHAN_REFERENCE in kinds(reconcile_meta_fiber_registry((d("META_N001_ALPHA"),), (r("META_N002_BETA"),)))


def test_identical_duplicate_idempotent():
    assert reconcile_meta_fiber_registry((d("META_N001_ALPHA"), d("META_N001_ALPHA"))).verdict == RegistryVerdict.CONSISTENT


def test_source_identity_conflict():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA", h=H1), d("META_N002_BETA", src="s", h=H2)))
    assert RegistryIssueKind.SOURCE_IDENTITY_CONFLICT in kinds(z)


def test_supersession_cycle():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA", sup=("META_N002_BETA",)), d("META_N002_BETA", src="s2", sup=("META_N001_ALPHA",))))
    assert RegistryIssueKind.SUPERSESSION_CYCLE in kinds(z)


def test_alias_target_orphan():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA"),), aliases=(a("META_N001_ALPHA", "META_N002_BETA"),))
    assert RegistryIssueKind.ALIAS_TARGET_ORPHAN in kinds(z)


def test_alias_cycle():
    defs = (d("META_N001_ALPHA"), d("META_N002_BETA", src="s2"))
    z = reconcile_meta_fiber_registry(defs, aliases=(a("META_N001_ALPHA", "META_N002_BETA", "a1"), a("META_N002_BETA", "META_N001_ALPHA", "a2", src="as2")))
    assert RegistryIssueKind.ALIAS_CYCLE in kinds(z)


def test_alias_chronology_unknown():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA"), d("META_N002_BETA", src="s2")), aliases=(a("META_N001_ALPHA", "META_N002_BETA", frozen=None),))
    assert z.verdict == RegistryVerdict.CANNOT_CHECK


def test_posthoc_alias_invalid():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA"), d("META_N002_BETA", src="s2")), aliases=(a("META_N001_ALPHA", "META_N002_BETA", frozen=False),))
    assert z.verdict == RegistryVerdict.TRIAL_INVALID


def test_semantic_similarity_does_not_merge():
    z = reconcile_meta_fiber_registry((d("META_N001_APPLE", "shared mechanism"), d("META_N002_BANANA", "shared mechanism", src="s2")))
    assert z.verdict == RegistryVerdict.CONSISTENT and dict(z.canonical_id_map)["META_N001_APPLE"] == "META_N001_APPLE"


def test_explicit_renumber_resolves_slot_collision_and_preserves_history():
    defs = (d("META_N101_OLD", "old"), d("META_N101_NEW", "new", src="new"), d("META_N108_NEW", "new", src="recon"))
    z = reconcile_meta_fiber_registry(defs, aliases=(a("META_N101_NEW", "META_N108_NEW", "rename", src="recon-alias"),))
    assert z.verdict == RegistryVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    issue = [i for i in z.issues if i.kind == RegistryIssueKind.NAMESPACE_SLOT_COLLISION][0]
    assert issue.resolved and dict(z.canonical_id_map)["META_N101_NEW"] == "META_N108_NEW"
    assert not z.grants_scientific_authority and not z.establishes_framework_saturation


def test_permutation_deterministic():
    defs = (d("META_N002_BETA", src="b"), d("META_N001_ALPHA", src="a"))
    assert reconcile_meta_fiber_registry(defs) == reconcile_meta_fiber_registry(tuple(reversed(defs)))


def test_current_round_collision_detects_six_slots():
    old = [
        "META_N101_METACOGNITIVE_METHOD_COMPLETENESS", "META_N102_CONCEPTUAL_BASIS_INDEPENDENCE", "META_N103_TRIGGERED_REFLECTION_POLICY",
        "META_N104_EXPLANATION_DEPTH_CHALLENGE", "META_N105_DOMAIN_SCOPED_METACOG_CALIBRATION", "META_N106_HELD_OUT_MISSING_OPERATOR_DISCOVERY",
    ]
    new = [
        "META_N101_COMPRESSION_RECONSTRUCTION_UNDERSTANDING", "META_N102_COUNTERFACTUAL_MENTAL_SIMULATION", "META_N103_EXPERIENCE_TO_PROCEDURAL_ABILITY",
        "META_N104_MEASUREMENT_INSTRUMENT_COGNITION", "META_N105_HIERARCHICAL_RESEARCH_PROGRAM_CONTROL", "META_N106_SOCIAL_EPISTEMIC_ROUTING",
    ]
    defs = tuple(d(fid, fid, src=f"s{i}") for i, fid in enumerate(old + new))
    z = reconcile_meta_fiber_registry(defs)
    slots = {i.subject for i in z.issues if i.kind == RegistryIssueKind.NAMESPACE_SLOT_COLLISION and not i.resolved}
    assert slots == {f"META_N{i:03d}" for i in range(101, 107)} and not z.eligible_for_saturation_bookkeeping


def test_current_round_collision_can_be_explicitly_reconciled():
    old = [
        "META_N101_METACOGNITIVE_METHOD_COMPLETENESS", "META_N102_CONCEPTUAL_BASIS_INDEPENDENCE", "META_N103_TRIGGERED_REFLECTION_POLICY",
        "META_N104_EXPLANATION_DEPTH_CHALLENGE", "META_N105_DOMAIN_SCOPED_METACOG_CALIBRATION", "META_N106_HELD_OUT_MISSING_OPERATOR_DISCOVERY",
    ]
    new = [
        "META_N101_COMPRESSION_RECONSTRUCTION_UNDERSTANDING", "META_N102_COUNTERFACTUAL_MENTAL_SIMULATION", "META_N103_EXPERIENCE_TO_PROCEDURAL_ABILITY",
        "META_N104_MEASUREMENT_INSTRUMENT_COGNITION", "META_N105_HIERARCHICAL_RESEARCH_PROGRAM_CONTROL", "META_N106_SOCIAL_EPISTEMIC_ROUTING",
    ]
    targets = [
        "META_N108_COMPRESSION_RECONSTRUCTION_UNDERSTANDING", "META_N109_COUNTERFACTUAL_MENTAL_SIMULATION", "META_N110_EXPERIENCE_TO_PROCEDURAL_ABILITY",
        "META_N111_MEASUREMENT_INSTRUMENT_COGNITION", "META_N112_HIERARCHICAL_RESEARCH_PROGRAM_CONTROL", "META_N113_SOCIAL_EPISTEMIC_ROUTING",
    ]
    defs = []
    aliases = []
    for i, fid in enumerate(old):
        defs.append(d(fid, fid, src=f"o{i}"))
    for i, (fid, tgt) in enumerate(zip(new, targets)):
        defs.extend([d(fid, fid, src=f"n{i}"), d(tgt, fid, src=f"t{i}")])
        aliases.append(a(fid, tgt, aid=f"rename-{i}", src=f"a{i}"))
    z = reconcile_meta_fiber_registry(tuple(defs), aliases=tuple(aliases))
    assert z.verdict == RegistryVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY and z.eligible_for_saturation_bookkeeping
    assert all(i.resolved for i in z.issues if i.kind == RegistryIssueKind.NAMESPACE_SLOT_COLLISION)


def test_authority_never_escalates():
    z = reconcile_meta_fiber_registry((d("META_N001_ALPHA"),))
    assert not z.grants_scientific_authority and not z.grants_method_authority and not z.grants_target_authority and not z.establishes_framework_saturation


def test_invalid_id_is_trial_invalid():
    assert reconcile_meta_fiber_registry((d("BAD_ID"),)).verdict == RegistryVerdict.TRIAL_INVALID


def test_invalid_hash_is_cannot_check():
    assert reconcile_meta_fiber_registry((d("META_N001_ALPHA", h="bad"),)).verdict == RegistryVerdict.CANNOT_CHECK
