# Paper 3 confirmatory annotation rubric v2

**Rubric ID:** `paper3-annotation-rubric-v2-20260810`  
**Authority:** frozen instructions for a future, fresh, label-blind item set  
**Not evidence:** this document and any AI-generated example are proposal-only

## Object, context and QoI

The object is a proposed directional transfer from a source description to a
target description.  The quantity of interest is whether the source structural
mechanism can be reused for the registered target QoI within the stated target
boundaries.  Surface similarity, shared skill names and structural validity are
separate coordinates.

Annotators receive only the packet, this rubric and cited source/target evidence.
They must not inspect the RAKL proposal benchmark, proposed labels, diagnostic
predictions, another annotator's submission or adjudication.  Each annotator uses
a coordinator-issued pseudonym; direct identifiers stay outside Git.

## Required coordinates

For every item, record Boolean values for:

1. `semantic_similarity_high`: the source and target use substantially similar
   domain vocabulary or surface concepts.
2. `structural_match`: the load-bearing roles, typed relations, invariant,
   boundary and QoI jointly support the proposed directional reuse.
3. `roles_preserved`: the necessary source roles have explicit target images.
4. `typed_relations_preserved`: the load-bearing signed/directed/typed relations
   are preserved; loose thematic analogy is insufficient.
5. `invariant_preserved`: the stated invariant holds in the registered target
   regime.
6. `boundary_matched`: target assumptions and operating regime fall inside the
   invariant's validity boundary.
7. `qoi_matched`: the source and target claims answer the same registered QoI.
8. `directional_mapping_complete`: every load-bearing source element has a
   justified target mapping and non-preserved properties are disclosed.
9. `transfer_valid`: using the source mechanism for the target QoI is licensed
   after the preceding checks.

Each coordinate requires evidence references and a short rationale.  Do not infer
`transfer_valid` mechanically from a majority vote across coordinates; explain
the decisive failure or support.

## CANNOT_CHECK

If the supplied evidence is insufficient, set `cannot_assess=true`.  Do not guess
or force a Boolean merely to complete the packet.  Any unresolved CANNOT_CHECK
makes that item ineligible for confirmatory evaluation.  The source item may be
repaired only in a new frozen packet version; prior submissions remain negative
history.

## Independence and chronology

- Two distinct human/domain-expert submissions are required for every item.
- Both submissions bind the exact packet, protocol and rubric hashes.
- Submissions are frozen before adjudication begins.
- A third human/domain expert, distinct from the benchmark author and both
  annotators, adjudicates every coordinate and cites evidence.
- An external coordinator audits distinct identities, relevant expertise,
  independence and access chronology.  Code validates the audit envelope but
  cannot prove that a human attestation is truthful.

## Agreement and adjudication

The import receipt reports exact agreement separately for every coordinate and
the number of conflicts per coordinate.  It does not hide disagreement in one
aggregate score.  Adjudication resolves each conflict with a rationale; unresolved
conflicts remain ineligible.  Adjudication is not permission to change the frozen
diagnostic thresholds.

## Promotion rule

Annotation eligibility is necessary but not sufficient for expensive compute.
The new v2 held-out structural-signal evaluator must also pass the thresholds
frozen in the v2 protocol.  Until both gates pass, Paper 3 training and inference
remain unauthorized.  The existing label-visible v1 proposal can never satisfy
this confirmatory rule.
