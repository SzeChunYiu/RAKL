# src/rakl module assignment — refactor plan (2026-08-14)

285 top-level modules + 3 subpackages (metrics/, schemas/, training_ladder/) = 288 units.
All assigned; `rakl/_unassigned` unused. Seeds from the two audits preserved verbatim.
Machine-readable map: `module_assignment.json` (same directory).

## Summary counts per target
| Target | n | | Target | n |
|---|---|---|---|---|
| rakl/studies | 67 | | rakl/solver/retrieval | 9 |
| rakl/governance | 24 | | rakl/solver/residual | 8 |
| rakl/solver/verification | 20 | | rakl/solver/contract | 7 |
| rakl/core | 18 | | rakl/orion/challenger_evaluation | 7 |
| rakl/solver/navigation | 18 | | rakl/solver/saturation | 6 |
| rakl/runtime | 16 | | rakl/solver/structuralization | 6 |
| rakl/orion/self_evolution | 15 | | rakl/solver/transport | 6 |
| rakl/solver/composition | 14 | | rakl/orion/operator_acquisition | 6 |
| rakl/orion/policy_learning | 10 | | rakl/orion/episode_memory | 5 |
| rakl/solver/knowledge_space | 10 | | rakl/orion/experience_analysis | 5 |
| rakl/orion/promotion | 4 | | rakl/orion/lesson_learning | 3 |
| rakl/solver/decomposition | 3 | | rakl (root __init__) | 1 |

Confidence: 166 high / 118 medium / 4 low
(low: controlled_witness_extraction, prepolymarket, unified_solver_registry, neural_structural_contract).

## Top-20 riskiest moves (importer count)
v3_authority 17 (core) · experience_substrate 15 (episode_memory) · formalism 12 (core) ·
paper3_annotation 12 (governance — NOT studies: obstruction_transformation_corpus imports it) ·
authority_ledger 11 (core) · structural_types 9 (structuralization) · evolution_trace 8 (self_evolution) ·
problem_solving_algebra 8 (decomposition) · semantic_shortcut 8 (retrieval) · canonical_commitment 7 (core) ·
core 7 (core) · failure_lattice 7 (residual) · invention 7 (contract) · issue_closeout_stubs 6 (studies) ·
matched_microtrial 6 (challenger_evaluation) · paper2_pendulum_microtrial 6 (studies) · problem_fibre 6 (contract) ·
research_tool_inventory 6 (contract seed pkg) · training_projection 6 (policy_learning) · typed_lattice 6 (knowledge_space).

## Path-pinned modules: 200 of 288
`src/rakl/<name>.py` literals appear in other files' content (skills/rakl-core/manifest.yaml
invention_resources, docs/, research/ ledgers, tests). Any physical move must add
compat shims or rewrite those pointers; full referrer map in `path_refs.json`.

## Non-obvious calls (rule 3 applied via importer checks)
- paper3_annotation → governance: imported by 12 modules incl. framework retrieval corpus.
- matched_microtrial → challenger_evaluation: imported by framework v3_metrology, defines
  matched-ceiling trial design; shared_with studies.
- invention_benchmark → composition: imported by invention_api (framework facade).
- issue_closeout_stubs + 6 alias stubs, all *_benchmark/panel/alr/ablation/closeout,
  epistemic_benchmark, structural_benchmark, rakl_cycle_metrics → studies (importers are studies-only).
- Invention engine family (formalism excepted) → composition: constructive_lattice, invention_api,
  invention_runtime, mechanism_compiler, symbolic_discovery, solver_compilation.
- RSHEA chain split per seeds: adapters/controllers → self_evolution; observability_reports,
  governed-gate surfaces (agent_authority_gateway, pre_action_receipt, application_feedback,
  authority_chokepoint, publication_gate, release_manifest, repository_boundary) → governance.
- metrics/ → experience_analysis (Orion KPI layer; shared_with governance);
  schemas/ → governance (only content: application-feedback bundle schema);
  training_ladder/ → policy_learning (training-time #461 scaffold with training_projection).

## Shared-tension modules (single home chosen, `shared_with` recorded): 31
Largest tensions: core↔governance (v3_authority, subject_identity, framework_ladder),
contract↔verification (hard_gates), residual↔experience_analysis (failure_lattice),
policy_learning↔self_evolution (epistemic_evolution), self_evolution↔governance (observability_adapters).
