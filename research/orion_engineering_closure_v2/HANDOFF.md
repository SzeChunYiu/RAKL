# ORION engineering closure V2 — implementation handoff

Programme: #736  
Date: 2026-08-15  
Branch base / repo re-audit cutoff: `19dc8d022e5c609d30d075a754f52f58242ce917`  
Terminal: `REFERENCE_ENGINEERING_RESEARCH_SATURATED__IMPLEMENTATION_RESIDUALS_OPEN`

## Claim boundary

The engineering **research/design question** reached bounded saturation across the registered independent route families after the final hostile rounds produced zero new retained defect classes. This does **not** establish `PRODUCTION_READY_SCOPED`. Real-repository integration and real deployment assurance remain open.

## External V2 packet

Artifact: `ORION_ENGINEERING_CLOSURE_V2_HANDOFF.zip`  
SHA-256: `77c08e199252263de377205dbe3343b750512563581af1a3f3d91b3ad19dac03`

The packet contains the full additions-only git patch, repo-relative overlay, `AI_SESSION_HANDOFF.md`, file-hash manifest, PostgreSQL design draft, 17-finding defect ledger, E1–E20 closure assessment, bounded research-saturation receipt, schemas, reference backends, hostile tests, and migration/restore/runbook material.

Clean-apply validation at freeze: **82 / 82 engineering tests passed** after applying the generated patch to a clean temporary git repository with whitespace checking.

## Executable reference mechanics added in V2

The packet implements a single-node reference substrate for exact evidence-byte identity; immutable evidence metadata/revisions; `ProjectSnapshot`; effect-bound/idempotent state transitions; append-only semantic fibres/atoms/relations; single-transaction evidence/semantic mutation + snapshot/head/receipt commits; canonical `EpistemicStatus`; common controller/Observatory projections; snapshot-bound solver/control/workflow objects; rebuildable indexes; durable hash-chained workflow history; explicit `RECOVERY_REQUIRED`; consistent online SQLite backup and closed-world restore; migration/security/runtime-artifact/capacity/diagnostic contracts; and machine-readable engineering closure/saturation evaluation.

Seventeen hostile defects found while implementing this are preserved in the packet rather than erased by the repairs. Load-bearing examples include status-coordinate ambiguity, future-state leakage, cross-project snapshot binding, semantic/snapshot identity cycles, split semantic/project commits, idempotency not binding intended effect, live-WAL backup inconsistency, cross-project production-schema FKs, semantic parent cycles, ambiguous ZIP members, unknown snapshot strings, and effect smuggling between state planes.

## First work on a real implementation session

1. Re-audit current main after the cutoff above and absorb any stronger equivalent implementation rather than duplicating it.
2. Apply/reconcile the packet contracts and reference backends; run the full incumbent suite and protected CI.
3. Derive snapshot heads from incumbent evidence, Atlas, MetricLedger/evaluation epoch, episode-store head, saturation bases/certificates, scientific-authority projection, and controller epoch.
4. Complete durable Atlas chart/transition/obstruction persistence under the same semantic revision/atomic transaction.
5. Wire real knowledge saturation -> hard-gate receipts -> canonical `EpistemicStatus` -> controller -> snapshot-bound solver view -> cut/repair/residual -> targeted reopening.
6. Translate the reference transaction semantics to the production metadata/blob/workflow backends; preserve project scoping, whole-transaction retries, idempotency and `RECOVERY_REQUIRED` semantics.
7. Add the network API/Observatory, OTel export, production auth/secrets/build provenance, PITR/restore, load/SLO and fresh hostile release assurance.

Do not introduce a global RAKL score, UI-local saturation calculation, vector-database source of truth, or distributed exactly-once external-effect claim without a demonstrated transaction/idempotency boundary.

The complete implementation instructions live in `AI_SESSION_HANDOFF.md` inside the V2 packet.