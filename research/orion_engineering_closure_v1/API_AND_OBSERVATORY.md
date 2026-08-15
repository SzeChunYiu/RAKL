# API and Observatory contract

## Service rule

Mutations are snapshot-conditional and idempotency-bound. Reads may name an exact snapshot or the current head explicitly.

## Minimal API

```text
POST /v1/projects
GET  /v1/projects/{project_id}/head
GET  /v1/projects/{project_id}/snapshots/{snapshot_id}

POST /v1/projects/{project_id}/evidence
POST /v1/projects/{project_id}/research-rounds

GET  /v1/projects/{project_id}/epistemic-status
     ?snapshot=...
     &target=...
     &fiber=...

POST /v1/projects/{project_id}/actions:plan
POST /v1/projects/{project_id}/actions:execute

GET  /v1/projects/{project_id}/transitions/{transition_id}
GET  /v1/projects/{project_id}/decisions/{decision_id}
GET  /v1/projects/{project_id}/runs/{invocation_id}
GET  /v1/projects/{project_id}/provenance/{entity_id}
```

Every mutation accepts:

```text
Idempotency-Key
If-Project-Snapshot (or request-body equivalent)
```

Every mutation returns a `StateTransitionReceipt`, even on `RETRY_REQUIRED`, `RECOVERY_REQUIRED` or `CANNOT_CHECK`.

## Epistemic status response

The service returns the canonical `EpistemicStatus` object. It does not synthesize one scalar saturation percentage.

UI summary can show:

```text
knowledge fibre identity
project snapshot / evaluator epoch
per-axis saturation
route coverage
freshness
active residuals
blocking epistemic cuts / minimal repair link
hard gate state
controller next action + reasons
recent novelty/cost history
evidence lineage drill-down
```

## Observatory read-only first

The first production Observatory should not mutate scientific state. This removes an entire class of UI privilege and stale-form bugs while the state/control path is being established.

Views:

1. **Project head** — exact snapshot, health, backup freshness.
2. **Epistemic status** — axis vector, route coverage, residuals, freshness.
3. **Decision trace** — hard gates, control inputs, selected/blocked/abstained action.
4. **Solver state** — compiled-view identity, support paths, cuts/repairs.
5. **Evidence provenance** — atom/claim -> receipt -> exact source bytes.
6. **Execution/recovery** — attempts, leases, terminal/recovery states.
7. **Evolution history** — challenger/assurance/governance/rollback identities.
8. **Operational health** — queue/DB/index/blob/backup/exporter health, clearly separated from scientific status.

## Correlation context

Every service/workflow boundary propagates:

```text
project_id
snapshot_id
workflow_id
activity_or_invocation_id
research_round_id
episode_id
target_id
fiber_id
evaluation_epoch_id
controller_decision_id
```

This context is operational/provenance metadata and grants no RAKL authority.
