# Formal results and audit — RAKL × LLM Structural Bridge

These are architectural/mathematical statements, not empirical LLM results. Standard facts are labelled as such; no priority is claimed for elementary quotient or symmetry arguments.

## 1. Quotient sufficiency factorization — standard result, useful RAKL contract

Let `X` be the original problem space under fixed QoI/context `(q,c)`, and let

```text
Q_(q,c) : X -> Z_(q,c)
```

be a quotient/derived representation. Define `x ~_(q,c) y` iff `Q_(q,c)(x)=Q_(q,c)(y)`.

Let the original verifier/decision be

```text
F_(q,c) : X -> Y.
```

### Proposition

If `F_(q,c)` is constant on every equivalence class of `~_(q,c)`, then there exists a unique function on the image of the quotient,

```text
Fbar_(q,c) : im(Q_(q,c)) -> Y
```

such that

```text
F_(q,c) = Fbar_(q,c) o Q_(q,c).
```

### Proof

For each quotient value `z` in `im(Q)`, choose any `x` with `Q(x)=z` and define `Fbar(z)=F(x)`. This is well-defined because every other `y` with `Q(y)=z` is in the same equivalence class and therefore has `F(y)=F(x)`. Then `Fbar(Q(x))=F(x)` for every `x`. Uniqueness follows because every `z` in the image has at least one preimage.

### RAKL interpretation

TCSQ's load-bearing problem is **not** whether this theorem is new. It is how to establish, under bounded evidence, that the proposed erased coordinates really satisfy the constancy/sufficiency obligation, how to fail closed when they do not, and how to preserve source lineage/reconstruction/original verification.

SQ-1 provides an oracle upper-bound world where the factorization is exact. SQ-2 tests a finite registered intervention method for dependency discovery. SQ-3 must test net practical value.

---

## 2. Symmetric quotient geometry cannot represent every directional StructuralWitness

Let `A_(q,c)(x,y) in {0,1}` be a transfer-applicability relation. RAKL explicitly allows one-way transfer, so there may exist `x,y` for which

```text
A(x,y)=1
A(y,x)=0.
```

Consider any predictor that depends only on a symmetric similarity/distance of quotient embeddings:

```text
P(x,y) = h(s(z(x), z(y)))
```

with

```text
s(a,b)=s(b,a).
```

Cosine similarity, Euclidean distance and ordinary symmetric metric thresholds are examples.

### Proposition

If the target applicability relation contains any asymmetric pair, no predictor of the symmetric form above can be exactly correct on both directions of that pair.

### Proof

Symmetry gives

```text
s(z(x),z(y)) = s(z(y),z(x)).
```

Therefore

```text
P(x,y)=P(y,x).
```

But the target labels differ: `A(x,y) != A(y,x)`. At least one direction must be wrong.

### Corollary

A RAKL-native neural system cannot identify `StructuralWitness` applicability with task-conditioned quotient distance alone whenever the registered witness relation is genuinely directional. It needs an asymmetric object, for example:

- direction-conditioned scorer `g(z_source,z_target,witness)`;
- learned transport operator `T_w(z_source)` evaluated against target obligations;
- obligation-level gate with source/target roles distinguished;
- asymmetric bilinear/order/energy model.

This yields a clean two-object architecture:

```text
TCSQ quotient:      what distinctions are irrelevant for this QoI/context?
StructuralWitness:  what can be transported in this direction, under which boundaries?
```

Do not collapse them into one metric.

### Novelty boundary

The symmetry observation is elementary and directional analogy/transport is not new. The RAKL research question is whether its exact QoI/boundary/non-preservation witness semantics add measurable value beyond strong asymmetric relational/causal parents.

---

## 3. Exact error floor for symmetric transfer classifiers on reversed-pair panels

Suppose a test panel contains both ordered directions for each of `N` unordered structure pairs. Let `D` of those unordered pairs have asymmetric gold labels (one direction licensed, the reverse rejected). Any symmetric classifier must make at least one error on each of those `D` pairs.

Hence its ordered-pair accuracy is bounded by

```text
accuracy <= 1 - D/(2N).
```

This is a useful design diagnostic for NB-2: construct a nontrivial registered fraction of genuinely one-way witnesses. A symmetric-metric parent then has a transparent representational ceiling, while stronger *asymmetric* parents must still be included for the actual RAKL residual test.

---

## 4. Training/scientific-authority noninterference — architectural invariant

Let complete state be split into at least

```text
(E, L, theta)
```

where:

- `E` is evidence/scientific-authority state;
- `L` is learner/training state;
- `theta` is model parameters.

Let scientific authority be

```text
K = pi_epi(E)
```

and let a training transition be constrained to

```text
U_train(E,L,theta) = (E, L', theta').
```

### Proposition

Under this state-transition contract, a training-only update cannot change scientific authority:

```text
pi_epi(E') = pi_epi(E).
```

### Proof

By definition of the allowed training transition, `E'=E`. Since `pi_epi` depends only on `E`, substitution gives equality.

### RAKL interpretation

This is a software/state-ownership theorem, not a statement that models cannot influence future science. Model changes can generate new *proposals*, searches, experiments or evidence-acquisition actions. Those later actions may eventually modify `E` through the separately governed evidence/promotion path. What is forbidden is the direct implication:

```text
training metric improved -> scientific claim promoted.
```

The invariant should be regression-tested at every future neural/training surface.

---

## 5. Audit: current scalar-mastery proposition is overstrong

The current `publication/papers/paper-04-structural-learning-mechanics/main.tex` states, in substance, that a scalar mastery summary cannot be a sufficient statistic for allocation because vectors such as `(1,0,...)` and `(1/2,1/2,...)` can share a mean but require different actions.

### Problem

That argument proves only that the **chosen many-to-one scalarization** (for example the arithmetic mean) is insufficient. It does **not** prove that no scalar statistic can ever separate policy-relevant states.

A scalar function can be constructed to distinguish those two vectors; more generally, on a finite registered mastery state set an injective scalar code always exists. Even on continuous spaces, pathological injections/bijections can defeat an unrestricted cardinality claim. Therefore the universal statement

> “no scalar mastery score is a sufficient statistic for allocation”

is mathematically too strong without additional restrictions such as continuity, monotonicity, permutation invariance, coordinate anonymity, limited precision, or a specified scalarization family.

### Safe replacement

A defensible proposition is:

> Any **many-to-one scalarization that identifies two mastery vectors requiring different allocation actions is insufficient for that allocation policy.** In particular, coordinate-averaging summaries can erase a low composition/boundary/transfer coordinate and are not sufficient whenever the policy treats that low coordinate differently.

Or, if the intended claim is architectural rather than information-theoretic:

> RAKL retains the vector as canonical state because policy/audit semantics are coordinate-specific; any scalar is a derived reporting/ranking projection and may not be treated as lossless unless sufficiency for the registered policy is separately established.

### Action

Do not use the current universal scalar-impossibility wording as a novelty/theory pillar. Patch the paper before publication or formal review.

---

## 6. Audit: learner-conditioned saturation proposition should use “may”, not an implied universal change

The same manuscript argues that after a nontrivial parameter update, the training projection generally changes because mastery probes depend on `theta`.

The safe statement is:

```text
A saturation receipt at theta_t need not remain valid at theta_(t+1);
therefore it must be checkpoint-bound/staleable.
```

It is not true that every nonzero weight update necessarily changes every relevant probe or the resulting allocation projection. An update can lie in a functionally irrelevant/null direction for the registered probe panel, or change probe values without crossing any policy boundary.

The implementation's stale-by-checkpoint rule is conservative and valid even when the observable mastery state happens not to change.

---

## 7. Architectural consequence for the Neural Bridge

The cleanest current model is therefore **not one universal structural embedding**. It is a typed composition:

```text
raw/problem state
    |
    +--> TCSQ / quotient representation
    |       symmetric equivalence-like invariances for (QoI,context)
    |
    +--> StructuralWitness transport/gate
    |       asymmetric source->target applicability + boundaries/non-preservation
    |
    +--> learner mastery / training projection
    |       checkpoint-bound coordinate state, no scientific authority
    |
    +--> scientific authority projection
            evidence-governed, unchanged by training-only transitions
```

A neural architecture may share parameters across these views, but the semantics and authority of the views must remain typed and separately testable.