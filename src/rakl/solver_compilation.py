from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf
from typing import Tuple


class TransformationEffect(str, Enum):
    PRECONDITION = "PRECONDITION"
    CHANGE_METRIC = "CHANGE_METRIC"
    CONTINUATION = "CONTINUATION"
    HOMOTOPY = "HOMOTOPY"
    LIFT = "LIFT"
    AUGMENT_STATE = "AUGMENT_STATE"
    ELIMINATE = "ELIMINATE"
    MARGINALIZE = "MARGINALIZE"
    QUOTIENT = "QUOTIENT"
    FACTORIZE = "FACTORIZE"
    DUALIZE = "DUALIZE"
    RELAX = "RELAX"
    TIGHTEN = "TIGHTEN"
    CONVEXIFY = "CONVEXIFY"
    LOCALIZE = "LOCALIZE"
    DECOUPLE = "DECOUPLE"
    SEPARATE_SCALES = "SEPARATE_SCALES"
    EXPOSE_SYMMETRY = "EXPOSE_SYMMETRY"
    EXPOSE_INVARIANT = "EXPOSE_INVARIANT"
    EXPOSE_CAUSAL_ORDER = "EXPOSE_CAUSAL_ORDER"
    MAKE_INTERFACE_EXPLICIT = "MAKE_INTERFACE_EXPLICIT"
    COMPILE_TO_FORMAL_PROVER = "COMPILE_TO_FORMAL_PROVER"
    COMPILE_TO_SAT_SMT = "COMPILE_TO_SAT_SMT"
    COMPILE_TO_OPTIMIZER = "COMPILE_TO_OPTIMIZER"
    COMPILE_TO_LINEAR_ALGEBRA = "COMPILE_TO_LINEAR_ALGEBRA"
    COMPILE_TO_DYNAMIC_PROGRAM = "COMPILE_TO_DYNAMIC_PROGRAM"
    COMPILE_TO_FIELD = "COMPILE_TO_FIELD"
    COMPILE_TO_SIMULATOR = "COMPILE_TO_SIMULATOR"


class CompilationStatus(str, Enum):
    PROPOSAL_ONLY = "PROPOSAL_ONLY"
    VALIDATED_FOR_ROUTING = "VALIDATED_FOR_ROUTING"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SolverCompilationCandidate:
    compilation_id: str
    source_problem_hash: str
    specification_hash: str
    root_qoi: str
    representation_id: str
    transform_id: str
    solver_id: str
    decoder_id: str | None
    verifier_id: str
    claimed_effects: Tuple[TransformationEffect, ...]
    preservation_report_id: str | None = None
    build_cost: float = 0.0
    execution_cost: float = 0.0
    decode_cost: float = 0.0
    verification_cost: float = 0.0
    expected_reuse: float | None = None
    invalidation_hazard_per_use: float | None = None
    status: CompilationStatus = CompilationStatus.PROPOSAL_ONLY

    def __post_init__(self) -> None:
        if not all((self.compilation_id, self.source_problem_hash, self.specification_hash, self.root_qoi, self.representation_id, self.transform_id, self.solver_id, self.verifier_id)):
            raise ValueError("solver compilation candidate requires bound identities")
        if not self.claimed_effects:
            raise ValueError("solver compilation candidate requires claimed transformation effects")
        if min(self.build_cost, self.execution_cost, self.decode_cost, self.verification_cost) < 0:
            raise ValueError("compilation costs must be nonnegative")
        if self.expected_reuse is not None and self.expected_reuse < 0:
            raise ValueError("expected_reuse must be nonnegative")
        if self.invalidation_hazard_per_use is not None and not 0 <= self.invalidation_hazard_per_use <= 1:
            raise ValueError("invalidation hazard must be in [0,1]")
        if self.status is CompilationStatus.VALIDATED_FOR_ROUTING and not self.preservation_report_id:
            raise ValueError("routing-validated compilation requires preservation report")

    @property
    def one_shot_cost(self) -> float:
        return self.build_cost + self.execution_cost + self.decode_cost + self.verification_cost

    def amortized_per_use_cost(self, uses: int) -> float:
        if uses < 1:
            raise ValueError("uses must be positive")
        return self.build_cost / uses + self.execution_cost + self.decode_cost + self.verification_cost

    @property
    def stability_adjusted_per_use_cost(self) -> float | None:
        if self.invalidation_hazard_per_use is None:
            return None
        return self.execution_cost + self.decode_cost + self.verification_cost + self.invalidation_hazard_per_use * self.build_cost

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def compilation_break_even_uses(candidate: SolverCompilationCandidate, *, baseline_per_use_cost: float) -> float:
    if baseline_per_use_cost < 0:
        raise ValueError("baseline cost must be nonnegative")
    per_use = candidate.execution_cost + candidate.decode_cost + candidate.verification_cost
    advantage = baseline_per_use_cost - per_use
    if advantage <= 0:
        return inf
    return candidate.build_cost / advantage
