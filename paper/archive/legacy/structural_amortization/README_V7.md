# Structural Amortization paper

Working title: **Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer**

Status: formalism + deterministic conformance + internal cheap diagnostic + pre-label strong-control freeze. The cheap gate fails closed because the exact cross-encoder asset, independent human/expert annotations and adjudication are absent; no strong-control score, large-model training or matched inference result is claimed.

The label-visible 44-item v1 proposal is permanently non-confirmatory: its frozen
protocol records that confirmatory use is not permitted.  External annotations
cannot retroactively repair that chronology.  A separate v2 protocol and rubric
therefore require a fresh label-blind item set, two genuinely independent
human/expert submissions, distinct adjudication and an external provenance audit.
Until those inputs and the subsequent v2 signal gate pass, the LUNARC submission
preflight refuses every Paper 3 training or inference job.

A fresh 16-item, four-family label-blind source set is now frozen in
`research/paper3/annotation/SOURCE_ITEM_SET_V2_20260810.json`. It contains
cited descriptions only: zero external annotations, no adjudication, and no
empirical signal estimate. The base FS9 directory is ready on LUNARC, but no
SLURM job was submitted because the authorization gate is closed.

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

## Source identifier repair

A same-context hostile audit found outcome-suggestive `near_miss` suffixes in four
curator source identifiers. The v2 source set is retained as negative history;
`SOURCE_ITEM_SET_V2_1_20260810.json` replaces only those identifiers with neutral
sequential codes before any external judgement. The first packet attempt and
private linkage were discarded. Compute remains unauthorized.

## v2.1 external annotation packet

The fresh packet `research/paper3/annotation/EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json` is bound to merged subject `f4cee8313ec64d02873b87f92c51c35c113cd70d`. Its coordinator-only linkage is stored outside Git on FS9 with mode `0600`; only its path and hashes are public. The packet contains 16 opaque items and zero judgements.

A hostile usability pass also repaired the submission and adjudication schemas so a reviewer can record `cannot_assess=true` with null coordinates rather than guess. Such an artifact is preserved as negative history and still fails confirmatory import. Two complete external submissions per item, distinct adjudication and external provenance audit remain required before the cheap v2 signal gate may run. No SLURM training or inference job is authorized.

## Strong-control freeze

An audit found that the historical 44-item internal result compared against
surface, skill-tag and dependency-tag Jaccard controls. Those are useful
transparent conformance baselines but not a strongest-feasible modern semantic
control. Before any external label became visible, v1 froze:

- exact `BAAI/bge-reranker-v2-m3` revision and required-file hashes;
- an authority record distinguishing locally checked small-file hashes from
  not-yet-locally-verified Hugging Face LFS metadata;
- a deterministic, hash-bound content projection of the v2.1 source items;
- exclusion of candidate structural proposals, annotations and outcomes;
- local-only CPU/float32 inference and pre-label chronology;
- comparison against the strongest non-structural arm including the reranker;
- faithful, phase-specific applicability boundaries for Skill-It, MASS and SWIFT.

The model asset is not staged in this clean environment. The builder therefore
fails closed with zero descriptors. This is governance progress, not an
empirical result, and compute remains unauthorized.

The native successor now has a frozen two-job LUNARC contract: an allocated CPU
job must download and locally hash-verify the exact public BGE snapshot before a
separate allocated CPU job may execute the label-blind descriptor. The second
submission requires a scheduler-bound stage harvest, exact clean merged checkout
SHA, an exact shared-runtime tree digest attested by the allocated stage job,
offline fast-tokenizer probe, and unchanged model/runtime content digests. A
descriptor harvest additionally requires a payload-free chronology receipt made
after the descriptor (or a first-label cutoff) that proves the descriptor
predates external labels. The freeze-time zero-label observation alone cannot
promote a later descriptor.
No job has yet been submitted under this contract, so the descriptor remains
absent and all scientific claims remain unchanged.
