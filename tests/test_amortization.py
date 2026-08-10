from rakl.amortization import CapabilityPoint, CostBreakdown, ReuseEconomics, cost_to_capability


def test_break_even_counts_induction_cost() -> None:
    economics = ReuseEconomics(
        induction_cost=100.0,
        baseline_per_task_cost=20.0,
        reuse_per_task_cost=10.0,
    )
    assert economics.break_even_reuse_count == 11
    assert economics.saving_at(10) == 0
    assert economics.saving_at(11) > 0


def test_no_break_even_when_reuse_is_not_cheaper_per_task() -> None:
    economics = ReuseEconomics(
        induction_cost=10.0,
        baseline_per_task_cost=5.0,
        reuse_per_task_cost=6.0,
    )
    assert economics.break_even_reuse_count is None


def test_total_cost_does_not_hide_preprocessing_or_verification() -> None:
    cost = CostBreakdown(
        induction=5,
        training=10,
        retrieval=2,
        adaptation_or_reasoning=3,
        tools=4,
        verification=6,
    )
    assert cost.total == 30


def test_cost_to_capability_respects_validity_constraint() -> None:
    cheap_invalid = CapabilityPoint(
        capability=0.9,
        cost=CostBreakdown(adaptation_or_reasoning=1),
        validity_failures=1,
    )
    valid = CapabilityPoint(
        capability=0.9,
        cost=CostBreakdown(adaptation_or_reasoning=3),
        validity_failures=0,
    )
    selected = cost_to_capability(
        (cheap_invalid, valid),
        target_capability=0.8,
        max_validity_failures=0,
    )
    assert selected == valid


def test_cost_to_capability_returns_none_when_target_unreached() -> None:
    point = CapabilityPoint(
        capability=0.4,
        cost=CostBreakdown(training=1),
    )
    assert cost_to_capability((point,), target_capability=0.8) is None
