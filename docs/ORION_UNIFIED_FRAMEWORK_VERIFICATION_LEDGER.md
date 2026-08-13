# Orion Unified Problem-Solving Framework — Verification Ledger

Status: **proposal-only framework hardening**. This ledger is a claim limiter, not a promotion receipt.

## What is being verified

The unified problem-solving work adds proposal/routing sidecars around existing Orion objects rather than a second canonical framework. The new surfaces cover: partial operational map belief and coverage; path/concurrency equivalence; noncompensatory path cost; fieldability and geometry lifecycle; mechanic differential diagnosis; verified solver compilation; and trajectory-to-certificate assembly.

Every new module is owned by an existing canonical method surface through `src/rakl/unified_solver_registry.py`. A sidecar is rejected by the registry if it attempts to mint scoped certificate or stronger authority.

## Evidence ladder

A mechanism may accumulate several kinds of evidence without those kinds being interchangeable:

| Level | Meaning | Does it prove real-world utility? |
|---|---|---|
| `PROVED_BY_CONSTRUCTION` | A property follows from types/guards and is attacked by negative tests. | No |
| `UNIT_TESTED` | Deterministic examples execute the intended branch and hostile inputs fail closed. | No |
| `PROPERTY_OR_ADVERSARIAL_TESTED` | Generated or constructed cases attack a general invariant. | No |
| `DEVELOPMENT_KNOWN_WORLD` | The mechanism changes an objective result in a world with known ground truth. | Only in that registered world |
| `EXTERNAL_CI_PASSED` | Exact-commit repository tests/builds pass in GitHub Actions. | Software/build assurance only |
| `FRESH_SCOPED_UTILITY` | A frozen fresh benchmark shows root-level benefit under matched resources. | Yes, in scope |
| `INDEPENDENT_EXTERNAL_ASSURANCE` | Qualified process and evidence-lineage independent review/replication. | Stronger, still scoped |

Formal closure, passing tests, and clean PDFs never imply framework saturation, scientific truth, or empirical superiority.

## Load-bearing invariants

### Operational map belief

- `UNKNOWN != BLOCKED`.
- A failed attempt is not a formal impossibility result.
- A route is `VERIFIED_ROUTE_FOUND` only through registered verified transitions.
- No operational-map object grants theorem or scientific authority.

### Path equivalence and concurrency

- Nontrivial commuting/equivalent histories require explicit conditions and verifier evidence.
- A partial-order quotient is a derived search view; raw chronological TaskEpisodes remain immutable evidence roots.
- Path equivalence never proves the target theorem.

### Path cost algebra

- Hard legality, specification, portal, trust and root-scope constraints are checked before cost comparison.
- Invalid paths cannot compensate with lower compute cost.
- Incomparable admissible routes remain on a Pareto frontier unless a registered consumer supplies an explicit comparison order.

### Fieldability and geometry lifecycle

- Local progress alignment alone is insufficient for a routing-utility claim.
- Geometry identity is bound to specification, operator basis, map revision and representation chart.
- Construction, extraction, verification, reuse and invalidation cost are separate coordinates.
- Geometry/routing outputs grant no epistemic authority.

### Mechanic differential diagnosis

- Multiple surviving causes remain multiple.
- If a discriminator is required, a diagnosis cannot silently collapse to one cause.
- Unknown signals return `CANNOT_CHECK` rather than minting an ontology.
- Diagnosis cannot promote a method.

### Verified solver compilation

- The compiled object binds the source problem, specification, representation, transform, solver, decoder and verifier.
- A candidate marked `VALIDATED_FOR_ROUTING` requires a separately bound preservation receipt.
- Build, execution, decode and verification cost are all counted.
- Reuse/staleness are explicit; compilation never grants target/scientific/method authority.

### Trajectory-to-certificate assembly

- Search chronology and final proof/solution structure are different objects.
- Assembly requires a valid exact-hash dependency DAG, full root dependency closure, verified dependencies, a verified root and a passing assembly verifier.
- Passing assembly returns only `READY_FOR_EXTERNAL_AUTHORITY_GATE`; ordinary mathematical/scientific authority gates remain necessary.

## What cannot honestly be proved by this release

The project does **not** claim:

- absence of every undiscovered software bug;
- global logical completeness of every solver mechanic or failure taxonomy;
- global bibliographic completeness;
- a generally useful hidden geometry of mathematical reachability;
- empirical superiority of MDD, VSC, field dynamics, multiscale routing or path quotienting on open research;
- semantic fidelity of every future informal-to-formal translation;
- soundness of external verifiers beyond their registered trust assumptions.

Those are either open empirical coordinates or external trust assumptions. A new native residual reopens the affected mechanic.

## Release gate

A paper may describe a new object as **implemented** only when its tests pass at the paper-bound implementation SHA. It may describe a deterministic/known-world effect only when the generation script and result receipt are present. It may describe real task utility only after a separately frozen fresh benchmark. Plots must identify which of these evidentiary levels they visualize.
