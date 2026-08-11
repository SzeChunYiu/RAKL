# SELF_RAKL_RESEARCH_042 — Epistemic gain, failure saturation, and failure-cause atoms

**Status:** `SELF_RAKL_SOURCE_BOUND_PROPOSAL / METHOD_RESEARCH / NO_CAPABILITY_UPGRADE_CLAIM`

## Frozen question

What should an autonomous discovery system optimize while attacking a difficult problem? In particular:

1. Is “maximize failure volume” a good objective?
2. What does it mean when the failure-experience lattice stops growing?
3. When should repeated failure trigger a new method/operator basis rather than another candidate?
4. Should explaining why a candidate failed become a first-class research problem of its own?

This note treats the P-versus-NP programme as a calibration environment for RAKL itself. It does not claim that the literature below proves that the proposed RAKL controller is optimal.

## Atomization

- **A42.1 — value of a failure.** Distinguish raw failure count from information gained by a failed test.
- **A42.2 — action selection.** Decide which candidate/test to run next when many plausible routes exist.
- **A42.3 — saturation diagnosis.** Distinguish genuine method-basis exhaustion from repeated low-diversity search, underexplored context, coarse failure taxonomy, or actual convergence toward a solution.
- **A42.4 — failure-cause research.** Treat competing explanations of a failure as child atoms that can themselves be solved/refuted.
- **A42.5 — memory feedback.** Feed scoped successful tools and normalized failure experience back into future candidate selection.

## Source-bound analogous contexts

### S42.1 — disagreement/version-space active learning

Primary sources in active learning select queries where surviving hypotheses disagree and analyze how observations shrink the current version space rather than maximizing the number of wrong hypotheses. Relevant anchors include Cortes et al., *Active Learning with Disagreement Graphs*, ICML 2019, and the broader version-space/disagreement literature.

**Transfer:** RAKL should prefer a candidate/falsifier whose possible outcomes distinguish large, structurally different portions of the surviving method/hypothesis space.

**Disanalogy:** mathematical research does not generally provide a finite calibrated hypothesis class or trustworthy probability measure over candidate proofs.

### S42.2 — Bayesian experimental design / entropy search

Bayesian experimental design commonly formulates experiment choice as maximizing expected information gain. Entropy Search similarly chooses evaluations to learn about the optimizer rather than merely obtaining locally good objective values. Primary anchors include Hennig–Schuler, JMLR 2012, and later information-based Bayesian optimization work.

**Transfer:** “failure volume” is useful only insofar as it is a proxy for expected contraction of uncertainty.

**Disanalogy:** RAKL often lacks a justified posterior over mathematical mechanisms, so exact mutual information should not be fabricated. Structural surrogates or robust/minimax bounds are safer.

### S42.3 — adaptive submodularity

Golovin–Krause introduced adaptive submodularity for sequential choices under partial observation. When the utility has diminishing returns, greedy adaptive selection can have strong approximation guarantees.

**Transfer:** repeated failure-family discoveries should normally have diminishing marginal value. A controller should explicitly measure marginal information gain rather than reward repeated copies of the same failure mode.

**Disanalogy:** no claim is made that RAKL's research utility is currently adaptive-submodular.

### S42.4 — counterexample-guided abstraction refinement

CEGAR starts with an abstraction and uses counterexamples to refine it. Invalid/spurious counterexamples diagnose what the current abstraction omits; the response is to refine the representation rather than merely rerun the same verifier. Primary source: Clarke, Grumberg, Jha, Lu, Veith, CAV 2000 / JACM 2003.

**Transfer:** a failed mathematical candidate may expose a missing structural coordinate, missing invariant, bad abstraction, or wrong method assumption. That diagnosis can become a new atom whose resolution improves the search representation.

### S42.5 — novelty search

Lehman–Stanley showed that direct objective optimization can be deceptive in some search spaces and that behavior novelty can uncover useful stepping stones. This does not make novelty universally optimal.

**Transfer:** when objective-directed search repeatedly revisits the same failure basin, RAKL should increase search-basis diversity rather than merely generate more objective-looking candidates.

## Derived result R42.1 — do not maximize failure count

Raw failure count is an unsafe objective. It can be maximized by generating obviously bad candidates and produces no guarantee of useful learning.

The primary control objective should instead be **expected epistemic contraction**: choose the next bounded action whose possible outcomes are expected to reduce uncertainty about the active atom, its failure causes, method applicability, or proof obligations as much as possible per unit cost and verification debt.

A conceptual utility is

```text
U(a) = E_o[ΔV(o)] / cost(a) - verification_debt(a) - boundary_risk(a)
```

where `V` is a registered uncertainty/possibility volume and `o` ranges over result branches. In settings without defensible probabilities, replace the expectation with bounded branch scores, committee disagreement, robust worst-case contraction, or another explicitly registered surrogate.

`ΔV` may be decomposed operationally into non-authoritative planning coordinates:

```text
ΔK  verified knowledge / proof-DAG contraction
ΔF  normalized failure-family information
ΔC  context / representation coverage
ΔT  scoped reusable-tool information
ΔD  diagnosis discrimination among failure causes
ΔM  evidence about a method-basis or ontology gap
```

These coordinates are for action selection only; they do not mint theorem authority.

## Derived result R42.2 — failure information volume

A negative result is valuable when it does one or more of the following:

- eliminates a broad class of candidates rather than one literal candidate;
- identifies a broken assumption shared by several methods;
- exposes a previously missing structural coordinate;
- separates competing explanations of the obstruction;
- yields a reusable impossibility/upper-bound checkpoint;
- identifies a repair condition that can be tested cheaply;
- demonstrates that a representation or method basis is systematically inadequate.

Therefore define a diagnostic **failure information value**, not a success metric, from structural elimination and diagnosis gain with a redundancy penalty. Two failures with the same normalized cause should have sharply diminishing marginal value.

## Derived result R42.3 — a failure creates a second research programme

When candidate `C` fails, do not store only `C -> REFUTED`.

Create a **failure-cause atom set**:

```text
C failed
  -> D1: wrong statement/specification?
  -> D2: source/target model mismatch?
  -> D3: hidden assumption violated?
  -> D4: representation loses load-bearing structure?
  -> D5: method is too weak but directionally correct?
  -> D6: genuine impossibility for this method class?
  -> D7: checker/computation/implementation failure?
  -> ...
```

Each material diagnosis may become a child research atom with its own context packet, analogues, tool/failure-memory review, falsifiers, and success criteria. Confirmed causes update the failure lattice; disproved diagnoses remain negative history.

The failure-cause DAG and the positive solution DAG are cross-linked. Solving a failure-cause atom may create the missing representation or tool that later closes the parent theorem.

## Derived result R42.4 — failure-lattice saturation is ambiguous

A low rate of new failure-lattice growth does **not** by itself imply “invent new methods.” At least these cases must be distinguished.

| Failure novelty | Verified knowledge gain | Candidate/method diversity | Context coverage | Interpretation | Response |
|---|---:|---:|---:|---|---|
| low | high | any | any | convergence / productive success | continue current route |
| high | low/moderate | high | growing | productive exploration | continue; normalize failures |
| low | low | low | any | search degeneracy / repeated basis | diversify candidates and analogues |
| low | low | high | low | underexplored context | expand context/literature/representations |
| low | low | high | high | plausible method-basis gap | open metacognitive method-basis atom |
| low structural novelty but many repeated instances | low | high | high | failure family saturated | seek theorem-level characterization/repair or change basis |

Thus a method-basis escalation should require evidence that **both** failure novelty and knowledge gain are stagnant **after** candidate diversity and context coverage are sufficiently broad.

## Proposed controller: Epistemic Frontier Control

Before selecting the next candidate, compute a bounded frontier portrait over a recent window and the persistent memories:

```text
knowledge_gain_rate
failure_family_novelty_rate
failure_redundancy_rate
candidate_structural_diversity
method_family_diversity
context/analogue coverage
reusable_tool_gain_rate
unresolved_failure_diagnosis_mass
proof-obligation closure rate
```

The controller should classify the state before choosing an action:

- `EXPLOIT_CURRENT_ROUTE`
- `RUN_HIGH_DISAGREEMENT_FALSIFIER`
- `EXPAND_CONTEXT`
- `DIVERSIFY_CANDIDATE_BASIS`
- `SOLVE_FAILURE_CAUSE_ATOM`
- `FORMALIZE_FAILURE_FAMILY`
- `OPEN_METHOD_BASIS_GAP`
- `OPEN_ONTOLOGY_GAP`

## Search objective: partition power, not failure volume

A useful approximation to the information-gain principle is **counterfactual partition power**.

For each proposed test/action, freeze the plausible result branches and ask:

1. Which surviving hypotheses/method families predict each branch?
2. How much of the current uncertainty would each branch eliminate or reclassify?
3. Would a negative result create a genuinely new failure family or only another instance of a known one?
4. Would a positive result create a reusable scoped tool or close a proof obligation?
5. Which branch is least informative?
6. Is there a cheaper test producing a better partition?

Prefer actions whose branches disagree strongly and remain informative even in the least convenient outcome.

## Implication for P versus NP calibration

The P/NP lane should not optimize “number of refuted ideas.” Its recent value came from refutations such as padding/threshold cancellation and restricted-vs-unrestricted reuse gaps because they removed **classes of reasoning**, not because they incremented a failure counter.

For the current reuse-stable-invariant obstruction, the next strict RAKL cycle should first build the post-hardening context/memory/trace packet. Candidate selection should explicitly compare actions by partition power: e.g. whether an attempted invariant, upper-bound construction, or failure-cause investigation would most sharply distinguish the surviving structural possibilities.

## Proposed implementation atoms

- **SR42-I1 — FailureCauseDAG.** Typed diagnosis nodes/edges cross-linked to candidate and proof DAG.
- **SR42-I2 — EpistemicFrontierSnapshot.** Windowed rates for knowledge gain, failure novelty/redundancy, candidate diversity and context coverage.
- **SR42-I3 — SaturationClassifier.** Fail-closed diagnostic implementing the table above; no single `failure_count` threshold.
- **SR42-I4 — ActionBranchPacket.** Frozen branch predictions and uncertainty partitions before an expensive action.
- **SR42-I5 — EpistemicActionScore.** Planning-only robust/disagreement/information surrogate with explicit costs and debt.
- **SR42-I6 — Metacognitive escalation.** `OPEN_METHOD_BASIS_GAP` only when stagnation survives diversity/coverage checks.

## Primary-source anchors

- Corinna Cortes et al., *Active Learning with Disagreement Graphs*, ICML 2019, PMLR 97.
- Philipp Hennig and Christian J. Schuler, *Entropy Search for Information-Efficient Global Optimization*, JMLR 13, 2012.
- Daniel Golovin and Andreas Krause, *Adaptive Submodularity: Theory and Applications in Active Learning and Stochastic Optimization*, 2010/2011.
- Edmund M. Clarke, Orna Grumberg, Somesh Jha, Yuan Lu, Helmut Veith, *Counterexample-Guided Abstraction Refinement*, CAV 2000; expanded JACM 2003.
- Joel Lehman and Kenneth O. Stanley, *Abandoning Objectives: Evolution Through the Search for Novelty Alone*, Evolutionary Computation 19(2), 2011, DOI 10.1162/EVCO_a_00025.

## Authority boundary

This is a source-informed RAKL design hypothesis. It does not establish that the proposed utility is mathematically optimal, that RAKL's research process is adaptive-submodular, or that the new controller improves open-problem solving. Those are empirical/formal validation atoms.
