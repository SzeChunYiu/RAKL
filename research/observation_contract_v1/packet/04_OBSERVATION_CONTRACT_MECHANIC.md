# Observation / Information Contract mechanic

## Why it exists

RFA-v1 can already decide to `REFRAME_QUESTION`, `REVISE_MEASUREMENT`, `AUDIT_EVALUATOR`, `ASCEND`, or return a resource boundary. What it lacked as an explicit reusable object was a frozen statement of **what information the question permits the solver to use**.

The plugin in `implementation/observation_contract_reference.py` supplies that object without changing authority semantics.

## Type

\[
\Omega=(id,v,\rho,I,N,W,P,A,E,e),
\]

where:

- \(\rho\) = information regime;
- \(I\) = input sources;
- \(N\) = registered normalizers;
- \(W\) = external-knowledge policy;
- \(P\) = provenance requirement;
- \(A\) = abstention policy;
- \(E\) = evaluator/gold policy;
- \(e\) = evaluator epoch.

The reference regimes are:

```text
SOURCE_GROUNDED
SEMANTIC_NORMALIZED
EXTERNAL_COMPLETION
```

## Validity constraints

- `SOURCE_GROUNDED`: no semantic normalizer and external knowledge forbidden.
- `SEMANTIC_NORMALIZED`: at least one named normalizer; external completion forbidden.
- `EXTERNAL_COMPLETION`: external-knowledge policy must be explicit and provenance is mandatory.
- Any change to regime/evaluator/normalizer policy changes the content digest and therefore defines a successor contract.

## Pair audit verdicts

The reference implementation can return:

```text
LICENSED_VISIBLE
LICENSED_SEMANTIC
LICENSED_EXTERNAL
REQUIRES_NORMALIZATION
REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE
EVALUATOR_CONTRACT_TENSION
CANNOT_CHECK
```

These are pursuit/audit verdicts. They do not promote scientific authority.

## Integration with RFA-v1

Suggested mapping into the existing RFA coordinates:

- mismatch in source license -> `QUESTION` + `MEASUREMENT` audit;
- explicit source/gold contradiction -> `EVALUATOR` audit;
- semantic normalizer required -> `FRAMEWORK`/`METHOD` candidate, depending implementation;
- external knowledge required -> `RESOURCE`/capability route;
- repeated child failures caused by hidden information assumption -> `ASCEND` with an ancestor challenge.

Do not add an L8 or a new protected effect.
