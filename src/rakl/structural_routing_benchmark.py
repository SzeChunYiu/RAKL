from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence
import hashlib
import random

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    RobustTask,
    generate,
    lexical_score,
    mechanism_predict,
    relational_predict,
    verify,
)


class RoutingArm(str, Enum):
    SEMANTIC_TOP1 = "SEMANTIC_TOP1"
    RELATIONAL_TOP1 = "RELATIONAL_TOP1"
    MECHANISM_TOP1 = "MECHANISM_TOP1"
    FULL_APPLICABILITY_GATE = "FULL_APPLICABILITY_GATE"
    FULL_HYBRID_RECOVERY = "FULL_HYBRID_RECOVERY"


@dataclass(frozen=True)
class RoutingEpisode:
    episode_id: str
    family: str
    episode_type: str
    candidates: tuple[RobustTask, ...]


@dataclass(frozen=True)
class RouteResult:
    arm: RoutingArm
    selected_item_id: str | None
    selected_gold: Decision | None
    success: bool
    invalid_execution: bool
    correct_abstention: bool
    selected_valid_distant: bool
    structural_checks: int
    recovered_after_rejected_candidate: bool


def _episode_id(seed: int, family: str, index: int, kind: str) -> str:
    return "route-" + hashlib.sha256(
        f"{seed}:{family}:{index}:{kind}".encode()
    ).hexdigest()[:16]


def _family_pool(seed: int, n_per_cell: int) -> dict[str, list[RobustTask]]:
    pool = {family: [] for family in FAMILIES}
    for task in generate(seed, n_per_cell):
        pool[task.family].append(task)
    return pool


def _cycle(items: Sequence[RobustTask], index: int) -> RobustTask:
    if not items:
        raise RuntimeError("registered routing stratum is empty")
    return items[index % len(items)]


def _candidate_sets(tasks: Sequence[RobustTask]) -> tuple[list[RobustTask], list[RobustTask], list[RobustTask]]:
    valid = [
        task
        for task in tasks
        if task.item_type == "VALID_DISTANT_TRANSFER"
        and verify(task) is Decision.ACCEPT
    ]
    # Load-bearing downstream trap: the candidate is actually invalid but a
    # derived-effect/mechanism projection still licenses it. Prefer the most
    # semantically attractive member of that class so the surface policy has a
    # genuine reason to choose it.
    invalid_mechanism = [
        task
        for task in tasks
        if verify(task) is Decision.REJECT
        and mechanism_predict(task) is Decision.ACCEPT
    ]
    invalid_mechanism.sort(key=lexical_score, reverse=True)
    unknown = [task for task in tasks if verify(task) is Decision.CANNOT_CHECK]
    return valid, invalid_mechanism, unknown


def make_routing_episodes(
    seed: int,
    n_standard_per_family: int,
    n_unknown_only_per_family: int,
) -> tuple[RoutingEpisode, ...]:
    # Large enough internal pool to avoid a one-template episode set while
    # preserving exact deterministic generation from the registered seed.
    pool = _family_pool(seed, max(4, n_standard_per_family * 2))
    rng = random.Random(seed ^ 0xA5A55A5A)
    episodes: list[RoutingEpisode] = []

    for family in FAMILIES:
        valid, invalid_mechanism, unknown = _candidate_sets(pool[family])
        if not valid or not invalid_mechanism or not unknown:
            raise RuntimeError(f"family lacks registered routing candidate strata: {family}")

        for index in range(n_standard_per_family):
            candidates = [
                _cycle(valid, index),
                _cycle(invalid_mechanism, index),
                _cycle(unknown, index),
            ]
            rng.shuffle(candidates)
            episodes.append(
                RoutingEpisode(
                    _episode_id(seed, family, index, "STANDARD"),
                    family,
                    "STANDARD",
                    tuple(candidates),
                )
            )

        # Unknown-only controls test whether gating can truly abstain. Candidate
        # IDs/order remain opaque; we deliberately use repeated *types* rather
        # than leaking a special control marker to routing policies.
        for index in range(n_unknown_only_per_family):
            start = index * 3
            candidates = [
                _cycle(unknown, start),
                _cycle(unknown, start + 1),
                _cycle(unknown, start + 2),
            ]
            rng.shuffle(candidates)
            episodes.append(
                RoutingEpisode(
                    _episode_id(seed, family, index, "UNKNOWN_ONLY"),
                    family,
                    "UNKNOWN_ONLY",
                    tuple(candidates),
                )
            )

    rng.shuffle(episodes)
    return tuple(episodes)


def _semantic_rank(episode: RoutingEpisode) -> list[RobustTask]:
    return sorted(episode.candidates, key=lexical_score, reverse=True)


def route_episode(episode: RoutingEpisode, arm: RoutingArm) -> RouteResult:
    ranked = _semantic_rank(episode)
    selected: RobustTask | None = None
    checks = 0
    recovered = False

    if arm is RoutingArm.SEMANTIC_TOP1:
        selected = ranked[0]
    elif arm is RoutingArm.RELATIONAL_TOP1:
        for task in ranked:
            checks += 1
            if relational_predict(task) is Decision.ACCEPT:
                selected = task
                break
    elif arm is RoutingArm.MECHANISM_TOP1:
        for task in ranked:
            checks += 1
            if mechanism_predict(task) is Decision.ACCEPT:
                selected = task
                break
    elif arm is RoutingArm.FULL_APPLICABILITY_GATE:
        checks = 1
        if verify(ranked[0]) is Decision.ACCEPT:
            selected = ranked[0]
    elif arm is RoutingArm.FULL_HYBRID_RECOVERY:
        for position, task in enumerate(ranked):
            checks += 1
            if verify(task) is Decision.ACCEPT:
                selected = task
                recovered = position > 0
                break
    else:  # pragma: no cover
        raise AssertionError(arm)

    if selected is None:
        all_unknown = all(verify(task) is Decision.CANNOT_CHECK for task in episode.candidates)
        return RouteResult(
            arm,
            None,
            None,
            False,
            False,
            all_unknown,
            False,
            checks,
            False,
        )

    gold = verify(selected)
    return RouteResult(
        arm=arm,
        selected_item_id=selected.item_id,
        selected_gold=gold,
        success=gold is Decision.ACCEPT,
        invalid_execution=gold is Decision.REJECT,
        correct_abstention=False,
        selected_valid_distant=(
            gold is Decision.ACCEPT
            and selected.item_type == "VALID_DISTANT_TRANSFER"
        ),
        structural_checks=checks,
        recovered_after_rejected_candidate=recovered,
    )


def route_all(
    episodes: Sequence[RoutingEpisode], arm: RoutingArm
) -> tuple[RouteResult, ...]:
    return tuple(route_episode(episode, arm) for episode in episodes)
