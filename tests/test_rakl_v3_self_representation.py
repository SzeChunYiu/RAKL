from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

from rakl.evolution_archive import (
    RAKLVariant,
    VariantStatus,
    initialize_evolution_archive,
    register_challenger,
)
from rakl.experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes
from rakl.v3_runtime import RAKLV3State, materialize_state_substrate, record_task_episode, state_fingerprint
from rakl.experience_substrate import SubstrateKind, SubstrateRelation


def test_self_rakl_variants_appear_as_meta_method_substrate_nodes() -> None:
    archive = initialize_evolution_archive(
        RAKLVariant(
            variant_id="v1",
            method_hash="sha256:v1",
            parent_ids=(),
            capability_tags=("general",),
            resource_profile=(("token_cost", 1.0),),
            created_by_episode_ids=(),
            status=VariantStatus.INCUMBENT,
        )
    )
    archive = register_challenger(
        archive,
        RAKLVariant(
            variant_id="v2",
            method_hash="sha256:v2",
            parent_ids=("v1",),
            capability_tags=("general", "experience-learning"),
            resource_profile=(("token_cost", 1.1),),
            created_by_episode_ids=("meta-E1",),
            status=VariantStatus.CHALLENGER,
        ),
    )
    state = RAKLV3State(evolution=archive)
    snapshot = materialize_state_substrate(state)
    meta = snapshot.nodes_of_kind(SubstrateKind.META_METHOD)
    assert {node.node_id for node in meta} == {"variant:v1", "variant:v2"}
    incumbent = next(node for node in meta if node.node_id == "variant:v1")
    assert ("incumbent", "true") in incumbent.metadata
    ancestry = next(
        edge
        for edge in snapshot.edges
        if edge.source_id == "variant:v2" and edge.target_id == "variant:v1"
    )
    assert ancestry.relation is SubstrateRelation.DERIVED_FROM


def test_state_fingerprint_is_stable_for_equal_values_and_changes_with_learning() -> None:
    initial = RAKLV3State()
    assert state_fingerprint(initial) == state_fingerprint(replace(initial))

    episode_draft = TaskEpisode(
        episode_id="E1",
        task_id="task",
        atom_id="A1",
        context_hash="ctx",
        problem_signature=("structure",),
        fibre_snapshot_hash="fibre",
        operator_ids=("op",),
        action_trace=("act",),
        observation_ids=("obs",),
        verification_ids=("verify",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("artifact:E1",),
        artifact_hash="",
        timestamp="2026-08-11T09:15:00+00:00",
    )
    episode = replace(
        episode_draft,
        artifact_hash=sha256(episode_content_bytes(episode_draft)).hexdigest(),
    )
    learned = record_task_episode(initial, episode)
    assert state_fingerprint(learned) != state_fingerprint(initial)
