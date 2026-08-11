# Same-context expert review — NS-B1 pre-candidate packet

**Review authority:** role-separated same-context review only; **not independent peer review**.

**Atom:** `NS-B1` — classify the Type-I rescaled blow-up object before proposing a new rigidity theorem.

## Expert cell

### 1. PDE regularity lead

**Background:** 3D incompressible Navier–Stokes regularity, suitable weak solutions, local energy inequalities, epsilon-regularity.

**Delegated checks:** bind the atom to the exact Clay statement; separate smooth/local/weak solution classes; audit the CKN and Type-I assumptions.

**Finding:** the active reduction is legitimate only if every rescaling/compactness step retains the precise suitable/mild hypotheses used by the downstream theorem. “Type-I” must never be used as a single unqualified norm condition.

**Strongest objection:** excluding one Type-I formulation or one ancient subclass cannot be promoted to exclusion of all finite-time singularities.

**Vote:** `PROCEED_WITH_SOURCE_MATRIX`.

### 2. Blow-up and renormalization lead

**Background:** singularity rescaling, ancient solutions, self-similar/DSS analysis, concentration-compactness.

**Delegated checks:** distinguish stationary, periodic, and general complete rescaled trajectories; inspect the Albritton–Barker reduction and persistence-of-singularity logic.

**Finding:** the fixed-point representation is useful but dangerous. Exact self-similarity is only one orbit type. A generic Type-I rescaled limit can be a broader ancient trajectory.

**Strongest objection:** no current packet ingredient forces convergence of the renormalized trajectory to a fixed point or periodic orbit.

**Vote:** `PROCEED_WITH_ORBIT_CLASSIFICATION_FIRST`.

### 3. Analogy and method-transfer lead

**Background:** critical PDEs, geometric blow-up methods, renormalization/dynamical-systems transfer.

**Delegated checks:** compare Navier–Stokes with contexts where compactness-rigidity closes; identify enabling assumptions that do not transfer.

**Finding:** the renormalization fixed-point/limit-cycle/general-trajectory analogy survives the structural witness gate. The missing enabling structure is precisely what many neighboring critical problems obtain from a monotonicity formula, coercive Lyapunov quantity, or stronger compactness. No such principle is available here at the required strength.

**Strongest objection:** importing a compactness-rigidity template without an inherited monotone/critical quantity merely renames the Navier–Stokes obstruction.

**Vote:** `RETAIN_ANALOGY_PROPOSAL_ONLY`.

### 4. Adversarial falsification lead

**Background:** hostile examples, weak-limit pathology, pressure nonlocality, PDE counterexample design.

**Delegated checks:** try to falsify shortcuts before they become candidates.

**Finding:** four immediate hostile tests must be frozen for future candidates:

1. `fixed-point-only`: does the argument say anything about a nonperiodic bounded rescaled trajectory?
2. `critical-norm-smuggling`: does it assume `L^3` or another criterion that has not been derived from the Type-I hypothesis?
3. `weak-limit-vanishing`: can the purported singular core disappear in the chosen topology?
4. `far-field-pressure`: does localization lose the global pressure/decay hypothesis used by the Liouville step?

Forward self-similar/DSS existence is a useful calibration showing that scale invariance alone is not a contradiction.

**Strongest objection:** a proof that passes only the stationary-profile test has low partition power because that class is already known to be heavily constrained.

**Vote:** `BLOCK_NEW_RIGIDITY_CANDIDATE_UNTIL_MATRIX`.

### 5. Formal-methods lead

**Background:** theorem statement binding, quantifier audit, proof dependency/trust boundaries.

**Delegated checks:** identify what must be formalized before any new theorem claim.

**Finding:** a future candidate needs explicit domains in space/time, solution class, pressure normalization, scaling center, topology of convergence, all inherited bounds, and exact quantifier order. The implication `Type-I singularity -> ancient class P -> trivial` must be represented as separate proof-DAG edges; neither edge can be hidden inside prose.

**Strongest objection:** phrases such as “bounded ancient solution” or “Type-I” are too coarse unless tied to a precise source definition.

**Vote:** `PROCEED_WITH_TYPED_IMPLICATION_GRAPH`.

### 6. Novelty and research-value lead

**Background:** mathematical literature mapping, novelty risk, information-value prioritization.

**Delegated checks:** decide whether the first action would rediscover known self-similar or critical-norm criteria.

**Finding:** another exact self-similar exclusion has low expected information value unless it materially weakens known hypotheses. The highest-value next step is a notation-normalized implication/counterexample matrix that shows which bridge is genuinely absent from the source literature.

**Strongest objection:** generating a “new” Liouville theorem before this normalization has high rediscovery and assumption-duplication risk.

**Vote:** `PROCEED_WITH_SOURCE_NORMALIZATION`.

## Cell discussion and preserved disagreement

The regularity and formal-methods leads favor a very narrow source-defined Type-I atom. The blow-up lead would like to retain a broader ancient-solution view so the representation does not overfit one norm. The adversarial lead agrees with the broader view but refuses any candidate until fixed/periodic/general trajectories are separated. The novelty lead argues that the cheapest high-information action is literature/implication normalization rather than proof search.

No role claims that `NS-B1` is close to solving the root. The strongest consensus objection is:

> **Even a complete Type-I exclusion leaves Type-II open, and fixed-point/self-similar rigidity is strictly weaker than full Type-I ancient-solution rigidity.**

## Decision

Recommended search mode:

- `REFLECTIVE_RESTRUCTURE`
- `CONTRASTIVE_DISCRIMINATION`

Not selected yet:

- unrestricted theorem invention;
- target-specific scalar criterion invention;
- another fixed-profile proof;
- Type-II exploration before the Type-I implication graph is learned.

**Next action:** machine-audit the strict pre-candidate packet, then build the source-bound implication/counterexample matrix. Only after that matrix identifies a smallest open bridge may candidate generation begin.
