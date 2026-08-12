# Experiment Matrix

These experiments answer separate causal questions.

## E1 — Does mechanic diagnosis contain information?

Arms:

```text
A current continuation
B random mechanic
C diagnosis -> mechanic
D oracle mechanic
```

Primary:

```text
cause identification
verified success
cost
```

If C ~= B, diagnosis is not useful.

If C improves diagnosis but not task outcome, specialists may not have sufficient differential advantage.

---

## E2 — Does representation selection help?

Arms:

```text
A original representation
B random transform
C effect-based representation search
D oracle representation
```

Measure:

```text
branching reduction
verification tractability
solve rate
total cost
```

---

## E3 — Can representation create solvability geometry?

For each problem with multiple representations:

1. build explicit solver-state graph;
2. compute true verified cost-to-go;
3. construct field in each representation;
4. measure local gradient alignment;
5. execute field-guided route.

Hypothesis:

```text
some representations produce much higher local-global alignment
```

This is the direct “path becomes visible” experiment.

---

## E4 — Field versus path search

Arms:

```text
uniform-cost
A*
conductive field
breakdown front
field + exploration
oracle field
```

Important output:

```text
total cost including field construction
```

---

## E5 — Is branching useful?

Vary:

```text
K = 1, 2, 4, 8
```

under matched total expansion budget.

Test deceptive and multimodal worlds.

Expected possibility:

- `K=1` locks into false attractor;
- moderate K improves robustness;
- high K wastes compute.

---

## E6 — Does conductance memory transfer?

Train/update on development worlds.

Test surface-shifted worlds with same deep structure.

Compare:

```text
no conductance memory
raw frequency memory
scoped structural conductance memory
oracle prior
```

---

## E7 — Adaptive scale

Arms:

```text
fixed coarse
fixed fine
residual-only adaptive
adaptive + scout
oracle
```

Families:

```text
narrow hidden feature
smooth feature
global residual
mixed-scale
```

---

## E8 — Contracted recursive composition

Arms:

```text
monolithic
decompose + naive concatenate
decompose + interface checks
decompose + hierarchical verification
```

Measure:

```text
local success
root success
verification cost
false accept
false reject
```

---

## E9 — Auxiliary object invention

Families where a known helper exists.

Arms:

```text
direct solve
retrieve helper
enumerate helper
residual-conditioned helper request
oracle helper
```

Later:

```text
LLM helper proposal
```

---

## E10 — Sequential evidence versus solver mechanic change

Construct paired cases:

```text
same visible failure
but one is missing evidence
and one is wrong method
```

A good controller must not “invent a new solver” when one measurement is missing.

---

## E11 — Cognitive compute allocation

Give fixed total budget.

Mechanics compete for it:

```text
retrieval
representation
operator search
verification
coverage scout
```

Compare:

```text
fixed split
hand policy
learned value policy
oracle
```

---

## E12 — Full challenger

Arms:

```text
A incumbent
B + diagnosis only
C + diagnosis + representation
D + diagnosis + representation + scale
E + diagnosis + representation + field
F full recursive multiscale mechanics controller
```

Do not jump directly to this experiment.

---

# Claim matrix

| Result | Allowed claim |
|---|---|
| Better diagnosis only | diagnostic improvement |
| Better field geometry only | routing-signal improvement |
| Lower search expansions but higher total cost | no efficiency improvement |
| Better representation on dev only | development result |
| Fresh lower verified cost | scoped solver improvement |
| Full system wins but atoms unclear | system-level improvement only |
| One atom wins, full system does not | promote/narrow atom, not architecture |
