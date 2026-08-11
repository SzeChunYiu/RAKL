from __future__ import annotations

from rakl.math_research_api import (
    ContextGateVerdict,
    MathResearchRecord,
    ProblemSignature,
    ProofDAG,
    StrategyMotif,
    plan_math_research,
    publication_ready,
)


def test_public_facade_blocks_candidate_planning_until_context_exists() -> None:
    signature = ProblemSignature(domain="mathematics", goal_type="prove theorem")
    record = MathResearchRecord(claim_id="C")
    plan = plan_math_research(signature=signature, record=record)
    assert plan.context_gate.verdict is ContextGateVerdict.CANNOT_CHECK
    assert not plan.candidate_generation_allowed
    assert not plan.candidate_paths
    assert plan.pre_candidate_actions
    assert not publication_ready(record)
    assert ProofDAG().nodes == ()
    assert StrategyMotif("m", ("formalize_target",)).motif_id == "m"
