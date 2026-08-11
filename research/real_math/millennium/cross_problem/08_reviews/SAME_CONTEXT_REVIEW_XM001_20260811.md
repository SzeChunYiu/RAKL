# XM001 same-context expert review — root-bridge stability audit

**Atom:** `XM-ROOT-BRIDGE-001`  
**Authority:** `SAME_CONTEXT_REVIEW_ONLY / NOT_INDEPENDENT / PROPOSAL_SELECTION_ONLY`  
**Frozen context:** `sha256:bc11ed85c3987cd24998512641afbf0e8317d09aabf665f06852ef2a8c02f120`

This cell reviews one cross-problem question: whether the merged P-vs-NP C024 calibration failure supports a reusable *audit obligation* for routes that prove something on a surrogate object and then need a separate lift/limit/assembly step to reach a Millennium root. The cell explicitly rejects the stronger claim that the six problems share one mathematical obstruction.

## 1. Complexity / optimization lead

**Background:** circuit and communication complexity, LP/SDP relaxations, integrality gaps, lower-bound certificates.

**Finding.** C024 separates two facts that must not be conflated: the LP-dual local inequality is valid, while the relaxation is a poor primary proxy for the integral multi-fusion quantity on `G_NEQ`. The transferable content is therefore not the LP formula but the *calibration-first* rule: test whether a surrogate preserves the coordinate that the root quantity accumulates.

**Strongest objection.** Integrality is a discrete combinatorial phenomenon; calling a continuum limit an “integrality gap” would be false transfer.

**Delegated check.** Require every target mapping to state a different broken coordinate and a target-specific falsifier. Do not select `T-PNP-FRACTIONAL-SEMIFILTER-PACKING` for non-PNP work.

**Vote:** `ACCEPT_AUDIT_ABSTRACTION / REJECT_LITERAL_METHOD_TRANSFER`.

## 2. PDE / geometric-flow lead

**Background:** scale-invariant PDE estimates, blow-up analysis, concentration compactness, Ricci-flow singularity analysis.

**Finding.** Navier–Stokes issues #83/#88 already expose two bridge-sensitive boundaries: Type-I/profile rigidity is not automatically a classification of Type-II blow-up, and energy-class control is not automatically critical control. Perelman is a useful solved calibration because monotonicity was accompanied by non-collapsing/singularity-control machinery before global topological closure.

**Strongest objection.** “Bridge loss” is too generic unless the exact compactness or scale-critical coordinate is named; otherwise it just renames “hard step.”

**Delegated check.** Do not use Navier–Stokes as the first candidate target. Keep it as a warning until a concrete implication and adversarial profile family can be written with exact hypotheses.

**Vote:** `REVISE_TO_TARGET_SPECIFIC_WITNESSES`.

## 3. Mathematical-physics / spectral lead

**Background:** lattice gauge theory, transfer matrices, Osterwalder–Schrader reconstruction, continuum limits, spectral gaps.

**Finding.** Yang–Mills issue #85 exposes the cleanest exact discriminator. If `r(a,L)=lambda_1/lambda_0` and the physical gap is normalized as `Delta_phys(a,L)=-a^{-1} log r(a,L)`, then positivity of the dimensionless finite-lattice gap `-log r(a,L)` for every `a>0` does not by itself imply a positive continuum physical gap. The missing condition is quantitative in `a`, not merely pointwise positivity or volume-uniform positivity at fixed `a`.

**Strongest objection.** An arbitrary sequence `r(a,L)` is not a Yang–Mills transfer matrix and cannot refute a property of actual Yang–Mills dynamics.

**Delegated check.** Use the sequence only to falsify the *logical inference form*. State the minimum bridge obligation as a scaled liminf/uniform lower bound and make no claim that the bad sequence is physically realized.

**Vote:** `ACCEPT_YM_S1_AS_FIRST_CALIBRATION`.

## 4. Arithmetic geometry / number theory lead

**Background:** Hodge theory and algebraic cycles, arithmetic geometry, L-functions, local-global and realization problems.

**Finding.** RH issue #84 and Hodge issue #86 support the taxonomy only at the level of proof obligations: a spectral model still needs an exact arithmetic trace/positivity bridge, while a motivic/categorical/cohomological object still needs an actual algebraic-cycle lift. Those are structurally analogous preservation obligations but mathematically different maps.

**Strongest objection.** BSD currently has no persistent workspace visible in the repository, so inventing a BSD-specific failure family from general knowledge would violate the evidence-before-narrative rule.

**Delegated check.** Mark BSD `CANNOT_CHECK_PROBLEM_SPECIFIC_FAILURE` in this packet. Revisit only after its own root/context artifacts exist.

**Vote:** `ACCEPT_BOUNDED_TAXONOMY / BLOCK_BSD_FAILURE_INFERENCE`.

## 5. Formal methods / assurance lead

**Background:** typed proof obligations, proof DAGs, statement alignment, chronology and verifier boundaries.

**Finding.** A reusable audit can be made precise if each use records a tuple: `(surrogate object, surrogate certificate, root object, root-lifting map, preservation property, disanalogy, cheapest falsifier)`. The audit may certify that a weak implication is invalid; it cannot certify the missing positive bridge.

**Strongest objection.** A meta-tool promoted too broadly could become a narrative shortcut that falsely groups unrelated open problems.

**Delegated check.** Give any promoted tool explicit non-guarantees, require a `DifferenceWitness` on every cross-domain reuse, and keep root authority at zero.

**Vote:** `ACCEPT_WITH_FAIL_CLOSED_SCOPE`.

## 6. Adversarial transfer / meta-learning lead

**Background:** falsification design, analogy validation, scientific search policy, fixation detection.

**Finding.** The highest-information next action is not another literature sweep. It is a cheap target-specific counterexample to the weakest YM-S1 inference: “positive finite-lattice gap at every spacing (even uniformly in volume) implies positive physical continuum mass gap.” A single exact sequence can partition the search: if the implication fails abstractly, the YM lane must state and prove an `a`-scaled preservation bound before treating finite-lattice positivity as root progress.

**Strongest objection.** The counterexample is elementary and may merely formalize something the YM lane already knows.

**Delegated check.** Promote the result only as a reusable *screening tool*. Its value is preventing future lanes from spending cycles strengthening a surrogate before freezing the preservation modulus. Require future reuse benchmarks to show actual research-time savings or a pruned route.

**Vote:** `ACCEPT_AS_CALIBRATION_TOOL_CANDIDATE`.

## Cell decision

The cell selects **YM-S1 scaled-gap calibration** as the first action. It rejects literal transfer of the P-vs-NP LP and rejects any claim of a common Millennium theorem. The candidate action must prove only this narrow statement:

> Pointwise positivity of a dimensionless finite-scale gap, even when uniform in volume for each fixed lattice spacing, is logically insufficient to imply a positive physical continuum gap without an `a`-scaled quantitative lower bound.

The cheapest falsifier is `r(a,L)=exp(-a^2)`, independent of `L`. It must be presented as an abstract inference counterexample, not as a Yang–Mills model. If the counterexample is verified, the residual is to formulate the exact target-specific uniform/scaled bridge needed by YM-S1 and to test whether existing or future lattice/RG results actually supply it.
