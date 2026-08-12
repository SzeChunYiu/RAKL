# GLM-5.2 Mechanism-Isolation Suite v1

This directory is a prospective experiment harness created after the normalization/relevance-oracle nulls. It **does not reinterpret those nulls** and it is not designed to guarantee a RAKL win.

The suite isolates three mechanisms that the existing results do not establish: selective evidence retrieval under information pressure, verified cross-task experience transfer, and typed scientific-state governance.

## Security

The runner reads `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and `ANTHROPIC_MODEL` from the environment. The token is never serialized to a result artifact. Do not place credentials in Git, workflow inputs, command-line arguments, or result JSON.

## Causal discipline

Run `python run_suite.py dev` first. Confirmatory execution is refused unless all three **non-RAKL** development gates pass:

* retrieval: the gold evidence oracle must demonstrate measurable evidence-selection headroom over a strong generic hybrid retriever;
* experience: the gold verified lesson must demonstrate measurable headroom over reset;
* governance: the DIRECT baseline must sit away from floor/ceiling.

Task difficulty and confirmatory thresholds may not be tuned against RAKL development outcomes. If a development gate fails, the correct result is `NON_DISCRIMINATING`; any redesign is versioned before confirmatory output access.

`python run_suite.py confirm --selective-dev DEV_SELECTIVE.json --experience-dev DEV_EXPERIENCE.json --trajectory-dev DEV_TRAJECTORY.json` runs the disjoint confirmatory seeds only after the gates pass.

## Experiment 1 — selective retrieval

Arms: `GENERIC_HYBRID`, `RAKL_SELECTIVE`, `GOLD_ORACLE`, and `NATIVE_LONG`. All retrieval arms have the same downstream model and evidence-object budget. The typed selector uses visible scope/root/document-kind metadata but never reads hidden gold or finding labels. The full-context control is retained up to a configurable native context budget rather than deliberately truncating DIRECT at the Claude Code agent limit.

## Experiment 2 — verified experience transfer

Arms: `RESET`, budget-matched `SHAM_MEMORY`, `GENERIC_MEMORY`, `RAKL_MEMORY`, and `GOLD_LESSON_ORACLE`. Lessons are method guidance only; current-task scientific evidence remains separate. Near-miss lessons share vocabulary but have incompatible boundaries, so simple lexical retrieval is not automatically sufficient.

## Experiment 3 — trajectory governance

The same GLM proposal is scored directly and after a fail-closed governance gate. The gate never reads hidden world truth. It checks reviewed evidence, scope/axis identity, independent roots, registered discriminators, and exact cited IDs. Success requires lower authority leakage **without** a material valid-update-recall loss.

## Outcome boundary

A positive hosted result is empirical evidence at the hosted provider/model operating point. It is not weight-attested local evidence and does not automatically update manuscript claims or framework authority.
