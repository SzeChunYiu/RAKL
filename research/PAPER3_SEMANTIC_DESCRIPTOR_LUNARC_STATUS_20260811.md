# Paper 3 label-blind semantic descriptor — LUNARC execution status

Date: 2026-08-11  
Authority: verified pre-execution contract only; no empirical result

## Object and QoI

The object remains the content-semantic relatedness of each frozen v2.1
source/target description pair. The quantity of interest is whether the later
witnessed-structure arm adds held-out discrimination beyond a modern
content-bound cross-encoder. This iteration does not answer that question.

## Frozen native order

`CONTRACT_V1.json` binds the frozen parent, protocol, source set, descriptor
implementation, BGE revision and six required assets. It also binds an exact
read-only CPU runtime and every submission, batch, execution and harvest
artifact. Native execution is two separate LUNARC `lu48` allocations:

1. download the exact public model revision, recompute every size and SHA-256,
   and atomically promote the snapshot only on an exact match;
2. only after a scheduler-bound stage harvest passes, run the frozen descriptor
   in a separate CPU batch with network disabled and local files only.

The second job requires the fast `tokenizer.json` path to load and tokenize a
pair. The absence of the optional SentencePiece Python package is tolerated only
if that exact probe passes; otherwise execution produces a typed
`CANNOT_CHECK`. Model files and the shared Paper-2 runtime are content-digested
before and after inference and must remain unchanged.

## Current result boundary

No job was submitted from this unmerged branch. No model asset was staged, no
model was executed, no descriptor record was generated, and no quantitative
figure was produced. No annotation, adjudication or evaluated result was
accessed. The internal hostile pass is same-context review, not independent or
peer review.

After merge, bind a fresh clean FS9 checkout to the exact merged SHA, submit and
harvest the model-stage job, and only then submit and harvest the descriptor
job. Preserve any model, tokenizer, scheduler or runtime failure as a typed null;
do not alter the frozen projection or model to obtain a pass.
