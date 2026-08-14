"""Oracle-ceiling admissibility gate for equal-budget allocation-comparison instruments.

Implements the sealed revival packet
``research/paper4_allocator_attribution_v1/PACKET_oracle_ceiling_calibration_gate_v1.json``
(sha256 ``d318363d…``): before an equal-budget allocation comparison is executed,
compute bounds on the best advantage ANY allocation policy could achieve over the
reference parent under the identical budget, and require

    achievable ceiling >= kappa * registered_minimum_detectable_effect

with ``kappa`` and the MDE frozen before any ceiling value is seen.

Direction of every bound is load-bearing:

- a POLICY score (greedy oracle, local search) is a LOWER bound on the ceiling.
  It may license ``ADMISSIBLE`` — achievability demonstrated constructively —
  but it may NEVER license ``INADMISSIBLE``;
- only a rigorous UPPER bound (e.g. a monotone relaxation solved exactly) may
  license ``INADMISSIBLE``;
- when the instrument's generative parameters are unknown the oracle is not
  computable and the gate fails closed to ``CANNOT_CHECK`` — never ``ADMISSIBLE``.

The gate decides only whether a comparison is worth executing.  It grants no
scientific authority, promotes nothing, and never revives or reverses an
allocator terminal.  An ``INADMISSIBLE`` verdict may never be upgraded by
access to arm outcomes.

Motivating observation (preserved, not re-litigated): the Paper IV model-free
development-stress instrument carries bootstrap CIs ~0.0016 wide on its primary
contrast — amply powered by conventional power analysis — while a rigorous
upper bound on any equal-budget policy's advantage over the static parent is
+0.02457 against the instrument's own frozen 0.05 gate.  Power analysis bounds
sampling noise for an assumed effect; it is silent on whether the instrument
can generate the effect at all.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Mapping, Tuple


class BoundKind(str, Enum):
    #: A policy score or constructive allocation: the ceiling is at least this.
    LOWER_BOUND = "LOWER_BOUND"
    #: A rigorous relaxation optimum: the ceiling is at most this.
    UPPER_BOUND = "UPPER_BOUND"
    #: An exactly computed optimum: both a lower and an upper bound.
    EXACT = "EXACT"


class OracleComputability(str, Enum):
    COMPUTABLE = "COMPUTABLE"
    UNCOMPUTABLE = "UNCOMPUTABLE"
    UNKNOWN = "UNKNOWN"


class AdmissibilityVerdict(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    INADMISSIBLE = "INADMISSIBLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class CeilingBound:
    """One bound on the instrument's achievable mean advantage over the reference parent."""

    bound_id: str
    kind: BoundKind
    value: float
    method: str
    per_world: Mapping[str, float] | None = None
    bootstrap_ci: Tuple[float, float] | None = None


@dataclass(frozen=True)
class FrozenAdmissibilityDeclaration:
    """The pre-ceiling freeze: instrument identity, metric, MDE and kappa.

    Constructing this object is the freeze act.  Validation happens here —
    before any ceiling evidence exists in scope — so a nonsensical declaration
    fails at freeze time rather than surviving into a verdict.
    """

    instrument_id: str
    registered_primary_metric: str
    registered_minimum_detectable_effect: float
    frozen_kappa: float
    declared_on: str
    rationale: str

    def __post_init__(self) -> None:
        if not self.instrument_id:
            raise ValueError("instrument_id must be non-empty")
        if not self.registered_primary_metric:
            raise ValueError("registered_primary_metric must be non-empty")
        mde = self.registered_minimum_detectable_effect
        if not (isinstance(mde, (int, float)) and isfinite(mde) and mde > 0.0):
            raise ValueError("registered_minimum_detectable_effect must be finite and positive")
        kappa = self.frozen_kappa
        if not (isinstance(kappa, (int, float)) and isfinite(kappa) and kappa > 0.0):
            raise ValueError("frozen_kappa must be finite and positive")

    @property
    def admissibility_threshold(self) -> float:
        return self.frozen_kappa * self.registered_minimum_detectable_effect

    @property
    def content_sha256(self) -> str:
        payload = {
            "instrument_id": self.instrument_id,
            "registered_primary_metric": self.registered_primary_metric,
            "registered_minimum_detectable_effect": self.registered_minimum_detectable_effect,
            "frozen_kappa": self.frozen_kappa,
            "declared_on": self.declared_on,
            "rationale": self.rationale,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class CeilingEvidence:
    """Everything the gate is allowed to read after the declaration is frozen."""

    instrument_id: str
    oracle_computability: OracleComputability
    equal_budget_verified: bool
    reference_parent_arm_id: str
    bounds: Tuple[CeilingBound, ...]
    arm_budget_l1_distance_from_uniform: float | None = None


@dataclass(frozen=True)
class AdmissibilityDecision:
    """The verdict plus the telemetry the sealed packet requires."""

    verdict: AdmissibilityVerdict
    instrument_id: str
    registered_primary_metric: str
    registered_minimum_detectable_effect: float
    frozen_kappa: float
    declaration_sha256: str
    oracle_computability_status: OracleComputability
    equal_budget_verified: bool
    reference_parent_arm_id: str
    licensing_bound_id: str | None
    licensing_bound_kind: BoundKind | None
    best_lower_bound: float | None
    least_upper_bound: float | None
    verdict_kappa_range: str
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def licenses_comparison_execution(self) -> bool:
        """Only an ADMISSIBLE verdict licenses spending the comparison.

        Even then, admissibility grants no expectation that any policy will win.
        """
        return self.verdict is AdmissibilityVerdict.ADMISSIBLE

    @property
    def upgradeable_by_outcome_access(self) -> bool:
        return False


def _cannot_check(
    declaration: FrozenAdmissibilityDeclaration,
    evidence: CeilingEvidence,
    reasons: Tuple[str, ...],
    *,
    best_lower: float | None = None,
    least_upper: float | None = None,
) -> AdmissibilityDecision:
    return AdmissibilityDecision(
        verdict=AdmissibilityVerdict.CANNOT_CHECK,
        instrument_id=declaration.instrument_id,
        registered_primary_metric=declaration.registered_primary_metric,
        registered_minimum_detectable_effect=declaration.registered_minimum_detectable_effect,
        frozen_kappa=declaration.frozen_kappa,
        declaration_sha256=declaration.content_sha256,
        oracle_computability_status=evidence.oracle_computability,
        equal_budget_verified=evidence.equal_budget_verified,
        reference_parent_arm_id=evidence.reference_parent_arm_id,
        licensing_bound_id=None,
        licensing_bound_kind=None,
        best_lower_bound=best_lower,
        least_upper_bound=least_upper,
        verdict_kappa_range="CANNOT_CHECK_is_kappa_independent",
        reasons=reasons,
    )


def decide_instrument_admissibility(
    declaration: FrozenAdmissibilityDeclaration,
    evidence: CeilingEvidence,
    *,
    tolerance: float = 1e-12,
) -> AdmissibilityDecision:
    """Decide ADMISSIBLE / INADMISSIBLE / CANNOT_CHECK for one frozen instrument.

    Decision logic, in authority order:

    1. any scope or integrity failure -> ``CANNOT_CHECK`` (fail closed);
    2. least UPPER bound below ``kappa * MDE`` -> ``INADMISSIBLE`` — only an
       upper bound may license this verdict;
    3. best LOWER bound at or above ``kappa * MDE`` -> ``ADMISSIBLE`` —
       achievability shown constructively;
    4. otherwise the bounds are too loose to decide -> ``CANNOT_CHECK``.
    """

    if evidence.instrument_id != declaration.instrument_id:
        return _cannot_check(
            declaration,
            evidence,
            (
                "instrument_identity_mismatch:"
                f"declaration={declaration.instrument_id!r},evidence={evidence.instrument_id!r}",
            ),
        )
    if not evidence.equal_budget_verified:
        return _cannot_check(
            declaration,
            evidence,
            ("equal_budget_not_verified:unequal_budget_comparisons_are_out_of_scope",),
        )
    if evidence.oracle_computability is not OracleComputability.COMPUTABLE:
        return _cannot_check(
            declaration,
            evidence,
            (
                "oracle_not_computable:fail_closed",
                "an_uncomputable_oracle_never_yields_ADMISSIBLE",
            ),
        )
    if not evidence.bounds:
        return _cannot_check(declaration, evidence, ("no_ceiling_bounds_supplied",))

    for bound in evidence.bounds:
        if not (isinstance(bound.value, (int, float)) and isfinite(bound.value)):
            return _cannot_check(
                declaration,
                evidence,
                (f"non_finite_bound_value:{bound.bound_id}",),
            )

    lowers = [b for b in evidence.bounds if b.kind in (BoundKind.LOWER_BOUND, BoundKind.EXACT)]
    uppers = [b for b in evidence.bounds if b.kind in (BoundKind.UPPER_BOUND, BoundKind.EXACT)]
    best_lower = max(lowers, key=lambda b: b.value) if lowers else None
    least_upper = min(uppers, key=lambda b: b.value) if uppers else None
    best_lower_value = best_lower.value if best_lower is not None else None
    least_upper_value = least_upper.value if least_upper is not None else None

    if (
        best_lower_value is not None
        and least_upper_value is not None
        and best_lower_value > least_upper_value + tolerance
    ):
        return _cannot_check(
            declaration,
            evidence,
            (
                "inconsistent_bounds:best_lower_exceeds_least_upper",
                f"best_lower={best_lower_value}",
                f"least_upper={least_upper_value}",
            ),
            best_lower=best_lower_value,
            least_upper=least_upper_value,
        )

    threshold = declaration.admissibility_threshold
    mde = declaration.registered_minimum_detectable_effect

    if least_upper is not None and least_upper_value < threshold:
        # kappa-sensitivity: INADMISSIBLE holds for every kappa > least_upper/MDE.
        kappa_floor = least_upper_value / mde
        return AdmissibilityDecision(
            verdict=AdmissibilityVerdict.INADMISSIBLE,
            instrument_id=declaration.instrument_id,
            registered_primary_metric=declaration.registered_primary_metric,
            registered_minimum_detectable_effect=mde,
            frozen_kappa=declaration.frozen_kappa,
            declaration_sha256=declaration.content_sha256,
            oracle_computability_status=evidence.oracle_computability,
            equal_budget_verified=evidence.equal_budget_verified,
            reference_parent_arm_id=evidence.reference_parent_arm_id,
            licensing_bound_id=least_upper.bound_id,
            licensing_bound_kind=least_upper.kind,
            best_lower_bound=best_lower_value,
            least_upper_bound=least_upper_value,
            verdict_kappa_range=f"holds_for_all_kappa_greater_than_{kappa_floor:.6f}",
            reasons=(
                "least_upper_bound_below_threshold",
                f"least_upper={least_upper_value}",
                f"threshold=kappa*mde={threshold}",
                f"licensed_by_upper_bound:{least_upper.bound_id}",
                "verdict_may_never_be_upgraded_by_arm_outcome_access",
            ),
        )

    if best_lower is not None and best_lower_value >= threshold:
        kappa_ceiling = best_lower_value / mde
        return AdmissibilityDecision(
            verdict=AdmissibilityVerdict.ADMISSIBLE,
            instrument_id=declaration.instrument_id,
            registered_primary_metric=declaration.registered_primary_metric,
            registered_minimum_detectable_effect=mde,
            frozen_kappa=declaration.frozen_kappa,
            declaration_sha256=declaration.content_sha256,
            oracle_computability_status=evidence.oracle_computability,
            equal_budget_verified=evidence.equal_budget_verified,
            reference_parent_arm_id=evidence.reference_parent_arm_id,
            licensing_bound_id=best_lower.bound_id,
            licensing_bound_kind=best_lower.kind,
            best_lower_bound=best_lower_value,
            least_upper_bound=least_upper_value,
            verdict_kappa_range=f"holds_for_all_kappa_up_to_{kappa_ceiling:.6f}",
            reasons=(
                "best_lower_bound_at_or_above_threshold",
                f"best_lower={best_lower_value}",
                f"threshold=kappa*mde={threshold}",
                f"licensed_by_achievability_bound:{best_lower.bound_id}",
                "admissibility_grants_no_expectation_that_any_policy_wins",
            ),
        )

    return _cannot_check(
        declaration,
        evidence,
        (
            "bounds_too_loose_to_decide",
            "no_upper_bound_below_threshold_and_no_lower_bound_at_or_above_it",
            f"best_lower={best_lower_value}",
            f"least_upper={least_upper_value}",
            f"threshold={threshold}",
            "a_policy_score_may_never_license_INADMISSIBLE",
        ),
        best_lower=best_lower_value,
        least_upper=least_upper_value,
    )
