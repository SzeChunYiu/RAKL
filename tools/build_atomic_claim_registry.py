#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "research" / "unified_problem_solving_v1" / "results"
OUT = RES / "ATOMIC_CLAIM_REGISTRY.json"
CUTOFF = "9a9b1ced"
CUTOFF_TIME = "2026-08-13T16:48:58Z"

def load(p):
    with open(p) as f:
        return json.load(f)

def sha_prefix(p, n=16):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:n]

gate = load(RES / "PROMOTION_GATE.json")
ledger = load(RES / "CLOSURE_LEDGER.json")
pfc = load(RES / "PAPER_FRAMEWORK_CONSISTENCY.json")

NETBEN = {
 "navigation_dynamics": {
   "claim_id": "EMP-NAV-NETBENEFIT",
   "paper_owner": "paper-06-rakl-scientific-research-engine",
   "claim": "Flow/diffusion path-integral navigation yields net node-expansion savings over A* at matched iteration cost.",
   "baseline": "A* (strong control)",
   "falsifier": "After a fair crossover (defect-free diffusion, construction cost charged), no graph-size x heuristic-quality x reuse-count cell has a net-expansions-vs-A* CI excluding 0 in the method's favor.",
   "terminal_state": "NEGATIVE", "open": False, "owner_issue": "#519",
   "terminal_scope": "DECISIVE: hard-coded diffusion defect fixed and a fair crossover rerun across graph-size x heuristic-quality x reuse-count; path-integral still loses to A* in every cell (mean -364.4, CI [-538.8,-210.0], n=18). The fix made it MORE negative (the old defect was accidentally helping the method). Method valid; no net-benefit regime found. Lane #519 closed.",
   "code": ["src/rakl/navigation_dynamics.py", "research/unified_problem_solving_v1/navigation_dynamics_experiment.py"]},
 "field_construction": {
   "claim_id": "EMP-FIELDCONST-NETBENEFIT",
   "paper_owner": "paper-06-rakl-scientific-research-engine",
   "claim": "Reachability-grounded field construction pays for its build cost via amortized search savings over repeated queries.",
   "baseline": "unaided search (no field)",
   "falsifier": "No query-count threshold exists at which cumulative search saving exceeds one-time construction cost; amortization crossover absent.",
   "terminal_state": "NEGATIVE", "open": False, "owner_issue": "#520",
   "terminal_scope": "DECISIVE: with reachability-grounded landmarks (exact backward BFS from the goal condition) and 100 repeated queries, build cost (mean 37.09) exceeds cumulative saving (mean -37.38); crossover fraction 0.0. Method is valid; economics negative. Lane #520 closed.",
   "code": ["src/rakl/field_construction.py", "research/unified_problem_solving_v1/run_field_construction.py"]},
 "fieldability_given_field": {
   "claim_id": "EMP-FIELDABILITY-GIVEN",
   "paper_owner": "paper-06-rakl-scientific-research-engine",
   "claim": "Given a supplied metric field, fieldability discriminates solvable from unsolvable instances above chance.",
   "baseline": "chance / no-field",
   "falsifier": "net fieldability advantage CI includes 0 on the given-field benchmark.",
   "terminal_state": "SUPPORTED", "open": False, "owner_issue": "#466",
   "terminal_scope": "Given-metric field only (net +0.7247, CI [0.712,0.7375], n=400); construction cost not applicable (field supplied by domain). Does NOT support the construction claim, which is NEGATIVE (see EMP-FIELDCONST-NETBENEFIT).",
   "code": ["src/rakl/fieldability.py", "research/unified_problem_solving_v1/field_hypothesis_experiment.py"]},
 "mechanic_diagnosis": {
   "claim_id": "EMP-DIAG-HONESTY",
   "paper_owner": "paper-06-rakl-scientific-research-engine",
   "claim": "The diagnosis mechanic degrades to ambiguity rather than confident error on uncertain causes (verdict honesty), discriminating causes from raw telemetry non-circularly.",
   "baseline": "confident wrong labeling",
   "falsifier": "forced-wrong rate CI includes the confident-error baseline, or signal-name lookup reconstructs the cause table (circularity).",
   "terminal_state": "CANNOT_CHECK", "open": True, "owner_issue": "#523",
   "terminal_scope": "CI unavailable at cutoff (rate 0.0, degenerate interval). #523 suspects INVALID_CONTAMINATED: pre-classified signal names feed a deterministic cause table (circular at noise 0). Raw-telemetry redesign in flight.",
   "code": ["src/rakl/mechanic_diagnosis.py", "research/unified_problem_solving_v1/diagnosis_accuracy_experiment.py"]},
}

NETBEN.update({
 "tcsq_sq3": {
   "claim_id": "EMP-TCSQ-NETBENEFIT",
   "paper_owner": "paper-04-verified-discovery",
   "claim": "Typed Canonical Semantic Quotient (SQ-3) yields net solver/cost advantage over unquotiented RAW after construction+validation+projection+reconstruction+verification are charged.",
   "baseline": "RAW (unquotiented)",
   "falsifier": "net cost advantage CI includes 0 across redundancy/solver-cost cells, or oracle quotient still loses to RAW (economics, not semantics).",
   "terminal_state": "NEGATIVE", "open": True, "owner_issue": "#521",
   "terminal_scope": "Strongly negative in tested regime (mean -4074, CI [-5333,-2879], n=6 cells). Root-cause in flight (#521): stage-cost decomposition plus an oracle-quotient test to separate quotient semantics from verification/bookkeeping overhead.",
   "code": ["src/rakl/semantic_quotient.py", "research/tcsq_sq3_v1/run_sq3.py"]},
 "path_equivalence_quotient": {
   "claim_id": "EMP-PATHQ-NETBENEFIT",
   "paper_owner": "paper-06-rakl-scientific-research-engine",
   "claim": "The path-equivalence quotient yields net search savings after witness/certification cost, with a regime-conditional crossover.",
   "baseline": "unquotiented search",
   "falsifier": "no certification-cost x commutation cell has a net-saving CI excluding 0 in the quotient's favor.",
   "terminal_state": "PARTIAL", "open": False, "owner_issue": "#522",
   "terminal_scope": "GENUINE CROSSOVER: quotient WINS for k=5,6 with moderate-high commutation (positive subset net +194.2, CI [+57.9,+357.0]) and LOSES for k=3,4 where certification cost dominates; overall net +70.2 CI [+4.7,+145.1]. Full phase diagram published, no hidden cells. Lane #522 closed. Gate reads the top-level net and PROMOTEs on the overall mean, but the honest scientific state is regime-conditional PARTIAL, not a uniform win.",
   "code": ["src/rakl/structural_types.py", "research/unified_problem_solving_v1/path_quotient_experiment.py"]},
 "six_family_law": {
   "claim_id": "EMP-SIXFAMILY-GENERALIZATION",
   "paper_owner": "paper-02-structural-mechanics",
   "claim": "The structural law generalizes across at least 6 independent families in the predicted direction (cross-family sign test).",
   "baseline": "random direction (p=0.5 per family)",
   "falsifier": "sign-test p >= 0.05 (too few families in the predicted direction).",
   "terminal_state": "SUPPORTED", "open": False, "owner_issue": "#515", "underpowered": True,
   "terminal_scope": "Sign test p=0.03125, count_met (5/5 tested families positive). Modest: n=5 is the minimum for one-sided significance, so UNDERPOWERED for smaller effects. Generalization holds at this resolution only.",
   "code": ["src/rakl/structural_types.py", "research/six_family_extension_v1/run_six_family.py"]},
 "identity_reuse": {
   "claim_id": "EMP-IDENTITYREUSE",
   "paper_owner": "paper-03-identity",
   "claim": "Exact structural identity reuse saves re-derivation cost versus reconstructing semantically-equivalent-but-independent structure, with stale-reuse error rate held at 0.",
   "baseline": "re-derivation (no reuse)",
   "falsifier": "stale-reuse error rate > 0 (hard constraint violated) or net reuse advantage CI includes 0.",
   "terminal_state": "SUPPORTED", "open": False, "owner_issue": "#467",
   "terminal_scope": "Constructed benchmark: net +700, CI degenerate (deterministic), n=200, stale-reuse error 0. Real-model/runtime generalization is a SEPARATE unrun claim (EMP-REAL-IDENTITY / #532, SCAFFOLD).",
   "code": ["src/rakl/subject_identity.py", "src/rakl/structural_identity_bridge.py", "research/identity_reuse_v1/run_identity_reuse.py"]},
})

SCAFFOLDS = [
 {"claim_id": "MATH-CANONICAL-COMMITMENT", "claim_type": "theorem", "mechanic": "canonical_commitment",
  "paper_owner": "paper-02-structural-mechanics", "experiment_owner_issue": "#530", "open": True,
  "claim": "Typed canonical encoding is deterministic and context-independent (exact Decimal, exact binary64 bit preservation, cycle/unsupported-type rejection, domain separation).",
  "falsifier": "A finite input with two distinct canonical encodings, or a binary64 value whose bits are not preserved across the round trip.",
  "code": ["src/rakl/semantic_quotient.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Search tiny finite counterexamples first; mechanize load-bearing results in Lean (#530)."},
 {"claim_id": "MATH-TCSQ-SOUNDNESS", "claim_type": "theorem", "mechanic": "tcsq",
  "paper_owner": "paper-04-verified-discovery", "experiment_owner_issue": "#530", "open": True,
  "claim": "TCSQ projection/reconstruction preserves the solution set (sound); a quotient that drops a valid solution or admits an invalid one falsifies it.",
  "falsifier": "A quotient class that loses a true solution or gains a spurious one under projection/reconstruction.",
  "code": ["src/rakl/semantic_quotient.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Mechanize soundness of projection/reconstruction; pair with the resolved-validation gate (#530)."},
 {"claim_id": "MATH-VTG-CONTRACTS", "claim_type": "theorem", "mechanic": "verified_transformation_geometry",
  "paper_owner": "paper-05-verified-discovery-in-mathematics", "experiment_owner_issue": "#530", "open": True,
  "claim": "Typed VTG abstraction contracts (exact/sound/empirical; operational subject identity; reachability quantifiers) are internally consistent.",
  "falsifier": "A contract pair that contradicts, or a reachability-under-operators result that diverges from intended mathematical possibility.",
  "code": ["src/rakl/verified_transformation_geometry.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Audit every theorem-like statement; tiny finite counterexamples first (#530)."},
 {"claim_id": "ML-STRUCTURAL-RESIDUAL", "claim_type": "ml_representation", "mechanic": "neural_structural_bridge",
  "paper_owner": "paper-03-directional-witness", "experiment_owner_issue": "#526", "open": True,
  "claim": "Explicit TCSQ plus directional-witness semantics beats the strongest matched conditional-metric and asymmetric relational/causal parents on fresh domains, QoI flips and hostile boundary near-misses (Cut 2).",
  "falsifier": "A matched parent matches or beats the RAKL residual on held-out domains / QoI flips / near-misses.",
  "code": [], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Preregistered, unexecuted. Required plots: ROC/PR, calibration, direction reversal, boundary/QoI severity, leave-family-out, error taxonomy (#526)."},
 {"claim_id": "ML-TRAINING-SIGNAL", "claim_type": "ml_representation", "mechanic": "training_ladder",
  "paper_owner": "paper-04-verified-discovery", "experiment_owner_issue": "#527", "open": True,
  "claim": "A corrected Phase-1 v2 learner signal yields a checkpoint-dependent structural residual that survives (Cut 3).",
  "falsifier": "No checkpoint-dependent structural residual survives the corrected Phase-1 v2 rerun.",
  "code": ["src/rakl/driver_learning.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Learning curves, structural mastery trajectories, adaptive-vs-static, forgetting, OOD, model-scale curves (#527). A100 ladder re-harvest pending (~Aug 14-15)."},
 {"claim_id": "ML-VTG-LOCAL-GEOMETRY", "claim_type": "systems", "mechanic": "verified_transformation_geometry",
  "paper_owner": "paper-05-verified-discovery-in-mathematics", "experiment_owner_issue": "#528", "open": True,
  "claim": "Local/bounded VTG navigation is useful on held-out Lean theorem families versus best-first/A*/MCTS/equality-saturation at matched cost (Cut 5/6).",
  "falsifier": "No useful local geometry in registered scope; primary failure terminal NO_USEFUL_LOCAL_GEOMETRY_IN_REGISTERED_SCOPE.",
  "code": ["src/rakl/verified_transformation_geometry.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Construct the bounded verifier-defined formal universe first; only add dynamics if local geometry survives (#528)."},
 {"claim_id": "EMP-REAL-IDENTITY", "claim_type": "ml_representation", "mechanic": "identity_reuse",
  "paper_owner": "paper-03-identity", "experiment_owner_issue": "#532", "open": True,
  "claim": "Exact structural identity reuse yields a benefit in a real model/runtime test versus reconstructed/semantic alternatives (Cut 4).",
  "falsifier": "Exact reuse is indistinguishable from semantic reconstruction at runtime (exact reuse is then provenance discipline only).",
  "code": ["src/rakl/subject_identity.py"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Real-model/runtime test; distinct from the constructed-benchmark SUPPORTED claim EMP-IDENTITYREUSE (#532)."},
 {"claim_id": "META-COGNITIVE-COMPILATION", "claim_type": "ml_representation", "mechanic": "cognitive_compilation",
  "paper_owner": "paper-04-verified-discovery", "experiment_owner_issue": "#530", "open": True,
  "claim": "Typed structural diagnosis then bounded update then disjoint fresh assurance beats generic reflection/distillation, failure-example fine-tuning, textual skill compilation, matched random update and no update (Cut 7).",
  "falsifier": "A generic baseline matches the typed-pipeline residual.",
  "code": [], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Preregistered, unexecuted. Training cannot move pi_epi; fresh assurance separated from proposal/training."},
 {"claim_id": "SYS-CAPSTONE", "claim_type": "systems", "mechanic": "integrated_system",
  "paper_owner": "paper-06-rakl-scientific-research-engine", "experiment_owner_issue": "#525", "open": True,
  "claim": "The integrated RAKL system beats substantially simpler matched agent/research baselines at matched model, evidence cutoff, compute, wall-time and human-review budget (Cut 8).",
  "falsifier": "A simpler baseline matches RAKL on verified success/safety/compute/latency/memory/cost.",
  "code": [], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Full system plus ablations vs matched strong baselines; Pareto and scaling plots (#525). Complexity justified only by a measurable residual."},
 {"claim_id": "SYS-REPRO", "claim_type": "meta_reproducibility", "mechanic": "n/a",
  "paper_owner": "I-VI", "experiment_owner_issue": "#531", "open": True,
  "claim": "Frozen inputs, raw outputs, analysis, figures, environment, commands, seeds and hashes reproduce in a clean environment.",
  "falsifier": "A receipt that does not regenerate from the frozen bundle in a clean env.",
  "code": [], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Freeze and reproduce end-to-end in a clean environment (#531)."},
 {"claim_id": "META-PAPER-ALIGNMENT", "claim_type": "meta_paper", "mechanic": "n/a",
  "paper_owner": "I-VI", "experiment_owner_issue": "#533", "open": True,
  "claim": "Every quantitative sentence in Papers I-VI maps to an artifact; stale or unsupported claims removed; negative results preserved.",
  "falsifier": "A quantitative sentence with no artifact, or a stale/unsupported claim remaining in a manuscript.",
  "code": ["paper/arxiv/main.tex"], "terminal_state": "SCAFFOLD",
  "terminal_scope": "Update manuscripts only from validated receipts (#533), after evidence lands."},
]

claims = []

# (A) net-benefit / empirical claims from the gate.
for key, cand in gate["candidates"].items():
    meta = NETBEN.get(key)
    if not meta:
        meta = {"claim_id": "EMP-" + key.upper(), "claim": "[unmapped candidate - add judgement]",
                "terminal_state": "CANNOT_CHECK", "open": True, "paper_owner": "unassigned",
                "baseline": "", "falsifier": "", "code": [], "owner_issue": "",
                "terminal_scope": ""}
    rec = {
        "claim_id": meta["claim_id"], "mechanic": key, "paper_owner": meta["paper_owner"],
        "claim": meta["claim"], "claim_type": "empirical_net_benefit",
        "code": meta["code"], "experiment_owner_issue": meta["owner_issue"],
        "baseline": meta["baseline"], "falsifier": meta["falsifier"],
        "promotion_verdict": cand.get("verdict"), "result": cand.get("net"),
        "artifact": cand.get("artifact") or "", "terminal_state": meta["terminal_state"],
        "terminal_scope": meta["terminal_scope"], "open": meta["open"],
    }
    if cand.get("artifact"):
        p = REPO / cand["artifact"]
        rec["artifact_sha256_prefix"] = sha_prefix(p) if p.exists() else "MISSING"
    if meta.get("underpowered"):
        rec["underpowered"] = True
    claims.append(rec)

# (B) implementation-closure claims from the ledger.
for mkey, m in ledger["mechanics"].items():
    paper_paths = m.get("paper", {}).get("paths", [])
    claims.append({
        "claim_id": "IMPL-" + mkey.upper(), "mechanic": mkey,
        "paper_owner": paper_paths[0] if paper_paths else "unassigned",
        "claim": "Mechanic %s is implemented, tested, has evidence and a paper owner at cutoff; its registered open question is the falsifier." % mkey,
        "claim_type": "implementation_closure",
        "code": m.get("impl", {}).get("paths", []),
        "tests": m.get("tests", {}).get("paths", []),
        "evidence": m.get("evidence", {}).get("paths", []),
        "falsifier": (m.get("open_question") or [""])[0],
        "terminal_state": "ARCHITECTURE_ONLY", "open": True,
        "terminal_scope": "Closed at cutoff = impl+tests+evidence+paper+openQ present. Architecture-complete; confirmatory net-benefit (where it exists) is a separate claim. Does not confer scientific authority.",
    })

# (C) wave-2 scaffolds.
for s in SCAFFOLDS:
    rec = dict(s)
    rec.setdefault("claim_type", "scaffold")
    rec["baseline"] = rec.get("baseline", "")
    rec["result"] = {}
    rec["artifact"] = ""
    claims.append(rec)

# (D) paper-framework consistency meta-claim.
pfc_path = RES / "PAPER_FRAMEWORK_CONSISTENCY.json"
claims.append({
    "claim_id": "META-PAPER-CONSISTENCY", "mechanic": "n/a", "paper_owner": "I-VI",
    "claim": "Papers I-VI are internally consistent with the implemented framework: every mechanic has a module and owner, no paper claim lacks a module, no numeric drift.",
    "claim_type": "meta_consistency",
    "baseline": "D1 mechanic-without-owner / D2 paper-claim-missing-module / D3 number-drift == 0",
    "falsifier": "Any nonempty D1/D2/D3 finding on re-audit.",
    "result": {"checked_mechanics": pfc["checked_mechanics"], "checked_numbers": pfc["checked_numbers"],
               "verdict": pfc["verdict"], "findings": pfc["findings"]},
    "artifact": str(pfc_path.relative_to(REPO)), "artifact_sha256_prefix": sha_prefix(pfc_path),
    "terminal_state": "SUPPORTED", "open": False,
    "terminal_scope": "Mechanical consistency check passes (CONSISTENT). Consistency is not correctness and not scientific authority.",
})

registry = {
    "schema_version": "orion-atomic-claim-registry-v1",
    "generated_at_cutoff": CUTOFF, "generated_at_cutoff_time": CUTOFF_TIME,
    "grants_scientific_authority": False, "global_completeness_claimed": False,
    "policy": "One record per distinct claim; implementation-closure and net-benefit are separate claims. promotion_verdict is engineering routing status ONLY; terminal_state is the scientific state. A decisive NEGATIVE counts as successful scientific closure. Single-writer: maintained centrally; lanes report terminals and the integrator re-runs this.",
    "terminal_vocabulary": ["SUPPORTED", "PARTIAL", "NEGATIVE", "CANNOT_CHECK", "UNDERPOWERED",
                            "INVALID_CONTAMINATED", "ARCHITECTURE_ONLY", "SCAFFOLD"],
    "source_artifacts": {
        "promotion_gate": {"path": str((RES / "PROMOTION_GATE.json").relative_to(REPO)), "sha256_prefix": sha_prefix(RES / "PROMOTION_GATE.json")},
        "closure_ledger": {"path": str((RES / "CLOSURE_LEDGER.json").relative_to(REPO)), "sha256_prefix": sha_prefix(RES / "CLOSURE_LEDGER.json")},
        "paper_framework_consistency": {"path": str(pfc_path.relative_to(REPO)), "sha256_prefix": sha_prefix(pfc_path)},
    },
    "summary": {
        "total_claims": len(claims),
        "by_terminal": {},
        "open": sum(1 for c in claims if c.get("open")),
    },
}
for c in claims:
    registry["summary"]["by_terminal"].setdefault(c["terminal_state"], 0)
    registry["summary"]["by_terminal"][c["terminal_state"]] += 1
registry["claims"] = claims

with open(OUT, "w") as f:
    json.dump(registry, f, indent=2)
print("wrote", OUT)
print("total_claims", len(claims), "by_terminal", registry["summary"]["by_terminal"])
