from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Iterable, Tuple

from rakl.experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes
from rakl.trajectory_lesson_induction import (
    TrajectoryInductionVerdict,
    induce_candidate_lesson_from_trajectory,
)

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "research" / "paper3_trajectory_lesson_induction_v1" / "PROTOCOL.json"


@dataclass(frozen=True)
class Case:
    case_id: str
    family: str
    episodes: Tuple[TaskEpisode, ...]
    gold_verdict: str
    gold_action: str | None
    gold_negative_count: int
    gold_boundary_count: int

    @property
    def gold_signature(self) -> tuple:
        return (
            self.gold_verdict,
            self.gold_action,
            self.gold_negative_count,
            self.gold_boundary_count,
        )


def _episode(
    token: str,
    ordinal: int,
    *,
    action: str = "JUMP",
    outcome: EpisodeOutcome = EpisodeOutcome.SUCCESS,
    context: str = "ctx-main",
    signature: tuple[str, ...] = ("obstruction-main", "qoi-main"),
    verified: bool = True,
    residual: tuple[str, ...] = (),
    tamper_after_hash: bool = False,
) -> TaskEpisode:
    draft = TaskEpisode(
        episode_id=f"{token}-ep-{ordinal}",
        task_id=f"{token}-task-{ordinal}",
        atom_id="atom-main",
        context_hash=context,
        problem_signature=signature,
        fibre_snapshot_hash=sha256(f"{token}:fibre:{ordinal}".encode()).hexdigest(),
        operator_ids=("operator-a",),
        action_trace=(action,),
        observation_ids=(f"{token}-obs-{ordinal}",),
        verification_ids=((f"{token}-verification-{ordinal}",) if verified else ()),
        outcome=outcome,
        residual_signature=residual,
        evidence_pointers=(f"{token}-evidence-{ordinal}",),
        artifact_hash="",
        timestamp=f"2026-08-14T{ordinal % 20:02d}:{(ordinal * 3) % 60:02d}:00+00:00",
    )
    exact = replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())
    return replace(exact, context_hash="ctx-tampered") if tamper_after_hash else exact


def _case(token: str, family: str, episodes: Iterable[TaskEpisode], *, candidate: bool, action: str | None = "JUMP") -> Case:
    rows = tuple(episodes)
    negatives = sum(item.outcome is not EpisodeOutcome.SUCCESS for item in rows)
    boundaries = len({r for item in rows if item.outcome is not EpisodeOutcome.SUCCESS for r in item.residual_signature})
    return Case(
        case_id=token,
        family=family,
        episodes=rows,
        gold_verdict="INDUCED_CANDIDATE" if candidate else "CANNOT_CHECK",
        gold_action=action if candidate else None,
        gold_negative_count=negatives,
        gold_boundary_count=boundaries,
    )


def _pair(family: str, i: int) -> tuple[Case, Case]:
    t = f"{family[:7]}-{i:03d}"
    s1 = _episode(t + "a", 1)
    s2 = _episode(t + "a", 2)
    if family == "CONSISTENT_VERIFIED_SUCCESS_INDUCES_CANDIDATE":
        return _case(t+"A",family,(s1,s2),candidate=True), _case(t+"B",family,(s1,replace(s2,verification_ids=())),candidate=False)
    if family in {"SAME_ACTION_UNVERIFIED_BLOCKS", "MISSING_VERIFICATION_ID_BLOCK"}:
        u2 = _episode(t+"b",2,verified=False)
        return _case(t+"A",family,(_episode(t+"b",1),u2),candidate=False), _case(t+"B",family,(_episode(t+"c",1),_episode(t+"c",2)),candidate=True)
    if family == "MIXED_ACTIONS_BLOCK":
        bad=(_episode(t+"d",1,action="A"),_episode(t+"d",2,action="A"),_episode(t+"d",3,action="B"),_episode(t+"d",4,action="B"))
        good=(_episode(t+"e",1,action="A"),_episode(t+"e",2,action="A"))
        return _case(t+"A",family,bad,candidate=False), _case(t+"B",family,good,candidate=True,action="A")
    if family == "SAME_ACTION_FAILURE_CONTRADICTS":
        bad=(_episode(t+"f",1),_episode(t+"f",2),_episode(t+"f",3,outcome=EpisodeOutcome.FAILURE,residual=("same-action-failed",)))
        good=(_episode(t+"g",1),_episode(t+"g",2),_episode(t+"g",3,action="OLD",outcome=EpisodeOutcome.FAILURE,residual=("old-action-failed",)))
        return _case(t+"A",family,bad,candidate=False), _case(t+"B",family,good,candidate=True)
    if family in {"CONTEXT_MISMATCH_BLOCK", "MULTIPLE_CONTEXTS_REQUIRE_CANNOT_CHECK"}:
        bad=(_episode(t+"h",1),_episode(t+"h",2,context="ctx-other"))
        good=(_episode(t+"i",1),_episode(t+"i",2))
        return _case(t+"A",family,bad,candidate=False), _case(t+"B",family,good,candidate=True)
    if family == "PROBLEM_SIGNATURE_MISMATCH_BLOCK":
        bad=(_episode(t+"j",1),_episode(t+"j",2,signature=("other-obstruction","qoi-main")))
        good=(_episode(t+"k",1),_episode(t+"k",2))
        return _case(t+"A",family,bad,candidate=False), _case(t+"B",family,good,candidate=True)
    if family == "RESIDUAL_BOUNDARY_SPLITS_SCOPE":
        bounded=(_episode(t+"l",1),_episode(t+"l",2),_episode(t+"l",3,action="OLD",outcome=EpisodeOutcome.PARTIAL_SUCCESS,residual=("boundary-x",)))
        clean=(_episode(t+"m",1),_episode(t+"m",2))
        return _case(t+"A",family,bounded,candidate=True), _case(t+"B",family,clean,candidate=True)
    if family == "STALE_ARTIFACT_IDENTITY_BLOCK":
        bad=(_episode(t+"n",1),_episode(t+"n",2,tamper_after_hash=True))
        good=(_episode(t+"o",1),_episode(t+"o",2))
        return _case(t+"A",family,bad,candidate=False), _case(t+"B",family,good,candidate=True)
    if family == "NEGATIVE_HISTORY_MUST_BE_RETAINED":
        neg=(_episode(t+"p",1,action="OLD",outcome=EpisodeOutcome.FAILURE,residual=("old-bound",)),_episode(t+"p",2),_episode(t+"p",3))
        clean=(_episode(t+"q",1),_episode(t+"q",2))
        return _case(t+"A",family,neg,candidate=True), _case(t+"B",family,clean,candidate=True)
    if family == "SUCCESSOR_ACTION_AFTER_FAILURE":
        good=(_episode(t+"r",1,action="OLD",outcome=EpisodeOutcome.FAILURE,residual=("old-failed",)),_episode(t+"r",2,action="NEW"),_episode(t+"r",3,action="NEW"))
        bad=(_episode(t+"s",1,action="NEW",outcome=EpisodeOutcome.FAILURE,residual=("new-failed",)),_episode(t+"s",2,action="NEW"),_episode(t+"s",3,action="NEW"))
        return _case(t+"A",family,good,candidate=True,action="NEW"), _case(t+"B",family,bad,candidate=False)
    if family == "SINGLE_SUCCESS_INSUFFICIENT":
        one=(_episode(t+"t",1),)
        two=(_episode(t+"u",1),_episode(t+"u",2))
        return _case(t+"A",family,one,candidate=False), _case(t+"B",family,two,candidate=True)
    if family == "PARTIAL_SUCCESS_NOT_FULL_SUPPORT":
        partial=(_episode(t+"v",1),_episode(t+"v",2,outcome=EpisodeOutcome.PARTIAL_SUCCESS,residual=("partial",)))
        full=(_episode(t+"w",1),_episode(t+"w",2))
        return _case(t+"A",family,partial,candidate=False), _case(t+"B",family,full,candidate=True)
    if family == "BLOCKED_EPISODE_NOT_NEGATIVE_PROOF":
        blocked=(_episode(t+"x",1),_episode(t+"x",2),_episode(t+"x",3,outcome=EpisodeOutcome.BLOCKED,residual=("resource",)))
        failed=(_episode(t+"y",1),_episode(t+"y",2),_episode(t+"y",3,outcome=EpisodeOutcome.FAILURE,residual=("failure",)))
        return _case(t+"A",family,blocked,candidate=True), _case(t+"B",family,failed,candidate=False)
    raise KeyError(family)


def _production(case: Case) -> tuple:
    report=induce_candidate_lesson_from_trajectory(case.episodes,lesson_id="lesson:"+case.case_id)
    action=report.candidate.action if report.candidate is not None else None
    return (report.verdict.value,action,len(report.negative_history_episode_ids),len(report.boundary_residuals))


def _action_counts(case: Case, *, successes_only: bool=False) -> Counter:
    rows=[ep for ep in case.episodes if (not successes_only or ep.outcome is EpisodeOutcome.SUCCESS)]
    return Counter(ep.action_trace[0] for ep in rows)


def _parent(case: Case, name: str) -> tuple:
    successes=[ep for ep in case.episodes if ep.outcome is EpisodeOutcome.SUCCESS]
    negatives=[ep for ep in case.episodes if ep.outcome is not EpisodeOutcome.SUCCESS]
    if name=="LAST_SUCCESS":
        return ("INDUCED_CANDIDATE",successes[-1].action_trace[0],0,0) if successes else ("CANNOT_CHECK",None,0,0)
    if name=="MAJORITY_ACTION":
        counts=_action_counts(case)
        action=sorted(counts, key=lambda a:(-counts[a],a))[0]
        return ("INDUCED_CANDIDATE",action,0,0)
    if name=="OUTCOME_FREQUENCY":
        positive=sum(ep.outcome in {EpisodeOutcome.SUCCESS,EpisodeOutcome.PARTIAL_SUCCESS} for ep in case.episodes)
        if positive >= max(1,len(case.episodes)-positive):
            counts=_action_counts(case,successes_only=True)
            action=sorted(counts,key=lambda a:(-counts[a],a))[0] if counts else case.episodes[-1].action_trace[0]
            return ("INDUCED_CANDIDATE",action,0,0)
        return ("CANNOT_CHECK",None,0,0)
    if name=="UNTYPED_COMMON_ACTION":
        counts=_action_counts(case,successes_only=True)
        if not counts:
            return ("CANNOT_CHECK",None,0,0)
        action=sorted(counts,key=lambda a:(-counts[a],a))[0]
        return ("INDUCED_CANDIDATE",action,0,0)
    raise KeyError(name)


def _info_ceiling(cases: list[Case], parent_names: tuple[str,...]) -> float:
    groups=defaultdict(list)
    for case in cases:
        projection=tuple(_parent(case,name) for name in parent_names)
        groups[projection].append(case.gold_signature)
    correct=0
    for labels in groups.values():
        counts=Counter(labels)
        correct += max(counts.values())
    return correct/len(cases)


def _mutated(case: Case, mutation: str) -> tuple:
    episodes=list(case.episodes)
    if mutation=="IGNORE_VERIFICATION":
        episodes=[replace(ep,verification_ids=ep.verification_ids or ("forged-verification",), artifact_hash="") for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) for ep in episodes]
    elif mutation=="IGNORE_CONTEXT":
        episodes=[replace(ep,context_hash="ctx-normalized",artifact_hash="") for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) for ep in episodes]
    elif mutation=="IGNORE_PROBLEM_SIGNATURE":
        episodes=[replace(ep,problem_signature=("normalized","qoi"),artifact_hash="") for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) for ep in episodes]
    elif mutation=="IGNORE_RESIDUAL_BOUNDARY":
        base=_production(case)
        return (base[0],base[1],base[2],0)
    elif mutation=="IGNORE_CONTRADICTION":
        episodes=[replace(ep,outcome=EpisodeOutcome.BLOCKED,residual_signature=ep.residual_signature or ("ignored-failure",),artifact_hash="") if ep.outcome is EpisodeOutcome.FAILURE else ep for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) if not ep.artifact_hash else ep for ep in episodes]
    elif mutation=="ALLOW_SINGLE_SUCCESS":
        successes=[ep for ep in episodes if ep.outcome is EpisodeOutcome.SUCCESS]
        if len(successes)==1:
            clone=replace(successes[0],episode_id=successes[0].episode_id+"-clone",task_id=successes[0].task_id+"-clone",timestamp="2026-08-14T19:59:00+00:00",artifact_hash="")
            clone=replace(clone,artifact_hash=sha256(episode_content_bytes(clone)).hexdigest())
            episodes.append(clone)
    elif mutation=="COUNT_PARTIAL_AS_SUCCESS":
        episodes=[replace(ep,outcome=EpisodeOutcome.SUCCESS,residual_signature=(),verification_ids=ep.verification_ids or ("partial-as-ver",),artifact_hash="") if ep.outcome is EpisodeOutcome.PARTIAL_SUCCESS else ep for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) if not ep.artifact_hash else ep for ep in episodes]
    elif mutation=="COUNT_BLOCKED_AS_REFUTATION":
        episodes=[replace(ep,outcome=EpisodeOutcome.FAILURE,artifact_hash="") if ep.outcome is EpisodeOutcome.BLOCKED else ep for ep in episodes]
        episodes=[replace(ep,artifact_hash=sha256(episode_content_bytes(ep)).hexdigest()) if not ep.artifact_hash else ep for ep in episodes]
    elif mutation=="DROP_NEGATIVE_HISTORY":
        base=_production(case)
        return (base[0],base[1],0,base[3])
    elif mutation=="OLD_FAILURE_SUPPRESSES_VERIFIED_SUCCESSOR":
        if any(ep.outcome is EpisodeOutcome.FAILURE for ep in episodes):
            return ("CANNOT_CHECK",None,len([ep for ep in episodes if ep.outcome is not EpisodeOutcome.SUCCESS]),len({r for ep in episodes if ep.outcome is not EpisodeOutcome.SUCCESS for r in ep.residual_signature}))
    report=induce_candidate_lesson_from_trajectory(tuple(episodes),lesson_id="mut:"+case.case_id)
    return (report.verdict.value,report.candidate.action if report.candidate else None,len(report.negative_history_episode_ids),len(report.boundary_residuals))


def run(outdir: Path) -> dict:
    protocol=json.loads(PROTOCOL.read_text())
    cases=[]
    for family in protocol["families"]:
        for i in range(int(protocol["pairs_per_family"])):
            cases.extend(_pair(family,i))
    exact=sum(_production(c)==c.gold_signature for c in cases)/len(cases)
    gold_cc=[c for c in cases if c.gold_verdict=="CANNOT_CHECK"]
    cc_recall=sum(_production(c)[0]=="CANNOT_CHECK" for c in gold_cc)/len(gold_cc)
    unsafe=sum(_production(c)[0]=="INDUCED_CANDIDATE" and c.gold_verdict=="CANNOT_CHECK" for c in cases)/len(cases)
    negative_cases=[c for c in cases if c.gold_negative_count>0]
    negative_recall=sum(_production(c)[2]==c.gold_negative_count for c in negative_cases)/len(negative_cases)
    parent_names=tuple(protocol["parents"])[0:4]
    parents={name:sum(_parent(c,name)==c.gold_signature for c in cases)/len(cases) for name in parent_names}
    ceiling=_info_ceiling(cases,parent_names)
    mutations={m:sum(_mutated(c,m)!=c.gold_signature for c in cases) for m in protocol["mutations"]}
    gates=protocol["hard_gates"]
    passed=(exact>=gates["typed_exact_min"] and unsafe<=gates["unsafe_candidate_max"] and cc_recall>=gates["cannot_check_recall_min"] and negative_recall>=gates["negative_history_recall_min"] and ceiling<=gates["strongest_parent_information_ceiling_max"] and all(v>0 for v in mutations.values()))
    receipt={
        "schema_version":"paper3-trajectory-lesson-induction-result-v1",
        "n_cases":len(cases),
        "n_families":len(protocol["families"]),
        "typed":{"exact":exact,"unsafe_candidate_rate":unsafe,"cannot_check_recall":cc_recall,"negative_history_recall":negative_recall},
        "parents":parents,
        "composite_simple_parent_information_ceiling":ceiling,
        "mutation_error_counts":mutations,
        "all_mutations_caught":all(v>0 for v in mutations.values()),
        "all_gates_pass":passed,
        "terminal":protocol["promotion_if_green"] if passed else "RSHEA_SUCCESSOR_REQUIRED",
        "scope":protocol["scope"],
        "composition_rule":protocol["composition_rule"],
        "grants_scientific_authority":False,
    }
    outdir.mkdir(parents=True,exist_ok=True)
    (outdir/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    return receipt


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--outdir",type=Path,required=True); args=ap.parse_args()
    result=run(args.outdir); raise SystemExit(0 if result["all_gates_pass"] else 1)


if __name__=="__main__": main()
