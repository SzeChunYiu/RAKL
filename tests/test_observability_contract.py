import math
import pytest

from rakl.evolution_metrics import (
    alpha_per_look,
    brier_score,
    categorical_information_gain,
    expected_calibration_error,
    gain_per_cost,
    normalize_for_control,
    paired_effect,
)
from rakl.evolution_trace import (
    DecisionStatus,
    HardGateObservation,
    HardGateStatus,
    MetricAuthority,
    MetricDefinition,
    MetricDirection,
    MetricLedger,
    MetricRegistry,
    MetricReceipt,
    SelfModelSnapshot,
)
from rakl.meta_controller import (
    ActionEstimate,
    ComponentEstimate,
    DecisionPolicy,
    choose_meta_action,
)

H = "a" * 64
B = "b" * 64
C = "c" * 64
EPOCH = "epoch-1"


def defn(name="quality", authority=MetricAuthority.CONTROL_INPUT, direction=MetricDirection.MAXIMIZE):
    return MetricDefinition(name, "v1", "score", direction, authority, 0.0, 1.0) if authority is MetricAuthority.CONTROL_INPUT else MetricDefinition(name, "v1", "score", direction, authority)


def receipt(metric_id, definition, authority=None, index=0, sources=()):
    return MetricReceipt(
        metric_id=metric_id,
        metric_name=definition.metric_name,
        definition_hash=definition.definition_hash,
        epoch_id=EPOCH,
        value=0.5,
        unit=definition.unit,
        sample_n=20,
        candidate_hash=H,
        dataset_hash=B,
        evaluator_hash=C,
        resource_profile_hash=H,
        authority=authority or definition.authority,
        sequence_index=index,
        ci_low=0.4,
        ci_high=0.6,
        source_receipt_ids=sources,
    )


def self_model(epoch=EPOCH):
    return SelfModelSnapshot(H, B, epoch, C, ("problem:search", "regime:operator-exhausted"))


def policy(**overrides):
    values = dict(
        policy_id="p1",
        evaluation_epoch_id=EPOCH,
        weights=(("information_gain", 1.0), ("transfer_gain", 1.0)),
        uncertainty_penalty=0.5,
        max_component_uncertainty=0.3,
        minimum_utility_margin=0.05,
    )
    values.update(overrides)
    return DecisionPolicy(**values)


def action(name, receipt_ids, gate_receipt_id, vals=(0.8, 0.6), uncertainty=0.05, gate_status=HardGateStatus.PASS):
    d1, d2 = defn("information_gain"), defn("transfer_gain")
    return ActionEstimate(
        name,
        (
            ComponentEstimate("information_gain", vals[0], uncertainty, d1.definition_hash, (receipt_ids[0],)),
            ComponentEstimate("transfer_gain", vals[1], uncertainty, d2.definition_hash, (receipt_ids[1],)),
        ),
        (HardGateObservation("authority_leakage_zero", gate_status, (gate_receipt_id,)),),
    )


def registry():
    return MetricRegistry("reg-1", (defn("information_gain"), defn("transfer_gain"), defn("authority_leakage", MetricAuthority.HARD_PROTECTED, MetricDirection.CONSTRAINT)))


def ledger():
    d1, d2 = defn("information_gain"), defn("transfer_gain")
    gate = defn("authority_leakage", MetricAuthority.HARD_PROTECTED, MetricDirection.CONSTRAINT)
    return MetricLedger((
        receipt("m1", d1, index=0),
        receipt("m2", d2, index=1),
        receipt("m3", d1, index=2),
        receipt("m4", d2, index=3),
        receipt("g1", gate, index=4),
        receipt("g2", gate, index=5),
    ))


def test_frozen_normalization_uses_definition_not_candidate_set():
    dmax = MetricDefinition("quality", "v1", "score", MetricDirection.MAXIMIZE, MetricAuthority.CONTROL_INPUT, 0.0, 100.0)
    dmin = MetricDefinition("cost", "v1", "calls", MetricDirection.MINIMIZE, MetricAuthority.CONTROL_INPUT, 0.0, 100.0)
    assert normalize_for_control(25.0, dmax) == pytest.approx(0.25)
    assert normalize_for_control(25.0, dmin) == pytest.approx(0.75)
    assert normalize_for_control(1000.0, dmax) == 1.0


def test_metric_ledger_requires_backward_only_lineage_and_unique_sequence():
    d = defn()
    r1 = receipt("r1", d, index=0)
    r2 = receipt("r2", d, index=1, sources=("r1",))
    MetricLedger((r1, r2))
    with pytest.raises(ValueError, match="earlier"):
        MetricLedger((r2, r1))


def test_controller_enforces_hard_gates_and_does_not_let_failed_action_win():
    l = ledger()
    strong_but_failed = action("REPRESENTATION", ("m1", "m2"), "g1", vals=(1.0, 1.0), gate_status=HardGateStatus.FAIL)
    weaker_valid = action("OPERATOR", ("m3", "m4"), "g2", vals=(0.6, 0.5))
    result = choose_meta_action(decision_id="d", self_model=self_model(), actions=(strong_but_failed, weaker_valid), policy=policy(), metric_ledger=l, metric_registry=registry())
    assert result.status is DecisionStatus.SELECTED
    assert result.selected_action == "OPERATOR"


def test_controller_rejects_assurance_metric_as_control_input():
    d1, d2 = defn("information_gain"), defn("transfer_gain")
    gate = defn("authority_leakage", MetricAuthority.HARD_PROTECTED, MetricDirection.CONSTRAINT)
    bad = receipt("m1", d1, authority=MetricAuthority.EVOLUTION_EVIDENCE, index=0)
    l = MetricLedger((bad, receipt("m2", d2, index=1), receipt("g1", gate, index=2)))
    a = action("REPRESENTATION", ("m1", "m2"), "g1")
    with pytest.raises(ValueError, match="authority"):
        choose_meta_action(decision_id="d", self_model=self_model(), actions=(a,), policy=policy(), metric_ledger=l, metric_registry=registry())


def test_controller_abstains_on_small_margin_and_blocks_high_uncertainty():
    l = ledger()
    a = action("A", ("m1", "m2"), "g1", vals=(0.70, 0.70))
    b = action("B", ("m3", "m4"), "g2", vals=(0.69, 0.69))
    result = choose_meta_action(decision_id="d", self_model=self_model(), actions=(a,b), policy=policy(minimum_utility_margin=0.05), metric_ledger=l, metric_registry=registry())
    assert result.status is DecisionStatus.ABSTAIN
    high_u = action("C", ("m1", "m2"), "g1", vals=(1.0,1.0), uncertainty=0.9)
    result2 = choose_meta_action(decision_id="d2", self_model=self_model(), actions=(high_u,), policy=policy(), metric_ledger=l, metric_registry=registry())
    assert result2.status is DecisionStatus.BLOCKED


def test_self_model_and_policy_must_share_evaluation_epoch():
    l = ledger()
    a = action("A", ("m1", "m2"), "g1")
    with pytest.raises(ValueError, match="different evaluation epochs"):
        choose_meta_action(decision_id="d", self_model=self_model("epoch-old"), actions=(a,), policy=policy(), metric_ledger=l, metric_registry=registry())


def test_frozen_registry_catches_forged_receipt_authority():
    d1, d2 = defn("information_gain"), defn("transfer_gain")
    gate = defn("authority_leakage", MetricAuthority.HARD_PROTECTED, MetricDirection.CONSTRAINT)
    forged = receipt("m1", d1, authority=MetricAuthority.CONTROL_INPUT, index=0)
    # Same name but a forged definition hash/authority pair cannot become controller truth.
    forged = type(forged)(**{**forged.__dict__, "definition_hash": "f" * 64})
    l = MetricLedger((forged, receipt("m2", d2, index=1), receipt("g1", gate, index=2)))
    a = action("A", ("m1", "m2"), "g1")
    with pytest.raises(ValueError, match="definition hash"):
        choose_meta_action(decision_id="d", self_model=self_model(), actions=(a,), policy=policy(), metric_ledger=l, metric_registry=registry())


def test_information_gain_has_no_hidden_smoothing_and_statistics_are_explicit():
    assert math.isinf(categorical_information_gain([1.0, 0.0], [0.5, 0.5]))
    finite = categorical_information_gain([1.0, 0.0], [0.5, 0.5], smoothing_epsilon=1e-6)
    assert math.isfinite(finite) and finite > 0
    assert alpha_per_look(0.05, 5) == pytest.approx(0.01)
    assert brier_score([0, 1], [0, 1]) == 0
    assert expected_calibration_error([0.1, 0.9], [0, 1], bins=2) == pytest.approx(0.1)


def test_paired_effect_and_efficiency_remain_vector_metrics_not_one_fitness_score():
    effect = paired_effect([0, 0, 1], [1, 0, 2])
    assert effect.n == 3 and effect.win_rate == pytest.approx(2/3)
    assert effect.mean_delta == pytest.approx(2/3)
    assert gain_per_cost(2, 4) == 0.5
