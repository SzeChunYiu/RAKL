"""Training-time RAKL Phase 0/1 scaffold (#461)."""

from .controls import build_hostile_control_suite
from .exposure import ExposureCurveHarness, ExposureProbeKind, build_exposure_curve_harness
from .generator import (
    STRUCTURAL_FAMILIES,
    TrainingCase,
    build_known_structure_catalog,
    generate_family_cases,
)
from .protocol import (
    build_protocol_freeze_packet,
    build_protocol_freeze_receipt,
    validate_protocol_freeze,
)
from .types import ControlKind, FamilyId, GoldLabel, StructuralCoordinate
from .verifier import verify_case

__all__ = [
    "ControlKind",
    "ExposureCurveHarness",
    "ExposureProbeKind",
    "FamilyId",
    "GoldLabel",
    "STRUCTURAL_FAMILIES",
    "StructuralCoordinate",
    "TrainingCase",
    "build_exposure_curve_harness",
    "build_hostile_control_suite",
    "build_known_structure_catalog",
    "build_protocol_freeze_packet",
    "build_protocol_freeze_receipt",
    "generate_family_cases",
    "validate_protocol_freeze",
    "verify_case",
]
