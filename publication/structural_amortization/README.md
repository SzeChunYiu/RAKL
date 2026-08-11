# Structural Amortization paper

Working title: **Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer**

Status: formalism + deterministic conformance + internal cheap diagnostic. The cheap gate fails closed because independent human/expert annotations and adjudication are absent; no large-model training or matched inference result is claimed.

## Scientific question

Can one context/QoI-scoped, evidence-bearing structural representation be reused both to:

1. identify structurally redundant training examples across surface-disjoint domains; and
2. license or reject test-time reasoning/operator transfer?

The paper is designed to fail cheaply before large compute is spent. Its killer controlled benchmark crosses semantic similarity with structural similarity. The central positive case has low semantic similarity but high structural match; the central negative case is a semantic decoy with high surface similarity but a load-bearing structural mismatch.

## Current executable objects

- `src/rakl/structural_types.py`: structural roles, relations, boundaries, objects and directional witnesses;
- `src/rakl/structural_transfer.py`: witnessed transfer gate and transparent relation/invariant overlap baseline;
- `src/rakl/structural_benchmark.py`: deterministic Q1--Q4 benchmark cases;
- `src/rakl/amortization.py`: total-cost, break-even and cost-to-capability objects;
- `tests/test_structural_transfer.py`;
- `tests/test_amortization.py`.

## Important novelty boundary

The project does **not** claim novelty for skill graphs, data selection, structural priors, reasoning primitive induction, trace compilation, abstract reasoning or workflow amortization in isolation. MASS, Skill-It, SWIFT, Reasoning Primitive Induction and TraceCompiler are parent mechanisms to reproduce and assimilate.

The candidate residual is the use of the **same scientifically scoped structural object** across training-data selection and inference-time transfer, with explicit mapping witnesses, non-preserved properties and boundary-aware rejection.
