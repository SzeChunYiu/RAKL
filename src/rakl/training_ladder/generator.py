from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping, Sequence

from rakl.structural_types import StructuralObject

from .families import FAMILY_BUILDERS
from .types import ControlKind, FamilyId, GoldLabel, StructuralCoordinate


@dataclass(frozen=True)
class TrainingCase:
    """One generator instance with deterministic verifier gold.

    ``gold_label`` is assigned only by ``verify_case``; callers must not set it
    from perturbation identity or control kind.
    """

    case_id: str
    family_id: FamilyId
    structure: StructuralObject
    executable_payload: tuple[tuple[str, object], ...]
    surface_text: str
    surface_template_id: str
    coordinate_values: tuple[tuple[StructuralCoordinate, str], ...]
    control_kind: ControlKind
    twin_of_case_id: str | None
    gold_label: GoldLabel | None = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case requires identity")
        if not self.surface_text.strip():
            raise ValueError("case requires non-empty surface text")
        if not self.surface_template_id.strip():
            raise ValueError("case requires surface template identity")
        keys = [key for key, _ in self.coordinate_values]
        if len(keys) != len(set(keys)):
            raise ValueError("coordinate values must be unique per case")
        if self.family_id.value not in self.structure.domain and self.structure.domain not in {
            "synthetic_numeric",
            "synthetic_symbolic",
            "synthetic_graph",
        }:
            pass  # domain shell is intentionally independent of family id

    @property
    def coordinate_map(self) -> Mapping[StructuralCoordinate, str]:
        return dict(self.coordinate_values)

    @property
    def content_hash(self) -> str:
        payload = repr(
            (
                "RAKL_TRAINING_CASE_V1",
                self.case_id,
                self.family_id.value,
                self.structure.structure_id,
                self.executable_payload,
                self.surface_text,
                self.surface_template_id,
                self.coordinate_values,
                self.control_kind.value,
                self.twin_of_case_id,
            )
        ).encode("utf-8")
        return sha256(payload).hexdigest()


STRUCTURAL_FAMILIES: tuple[FamilyId, ...] = tuple(FamilyId)


def _coords(**values: str) -> tuple[tuple[StructuralCoordinate, str], ...]:
    order = (
        StructuralCoordinate.PRINCIPLE,
        StructuralCoordinate.COMPOSITION,
        StructuralCoordinate.BOUNDARY,
        StructuralCoordinate.REPRESENTATION,
        StructuralCoordinate.DOMAIN_SHELL,
        StructuralCoordinate.SURFACE_DETAIL,
    )
    return tuple((axis, values[axis.value]) for axis in order)


def _render_surface(template_id: str, tokens: Sequence[str]) -> str:
    """Render surface text from opaque tokens — no family or validity leakage."""

    body = " | ".join(tokens)
    return f"[{template_id}] {body}"


def _sequence_cases(seed_offset: int) -> tuple[TrainingCase, ...]:
    family = FamilyId.SEQUENCE_COMPOSITION
    builder = FAMILY_BUILDERS[family]
    cases: list[TrainingCase] = []

    valid_ops = (("add", 3), ("mul", 2))
    invalid_ops = (("mul", 2), ("add", 3))  # non-commutative under this semantics

    for idx, (ops, suffix) in enumerate(((valid_ops, "a"), (invalid_ops, "b"))):
        start = 5 + seed_offset
        structure = builder(
            f"seq-{seed_offset}-{idx}",
            domain="synthetic_numeric",
            composition_tag=f"c{seed_offset}",
            boundary_regime="closed",
            representation="infix",
        )
        payload = (
            ("family", family.value),
            ("start", start),
            ("ops", ops),
            ("expected_semantics", "left_associative"),
        )
        surface = _render_surface(
            f"TPL-OPS-{seed_offset % 7}",
            (str(start), *(f"{op}:{val}" for op, val in ops)),
        )
        cases.append(
            TrainingCase(
                case_id=f"seq-{seed_offset}-{suffix}",
                family_id=family,
                structure=structure,
                executable_payload=payload,
                surface_text=surface,
                surface_template_id=f"TPL-OPS-{seed_offset % 7}",
                coordinate_values=_coords(
                    PRINCIPLE="ordered_ops",
                    COMPOSITION=f"chain_{seed_offset}",
                    BOUNDARY="closed",
                    REPRESENTATION="infix",
                    DOMAIN_SHELL="synthetic_numeric",
                    SURFACE_DETAIL=f"seed_{seed_offset}",
                ),
                control_kind=ControlKind.NORMAL,
                twin_of_case_id=None,
            )
        )
    return tuple(cases)


def _balance_cases(seed_offset: int) -> tuple[TrainingCase, ...]:
    family = FamilyId.BALANCE_CONSERVATION
    builder = FAMILY_BUILDERS[family]
    cases: list[TrainingCase] = []

    specs = (((10, 4, 6), "a"), ((10, 4, 5), "b"))
    for idx, ((inflow, outflow, store), suffix) in enumerate(specs):
        structure = builder(
            f"bal-{seed_offset}-{idx}",
            domain="synthetic_symbolic",
            composition_tag=f"net_{seed_offset}",
            boundary_regime="isolated",
            representation="tabular",
        )
        payload = (
            ("family", family.value),
            ("inflow", inflow),
            ("outflow", outflow),
            ("store", store),
        )
        surface = _render_surface(
            f"TPL-FLOW-{seed_offset % 5}",
            (f"in={inflow}", f"out={outflow}", f"store={store}"),
        )
        cases.append(
            TrainingCase(
                case_id=f"bal-{seed_offset}-{suffix}",
                family_id=family,
                structure=structure,
                executable_payload=payload,
                surface_text=surface,
                surface_template_id=f"TPL-FLOW-{seed_offset % 5}",
                coordinate_values=_coords(
                    PRINCIPLE="conservation",
                    COMPOSITION=f"net_{seed_offset}",
                    BOUNDARY="isolated",
                    REPRESENTATION="tabular",
                    DOMAIN_SHELL="synthetic_symbolic",
                    SURFACE_DETAIL=f"seed_{seed_offset}",
                ),
                control_kind=ControlKind.NORMAL,
                twin_of_case_id=None,
            )
        )
    return tuple(cases)


def _reachability_cases(seed_offset: int) -> tuple[TrainingCase, ...]:
    family = FamilyId.STATE_REACHABILITY
    builder = FAMILY_BUILDERS[family]
    cases: list[TrainingCase] = []

    specs = (
        (("A", "B", "C"), (("A", "B"), ("B", "C")), "C", "a"),
        (("A", "B", "C"), (("A", "B"),), "C", "b"),
    )
    for idx, (states, edges, target, suffix) in enumerate(specs):
        structure = builder(
            f"fsm-{seed_offset}-{idx}",
            domain="synthetic_graph",
            composition_tag=f"path_{seed_offset}",
            boundary_regime="deterministic",
            representation="edge_list",
        )
        payload = (
            ("family", family.value),
            ("states", states),
            ("edges", edges),
            ("start", states[0]),
            ("target", target),
        )
        surface = _render_surface(
            f"TPL-GRAPH-{seed_offset % 3}",
            (f"start={states[0]}", f"target={target}", f"edges={len(edges)}"),
        )
        cases.append(
            TrainingCase(
                case_id=f"fsm-{seed_offset}-{suffix}",
                family_id=family,
                structure=structure,
                executable_payload=payload,
                surface_text=surface,
                surface_template_id=f"TPL-GRAPH-{seed_offset % 3}",
                coordinate_values=_coords(
                    PRINCIPLE="reachability",
                    COMPOSITION=f"path_{seed_offset}",
                    BOUNDARY="deterministic",
                    REPRESENTATION="edge_list",
                    DOMAIN_SHELL="synthetic_graph",
                    SURFACE_DETAIL=f"seed_{seed_offset}",
                ),
                control_kind=ControlKind.NORMAL,
                twin_of_case_id=None,
            )
        )
    return tuple(cases)


_FAMILY_GENERATORS = {
    FamilyId.SEQUENCE_COMPOSITION: _sequence_cases,
    FamilyId.BALANCE_CONSERVATION: _balance_cases,
    FamilyId.STATE_REACHABILITY: _reachability_cases,
}


def generate_family_cases(family_id: FamilyId, *, seed_offset: int = 0) -> tuple[TrainingCase, ...]:
    if family_id not in _FAMILY_GENERATORS:
        raise ValueError(f"unknown family: {family_id}")
    return _FAMILY_GENERATORS[family_id](seed_offset)


def build_known_structure_catalog(*, seed_offsets: Sequence[int] | None = None) -> tuple[TrainingCase, ...]:
    offsets = tuple(seed_offsets or range(3))
    cases: list[TrainingCase] = []
    for family in STRUCTURAL_FAMILIES:
        for offset in offsets:
            cases.extend(generate_family_cases(family, seed_offset=offset))
    return tuple(cases)
