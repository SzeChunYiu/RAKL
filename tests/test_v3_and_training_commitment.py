from dataclasses import dataclass

from rakl.training_projection_binding import IntervalEstimate, build_training_projection_assurance
from rakl.v3_commitment import commit_named_components_v3


def test_component_commitment_is_order_stable_and_chained():
    schemas = {"a": "v1", "b": "v1"}
    a = commit_named_components_v3({"b": 2, "a": 1}, component_schema_versions=schemas, state_schema_version="s", sequence=0)
    b = commit_named_components_v3({"a": 1, "b": 2}, component_schema_versions=schemas, state_schema_version="s", sequence=0)
    assert a.digest == b.digest
    nxt = commit_named_components_v3({"a": 2, "b": 2}, component_schema_versions=schemas, state_schema_version="s", sequence=1, previous_digest=a.digest)
    assert nxt.previous_digest == a.digest


@dataclass(frozen=True)
class Structural:
    structure_id: str
    payload: str


@dataclass(frozen=True)
class Snapshot:
    snapshot_hash: str = "legacy"
    model_checkpoint_hash: str = "model"
    structural_catalog_hash: str = "catalog"
    probe_family_hash: str = "probe"
    values: tuple[int, ...] = (1, 2)


def test_training_assurance_binds_environment_and_fresh_split():
    assurance = build_training_projection_assurance(
        Snapshot(),
        (Structural("s1", "payload"),),
        assurance_id="a",
        code_commit_hash="code",
        tokenizer_hash="tok",
        optimizer_config_hash="opt",
        sampling_policy_hash="sample",
        train_split_hash="train",
        probe_split_hash="probe-split",
        fresh_assurance_split_hash="fresh",
        effect_intervals={"transfer": IntervalEstimate(.2, .1, .3)},
    )
    assert assurance.ready_for_fresh_experiment
    assert assurance.canonical_snapshot_digest.startswith("sha256:")
    assert assurance.canonical_structural_catalog_digest.startswith("sha256:")
    assert not assurance.grants_scientific_authority
