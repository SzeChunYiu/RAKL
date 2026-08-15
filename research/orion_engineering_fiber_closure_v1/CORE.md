# Engineering fibers E3, E4, E9 — residuals addressed

Three of the thirteen open fibers in `CLOSURE_ASSESSMENT_V2` were the ones Orion-s own
session loop licensed as local wiring. Each now has code and tests. The packet-s terminal is
**not** changed here: re-assessing it is the packet-s own job, and three residuals closed out of
thirteen is not closure.

## E9 — the runtime now calls the EpistemicStatus gate

> `principal_RAKL_problem_solving_runtime_not_yet_calling_EpistemicStatus_gate`

`RAKLProject.status(epistemic_service=...)` consults the gate. Wired by dependency injection, so
`project_runtime` gains no dependency on the engineering layer. **The gate may refuse and its
refusal survives into the output** — unavailable or stale is reported as consulted-with-reason,
never omitted, because a gate whose refusal disappears is not a gate. Payload health and epistemic
availability stay separate questions.

## E4 — the incumbent decision heads are wired in

> `principal_incumbent_metric_saturation_decision_heads_not_yet_wired_into_project_runtime`

`RAKLProject.next_action(source)` projects them. Driving it against the shipped
`IncumbentStateHeads` found a defect in the first version: that object has no `next_action`
attribute — the layer supplies the projection as a module function — so the duck-typed lookup
returned `None` while reporting `wired: True`. A wiring that reports success while carrying nothing
is worse than no wiring. It now accepts a callable, reports how it resolved, and reports
`wired: False` when the source yields nothing. The real object is a regression test.

## E3 — the Atlas plane persists atomically

> `local_reference_does_not_yet_persist_full_Atlas_chart_transition_obstruction_plane_atomically`

`engineering_atlas_store` persists charts, overlap transitions and obstruction certificates as **one
transactional unit**. The three are one plane, not three related tables: a chart whose transitions
are missing describes a cover that was never checked, and an obstruction without its transition is
unattributable.

Referential integrity is checked **before any write**, so a batch that could only be half-written is
refused at construction. The store mirrors `engineering_semantic_store` deliberately — same batch
and commit shape, same `BEGIN IMMEDIATE` discipline, same idempotent-replay contract — because a
second store inventing its own transactional semantics is a second thing to get wrong.

The load-bearing test is the failure case, induced through a **real constraint violation** rather
than a patched driver: a second batch reuses a committed obstruction id, so its insert fails after
its own charts and transitions are already written inside the transaction. Row counts must be
unchanged afterwards. Eleven tests.

## What is not claimed

Ten fibers remain open and every one needs infrastructure this session does not have — multi-worker
backend, network transport, observatory UI, OpenTelemetry, identity provider, PostgreSQL restore
drill, load SLO, hostile assurance on a production release, build attestation, live operator drill.
The loop abstains on all ten rather than pretending they are close. `production_ready_scoped` stays
false.
