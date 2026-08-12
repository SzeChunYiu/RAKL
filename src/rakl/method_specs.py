from __future__ import annotations

from .formal_contracts import AuthorityEffect, MechanicContract


_SCOPE = (
    "object/fiber identity",
    "QoI/consumer",
    "population/scale/regime/time",
    "observation/measurement model",
    "assumptions/evidence cutoff",
)
_ASSUMPTIONS = (
    "authority and equivalence are scope-relative",
    "missing required evidence yields BLOCKED/CANNOT_CHECK rather than invented certainty",
)
_READ = ("A", "T", "V", "E", "U", "O", "F", "H-", "S", "G")
_WRITE = (
    "A:append_or_scoped_supersede",
    "T:append",
    "V:scoped_update",
    "E:append",
    "U:scoped_update",
    "O:append_or_resolve",
    "F:open_close_reopen",
    "H-:append",
    "S:update",
    "G:protected_read_or_governed_update",
)
_NONESC = (
    "representation/prediction cannot mint mechanism authority",
    "provenance/citation multiplicity cannot mint truth or independent evidence",
    "support-layer success cannot self-promote canonical knowledge",
    "scope/context changes require a new or translated certificate",
)
_FAILURE = (
    "REFUTED",
    "PARTIALLY_IDENTIFIED",
    "BLOCKED",
    "CANNOT_CHECK",
    "TRIAL_INVALID_or_domain_specific_failure",
    "transport/execution failure is not scientific refutation",
)
_INVARIANTS = (
    "LLM proposes; evidence governs",
    "negative history is preserved",
    "new native residual reopens the affected fiber",
    "same-context reflection is not independent review",
)


def _c(
    surface: str,
    obj: str,
    inputs: tuple[str, ...],
    outputs: tuple[str, ...],
    math: tuple[str, ...],
    impl: tuple[str, ...],
    tests: tuple[str, ...],
    empirical: tuple[str, ...],
    effect: AuthorityEffect = AuthorityEffect.SCOPED_CERTIFICATE_ONLY,
) -> MechanicContract:
    return MechanicContract(
        surface=surface,
        object=obj,
        inputs=inputs,
        outputs=outputs,
        scope_context=_SCOPE,
        assumptions=_ASSUMPTIONS,
        state_read_set=_READ,
        state_write_set=_WRITE,
        authority_effect=effect,
        non_escalation_rules=_NONESC,
        failure_semantics=_FAILURE,
        invariants=_INVARIANTS,
        mathematical_semantics=math,
        implementation_refs=impl,
        test_refs=tests,
        empirical_open_coordinates=empirical,
    )


METHOD_CONTRACTS = (
    _c("decomposition", "Recursive partition of an unresolved transformation into decision-relevant atomic fibers.",
       ("O", "Q", "gamma", "residual", "budget"), ("child fibers", "lineage", "recurse/stop"),
       ("f=(o_f,q_f,gamma_f,r_f,parent(f))", "rho(r,K_t) subseteq F_{t+1}"),
       ("src/rakl/core.py", "src/rakl/tree.py", "src/rakl/missing_operator.py"),
       ("tests/test_core.py", "tests/test_tree.py", "tests/test_missing_operator.py"),
       ("real hidden-facet decomposition utility",), AuthorityEffect.PROPOSAL_ONLY),
    _c("routing", "Selection of the next admissible method/operator family without granting authority.",
       ("active fiber", "residual class", "operator contracts", "availability/cost evidence"), ("candidate route", "block/CANNOT_CHECK", "rationale"),
       ("a*=argmax_{a in A_adm} U(a|K_t) subject to blocking invariants",),
       ("src/rakl/assimilation.py", "src/rakl/search_controller.py", "src/rakl/challenge_learning.py"),
       ("tests/test_assimilation.py", "tests/test_search_controller.py", "tests/test_challenge_learning.py"),
       ("matched real routing utility",), AuthorityEffect.PROPOSAL_ONLY),
    _c("search_query_generation", "Evidence-acquisition query generation targeted at active residuals.",
       ("fiber", "residual", "source universe", "query budget"), ("query candidates", "selected query", "provenance"),
       ("q*=argmax E[decision-relevant gain(q)]/Cost(q) when calibrated; otherwise use set-valued obstruction elimination",),
       ("src/rakl/search_controller.py", "src/rakl/tree.py"), ("tests/test_search_controller.py", "tests/test_tree.py"),
       ("real goal-robust query selection",), AuthorityEffect.PROPOSAL_ONLY),
    _c("source_selection_reliability", "Qualification of sources with identity and lineage dependence.",
       ("candidate sources", "claim/QoI", "metadata", "lineage graph"), ("qualified set", "identity records", "dependence warnings"),
       ("EffectiveEvidence != CitationCount", "shared lineage does not add independent evidence mass"),
       ("src/rakl/retrieval_benchmark.py", "src/rakl/claim_evidence.py", "src/rakl/identity.py", "src/rakl/evidence_lineage.py"),
       ("tests/test_retrieval_benchmark.py", "tests/test_claim_evidence.py", "tests/test_evidence_lineage.py"),
       ("graded real-source reliability and semantic support accuracy",)),
    _c("claim_extraction", "Projection of source material into atomic scoped claims with exact selectors.",
       ("source snapshot", "selector/span", "claim text", "context"), ("claim atom", "claim-evidence link", "verdict"),
       ("claim authority <= evidence selector and source projection scope",),
       ("src/rakl/claim_evidence.py",), ("tests/test_claim_evidence.py",), ("automatic multi-span extraction quality",)),
    _c("ontology_terminology_normalization", "Typed normalization without collapsing distinct concepts or identities.",
       ("local terms", "contexts", "identity/equivalence evidence"), ("normalized concepts", "aliases/obstructions", "identity ledger"),
       ("Normalize(x_i,gamma_i)->z only under a typed identity/equivalence witness",),
       ("src/rakl/core.py", "src/rakl/meta_registry.py", "src/rakl/generator_transport.py"),
       ("tests/test_core.py", "tests/test_meta_registry.py", "tests/test_generator_transport.py"),
       ("real contextual ontology alignment",)),
    _c("mathematical_context_translation", "Explicit coordinate, assumption and uncertainty transformation between local charts.",
       ("source chart", "target chart", "typed transition", "measurement transform", "uncertainty model"), ("translated view", "certificate", "obstruction"),
       ("T_ij^{tau,sigma}:phi_i(U_i cap U_j)->phi_j(U_i cap U_j)", "mu_y=A mu_x+b; Sigma_y=A Sigma_x A^T"),
       ("src/rakl/atlas_gluing.py", "src/rakl/bridge_composition.py", "src/rakl/measurement.py", "src/rakl/metrology.py"),
       ("tests/test_atlas_gluing.py", "tests/test_bridge_composition.py", "tests/test_measurement.py", "tests/test_metrology.py"),
       ("real executed coordinate-transform packets",)),
    _c("equivalence_similarity", "Typed scoped equivalence/similarity with preserved and non-preserved structure.",
       ("source", "target", "relation", "witness", "probe family"), ("relation report", "distinguishing probes", "non-preservation ledger"),
       ("W_{A->B}^{tau,q}=(phi,P+,P-,Gamma,Delta,E)", "equivalence is query/probe-family and scope indexed"),
       ("src/rakl/similarity.py", "src/rakl/measurement.py", "src/rakl/generator_transport.py"),
       ("tests/test_similarity.py", "tests/test_measurement.py", "tests/test_generator_transport.py"), ("real analogy/far-transfer utility",)),
    _c("contextual_theory_gluing", "Local-to-global synthesis preserving plural views when compatibility fails.",
       ("atlas charts", "overlap transitions", "alignment", "cycle witnesses"), ("GLOBAL_FORMALISM/PLURAL_ATLAS/OBSTRUCTED_OR_IDENTIFIED_SET", "obstruction certificates"),
       ("Contradict_l=Overlap and Align_l and not Compatible_l", "global glue requires compatible overlaps and licensed cycle composition"),
       ("src/rakl/atlas_gluing.py",), ("tests/test_atlas_gluing.py",), ("real multi-paper coherence benchmark",)),
    _c("contradiction_diagnosis", "Classification of disagreement into contradiction, context difference, undercut, identity issue or obstruction.",
       ("claims/charts", "contexts", "evidence", "transitions"), ("contradiction/obstruction type", "required discriminator"),
       ("Contradict_l=Overlap∧Align_l∧¬Compatible_l",),
       ("src/rakl/core.py", "src/rakl/atlas_gluing.py", "src/rakl/claim_evidence.py"),
       ("tests/test_core.py", "tests/test_atlas_gluing.py", "tests/test_claim_evidence.py"), ("broader real attack/undercut semantics",)),
    _c("gap_discovery", "Localization of the epistemic cut preventing the current target.",
       ("target/QoI", "survivors", "obstructions", "residual history", "operator basis"), ("epistemic cut", "known weakness/missing operator candidate", "fiber"),
       ("cut(K,target)=minimal unresolved coordinate set whose resolution can change target status",),
       ("src/rakl/metacognition.py", "src/rakl/missing_operator.py", "src/rakl/challenge_learning.py"),
       ("tests/test_metacognition.py", "tests/test_missing_operator.py", "tests/test_challenge_learning.py"), ("real hidden-facet/missing-operator precision",), AuthorityEffect.PROPOSAL_ONLY),
    _c("experiment_query_selection", "Selection of probes that separate survivors or decisions per cost.",
       ("V", "Q", "candidate actions", "costs", "calibrated probability/set model"), ("selected discriminator", "separation certificate"),
       ("u(a|K)=[lambda_Q I(Q;Y_a|K)+lambda_M Sep(a,V)+lambda_N E DeltaN]/Cost(a) when probabilities are justified",),
       ("src/rakl/tree.py", "src/rakl/formal_oracles.py", "src/rakl/math_oracles.py"),
       ("tests/test_tree.py", "tests/test_formal_oracles.py", "tests/test_math_oracles.py"), ("prospective real experiment selection",), AuthorityEffect.PROPOSAL_ONLY),
    _c("synthesis", "Scoped synthesis without erasing pluralism, residuals or uncertainty.",
       ("verified charts", "survivors", "obstructions", "identified sets", "authority certificates"), ("scoped synthesis", "residual ledger", "qualified conclusions"),
       ("Synthesize(K,Q) returns a global formalism, plural atlas, or identified/bounded set",),
       ("src/rakl/mechanism_compiler.py", "src/rakl/atlas_gluing.py", "src/rakl/bridge_composition.py"),
       ("tests/test_mechanism_compiler.py", "tests/test_atlas_gluing.py", "tests/test_bridge_composition.py"), ("real synthesis/bridge utility",)),
    _c("memory", "Immutable archive plus reconstructable views and bounded operation-specific working sets.",
       ("canonical records", "source pins", "operation request", "budget"), ("records/views", "compiled context", "rehydration lineage"),
       ("storage_growth does_not_imply prompt_growth", "C*=argmax U(C|o) s.t. M(o) subseteq C and Tokens(C)<=B"),
       ("src/rakl/memory.py", "src/rakl/multires_memory.py", "src/rakl/context_compiler.py"),
       ("tests/test_memory.py", "tests/test_multires_memory.py", "tests/test_context_compiler.py"), ("long-horizon real memory ablations",)),
    _c("review", "Adversarial/independent checking with process and evidence-lineage independence.",
       ("candidate", "falsifiers", "reviewer context", "evidence lineage"), ("findings", "blocking issues", "independence qualification"),
       ("IndependentCredit=ProcessIndependent∧LineageIndependent",),
       ("src/rakl/hard_gates.py", "src/rakl/parent_evaluator.py", "src/rakl/promotion_attestation.py"),
       ("tests/test_hard_gates.py", "tests/test_parent_evaluator.py", "tests/test_promotion_attestation.py"), ("real isolated review benchmarks",)),
    _c("benchmarking", "Frozen evaluation under subject, chronology, resource and evaluator identity constraints.",
       ("benchmark", "subject", "candidate output", "evaluator"), ("metrics", "blocking verdicts", "receipts"),
       ("valid benchmark freezes target/evaluator/thresholds before candidate execution",),
       ("src/rakl/evaluator.py", "src/rakl/retrieval_benchmark.py", "src/rakl/invention_benchmark.py", "src/rakl/publication_gate.py"),
       ("tests/test_evaluator.py", "tests/test_retrieval_benchmark.py", "tests/test_invention_benchmark.py", "tests/test_publication_gate.py"), ("global matched RAKLBench and Polymarket studies",)),
    _c("authority_promotion", "Evidence-gated update of scoped authority coordinates under protected trust boundaries.",
       ("candidate", "evidence certificates", "required checks", "subject/evaluator identity"), ("promotion decision", "scoped authority update/block"),
       ("alpha(c)=(G,R,M,I,D) is coordinatewise only under compatible scope", "Class-B Promote(M') requires all blockers pass and a registered meta-QoI improves"),
       ("src/rakl/promotion.py", "src/rakl/promotion_attestation.py", "src/rakl/subject_identity.py", "src/rakl/evidence_lineage.py"),
       ("tests/test_promotion.py", "tests/test_promotion_attestation.py", "tests/test_subject_identity.py", "tests/test_evidence_lineage.py"), ("real runner/evaluator trust-boundary closure",), AuthorityEffect.EXTERNAL_GATE_REQUIRED),
    _c("saturation_stopping", "Scoped stopping from semantic novelty, route coverage, lineage diversity and residual absence.",
       ("canonical semantic sets", "route coverage", "review independence", "residuals"), ("continue/flat/reopen", "scoped certificate"),
       ("Delta_t^f=C_t^f\\C_{t-1}^f", "flat also requires no new contradiction/discriminator/data requirement/residual"),
       ("src/rakl/saturation.py", "src/rakl/identity_saturation.py", "src/rakl/meta_registry.py"),
       ("tests/test_saturation.py", "tests/test_identity_saturation.py", "tests/test_meta_registry.py"), ("independent flat rounds and real stopping benchmarks",)),
    _c("prompting_context_policy", "Smallest sufficient epistemic working set under a hard token budget.",
       ("operation", "candidate items", "mandatory atoms", "budget"), ("selected manifest", "CANNOT_COMPILE on mandatory overflow"),
       ("C*=argmax_{C subseteq V(o)} U(C|o) s.t. M(o) subseteq C, Tokens(C)<=B",),
       ("src/rakl/context_compiler.py", "src/rakl/token_budget.py"), ("tests/test_context_compiler.py", "tests/test_token_budget.py"), ("real matched context-policy/tokenizer calibration",), AuthorityEffect.PROPOSAL_ONLY),
    _c("capability_shaping", "Controlled modification/attribution of research capabilities without confusing compensators with truth.",
       ("capability trial", "operator candidate", "matched baseline", "failure pattern"), ("attribution", "operator verdict", "learning action"),
       ("gain decomposes into model-utilization, external-resource, specialist-complementation and whole-system coordinates",),
       ("src/rakl/capability.py", "src/rakl/challenge_learning.py", "src/rakl/metacognition.py", "src/rakl/missing_operator.py"),
       ("tests/test_capability.py", "tests/test_challenge_learning.py", "tests/test_metacognition.py", "tests/test_missing_operator.py"), ("real self-evolution transfer",), AuthorityEffect.PROPOSAL_ONLY),
    _c("software_architecture_execution", "Content-addressed execution with immutable event chains and proposal-only runner outputs.",
       ("task packet", "runner contract", "generation config", "environment", "project store"), ("events", "immutable receipt", "replay/recovery outcome"),
       ("invocation_id=SHA256(canonical(spec))", "event_n binds SHA256(event_{n-1})"),
       ("src/rakl/project_runtime.py", "src/rakl/execution.py", "src/rakl/release_manifest.py", "src/rakl/reference_profile.py", "src/rakl/artifact_attestation.py"),
       ("tests/test_project_runtime.py", "tests/test_execution.py", "tests/test_release_manifest.py", "tests/test_reference_profile.py", "tests/test_artifact_attestation.py"), ("real external model runner and long-running recovery",)),
    _c("research_portfolio_tree", "Non-greedy allocation across exploit/diversify/moonshot/meta branches.",
       ("open fibers", "decision value/separation", "costs", "portfolio constraints"), ("agenda", "branch allocations", "revisit triggers"),
       ("Portfolio={exploit,diversify,moonshot,meta} under validity and budget constraints",),
       ("src/rakl/tree.py", "src/rakl/search_controller.py"), ("tests/test_tree.py", "tests/test_search_controller.py"), ("real deceptive-landscape/scientific-taste benchmarks",), AuthorityEffect.PROPOSAL_ONLY),
    _c("objective_evolution", "Governed revision of operational objectives while preserving protected invariants.",
       ("current objective", "feedback", "meta-QoIs", "protected criteria"), ("objective proposal", "guarded update/block", "negative history"),
       ("objective update admissible only if protected invariants are unchanged and target/meta-QoI evidence supports it",),
       ("src/rakl/evolution.py", "src/rakl/meta.py", "src/rakl/challenge_learning.py"), ("tests/test_evolution.py", "tests/test_meta.py", "tests/test_challenge_learning.py"), ("Goodhart/proxy-degradation experiments",), AuthorityEffect.PROPOSAL_ONLY),
    _c("generator_transport", "Typed transport of structural generators across domains with explicit lifts and target validation.",
       ("source/target generators", "lift", "relation witness", "scope", "target trial"), ("transport proposal/report", "validation/refutation/partial identification"),
       ("transport authority <= weakest licensed lift/relation/measurement/target certificate", "multi-hop requires composable handoffs and global regime intersection"),
       ("src/rakl/generator_transport.py", "src/rakl/similarity.py", "src/rakl/bridge_composition.py"),
       ("tests/test_generator_transport.py", "tests/test_similarity.py", "tests/test_bridge_composition.py"), ("real comparative target transfer and multi-hop bridge benchmark",)),
)


# RAKL v3 is an implementation overlay, not a parallel method constitution.
# Every new public module/function remains owned by one of the canonical method
# surfaces above.  Reviewers can therefore detect an ungoverned v3 surface
# instead of accepting a manifest label as authority.
V3_IMPLEMENTATION_OWNER_MAP = {
    "src/rakl/v3_authority.py": "authority_promotion",
    "src/rakl/experience_substrate.py": "memory",
    "src/rakl/experience_learning.py": "authority_promotion",
    "src/rakl/experience_memory.py": "memory",
    "src/rakl/failure_learning.py": "contradiction_diagnosis",
    "src/rakl/problem_fibre.py": "decomposition",
    "src/rakl/gluing_learning.py": "contextual_theory_gluing",
    "src/rakl/experience_policy.py": "routing",
    "src/rakl/experience_benchmark.py": "benchmarking",
    "src/rakl/saturation_vector.py": "saturation_stopping",
    "src/rakl/problem_novelty.py": "gap_discovery",
    "src/rakl/unified_substrate.py": "memory",
    "src/rakl/evolution_archive.py": "objective_evolution",
    "src/rakl/v3_runtime.py": "software_architecture_execution",
    "src/rakl/v3_scientific_authority.py": "authority_promotion",
    "src/rakl/driver_learning.py": "software_architecture_execution",
    "src/rakl/v3.py": "software_architecture_execution",
    "src/rakl/shadow_artifact_hash.py": "software_architecture_execution",
    "src/rakl/summation_compatibility.py": "contextual_theory_gluing",
}

V3_PUBLIC_AUTHORITY_SURFACE_OWNERS = {
    "resolve_protected_attestation": "authority_promotion",
    "assess_lesson_consolidation": "authority_promotion",
    "promoted_lesson_version": "authority_promotion",
    "lesson_to_research_tool": "authority_promotion",
    "glue_local_sections": "contextual_theory_gluing",
    "validate_experience_benchmark": "benchmarking",
    "assess_experience_benchmark": "benchmarking",
    "record_evolution_trial": "objective_evolution",
    "promote_incumbent": "authority_promotion",
}


def validate_v3_method_ownership() -> tuple[str, ...]:
    canonical = {contract.surface for contract in METHOD_CONTRACTS}
    problems = [
        f"v3_owner_not_canonical:{surface}:{owner}"
        for surface, owner in sorted(
            {**V3_IMPLEMENTATION_OWNER_MAP, **V3_PUBLIC_AUTHORITY_SURFACE_OWNERS}.items()
        )
        if owner not in canonical
    ]
    from . import v3 as v3_facade

    for public_name in v3_facade.__all__:
        value = getattr(v3_facade, public_name)
        module = getattr(value, "__module__", "")
        implementation_path = f"src/{module.replace('.', '/')}.py" if module.startswith("rakl.") else ""
        owner = V3_PUBLIC_AUTHORITY_SURFACE_OWNERS.get(public_name)
        if owner is None and implementation_path:
            owner = V3_IMPLEMENTATION_OWNER_MAP.get(implementation_path)
        if owner is None and public_name == "LESSON_ERASURE_TAGS":
            owner = "memory"
        if owner is None:
            problems.append(f"v3_public_surface_owner_missing:{public_name}:{module}")
    return tuple(problems)
