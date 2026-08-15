-- ORION engineering closure — PostgreSQL production schema V1.
--
-- PROVENANCE AND PRECEDENCE
-- ------------------------------------------------------------------------
-- POSTGRES_SCHEMA_DRAFT.sql is a *design artifact* that predates the shipped
-- SQLite reference implementation. Where the two disagree, THE SHIPPED CODE
-- WINS and the divergence is recorded below in "DRAFT VS CODE DISCREPANCIES".
-- Every table, column, type, constraint and index in section 1 is derived
-- field-for-field from a `CREATE TABLE` statement that exists in src/rakl:
--
--   snapshots, project_heads, epistemic_statuses, transitions
--       <- src/rakl/engineering_store.py:120-156
--   semantic_fibers, semantic_atoms, semantic_atom_versions,
--   semantic_witnesses, semantic_witness_versions, semantic_batch_commits
--       <- src/rakl/engineering_semantic_store.py:258-303
--   atlas_plane_commits, atlas_charts, atlas_transitions, atlas_obstructions
--       <- src/rakl/engineering_atlas_store.py:196-223
--   engineering_evidence_records, engineering_evidence_batch_commits
--       <- src/rakl/engineering_evidence_store.py:134-153
--   control_projection
--       <- src/rakl/engineering_control_store.py:86-96
--   workflows, workflow_events, workflow_activities
--       <- src/rakl/engineering_workflow.py:146-175
--   worker_activities, leases, worker_events
--       <- src/rakl/engineering_workflow_workers.py:139-169
--
-- NOTHING in this file has been executed. There is no PostgreSQL server and no
-- PostgreSQL client on the verification host, so this DDL is UNPARSED and
-- UNVALIDATED. See BACKEND_PARITY_V1.json -> not_exercised.
--
--
-- ISOLATION CONTRACT
-- ------------------------------------------------------------------------
-- Every reference store wraps its writes in `BEGIN IMMEDIATE`, which takes the
-- database write lock at transaction *start*. Correctness of the project-head
-- compare-and-swap (engineering_store.py:339-384) rests on the head SELECT and
-- the head UPDATE being atomic with respect to every other writer.
--
-- The faithful PostgreSQL analogue is SERIALIZABLE with retry on SQLSTATE
-- 40001. The batch stores (semantic, evidence) validate a *base revision* read
-- from one table and then write rows into several others; only a true
-- serializable snapshot covers that read/write skew. `SELECT ... FOR UPDATE`
-- on project_heads is the narrower pessimistic equivalent and matches
-- BEGIN IMMEDIATE's blocking behaviour more literally, but it protects only
-- the head-CAS path. SERIALIZABLE is therefore the default; FOR UPDATE is an
-- acceptable optimisation for the head-CAS path alone.
--
--
-- PAYLOAD COLUMNS ARE text, NOT jsonb  (deliberate divergence from the draft)
-- ------------------------------------------------------------------------
-- The draft types every payload column `jsonb`. That would be a correctness
-- regression here. Two shipped code paths compare the STORED STRING to a
-- freshly canonicalised JSON string byte-for-byte to decide idempotent replay
-- versus integrity failure:
--
--   engineering_atlas_store.py:261  existing["payload_json"] != self._dump(batch.payload())
--   engineering_workflow_workers.py:220  existing["spec_json"] != self._dump(spec.to_dict())
--
-- `jsonb` does not preserve byte identity: it reorders object keys, drops
-- duplicate keys and renormalises numbers and whitespace. Round-tripping the
-- canonical payload through `jsonb` would break both comparisons and, with
-- them, the idempotency contract. All payload columns are `text`.
-- (`json` would preserve bytes, but buys nothing the code uses; if operators
-- want indexed querying, add a GENERATED column `payload_json::jsonb` — the
-- authoritative bytes must stay in the text column.)


--
-- CONSTRAINTS PROMOTED BEYOND THE SQLite DDL
-- ------------------------------------------------------------------------
-- Section 1 declares a small number of constraints the SQLite `CREATE TABLE`
-- statements do not. Each is admitted only because a Python invariant already
-- makes it unfalsifiable — a promoted constraint that could reject a write the
-- reference accepts would be a behaviour change, not a tightening:
--
--   * id-format regexes on snapshot_id / transition_id / status_id
--       -> the ids are computed as "<prefix>:" + canonical_sha256(...)
--          (engineering_state.py:159, :317, :476) and the dataclasses reject
--          any supplied id that does not equal that value.
--   * hex-64 regexes on request_hash / event_hash / payload_sha256
--       -> canonical_sha256 returns lowercase hexdigest; _require_sha256
--          (engineering_state.py:45) enforces it on inputs.
--   * `sequence >= 0` on snapshots/project_heads/workflows/*_events
--       -> ProjectSnapshot.__post_init__ rejects a negative sequence
--          (engineering_state.py:112); event sequences start at 0 and only
--          increment (engineering_workflow_workers.py:184).
--   * `attempt_count >= 0` -> initialised to 0 and only incremented.
--   * enum CHECKs on transitions.status / workflows.status / *_activities.status
--       -> the writers pass `<Enum>.value` exclusively.
--   * snapshots' sequence/previous_snapshot_id CHECK -> engineering_state.py:113-118.
--   * transitions' status/after_snapshot_id CHECK -> verified against all three
--     writers; see D-14.
-- Everything else in section 1 is exactly what the shipped DDL declares.


-- ========================================================================
-- 1. TABLES THAT EXIST IN THE SHIPPED CODE  (authoritative)
-- ========================================================================

-- ---- state plane: engineering_store.py ---------------------------------

CREATE TABLE snapshots (
    snapshot_id          text PRIMARY KEY
                         CHECK (snapshot_id ~ '^snapshot:[0-9a-f]{64}$'),
    project_id           text NOT NULL,
    sequence             bigint NOT NULL CHECK (sequence >= 0),
    previous_snapshot_id text REFERENCES snapshots(snapshot_id),
    payload_json         text NOT NULL,
    UNIQUE (project_id, sequence),
    -- ProjectSnapshot.__post_init__ (engineering_state.py:113-118) rejects a
    -- sequence-0 snapshot with a parent and a sequence>0 snapshot without one.
    -- Promoted from the draft: the invariant is enforced by the dataclass, so
    -- the CHECK cannot reject anything the code would have written.
    CHECK ((sequence = 0 AND previous_snapshot_id IS NULL)
        OR (sequence > 0 AND previous_snapshot_id IS NOT NULL))
);

CREATE TABLE project_heads (
    project_id  text PRIMARY KEY,
    snapshot_id text NOT NULL REFERENCES snapshots(snapshot_id),
    sequence    bigint NOT NULL CHECK (sequence >= 0)
);

CREATE TABLE epistemic_statuses (
    status_id           text PRIMARY KEY
                        CHECK (status_id ~ '^epistemic-status:[0-9a-f]{64}$'),
    project_snapshot_id text NOT NULL REFERENCES snapshots(snapshot_id),
    target_id           text NOT NULL,
    fiber_id            text NOT NULL,
    payload_json        text NOT NULL
);

-- Load-bearing. engineering_store.py:266 fails closed when the same
-- snapshot/target/fibre coordinates yield a different EpistemicStatus: a
-- supposedly snapshot-bound input changed without minting a new snapshot.
-- Without this index the store degrades to last-writer-wins.
CREATE UNIQUE INDEX epistemic_status_unique_coordinates
    ON epistemic_statuses (project_snapshot_id, target_id, fiber_id);

CREATE TABLE transitions (
    transition_id       text PRIMARY KEY
                        CHECK (transition_id ~ '^transition:[0-9a-f]{64}$'),
    project_id          text NOT NULL,
    idempotency_key     text NOT NULL,
    request_hash        text NOT NULL CHECK (request_hash ~ '^[0-9a-f]{64}$'),
    before_snapshot_id  text NOT NULL REFERENCES snapshots(snapshot_id),
    after_snapshot_id   text REFERENCES snapshots(snapshot_id),
    status              text NOT NULL CHECK (status IN (
                            'COMMITTED','ABORTED','RETRY_REQUIRED',
                            'RECOVERY_REQUIRED','CANNOT_CHECK')),
    payload_json        text NOT NULL,
    -- Load-bearing. engineering_store.py:330-337 replays the stored receipt on
    -- a repeated key and raises IdempotencyConflict when the request hash
    -- differs. Both branches presuppose at most one row per (project, key).
    UNIQUE (project_id, idempotency_key),
    -- Verified against every writer: commit_transition writes after_snapshot_id
    -- only on the COMMITTED branch (engineering_store.py:399-414); the
    -- RETRY_REQUIRED branch (:350) and record_noncommitted_transition (:437)
    -- both hard-code after_snapshot_id=None.
    CHECK ((status =  'COMMITTED' AND after_snapshot_id IS NOT NULL)
        OR (status <> 'COMMITTED' AND after_snapshot_id IS NULL))
);

-- ---- semantic plane: engineering_semantic_store.py ---------------------

CREATE TABLE semantic_fibers (
    fiber_id                 text PRIMARY KEY,
    parent_fiber_id          text REFERENCES semantic_fibers(fiber_id),
    created_from_snapshot_id text NOT NULL,
    created_from_sequence    bigint NOT NULL CHECK (created_from_sequence >= 0)
);

CREATE TABLE semantic_atoms (
    atom_id  text PRIMARY KEY,
    fiber_id text NOT NULL REFERENCES semantic_fibers(fiber_id),
    kind     text NOT NULL
);

CREATE TABLE semantic_atom_versions (
    version_id             text PRIMARY KEY,
    atom_id                text NOT NULL REFERENCES semantic_atoms(atom_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence    bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_version_id  text REFERENCES semantic_atom_versions(version_id),
    payload_json           text NOT NULL,
    -- Load-bearing: one atom cannot have two versions valid from the same
    -- sequence (engineering_semantic_store.py:436).
    UNIQUE (atom_id, valid_from_sequence)
);
CREATE INDEX semantic_atom_versions_lookup
    ON semantic_atom_versions (atom_id, valid_from_sequence DESC);

CREATE TABLE semantic_witnesses (
    witness_id    text PRIMARY KEY,
    left_atom_id  text NOT NULL REFERENCES semantic_atoms(atom_id),
    right_atom_id text NOT NULL REFERENCES semantic_atoms(atom_id)
);

CREATE TABLE semantic_witness_versions (
    version_id             text PRIMARY KEY,
    witness_id             text NOT NULL REFERENCES semantic_witnesses(witness_id),
    valid_from_snapshot_id text NOT NULL,
    valid_from_sequence    bigint NOT NULL CHECK (valid_from_sequence >= 0),
    supersedes_version_id  text REFERENCES semantic_witness_versions(version_id),
    payload_json           text NOT NULL,
    UNIQUE (witness_id, valid_from_sequence)
);
CREATE INDEX semantic_witness_versions_lookup
    ON semantic_witness_versions (witness_id, valid_from_sequence DESC);

CREATE TABLE semantic_batch_commits (
    batch_id             text PRIMARY KEY,
    sequence             bigint NOT NULL,
    committed_snapshot_id text NOT NULL,
    semantic_revision    text NOT NULL,
    batch_json           text NOT NULL,
    -- Load-bearing: serialises the semantic plane. A second batch at the same
    -- sequence is a stale-base write, not a newer one
    -- (engineering_semantic_store.py:578).
    UNIQUE (sequence)
);

-- ---- atlas plane: engineering_atlas_store.py ---------------------------
-- Batch-scoped, not version-scoped. Charts/transitions/obstructions belong to
-- exactly one commit batch and the whole plane commits or none of it does.

CREATE TABLE atlas_plane_commits (
    batch_id              text PRIMARY KEY,
    committed_snapshot_id text NOT NULL,
    atlas_revision        text NOT NULL,
    chart_count           integer NOT NULL,
    transition_count      integer NOT NULL,
    obstruction_count     integer NOT NULL,
    payload_json          text NOT NULL
);

CREATE TABLE atlas_charts (
    chart_id     text PRIMARY KEY,
    batch_id     text NOT NULL REFERENCES atlas_plane_commits(batch_id),
    layer        text NOT NULL,
    payload_json text NOT NULL
);

CREATE TABLE atlas_transitions (
    transition_id   text PRIMARY KEY,
    batch_id        text NOT NULL REFERENCES atlas_plane_commits(batch_id),
    source_chart_id text NOT NULL REFERENCES atlas_charts(chart_id),
    target_chart_id text NOT NULL REFERENCES atlas_charts(chart_id),
    payload_json    text NOT NULL
);

CREATE TABLE atlas_obstructions (
    obstruction_id text PRIMARY KEY,
    batch_id       text NOT NULL REFERENCES atlas_plane_commits(batch_id),
    -- NOT NULL in the code. An obstruction always names the transition it
    -- obstructs; the draft's atlas_obstruction has no such column at all.
    transition_id  text NOT NULL REFERENCES atlas_transitions(transition_id),
    payload_json   text NOT NULL
);

-- ---- evidence plane: engineering_evidence_store.py ---------------------

CREATE TABLE engineering_evidence_records (
    evidence_id         text PRIMARY KEY,
    project_id          text NOT NULL,
    logical_record_id   text NOT NULL,
    payload_sha256      text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
    created_snapshot_id text NOT NULL,
    created_sequence    bigint NOT NULL CHECK (created_sequence >= 0),
    payload_json        text NOT NULL,
    -- Load-bearing. engineering_evidence_store.py:234/276 refuses to rebind a
    -- logical evidence record id to different content. The draft's
    -- evidence_record table has no logical_record_id column and therefore
    -- CANNOT express this invariant — see discrepancy D-07.
    UNIQUE (project_id, logical_record_id)
);
CREATE INDEX engineering_evidence_by_project_sequence
    ON engineering_evidence_records (project_id, created_sequence, logical_record_id);

CREATE TABLE engineering_evidence_batch_commits (
    batch_id              text PRIMARY KEY,
    project_id            text NOT NULL,
    sequence              bigint NOT NULL,
    committed_snapshot_id text NOT NULL,
    evidence_revision     text NOT NULL,
    batch_json            text NOT NULL
);

-- ---- control projection: engineering_control_store.py ------------------
-- Derived/rebuildable read model. Keep it in the same database for
-- transactional convenience; its loss is a latency event, not knowledge loss.

CREATE TABLE control_projection (
    record_id           text PRIMARY KEY,
    project_snapshot_id text NOT NULL,
    kind                text NOT NULL,
    source_object_id    text NOT NULL,
    payload_json        text NOT NULL,
    UNIQUE (project_snapshot_id, kind, source_object_id)
);
CREATE INDEX control_projection_snapshot_kind
    ON control_projection (project_snapshot_id, kind, source_object_id);

-- ---- durable workflow history: engineering_workflow.py -----------------

CREATE TABLE workflows (
    workflow_id         text PRIMARY KEY,
    project_id          text NOT NULL,
    project_snapshot_id text NOT NULL,
    status              text NOT NULL CHECK (status IN (
                            'RUNNING','COMPLETED','FAILED',
                            'RECOVERY_REQUIRED','CANNOT_CHECK')),
    next_sequence       bigint NOT NULL CHECK (next_sequence >= 0),
    head_event_hash     text NOT NULL
);

CREATE TABLE workflow_events (
    workflow_id         text NOT NULL REFERENCES workflows(workflow_id),
    sequence            bigint NOT NULL CHECK (sequence >= 0),
    kind                text NOT NULL,
    payload_json        text NOT NULL,
    -- The genesis event stores the empty string, not NULL. Do not "fix" this
    -- to NULL: the empty string is a hashed input to the chain link.
    previous_event_hash text NOT NULL,
    event_hash          text NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (workflow_id, sequence),
    UNIQUE (event_hash)
);

CREATE TABLE workflow_activities (
    workflow_id   text NOT NULL REFERENCES workflows(workflow_id),
    activity_id   text NOT NULL,
    spec_json     text NOT NULL,
    status        text NOT NULL CHECK (status IN (
                      'SCHEDULED','RUNNING','COMPLETED','FAILED','RECOVERY_REQUIRED')),
    attempt_count integer NOT NULL CHECK (attempt_count >= 0),
    result_digest text,
    last_error    text,
    PRIMARY KEY (workflow_id, activity_id)
);

-- ---- multi-worker execution: engineering_workflow_workers.py -----------
-- A separate SQLite file in the reference implementation, hence no declared FK
-- from worker_activities to workflows. See section 3.

CREATE TABLE worker_activities (
    workflow_id     text NOT NULL,
    activity_id     text NOT NULL,
    spec_json       text NOT NULL,
    status          text NOT NULL CHECK (status IN (
                        'SCHEDULED','RUNNING','COMPLETED','FAILED','RECOVERY_REQUIRED')),
    attempt_count   integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    -- SQLite INTEGER 0/1 flag; boolean is the faithful PostgreSQL type.
    effect_started  boolean NOT NULL DEFAULT false,
    result_digest   text,
    idempotency_key text NOT NULL,
    PRIMARY KEY (workflow_id, activity_id)
);

-- Load-bearing. engineering_workflow_workers.py:218-226 treats a repeated
-- (workflow_id, idempotency_key) as duplicate delivery of the same logical
-- schedule and raises WorkflowIntegrityError when the bound spec differs.
-- Without this index a duplicated at-least-once delivery silently creates a
-- second activity and a second external effect.
CREATE UNIQUE INDEX ux_worker_activity_idem
    ON worker_activities (workflow_id, idempotency_key);

CREATE TABLE leases (
    workflow_id  text NOT NULL,
    activity_id  text NOT NULL,
    worker_id    text NOT NULL,
    lease_token  text NOT NULL,
    -- Injected integer clock in the reference engine; keep it integral so a
    -- production clock substitution does not change lease arithmetic.
    acquired_at  bigint NOT NULL,
    heartbeat_at bigint NOT NULL,
    ttl          bigint NOT NULL,
    PRIMARY KEY (workflow_id, activity_id)
    -- No FK to worker_activities: the code declares none, and a lease row is
    -- deleted independently of the activity it covers. Adding it is listed in
    -- section 3, not done here.
);

CREATE TABLE worker_events (
    workflow_id         text NOT NULL,
    sequence            bigint NOT NULL CHECK (sequence >= 0),
    kind                text NOT NULL,
    payload_json        text NOT NULL,
    previous_event_hash text NOT NULL,
    event_hash          text NOT NULL CHECK (event_hash ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (workflow_id, sequence)
    -- NOTE: no UNIQUE(event_hash) here, matching the code. workflow_events in
    -- engineering_workflow.py DOES declare it. See discrepancy D-11.
);


-- ========================================================================
-- 2. DRAFT-ONLY TABLES — NOT IMPLEMENTED IN THE SHIPPED CODE
-- ========================================================================
-- POSTGRES_SCHEMA_DRAFT.sql defines the tables below. No `CREATE TABLE` in
-- src/rakl corresponds to any of them, and no store writes them. They are
-- listed, not created: creating an unwritten table invites a reader to believe
-- a plane is persisted when it is not.
--
--   orion_project               (no project registry exists; project_id is a
--                                bare TEXT column everywhere in the code)
--   residual_event
--   saturation_certificate
--   metric_receipt_record
--   controller_decision_record
--   solver_view_record          (SolverView is built in engineering_integration.py
--                                but never persisted to a store)
--   migration_import_receipt    (ImportReceipt exists in engineering_migration.py
--                                as an in-memory dataclass only; nothing writes it
--                                to any database)
--   runtime_artifact_identity
--
-- Promote each one only together with the code that writes it, so that the
-- schema never claims durability the runtime does not provide.


-- ========================================================================
-- 3. CONSTRAINTS POSTGRES COULD ENFORCE THAT THE REFERENCE CANNOT
-- ========================================================================
-- Deliberately NOT declared in section 1. The reference implementation splits
-- these planes across separate SQLite database files, so it cannot declare
-- cross-plane foreign keys. Co-locating them in one PostgreSQL database makes
-- the keys expressible — and enabling them would reject writes the SQLite
-- reference accepts. That is a behavioural change, not a free tightening, and
-- it must be gated on the MIGRATION_PLAN M2 dual-write parity evidence:
--
--   epistemic_statuses.project_snapshot_id      -> snapshots            (declared: same file)
--   semantic_*.valid_from_snapshot_id           -> snapshots(snapshot_id)
--   semantic_fibers.created_from_snapshot_id    -> snapshots(snapshot_id)
--   engineering_evidence_records.created_snapshot_id -> snapshots(snapshot_id)
--   atlas_plane_commits.committed_snapshot_id   -> snapshots(snapshot_id)
--   semantic_batch_commits.committed_snapshot_id-> snapshots(snapshot_id)
--   control_projection.project_snapshot_id      -> snapshots(snapshot_id)
--   workflows.project_snapshot_id               -> snapshots(snapshot_id)
--   worker_activities.workflow_id               -> workflows(workflow_id)
--   worker_events.workflow_id                   -> workflows(workflow_id)
--
-- Likewise the draft's project-scoped composite keys — PRIMARY KEY
-- (project_id, fiber_id) instead of PRIMARY KEY (fiber_id) — are a genuine
-- semantic upgrade the code does not have. Adopting them is a data-model
-- migration with an identity rewrite, not a DDL detail. See D-04.


-- ========================================================================
-- 4. DRAFT VS CODE DISCREPANCIES  (draft predates the code; the code wins)
-- ========================================================================
--
-- D-01  Table names: the draft renames every table.
--         orion_snapshot/snapshots, orion_project_head/project_heads,
--         orion_state_transition/transitions,
--         orion_epistemic_status/epistemic_statuses,
--         knowledge_fiber/semantic_fibers, knowledge_atom/semantic_atoms,
--         knowledge_atom_version/semantic_atom_versions,
--         compatibility_witness/semantic_witnesses,
--         compatibility_witness_version/semantic_witness_versions,
--         evidence_record/engineering_evidence_records,
--         workflow_execution/workflows, workflow_activity/worker_activities.
--       V1 keeps the shipped names.
--
-- D-02  orion_project does not exist in the code. Every draft FK to
--       orion_project(project_id) is unbacked. V1 omits the table and the FKs.
--
-- D-03  Column names differ inside matched tables:
--         created_snapshot_id/created_from_snapshot_id (fibers),
--         created_sequence/created_from_sequence,
--         atom_version_id/version_id,
--         supersedes_atom_version_id/supersedes_version_id,
--         canonical_payload/payload_json,
--         orion_project_head.snapshot_id vs project_heads.snapshot_id (same).
--       V1 keeps the shipped names.
--
-- D-04  Scoping: the draft is project-scoped (PRIMARY KEY (project_id, X));
--       the code is globally scoped (PRIMARY KEY (X)). Under the shipped code
--       two projects cannot hold the same fiber/atom/chart id. This is a real
--       semantic divergence and the draft's choice is the better one, but it
--       is an identity migration, not a schema tweak. Recorded, not adopted.
--
-- D-05  Payload type: draft says jsonb, V1 says text. jsonb breaks the
--       byte-for-byte payload comparison at engineering_atlas_store.py:261 and
--       engineering_workflow_workers.py:220. See the header note. CODE WINS
--       and this one is a correctness finding, not a preference.
--
-- D-06  Atlas plane shape. Draft: atlas_chart + atlas_chart_version, snapshot-
--       bound and versioned, with atlas_transition keyed on chart ids and
--       CHECK (source_chart_id <> target_chart_id). Code: atlas_charts with a
--       `layer` column and a batch_id FK into atlas_plane_commits — batch
--       scoped, unversioned, whole-plane commit. Draft has no atlas_plane_commits.
--       These are different designs, not different spellings.
--
-- D-07  DEFECT-CLASS DISCREPANCY. Draft evidence_record has no
--       logical_record_id column, so it cannot carry the code's
--       UNIQUE(project_id, logical_record_id). That constraint is precisely
--       what makes "logical evidence record id cannot be rebound"
--       (engineering_evidence_store.py:234) enforceable. Deploying the draft
--       schema would silently permit a rebinding the shipped code fails closed
--       on. V1 keeps the column and the constraint.
--
-- D-08  DEFECT-CLASS DISCREPANCY. Draft workflow_activity has no
--       idempotency_key column and therefore no analogue of
--       ux_worker_activity_idem UNIQUE(workflow_id, idempotency_key). Under
--       at-least-once delivery the draft schema admits a duplicate activity
--       and a duplicate external effect. V1 keeps the column and the index.
--
-- D-09  DEFECT-CLASS DISCREPANCY. Draft atlas_obstruction has only
--       (project_id, obstruction_id) — it drops the code's NOT NULL
--       transition_id FK, so a draft-schema obstruction cannot name what it
--       obstructs. V1 keeps the column.
--
-- D-10  Tables present in the code and absent from the draft:
--       atlas_plane_commits, semantic_batch_commits (with its UNIQUE(sequence)
--       plane serialiser), engineering_evidence_batch_commits, leases,
--       control_projection. Batch-commit tables are how the reference proves
--       whole-plane atomicity and idempotent replay; omitting them removes
--       the audit trail for "the batch committed or none of it did".
--
-- D-11  Draft workflow_event declares event_hash UNIQUE globally. The code's
--       worker_events does NOT (PK is (workflow_id, sequence)), while
--       engineering_workflow.py's workflow_events DOES. V1 mirrors each
--       shipped table's own choice rather than unifying them. The asymmetry
--       between the two shipped event logs is itself worth a follow-up.
--
-- D-12  Draft carries timestamptz columns (created_at, created_at_utc) on
--       several tables. The shipped stores keep every timestamp inside the
--       canonical payload, because the timestamp is a hashed input to the
--       object's content identity. V1 adds no timestamp columns: a column
--       whose value is not the hashed one invites two disagreeing answers to
--       "when". Add them later only as non-authoritative operational metadata.
--
-- D-13  Draft orion_snapshot carries the ProjectSnapshot fields as first-class
--       columns (evidence_cutoff, semantic_state_revision, metric_ledger_head,
--       episode_store_head, authority_projection_revision, controller_epoch_id,
--       saturation_basis_ids). The code stores the whole ProjectSnapshot as
--       payload_json and indexes only (project_id, sequence). Projecting those
--       fields into columns is safe (they are covered by the snapshot hash) and
--       is the single most useful draft idea not adopted here — deferred
--       because V1's remit is parity with the shipped code, and a generated
--       column set can be added without touching the authoritative bytes.
--
-- D-14  Draft CHECK on orion_state_transition status/after_snapshot_id was
--       verified against all three writers before promotion (see the comment on
--       `transitions`). It holds. Promoted.
