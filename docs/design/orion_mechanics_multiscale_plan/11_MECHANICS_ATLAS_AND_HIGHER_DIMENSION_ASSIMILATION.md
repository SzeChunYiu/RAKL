# Mechanics Atlas and Higher-Dimension Assimilation

## 1. Spirit

Existing theories, algorithms and projects are not boxes Orion must choose between.

They are a dataset of **mechanisms**.

The unit of learning should not be:

```text
"Method X"
```

but:

```text
what representation did it assume?
what local rule did it use?
what global objective emerged?
what feedback signal shaped the process?
what scale did it operate at?
what memory did it preserve?
what verifier made it trustworthy?
where did it fail?
under what cost regime did it win?
```

## 2. Mechanism vector

Represent each donor system as:

\[
m =
(R,L,G,F,S,M,V,C,A,X)
\]

where:

- `R`: representation;
- `L`: local update/action rule;
- `G`: global objective/property;
- `F`: feedback/reinforcement;
- `S`: scale structure;
- `M`: memory;
- `V`: verifier/evidence boundary;
- `C`: cost regime;
- `A`: assumptions;
- `X`: failure modes.

This is the “one dimension higher” view.

## 3. Example donor decomposition

### Lightning / dielectric breakdown

```text
R: conductive medium / field
L: grow where field/threshold favors
G: discharge connection/current path
F: conductivity changes field
S: branching, multi-scale structure
M: physical channel persists
V: actual conduction
C: parallel physical dynamics
X: not an optimizer in generic abstract problems; path depends on physical law
```

### Physarum

```text
R: transport network
L: tube conductance adapts to flux
G: efficient connection
F: high flow thickens tube
S: network-wide
M: persistent tube thickness
V: physical transport
X: convergence/parameter/scope limits
```

### Fast Marching

```text
R: arrival-time field
L: accept smallest causal front value
G: Eikonal solution
F: deterministic local update
S: front propagation
M: accepted set
V: numerical PDE semantics
X: assumptions on front/cost structure
```

### A*

```text
R: discrete graph
L: expand min g+h
G: shortest path
F: heuristic cost-to-go
S: single graph scale
M: open/closed sets
V: path cost / admissibility theorem
X: heuristic weakness, state explosion
```

### Convex lifting

```text
R: higher-dimensional variables
L: convex optimization
G: original solution recovered through lifted constraints
F: global convex objective
S: global
M: n/a
V: reconstruction theorem/check
X: dimensional/computational blow-up
```

### Koopman-style lifting

```text
R: observable functions in lifted space
L: approximately linear dynamics
G: easier prediction/control
F: learned/selected observables
S: state to observable space
M: model
V: prediction/control performance
X: finding useful invariant observables
```

## 4. Atlas relation types

```text
SPECIALIZES
GENERALIZES
DUAL_OF
LIFTS
PROJECTS
COMPOSES_WITH
REQUIRES
CONFLICTS_WITH
DOMINATES_UNDER
FAILS_UNDER
APPROXIMATES
SHARES_LOCAL_RULE
SHARES_GLOBAL_OBJECTIVE
SHARES_FEEDBACK
SHARES_SCALE_MECHANIC
```

## 5. Higher-dimensional synthesis procedure

Given N related methods:

### Step 1

Decompose each into the mechanism vector.

### Step 2

Find dimensions with variation.

Example:

```text
serial path enumeration
vs
parallel front propagation

static edge weights
vs
adaptive conductance

fixed representation
vs
lifted representation

single-scale
vs
multi-scale
```

### Step 3

Find correlated success/failure regimes.

### Step 4

Ask whether the methods are points on a more general family.

### Step 5

Construct the missing combinations.

Example matrix:

| Field | Adaptive conductance | Representation search | Multiscale | Verified decode |
|---|---:|---:|---:|---:|
| A* | no | no | no | domain-dependent |
| Fast Marching | fixed local speed | no | limited | yes in domain |
| Physarum model | yes | no | implicit | physical |
| Orion challenger | candidate | candidate | candidate | mandatory |

The empty or weakly explored cells become hypotheses.

## 6. Import rule

An imported mechanism enters Orion only if:

```text
source is recorded
mechanism is atomized
assumptions are explicit
failure modes are recorded
closest incumbent mechanic is identified
non-duplicate delta is stated
benchmark is defined
```

## 7. Learn why methods are bad

Every donor record must contain a `failure_surface`.

Questions:

```text
When does the method become circular?
What hidden assumptions make it work?
What does it optimize that is not our QoI?
What does it erase?
What cost does the paper exclude?
What does it mistake for evidence?
How does it fail under distribution shift?
Does it require an oracle representation?
Does it require an admissible heuristic?
Does it collapse exploration?
```

## 8. “Whole set of data” rule

Do not benchmark Orion against one famous parent and declare novelty.

For a mechanic family, construct a **parent envelope**:

```text
best known simple baseline
best known structural baseline
best known adaptive baseline
best known learned baseline
oracle / upper bound where possible
```

Orion must beat or complement the envelope in a registered regime.

## 9. Mechanics Atlas storage

V0 can be Markdown/JSON research artifacts.

Later add:

```python
@dataclass(frozen=True)
class MechanicAtlasEntry:
    mechanic_id: str
    source_ids: tuple[str, ...]
    representation_assumptions: tuple[str, ...]
    local_rules: tuple[str, ...]
    global_properties: tuple[str, ...]
    feedback_rules: tuple[str, ...]
    scale_properties: tuple[str, ...]
    memory_properties: tuple[str, ...]
    verification_properties: tuple[str, ...]
    cost_properties: tuple[str, ...]
    failure_surface: tuple[str, ...]
```

Do not let the Atlas grant authority.
