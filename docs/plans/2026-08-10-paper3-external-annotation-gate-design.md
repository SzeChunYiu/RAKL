# Paper 3 external-annotation gate design

## Decision

The next Paper 3 iteration will operationalize a fresh v2 independent-annotation
gate without manufacturing evidence.  It will not launch training or inference.
The frozen v1 protocol records that labels were visible during construction and
that confirmatory use is forbidden.  The existing 44 v1 items and receipt remain
immutable negative history; adding annotations to them can never authorize
compute.  The repository will instead freeze a v2 rubric/protocol, accept only a
fresh label-blind source-item set, provide strict schemas for two independent
submissions and a distinct adjudication, and compile a confirmatory benchmark
only when every new item has complete, distinct and attested external inputs.

Three approaches were considered.  Treating the same-session proposal as
confirmatory is rejected because it violates the frozen gate.  Integrating a
survey vendor is deferred because it introduces external state, personal data
and credentials without improving the scientific contract.  A repository-native
packet/compiler is preferred because it is auditable, provider-neutral and fails
closed while human/expert evidence is absent.

## Components and data flow

`rakl.paper3_annotation` will reject the v1 proposal and any input containing a
quadrant, outcome label, proposed match decision, diagnostic result or prior
annotation.  It generates two artifacts only from a newly frozen label-blind
source-item set: an annotator packet and a coordinator linkage file mapping
opaque item identifiers to case identifiers.  The linkage file is not sent to
annotators.  Annotators return pseudonymous, attested JSON submissions.  A
third, distinct adjudicator returns resolved item-level judgements only after
both submissions are frozen.  The compiler verifies protocol/rubric/packet
hashes, item coverage, distinct identities, independence attestations,
chronology and typed fields before producing a new benchmark whose canonical
structural fields come solely from adjudication.

The v1 cheap-gate evaluator and workflow remain byte-identical.  A separate v2
gate will consume canonical adjudicated fields only and will enforce the v2
chronology flag.  It has no fallback to `*_proposal` fields.  The annotation gate
requires at least two distinct eligible annotators, complete final statuses and
distinct adjudication for every item.  Missing or malformed evidence leaves the
v2 gate closed.

No direct identifiers are stored; coordinators assign pseudonyms and retain any
identity/contact mapping outside Git.  The packet receipt records hashes and the
parent Git subject but is not an empirical result.

## LUNARC boundary

No SLURM job is submitted while the annotation and diagnostic gates are closed.
After both gates pass, an allocated GPU-node environment preflight will recheck
content hashes for the exact protocol, benchmark, task set, model descriptor,
environment, seed schedule and batch script; the exact clean Git subject; and a
single new FS9 output child before writing anything.  Training and inference are
then separate LUNARC batch jobs under
`/projects/hep/fs9/users/scyiu/RAKL-paper3`, each bound to the same immutable
manifest and gate receipt.  A scheduler failure is retained as a
machine-readable submission-failure receipt rather than being mistaken for a
run.

## Tests and promotion

Tests are written first and must demonstrate that labels are absent from the
annotator packet, duplicate annotators and self-adjudication fail, incomplete
submissions fail, canonical adjudicated values override proposal values, and the
current proposal remains closed.  Focused tests, the full suite, manuscript PDF
preflight, passive trusted-parent evaluation and exact GitHub CI are required
before merge.  Internal review is labelled internal; no step is described as
independent until external human/expert submissions actually exist.
