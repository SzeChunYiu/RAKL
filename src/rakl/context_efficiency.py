from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Tuple

from .context_compiler import ContextCompileReport, ContextItem


@dataclass(frozen=True)
class ContextEfficiencyReport:
    archive_record_count: int
    archive_declared_token_cost: int
    selected_record_count: int
    active_tokens: int
    budget_tokens: int
    mandatory_recall: float
    required_coverage_recall: float
    archive_context_ratio: float
    active_budget_ratio: float
    weighted_epistemic_density: float
    zero_marginal_selected_optional_ids: Tuple[str, ...]
    authority_scope: str = "ENGINEERING_CONTEXT_EFFICIENCY_ONLY"

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def measure_context_efficiency(
    items: Iterable[ContextItem],
    compile_report: ContextCompileReport,
    *,
    required_coverage_atoms: Iterable[str] = (),
    coverage_weights: Mapping[str, float] | None = None,
) -> ContextEfficiencyReport:
    """Measure context efficiency without interpreting it as scientific quality.

    The routine uses declared token costs. Strict model-specific token claims still
    require the exact counter/certificate path in ``token_budget.py``.
    """
    pool = tuple(items)
    by_id = {item.record_id: item for item in pool}
    if len(by_id) != len(pool):
        raise ValueError("duplicate context record_id")
    selected = tuple(by_id[record_id] for record_id in compile_report.selected_record_ids)

    mandatory_ids = {item.record_id for item in pool if item.mandatory}
    selected_ids = {item.record_id for item in selected}
    mandatory_recall = 1.0 if not mandatory_ids else len(mandatory_ids & selected_ids) / len(mandatory_ids)

    required = set(required_coverage_atoms)
    covered = set(compile_report.covered_atoms)
    required_recall = 1.0 if not required else len(required & covered) / len(required)

    archive_tokens = sum(item.token_cost for item in pool)
    archive_context_ratio = 0.0 if archive_tokens == 0 else compile_report.used_tokens / archive_tokens
    active_budget_ratio = 0.0 if compile_report.budget_tokens == 0 else compile_report.used_tokens / compile_report.budget_tokens

    weights = dict(coverage_weights or {})
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("coverage weights cannot be negative")

    # Reconstruct the marginal coverage contribution of the deterministic output
    # order. Mandatory items are not labelled padding even when redundant because
    # their inclusion is an epistemic constraint rather than an optimization choice.
    seen: set[str] = set()
    selected_value = 0.0
    zero_marginal_optional: list[str] = []
    for item in selected:
        new_atoms = set(item.coverage_atoms) - seen
        marginal = sum(weights.get(atom, 1.0) for atom in new_atoms)
        if not item.mandatory and marginal <= 0:
            zero_marginal_optional.append(item.record_id)
        selected_value += marginal
        seen.update(item.coverage_atoms)
    density = 0.0 if compile_report.used_tokens == 0 else selected_value / compile_report.used_tokens

    return ContextEfficiencyReport(
        archive_record_count=len(pool),
        archive_declared_token_cost=archive_tokens,
        selected_record_count=len(selected),
        active_tokens=compile_report.used_tokens,
        budget_tokens=compile_report.budget_tokens,
        mandatory_recall=mandatory_recall,
        required_coverage_recall=required_recall,
        archive_context_ratio=archive_context_ratio,
        active_budget_ratio=active_budget_ratio,
        weighted_epistemic_density=density,
        zero_marginal_selected_optional_ids=tuple(zero_marginal_optional),
    )
