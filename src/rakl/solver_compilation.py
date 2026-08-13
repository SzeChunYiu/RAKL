from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import inf
from typing import Tuple


class TransformationEffect(str, Enum):
    PRECONDITION = "PRECONDITION"
    CHANGE_METRIC = "CHANGE_METRIC"
    CONTINUATION = "CONTINUATION"
    PARAMETER_HOMOTOPY = "PARAMETER_HOMOTOPY"
    # Compatibility alias. New theory reserves bare path homotopy for
    # equivalence of transformation histories/higher cells.
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


# Declared incompatibility relation on transformation effects (audit I4):
# ``claimed_effects`` is otherwise a word in the free monoid over
# TransformationEffect, so mutually contradictory claims (a sound relaxation
# that is simultaneously a sound tightening of the same problem) would
# validate. Symmetric; minimal by design — extend only with pairs that are
# contradictory as simultaneous claims about ONE compilation step.
EFFECT_CONFLICTS: frozenset[frozenset[TransformationEffect]] = frozenset(
    {
        frozenset({TransformationEffect.RELAX, TransformationEffect.TIGHTEN}),
    }
)


def conflicting_claimed_effects(
    effects: Tuple[TransformationEffect, ...],
) -> tuple[frozenset[TransformationEffect], ...]:
    """Return the declared conflict pairs jointly present in ``effects``."""
    present = frozenset(effects)
    return tuple(sorted((pair for pair in EFFECT_CONFLICTS if pair <= present), key=lambda p: sorted(e.value for e in p)))


@dataclass(frozen=True)
class PreservationValidationReceipt:
    """Bound validation of a representation/transform preservation claim.

    ``target_problem_hash`` (optional, additive) names the transformed
    problem this step produces. It is the interface hash that makes receipts
    COMPOSABLE (audit I4): ``compose_preservation_receipts`` derives a
    composite receipt only when each step's certified output interface equals
    the next step's input. Receipts without it cannot participate in a
    composite (fail closed).
    """

    report_id: str
    source_problem_hash: str
    specification_hash: str
    root_qoi: str
    representation_id: str
    transform_id: str
    verifier_id: str
    passed: bool
    target_problem_hash: str | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.report_id,
                self.source_problem_hash,
                self.specification_hash,
                self.root_qoi,
                self.representation_id,
                self.transform_id,
                self.verifier_id,
            )
        ):
            raise ValueError("preservation validation receipt requires bound subject and verifier identities")

    def matches(
        self,
        *,
        source_problem_hash: str,
        specification_hash: str,
        root_qoi: str,
        representation_id: str,
        transform_id: str,
    ) -> bool:
        return (
            self.source_problem_hash == source_problem_hash
            and self.specification_hash == specification_hash
            and self.root_qoi == root_qoi
            and self.representation_id == representation_id
            and self.transform_id == transform_id
        )

    @property
    def grants_target_authority(self) -> bool:
        return False


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
    preservation_receipt: PreservationValidationReceipt | None = None
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
        conflicts = conflicting_claimed_effects(self.claimed_effects)
        if conflicts:
            rendered = "; ".join(",".join(sorted(e.value for e in pair)) for pair in conflicts)
            raise ValueError(
                f"claimed_effects contain declared conflicting effect pairs (audit I4): {rendered}"
            )
        if min(self.build_cost, self.execution_cost, self.decode_cost, self.verification_cost) < 0:
            raise ValueError("compilation costs must be nonnegative")
        if self.expected_reuse is not None and self.expected_reuse < 0:
            raise ValueError("expected_reuse must be nonnegative")
        if self.invalidation_hazard_per_use is not None and not 0 <= self.invalidation_hazard_per_use <= 1:
            raise ValueError("invalidation hazard must be in [0,1]")
        if self.status is CompilationStatus.VALIDATED_FOR_ROUTING:
            if self.preservation_receipt is None:
                raise ValueError("routing-validated compilation requires bound preservation receipt")
            if not self.preservation_receipt.passed:
                raise ValueError("routing-validated compilation requires passing preservation receipt")
            if not self.preservation_receipt.matches(
                source_problem_hash=self.source_problem_hash,
                specification_hash=self.specification_hash,
                root_qoi=self.root_qoi,
                representation_id=self.representation_id,
                transform_id=self.transform_id,
            ):
                raise ValueError("preservation receipt subject does not match compilation candidate")

    @property
    def preservation_report_id(self) -> str | None:
        return None if self.preservation_receipt is None else self.preservation_receipt.report_id

    @property
    def one_shot_cost(self) -> float:
        # Explicit additive resource-accounting projection only. It is not the
        # general mathematical path-cost algebra used by VTG.
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


@dataclass(frozen=True)
class CompositePreservationReceipt:
    """Derived receipt for a COMPOSED transform chain (audit I4).

    Validated-ness must be closed under composition to license pipelines:
    a composite receipt exists exactly when every component receipt passed
    and each step's certified output interface (``target_problem_hash``)
    equals the next step's input (``source_problem_hash``), with one shared
    root QoI. This is the subcategory law: components are the morphism data,
    the composite is derived, never self-declared. Fail-closed: legacy
    receipts without ``target_problem_hash`` cannot compose.
    """

    composite_id: str
    components: Tuple[PreservationValidationReceipt, ...]

    def __post_init__(self) -> None:
        if not self.composite_id:
            raise ValueError("composite preservation receipt requires an identity")
        if len(self.components) < 2:
            raise ValueError("composite preservation receipt requires at least two component receipts")
        root_qoi = self.components[0].root_qoi
        for receipt in self.components:
            if not receipt.passed:
                raise ValueError(
                    f"component receipt {receipt.report_id!r} did not pass; a composite is not derivable (audit I4)"
                )
            if receipt.root_qoi != root_qoi:
                raise ValueError("composite preservation receipt requires one shared root QoI")
        for first, second in zip(self.components, self.components[1:]):
            if first.target_problem_hash is None:
                raise ValueError(
                    f"component receipt {first.report_id!r} declares no target_problem_hash; "
                    "its output interface is unnamed and cannot compose (audit I4)"
                )
            if first.target_problem_hash != second.source_problem_hash:
                raise ValueError(
                    "interface hash mismatch in composite preservation receipt: "
                    f"{first.report_id!r} certifies output {first.target_problem_hash!r} but "
                    f"{second.report_id!r} validates input {second.source_problem_hash!r} (audit I4)"
                )

    @property
    def source_problem_hash(self) -> str:
        return self.components[0].source_problem_hash

    @property
    def target_problem_hash(self) -> str | None:
        return self.components[-1].target_problem_hash

    @property
    def root_qoi(self) -> str:
        return self.components[0].root_qoi

    @property
    def transform_chain(self) -> Tuple[str, ...]:
        return tuple(receipt.transform_id for receipt in self.components)

    @property
    def passed(self) -> bool:
        # Derivable only from all-passing components (enforced in __post_init__).
        return True

    @property
    def grants_target_authority(self) -> bool:
        return False


def compose_preservation_receipts(
    first: PreservationValidationReceipt | CompositePreservationReceipt,
    second: PreservationValidationReceipt | CompositePreservationReceipt,
    *,
    composite_id: str,
) -> CompositePreservationReceipt:
    """Compose two (possibly already composite) preservation receipts (audit I4)."""
    left = first.components if isinstance(first, CompositePreservationReceipt) else (first,)
    right = second.components if isinstance(second, CompositePreservationReceipt) else (second,)
    return CompositePreservationReceipt(composite_id, left + right)


def compilation_break_even_uses(candidate: SolverCompilationCandidate, *, baseline_per_use_cost: float) -> float:
    """Renewal-reward break-even consistent with the candidate's own hazard model (audit U6).

    Uses the candidate's declared ``invalidation_hazard_per_use`` (0 when
    undeclared): long-run per-use advantage is
    ``baseline - (execution + decode + verification) - hazard * build``, i.e.
    ``baseline - stability_adjusted_per_use_cost``. When the advantage is not
    positive the compilation never amortizes.
    """
    if baseline_per_use_cost < 0:
        raise ValueError("baseline cost must be nonnegative")
    per_use = candidate.execution_cost + candidate.decode_cost + candidate.verification_cost
    hazard = 0.0 if candidate.invalidation_hazard_per_use is None else candidate.invalidation_hazard_per_use
    advantage = baseline_per_use_cost - per_use - hazard * candidate.build_cost
    if advantage <= 0:
        return inf
    return candidate.build_cost / advantage
