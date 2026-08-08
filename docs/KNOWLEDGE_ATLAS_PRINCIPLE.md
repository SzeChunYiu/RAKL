# Knowledge Atlas Principle

The Apple Principle is the intuitive version of a more general idea.

Different sources often provide **local coordinates on the same underlying object**.

One paper describes color, another shape, another taste. A mathematical paper may use one state representation, another an equivalent operator representation, and a third an asymptotic limit. These are not automatically mutually exclusive descriptions.

RAKL therefore treats a mature body of knowledge as an **atlas of local views** rather than demanding one universal coordinate system too early.

## 1. Local charts

For object `O`, a source or framework supplies a local chart

\[
C_i=(U_i,\phi_i,\mathcal C_i,E_i),
\]

where:

- `U_i` is the facet/subdomain of the object described;
- `φ_i` is the source's representation or projection;
- `C_i` is the context tuple: population, scale, observation model, assumptions, units and intervention;
- `E_i` is the evidence/uncertainty authority.

A source is therefore not stored merely as “paper X claims Y”. It is stored as a contextual chart of the object.

## 2. Transition maps

When two charts overlap, RAKL asks whether a transition map exists:

\[
T_{ij}:\phi_i(U_i\cap U_j)\to\phi_j(U_i\cap U_j).
\]

Examples:

- invertible coordinate transformation;
- generator-equivalent stochastic representations;
- one model being the scaling limit of another;
- two observation models producing the same QoI;
- a calibration mapping between different units or sensors.

If a transition map exists, the sources add translation and complementary scope rather than independent model count.

## 3. Gluing

A global portrait is justified only when local charts agree on overlaps within registered uncertainty and scope.

Conceptually:

```text
local descriptions
→ overlap checks
→ transition/equivalence maps
→ compatibility
→ global object portrait
```

If compatible local views uniquely determine a global object for the registered consumer, RAKL may synthesize one global formalism.

If not, RAKL keeps the **atlas** or an identified/model set rather than forcing one global coordinate system.

## 4. Obstructions are useful

Failure to glue is not a nuisance to average away.

It can indicate:

```text
missing context coordinate
hidden state
measurement incompatibility
scale transition
wrong ontology
true scientific contradiction
non-identifiability
insufficient uncertainty model
```

The obstruction itself becomes a residual and opens a child knowledge fiber.

## 5. Dynamic atlas

Many scientific objects are not static apples.

The object may evolve with state, regime or intervention. Then the atlas includes transition dynamics:

\[
O_t \to O_{t+dt},
\]

and each local chart may only be valid in part of state-space or at a particular scale.

RAKL should prefer a **mechanism atlas** when different effective laws are valid in different regimes but share a common lower-level ancestry.

## 6. Mechanism gluing

RAKL distinguishes observational gluing from mechanistic gluing.

Two representations may agree on predictions while implying different microscopic mechanisms.

Therefore every overlap may carry multiple relationship layers:

```text
semantic equivalence
mathematical equivalence
observational equivalence
QoI equivalence
microscopic mechanism equivalence
```

Agreement at a weaker layer never silently upgrades to a stronger one.

## 7. Sheaf-like interpretation

The local-to-global structure resembles sheaf-based multi-view consistency: local descriptions are attached to parts of an object and compatibility is checked on overlaps before global synthesis.

RAKL does not require every application to implement full category/sheaf theory. The practical rule is sufficient:

> **Gluing must be earned on overlaps; incompatible local views remain visible as an obstruction.**

For domains where multi-view consistency is central, a formal sheaf implementation may become a RAKL child formalism and must face its own known-answer and native validation.

## 8. Recursive atlas

Each chart can itself be an object with its own atlas.

For example, a chart called `memory` may split into:

```text
self-excitation
age dependence
relaxation spectrum
fractional/Volterra representation
latent regimes
common forcing
observation artifact
```

Each of these receives local views from different research traditions. RAKL recursively repeats the same gluing process.

## 9. RAKL itself as an atlas

External research frameworks should be treated as local charts of the object:

> “How should an autonomous scientific research system work?”

One framework may be strong in retrieval, another experiment search, another peer review, another memory, another evaluation.

RAKL absorbs the compatible local contributions into its method atlas instead of replacing itself wholesale with whichever repository is currently fashionable.
