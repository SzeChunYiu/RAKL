# Paper 3 strong-control status

Date: 2026-08-11  
Authority: protocol/implementation freeze only; no empirical promotion

## Object and QoI

The object is the content-semantic relatedness of each frozen Paper-3 v2.1
source/target description pair. The quantity of interest is whether witnessed
structure later adds held-out transfer discrimination beyond a modern
content-bound semantic comparator, rather than only beyond surface-token and
curator-tag overlap.

## Audit finding

The frozen v2 evaluator uses surface, skill-tag and dependency-tag Jaccard
features. Its historical 44-item result remains valid only as an internal
constructed diagnostic against those controls. It does not establish
incremental value over a dense encoder, cross-encoder or LLM analogy judge.

## Frozen successor control

`PAPER3_STRONG_CONTROL_PROTOCOL_V1_20260811.json` binds the exact
`BAAI/bge-reranker-v2-m3` revision, six required model-file sizes and SHA-256
hashes, deterministic CPU/float32 local-only inference, and a canonical content
projection. The projection includes domain, surface terms, skill tags,
dependencies, citation/title strings and shared QoI. It excludes candidate
invariant/boundary proposals, annotations, quadrants and outcomes.

`PAPER3_BGE_MODEL_PROVENANCE_20260811.json` records two revision authorities,
the Hugging Face model-card Apache-2.0 license metadata, Git blob identifiers,
and the provenance class of each SHA-256. Three small JSON files were downloaded
from the exact revision and locally hashed; the three LFS hashes remain registry
metadata until the full assets are staged and locally reverified.

Every future score must bind to source-text, target-text and pair hashes. The
descriptor must predate the first external annotation completion. Missing or
mismatched model assets, content, chronology or cases fail closed; surface
Jaccard cannot be substituted after labels are visible.

## Parent boundaries

Skill-It and MASS are training-data-selection parents, not inference baselines.
SWIFT is an inference workflow-transfer parent only when an executable operator
interface exists. The exact requirements for a faithful reproduction are frozen
in `PAPER3_PARENT_CONTROL_APPLICABILITY_V1_20260811.json`. None has been run.

## Current residual

The exact 2.27-GB model file is absent from the clean environment, so no semantic
descriptor was generated. No external annotation or adjudication was accessed.
No structural-signal, training, inference or break-even result was generated,
and LUNARC compute remains unauthorized.

Next discriminator: stage and hash-verify the exact model repository, run the
label-blind descriptor builder before any external annotation is completed, and
freeze that receipt. Only then may genuinely external annotations be imported
and the successor held-out signal evaluator run.
