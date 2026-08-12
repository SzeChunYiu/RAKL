from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from rakl.structural_types import StructuralObject

from .families import FAMILY_BUILDERS
from .generator import TrainingCase, build_known_structure_catalog
from .types import ControlKind, FamilyId, StructuralCoordinate
from .verifier import verify_case


@dataclass(frozen=True)
class HostileControlSuite:
    template_leak_probes: tuple[TrainingCase, ...]
    coordinate_ablated_twins: tuple[TrainingCase, ...]
    semantic_near_decoys: tuple[TrainingCase, ...]

    @property
    def all_cases(self) -> tuple[TrainingCase, ...]:
        return self.template_leak_probes + self.coordinate_ablated_twins + self.semantic_near_decoys


def _ablated_structure(base: StructuralObject, ablated: StructuralCoordinate) -> StructuralObject:
    kept = tuple(b for b in base.boundaries if b.key != ablated.value.lower())
    if len(kept) == len(base.boundaries):
        kept = base.boundaries[:-1]
    return StructuralObject(
        structure_id=f"{base.structure_id}-abl-{ablated.value.lower()}",
        domain=base.domain,
        qoi=base.qoi,
        context_id=base.context_id,
        roles=base.roles,
        relations=base.relations,
        invariants=base.invariants,
        boundaries=kept,
        evidence_ids=base.evidence_ids + (f"ablation:{ablated.value}",),
    )


def _build_semantic_near_decoy(base: TrainingCase) -> TrainingCase:
    family = base.family_id
    payload = dict(base.executable_payload)
    if family == FamilyId.SEQUENCE_COMPOSITION:
        payload["ops"] = (("add", 3), ("add", 3))
    elif family == FamilyId.BALANCE_CONSERVATION:
        payload["store"] = int(payload["store"]) + 1
    elif family == FamilyId.STATE_REACHABILITY:
        payload["edges"] = tuple(payload["edges"])[:-1]
    builder = FAMILY_BUILDERS[family]
    decoy_structure = builder(
        f"{base.structure.structure_id}-decoy",
        domain=base.structure.domain,
        composition_tag="decoy",
        boundary_regime="open",
        representation=base.coordinate_map[StructuralCoordinate.REPRESENTATION],
    )
    return TrainingCase(
        case_id=f"{base.case_id}-decoy",
        family_id=family,
        structure=decoy_structure,
        executable_payload=tuple(sorted(payload.items())),
        surface_text=base.surface_text,
        surface_template_id=base.surface_template_id,
        coordinate_values=base.coordinate_values,
        control_kind=ControlKind.SEMANTIC_NEAR_DECOY,
        twin_of_case_id=base.case_id,
    )


def build_hostile_control_suite(*, seed_offset: int = 0) -> HostileControlSuite:
    base_cases = build_known_structure_catalog(seed_offsets=(seed_offset,))
    template_probes: list[TrainingCase] = []
    ablation_twins: list[TrainingCase] = []
    decoys: list[TrainingCase] = []

    for family in (FamilyId.SEQUENCE_COMPOSITION, FamilyId.BALANCE_CONSERVATION, FamilyId.STATE_REACHABILITY):
        family_cases = [c for c in base_cases if c.family_id == family]
        if len(family_cases) < 2:
            continue
        valid_case = verify_case(family_cases[0])
        invalid_case = verify_case(family_cases[1])
        shared_template = f"TPL-LEAK-{family.value[:4]}"
        shared_surface = valid_case.surface_text.rsplit("]", 1)[-1].strip()
        for idx, case in enumerate((valid_case, invalid_case)):
            template_probes.append(
                verify_case(
                    TrainingCase(
                        case_id=f"leak-{family.value}-{idx}",
                        family_id=case.family_id,
                        structure=case.structure,
                        executable_payload=case.executable_payload,
                        surface_text=f"[{shared_template}] {shared_surface}",
                        surface_template_id=shared_template,
                        coordinate_values=case.coordinate_values,
                        control_kind=ControlKind.TEMPLATE_LEAK_PROBE,
                        twin_of_case_id=case.case_id,
                    )
                )
            )

        anchor = verify_case(family_cases[0])
        ablated = _ablated_structure(anchor.structure, StructuralCoordinate.COMPOSITION)
        ablation_twins.append(
            verify_case(
                TrainingCase(
                    case_id=f"abl-{family.value}",
                    family_id=anchor.family_id,
                    structure=ablated,
                    executable_payload=anchor.executable_payload,
                    surface_text=anchor.surface_text,
                    surface_template_id=anchor.surface_template_id,
                    coordinate_values=anchor.coordinate_values,
                    control_kind=ControlKind.COORDINATE_ABLATED_TWIN,
                    twin_of_case_id=anchor.case_id,
                )
            )
        )
        decoys.append(verify_case(_build_semantic_near_decoy(anchor)))

    return HostileControlSuite(
        template_leak_probes=tuple(template_probes),
        coordinate_ablated_twins=tuple(ablation_twins),
        semantic_near_decoys=tuple(decoys),
    )


def hostile_suite_digest(suite: HostileControlSuite) -> str:
    rows = tuple(sorted(case.content_hash for case in suite.all_cases))
    return sha256(repr(("RAKL_TRAINING_HOSTILE_SUITE_V1", rows)).encode("utf-8")).hexdigest()
