"""Required evolution-observatory outputs.

Production integration must render these from canonical receipts/traces; plots are
views, never evidence-authority objects and never sources of reconstructed truth.
"""
from __future__ import annotations

REQUIRED_PLOTS = (
    "evolution_causal_timeline",
    "genome_component_diff",
    "diagnosis_competing_causes",
    "controller_utility_runner_up_uncertainty",
    "hard_gate_panel",
    "development_paired_effects_ci",
    "fresh_assurance_paired_effects_ci",
    "resource_cost_decomposition",
    "predicted_vs_observed_history",
    "meta_prediction_calibration",
    "residual_layer_heatmap",
    "mutation_effectiveness_by_context",
    "quality_cost_pareto",
    "attribution_ablation",
    "evolution_efficiency_trend",
    "variant_dag_with_negative_branches",
    "epoch_boundaries_intervention_ledger",
    "metric_lineage_drilldown",
)


def required_plot_names() -> tuple[str, ...]:
    return REQUIRED_PLOTS
