from __future__ import annotations

from rakl.math_research_api import (
    MathResearchRecord,
    ProblemSignature,
    ProofDAG,
    StrategyMotif,
    plan_math_research,
    publication_ready,
)


def test_public_facade_supports_minimal_planning_workflow() -> None:
    signature = ProblemSignature(domain="mathematics", goal_type="prove theorem")
    record = MathResearchRecord(claim_id="C")
    plan = plan_math_research(signature=signature, record=record)
    assert plan.candidate_paths
    assert not publication_ready(record)
    assert ProofDAG().nodes == ()
    assert StrategyMotif("m", ("formalize_target",)).motif_id == "m"
