# HOSTILE MATH AUDIT — Orion unified-solver formal layer

- Audit target: HEAD = `1bdf9101` ("verify + rebuild after closure-branch merge"), 2026-08-13.
- Scope: `path_cost.py`, `solution_assembly.py`, `operational_map.py`, `fieldability.py`, `mechanic_diagnosis.py`, `unified_solver_registry.py`, `solver_compilation.py`, `structural_types.py`, `path_equivalence.py`/`path_congruence.py` (context-soundness of the new closure only), Paper 05 §11, Paper 06 §10c.
- Exclusions (previously found, NOT re-reported): (1) missing equivalence/congruence laws for path quotienting — closed on HEAD by `path_congruence.py`; (2) budget-indexed d not a metric — closed on HEAD by `cost_geometry.py`. Gap U1 below is a *new residual* of closure (1), not a restatement.
- Every counterexample below was executed against HEAD with `/tmp/orion-venv/bin/python` (`PYTHONPATH=src`). Runner: `/tmp/claude-1000/-home-billy-Desktop/85736cc6-4363-40ad-ab5e-b95a1afdff6a/scratchpad/hostile_counterexamples.py` — all 19 checks reproduce (`ALL_REPRODUCED`).

Severity counts: **UNSOUND 6 · ILL-POSED 6 · OVERCLAIM 2 · COSMETIC 1** (15 gaps).

---

## UNSOUND

### U1. Context-bound independence witnesses feed a context-free trace quotient

**Where:** `src/rakl/path_equivalence.py:150-171` (single `context_hash` filter at line 155; swap loop 159-171), `src/rakl/path_congruence.py:49-63` (`TraceMonoid.build` takes bare pairs, no context), Paper 05 `sections/11_verified_transformation_geometry.tex:57-61`.

**What is missing:** Mazurkiewicz trace congruence (the structure the closure correctly installed) is sound only for a *static* independence relation `I ⊆ A×A`. The witnesses are context-bound: `TransitionIndependenceWitness.context_hash` certifies that `a,b` commute *in one state*. `equivalent_under_declared_partial_order` filters witnesses against a single caller-supplied `context_hash` and then uses each witnessed pair to license adjacent swaps at **every position** in the history. A swap at position `k` occurs in the state reached after the length-`k` prefix — a context in which commutation was never certified. `path_congruence.TraceMonoid` discards context entirely. The paper's own licensing condition ("independent/commuting transformations *in the relevant context*") is not expressible in the data model: histories carry no intermediate state hashes, so "relevant context" of a swap cannot even be named.

**Counterexample (verified, check G16):** witness `w(a,b)` bound to `context_hash="state_after_EMPTY_prefix"`; `equivalent_under_declared_partial_order(("p","a","b"), ("p","b","a"), independence_witnesses=(w,), context_hash="state_after_EMPTY_prefix")` returns `True`, although the `a,b` swap happens after `p`, in a context where no witness exists. If `a,b` commute at the initial state but not after `p`, two semantically distinct histories are merged.

**Weakest closing structure:** local/state-indexed independence — asynchronous transition systems (Bednarczyk/Shields) with the independence-square axioms, i.e. `I` is a relation `I_s ⊆ A×A` indexed by state `s`, and an adjacent swap at position `k` requires `(a,b) ∈ I_{s_k}`. Minimal repair: witnesses bind the swap-point state hash and the checker recomputes prefix states.

**Severity: UNSOUND** — over-quotienting merges inequivalent proofs/computation histories; the paper's `m!` collapse claim (Paper 06 `10c:85`) inherits validity only under the unstated global-independence axiom.

### U2. Verified routes compose edges with incompatible scopes

**Where:** `src/rakl/operational_map.py:205-236` (BFS builds adjacency from `VERIFIED_TRANSITION` edges, never reads `edge.scope`); report reason `route_uses_verified_transition_edges_only` at line 236; Paper 05 Proposition premise (i) `11_...tex:132`.

**What is missing:** each edge is verified *relative to its scope*. A route is a composite claim; its verification scope is the meet `⋀_i scope(e_i)` in whatever ordering scopes carry. The router quantifies existentially over per-edge scopes and asserts a route-level "verified" without requiring any common scope — the composition law `verified_S1(e1) ∧ verified_S2(e2) ⟹ verified_?(e1;e2)` is applied with `? := true` regardless of `S1 ⊓ S2` (which may be empty).

**Counterexample (verified, check G1):** edges `s→a` verified in scope `"characteristic_zero"` and `a→t` verified in scope `"characteristic_p_only"` yield `VERIFIED_ROUTE_FOUND` with route `(e1,e2)`, though no single scope licenses both legs.

**Weakest closing structure:** a meet-semilattice of scopes with routes labelled by the meet of their edge scopes (equivalently, reachability in a category fibred/indexed over scopes); reject or downgrade routes whose scope-meet is ⊥.

**Severity: UNSOUND** — a route reported as verified-composite is not verified in any scope; Paper 05 Proposition premise (i) ("every materialized transition on it is replay-verified under the frozen subject") is not discharged by the implementation.

### U3. The materialized map drops the transformation coordinate of Σ_Θ(x,T,y); belief consistency is inexpressible

**Where:** `src/rakl/operational_map.py:80-97` (`OperationalEdge` has endpoints, status, scope — no operator/transformation id), `100-129` (receipt validates only `edge_id` uniqueness); Paper 05 `11_...tex:18-26` (Σ_Θ is a relation over (state, **T**, state); B_Θ,t presented as a partition K⁺/K⁻/K?/U).

**What is missing:** the paper's semantics assigns a status to a *transition instance* (x,T,y) in a scope; the code assigns statuses to anonymous (x,y) arrows. Consequences: (a) the partition/consistency axiom `K⁺ ∩ K⁻ = ∅` (per (x,T,y,scope)) cannot even be stated over the implemented carrier, and the receipt accepts a map in which the same (source, target, scope) is simultaneously `VERIFIED_TRANSITION` and `REFUTED_IN_SCOPE` — either a genuine contradiction or two different operators, and the model cannot distinguish these cases; (b) coverage contracts over an "operator basis" (`operator_basis_version`) are unverifiable against edges that do not name operators.

**Counterexample (verified, check G2):** receipt with `e1=(s,t,VERIFIED_TRANSITION,scope="S")` and `e2=(s,t,REFUTED_IN_SCOPE,scope="S")` validates and routes through `e1`.

**Weakest closing structure:** make status a *partial function* `status: X × Ω × X × Scope ⇀ StatusSet` (add an operator id to `OperationalEdge`); add the consistency integrity constraint (at most one epistemic status per key, or a declared join in an information lattice, e.g. Belnap-style conflict detection that forces `CANNOT_CHECK`).

**Severity: UNSOUND** — a map that is internally contradictory (or ambiguous between contradiction and multi-operator reading) passes validation and feeds routing and certified-no-route verdicts.

### U4. Coverage-completeness certificate is not bound to the edge set it certifies, and survives map mutation

**Where:** `src/rakl/operational_map.py:109-129` (`__post_init__` checks `matches()` on problem/operator/chart only; `closure_subject_hash` is never compared to anything), `131-133` (`coverage_complete := certificate is not None`), `188-191` (`add_edge` copies the certificate onto the mutated map), `68-73` (`matches` omits `closure_subject_hash`).

**What is missing:** the certificate object carries a `closure_subject_hash`, but no law connects it to the enumeration it allegedly closes. Completeness is a property of the *edge enumeration* (a Moore/closure fixpoint: "every (state, operator) pair in scope has a recorded status"), so the certificate must be bound to a canonical hash of that enumeration and must be invalidated by any mutation. As implemented, `coverage_complete` is again a free-floating flag — exactly the defect the closure branch removed for the boolean version, reintroduced one level up.

**Counterexample (verified, checks G3/G3b):** one `CoverageCompletenessCertificate` with `closure_subject_hash="hash_of_SOME_OTHER_edge_set"` is accepted by two receipts with *different* edge sets (empty; one refuted edge); both return `NO_VERIFIED_ROUTE_COVERAGE_COMPLETE`. And `add_edge` on a certified map returns a new map with `coverage_complete == True` — a strictly larger enumeration inherits the closure certificate of the smaller one.

**Weakest closing structure:** closure operator / Moore family with certified fixpoint: require `certificate.closure_subject_hash == H(edges)` (canonical multiset hash, certificate excluded) in `__post_init__`, and have `add_edge` drop the certificate.

**Severity: UNSOUND** — the scoped no-route-in-certified-map verdict (the strongest negative output this module produces) can be minted for an enumeration the closure verifier never saw.

### U5. Solution-assembly gate is REFUTES-blind, and the REDUCES_TO dependency direction inverts the natural encoding

**Where:** `src/rakl/solution_assembly.py:63-107` (no mention of `ProofRelation.REFUTES` or of `REFUTED` nodes outside the dependency closure); `src/rakl/proof_dag.py:38-40` (`DEPENDENCY_RELATIONS` excludes `REFUTES`), `188-206` (`dependency_closure` traverses source→target with "source is a premise" convention).

**What is missing:**
(a) *Conflict-freeness.* The gate checks positive conditions (closure selected, dependencies verified, root verified, receipt audit) but no consistency constraint: a DAG may simultaneously contain a VERIFIED root and a VERIFIED `COUNTEREXAMPLE` node with a `REFUTES` edge into the root — an assertion of ⊢P and ⊢¬P — and the gate still returns `READY_FOR_EXTERNAL_AUTHORITY_GATE` with reasons including `root_verified`. Because `required ⊆ selected` is only an inclusion, the refuter may even be *inside the selected certificate*.
(b) *Direction ambiguity.* `IMPLIES` and `REDUCES_TO` share the "source is a premise of target" convention (`proof_dag.py:195-197`). For `IMPLIES` that is natural (A⇒B: A is input to B). For `REDUCES_TO` it is backwards: "X REDUCES_TO Y" naturally means proving Y suffices for X, i.e. Y is the premise. A naturally-encoded reduction edge (source=X, target=Y) puts Y *outside* `dependency_closure(X)`, so `all_dependencies_verified` ignores Y entirely.

**Counterexamples (verified, checks G4/G4b):** (a) `dag = {root: THEOREM VERIFIED, cex: COUNTEREXAMPLE VERIFIED}` with edge `cex —REFUTES→ root`, selected = {root, cex}, passing bound proof receipt → verdict `READY_FOR_EXTERNAL_AUTHORITY_GATE`. (b) `root —REDUCES_TO→ lem` with `lem` REFUTED → also `READY`.

**Weakest closing structure:** (a) an integrity constraint from paraconsistent/4-valued knowledge bases: no node in `selected ∪ closure(root) ∪ {root}` may be VERIFIED while a VERIFIED node REFUTES it (return `REJECT` or `CANNOT_CHECK` on conflict). (b) a per-relation premise-orientation map (declare explicitly that `REDUCES_TO` premises are targets, or rename the relation `SUFFICES_FOR`).

**Severity: UNSOUND** — the gate's reason vector (`dependencies_verified`, `root_verified`) misrepresents an internally inconsistent certificate to the downstream authority gate.

### U6. Amortization break-even law contradicts the module's own invalidation-hazard model

**Where:** `src/rakl/fieldability.py:126-132` (`amortization_break_even_queries`) vs `135-141` (`stability_adjusted_per_query_cost`); identically `src/rakl/solver_compilation.py:179-186` (`compilation_break_even_uses`) vs `160-164` (`stability_adjusted_per_use_cost`); Paper 06 `10c:55-58` ("The **exact** break-even law is q > C_build/(C_baseline − C_extract)").

**What is missing:** the break-even function computes `q* = C_b/(C_base − C_ext)`, silently assuming hazard `h = 0`, while three lines away the same module prices per-query cost as `C_ext + h·C_b`. Under the module's own Bernoulli-rebuild model (renewal process, i.i.d. invalidation with rebuild cost `C_b`), the long-run advantage per query is `C_base − C_ext − h·C_b`, so the correct law is `q* = C_b/(C_base − C_ext − h·C_b)` with domain condition `C_base − C_ext > h·C_b`; otherwise the field *never* pays off. No law tells a consumer which of the two mutually inconsistent quantities governs a routing decision. Additional unstated hypotheses shared by both laws: stationarity (constant per-query costs, i.i.d. hazard) and commensurability (build/extract/baseline — and in `one_shot_cost`, build/execution/decode/verification — summed on one scalar scale, the compensatory aggregation the framework's own noncompensatory doctrine forbids for path costs; the code comments hedge this, the paper's word "exact" does not).

**Counterexample (verified, checks G7/G7b):** `C_b=100, C_base=30, C_ext=10, h=0.25`: break-even returns `5.0` queries; hazard-adjusted per-query cost is `35 > 30` — amortization never occurs. Decision reversal, not an approximation error.

**Weakest closing structure:** renewal–reward accounting (one law, hazard a parameter with `h=0` as the special case), plus an explicit commensurability/stationarity axiom on the cost carrier.

**Severity: UNSOUND** for any routing decision with `h > 0`; the paper's "exact" is an OVERCLAIM for the `h=0` idealization.

---

## ILL-POSED

### I1. `PathCostVector` admits NaN: dominance stops being a decidable strict order and lexicographic selection is input-order-dependent

**Where:** `src/rakl/path_cost.py:87-89` (validation is only `< 0`, which NaN vacuously passes), `134-137` (`dominates`), `150-158` (`explicit_lexicographic_select` uses `min` over float-key tuples).

**What is missing:** the intended carrier is `([0,∞)^7, ≤)` — coordinates totally ordered so that product/lexicographic orders are well-defined. IEEE NaN is incomparable with everything (including itself), so with NaN admitted: `dominates` is no longer a strict order restricted to a poset (NaN vectors are never dominated — immortal frontier members), and `min` under an incomparable key returns whichever element is scanned first — "explicit lexicographic selection" is not a function of the option *set*.

**Counterexample (verified, checks G5/G5b):** `PathCostVector(compute=float("nan"))` constructs; `explicit_lexicographic_select([p_nan, p_five], ...)` returns `p_nan` but returns `p_five` when the input order is swapped; `dominates((0,...), (nan,...))` is `False`.

**Weakest closing structure:** finiteness axiom — validate `math.isfinite` per coordinate (carrier `[0,∞)`; keep `+∞` only if the order semantics for it is explicitly defined, which `min`/`<` do support; NaN never is).

**Severity: ILL-POSED** — a selection routine whose output depends on iteration order has no denotation.

### I2. `path_id` is silently assumed injective; a strictly dominated option survives the "Pareto frontier"

**Where:** `src/rakl/path_cost.py:129-131` (`PathOption` checks only non-emptiness), `144` (frontier pruning exempts comparisons with equal `path_id`), `158` (lex tie-break by `path_id` presumes it is a key).

**What is missing:** both algorithms treat `path_id` as an injective labelling (a key into the option set) but nothing enforces it. Line 144's guard `other.path_id != candidate.path_id` — intended to stop self-domination under strict dominance, which is already irreflexive — instead *disables pruning between distinct options that share an id*. The output then violates the definition of a Pareto frontier (it contains a strictly dominated point). Similarly the tie-break key `(costs..., path_id)` is not a total order on options when ids collide.

**Counterexample (verified, check G6):** options `("p", cost=1)` and `("p", cost=2)`: `dominates` holds, yet `admissible_pareto_frontier` returns both — frontier costs `[1.0, 2.0]`.

**Weakest closing structure:** quotient by identity — enforce `path_id` uniqueness across the input (raise on duplicates), or prune by cost comparison alone (strict dominance needs no id guard: it is irreflexive by construction).

**Severity: ILL-POSED** (locally UNSOUND: the function's output contradicts its own specification).

### I3. Mechanic diagnosis: UNKNOWN lives inside the hypothesis space, and union-only combination makes identification anti-monotone in evidence

**Where:** `src/rakl/mechanic_diagnosis.py:56-64` (receipt validation), `99-117` (`diagnose_mechanic_signals`: candidate set = union of `_SIGNAL_RULES[s]`).

**What is missing:**
(a) *Lattice confusion.* `UNKNOWN` is the bottom of the information order, not an element of the fault ontology; the receipt validator accepts `candidate_causes=(UNKNOWN,)` with `verdict=MECHANIC_GAP_IDENTIFIED` — "the uniquely identified mechanic gap is UNKNOWN" — because the only check is `len(candidate_causes) == 1`.
(b) *Combination semantics undeclared.* The union rule is the multi-fault (∃-cause-per-signal) semantics; `MECHANIC_GAP_IDENTIFIED` on `|union| = 1` is sound only under the additional closed-world axiom that `_SIGNAL_RULES` is exhaustive per signal — nowhere stated, and unfalsifiable from inside the module. Under a single-fault reading the correct combinator is intersection; the code never distinguishes these, so adding a signal can only *grow* the candidate set: evidence monotonically destroys identification even when the new signal is consistent with the identified cause, and jointly inconsistent signal sets (empty intersection) are indistinguishable from genuine multi-cause ambiguity.
(c) *Permutation variance.* `candidate_causes` preserves signal iteration order, so two diagnoses of the same signal *set* are unequal receipt objects (relevant for any content-addressed dedup, as used elsewhere in the codebase).

**Counterexamples (verified, checks G9/G9b/G9c):** (a) constructs without error. (b) `{portal_roundtrip_failed} → MECHANIC_GAP_IDENTIFIED` but `{portal_roundtrip_failed, decomposition_interface_missing} → PARTIALLY_IDENTIFIED`. (c) permuted signals give `e1 != e2`.

**Weakest closing structure:** abduction over a hypothesis lattice with an explicit fault-cardinality assumption: separate the epistemic status (⊥ = UNKNOWN) from the fault set; declare the combinator (∩ under single-fault with an explicit `INCONSISTENT_SIGNALS` outcome on ∅; ∪ under multi-fault, in which case rename the verdict to "all signals attributable to one cause"); canonicalize `candidate_causes` order. The closed-world exhaustiveness of `_SIGNAL_RULES` must be a stated axiom of the verdict.

**Severity: ILL-POSED** — the strongest verdict's meaning depends on an undeclared choice between two incompatible logics.

### I4. No certificate composes: transformation effects have no algebra, preservation receipts and navigation-quotient validations have no composition law, and registry ownership is not closed under composition

**Where:** `src/rakl/solver_compilation.py:110-124` (`claimed_effects` is a free tuple; no relations), `50-97` (`PreservationValidationReceipt` binds exactly one (representation, transform) pair; no composite constructor); `src/rakl/navigation_quotient.py` (per-quotient validation; no law for `q2 ∘ q1`); `src/rakl/unified_solver_registry.py:19-35, 132-154` (ownership is per-module; the reason string `all_new_modules_owned_by_existing_canonical_method_surfaces` quantifies over modules, not over compositions).

**What is missing:** the framework's central promise is pipelines — chained representations, transforms, quotients. But: (i) `claimed_effects` is a word in the free monoid over `TransformationEffect` with no relations or incompatibility constraints, so mutually annihilating or contradictory claims validate; (ii) two `VALIDATED_FOR_ROUTING` compilations chained end-to-end have no derived preservation receipt — validated-ness is not closed under composition and no rule says who owns or re-validates `X ∘ Y` (if mechanic A owns X and B owns Y, `X∘Y` is owned by no registry surface); (iii) two `EXACT_REACHABILITY_PRESERVING` navigation quotients have no composite verdict, although forward simulations and route liftings do compose — the safe theorem is simply absent, so callers will either re-verify (cost) or assume (unsound).

**Counterexample (verified, check G10):** `SolverCompilationCandidate(..., claimed_effects=(RELAX, TIGHTEN))` validates — a compilation simultaneously claiming a sound relaxation and a sound tightening of the same problem.

**Weakest closing structure:** a category of representations with certificates as morphism data: preservation/validation receipts must form a subcategory (identities exist; a composite receipt is derivable from composable receipts with matching interface hashes); effects act on a spec lattice with declared composition/incompatibility relations (at minimum a symmetric `conflicts ⊆ Effect × Effect`).

**Severity: ILL-POSED** — every multi-step claim in the papers ("bind representation, transformation, solver, decoder and verifier", fibred child/parent GLUE) presumes a composition law the formal layer does not contain.

### I5. Geometry certification class is self-declared — the exact defect just fixed for coverage, reintroduced

**Where:** `src/rakl/fieldability.py:8-14, 40, 58-68` (`certification_class` is a bare enum field; `supports_exact_cost_claim` and `is_theorem_certified_heuristic_class` read it directly).

**What is missing:** `EXACT_COST_TO_GO`, `ADMISSIBLE_LOWER_BOUND`, `CONSISTENT_HEURISTIC` are *theorems about a function relative to a cost algebra and map revision*. The closure branch (correctly) upgraded coverage-completeness from a boolean to a verifier-bound `CoverageCompletenessCertificate`; the certification class — which licenses strictly stronger downstream claims (A*-style admissibility/consistency arguments) — remains an unwitnessed self-declaration: no verifier id, no subject hash, no checker.

**Counterexample (verified, check G15):** `GeometryArtifactIdentity(..., certification_class=EXACT_COST_TO_GO)` constructs freely and `supports_exact_cost_claim` is `True`.

**Weakest closing structure:** same pattern as U4's fix: a `CertificationWitness` (verifier id + subject hash + class), with `matches()` checked against the geometry's own identity coordinates; default `UNCERTIFIED` without it.

**Severity: ILL-POSED** (OVERCLAIM at the API boundary: property names promise theorem-hood the type does not carry).

### I6. Structural transfer: "structurally complete" is decided by cardinality, and multi-chart gluing has no cocycle condition

**Where:** `src/rakl/structural_types.py:125-139` (`TransferAssessment.structurally_complete` compares `preserved_*_count == required_*_count`); `StructuralWitness:93-122` (one-to-one role mapping per witness; no composition); `chart_id` appears in `operational_map.py` and `fieldability.py` identities with no inter-chart compatibility object anywhere; Paper 05 `11_...tex:66` (atlas/groupoid language), outcome label `ATLAS_NAVIGABILITY_SUPPORTED_GLOBAL_GEOMETRY_UNSUPPORTED` (`11_...tex:165`).

**What is missing:** (a) completeness of a preservation claim is set inclusion (`required ⊆ preserved`), not equal cardinality; the type carries only counts, so "the wrong 3 of the required 3 relations preserved" is structurally undetectable — the property is not merely unchecked, it is *unstatable* in the type. (b) The paper speaks of an atlas and of multi-chart navigability, and witnesses/charts are plainly intended to be glued (child→parent GLUE, `chart_id`-indexed geometries), but there is no composition of `StructuralWitness` role mappings (partial injections do compose), no intersection law for `preserved_invariants`, and no triple-overlap coherence (cocycle) condition `φ_ik = φ_jk ∘ φ_ij` for charts. Witness non-transitivity is honestly disclaimed for *semantic* transfer, but any multi-chart geometric claim silently assumes exactly the gluing coherence the model never demands.

**Counterexample (verified, check G14):** `TransferAssessment(LICENSED, (), 3, 3, 2, 2).structurally_complete == True` regardless of *which* relations were preserved.

**Weakest closing structure:** (a) a Galois-connection-friendly certificate: store the preserved and required *sets* (or their canonical hashes) and define completeness as inclusion. (b) For charts: groupoid of chart transition witnesses with the cocycle condition checked on registered overlaps — the standard atlas coherence axiom, and the weakest one under which "atlas navigability" is a well-formed claim.

**Severity: ILL-POSED.**

---

## OVERCLAIM

### O1. Descent-completeness proposition (Paper 05) is false as stated: missing π-invariance of S

**Where:** Paper 05 `sections/11_verified_transformation_geometry.tex:108-112`.

**The claim:** "Let W be well founded and h: X→W. A local policy π is *descent-complete* on a registered solvable set S when every non-goal x∈S has a verified legal successor π(x) with h(π(x)) ≺ h(x), and every minimal reachable h-state in S is a verified goal. Then repeated application of π reaches a goal in finitely many steps."

**What is wrong:** the well-founded-descent argument needs the π-orbit to *stay inside* the set on which descent is guaranteed; the hypothesis π(S∖Goals) ⊆ S is absent. Additionally "minimal reachable h-state" is quantifier-ambiguous: reachable under π or under the full legal successor relation? Under the legal-reachability reading the proposition is **false**; under the π-orbit reading the second premise quantifies over the very orbits whose termination is being proven, making the condition non-local and the theorem near-vacuous.

**Counterexample (verified, check P1; 3 states):** X={a,b,g}, S={a,g}, h(a)=2, h(b)=1, h(g)=0; legal edges a→b, b→b, b→g; π(a)=b, π(b)=b; goal g. Every non-goal in S descends (a→b, 1≺2) ✓; the h-minimal legally-reachable state in S is g, a verified goal ✓; yet the π-orbit from a is a,b,b,b,… and never reaches a goal.

**Weakest closing structure:** the standard Floyd/loop-termination pairing — a variant (well-founded h) *together with* an invariant (a π-closed subset S′ ∋ start with π(S′∖Goals) ⊆ S′). One added hypothesis fixes the proposition.

**Severity: OVERCLAIM** (a false theorem-like statement in the paper; the code does not implement it, so no runtime unsoundness).

### O2. Noninterference Proposition premises are not discharged by the implementation, and residual symbol gaps

**Where:** Paper 05 `11_...tex:131-136` (Proposition "Map, geometry and quotient noninterference"); implementation counterparts in `operational_map.py` and `navigation_quotient.py`; Paper 05 `11_...tex:149-153`; Paper 06 `10c:55, 85`.

**What is wrong:**
- Premise (i) ("a route is called verified only when every materialized transition on it is replay-verified under the frozen subject") is falsified by U2/U3: the implemented router accepts scope-heterogeneous and operator-anonymous routes. The proposition is fine as mathematics; presenting it as a property of "the implementation contract" is stronger than the code supports.
- Premise (iii) (spurious quotient routes "revalidated in the original semantics") is represented only by advisory properties (`requires_concrete_route_revalidation`, `navigation_quotient.py:88-90`); nothing in the formal layer consumes them, so (iii) is an obligation on unwritten callers, not an invariant.
- `N(k,B)` (`11_...tex:149-153`) is called a "curve" valued in an unordered 4-tuple with no stated domain, ordering, or evaluation measure — as displayed mathematics it is a type signature, not a definition.
- Paper 06 `10c:55` "exact break-even law": exact only under h=0/stationarity/commensurability (see U6). Paper 06 `10c:85` states the `m!`-to-one collapse without the "when independence is actually certified" hedge that Paper 05's twin caption acquired — and *with* certification the collapse is only valid under the global-independence axiom of U1.

**Weakest closing structure:** state the proposition's premises as named implementation obligations and cite the enforcing check for each (or mark unenforced ones as assumptions); give `N(k,B)` a domain and an ordering (e.g. a map into ℝ⁴ with componentwise comparison declared).

**Severity: OVERCLAIM.**

---

## COSMETIC

### C1. Content hashes distinguish semantically identical objects

**Where:** `src/rakl/solution_assembly.py:13-19` (`proof_dag_content_hash` includes free-text `notes`; edge list tolerates exact duplicate `(source,target,relation)` triples, which `validate_proof_dag` does not reject); `mechanic_diagnosis.py` receipt order-variance (see I3(c)).

**What is missing:** hash-respects-equivalence: semantically equal DAGs (same nodes/edges/statuses, different notes or a duplicated edge) receive different content hashes, so hash equality is sound but hash *in*equality carries no semantic information; any dedup keyed on it over-splits. Quotient the hashed payload by the intended equivalence (drop notes or hash them separately; canonicalize edges as a set).

**Severity: COSMETIC** (fail-safe direction: causes spurious mismatch REJECTs, never false acceptance).

---

## Cross-cutting note for the closure team

Three of the six UNSOUND gaps (U1, U4, I5) are residuals *of the closure pattern itself*: a law was installed for the flagged instance (static trace monoid; coverage certificate; coverage boolean→certificate) but the binding that makes the law apply to the runtime object (swap-point context; certified edge-set hash; certification witness) was left out. The general repair schema is the same everywhere: every certificate must carry, and every consumer must check, the canonical hash of the exact object it certifies.
