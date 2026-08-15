# Parent absorption ledger — V2

The V2 engineering packet does not claim these ideas as novel. It treats them as strongest-parent mechanics and preserves RAKL-specific differences.

## Incumbent RAKL parents absorbed

- `docs/ENGINEERING_CLOSURE.md`: engineering defects are RAKL fibres; scoped closure requires hostile/restart/replay/rollback/release evidence.
- `META_N076`: reconstructable multi-resolution memory; canonical history separated from active views.
- `META_N078`: clean-install/init/run/restart/reconstruct as a release obligation.
- `META_N019`: durable research execution remained partial at invocation level; V2 adds reference workflow history and snapshot binding, not a production scheduler.
- `META_N082`: release artifact identity; V2 adds exact runtime artifact content identity but not a real attestation verifier.
- `META_N083`: distributed coordination; remains deployment-dependent rather than pretending local SQLite is multi-host.
- `META_N084`: runner/environment attestation; V2 separates infrastructure identity from epistemic authority.
- `META_N085`: trace export; V2 carries correlation context but actual OTel export remains open.

## External strongest-parent mechanics

- Durable workflow/event history: assimilate deterministic resume/retry/idempotency semantics; keep RAKL `RECOVERY_REQUIRED` for ambiguous external effects.
- Serializable transactional metadata: whole state transition retries on serialization conflict; no last-writer-wins for epistemic/controller state.
- OpenTelemetry: operational traces/logs/metrics correlate through execution context but never replace RAKL `MetricReceipt` authority.
- W3C PROV: interoperable Entity/Activity/Agent and derivation/use/generation projection; does not flatten RAKL's typed authority/identity algebra.
- SLSA build provenance: bind executable artifact to build/source process; infrastructure provenance remains distinct from scientific authority.

The final external-parent refresh produced no additional architecture class beyond the registered E1–E20 fibres.
