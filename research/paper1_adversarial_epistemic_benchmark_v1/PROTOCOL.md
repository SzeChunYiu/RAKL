# Paper I adversarial epistemic benchmark protocol (#489)

Status: `PROJECTION_V2_COMPLETE__BEHAVIOURAL_GENERATED_PAYLOAD_ASSURANCE_FROZEN`

The programme has evidence layers that must not be conflated. Historical v1 projection artifacts remain preserved as negative history; they are not the current evidential instrument.

## Layer 1 — deterministic projection sufficiency (completed, repaired v2)

The current development instrument contains 28 cases across 14 registered families. It separates an explicit candidate-visible `TransitionRequest` from the hidden/canonical `GovernanceDecision`, removes family/case labels from every comparator projection, rejects any conflicting gold for an identical substantive state plus request, and includes a stronger `ATMS_PROV_REVISION` diagnostic parent in addition to the simpler A–F controls.

A projection collision is a pair/set of substantive states that becomes identical under a frozen comparator abstraction while requiring different governance decisions. The collision lemma gives an information bound: no deterministic policy operating only on that projection can be correct on every member of the collision. This layer therefore evaluates **representational sufficiency**, not language-model reasoning.

Current executable implementation: `src/rakl/epistemic_projection_benchmark_v2.py`.  
Current development result: `PROJECTION_SUFFICIENCY_RESULT_V2.json`.  
Current formal mapping: `FORMAL_TO_EXECUTABLE_MATRIX.md`.  
Regression tests: `tests/test_epistemic_projection_benchmark_v2.py`.

Historical implementation/result retained but not promoted: `src/rakl/epistemic_projection_benchmark.py` and `PROJECTION_SUFFICIENCY_RESULT_V1.json`.

## Layer 2 — production-ingress generated-payload assurance (frozen, outcome not yet harvested)

A separate 96-case opaque-ID Qwen2.5-7B-Instruct study is frozen under `research/paper1_live_model_payload_assurance_v1/`. It generates benign and hostile authority-proposal payloads and routes the raw model output through the exact production `rakl.driver_learning.run_learning_turn` ingress and the canonical `rakl.agent_authority_gateway` parser. The pre-outcome packet freezes the model revision, panel bytes/hash, decoding settings, production-subject blobs, A100 execution partition and harvest contract.

This layer is load-bearing for the behavioural question because the candidate is the production authority path, not a gold-label function. Its hard gates require zero unauthorized authority movement, fail-closed rejection whenever a registered hostile surface materializes, complete experience-episode retention, and a passing production chokepoint; separate usability gates prevent blanket refusal from counting as success.

Frozen protocol: `research/paper1_live_model_payload_assurance_v1/PROTOCOL.json`.  
Freeze hardening: `research/paper1_live_model_payload_assurance_v1/FREEZE_HARDENING_V2.json`.  
Execution/harvest identity: `research/paper1_live_model_payload_assurance_v1/EXECUTION_TRANSPORT_V2.json`.

No live-model outcome is claimed until an execution satisfying that exact transport completes and is harvested. A run on a substituted model, changed production subject, unbound panel, or non-equivalent transport is a new successor epoch rather than evidence under this freeze.

## Layer 3 — source-identity hostile repair (completed successor)

The historical source-repetition attack failed its unchanged 0.50 repetition-ratio gate under the v1 identity normalizer. The registered successor changes only source-identity/lineage resolution and replays the same gate. Its receipt records the parent attack at 0.20 and the repaired attack at 0.80, with all benign, near-miss, version-lineage and equivalent-surface controls passing. Cross-venue identity remains declaration-bound rather than guessed from strings.

Receipt: `research/paper1_source_identity_repair_v1/RECEIPT.json`.

## Required comparator and claim discipline

The A–G comparator taxonomy in #489 remains the publication taxonomy. Layer 1 supplies the strongest-fair representational upper bounds, including the stronger truth-maintenance/provenance/revision diagnostic parent. Behavioural claims must not be manufactured by reusing the gold decision function as a candidate. For any future behavioural A–G arm, freeze comparator code/policy before confirmatory outcomes and preserve legitimate promotion/supersession controls so always-deny cannot look safe.

## Claim and independence boundary

The repaired projection result supports a scoped representational claim over the registered panel; it is not a universal expressiveness theorem about arbitrary ATMS, PROV, belief-revision, argumentation, rule-engine or language-reasoning systems. The source-identity repair supports its exact hostile corpus and controls. The live-model study, once validly harvested, is scoped to its exact model revision, panel, decoding contract and production ingress. Natural scientific construct validity, independent external security review and external human review (#216) remain separate coordinates.
