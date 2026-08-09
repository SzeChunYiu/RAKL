"""Public facade for the Round-036 constructive invention engine."""

from .availability_oracle import (
    AvailabilityReport,
    AvailabilityVerdict,
    SymbolAvailability,
    check_predictive_availability,
)
from .constructive_lattice import ConstructiveKnowledgeState
from .formal_oracles import (
    DynamicsClock,
    MatrixOracleReport,
    OracleVerdict,
    StabilityReport,
    check_covariance_psd,
    check_local_identifiability,
    check_local_linear_stability,
    check_transition_matrix,
    matrix_rank,
)
from .formalism import (
    EquationKind,
    ExprOp,
    FormalEquation,
    FormalExpression,
    FormalSymbol,
    Formalism,
    MechanismEdge,
    MechanismGraph,
    MechanismNode,
    MechanismNodeKind,
    MechanismRelation,
    ObservationMap,
    SymbolRole,
    VerificationPacket,
    VerificationReport,
    VerificationVerdict,
    validate_formalism_structure,
    verify_formalism,
)
from .hard_gates import (
    FullPositiveGoalReport,
    HardGateContract,
    HardGateObservation,
    HardGateReport,
    HardGateRequirement,
    HardGateState,
    evaluate_full_positive_goal,
    evaluate_hard_gates,
    polymarket_crypto_spot_gate_contract,
)
from .invention import (
    CandidateScore,
    CandidateTheory,
    GoalAssessment,
    GoalAssessmentVerdict,
    InventionMove,
    InventionOperator,
    PositiveGoalContract,
    ResidualKind,
    ResidualSignature,
    apply_invention_move,
    evaluate_positive_goal,
    invention_tasks_for_residual,
    pareto_frontier,
    recombine_candidates,
    residual_from_goal_assessment,
)
from .invention_benchmark import (
    InventionAttempt,
    InventionBenchmarkCase,
    InventionBenchmarkReport,
    InventionBenchmarkSuiteReport,
    InventionBenchmarkVerdict,
    InventionWorldKind,
    evaluate_invention_attempt,
    summarize_invention_suite,
)
from .invention_runtime import InventionRuntime, RuntimeCandidateAssessment
from .math_oracles import (
    Dimension,
    DimensionVerdict,
    EquationDimensionReport,
    FormalismDimensionReport,
    check_equation_dimensions,
    check_formalism_dimensions,
    infer_expression_dimension,
)
from .mechanism_compiler import (
    InteractionAggregation,
    InteractionLaw,
    MechanismCompileReport,
    MechanismCompileVerdict,
    StateEvolutionSpec,
    attach_compiled_equations,
    compile_mechanism_equations,
)
from .search_controller import (
    GenerationRequest,
    OperatorFamily,
    SearchBudget,
    SearchLoopState,
    SearchLoopVerdict,
    SearchRoundPlan,
    plan_next_search_round,
    record_search_round,
)
from .symbolic_discovery import (
    SymbolicDiscoveryReport,
    SymbolicDiscoverySpec,
    SymbolicLawCandidate,
    SymbolicSearchVerdict,
    discover_symbolic_laws,
    evaluate_expression,
)
from .typed_lattice import (
    CompatibilityWitness,
    ConstructiveLatticePath,
    KnowledgeAtom,
    KnowledgeAtomKind,
    LatticeCompatibility,
    LatticeSynthesisSeed,
    TypedKnowledgeLattice,
)

__all__ = [name for name in globals() if not name.startswith("_")]
