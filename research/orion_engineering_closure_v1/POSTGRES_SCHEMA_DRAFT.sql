-- ORION engineering closure V2 — production metadata source-of-truth draft.
--
-- DESIGN ARTIFACT ONLY. Adapt through the repository's migration framework.
-- Consequential state transitions should run at SERIALIZABLE isolation and retry
-- the complete read/plan/write transaction on SQLSTATE 40001. External side effects
-- remain outside the illusion of database exactly-once semantics.

CREATE TABLE orion_project (
    project_id text PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE orion_snapshot (
    snapshot_id text PRIMARY KEY CHECK (snapshot_id ~ '^snapshot:[0-9a-f]{64}$'),
    project_id text NOT NULL REFERENCES orion_project(project_id),
    sequence bigint NOT NULL CHECK (sequence >= 0),
    previous_snapshot_id text,
    evidence_cutoff text NOT NULL,
    semantic_state_revision text NOT NULL,
    metric_ledger_head text NOT NULL,
    episode_store_head text NOT NULL,
    authority_projection_revision text NOT NULL,
    controller_epoch_id text NOT NULL,
    saturation_basis_ids jsonb NOT NULL,
    created_at_utc timestamptz NOT NULL,
    canonical_payload jsonb NOT NULL,
    UNIQUE(project_id, sequence),
    UNIQUE(snapshot_id, project_id),
    FOREIGN KEY(previous_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    CHECK ((sequence = 0 AND previous_snapshot_id IS NULL) OR
           (sequence > 0 AND previous_snapshot_id IS NOT NULL))
);

CREATE TABLE orion_project_head (
    project_id text PRIMARY KEY REFERENCES orion_project(project_id),
    snapshot_id text NOT NULL,
    sequence bigint NOT NULL CHECK (sequence >= 0),
    FOREIGN KEY(snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    FOREIGN KEY(project_id, sequence)
        REFERENCES orion_snapshot(project_id, sequence)
);

CREATE TABLE orion_state_transition (
    transition_id text PRIMARY KEY CHECK (transition_id ~ '^transition:[0-9a-f]{64}$'),
    project_id text NOT NULL REFERENCES orion_project(project_id),
    idempotency_key text NOT NULL,
    request_hash text NOT NULL,
    before_snapshot_id text NOT NULL,
    after_snapshot_id text,
    action text NOT NULL,
    action_payload_hash char(64) NOT NULL CHECK (action_payload_hash ~ '^[0-9a-f]{64}$'),
    process_identity text NOT NULL,
    status text NOT NULL CHECK (status IN (
        'COMMITTED','ABORTED','RETRY_REQUIRED','RECOVERY_REQUIRED','CANNOT_CHECK'
    )),
    canonical_payload jsonb NOT NULL,
    created_at_utc timestamptz NOT NULL,
    UNIQUE(project_id, idempotency_key),
    FOREIGN KEY(before_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    FOREIGN KEY(after_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    CHECK ((status = 'COMMITTED' AND after_snapshot_id IS NOT NULL) OR
           (status <> 'COMMITTED' AND after_snapshot_id IS NULL))
);

-- Exactly one canonical status projection per snapshot + target + fibre. A second
-- different result for the same coordinates is an integrity failure, not "latest".
CREATE TABLE orion_epistemic_status (
    status_id text PRIMARY KEY CHECK (status_id ~ '^epistemic-status:[0-9a-f]{64}$'),
    project_snapshot_id text NOT NULL REFERENCES orion_snapshot(snapshot_id),
    target_id text NOT NULL,
    fiber_id text NOT NULL,
    canonical_payload jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(project_snapshot_id, target_id, fiber_id)
);

-- Canonical evidence metadata. Exact bytes live in the BlobStore by raw SHA-256.
CREATE TABLE evidence_record (
    evidence_record_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    payload_sha256 char(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    source_identity text NOT NULL,
    source_version text,
    provenance_payload jsonb NOT NULL,
    created_snapshot_id text NOT NULL,
    FOREIGN KEY(created_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);
CREATE INDEX evidence_by_blob ON evidence_record(payload_sha256);

-- Semantic identities are stable; semantic content is append-only/versioned.
CREATE TABLE knowledge_fiber (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    fiber_id text NOT NULL,
    parent_fiber_id text,
    created_snapshot_id text NOT NULL,
    created_sequence bigint NOT NULL CHECK (created_sequence >= 0),
    PRIMARY KEY(project_id, fiber_id),
    FOREIGN KEY(project_id, parent_fiber_id)
        REFERENCES knowledge_fiber(project_id, fiber_id),
    FOREIGN KEY(created_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE knowledge_atom (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    atom_id text NOT NULL,
    fiber_id text NOT NULL,
    kind text NOT NULL,
    PRIMARY KEY(project_id, atom_id),
    UNIQUE(atom_id, project_id),
    FOREIGN KEY(project_id, fiber_id)
        REFERENCES knowledge_fiber(project_id, fiber_id)
);

CREATE TABLE knowledge_atom_version (
    atom_version_id text PRIMARY KEY,
    atom_id text NOT NULL,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_atom_version_id text REFERENCES knowledge_atom_version(atom_version_id),
    semantic_payload jsonb NOT NULL,
    UNIQUE(atom_id, valid_from_sequence),
    FOREIGN KEY(project_id, atom_id) REFERENCES knowledge_atom(project_id, atom_id),
    FOREIGN KEY(valid_from_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);
CREATE INDEX atom_version_by_snapshot ON knowledge_atom_version(project_id, valid_from_sequence);

-- This table is the symmetric compatibility-witness layer represented by
-- TypedKnowledgeLattice. Directional Atlas transitions belong in separate tables.
CREATE TABLE compatibility_witness (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    witness_id text NOT NULL,
    left_atom_id text NOT NULL,
    right_atom_id text NOT NULL,
    CHECK (left_atom_id <> right_atom_id),
    PRIMARY KEY(project_id, witness_id),
    UNIQUE(witness_id, project_id),
    FOREIGN KEY(project_id, left_atom_id)
        REFERENCES knowledge_atom(project_id, atom_id),
    FOREIGN KEY(project_id, right_atom_id)
        REFERENCES knowledge_atom(project_id, atom_id)
);

CREATE TABLE compatibility_witness_version (
    witness_version_id text PRIMARY KEY,
    witness_id text NOT NULL,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_witness_version_id text REFERENCES compatibility_witness_version(witness_version_id),
    semantic_payload jsonb NOT NULL,
    UNIQUE(witness_id, valid_from_sequence),
    FOREIGN KEY(project_id, witness_id)
        REFERENCES compatibility_witness(project_id, witness_id),
    FOREIGN KEY(valid_from_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

-- Contextual Atlas plane: directional local charts/transitions/obstructions remain
-- typed rather than being forced into the symmetric compatibility table. Stable
-- identities are project-scoped; versions may not point at another project.
CREATE TABLE atlas_chart (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    chart_id text NOT NULL,
    atlas_object_id text NOT NULL,
    PRIMARY KEY(project_id, chart_id)
);

CREATE TABLE atlas_chart_version (
    chart_version_id text PRIMARY KEY,
    chart_id text NOT NULL,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_chart_version_id text REFERENCES atlas_chart_version(chart_version_id),
    canonical_payload jsonb NOT NULL,
    UNIQUE(project_id, chart_id, valid_from_sequence),
    FOREIGN KEY(project_id, chart_id)
        REFERENCES atlas_chart(project_id, chart_id),
    FOREIGN KEY(valid_from_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE atlas_transition (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    transition_id text NOT NULL,
    source_chart_id text NOT NULL,
    target_chart_id text NOT NULL,
    CHECK (source_chart_id <> target_chart_id),
    PRIMARY KEY(project_id, transition_id),
    FOREIGN KEY(project_id, source_chart_id)
        REFERENCES atlas_chart(project_id, chart_id),
    FOREIGN KEY(project_id, target_chart_id)
        REFERENCES atlas_chart(project_id, chart_id)
);

CREATE TABLE atlas_transition_version (
    transition_version_id text PRIMARY KEY,
    transition_id text NOT NULL,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_transition_version_id text REFERENCES atlas_transition_version(transition_version_id),
    canonical_payload jsonb NOT NULL,
    UNIQUE(project_id, transition_id, valid_from_sequence),
    FOREIGN KEY(project_id, transition_id)
        REFERENCES atlas_transition(project_id, transition_id),
    FOREIGN KEY(valid_from_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE atlas_obstruction (
    project_id text NOT NULL REFERENCES orion_project(project_id),
    obstruction_id text NOT NULL,
    PRIMARY KEY(project_id, obstruction_id)
);

CREATE TABLE atlas_obstruction_version (
    obstruction_version_id text PRIMARY KEY,
    obstruction_id text NOT NULL,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_obstruction_version_id text REFERENCES atlas_obstruction_version(obstruction_version_id),
    canonical_payload jsonb NOT NULL,
    UNIQUE(project_id, obstruction_id, valid_from_sequence),
    FOREIGN KEY(project_id, obstruction_id)
        REFERENCES atlas_obstruction(project_id, obstruction_id),
    FOREIGN KEY(valid_from_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE residual_event (
    residual_event_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    residual_id text NOT NULL,
    fiber_id text,
    event_type text NOT NULL,
    payload jsonb NOT NULL,
    snapshot_id text NOT NULL,
    FOREIGN KEY(snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    FOREIGN KEY(project_id, fiber_id)
        REFERENCES knowledge_fiber(project_id, fiber_id)
);
CREATE INDEX residual_by_fiber_snapshot ON residual_event(project_id, fiber_id, snapshot_id);

CREATE TABLE saturation_certificate (
    saturation_certificate_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    fiber_id text NOT NULL,
    basis_fingerprint text NOT NULL,
    status text NOT NULL,
    axis_payload jsonb NOT NULL,
    route_payload jsonb NOT NULL,
    metric_receipt_ids jsonb NOT NULL,
    snapshot_id text NOT NULL,
    FOREIGN KEY(snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id),
    FOREIGN KEY(project_id, fiber_id)
        REFERENCES knowledge_fiber(project_id, fiber_id),
    UNIQUE(snapshot_id, fiber_id, basis_fingerprint)
);

-- Incumbent MetricReceipt bodies stay intact; this is durable query binding only.
CREATE TABLE metric_receipt_record (
    metric_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    epoch_id text NOT NULL,
    authority text NOT NULL,
    sequence_index bigint NOT NULL CHECK (sequence_index >= 0),
    canonical_payload jsonb NOT NULL,
    snapshot_id text NOT NULL,
    UNIQUE(epoch_id, sequence_index),
    FOREIGN KEY(snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE controller_decision_record (
    decision_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    evaluation_epoch_id text NOT NULL,
    status text NOT NULL,
    canonical_payload jsonb NOT NULL,
    snapshot_id text NOT NULL,
    FOREIGN KEY(snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE solver_view_record (
    view_id text PRIMARY KEY CHECK (view_id ~ '^solver-view:[0-9a-f]{64}$'),
    project_id text NOT NULL REFERENCES orion_project(project_id),
    project_snapshot_id text NOT NULL,
    target_id text NOT NULL,
    compiler_identity text NOT NULL,
    canonical_payload jsonb NOT NULL,
    FOREIGN KEY(project_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);
CREATE INDEX solver_view_by_target_snapshot
    ON solver_view_record(project_id, target_id, project_snapshot_id);

-- Durable workflow history. Event heads should also be sealed into resumable/release
-- state so a valid-but-shortened internal history is detectable after tail loss.
CREATE TABLE workflow_execution (
    workflow_id text PRIMARY KEY,
    project_id text NOT NULL REFERENCES orion_project(project_id),
    project_snapshot_id text NOT NULL,
    workflow_status text NOT NULL,
    next_sequence bigint NOT NULL CHECK (next_sequence >= 0),
    head_event_hash char(64) NOT NULL,
    FOREIGN KEY(project_snapshot_id, project_id)
        REFERENCES orion_snapshot(snapshot_id, project_id)
);

CREATE TABLE workflow_event (
    workflow_id text NOT NULL REFERENCES workflow_execution(workflow_id),
    sequence bigint NOT NULL CHECK (sequence >= 0),
    event_hash char(64) NOT NULL UNIQUE,
    previous_event_hash text NOT NULL,
    kind text NOT NULL,
    canonical_payload jsonb NOT NULL,
    PRIMARY KEY(workflow_id, sequence)
);

CREATE TABLE workflow_activity (
    workflow_id text NOT NULL REFERENCES workflow_execution(workflow_id),
    activity_id text NOT NULL,
    invocation_id text NOT NULL,
    input_digest text NOT NULL,
    retry_safe boolean NOT NULL,
    external_effect boolean NOT NULL,
    max_attempts integer NOT NULL CHECK (max_attempts >= 1),
    attempt_count integer NOT NULL CHECK (attempt_count >= 0),
    status text NOT NULL,
    result_digest text,
    last_error text,
    PRIMARY KEY(workflow_id, activity_id)
);

CREATE TABLE migration_import_receipt (
    receipt_id text PRIMARY KEY CHECK (receipt_id ~ '^import-receipt:[0-9a-f]{64}$'),
    project_id text NOT NULL REFERENCES orion_project(project_id),
    source_store_kind text NOT NULL,
    source_store_identity text NOT NULL,
    source_head_hash text NOT NULL,
    target_backend_identity text NOT NULL,
    parity_digest char(64) NOT NULL CHECK (parity_digest ~ '^[0-9a-f]{64}$'),
    canonical_payload jsonb NOT NULL,
    created_at_utc timestamptz NOT NULL
);

CREATE TABLE runtime_artifact_identity (
    identity_id text PRIMARY KEY CHECK (identity_id ~ '^runtime-artifact:[0-9a-f]{64}$'),
    artifact_sha256 char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    source_revision text NOT NULL,
    builder_id text NOT NULL,
    build_type text NOT NULL,
    provenance_id text NOT NULL,
    image_digest text,
    environment_manifest_digest text,
    canonical_payload jsonb NOT NULL
);

-- Rebuildable full-text/vector/graph indexes are deliberately absent from this
-- source-of-truth schema. Their loss must reduce speed, not erase knowledge or mint
-- authority. Likewise, infrastructure authentication/authorization is separate from
-- RAKL scientific authority even when both are represented in the same deployment.
