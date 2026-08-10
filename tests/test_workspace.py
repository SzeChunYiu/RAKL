from rakl.workspace import (
    CognitiveProvenanceEdge,
    EvidentialProvenanceEdge,
    WorkspaceCandidate,
    WorkspaceGatePolicy,
    WorkspaceIntervention,
    WorkspaceInterventionKind,
    WorkspacePartition,
    coactivation_pairs,
    gate_workspace,
    intervene_candidates,
    proposals_from_workspace,
)


def _candidates():
    return (
        WorkspaceCandidate("core", "claim:core", WorkspacePartition.CORE, 100, ("synth",)),
        WorkspaceCandidate("challenge", "claim:challenge", WorkspacePartition.CHALLENGE, 5, ("critic",)),
        WorkspaceCandidate("novel", "claim:novel", WorkspacePartition.NOVEL, 4, ("search",)),
        WorkspaceCandidate("history", "claim:history", WorkspacePartition.HISTORY, 3, ("critic",)),
        WorkspaceCandidate("core-2", "claim:core-2", WorkspacePartition.CORE, 90, ("synth",)),
    )


def test_gate_reserves_adversarial_novel_and_history_capacity():
    frame = gate_workspace(_candidates(), WorkspaceGatePolicy(capacity=4))
    assert {"challenge", "novel", "history"}.issubset(frame.selected_item_ids)
    assert "core" in frame.selected_item_ids
    assert "core-2" not in frame.selected_item_ids


def test_gate_fails_closed_when_reserved_partition_is_absent():
    candidates = tuple(item for item in _candidates() if item.partition is not WorkspacePartition.CHALLENGE)
    try:
        gate_workspace(candidates, WorkspaceGatePolicy(capacity=4))
    except ValueError as error:
        assert "CHALLENGE" in str(error)
    else:
        raise AssertionError("missing challenge reservation should fail closed")


def test_workspace_broadcast_yields_proposals_not_authority_updates():
    frame = gate_workspace(_candidates(), WorkspaceGatePolicy(capacity=4))
    proposals = proposals_from_workspace(
        frame,
        {
            "core:synth": "candidate synthesis",
            "challenge:critic": "candidate objection",
            "novel:search": "candidate search route",
            "history:critic": "candidate negative-history warning",
        },
    )
    assert {proposal.target_operator for proposal in proposals} == {"synth", "critic", "search"}
    assert not hasattr(frame, "authority")
    assert all(not hasattr(proposal, "authority") for proposal in proposals)


def test_coactivation_is_not_a_compatibility_or_gluing_witness():
    frame = gate_workspace(_candidates(), WorkspaceGatePolicy(capacity=4))
    pairs = coactivation_pairs(frame)
    assert frozenset(("core", "challenge")) in pairs
    assert all(isinstance(pair, frozenset) for pair in pairs)
    assert not hasattr(frame, "compatibility")
    assert not hasattr(frame, "gluing")


def test_workspace_interventions_change_computational_candidates_only():
    dropped = intervene_candidates(
        _candidates(),
        WorkspaceIntervention(WorkspaceInterventionKind.DROP, "core"),
    )
    assert "core" not in {item.item_id for item in dropped}

    reweighted = intervene_candidates(
        _candidates(),
        WorkspaceIntervention(
            WorkspaceInterventionKind.REWEIGHT,
            "challenge",
            weight_multiplier=100.0,
        ),
    )
    challenge = next(item for item in reweighted if item.item_id == "challenge")
    assert challenge.priority == 500.0


def test_cognitive_and_evidential_provenance_are_distinct_types():
    cognitive = CognitiveProvenanceEdge("core", "proposal:core:synth", "drop:history")
    evidential = EvidentialProvenanceEdge("source:1", "claim:1", "verify:1")
    assert type(cognitive) is not type(evidential)
    assert not hasattr(cognitive, "evidence_id")
    assert not hasattr(evidential, "source_item_id")
