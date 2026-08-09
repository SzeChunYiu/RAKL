from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .formal_contracts import METHOD_SURFACES


@dataclass(frozen=True)
class ChildOperatorOwnership:
    operator_id: str
    parent_surfaces: Tuple[str, ...]
    purpose: str
    authority_boundary: str

    def validate(self) -> Tuple[str, ...]:
        problems: list[str] = []
        if not self.operator_id.strip():
            problems.append("operator_id_missing")
        if not self.parent_surfaces:
            problems.append("parent_surfaces_missing")
        for surface in self.parent_surfaces:
            if surface not in METHOD_SURFACES:
                problems.append(f"unknown_parent_surface:{surface}")
        if not self.purpose.strip():
            problems.append("purpose_missing")
        if not self.authority_boundary.strip():
            problems.append("authority_boundary_missing")
        return tuple(problems)


CHILD_OPERATORS = (
    ChildOperatorOwnership(
        operator_id="MODEL_CRITICISM_GENERATIVE_ADEQUACY",
        parent_surfaces=("benchmarking", "gap_discovery", "synthesis"),
        purpose="Evaluate frozen predictive/generative discrepancy probes and turn scientifically material misspecification into typed residuals.",
        authority_boundary="Probe adequacy is scoped and proposal-only; it cannot establish truth or mechanism identity.",
    ),
    ChildOperatorOwnership(
        operator_id="ASSUMPTION_SENSITIVITY_ROBUSTNESS",
        parent_surfaces=("benchmarking", "experiment_query_selection", "synthesis", "authority_promotion"),
        purpose="Evaluate whether a conclusion class survives a frozen scope-compatible envelope of assumption perturbations.",
        authority_boundary="Robustness is relative to the registered envelope and never proves the assumptions true.",
    ),
    ChildOperatorOwnership(
        operator_id="SELF_BOOTSTRAP_ACCEPTANCE",
        parent_surfaces=("capability_shaping", "objective_evolution", "benchmarking", "review"),
        purpose="Classify whether Self-RAKL improvement transfers to fresh protected assurance rather than only development tasks.",
        authority_boundary="The classifier never promotes its own challenger and same-context self-application is first-sign evidence only.",
    ),
    ChildOperatorOwnership(
        operator_id="ARCHIVE_SCALE_CONTEXT_EFFICIENCY",
        parent_surfaces=("memory", "prompting_context_policy", "benchmarking"),
        purpose="Measure mandatory recall, target coverage and active-token behavior as the external archive grows.",
        authority_boundary="Efficiency evidence cannot establish scientific correctness.",
    ),
    ChildOperatorOwnership(
        operator_id="MEASUREMENT_TRANSFORM_AND_UNCERTAINTY_EXECUTION",
        parent_surfaces=("mathematical_context_translation", "equivalence_similarity", "benchmarking"),
        purpose="Execute affine and first-order uncertainty transforms with explicit dimensional, PSD, differentiability and dependence assumptions.",
        authority_boundary="Metrology execution certifies the transform only; it cannot mint mechanism or target truth.",
    ),
    ChildOperatorOwnership(
        operator_id="RUNTIME_ARTIFACT_ENVIRONMENT_ATTESTATION",
        parent_surfaces=("software_architecture_execution", "authority_promotion", "benchmarking"),
        purpose="Bind observed executable bytes and declared environment fingerprints for reproducible execution identity.",
        authority_boundary="Artifact identity is reproducibility evidence and never scientific truth.",
    ),
    ChildOperatorOwnership(
        operator_id="CODING_AGENT_SKILL_ADAPTER",
        parent_surfaces=("software_architecture_execution", "prompting_context_policy", "routing"),
        purpose="Expose the canonical RAKL method to coding agents through thin recurring instructions and on-demand workflow loading.",
        authority_boundary="Agent packaging changes execution usability only and creates no scientific authority.",
    ),
)


def validate_child_operator_ownership() -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
    issues = tuple(
        (operator.operator_id, operator.validate())
        for operator in CHILD_OPERATORS
        if operator.validate()
    )
    return issues
