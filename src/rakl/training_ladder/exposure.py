from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Sequence

from rakl.training_projection import MasteryCoordinate


class ExposureProbeKind(str, Enum):
    SAME_STRUCTURE = "SAME_STRUCTURE"
    NEW_COMPOSITION = "NEW_COMPOSITION"
    NEW_BOUNDARY = "NEW_BOUNDARY"
    NEW_REPRESENTATION = "NEW_REPRESENTATION"
    NEW_DOMAIN = "NEW_DOMAIN"
    HOSTILE_NEAR_MISS = "HOSTILE_NEAR_MISS"


REGISTERED_EXPOSURE_COUNTS: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)

MASTERY_COORDINATES: tuple[MasteryCoordinate, ...] = tuple(MasteryCoordinate)

COMPARATOR_PROXY_KINDS: tuple[str, ...] = (
    "loss_perplexity",
    "gradient_norm",
    "influence_probe",
    "structural_mastery_coordinates",
)


@dataclass(frozen=True)
class ExposureScheduleEntry:
    exposure_count: int
    probe_kind: ExposureProbeKind
    family_id: str
    structure_id: str
    case_id: str

    def __post_init__(self) -> None:
        if self.exposure_count not in REGISTERED_EXPOSURE_COUNTS:
            raise ValueError("exposure count must be registered")


@dataclass(frozen=True)
class ExposureCurveHarness:
    harness_id: str
    schedule: tuple[ExposureScheduleEntry, ...]
    exposure_counts: tuple[int, ...]
    mastery_coordinates: tuple[MasteryCoordinate, ...]
    comparator_proxies: tuple[str, ...]
    frozen_before_outcomes: bool
    harness_hash: str

    @property
    def grants_efficacy_claim(self) -> bool:
        return False

    @property
    def learner_outcomes_accessed(self) -> bool:
        return False


def _harness_hash(
    harness_id: str,
    schedule: Sequence[ExposureScheduleEntry],
    exposure_counts: Sequence[int],
    mastery_coordinates: Sequence[MasteryCoordinate],
    comparator_proxies: Sequence[str],
    frozen_before_outcomes: bool,
) -> str:
    payload = repr(
        (
            "RAKL_EXPOSURE_HARNESS_V1",
            harness_id,
            tuple(schedule),
            tuple(exposure_counts),
            tuple(mastery_coordinates),
            tuple(comparator_proxies),
            frozen_before_outcomes,
        )
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def build_exposure_curve_harness(
    *,
    harness_id: str,
    case_ids_by_probe: dict[ExposureProbeKind, Sequence[str]],
    frozen_before_outcomes: bool = True,
) -> ExposureCurveHarness:
    if not harness_id.strip():
        raise ValueError("harness requires identity")
    schedule: list[ExposureScheduleEntry] = []
    for probe_kind, case_ids in case_ids_by_probe.items():
        for exposure_count in REGISTERED_EXPOSURE_COUNTS:
            for case_id in case_ids:
                parts = case_id.split("-", 1)
                family_id = parts[0] if parts else "unknown"
                schedule.append(
                    ExposureScheduleEntry(
                        exposure_count=exposure_count,
                        probe_kind=probe_kind,
                        family_id=family_id,
                        structure_id=case_id,
                        case_id=case_id,
                    )
                )
    schedule_tuple = tuple(schedule)
    harness_hash = _harness_hash(
        harness_id,
        schedule_tuple,
        REGISTERED_EXPOSURE_COUNTS,
        MASTERY_COORDINATES,
        COMPARATOR_PROXY_KINDS,
        frozen_before_outcomes,
    )
    return ExposureCurveHarness(
        harness_id=harness_id,
        schedule=schedule_tuple,
        exposure_counts=REGISTERED_EXPOSURE_COUNTS,
        mastery_coordinates=MASTERY_COORDINATES,
        comparator_proxies=COMPARATOR_PROXY_KINDS,
        frozen_before_outcomes=frozen_before_outcomes,
        harness_hash=harness_hash,
    )
