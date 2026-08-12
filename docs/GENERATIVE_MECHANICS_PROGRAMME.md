# Generative Mechanics — a Method-Saturation Programme

Status: research proposal / synthesis. Proposal-only; no canonical authority.
Source: a five-domain completeness audit of the three RAKL mechanics (mathematics,
science, engineering, philosophy, and LLM-vs-human problem-solving), read against
the papers and the `docs/` method layer.

---

## 1. The question, and the only honest form of its answer

"Are the three mechanics complete — do they reproduce how humans (and AIs) actually
solve problems?" The honest answer is not a list ("here are all the methods"), which
is unfalsifiable. It is a **bounded-saturation claim over the semantic space of
problem-solving primitives**:

> Observe how humans and AIs solve problems across heterogeneous, lexically-independent
> domains; extract each method primitive; deduplicate primitives in semantic space; and
> track whether the primitive **basis** stops growing. When *K* heterogeneous rounds add
> nothing fundamentally new under a fixed basis, the method set is **bounded-saturated**
> relative to those sources, that basis, and that horizon. Any newly observed primitive
> reopens it.

This is Paper I's own bounded-saturation rule, turned on RAKL's own method basis — the
"meta-lattice whose object is RAKL." Three constraints, forced by RAKL's own results,
keep it honest:

1. **Bounded, never absolute.** Paper I proves open-world non-certifiability: no finite
   transcript shows an unknown method does not exist. "1000 episodes, no new primitive"
   is a certificate *under a declared basis*, not a proof of human-completeness.
2. **The de-duplication engine is Paper II + the Apple Principle.** "Generalize in
   semantic space" requires deciding *when two methods are the same method*.
   Backward-chaining (math), root-cause analysis (engineering) and Socratic "how do you
   know?" (philosophy) may be one latent primitive under three vocabularies — different
   projections of one object. Deciding that is a directional structural witness.
3. **Heterogeneous, lexically-independent sources**, or "saturation" is a vocabulary
   artifact of sampling one community.

The five audits below are **rounds 1–5** of this ledger — already convergent, which is
*suggestive* of approaching saturation, not yet a certificate (five expert reads are not
1000 frozen episodes under a frozen equivalence metric).

---

## 1a. Motivation: why discovery is slow, and the two-stroke generalized method

Human discovery of a single hard result took generations, but most of that time was
**not** the creative leap. It was compressible overhead: building prerequisite towers,
serial mortal bandwidth with lossy transmission, redundant un-shared re-search of the
same dead-ends, and being stuck in the wrong representational frame. A machine changes
those constants --- perfect negative-history memory (no redundant re-search), true
parallelism, no mortality, instant transmission --- which is exactly evolutionary/cultural
search with civilizational constants (the FunSearch/AlphaEvolve/AlphaProof pattern: model
as mutation, verifier as selection, memory as inheritance, parallelism as population). The
compression is real but **gated by verification, not generation**: you can only compress a
field as fast as you can *check* it, some dependency depth is irreducibly serial, and
parallelism buys orders of magnitude, not omniscience.

It is tempting to conclude the whole project is: **saturate the lattice, and the solution
is contained in it.** That is exactly half right, and the missing half is the point of this
programme:

- **CLOSE (saturate the lattice).** RAKL's closure operator is extensive/monotone/idempotent;
  its fixed points form a complete lattice and a saturated state is a fixed point. Closing
  the lattice reveals *everything the current basis entails* --- the deductive, parallelizable,
  compressible half RAKL already does well. For any problem whose answer is a compatible
  gluing of known atoms, saturation finds it.
- **The word "contained" is what open-world non-certifiability forbids.** The lattice is built
  from a *finite basis*; saturation is *bounded* relative to declared atoms/routes/horizon.
  The solution is in the lattice **iff the basis already spans its primitives.** If the
  breakthrough needs a new atom (a reframe, an affordance, a concept the field never posed),
  it is *not* in the current lattice, and **closure never creates it** --- closure adds only
  what the atoms already imply. (Defining the lattice over "all possible atoms" is the Library
  of Babel: infinite, non-enumerable, and vacuous; the real question is reachability by bounded
  goal-directed expansion, which cannot be certified in finite time.)
- **GROW (expand the basis).** The generative mechanics inject primitives the lattice did not
  contain --- abduction, representation change/reframing, affordance discovery, cross-domain
  JUMP, constructive invention, concept-evolution under counterexample.

The generalized discovery method is therefore a **two-stroke loop**: GROW the basis, CLOSE the
lattice, inspect the residual, and bounded-saturate over *both* (stop only when neither
heterogeneous basis-growth nor closure adds anything substantive; reopen on any new primitive).
RAKL today has the CLOSE stroke; this programme is the GROW stroke. Saturate-the-lattice is
exactly half the method --- and the generative mechanics are what stop it from being an engine
that closes forever over too small a world.

## 2. Diagnosis (what the five rounds agree on)

**RAKL is a superb refutation / governance engine and an absent generative engine.**

It is strong — often superhumanly — on the *conservative / hygienic* half of discovery:
falsification, append-only negative history, replication and evidence-independence,
prior-art / novelty audit, preregistration, model criticism, robustness, scoped
analogical transfer, bounded stopping. It is weak-to-absent on the *ampliative / active /
evaluative* half: proposing boldly, evolving a concept under attack, trying hardest to
kill what you proposed, deciding what is worth pursuing, and judging what a question means.

Per domain, the deepest single hole:

| Domain | Deepest missing move |
|---|---|
| Mathematics | **Lakatos concept-evolution** — a counterexample can only *reject*; it can never *edit the definition/statement* (monster-barring, lemma-incorporation). RAKL is fail-closed, so it cannot create concepts. |
| Science | **Severity / corroboration** — the verifier is pass/fail against *existing* evidence; a claim surviving ten weak checks is indistinguishable from one surviving a single brutal, could-have-killed-it test. |
| Engineering | **Trade-off dissolution** — RAKL records Pareto fronts but never tries to *break* one (TRIZ ideality); and failure-learning is *reactive*, never prospective (no FMEA before building). |
| Philosophy | **Value / taste** — RAKL governs a *given* target but cannot *choose* targets by importance/depth/fruitfulness; and it never asks *what a question means* (well-posedness). |
| LLM path | **Generator-level diversity, a validated taste oracle, per-claim calibration** — the workspace itself concedes it can only rearrange locally-generated objects. |

The LLM round adds the "better path" reading: human heuristics are *one specialization*
of a universal problem-solving operator set, tuned to the human strength/weakness profile.
RAKL is the **re-specialization of the same operators for the inverted LLM profile** —
amplify breadth/throughput/tireless recall, externalize memory, substitute checkable
verification, gate authority so fluency cannot self-promote. The framework is therefore
positioned as the *LLM-optimal generalization* of problem-solving, not a new epistemology.

---

## 3. Method-primitive ledger (round 0, abridged)

Coverage: FULL (executable mechanic), PARTIAL (doc-layer / adjacent), NONE.

| Primitive | Domains attesting | Coverage | Mechanic / gap |
|---|---|---|---|
| Analogical / structural transfer | all | FULL | II (directional witness) |
| Decomposition / subgoaling | all | FULL | I / problem-solving algebra |
| Counterexample / falsification | math, sci | FULL | I (REFUTED, negative history) |
| Preregistration / freeze-before-outcome | sci | FULL | II, III |
| Replication & evidence-independence | sci | FULL | I |
| Prior-art / novelty audit | all | FULL | I (nearest-work, saturation) |
| Robustness / assumption sensitivity | sci, eng | FULL | model-criticism docs |
| Representation change | math, llm | FULL | II / algebra (cheap LLM strength) |
| Bounded stopping | all | FULL | I (bounded saturation) |
| **Severe testing / corroboration** | sci | **NONE** | → severity coordinate `S` |
| **Inference to best explanation** | sci | **NONE** | → explanatory-virtue comparator |
| **Consilience / unification** | sci | **NONE** | → consilience coordinate |
| **Discriminating experiment choice** | sci | PARTIAL | doc-only `D_g` |
| **Programme appraisal (progressive/degenerating)** | sci | **NONE** | → appraisal ledger |
| **Concept evolution under refutation (Lakatos)** | math | **NONE** | → `DIALECTIC` |
| **Proof-scheme library (induction/contradiction/...)** | math | **NONE** | → `PROOF_SCHEMA` |
| **Target strengthening (inventor's paradox)** | math | PARTIAL | → `STRENGTHEN_TARGET` |
| **Trade-off dissolution (TRIZ ideality)** | eng | **NONE** | → contradiction router |
| **Prospective failure anticipation (FMEA)** | eng | **NONE** | → anticipated-failure lattice |
| **Margin / worst-case design** | eng | PARTIAL | → robustness-budget |
| **Problem selection by value / taste** | phil, sci | PARTIAL (doc, flagged missing) | → value/promise projection |
| **Question well-posedness / concept clarification** | phil | PARTIAL (stub) | → well-posedness certificate |
| **Dialectical synthesis / steelmanning** | phil | PARTIAL | → synthesis operator |
| **Inquiry ethics / dual-use** | phil | **NONE** | → fail-closed ethics gate |
| **Aesthetic / depth / unification salience** | math, phil | **NONE** | → salience selector |

The FULL rows are the "hygiene" half; the NONE/PARTIAL rows are the missing half, and they
cluster into exactly three phases the current three mechanics under-serve.

---

## 4. The missing half: three proposed mechanics

RAKL today has three mechanics — **I Epistemic** (govern), **II Structural** (transfer),
**III Method-evolution** (learn). The audit says the missing half is three more, one per
under-served phase of the research loop `propose -> stress-test -> select`:

### Mechanic IV — Generative Mechanics (*propose boldly*)
Operators that **make** candidates, each emitting proposal-only objects with no authority:
- `DIALECTIC` — refutation-driven concept/statement evolution (monster-bar, exception-bar,
  lemma-incorporation, concept-stretch) with positive-preservation and anti-ad-hocness checks.
- `PROOF_SCHEMA` — typed proof architectures (induction / contradiction / infinite-descent /
  extremal / pigeonhole) instantiated into checker-verifiable obligation sets.
- `STRENGTHEN_TARGET` — inventor's-paradox substitution `τ′⇒τ` verified *before* `τ′` is attempted.
- Contradiction-dissolution router — detect an empirical trade-off, route to decoupling operators, estimate ideality.
- Anticipated-failure lattice — run the failure machinery *forward*: enumerate failure modes before building, score severity × occurrence × detectability.
- Generator-level far-concept diversity — close the workspace's own conceded gap.

### Mechanic V — Ampliative / Severity Mechanics (*earn confidence*)
Turn "survived a check" into "survived the cruelest check", via **new coordinates on the
authority poset** (reusing Paper I's own no-scalar-collapse theorem):
- Severity ledger — add coordinate `S`; `UNSEVERE_PASS` cannot raise `S`.
- Discriminating-experiment selector — expected separation per cost over a live rival set.
- Explanatory-virtue comparator (IBE) — Pareto order over rivals by scope / mechanism depth / simplicity / ad-hoc-count.
- Consilience certificate — add a unification coordinate counting *independent* evidence classes (Paper II `I⁻` guards against false unification).
- Research-programme appraisal — progressive / degenerating / stagnant, a *stop-and-abandon* signal distinct from saturation.
- Margin / worst-case certificate; causal-identification certificate for the `M` coordinate.

### Mechanic VI — Evaluative / Value Mechanics (*choose what matters*)
The judgment front-end that decides *what to pursue and what a question means*:
- Value / promise projection — `v(g)=(importance, novelty, tractability, discriminatory-leverage, cost, risk)` as an **incomparable poset**, not a scalar; the missing "research taste" fiber.
- Salience selector — depth / unification / compression salience as a *search-priority* signal only (never authority).
- Question well-posedness certificate — `WELL_POSED / AMBIGUOUS / PRESUPPOSITION_FAILS / VERBAL_DISPUTE` via minimal-twin term-sense probes; an unresolved ambiguity is an open fiber.
- Fitness-for-purpose stop — halt on decision-sufficiency, not only no-gain saturation.
- Inquiry-ethics / dual-use gate — fail-closed, non-compensatory, mandatory human signoff on the review band.

**Every proposed mechanic keeps the four invariants that make RAKL RAKL:** proposal-only
(non-sovereign); poset, never scalar; frozen benchmark/threshold before outcome access;
and explicit model-vs-system attribution.

---

## 5. The saturation protocol (how completeness gets certified, not asserted)

1. **Sample** problem-solving episodes across maximally heterogeneous sources (math, science,
   engineering, philosophy, LLM-native, and deliberately alien: evolutionary search, markets,
   child/animal cognition), with at least one lexically-independent route per round.
2. **Extract** each episode's method primitives.
3. **Deduplicate** in semantic space via a *frozen* equivalence metric = Paper II directional
   structural witness (same latent primitive under different vocabularies collapses to one node).
4. **Track** basis growth per round; log every new primitive with its first-witness source.
5. **Declare** bounded method-saturation after *K* consecutive heterogeneous rounds add zero
   new primitives under the frozen metric — and publish the ledger.
6. **Reopen** on any later primitive that the metric cannot map to an existing node.

The five audits are rounds 1–5 and already convergent; a real certificate needs the frozen
metric and many more, ideally-adversarial, rounds.

---

## 6. Honesty ledger (what may and may not be claimed)

- **Bounded, not absolute** — completeness is relative to declared sources/basis/horizon.
- **System vs. model** — nearly every "LLM beats human" gain here is a *system* win
  (parallelism, external oracles, externalized memory, typed routing), reported as
  system-level uplift via the four-arm attribution and the `ΔC` vector, never as "the model
  reasons better." The current empirical precursor is a *negative* result and no
  capability-gain claim is licensed.
- **Human-in-the-loop where required** — the value weights (what counts as important) and the
  ethics decisions remain human; the machine ranks and triages, humans choose and decide.

---

## 7a. Can the mechanics produce a breakthrough? (the fire test)

Test case: the first hominin realization that fire --- a dangerous natural event ---
is a *controllable tool*. Decompose the breakthrough:

1. **Affordance noticing** --- see a new *use* in an existing phenomenon (abduction over a surprising regularity).
2. **Reframe** --- object "dangerous event" becomes "tool I control" (representation change).
3. **Cross-domain transport** --- apply it to new functions: cooking, warmth, defence, tool-hardening (JUMP).
4. **Constructive invention** --- devise a way to *make* it (friction, flint) --- a new operator.
5. **Value recognition** --- judge it worth pursuing despite the danger (value/promise).
6. **Retention & transmission** --- keep the method and teach it (method evolution).

Against RAKL's three current mechanics: JUMP (II) and retention (III) and the
`docs/` OWMD/constructive-invention layer cover 3, 4 and 6 in part. **But the spark
--- steps 1, 2, 5 --- has no executable mechanic**, and worse:

> **A fail-closed governance engine is structurally biased *against* breakthroughs.**
> When "use fire" is first proposed it has zero evidence, so today's verifier returns
> \texttt{CANNOT\_CHECK} or \texttt{REJECTED}. The very discipline that keeps RAKL from
> fooling itself would kill the breakthrough at birth.

So the honest answer is **no** --- the current three mechanics govern and refute; they
do not (and by fail-closed design, resist) originating a category-creating breakthrough.

What *would* let the system originate one is exactly the generative half, working
together, with a **protected speculative lane** as the crux:

- **VI Value/Promise** holds a *high-promise, low-evidence* proposal as worth pursuing
  (importance and novelty high, evidence low) instead of discarding it --- the antidote
  to fail-closed suppression.
- **I workspace `NOVEL`/`CHALLENGE` partitions** carry it with *no authority* (so it is
  neither rejected nor believed) while it is investigated.
- **IV Generative** (affordance/reframe discovery, abduction, representation change,
  cross-domain JUMP, constructive invention) does the enumeration that *surfaces* the
  candidate at superhuman breadth.
- **V Severity** designs the could-have-killed-it test that lets it *earn* authority
  rather than assert it.
- **IV `DIALECTIC`** crystallizes the new *concept/category* once it survives.

The honest limit RAKL's own ethos demands: **no mechanic guarantees a breakthrough.**
The creative leap is still bounded by the model and by serendipity. What the mechanics
change is the odds and the machinery around the leap --- (a) not *filtering out* the wild
idea by being too conservative; (b) *enumerating* affordances, reframes and cross-domain
jumps exhaustively so more candidate breakthroughs surface; (c) *recognizing and
protecting* a promising one; (d) *testing* it honestly; (e) *preserving and transmitting*
it. That converts breakthrough from "wait for a rare genius" into "search the
affordance/reframe space with perfect memory and no premature rejection" --- which is the
one place a machine can plausibly out-*system* human discovery. Until the generative and
severity mechanics exist and are saturation-certified, RAKL should claim only that it
governs and transmits breakthroughs, not that it originates them.

## 7. Recommendation

Publish this as a distinct paper — **"Generative Mechanics"** (or a trilogy IV/V/VI mirroring
I/II/III) — whose completeness argument *is* the method-saturation ledger of §5, not an
asserted list. That makes the human-completeness claim falsifiable and evidence-governed,
which is the only kind of completeness claim RAKL is permitted to make. The individual
mechanics can be prototyped and confirmed one at a time on frozen benchmarks (Paper II's
confirmatory-lane protocol), starting with the two highest-leverage and most self-contained:
the **severity coordinate `S`** (Mechanic V) and the **value/promise projection** (Mechanic VI).
