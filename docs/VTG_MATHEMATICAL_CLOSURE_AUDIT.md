# VTG Mathematical Closure Audit — 2026-08-13

Status: `BOUNDED_MATHEMATICAL_CLOSURE_AUDIT_COMPLETE / EMPIRICAL_GEOMETRY_EXISTENCE_UNRESOLVED`.

This audit asks a narrower question than the broader framework work: is Verified Transformation Geometry (VTG) sufficiently well-defined mathematically that experts can distinguish theorem-level structure, engineering contracts, and empirical hypotheses?

## Main conclusion

No new top-level Orion architecture plane was required. The remaining gaps were cross-cutting mathematical obligations. The load-bearing corrections are now:

1. **Operational-state sufficiency.** A state geometry is meaningful only when the state contains all future-relevant operational information under a frozen subject. If two histories share the same encoding but induce different legal successors/costs, the state must be augmented.
2. **Verified path category.** States are objects and verifier-replayable transitions generate paths. This is the microscopic symbolic substrate; no useful geometry is assumed.
3. **Path-equivalence congruence.** Any quotient relation must preserve endpoints and be stable under path composition. Concurrency reduction is generated only by verifier-bound independence/commutation witnesses; absence of a dependency is not independence evidence.
4. **Transition semantics versus discovered map.** `UNKNOWN != BLOCKED`, and failed search is not refutation.
5. **Registered-map closure versus impossibility.** A closure certificate establishes only no route under the bound problem/operator-basis/chart/closure subject. It does not establish theorem falsity or unprovability without a separate completeness result.
6. **Representation category, not universal manifold atlas.** Exact reversible representation changes form the atlas/groupoid-like part. One-way reductions, quotients and relaxations remain non-invertible certified arrows.
7. **Navigation quotient contract.** QoI-preserving semantic quotienting is not automatically reachability preserving. Exact navigation claims need target preservation and two-way transition/route-lifting conditions; over-approximations require spurious-route detection/refinement.
8. **Hard admissibility before path cost.** Invalid portals, unlicensed assumptions, wrong specification and failed trust gates cannot be compensated by cheap compute.
9. **Typed path-cost algebra.** Different cost coordinates have different composition laws. Use a registered ordered algebra/quantale where justified, or retain a Pareto/set-valued frontier.
10. **Intrinsic geometry before budget.** Budget defines feasible reachability/control; a budget-truncated distance can violate triangle inequality and should not be called a metric by default.
11. **Geometry certification classes.** Distinguish exact cost-to-go, admissible lower bound, consistent heuristic, empirical ranker and uncertified geometry. Theorem rights differ.
12. **Certified local navigability.** For a registered class, a local policy with verifier-valid successors and a strictly decreasing well-founded rank reaches a goal finitely. This is the theorem-level version of the “gravity toward solution” intuition.
13. **Trajectory/certificate separation.** Search chronology is not the final proof DAG/term; authority attaches only through the final original-semantics proof/specification/trust gate.
14. **Deterministic/stochastic boundary.** Phase-0/1 VTG is deterministic. Stochastic actions require kernels/MDP/game semantics rather than silent reuse of deterministic edge geometry.
15. **Infinite-space boundary.** Infima may not be attained and geodesics may not exist. Metric/quasimetric/geodesic/manifold claims require explicit axioms.

## Code defects found and corrected on `orion/unified-problem-solving-v1`

- `VERIFIED_APPLICABLE` no longer counts as a traversable verified state transition.
- Naked `coverage_complete=True` was replaced by a subject-bound `CoverageCompletenessCertificate`.
- No complete-map result can set `establishes_mathematical_impossibility=True`.
- Reordered histories require `TransitionIndependenceWitness`; an empty dependency list no longer identifies arbitrary permutations.
- A routing-validated solver compilation requires a passing preservation receipt bound to the exact source/specification/QoI/representation/transform.
- Geometry identity now binds root QoI, verifier/environment subject, cost algebra and construction version in addition to operator basis/map/chart.

## Still recommended implementation hardening

1. Replace the naked `verifier_passed: bool` in `solution_assembly.py` with an audited proof/verifier receipt bound to the final certificate artifact hash.
2. Replace the development-only additive `PathCostVector` semantics with a registered typed coordinate algebra before making theorem-level multiobjective-distance claims.
3. Add a `NavigationQuotientValidation` object distinct from the existing TCSQ/QoI sufficiency validation.
4. Add explicit geometry certification class and admissibility/consistency tests where a heuristic wants A*-style theorem rights.

## Core theorem obligations

### Path quotient
If `~` is an endpoint-preserving congruence on verified paths, the quotient preserves source/target reachability. Cost preservation is separate.

### Map expansion monotonicity
Under a frozen subject, adding verified edges cannot invalidate an old verified route or worsen the best-known route frontier.

### Operator expansion monotonicity
If `Omega subset Omega'` and old operator semantics remain fixed, the reachable set under `Omega'` contains that under `Omega`. Therefore current-basis nonreachability is not future mathematical impossibility.

### Navigation quotient
Exact reachability preservation requires target-label preservation and suitable two-way simulation/lifting. One-way abstraction supports only one-way claims.

### Local descent
A policy mapping every non-goal solvable state to a verified successor with strictly lower rank in a well-founded order terminates at a goal if all reachable minima are goals.

### Authority noninterference
Map, quotient, geometry and navigation updates grant no theorem authority; only original-semantics verification plus the ordinary Orion assurance gate can change mathematical authority.

## Empirical questions intentionally left open

These are not mathematical gaps to hide; they are the actual research programme:

- Does a useful locally navigable geometry exist on held-out theorem families?
- Is bounded local branching sufficient where greedy descent fails?
- Is one global geometry possible, or only a multi-representation local atlas/network?
- Does path/concurrency quotienting save enough search to repay independence checking?
- Does MDD reliably diagnose geometry versus representation versus operator-basis failures?
- Does VSC beat simpler solver selection after compilation cost?
- Do flow/diffusion/conductance dynamics add value over best-first search on the same geometry?

## Claim boundary

Use:

```text
VTG_FORMAL_CORE_SPECIFIED
LOCAL_NAVIGABLE_GEOMETRY_EXISTENCE_UNRESOLVED
GLOBAL_METRIC_GEODESIC_OR_MANIFOLD_STRUCTURE_NOT_CLAIMED
NO_ROUTE_UNDER_REGISTERED_SUBSTRATE != MATHEMATICAL_IMPOSSIBILITY
```

Do not use `MATHEMATICAL_THEORY_COMPLETE` in the absolute sense. The defensible status is that the current formal gaps have been exposed and turned into explicit axioms, certificates, propositions or empirical falsifiers; additional hidden errors remain possible and should be sought by independent review and mechanization.
