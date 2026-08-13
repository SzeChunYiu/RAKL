from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


class MechanicCause(str, Enum):
    SPECIFICATION_GAP = "SPECIFICATION_GAP"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    MAP_COVERAGE_GAP = "MAP_COVERAGE_GAP"
    REPRESENTATION_GAP = "REPRESENTATION_GAP"
    PORTAL_GAP = "PORTAL_GAP"
    DECOMPOSITION_GAP = "DECOMPOSITION_GAP"
    SCALE_GAP = "SCALE_GAP"
    METRIC_FALSEHOOD = "METRIC_FALSEHOOD"
    LOCAL_MINIMUM_OR_DYNAMICS_GAP = "LOCAL_MINIMUM_OR_DYNAMICS_GAP"
    METHOD_OPERATOR_GAP = "METHOD_OPERATOR_GAP"
    AUXILIARY_OBJECT_GAP = "AUXILIARY_OBJECT_GAP"
    EXPERIMENT_SELECTION_GAP = "EXPERIMENT_SELECTION_GAP"
    VERIFIER_GAP = "VERIFIER_GAP"
    COMPOSITION_INTERFACE_GAP = "COMPOSITION_INTERFACE_GAP"
    MEMORY_VIEW_GAP = "MEMORY_VIEW_GAP"
    MODEL_TOOL_FLOOR = "MODEL_TOOL_FLOOR"
    COMPUTE_ALLOCATION_GAP = "COMPUTE_ALLOCATION_GAP"
    STOPPING_GAP = "STOPPING_GAP"
    ONTOLOGY_GAP = "ONTOLOGY_GAP"
    COMPILATION_BARRIER = "COMPILATION_BARRIER"
    IMPLEMENTATION_DEFECT = "IMPLEMENTATION_DEFECT"
    NO_LOCAL_GEOMETRY_IN_SCOPE = "NO_LOCAL_GEOMETRY_IN_SCOPE"
    UNKNOWN = "UNKNOWN"


class MechanicDiagnosisVerdict(str, Enum):
    NO_GAP = "NO_GAP"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    DISCRIMINATOR_REQUIRED = "DISCRIMINATOR_REQUIRED"
    MECHANIC_GAP_IDENTIFIED = "MECHANIC_GAP_IDENTIFIED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MechanicDiagnosisReceipt:
    diagnosis_id: str
    problem_state_id: str
    atom_id: str
    fibre_snapshot_hash: str
    residual_ids: Tuple[str, ...]
    observed_signals: Tuple[str, ...]
    candidate_causes: Tuple[MechanicCause, ...]
    ruled_out_causes: Tuple[MechanicCause, ...] = ()
    discriminator_ids: Tuple[str, ...] = ()
    chosen_discriminator_id: str | None = None
    verdict: MechanicDiagnosisVerdict = MechanicDiagnosisVerdict.CANNOT_CHECK

    def __post_init__(self) -> None:
        if not self.diagnosis_id or not self.problem_state_id or not self.atom_id or not self.fibre_snapshot_hash:
            raise ValueError("diagnosis receipt requires diagnosis/problem/atom/fibre identity")
        if set(self.candidate_causes) & set(self.ruled_out_causes):
            raise ValueError("cause cannot be both candidate and ruled out")
        if self.chosen_discriminator_id and self.chosen_discriminator_id not in self.discriminator_ids:
            raise ValueError("chosen discriminator must be registered in discriminator_ids")
        if self.verdict is MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED and len(self.candidate_causes) != 1:
            raise ValueError("identified mechanic gap requires exactly one surviving cause")
        if (
            self.verdict is MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
            and MechanicCause.UNKNOWN in self.candidate_causes
        ):
            # Audit I3(a): UNKNOWN is the bottom of the information order, not
            # an element of the fault ontology; "the identified gap is UNKNOWN"
            # is a lattice confusion and must fail closed (use CANNOT_CHECK).
            raise ValueError("UNKNOWN is an epistemic bottom, not an identifiable mechanic cause")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


_SIGNAL_RULES: dict[str, tuple[MechanicCause, ...]] = {
    "formal_target_alignment_failed": (MechanicCause.SPECIFICATION_GAP,),
    "missing_measurement": (MechanicCause.EVIDENCE_GAP,),
    "unknown_map_edge": (MechanicCause.MAP_COVERAGE_GAP,),
    "coverage_incomplete": (MechanicCause.MAP_COVERAGE_GAP, MechanicCause.STOPPING_GAP),
    "representation_preservation_failed": (MechanicCause.REPRESENTATION_GAP,),
    "portal_roundtrip_failed": (MechanicCause.PORTAL_GAP,),
    "decomposition_interface_missing": (MechanicCause.DECOMPOSITION_GAP, MechanicCause.COMPOSITION_INTERFACE_GAP),
    "coarse_result_fine_counterexample": (MechanicCause.SCALE_GAP,),
    "local_metric_descends_root_stalls": (MechanicCause.METRIC_FALSEHOOD, MechanicCause.LOCAL_MINIMUM_OR_DYNAMICS_GAP),
    "target_unreachable_current_operator_basis": (MechanicCause.METHOD_OPERATOR_GAP,),
    "missing_helper_object": (MechanicCause.AUXILIARY_OBJECT_GAP,),
    "wrong_discriminator": (MechanicCause.EXPERIMENT_SELECTION_GAP,),
    "verifier_inconsistent_replay": (MechanicCause.VERIFIER_GAP, MechanicCause.IMPLEMENTATION_DEFECT),
    "verified_children_parent_glue_failed": (MechanicCause.COMPOSITION_INTERFACE_GAP,),
    "memory_view_omitted_required_history": (MechanicCause.MEMORY_VIEW_GAP,),
    "model_capability_floor": (MechanicCause.MODEL_TOOL_FLOOR,),
    "budget_spent_on_wrong_mechanic": (MechanicCause.COMPUTE_ALLOCATION_GAP,),
    "repeated_unclassified_residual": (MechanicCause.ONTOLOGY_GAP,),
    "compile_cost_dominates": (MechanicCause.COMPILATION_BARRIER,),
    "implementation_contract_failed": (MechanicCause.IMPLEMENTATION_DEFECT,),
}


def diagnose_mechanic_signals(*, diagnosis_id: str, problem_state_id: str, atom_id: str, fibre_snapshot_hash: str, residual_ids: Iterable[str], signals: Iterable[str], discriminator_ids: Iterable[str] = ()) -> MechanicDiagnosisReceipt:
    observed = tuple(dict.fromkeys(signals))
    causes: list[MechanicCause] = []
    for signal in observed:
        for cause in _SIGNAL_RULES.get(signal, (MechanicCause.UNKNOWN,)):
            if cause not in causes:
                causes.append(cause)
    if not observed:
        causes = [MechanicCause.UNKNOWN]
    discriminators = tuple(dict.fromkeys(discriminator_ids))
    if causes == [MechanicCause.UNKNOWN]:
        verdict = MechanicDiagnosisVerdict.CANNOT_CHECK
    elif len(causes) == 1:
        verdict = MechanicDiagnosisVerdict.MECHANIC_GAP_IDENTIFIED
    elif discriminators:
        verdict = MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED
    else:
        verdict = MechanicDiagnosisVerdict.PARTIALLY_IDENTIFIED
    return MechanicDiagnosisReceipt(diagnosis_id, problem_state_id, atom_id, fibre_snapshot_hash, tuple(residual_ids), observed, tuple(causes), discriminator_ids=discriminators, verdict=verdict)
