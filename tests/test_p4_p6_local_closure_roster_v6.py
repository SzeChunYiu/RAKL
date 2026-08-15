from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROSTER=ROOT/'research'/'self_rakl_p4_p6_question_saturation_v8'/'LOCAL_CLOSURE_ROSTER_V6.json'
def _roster(): return json.loads(ROSTER.read_text(encoding='utf-8'))
def test_canonical_controller_roster_is_scoped_and_nonsovereign():
    d=_roster(); assert d['status']=='FROZEN_FOR_CANONICAL_CONTROLLER_EXACT_HEAD_CLOSURE'; assert d['global_completeness_claimed'] is False; assert d['grants_scientific_authority'] is False; assert d['grants_publication_authority'] is False; assert d['historical_api_rule'].strip(); assert d['publication_rule'].strip(); assert d['local_trust_root_boundary'].strip()
def test_every_canonical_local_artifact_exists():
    missing=[(x['id'],x['artifact']) for x in _roster()['local_obligations'] if not (ROOT/x['artifact']).is_file()]; assert missing==[]
def test_final_roster_uses_canonical_controller_and_strict_paper5_facade():
    items={x['id']:x['artifact'] for x in _roster()['local_obligations']}; assert items['P5-STRICT-PROMOTION-FACADE']=='src/rakl/math_research_promotion_strict.py'; assert items['P6-STRICT-EVOLUTION-FACADE-V5']=='src/rakl/meta_evolution_v5.py'; assert items['P6-CANONICAL-SELF-EVOLUTION-CONTROLLER']=='src/rakl/self_evolution_controller.py'; assert items['P6-CANONICAL-CONTROLLER-TEST']=='tests/test_self_evolution_controller.py'
def test_external_science_remains_open_or_blocked_by_scientific_predecessor():
    ext={x['id']:x for x in _roster()['external_obligations']}; assert ext['P4-Q1-INCREMENTAL-INFORMATION']['status']=='OPEN_EXTERNAL'; assert ext['P4-Q2-FIVE-ARM-PHASE2']['status']=='OPEN_EXTERNAL'; assert ext['P4-Q3-TRAIN-INFERENCE-IDENTITY']['status']=='BLOCKED_ON_Q2'; assert ext['P4-GENERALIZATION']['status']=='BLOCKED_ON_Q2'; assert ext['P5-PUBLIC-RESEARCH-PERFORMANCE']['status']=='OPEN_EXTERNAL'; assert ext['P5-CONCRETE-NOVELTY-AND-VALUE']['status']=='OPEN_EXTERNAL'; assert ext['P6-EXTERNAL-AGENT-EPOCH1-EPOCH2']['status']=='OPEN_EXTERNAL'
def test_exact_head_closure_requires_all_current_workflows():
    w=set(_roster()['required_exact_head_workflows']); assert {'test','paper5-formal-assurance','paper5-strict-current-publication','paper5-verified-discovery-release','publication-pdfs','active-packet-registry','p4-scheduler-promotion','p4-adaptive-receipt-admission','p4-phase2-execution-provenance-v1','p1-p4-claim-frontier-regression','trusted-parent-evaluator'}<=w
