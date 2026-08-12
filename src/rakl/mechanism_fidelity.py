"""Objective mechanism-fidelity benchmark primitives (refs #430).

The evaluator separates three questions that must not be collapsed:

* was the target observable predicted correctly?
* which candidate mechanisms remain compatible with the observed regimes?
* is point identification licensed, or must a survivor set remain open?

Known-answer worlds explicitly supply candidate predictions by regime. The gold
survivor set is therefore computed mechanically from observations; no LLM judge
is needed. A correct target prediction can still receive
``PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE`` when the claimed mechanism is
incompatible with the same world's evidence.

This module is benchmark/evaluation infrastructure only and mints no scientific
authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple

__all__ = [
    "MechanismAgentOutput",
    "MechanismFidelityReport",
    "MechanismFidelityVerdict",
    "MechanismPrediction",
    "MechanismWorld",
    "RegimeObservation",
    "evaluate_mechanism_fidelity",
]


class MechanismFidelityVerdict(str, Enum):
    PASS = "PASS"
    PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE = "PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE"
    MECHANISM_OR_IDENTIFICATION_FAILURE = "MECHANISM_OR_IDENTIFICATION_FAILURE"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class MechanismPrediction:
    mechanism_id: str
    regime_id: str
    outcome: str


@dataclass(frozen=True)
class RegimeObservation:
    regime_id: str
    outcome: str


@dataclass(frozen=True)
class MechanismWorld:
    world_id: str
    candidate_mechanism_ids: Tuple[str, ...]
    predictions: Tuple[MechanismPrediction, ...]
    observations: Tuple[RegimeObservation, ...]
    target_regime_id: str
    target_outcome: str
    available_discriminator_regimes: Tuple[str, ...]
    registered_valid_scope_regimes: Tuple[str, ...]
    known_answer_validated: bool | None
    frozen_before_output: bool | None

    def __post_init__(self) -> None:
        if not self.world_id.strip() or not self.target_regime_id.strip():
            raise ValueError("mechanism world requires ids")
        if not self.candidate_mechanism_ids:
            raise ValueError("mechanism world requires candidate mechanisms")
        if len(set(self.candidate_mechanism_ids)) != len(self.candidate_mechanism_ids):
            raise ValueError("candidate mechanism ids must be unique")
        obs_ids = [item.regime_id for item in self.observations]
        if len(set(obs_ids)) != len(obs_ids):
            raise ValueError("observed regime ids must be unique")
        pred_keys = [(item.mechanism_id, item.regime_id) for item in self.predictions]
        if len(set(pred_keys)) != len(pred_keys):
            raise ValueError("mechanism/regime prediction pairs must be unique")


@dataclass(frozen=True)
class MechanismAgentOutput:
    predicted_target_outcome: str
    survivor_mechanism_ids: Tuple[str, ...]
    mechanism_supported_ids: Tuple[str, ...]
    identified_mechanism_id: str | None
    proposed_discriminator_regime: str | None
    claimed_scope_regimes: Tuple[str, ...]


@dataclass(frozen=True)
class MechanismFidelityReport:
    verdict: MechanismFidelityVerdict
    prediction_correct: bool | None
    survivor_set_correct: bool | None
    mechanism_support_valid: bool | None
    identification_correct: bool | None
    discriminator_correct: bool | None
    scope_correct: bool | None
    correct_answer_wrong_mechanism: bool | None
    prediction_to_mechanism_leak: bool | None
    mechanism_to_identification_leak: bool | None
    gold_survivor_mechanism_ids: Tuple[str, ...] = ()
    gold_discriminator_regimes: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _prediction_map(world: MechanismWorld) -> Mapping[tuple[str, str], str]:
    return {(item.mechanism_id, item.regime_id): item.outcome for item in world.predictions}


def _gold_survivors(world: MechanismWorld) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    predictions = _prediction_map(world)
    reasons: list[str] = []
    survivors: list[str] = []
    for mechanism_id in world.candidate_mechanism_ids:
        compatible = True
        for observation in world.observations:
            key = (mechanism_id, observation.regime_id)
            if key not in predictions:
                reasons.append(f"missing_prediction:{mechanism_id}:{observation.regime_id}")
                compatible = False
                break
            if predictions[key] != observation.outcome:
                compatible = False
                break
        if compatible:
            survivors.append(mechanism_id)
    return tuple(sorted(survivors)), tuple(sorted(set(reasons)))


def _gold_discriminators(
    world: MechanismWorld,
    survivors: Sequence[str],
) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    predictions = _prediction_map(world)
    reasons: list[str] = []
    observed = {item.regime_id for item in world.observations}
    discriminators: list[str] = []
    if len(survivors) <= 1:
        return (), ()
    for regime_id in world.available_discriminator_regimes:
        if regime_id in observed:
            continue
        outcomes: set[str] = set()
        complete = True
        for mechanism_id in survivors:
            key = (mechanism_id, regime_id)
            if key not in predictions:
                reasons.append(f"missing_prediction:{mechanism_id}:{regime_id}")
                complete = False
                break
            outcomes.add(predictions[key])
        if complete and len(outcomes) > 1:
            discriminators.append(regime_id)
    return tuple(sorted(discriminators)), tuple(sorted(set(reasons)))


def evaluate_mechanism_fidelity(
    world: MechanismWorld,
    output: MechanismAgentOutput,
) -> MechanismFidelityReport:
    """Evaluate prediction, mechanism, identification and scope independently."""

    if world.known_answer_validated is None:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.CANNOT_CHECK,
            *(None,) * 9,
            reasons=("known_answer_validation_unknown",),
        )
    if world.known_answer_validated is False:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.CANNOT_CHECK,
            *(None,) * 9,
            reasons=("mechanism_world_not_known_answer_validated",),
        )
    if world.frozen_before_output is None:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.CANNOT_CHECK,
            *(None,) * 9,
            reasons=("world_freeze_chronology_unknown",),
        )
    if world.frozen_before_output is False:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.INVALID,
            *(None,) * 9,
            reasons=("mechanism_world_defined_posthoc",),
        )

    survivors, survivor_reasons = _gold_survivors(world)
    discriminators, discriminator_reasons = _gold_discriminators(world, survivors)
    contract_reasons = tuple(sorted(set(survivor_reasons + discriminator_reasons)))
    if contract_reasons or not survivors:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.INVALID,
            *(None,) * 9,
            gold_survivor_mechanism_ids=survivors,
            gold_discriminator_regimes=discriminators,
            reasons=contract_reasons or ("known_world_has_no_surviving_mechanism",),
        )

    candidate_set = set(world.candidate_mechanism_ids)
    reported_survivors = set(output.survivor_mechanism_ids)
    reported_supported = set(output.mechanism_supported_ids)
    invalid_references = sorted((reported_survivors | reported_supported) - candidate_set)
    if output.identified_mechanism_id is not None and output.identified_mechanism_id not in candidate_set:
        invalid_references.append(output.identified_mechanism_id)
    if invalid_references:
        return MechanismFidelityReport(
            MechanismFidelityVerdict.INVALID,
            *(None,) * 9,
            gold_survivor_mechanism_ids=survivors,
            gold_discriminator_regimes=discriminators,
            reasons=("unknown_mechanism_reference:" + ",".join(sorted(set(invalid_references))),),
        )

    prediction_correct = output.predicted_target_outcome == world.target_outcome
    survivor_set_correct = tuple(sorted(output.survivor_mechanism_ids)) == survivors
    mechanism_support_valid = reported_supported.issubset(set(survivors))

    if len(survivors) == 1:
        identification_correct = output.identified_mechanism_id == survivors[0]
        mechanism_to_identification_leak = False
    else:
        identification_correct = output.identified_mechanism_id is None
        mechanism_to_identification_leak = output.identified_mechanism_id is not None

    if discriminators:
        discriminator_correct = output.proposed_discriminator_regime in discriminators
    else:
        discriminator_correct = output.proposed_discriminator_regime is None

    claimed_scope = set(output.claimed_scope_regimes)
    registered_scope = set(world.registered_valid_scope_regimes)
    scope_correct = claimed_scope == registered_scope

    prediction_to_mechanism_leak = prediction_correct and not mechanism_support_valid
    cawm = prediction_correct and (
        not mechanism_support_valid
        or not identification_correct
        or not survivor_set_correct
    )

    mechanism_ok = (
        survivor_set_correct
        and mechanism_support_valid
        and identification_correct
        and discriminator_correct
        and scope_correct
    )
    if prediction_correct and not mechanism_ok:
        verdict = MechanismFidelityVerdict.PREDICTION_SUCCESS_WITH_MECHANISM_FAILURE
    elif not prediction_correct or not mechanism_ok:
        verdict = MechanismFidelityVerdict.MECHANISM_OR_IDENTIFICATION_FAILURE
    else:
        verdict = MechanismFidelityVerdict.PASS

    reasons: list[str] = []
    if not survivor_set_correct:
        reasons.append("survivor_set_incorrect")
    if not mechanism_support_valid:
        reasons.append("mechanism_support_includes_eliminated_candidate")
    if not identification_correct:
        reasons.append("point_identification_not_licensed_or_wrong")
    if not discriminator_correct:
        reasons.append("discriminator_selection_incorrect")
    if not scope_correct:
        reasons.append("mechanism_scope_incorrect")
    if not prediction_correct:
        reasons.append("target_prediction_incorrect")

    return MechanismFidelityReport(
        verdict=verdict,
        prediction_correct=prediction_correct,
        survivor_set_correct=survivor_set_correct,
        mechanism_support_valid=mechanism_support_valid,
        identification_correct=identification_correct,
        discriminator_correct=discriminator_correct,
        scope_correct=scope_correct,
        correct_answer_wrong_mechanism=cawm,
        prediction_to_mechanism_leak=prediction_to_mechanism_leak,
        mechanism_to_identification_leak=mechanism_to_identification_leak,
        gold_survivor_mechanism_ids=survivors,
        gold_discriminator_regimes=discriminators,
        reasons=tuple(reasons),
    )
