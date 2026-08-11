# Paper 5 implementation-status matrix

**Purpose:** prevent manuscript prose from conflating conceptual design, deployed v3 behavior, proposal-only Paper 5 instrumentation, and future assurance work.

Status vocabulary:

- `DEPLOYED_IMPLEMENTED` — code is on current RAKL `main` at the relevant evidence cutoff.
- `IMPLEMENTED_BUT_NOT_PROMOTION_HARDENED` — code exists, but authority-bearing evidence resolution is not strong enough for the claimed promotion path.
- `PAPER5_CHALLENGER_IMPLEMENTED` — implemented only on the Paper 5 draft/challenger branch; not canonical.
- `PROTOCOL_ONLY` — specified in docs/manuscript but no canonical executable enforcement yet.
- `PROSPECTIVE_EMPIRICAL` — requires future data/evaluation rather than more engineering prose.

| Surface | Status | What exists | What must not be claimed yet |
|---|---|---|---|
| `TaskEpisode` / `Lesson` experience substrate | DEPLOYED_IMPLEMENTED | immutable episodes, versioned lessons, typed substrate nodes/edges | that storing episodes improves fresh-task capability |
| experience consolidation | DEPLOYED_IMPLEMENTED | candidate/local/reusable/proof-backed consolidation classifier and lineage | that all reusable authority inputs are independently resolved by protected external evidence in every path |
| failure diagnosis revision | DEPLOYED_IMPLEMENTED | immutable diagnosis revisions, supported-boundary lesson construction | that observed failure automatically proves obstruction/impossibility |
| problem fibres | DEPLOYED_IMPLEMENTED | problem-conditioned knowledge/tool/episode/failure/motif/expertise compilation | that retrieval universe has complete cross-problem coverage |
| gluing reports | IMPLEMENTED_BUT_NOT_PROMOTION_HARDENED | coverage/interface compatibility, residuals, local/global distinction | promotion-grade global authority from caller-level `LocalSection.verified` without content-bound verification certificate |
| experience-conditioned routing | DEPLOYED_IMPLEMENTED | scoped operator/path ranking and motif induction | that experiential priors improve outcomes rather than merely change ordering |
| saturation vector | DEPLOYED_IMPLEMENTED | seven axes, independent-route flatness, residual reopening | absolute completeness or globally optimal stopping |
| RAKL-triviality/novelty classification | DEPLOYED_IMPLEMENTED | ancestry classes and zero-invention reports | that internal novelty labels are externally validated |
| unified substrate | DEPLOYED_IMPLEMENTED | common read-only overlay across experience, tools, failures, legacy knowledge fibres and evolution variants | that every repository artifact/store is automatically inside the measured/queryable universe |
| evolution archive | IMPLEMENTED_BUT_NOT_PROMOTION_HARDENED | challenger/assured/rejected/incumbent DAG and rollback targets | that `governance_approved: bool` is sufficient governance evidence |
| SelfEvolutionAssessor / bootstrap evaluator | IMPLEMENTED_BUT_NOT_PROMOTION_HARDENED | fail-closed classification from development/fresh-assurance/evaluator-separation/resource/history fields | that the assessor itself proves caller-supplied booleans such as evaluator separation, assurance blindness or lineage independence |
| `PromotionGate` | DEPLOYED_IMPLEMENTED | exact-candidate checks, protected-path/evaluator fingerprint, history, improvement and ref-state gates | that repository permissions/CI status sources are cryptographically impossible to spoof outside the assumed TCB |
| post-promotion attestation | DEPLOYED_IMPLEMENTED | active-main ancestry/content/exact-CI attestation classifier | that its boolean observations are self-resolving evidence rather than inputs from an external observer |
| v3 repeated-task experience benchmark | DEPLOYED_IMPLEMENTED | reset-vs-learning development/fresh transfer with state and resource validation | a global capability claim; property is hard-coded false |
| method-state manifest (`RAKL_VERSION.json`) | PAPER5_CHALLENGER_IMPLEMENTED | proposal-only method/package/constitution identity manifest | that the version manifest is canonical or self-promoting |
| upgrade protocol | PAPER5_CHALLENGER_IMPLEMENTED | detailed Class A/B/C proposal, evaluation, assurance, override, rollback and attestation rules | that every rule is enforced by current `main` |
| state/process metrology | PAPER5_CHALLENGER_IMPLEMENTED | explicit state scope, seven-axis growth, process telemetry, cost policy, public v3 API | that retained novelty is independently calibrated or that all historical agents emitted complete telemetry |
| four-arm causal attribution objects | PAPER5_CHALLENGER_IMPLEMENTED | MODEL_ONLY/RESET/SHAM/LEARNING arms, exact per-run state binding, state-leak validation, lift decomposition | any measured RAKL lift before the prospective experiment is run |
| process telemetry JSON schema | PAPER5_CHALLENGER_IMPLEMENTED | canonical method-surface enum, measurement-only record | that every current RAKL process automatically emits this record |
| quantified scheduled-agent receipts | OPERATIONAL_PROMPT_INSTRUMENTATION | active RAKL_math prompts require `RAKL_CYCLE_METRICS` | that every field is currently measurable or that prompt compliance is complete until artifacts are audited |
| cross-problem memory coverage receipt | PROTOCOL_ONLY | framework issue #119 and Paper 5 requirements | retrieval completeness/recall until bound indexes and receipts are implemented |
| content-bound governance attestation for v3 variant promotion | PROTOCOL_ONLY | target invariant and roadmap | strong autonomous/self-governed promotion |
| content-bound resolver for verification/review/proof IDs | PROTOCOL_ONLY | known hardening requirement | promotion authority from bare string IDs/booleans |
| promotion-grade gluing verification certificates | PROTOCOL_ONLY | known hardening requirement | theorem/root authority from local gluing booleans |
| machine-readable operator-override event | PROTOCOL_ONLY | documented override semantics | that current override history is automatically enforced rather than reconstructed from commits/prompts |
| state/schema migration framework | PROTOCOL_ONLY | compatibility/authority/rollback rules specified | seamless automatic migration across future method versions |
| independent semantic-novelty audit | PROSPECTIVE_EMPIRICAL | audit protocol v1 exists | externally validated seven-axis growth curves |
| four-arm attribution result | PROSPECTIVE_EMPIRICAL | preregistration design exists | static architecture, experience, content or total lift |
| fresh protected RAKL 3.1 assurance result | PROSPECTIVE_EMPIRICAL | existing SelfEvolution contracts + Paper 5 upgrade protocol | that any 3.1 challenger is better or should be incumbent |
| external peer review of Paper 5 | PROSPECTIVE_EMPIRICAL | same-session internal adversarial review ledger only | independent reviewer agreement or journal acceptance |

## Interpretation rule

A manuscript sentence may use `implements` only for `DEPLOYED_IMPLEMENTED` or clearly named `PAPER5_CHALLENGER_IMPLEMENTED` code, with branch scope explicit. It should use `proposes`, `specifies`, `preregisters`, or `requires` for protocol/prospective rows.

A repository merge can change deployment status. It does not automatically move a row from `PROSPECTIVE_EMPIRICAL` to validated evidence.