"""Operational correlation projection for ORION.

OpenTelemetry-style operational telemetry is intentionally separate from RAKL
``MetricReceipt`` authority.  Correlation attributes may point to epistemic receipts;
they cannot substitute for them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class OperationalCorrelationContext:
    project_id: str
    snapshot_id: str
    workflow_id: str
    activity_id: str = ""
    invocation_id: str = ""
    research_round_id: str = ""
    episode_id: str = ""
    target_id: str = ""
    fiber_id: str = ""
    evaluation_epoch_id: str = ""
    controller_decision_id: str = ""

    def __post_init__(self) -> None:
        for name in ("project_id", "snapshot_id", "workflow_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")

    def attributes(self) -> Mapping[str, str]:
        values = {
            "orion.project.id": self.project_id,
            "orion.snapshot.id": self.snapshot_id,
            "orion.workflow.id": self.workflow_id,
            "orion.activity.id": self.activity_id,
            "orion.invocation.id": self.invocation_id,
            "orion.research_round.id": self.research_round_id,
            "orion.episode.id": self.episode_id,
            "orion.target.id": self.target_id,
            "orion.fiber.id": self.fiber_id,
            "orion.evaluation_epoch.id": self.evaluation_epoch_id,
            "orion.controller_decision.id": self.controller_decision_id,
        }
        return {key: value for key, value in values.items() if value}

    @property
    def grants_scientific_authority(self) -> bool:
        return False
