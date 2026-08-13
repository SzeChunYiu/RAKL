"""Field CONSTRUCTION on non-metric domains: registered constructor strategies.

Closes the open coordinate "Field CONSTRUCTION on non-metric domains" in
``research/unified_problem_solving_v1/OPEN_GAPS_REGISTER.md`` (P3). The prior
field experiment (``field_hypothesis_experiment.py``) *used* a field that was
handed to it: Manhattan distance on a grid was a GIVEN. On a symbolic domain
(permutations, rewrites) there is no coordinate metric to hand over, so the
field has to be BUILT from cheap observables.

What this module is
-------------------
A registry of constructor strategies that map

    (domain observables, training budget)  ->  ConstructedField

where ``ConstructedField`` is a scalar potential Phi over states. Three
registered strategies:

  * ``landmark_alt``      -- ALT-style landmark bounds from exact cost-to-go
                             computed ONLY on a bounded training subgraph.
  * ``feature_regression``-- least squares of verified remaining cost on cheap
                             structural features, fit on training instances.
  * ``relaxation_pdb``    -- exact solution of a RELAXATION (a state
                             abstraction / pattern database).

Factorization discipline (cost_geometry.py)
-------------------------------------------
The intrinsic object is the Lawvere quasimetric
``d(x, y) = inf over operator paths of summed nonnegative step costs``.
A constructed Phi is a HEURISTIC ON TOP of that quasimetric, never a
replacement for it: ``ConstructedField.as_cost_geometry()`` always raises.
Budget stays where cost_geometry puts it -- in sublevel sets of the value
function -- and never inside Phi.

Admissibility discipline
------------------------
``admissibility_status`` starts at ``UNKNOWN`` for every constructor and is
never assumed. It can only be raised by an explicit audit:

  * ``certify_consistency`` -- ORACLE-FREE. Checks the heuristic composition
    law ``Phi(x) <= c(x, y) + Phi(y)`` on every operator edge plus
    ``Phi(target) == 0``. This is exactly the Lawvere triangle law transported
    to the potential; when it holds EXHAUSTIVELY it *proves*
    ``Phi(x) <= d(x, target)`` by induction on a shortest path. Consistency
    therefore earns ``CONSISTENT_HEURISTIC``.
  * ``audit_admissibility_against_oracle`` -- MEASUREMENT ONLY, requires
    ground truth, so it is available in known worlds and not in deployment.

Sampled audits never yield ADMISSIBLE; they yield UNKNOWN (fail closed) unless
they find a violation, which yields INADMISSIBLE. Guarantee requests that the
evidence cannot support raise ``FieldGuaranteeError``.

Nothing here grants scientific, method-promotion, proof or routing authority.
"""
from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field as dc_field, replace
from enum import Enum
from hashlib import sha256
from math import inf, isfinite
from typing import (
    Callable,
    Hashable,
    Iterable,
    Mapping,
    Protocol,
    Sequence,
    runtime_checkable,
)

from rakl.fieldability import (
    CertificationWitness,
    FieldabilityProfile,
    GeometryArtifactIdentity,
    GeometryCertificationClass,
)

State = Hashable

CONSTRUCTION_VERSION = "orion.field_construction.v1"

__all__ = [
    "AdmissibilityStatus",
    "AuditCoverage",
    "AdmissibilityAudit",
    "ConstructionCost",
    "ConstructedField",
    "FieldGuaranteeError",
    "FieldConstructor",
    "LandmarkFieldConstructor",
    "FeatureRegressionFieldConstructor",
    "RelaxationFieldConstructor",
    "ConstructionDomain",
    "StateAbstraction",
    "register_constructor",
    "get_constructor",
    "registered_strategy_ids",
    "certify_consistency",
    "audit_admissibility_against_oracle",
    "uniform_field",
    "pseudorandom_field",
    "explicit_field",
    "residual_vs_intrinsic",
    "DEFAULT_COST_RATES",
    "CONSTRUCTION_VERSION",
]


class FieldGuaranteeError(RuntimeError):
    """Raised when a constructed field is asked for a guarantee it cannot support."""


class AdmissibilityStatus(str, Enum):
    ADMISSIBLE = "ADMISSIBLE"
    INADMISSIBLE = "INADMISSIBLE"
    UNKNOWN = "UNKNOWN"


class AuditCoverage(str, Enum):
    EXHAUSTIVE = "EXHAUSTIVE"
    SAMPLE = "SAMPLE"


# ---------------------------------------------------------------------------
# construction cost accounting
# ---------------------------------------------------------------------------

#: Declared exchange rates into "node-expansion equivalents". A node expansion
#: is the atomic unit: one state popped, its successors generated. An abstract
#: (relaxed) expansion does the same shape of work in a smaller space, so it
#: costs 1.0. A cheap-feature scan touches the state once without generating
#: successors; charged 1.0 as a CONSERVATIVE (constructor-unfavourable) rate.
#: A table lookup is charged 0.0 -- it is a dict probe, orders of magnitude
#: below successor generation. These rates are declared, not derived; the
#: experiment reports a sensitivity with every rate forced to 1.0.
DEFAULT_COST_RATES: Mapping[str, float] = {
    "node_expansions": 1.0,
    "abstract_node_expansions": 1.0,
    "feature_evaluations": 1.0,
    "table_lookups": 0.0,
    "edge_checks": 0.25,
}


@dataclass(frozen=True)
class ConstructionCost:
    """Counted work a constructor did. ``oracle_calls`` must stay zero."""

    node_expansions: int = 0
    abstract_node_expansions: int = 0
    feature_evaluations: int = 0
    table_lookups: int = 0
    edge_checks: int = 0
    oracle_calls: int = 0

    def __post_init__(self) -> None:
        for name in (
            "node_expansions",
            "abstract_node_expansions",
            "feature_evaluations",
            "table_lookups",
            "edge_checks",
            "oracle_calls",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"construction cost counter {name} must be nonnegative")

    def total_node_equivalents(self, rates: Mapping[str, float] | None = None) -> float:
        r = DEFAULT_COST_RATES if rates is None else rates
        return float(
            self.node_expansions * r.get("node_expansions", 1.0)
            + self.abstract_node_expansions * r.get("abstract_node_expansions", 1.0)
            + self.feature_evaluations * r.get("feature_evaluations", 1.0)
            + self.table_lookups * r.get("table_lookups", 0.0)
            + self.edge_checks * r.get("edge_checks", 0.25)
        )

    def merged(self, other: "ConstructionCost") -> "ConstructionCost":
        return ConstructionCost(
            node_expansions=self.node_expansions + other.node_expansions,
            abstract_node_expansions=self.abstract_node_expansions + other.abstract_node_expansions,
            feature_evaluations=self.feature_evaluations + other.feature_evaluations,
            table_lookups=self.table_lookups + other.table_lookups,
            edge_checks=self.edge_checks + other.edge_checks,
            oracle_calls=self.oracle_calls + other.oracle_calls,
        )

    def as_dict(self) -> dict:
        return {
            "node_expansions": self.node_expansions,
            "abstract_node_expansions": self.abstract_node_expansions,
            "feature_evaluations": self.feature_evaluations,
            "table_lookups": self.table_lookups,
            "edge_checks": self.edge_checks,
            "oracle_calls": self.oracle_calls,
            "total_node_equivalents": round(self.total_node_equivalents(), 4),
        }


# ---------------------------------------------------------------------------
# admissibility evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissibilityAudit:
    """Evidence about whether Phi ever overestimates the intrinsic cost-to-go.

    ``method`` is one of ``CONSISTENCY_PROOF`` (oracle-free, structural) or
    ``ORACLE_COMPARISON`` (known-world measurement). ``status`` fails closed:
    a clean SAMPLE is UNKNOWN, never ADMISSIBLE.
    """

    method: str
    coverage: AuditCoverage
    units_checked: int
    violations: int
    max_overestimate: float
    target_value_is_zero: bool = True
    detail: Mapping[str, object] = dc_field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.method not in {"CONSISTENCY_PROOF", "ORACLE_COMPARISON"}:
            raise ValueError(f"unknown admissibility audit method: {self.method}")
        if self.units_checked < 0 or self.violations < 0:
            raise ValueError("audit counters must be nonnegative")
        if self.violations > self.units_checked:
            raise ValueError("violations cannot exceed units checked")

    @property
    def status(self) -> AdmissibilityStatus:
        if self.violations > 0:
            return AdmissibilityStatus.INADMISSIBLE
        if not self.target_value_is_zero:
            # Phi(target) > 0 is itself an overestimate of d(target,target)=0.
            return AdmissibilityStatus.INADMISSIBLE
        if self.coverage is AuditCoverage.EXHAUSTIVE and self.units_checked > 0:
            return AdmissibilityStatus.ADMISSIBLE
        return AdmissibilityStatus.UNKNOWN

    @property
    def proves_consistency(self) -> bool:
        return (
            self.method == "CONSISTENCY_PROOF"
            and self.coverage is AuditCoverage.EXHAUSTIVE
            and self.violations == 0
            and self.target_value_is_zero
            and self.units_checked > 0
        )

    @property
    def violation_rate(self) -> float:
        return (self.violations / self.units_checked) if self.units_checked else 0.0

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    def as_dict(self) -> dict:
        return {
            "method": self.method,
            "coverage": self.coverage.value,
            "units_checked": self.units_checked,
            "violations": self.violations,
            "violation_rate": round(self.violation_rate, 6),
            "max_overestimate": round(float(self.max_overestimate), 6),
            "target_value_is_zero": self.target_value_is_zero,
            "status": self.status.value,
            "detail": dict(self.detail),
        }


# ---------------------------------------------------------------------------
# the constructed field
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConstructedField:
    """A cheap scalar potential Phi built without oracle access.

    Phi is a heuristic layered on the intrinsic quasimetric named by
    ``intrinsic_geometry_id``/``cost_algebra_id``. It is NOT a distance: it has
    no composition law of its own until ``certify_consistency`` says so, and
    ``as_cost_geometry`` always refuses.
    """

    strategy_id: str
    target: State
    intrinsic_geometry_id: str
    cost_algebra_id: str
    construction_cost: ConstructionCost
    table: Mapping[State, float] = dc_field(default_factory=dict)
    evaluator: Callable[[State], float] | None = None
    default_value: float = 0.0
    per_query_evaluation_cost: float = 0.0
    construction_version: str = CONSTRUCTION_VERSION
    provenance: Mapping[str, object] = dc_field(default_factory=dict)
    audits: tuple[AdmissibilityAudit, ...] = ()

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise ValueError("constructed field requires a strategy_id")
        if self.construction_cost.oracle_calls > 0:
            raise FieldGuaranteeError(
                "a constructed field must be built without ground-truth oracle access; "
                f"strategy {self.strategy_id!r} recorded "
                f"{self.construction_cost.oracle_calls} oracle calls"
            )
        if self.per_query_evaluation_cost < 0:
            raise ValueError("per_query_evaluation_cost must be nonnegative")
        if not isfinite(self.default_value):
            raise ValueError("default_value must be finite")
        object.__setattr__(self, "_stats", {"evaluations": 0})

    # -- evaluation --------------------------------------------------------
    def phi(self, state: State) -> float:
        stats = getattr(self, "_stats")
        stats["evaluations"] += 1
        val = self.table.get(state)
        if val is None and self.evaluator is not None:
            val = self.evaluator(state)
        if val is None:
            val = self.default_value
        if not isfinite(val) or val < 0:
            raise FieldGuaranteeError(
                f"field {self.strategy_id!r} produced a non-finite/negative value {val!r}; "
                "a cost-to-go potential must be finite and nonnegative (fail closed)"
            )
        return float(val)

    __call__ = phi

    @property
    def evaluations(self) -> int:
        return int(getattr(self, "_stats")["evaluations"])

    def reset_evaluation_counter(self) -> None:
        getattr(self, "_stats")["evaluations"] = 0

    def query_cost(self, evaluations: int | None = None) -> float:
        n = self.evaluations if evaluations is None else evaluations
        return float(n) * self.per_query_evaluation_cost

    # -- admissibility -----------------------------------------------------
    @property
    def admissibility_status(self) -> AdmissibilityStatus:
        """Never assumed. INADMISSIBLE dominates; a clean SAMPLE stays UNKNOWN."""
        if any(a.status is AdmissibilityStatus.INADMISSIBLE for a in self.audits):
            return AdmissibilityStatus.INADMISSIBLE
        if any(a.status is AdmissibilityStatus.ADMISSIBLE for a in self.audits):
            return AdmissibilityStatus.ADMISSIBLE
        return AdmissibilityStatus.UNKNOWN

    @property
    def is_certified_consistent(self) -> bool:
        return any(a.proves_consistency for a in self.audits)

    def with_audit(self, audit: AdmissibilityAudit) -> "ConstructedField":
        return replace(self, audits=self.audits + (audit,))

    # -- authority ---------------------------------------------------------
    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion(self) -> bool:
        return False

    # -- certification -----------------------------------------------------
    @property
    def certification_class(self) -> GeometryCertificationClass:
        """Strongest class the *evidence on this object* supports."""
        if self.is_certified_consistent:
            return GeometryCertificationClass.CONSISTENT_HEURISTIC
        if self.admissibility_status is AdmissibilityStatus.ADMISSIBLE:
            return GeometryCertificationClass.ADMISSIBLE_LOWER_BOUND
        if self.audits:
            return GeometryCertificationClass.EMPIRICAL_RANKER
        return GeometryCertificationClass.UNCERTIFIED

    def subject_fingerprint(self) -> str:
        payload = "|".join(
            (
                "orion.field_construction.subject.v1",
                self.strategy_id,
                repr(self.target),
                self.intrinsic_geometry_id,
                self.cost_algebra_id,
                self.construction_version,
                repr(sorted(self.provenance.items(), key=lambda kv: kv[0])),
            )
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def geometry_identity(
        self,
        *,
        specification_hash: str,
        root_qoi: str,
        operator_basis_version: str,
        map_revision_hash: str,
        chart_id: str,
        verifier_subject_hash: str,
        verifier_id: str | None = None,
    ) -> GeometryArtifactIdentity:
        """Bind this field into a fieldability ``GeometryArtifactIdentity``.

        The declared class is the one the audits support. A certification
        witness is attached only when that class is above UNCERTIFIED, so the
        fieldability claim properties (``is_theorem_certified_heuristic_class``)
        fail closed for unaudited fields exactly as audit I5 requires.
        """
        cls = self.certification_class
        identity = GeometryArtifactIdentity(
            geometry_id=f"{self.strategy_id}@{self.intrinsic_geometry_id}",
            specification_hash=specification_hash,
            root_qoi=root_qoi,
            operator_basis_version=operator_basis_version,
            map_revision_hash=map_revision_hash,
            chart_id=chart_id,
            verifier_subject_hash=verifier_subject_hash,
            cost_algebra_id=self.cost_algebra_id,
            construction_version=self.construction_version,
            certification_class=cls,
        )
        if cls is GeometryCertificationClass.UNCERTIFIED:
            return identity
        if verifier_id is None:
            raise FieldGuaranteeError(
                "a certification class above UNCERTIFIED needs a named verifier "
                "(audit I5): pass verifier_id"
            )
        witness = CertificationWitness(
            witness_id=f"fieldctor:{self.subject_fingerprint()[:16]}",
            verifier_id=verifier_id,
            subject_hash=identity.certification_subject_hash,
            certified_class=cls,
        )
        return replace(identity, certification_witness=witness)

    def fieldability_profile(
        self,
        *,
        specification_hash: str,
        root_qoi: str,
        operator_basis_version: str,
        map_revision_hash: str,
        chart_id: str,
        verifier_subject_hash: str,
        verifier_id: str | None = None,
        baseline_per_query_cost: float | None = None,
        cost_rates: Mapping[str, float] | None = None,
        **profile_kwargs: float,
    ) -> FieldabilityProfile:
        identity = self.geometry_identity(
            specification_hash=specification_hash,
            root_qoi=root_qoi,
            operator_basis_version=operator_basis_version,
            map_revision_hash=map_revision_hash,
            chart_id=chart_id,
            verifier_subject_hash=verifier_subject_hash,
            verifier_id=verifier_id,
        )
        return FieldabilityProfile(
            identity=identity,
            build_cost=self.construction_cost.total_node_equivalents(cost_rates),
            baseline_per_query_cost=baseline_per_query_cost,
            extraction_per_query_cost=self.per_query_evaluation_cost,
            **profile_kwargs,
        )

    # -- fail-closed guards ------------------------------------------------
    def require_admissible_lower_bound(self) -> None:
        if self.admissibility_status is not AdmissibilityStatus.ADMISSIBLE:
            raise FieldGuaranteeError(
                f"field {self.strategy_id!r} cannot support an admissible-lower-bound claim: "
                f"admissibility_status={self.admissibility_status.value} "
                f"({len(self.audits)} audit(s); a sampled clean audit stays UNKNOWN by design)"
            )

    def require_consistent(self) -> None:
        if not self.is_certified_consistent:
            raise FieldGuaranteeError(
                f"field {self.strategy_id!r} has no exhaustive consistency proof; "
                "Phi(x) <= c(x,y) + Phi(y) is unverified on this operator basis"
            )

    def assert_supports_astar_optimality(self) -> None:
        """A* returns optimal paths only under an admissible heuristic."""
        self.require_admissible_lower_bound()

    def as_cost_geometry(self):  # pragma: no cover - always raises by design
        raise FieldGuaranteeError(
            "a constructed field is a scalar potential layered ON TOP of the intrinsic "
            "Lawvere quasimetric d(x,y); it is not a distance and cannot replace "
            "cost_geometry.OperatorCostGeometry. Use certify_consistency to test the "
            "composition law, and keep budget in sublevel sets of the value function."
        )

    def as_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "construction_version": self.construction_version,
            "intrinsic_geometry_id": self.intrinsic_geometry_id,
            "cost_algebra_id": self.cost_algebra_id,
            "construction_cost": self.construction_cost.as_dict(),
            "per_query_evaluation_cost": self.per_query_evaluation_cost,
            "table_entries": len(self.table),
            "admissibility_status": self.admissibility_status.value,
            "certification_class": self.certification_class.value,
            "is_certified_consistent": self.is_certified_consistent,
            "subject_fingerprint": self.subject_fingerprint(),
            "provenance": dict(self.provenance),
            "audits": [a.as_dict() for a in self.audits],
            "grants_scientific_authority": False,
            "grants_target_authority": False,
        }


# ---------------------------------------------------------------------------
# domain interface (cheap observables only -- no ground truth)
# ---------------------------------------------------------------------------


@runtime_checkable
class StateAbstraction(Protocol):
    """A RELAXATION: a cost-non-increasing homomorphic image of the domain.

    ``project`` maps concrete states to abstract states; ``abstract_predecessors``
    lets the constructor solve the relaxation exactly by backward search from
    the abstract target. Whether the projection really is a homomorphism is NOT
    trusted -- ``certify_consistency`` on the resulting field is what earns the
    admissibility claim.
    """

    abstraction_id: str

    def project(self, state: State) -> State: ...

    def abstract_predecessors(self, astate: State) -> Sequence[tuple[State, float]]: ...


@runtime_checkable
class ConstructionDomain(Protocol):
    """Cheap observables a constructor is allowed to see. No oracle here."""

    domain_id: str
    cost_algebra_id: str

    def successors(self, state: State) -> Sequence[tuple[State, float]]: ...

    def predecessors(self, state: State) -> Sequence[tuple[State, float]]: ...

    def feature_names(self) -> Sequence[str]: ...

    def features(self, state: State, target: State) -> Sequence[float]: ...

    def abstractions(self) -> Sequence[StateAbstraction]: ...


# ---------------------------------------------------------------------------
# audits
# ---------------------------------------------------------------------------


def certify_consistency(
    field: ConstructedField,
    domain: ConstructionDomain,
    states: Iterable[State],
    *,
    coverage: AuditCoverage,
) -> AdmissibilityAudit:
    """ORACLE-FREE admissibility route via the heuristic composition law.

    Checks ``Phi(x) <= c(x, y) + Phi(y)`` for every operator edge out of every
    state in ``states``, plus ``Phi(target) == 0``. Under EXHAUSTIVE coverage a
    clean result *proves* ``Phi(x) <= d(x, target)``: telescope the inequality
    along any optimal path from ``x`` to ``target``. This is the Lawvere
    triangle law of cost_geometry transported to the potential; no ground truth
    is consulted, so it is available in deployment, not only in known worlds.

    ``coverage`` is asserted by the caller and is what makes the difference
    between a proof and a spot check: only EXHAUSTIVE can return ADMISSIBLE.
    """
    checked = 0
    violations = 0
    worst = 0.0
    worst_edge: tuple[str, str] | None = None
    for x in states:
        px = field.phi(x)
        for y, c in domain.successors(x):
            checked += 1
            slack = px - (c + field.phi(y))
            if slack > 1e-9:
                violations += 1
                if slack > worst:
                    worst = slack
                    worst_edge = (repr(x), repr(y))
    target_zero = abs(field.phi(field.target)) <= 1e-12
    return AdmissibilityAudit(
        method="CONSISTENCY_PROOF",
        coverage=coverage,
        units_checked=checked,
        violations=violations,
        max_overestimate=worst,
        target_value_is_zero=target_zero,
        detail={
            "law": "Phi(x) <= c(x,y) + Phi(y) for every operator edge; Phi(target)=0",
            "oracle_free": True,
            "worst_edge": worst_edge,
        },
    )


def audit_admissibility_against_oracle(
    field: ConstructedField,
    true_cost_to_go: Mapping[State, float],
    *,
    coverage: AuditCoverage,
) -> AdmissibilityAudit:
    """MEASUREMENT-ONLY audit: count states where Phi(x) > d(x, target).

    Requires ground truth and is therefore a known-world instrument. It can
    REFUTE admissibility anywhere, but it can only confirm it when the state
    space was enumerated exhaustively.
    """
    checked = 0
    violations = 0
    worst = 0.0
    for x, true_c in true_cost_to_go.items():
        if true_c == inf:
            continue
        checked += 1
        over = field.phi(x) - true_c
        if over > 1e-9:
            violations += 1
            worst = max(worst, over)
    target_zero = abs(field.phi(field.target)) <= 1e-12
    return AdmissibilityAudit(
        method="ORACLE_COMPARISON",
        coverage=coverage,
        units_checked=checked,
        violations=violations,
        max_overestimate=worst,
        target_value_is_zero=target_zero,
        detail={"oracle_free": False, "note": "known-world measurement, not a deployment affordance"},
    )


def residual_vs_intrinsic(
    field: ConstructedField,
    geometry,
    target: State,
    states: Iterable[State],
) -> dict:
    """Phi(x) - d(x, target) against a cost_geometry.OperatorCostGeometry.

    Makes the layering explicit: the intrinsic quasimetric is the reference,
    the field is the approximation, and the residual is the approximation error.
    """
    residuals = []
    for x in states:
        d = geometry.d(x, target)
        if d == inf:
            continue
        residuals.append(field.phi(x) - d)
    if not residuals:
        return {"n": 0, "mean_residual": None, "max_overestimate": None}
    return {
        "n": len(residuals),
        "mean_residual": sum(residuals) / len(residuals),
        "max_overestimate": max(residuals),
        "max_underestimate": min(residuals),
    }
