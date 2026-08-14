# Paper V–VI RSHEA literature/mechanism saturation — round 008

Status: **CANONICAL_METHOD_SURFACE_STILL_FLAT; OPERATOR_BASIS_NOT_FLAT**.

This is the independent alternate-vocabulary repeat required by round 007. Search terms and parent families were changed to constraint explanation/repair, truth maintenance and automated algorithm configuration. No evaluated mechanic outcome is accessed and no authority is granted.

Parent surface-flatness head: `rshea/p5-p6-saturation-round-007@8b2cfe7ac3ea7bf5cb598dedb368d448d4d3c861`.

## Alternate-vocabulary families

### Constraint conflict/explanation and repair: QuickXplain, MUS/MCS

Junker's QuickXplain computes preferred/minimal conflict explanations and relaxations for over-constrained problems using an underlying SAT/CSP/DL consistency oracle. Minimal Unsatisfiable Subsets (MUSes) characterize inclusion-minimal inconsistent constraint sets; Minimal Correction Subsets (MCSes) characterize inclusion-minimal sets whose removal restores consistency. MARCO/CAMUS-style methods enumerate these objects.

This is not the same operation as delta debugging:

- failure-condition minimization asks for a small subset/configuration that still reproduces a registered failure;
- conflict analysis asks for a minimal inconsistent set relative to an explicit constraint theory;
- correction analysis asks what minimal relaxation/removal restores consistency.

**New missing operator:** `MINIMAL_CONFLICT_CORRECTION_ANALYSIS` under existing gap-discovery/failure-diagnosis/repair surfaces.

The operator must distinguish:

- inclusion-minimal conflict from minimum-cardinality conflict;
- minimal correction set from minimal conflict set;
- one explanation from exhaustive enumeration;
- solver inconsistency from causal/mechanistic explanation.

### Assumption-based truth maintenance

De Kleer's ATMS represents environments/assumption sets supporting beliefs and records nogoods for inconsistent assumption combinations.

**Mapping:** strengthens existing truth-maintenance/provenance, plural-context and negative-knowledge surfaces. No new canonical surface. It is a stronger parent for any claim that Orion uniquely tracks alternative assumption contexts or scoped inconsistencies.

### Automated algorithm configuration

ParamILS/SMAC optimize algorithm parameter/configuration choices using performance observations; modern algorithm configuration/selection is a direct parent for hyper-heuristic/mechanic-configuration claims.

**Mapping:** already owned by selector/portfolio/hyper-heuristic and value-of-computation surfaces. No new canonical surface.

**Retained detail:** whenever an Orion controller adapts continuous/discrete mechanic parameters rather than only selecting a named mechanic, include automated algorithm-configuration parents and charge configuration/training cost.

## Round 008 result

The independent repeat supports round 007's surface claim: **no new top-level canonical method surface** was found.

However the operator basis is not flat because `MINIMAL_CONFLICT_CORRECTION_ANALYSIS` is distinct from the previously frozen `failure_condition_minimization_v1` and `verified_failure_constraint_compilation_v1`:

1. minimize a reproducing failure context;
2. identify a minimal inconsistent constraint explanation;
3. identify a minimal correction/relaxation restoring consistency;
4. only then, when proof obligations are met, compile reusable nogoods/invariants.

Therefore the honest combined status is:

- `CANONICAL_METHOD_SURFACE_STILL_FLAT_ON_REGISTERED_AND_REPEAT_ROUTE_UNIVERSE`;
- `OPERATOR_BASIS_NOT_FLAT`;
- `LITERATURE_SATURATION_NOT_CLAIMED`.
