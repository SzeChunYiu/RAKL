"""Pre-Polymarket framework-hardening public API.

This module exposes the support layers added by the formal-closure/bootstrap pass
without requiring a risky rewrite of the package's historical root export list.
All exported reports preserve their own proposal/reproducibility-only authority
boundaries.
"""

from .artifact_attestation import (
    AttestationVerdict,
    RuntimeAttestation,
    attest_runtime,
    environment_fingerprint,
)
from .assumption_sensitivity import (
    AssumptionScenario,
    AssumptionSensitivityReport,
    AssumptionSensitivityTrial,
    AssumptionSensitivityVerdict,
    ConclusionClass,
    ScenarioAssessment,
    classify_conclusion,
    evaluate_assumption_sensitivity,
)
from .child_operators import (
    CHILD_OPERATORS,
    ChildOperatorOwnership,
    validate_child_operator_ownership,
)
from .context_efficiency import ContextEfficiencyReport, measure_context_efficiency
from .formal_contracts import (
    AuthorityEffect,
    ClosureVerdict,
    FormalClosureReport,
    METHOD_SURFACES,
    MechanicContract,
    validate_formal_closure,
)
from .meta_history import compile_meta_fiber_history
from .method_specs import METHOD_CONTRACTS
from .metrology import (
    AffineTransform,
    FirstOrderTransform,
    MetrologyReport,
    MetrologyVerdict,
    combine_independent_standard_uncertainties,
    propagate_affine,
    propagate_first_order_covariance,
)
from .model_criticism import (
    CriticismProbe,
    ModelCriticismReport,
    ModelCriticismTrial,
    ModelCriticismVerdict,
    ProbeCriticism,
    evaluate_model_criticism,
)
from .self_bootstrap import (
    BootstrapReport,
    BootstrapTrial,
    BootstrapVerdict,
    evaluate_bootstrap_trial,
)

__all__ = [
    "AffineTransform",
    "AssumptionScenario",
    "AssumptionSensitivityReport",
    "AssumptionSensitivityTrial",
    "AssumptionSensitivityVerdict",
    "AttestationVerdict",
    "AuthorityEffect",
    "BootstrapReport",
    "BootstrapTrial",
    "BootstrapVerdict",
    "CHILD_OPERATORS",
    "ChildOperatorOwnership",
    "ClosureVerdict",
    "ConclusionClass",
    "ContextEfficiencyReport",
    "CriticismProbe",
    "FirstOrderTransform",
    "FormalClosureReport",
    "METHOD_CONTRACTS",
    "METHOD_SURFACES",
    "MechanicContract",
    "MetrologyReport",
    "MetrologyVerdict",
    "ModelCriticismReport",
    "ModelCriticismTrial",
    "ModelCriticismVerdict",
    "ProbeCriticism",
    "RuntimeAttestation",
    "ScenarioAssessment",
    "attest_runtime",
    "classify_conclusion",
    "combine_independent_standard_uncertainties",
    "compile_meta_fiber_history",
    "environment_fingerprint",
    "evaluate_assumption_sensitivity",
    "evaluate_bootstrap_trial",
    "evaluate_model_criticism",
    "measure_context_efficiency",
    "propagate_affine",
    "propagate_first_order_covariance",
    "validate_child_operator_ownership",
    "validate_formal_closure",
]
