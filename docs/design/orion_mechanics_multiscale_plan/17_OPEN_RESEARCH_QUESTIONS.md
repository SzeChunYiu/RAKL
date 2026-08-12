# Open Research Questions

These should remain unresolved until experiments answer them.

## Q1 — Does a general solvability geometry exist?

Maybe only domain-specific geometries exist.

A useful negative result would be:

```text
no shared representation gives stable local-global progress alignment across domains
```

Then Orion should maintain a portfolio of domain/mechanic-specific geometries.

## Q2 — What should a field node represent?

Candidates:

```text
raw solver state
problem atom
representation state
obligation set
proof state
mechanic state
hybrid tuple
```

Too fine -> state explosion.  
Too coarse -> false gradients.

## Q3 — What is the correct field objective?

Candidates:

```text
expected verified cost-to-go
root residual
probability of resolution
obligation distance
information gain
multi-objective vector field
```

A single scalar may be insufficient.

## Q4 — Can a vector field replace scalar value?

Instead of \(\Phi(z)\), learn:

\[
F(z)
=
(\text{search direction},
 \text{representation direction},
 \text{scale direction},
 \text{verification direction})
\]

This may be more faithful to heterogeneous mechanics.

## Q5 — Can field and decomposition be solved jointly?

A good decomposition may be one that makes the field smooth.

Potential objective:

\[
\min_D
\left[
\text{field distortion under }D
+
\text{interface cost}(D)
\right].
\]

## Q6 — Can representation search be guided by desired field properties?

Instead of asking:

> Which representation is semantically meaningful?

ask:

> Which representation produces low branching, high gradient alignment and cheap verification?

## Q7 — Is “one dimension higher” often literal?

Sometimes adding dimensions linearizes/convexifies. Sometimes the useful move is actually:

```text
quotienting
coarse-graining
removing nuisance variables
changing topology
```

So the general operator should be `CHANGE_REPRESENTATION`, not always `LIFT`.

## Q8 — Can negative history define resistance?

A failed route might increase edge resistance.

But failure is context-scoped. How should resistance transport across similar tasks without overblocking?

## Q9 — Can success/failure memories create a learned PDE-like field?

Instead of a neural scalar value function, can we fit local compatibility/conductance rules whose global solve produces the field?

This may be more auditable.

## Q10 — Can target obligations create a backward field?

Scientific claims and proofs have explicit obligations.

Can backward obligation propagation meet forward capability propagation to locate bottlenecks?

## Q11 — Can missing mechanics be identified from field singularities?

Potential speculative hypothesis:

```text
if no available representation/operator produces continuous progress
and field repeatedly terminates at the same cut
then the cut may localize a missing mechanic
```

Needs careful benchmark; do not hard-code.

## Q12 — What is the relationship to current JUMP/GLUE/LIFT?

Possible future synthesis:

```text
JUMP = search for remote coordinate system/mechanic
GLUE = compose local charts/contracts
LIFT = invent missing solver object/mechanic
FIELD = route within/among charts
SCALE = decide resolution
```

This could become a unified geometry of Orion operations.

## Q13 — Can multiscale fields solve the hidden-feature problem?

A single coarse field may miss narrow routes.

Possible approach:

```text
coarse global field
+
fine local scouts
+
cross-scale consistency
```

This resembles multigrid in spirit but must be tested in solver-state spaces.

## Q14 — How should learned mechanics be trained?

Possibilities:

```text
supervised oracle action
pairwise ranking
temporal difference
counterfactual policy evaluation
offline RL
imitation + verification
```

Fresh assurance contamination is a major constraint.

## Q15 — What is the minimum viable cross-domain test?

Candidate trio:

```text
graph/planning
formal proof
scientific mechanism known-world
```

A mechanic that transfers across all three would be much more interesting than a domain-specific optimization trick.

## Q16 — Can we discover new representation transforms automatically?

Long-term loop:

```text
residual
-> desired representation effect
-> generate transform
-> preservation probe
-> solver probe
-> fresh task
```

This is likely one of the most powerful but dangerous capabilities.

## Q17 — Can the Mechanics Atlas itself expose missing dimensions?

If many methods fail on the same unrepresented coordinate, that may indicate an ontology/mechanic axis missing from Orion.

This should be tested with hidden-label benchmark worlds before being trusted.
