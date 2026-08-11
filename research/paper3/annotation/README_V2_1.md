# Paper 3 v2.1 external annotation solicitation

This directory contains a **solicitation packet, not annotation evidence**.

## Volunteer contact

To volunteer for one of the required external roles, comment only with the role and a brief public expertise summary on [GitHub issue #43](https://github.com/SzeChunYiu/RAKL/issues/43), using the [immutable v2.1 packet at commit `c6f2639b0927566c473817b4ebaafaee3a35ad36`](https://github.com/SzeChunYiu/RAKL/tree/c6f2639b0927566c473817b4ebaafaee3a35ad36/research/paper3/annotation). Do not post response files, identity evidence, affiliations, or private conflict material publicly. The coordinator must supply a secure return channel and separately audit identity, expertise, conflicts, role separation, exact bindings, and access chronology.

As observed on 2026-08-11, issue #43 has zero public responses; private response status is `CANNOT_CHECK` from the public repository. A solicitation or public comment is not an annotation submission, review, adjudication, provenance-audit evidence, a gate pass, peer review, or publication.

## Frozen public inputs

- Packet: `EXTERNAL_ANNOTATION_PACKET_V2_1_20260810.json`
- Packet file SHA-256: `9cf6d78962f2f2dc8db31f0e799f8aa23f7461b23d72d881837e7315caa74e0c`
- Packet canonical SHA-256: `1840e828a112dd51af03b50eaa8c486392213024b376ab9cd0aa68f511074a99`
- Parent subject: `f4cee8313ec64d02873b87f92c51c35c113cd70d`
- Rubric: `RUBRIC_V2.md`
- Submission schema: `../../../schemas/paper3-annotation-submission-v2-1.schema.json`
- Adjudication schema: `../../../schemas/paper3-adjudication-v2-1.schema.json`
- Provenance-audit schema: `../../../schemas/paper3-provenance-audit.schema.json`

Verify these bindings before opening the packet. Stop and notify the coordinator if any hash differs.

## Required external roles

The confirmatory annotation gate needs:

1. two distinct human/domain-expert annotators, each completing all 16 items without access to another response or any diagnostic result;
2. one distinct human/domain-expert adjudicator who starts only after both submissions are frozen; and
3. one external human provenance auditor who verifies identities, relevant expertise, conflicts, role separation and access chronology.

The coordinator assigns pseudonymous IDs. Do not commit direct identity, affiliation evidence or private conflict documentation to Git.

## Missing evidence

Do not guess. If an item cannot be assessed, set `cannot_assess=true`, set all nine judgement coordinates to `null`, and explain the missing evidence in `rationale` and `evidence_refs`. The schema preserves that response as negative history; confirmatory import still fails closed until the item is repaired in a new frozen packet.

## Claim boundary

The packet contains zero external judgements. Solicitation, volunteer interest, a single response, or same-context review is not independent review, peer review, a structural-signal result, or authorization for training/inference. The structural-signal evaluator remains closed until every annotation, adjudication and provenance condition passes.
