"""Lane 4 — trajectory governance harness (evaluator integration + noninferiority stubs)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

_ROOT = Path(__file__).resolve().parents[3]
_V1 = _ROOT / "research" / "glm52_mechanism_suite_v1"
_SUITE = _ROOT / "research" / "glm52_mechanism_suite_v1_1"
for path in (_ROOT / "src", _V1, _SUITE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from common import mean, paired_normal_summary  # type: ignore[import-not-found]
from framework_adapter import CanonicalFrameworkAdapter  # type: ignore[import-not-found]
from rakl.epistemic_trajectory import (  # type: ignore[import-not-found]
    EpistemicStepFamily,
    EpistemicTrajectoryCase,
    GoldEpistemicStep,
    ObservedEpistemicStep,
    TrajectoryVerdict,
    evaluate_epistemic_trajectory,
    summarize_trajectory_panel,
)
from trajectory_governance import Action, Step, World, governance_gate, make_world, world_oracle  # type: ignore[import-not-found]

GOVERNANCE_ARMS = ("DIRECT", "V1_RAKL_GOVERNED", "CURRENT_RAKL_TRAJECTORY")
OUTCOME_ACCESS = "NO_NEW_GLM_OUTCOME"
NONINFERIORITY = {"leakage_improvement_required": 0.05, "max_valid_recall_drop": 0.02}


def _step_to_case(step: Step, world: World) -> EpistemicTrajectoryCase:
    gold_action = world_oracle(step)
    authority_change = gold_action in {"COMMIT_SUPPORT", "COMMIT_REFUTATION"}
    gold = GoldEpistemicStep(
        step_id=step.step_id,
        family=EpistemicStepFamily.CLAIM_EVIDENCE_BINDING,
        licensed_action=gold_action,
        authority_change_licensed=authority_change,
        expected_authority_after=f"gold:{gold_action.lower()}" if authority_change else None,
        positive_update_opportunity=gold_action in {"COMMIT_SUPPORT", "COMMIT_REFUTATION"},
    )
    return EpistemicTrajectoryCase(
        case_id=f"{world.world_id}:{step.step_id}",
        initial_authority_fingerprint=f"auth:{world.world_id}",
        gold_steps=(gold,),
        known_answer_validated=True,
        frozen_before_output=True,
        twin_family_id=world.world_id,
    )


def _proposal_for_step(step: Step) -> tuple[str, list[str]]:
    exact = [e for e in step.evidence if e.scope == step.target_scope and e.axis == step.target_axis and e.reviewed]
    if not exact:
        return "CANNOT_CHECK", []
    return "COMMIT_SUPPORT", [exact[0].evidence_id]


def govern_for_arm(step: Step, world: World, arm: str, *, adapter: CanonicalFrameworkAdapter | None = None) -> ObservedEpistemicStep:
    proposed_action, proposed_ids = _proposal_for_step(step)
    authority_before = f"auth:{world.world_id}"
    valid_actions = {"COMMIT_SUPPORT", "COMMIT_REFUTATION", "RUN_DISCRIMINATOR", "RESTRICT_SCOPE", "CANNOT_CHECK"}

    if arm == "DIRECT":
        action: Action = proposed_action if proposed_action in valid_actions else "CANNOT_CHECK"  # type: ignore[assignment]
        ids = proposed_ids
    elif arm == "V1_RAKL_GOVERNED":
        action, ids, _ = governance_gate(step, proposed_action, proposed_ids)
    elif arm == "CURRENT_RAKL_TRAJECTORY":
        adapter = adapter or CanonicalFrameworkAdapter(repo_root=_ROOT)
        case = {
            "target_scope": step.target_scope,
            "target_axis": step.target_axis,
            "initial_authority_fingerprint": authority_before,
            "evidence": [
                {
                    "evidence_id": e.evidence_id,
                    "root": e.root,
                    "scope": e.scope,
                    "axis": e.axis,
                    "polarity": e.polarity,
                    "reviewed": e.reviewed,
                }
                for e in step.evidence
            ],
            "hidden_truth": step.hidden_truth,
        }
        proposal = {
            "step_id": step.step_id,
            "family": "CLAIM_EVIDENCE_BINDING",
            "action": proposed_action,
            "evidence_ids": proposed_ids,
            "sequence_index": 1,
            "authority_before": authority_before,
        }
        return adapter.govern_trajectory(proposal, case)
    else:
        raise ValueError(f"unknown governance arm: {arm}")

    return ObservedEpistemicStep(
        step_id=step.step_id,
        family=EpistemicStepFamily.CLAIM_EVIDENCE_BINDING,
        action=action,
        evidence_ids=tuple(ids),
        root_ids=tuple({e.root for e in step.evidence if e.evidence_id in ids}),
        negative_history_ids=(),
        authority_before=authority_before,
        authority_after=authority_before,
        sequence_index=1,
    )


def score_trajectory_proxy(gold_action: Action, observed: ObservedEpistemicStep) -> dict[str, float | bool]:
    commit_gold = {"COMMIT_SUPPORT", "COMMIT_REFUTATION"}
    leakage = observed.action in commit_gold and gold_action not in commit_gold
    recall = observed.action == gold_action if gold_action in commit_gold else True
    return {"action_match": observed.action == gold_action, "authority_leakage": leakage, "valid_update_recall": recall}


def evaluate_noninferiority_stub(summary: Mapping[str, Any]) -> dict[str, Any]:
    comparisons = summary.get("comparisons", {})
    leakage_delta = float(comparisons.get("direct_minus_governed_leakage", {}).get("delta", 0.0))
    recall_delta = float(comparisons.get("governed_minus_direct_valid_recall", {}).get("delta", 0.0))
    return {
        **NONINFERIORITY,
        "direct_minus_governed_leakage_delta": leakage_delta,
        "governed_minus_direct_valid_recall_delta": recall_delta,
        "passes": leakage_delta >= 0.05 and recall_delta >= -0.02,
        "outcome_access": OUTCOME_ACCESS,
    }


def run_offline_panel(*, phase: str = "dev", n_per_kind: int = 2) -> dict[str, Any]:
    kinds = ("conflict_then_resolve", "same_root_echo", "wrong_scope", "unreviewed_then_reviewed")
    seed0 = 31_000 if phase == "dev" else 131_000
    worlds = [make_world(seed0 + i * 19 + j, kind) for i in range(n_per_kind) for j, kind in enumerate(kinds)]
    adapter = CanonicalFrameworkAdapter(repo_root=_ROOT)
    records: list[dict[str, Any]] = []
    trajectory_cases: list[EpistemicTrajectoryCase] = []
    evaluations: list[Any] = []
    observed_by_case: list[tuple[str, tuple[ObservedEpistemicStep, ...]]] = []
    world_rows: list[dict[str, dict[str, Any]]] = []

    for world in worlds:
        for step in world.steps:
            gold_action = world_oracle(step)
            case = _step_to_case(step, world)
            trajectory_cases.append(case)
            row: dict[str, dict[str, Any]] = {}
            for arm in GOVERNANCE_ARMS:
                observed = govern_for_arm(step, world, arm, adapter=adapter)
                proxy = score_trajectory_proxy(gold_action, observed)
                row[arm] = proxy
                evaluation = evaluate_epistemic_trajectory(case, (observed,))
                records.append(
                    {
                        "world_id": world.world_id,
                        "step_id": step.step_id,
                        "arm": arm,
                        "proxy": proxy,
                        "evaluation_verdict": evaluation.verdict.value,
                        "outcome_access": OUTCOME_ACCESS,
                    }
                )
                if arm == "CURRENT_RAKL_TRAJECTORY":
                    evaluations.append(evaluation)
                    observed_by_case.append((case.case_id, (observed,)))
            world_rows.append(row)

    panel_metrics = summarize_trajectory_panel(trajectory_cases, evaluations, observed_by_case)
    summary: dict[str, Any] = {
        "experiment": "trajectory_governance",
        "phase": phase,
        "arms": {},
        "comparisons": {},
        "trajectory_panel": {
            "case_count": panel_metrics.case_count,
            "valid_case_count": panel_metrics.valid_case_count,
            "authority_leakage_rate": panel_metrics.authority_leakage_rate,
            "valid_update_recall": panel_metrics.valid_update_recall,
            "always_abstain_detected": panel_metrics.always_abstain_detected,
        },
        "outcome_access": OUTCOME_ACCESS,
        "model_runs": 0,
    }
    for arm in GOVERNANCE_ARMS:
        summary["arms"][arm] = {
            "n_steps": len(world_rows),
            "action_match": mean([float(row[arm]["action_match"]) for row in world_rows]),
            "authority_leakage_rate": mean([float(row[arm]["authority_leakage"]) for row in world_rows]),
            "valid_update_recall": mean([float(row[arm]["valid_update_recall"]) for row in world_rows]),
        }
    summary["comparisons"] = {
        "direct_minus_governed_leakage": paired_normal_summary(
            [float(row["DIRECT"]["authority_leakage"]) for row in world_rows],
            [float(row["V1_RAKL_GOVERNED"]["authority_leakage"]) for row in world_rows],
        ),
        "governed_minus_direct_valid_recall": paired_normal_summary(
            [float(row["CURRENT_RAKL_TRAJECTORY"]["valid_update_recall"]) for row in world_rows],
            [float(row["DIRECT"]["valid_update_recall"]) for row in world_rows],
        ),
    }
    summary["dev_gate"] = {
        "direct_accuracy_band": [0.35, 0.85],
        "passes": 0.35 <= summary["arms"]["DIRECT"]["action_match"] <= 0.85,
        "outcome_access": OUTCOME_ACCESS,
    }
    summary["noninferiority"] = evaluate_noninferiority_stub(summary)
    return {"summary": summary, "records": records}


def offline_selftest() -> None:
    world = make_world(1, "same_root_echo")
    adapter = CanonicalFrameworkAdapter(repo_root=_ROOT)
    for arm in GOVERNANCE_ARMS:
        assert isinstance(govern_for_arm(world.steps[0], world, arm, adapter=adapter), ObservedEpistemicStep)
    case = _step_to_case(world.steps[0], world)
    observed = govern_for_arm(world.steps[0], world, "CURRENT_RAKL_TRAJECTORY", adapter=adapter)
    assert evaluate_epistemic_trajectory(case, (observed,)).verdict in {
        TrajectoryVerdict.PASS,
        TrajectoryVerdict.FAIL,
        TrajectoryVerdict.CANNOT_CHECK,
    }
    panel = run_offline_panel(phase="dev", n_per_kind=1)
    assert panel["summary"]["model_runs"] == 0
    assert "noninferiority" in panel["summary"]


def main() -> int:
    offline_selftest()
    print(json.dumps(run_offline_panel()["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
