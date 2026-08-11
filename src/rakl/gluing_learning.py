from __future__ import annotations

from typing import Tuple

from .experience_substrate import EpisodeOutcome
from .problem_fibre import GluingReport


def gluing_residual_signature(report: GluingReport) -> Tuple[str, ...]:
    """Encode a failed/incomplete local-to-global assembly as a typed residual."""

    residuals: list[str] = []
    if not report.complete_coverage:
        residuals.append("gluing:incomplete_atom_coverage")
    if not report.all_sections_verified:
        residuals.append("gluing:unverified_local_section")
    for obstruction in report.obstructions:
        residuals.append(
            "gluing:interface_conflict:"
            + obstruction.key
            + ":"
            + obstruction.left_atom_id
            + ":"
            + obstruction.right_atom_id
        )
    return tuple(dict.fromkeys(residuals))


def gluing_episode_outcome(report: GluingReport) -> EpisodeOutcome:
    """Map gluing status to an experience outcome without granting extra authority."""

    if report.grants_solution_authority:
        return EpisodeOutcome.SUCCESS
    if report.compatible:
        return EpisodeOutcome.PARTIAL_SUCCESS
    return EpisodeOutcome.FAILURE
