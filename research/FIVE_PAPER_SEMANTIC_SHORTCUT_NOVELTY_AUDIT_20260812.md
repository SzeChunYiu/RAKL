# Semantic-shortcut system-level prior-art and novelty audit

**Internal audit cutoff:** 2026-08-12  
**Implementation lineage:** PR #376  
**Audit authority:** `INTERNAL_PRIOR_ART_AUDIT`  
**Independent successor:** #403

## Question audited

This audit does **not** ask whether analogy, case-based reasoning, failure repair, proof retrieval, external memory, skills, counterexample-guided synthesis or compositional search are new. Established work already answers that negatively.

The narrow candidate contribution is the executable combination:

```text
content-bound (O,T,O') transformation episodes
+ vocabulary-light obstruction fingerprint
+ invention-last SEARCH -> JUMP -> GLUE -> LIFT / CANNOT_CHECK
+ explicit source-to-target structural/precondition witness
+ full-effect SEARCH/JUMP vs partial-effect GLUE semantics
+ forbidden-loss gate
+ bounded candidate-accounted cross-problem exhaustion before LIFT
+ repeated-residual requirement
+ LIFT emits only a missing-transformation specification
+ proposal/search state is kept separate from scientific/theorem/novelty authority
```

The strongest defensible current novelty language is therefore about a **system-level fail-closed integration / governance contract**, not priority for the component ideas.

## Expert lenses used

The internal review deliberately separated five backgrounds:

1. **planning / case-based reasoning historian** — asks whether retrieval, replay, repair and partial-plan reuse are already present under older terminology;
2. **formal methods / theorem-proving specialist** — compares structure-aware premise/proof-fragment retrieval and verifier-gated search;
3. **program-synthesis specialist** — compares counterexample/property-guided repair, compositional synthesis and representation invention;
4. **agent-memory specialist** — compares episodic experience, hierarchical skills, selective retrieval and memory consolidation;
5. **scientific-assurance reviewer** — asks whether target transfer, provenance, bounded exhaustion and scientific-authority separation are materially distinct or just renamed standard controls.

The reviewers were same-process analytical roles, not independent external peer reviewers. #403 owns independent confirmation.

## Nearest prior-art families

### 1. Case-based planning and derivational analogy

#### Mostow (1989), derivational analogy

J. Mostow, *Design by derivational analogy: Issues in the automated replay of design plans*, Artificial Intelligence 40 (1989), DOI `10.1016/0004-3702(89)90048-9`.

The paper explicitly studies solving a new problem by replaying a previous design plan, modifying it where necessary. It compares representation/acquisition/retrieval of design plans, source-target correspondence, selection/adaptation of replayable steps and reuse of partial plans.

**Consequence for RAKL novelty:** retrieval + analogy + adaptation + partial reuse are old ideas. `JUMP` and parts of `GLUE` cannot be claimed as those ideas' invention.

#### Hammond (1989/1990), case-based planning and repair

K. Hammond, *Case-Based Planning: Viewing Planning as a Memory Task* (1989) and *Case-Based Planning: A Framework for Planning from Experience*, Cognitive Science 14 (1990), DOI `10.1207/s15516709cog1403_3`.

Case-based planning uses memories of past successes to construct/modify plans, failures to warn about impending problems, and repairs to address them. Hammond's repair work also uses causal explanations of failures to retrieve abstract repair strategies.

**Consequence:** experience memory, negative-history reuse, failure diagnosis and repair retrieval are established. RAKL's novelty boundary must lie in its typed/content-bound/governed contract or downstream integration, not the existence of these functions.

#### Veloso (1994), complete analogical experience cycle

M. Veloso, *Planning and Learning by Analogical Reasoning*, LNAI 886 (1994), DOI `10.1007/3-540-58811-6`.

The monograph describes construction, storage, retrieval and flexible reuse of problem-solving experience through derivational analogy.

**Consequence:** the broad phrase “learn by storing and reusing problem-solving transformations” is not novel.

### 2. Structure-aware proof retrieval and adaptation

#### PROMISE (2026)

Y. Ahn et al., *PROMISE: Proof Automation as Structural Imitation of Human Reasoning*, arXiv:`2604.05399`.

PROMISE represents theorem proving as stateful search over proof-state transitions, mines structural patterns rather than relying on shallow/surface retrieval, and retrieves/adapts compatible proof fragments.

**Consequence:** structure-aware retrieval of prior proof transformations is a very close modern neighbor. RAKL cannot claim novelty for “structural rather than lexical retrieval” alone.

#### Premise-retrieval systems

Current premise-retrieval systems such as LeanSearch v2 further establish that retrieval quality and formal proof success are tightly coupled.

**Consequence:** retrieval itself is an evaluated theorem-proving mechanism, not a new RAKL category. RAKL's distinct question is what target witness and governance are required before a retrieved transformation may license a proposal route.

### 3. Counterexample/property-guided synthesis and repair

#### Counterexample Guided Learning in the Large (2026)

H. Liu, F. Sala, T. Reps and A. Murali, *Counterexample Guided Learning in the Large using Reasoning Agents*, arXiv:`2606.11521`.

The system uses verifier counterexamples to refine LLM-generated symbolic hypotheses and reports substantial improvements in regex-induction tasks.

#### Property-Guided LLM Program Synthesis for Planning (2026)

A. Corrêa, A. Pereira and J. Seipp, *Property-Guided LLM Program Synthesis for Planning*, arXiv:`2605.16142`.

Candidate programs are checked against formal properties; violations produce concrete counterexamples that guide repair and reduce generation/evaluation cost.

**Consequence:** residual/counterexample-guided candidate refinement is established. RAKL cannot claim invention of “learn what is missing from failures” in the broad sense.

The narrower RAKL distinction is the chronology by which repeated residual structure can justify a **missing-transformation specification only after bounded retrieval/composition exhaustion**, while proof/scientific authority remains outside that proposal process.

### 4. Agent memory and skill libraries

Recent agent systems learn reusable trajectories, workflows or hierarchical skills from experience and retrieve them at inference time. This family materially overlaps RAKL's episode/lesson/tool memory and means external continual experience is not itself novel.

The important RAKL distinction, if it survives stronger review, is that transformation episodes are a **structural retrieval projection with explicit source authority, preconditions/effects/invariants/breakpoints and content identity**, and target transport never inherits source authority automatically.

## Component comparison

| RAKL component | Strong prior-art overlap | Internal audit conclusion |
|---|---|---|
| store prior problem-solving experience | case-based planning / analogical reasoning | established |
| retrieve structurally similar cases | analogy + structural proof mining | established / close |
| adapt a source solution to a target | derivational analogy | established |
| reuse partial source plans | Mostow / case-based planning | established |
| use failures/repairs as experience | Hammond / CEGIS families | established |
| counterexample/residual-guided refinement | CEGIS and 2026 reasoning-agent work | established |
| hierarchical external skills/method memory | agent-memory/skill literature | established |
| content-bound `(O,T,O')` episode with explicit source authority/preconditions/effects/invariants/breakpoints | partial analogues exist | candidate integration distinction |
| target mapping must account for every enabling source precondition and forbidden loss | analogy/transfer systems have correspondence/boundary concepts | candidate formal/governance distinction; needs strongest-parent audit |
| SEARCH/JUMP require complete desired effect; partial verified effects are GLUE-only | planning/composition analogues likely | candidate explicit fail-closed contract, not safe to claim broad conceptual priority |
| strict SEARCH→JUMP→GLUE→LIFT invention-last chronology | no identical contract found in bounded search | candidate system-level distinction |
| LIFT requires bounded candidate-accounted cross-problem coverage + repeated residual structure | CEGIS/exhaustive search analogues overlap | candidate compound gate; strongest-parent attack required |
| LIFT returns specification, not self-authorized tool/proof | assurance separation | candidate governance distinction |
| transformation memory cannot mint scientific/theorem/novelty authority | scientific assurance/provenance traditions overlap | RAKL integration distinction, not general invention of epistemic separation |

## Strongest-parent attack

The most serious challenge to the RAKL novelty boundary is not one paper but a combination:

```text
case-based / derivational analogy
+ structural proof retrieval
+ counterexample-guided repair/synthesis
+ compositional planning
+ evidence/provenance governance
```

Together these parents anticipate much of the conceptual space. Therefore the following broad claims are rejected by this audit:

```text
“first AI to use analogy for research”
“first system to store transformations”
“first system to learn from failed attempts”
“first system to reuse partial solutions”
“first invention-last system” (without a much deeper historical search)
“first structural retrieval system”
“first self-improving research memory”
```

The remaining candidate is an implementation-level/system-contract contribution: making these ideas interact under one content-bound, auditable, fail-closed pre-candidate protocol with explicit no-match coverage semantics and authority separation.

## Search limitations

This was a bounded internal search, not a global novelty certificate. Limitations include:

- terminology drift across planning, analogy, CBR, program synthesis, theorem proving and scientific-discovery literatures;
- incomplete access to older books/conference proceedings and non-indexed systems;
- possible prior systems that implement equivalent rules without the same names;
- system-level novelty may be anticipated by a combination of works even when no single source contains every component;
- same-process expert lenses are not independent external novelty reviewers.

The correct status is therefore:

```text
COMPONENT_NOVELTY: MOSTLY_PRECEDED / NOT_CLAIMED
FULL_CONTRACT_MATCH_FOUND: NO MATCH IDENTIFIED IN REGISTERED INTERNAL SEARCH
SYSTEM_LEVEL_NOVELTY: BOUNDED CANDIDATE ONLY
INDEPENDENT_NOVELTY_AUTHORITY: ABSENT
SUCCESSOR: #403
```

## Manuscript wording authorized by this audit

The five papers may use wording equivalent to:

> The contribution claimed here is the fail-closed integration and executable governance contract, not the invention of case-based reasoning, analogy, structural retrieval, skill memory, failure repair, partial-plan reuse or counterexample-guided synthesis individually. In a bounded internal primary-source search through 12 August 2026, we did not identify one source with the same complete content-bound SEARCH–JUMP–GLUE–LIFT contract; this is not a global priority certificate, and independent prior-art review remains open under #403.

The papers must **not** use absolute-first language on the basis of this audit.
