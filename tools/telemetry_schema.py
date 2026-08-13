"""
Canonical telemetry schema for RAKL experiments.
Defines the standard fields that all experiment results SHOULD emit.

Schema version: orion-telemetry-v1
grants_scientific_authority: false
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass
from enum import Enum


class FieldRequirement(Enum):
    """How required a telemetry field is."""
    REQUIRED = "required"  # Must be present for valid experiment results
    OPTIONAL = "optional"  # Nice to have, but absence is acceptable
    UNCOMPUTABLE = "uncomputable"  # Cannot be retro-computed from historical runs


@dataclass
class TelemetryField:
    """Definition of a telemetry field."""
    name: str
    description: str
    requirement: FieldRequirement
    dtype: str  # Expected data type: "number", "boolean", "string", "object"
    examples: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "requirement": self.requirement.value,
            "dtype": self.dtype,
            "examples": self.examples
        }


# Canonical telemetry field definitions
CANONICAL_FIELDS: Dict[str, TelemetryField] = {
    # Envelope fields (metadata)
    "schema_version": TelemetryField(
        name="schema_version",
        description="Version identifier for the result schema format",
        requirement=FieldRequirement.REQUIRED,
        dtype="string",
        examples=["orion-telemetry-v1", "paper2-a3-a4-matched-empirics-156-harvest-receipt-v1"]
    ),
    "grants_scientific_authority": TelemetryField(
        name="grants_scientific_authority",
        description="Whether this result grants scientific authority (default false)",
        requirement=FieldRequirement.REQUIRED,
        dtype="boolean",
        examples=["false", "true"]
    ),
    "seeds": TelemetryField(
        name="seeds",
        description="Random seeds used for reproducibility (single value or array)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="object",
        examples=["42", "[42, 123, 456]", "seed"]
    ),
    "n": TelemetryField(
        name="n",
        description="Sample size or number of independent units",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["100", "n_completed", "n_scenarios"]
    ),
    "independent_unit": TelemetryField(
        name="independent_unit",
        description="What constitutes an independent observation (e.g., scenario, query, graph)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="string",
        examples=["scenario", "query", "graph", "claim"]
    ),
    
    # Outcome fields
    "verified_success": TelemetryField(
        name="verified_success",
        description="Fraction of outcomes verified as successful (or boolean for single trial)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="object",
        examples=["0.85", "true", "valid_upgrade_recall", "success_rate"]
    ),
    "false_accept_rate": TelemetryField(
        name="false_accept_rate",
        description="Rate at which the system accepts false positives (Type I error)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["0.05", "0.12", "false_conservative_refusal_rate"]
    ),
    
    # Token usage
    "tokens_in": TelemetryField(
        name="tokens_in",
        description="Total input tokens processed (prompt tokens)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["12500", "tokens_prompt", "input_tokens"]
    ),
    "tokens_out": TelemetryField(
        name="tokens_out",
        description="Total output tokens generated (completion tokens)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["3200", "tokens_completion", "output_tokens"]
    ),
    
    # API/call counts
    "model_calls": TelemetryField(
        name="model_calls",
        description="Number of model API calls made",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["45", "n_calls", "api_calls"]
    ),
    "tool_calls": TelemetryField(
        name="tool_calls",
        description="Number of tool/function calls invoked",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["12", "n_tool_calls"]
    ),
    "verifier_calls": TelemetryField(
        name="verifier_calls",
        description="Number of verification calls made",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["8", "verification_calls"]
    ),
    "states_expanded": TelemetryField(
        name="states_expanded",
        description="Number of states/nodes expanded during search",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["1250", "baseline_expanded", "field_expanded", "nodes_visited"]
    ),
    
    # Time metrics
    "wall_time_s": TelemetryField(
        name="wall_time_s",
        description="Wall-clock execution time in seconds",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["12.5", "wall_time", "elapsed_time"]
    ),
    "cpu_time_s": TelemetryField(
        name="cpu_time_s",
        description="CPU time consumed in seconds",
        requirement=FieldRequirement.UNCOMPUTABLE,
        dtype="number",
        examples=["10.2", "cpu_time", "cputime", "cpu"]
    ),
    "gpu_time_s": TelemetryField(
        name="gpu_time_s",
        description="GPU time consumed in seconds",
        requirement=FieldRequirement.UNCOMPUTABLE,
        dtype="number",
        examples=["8.5", "gpu_time", "gputime"]
    ),
    
    # Resource usage
    "ram_peak_mb": TelemetryField(
        name="ram_peak_mb",
        description="Peak RAM usage in megabytes",
        requirement=FieldRequirement.UNCOMPUTABLE,
        dtype="number",
        examples=["4096", "maxrss", "memory_mb", "ram_peak"]
    ),
    "vram_peak_mb": TelemetryField(
        name="vram_peak_mb",
        description="Peak VRAM usage in megabytes",
        requirement=FieldRequirement.UNCOMPUTABLE,
        dtype="number",
        examples=["2048", "vram", "gpu_mem_mb", "vram_peak"]
    ),
    
    # Cost metrics
    "provider_cost_usd": TelemetryField(
        name="provider_cost_usd",
        description="Total provider API cost in USD",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["0.45", "cost_usd", "api_cost", "total_cost"]
    ),
    "construction_cost": TelemetryField(
        name="construction_cost",
        description="Cost to construct the field/structure (may include confidence interval)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="object",
        examples=["{mean: 0.12, lo: 0.10, hi: 0.14, n: 100}", "build_cost"]
    ),
    "verification_cost": TelemetryField(
        name="verification_cost",
        description="Cost to verify claims/hypotheses",
        requirement=FieldRequirement.OPTIONAL,
        dtype="number",
        examples=["0.08", "verification_cost_total"]
    ),
    
    # Cache performance
    "cache_hit": TelemetryField(
        name="cache_hit",
        description="Number of cache hits (or hit rate)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="object",
        examples=["45", "0.78", "cache_hits", "hit_rate"]
    ),
    "cache_miss": TelemetryField(
        name="cache_miss",
        description="Number of cache misses (or miss rate)",
        requirement=FieldRequirement.OPTIONAL,
        dtype="object",
        examples=["12", "0.22", "cache_misses", "miss_rate"]
    ),
}


# =========================================================================== #
# #544: claim-class-conditional telemetry requirements + completeness status.
# =========================================================================== #
# The canonical schema above marks every performance/cost field OPTIONAL, so an
# artifact carrying only the envelope (schema_version + grants_scientific_authority)
# plus a hand-written net metric passes schema-valid with ZERO performance
# evidence. #544 makes the required fields CONDITIONAL on the claim class the
# experiment makes, and exposes a machine-readable completeness status the
# promotion gate uses to refuse an UNCONDITIONAL positive efficiency verdict
# built on incomplete telemetry. Historical gaps are preserved + caveated
# (CANNOT_CHECK), never silently zeroed or defaulted.


class ClaimClass:
    """The kind of claim an experiment artifact supports. Drives which telemetry
    fields are REQUIRED (vs merely nice-to-have) for that artifact to certify a
    promotion of its class."""
    CONFORMANCE = "CONFORMANCE"      # protocol/structural compliance; no perf telemetry
    CORRECTNESS = "CORRECTNESS"      # does-it-work: graded on an outcome/rate, not cost
    PERFORMANCE = "PERFORMANCE"      # how-fast: needs a measured quantity (time or count)
    EFFICIENCY = "EFFICIENCY"        # net-of-cost advantage: measured quantity + charged cost
    LLM_RUNTIME = "LLM_RUNTIME"      # model-invoking run: PERFORMANCE + model/provider/tokens
    GPU_TRAINING = "GPU_TRAINING"    # GPU run: PERFORMANCE + gpu time/vram
    CACHE_REUSE = "CACHE_REUSE"      # reuse vs recompute: EFFICIENCY + reuse-error-rate


# A logical requirement maps to one or more concrete field names (aliases). The
# requirement is SATISFIED for an artifact if ANY alias is present (recursively).
# Aliases are grounded in the real field names emitted by the live experiment
# artifacts (validated against research/.../results/*.json, not guessed).
FIELD_ALIASES: Dict[str, List[str]] = {
    "sample": [
        "n", "n_completed", "n_instances", "n_instances_per_cell", "n_queries",
        "n_tasks", "n_scenarios_per_replicate", "n_tasks_per_replicate",
        "replicates", "replicates_per_cell", "sample_size", "worlds", "graphs_made",
    ],
    "seed": ["seed", "seeds"],
    "measured_quantity": [
        # wall time OR a primitive work counter -- one measured quantity suffices
        "wall_time_s", "wall_time", "elapsed_s", "runtime_s", "duration_s",
        "states_expanded", "n_expanded", "expansions", "nodes_expanded",
        "bfs_expanded", "field_expanded", "baseline_expanded", "astar_expanded",
        "calls", "n_calls", "model_calls", "function_calls",
        "tokens", "token_count", "total_tokens",
        "witnesses_registered", "mean_witnesses_registered", "n_witnesses",
        "cache_hits", "mean_cache_hits",
        "iterations", "n_iterations",
    ],
    "outcome": [
        # a correctness/honesty result: the thing the claim is graded on
        "verified_success", "success_rate", "outcome", "correct_rate",
        "forced_wrong_rate", "false_accept_rate", "sign_test_p", "signs_positive",
        "all_six_positive", "n_positive",
    ],
    "model": ["model", "model_name"],
    "provider": ["provider", "api_provider"],
    "tokens_count": ["tokens", "token_count", "total_tokens", "tokens_in"],
    "gpu_time_s": ["gpu_time_s", "gpu_time", "gputime"],
    "vram_peak_mb": ["vram_peak_mb", "vram", "peak_vram_mb"],
    "reuse_error_rate": [
        "reuse_error_rate", "stale_reuse_error_rate", "exact_error_rate",
        "unverified_reuse_error_rate",
    ],
    "construction_cost": ["construction_cost", "build_cost"],
    "verification_cost": [
        "verification_cost", "witness_cost", "certification_cost", "verify_cost",
        "mean_witnesses_registered", "witnesses_registered", "n_witnesses",
    ],
    "exact_cost": ["exact_cost"],
    "generic_cost": ["generic_cost"],
    "cost_model": ["cost_model", "cost_decomposition", "stage_costs", "total_cost"],
}


# Per-claim-class REQUIRED logical fields. Every listed group must be satisfiable
# from the artifact for the telemetry to be COMPLETE for that class. Economic
# (cost-charged) claims ADD their declared cost components via required_fields_for.
CLAIM_CLASS_REQUIREMENTS: Dict[str, List[str]] = {
    ClaimClass.CONFORMANCE:  ["sample"],
    ClaimClass.CORRECTNESS:  ["sample", "outcome"],            # may be deterministic -> no seed
    ClaimClass.PERFORMANCE:  ["sample", "seed", "measured_quantity"],
    ClaimClass.EFFICIENCY:   ["sample", "seed", "measured_quantity"],
    ClaimClass.LLM_RUNTIME:  ["sample", "seed", "measured_quantity",
                              "model", "provider", "tokens_count"],
    ClaimClass.GPU_TRAINING: ["sample", "seed", "measured_quantity",
                              "gpu_time_s", "vram_peak_mb"],
    ClaimClass.CACHE_REUSE:  ["sample", "seed", "reuse_error_rate"],
}

# Claim classes whose promotion is an EFFICIENCY/cost claim: a positive verdict
# here is blockable by the telemetry gate (issue #544 acceptance).
EFFICIENCY_CLAIM_CLASSES = frozenset({
    ClaimClass.PERFORMANCE, ClaimClass.EFFICIENCY, ClaimClass.LLM_RUNTIME,
    ClaimClass.GPU_TRAINING, ClaimClass.CACHE_REUSE,
})


def required_fields_for(
    claim_class: str, *, economic_cost_fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Return the structured required-field list for a claim class.

    Each element is ``{"requirement": <logical name>, "aliases": [...]}``.
    Economic (cost-charged) claims add their declared cost components: the net
    metric is only "net" if those cost fields are actually present in the
    artifact, so the gate can VERIFY a charged cost rather than trust a flag.
    """
    logical = list(CLAIM_CLASS_REQUIREMENTS.get(claim_class, []))
    if economic_cost_fields:
        for cf in economic_cost_fields:
            if cf not in logical:
                logical.append(cf)
    return [{"requirement": r, "aliases": list(FIELD_ALIASES.get(r, [r]))} for r in logical]


def _alias_present(obj: Any, aliases: List[str]) -> bool:
    """True if any alias key appears (recursively) anywhere in the artifact."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in aliases:
                return True
            if _alias_present(v, aliases):
                return True
    elif isinstance(obj, list):
        for it in obj:
            if _alias_present(it, aliases):
                return True
    return False


def telemetry_completeness_status(
    artifact: Any,
    claim_class: str,
    *,
    economic_cost_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute machine-readable telemetry completeness for an artifact + claim class.

    Returns a dict::

        {"status": "COMPLETE"|"PARTIAL"|"CANNOT_CHECK"|"INVALID_PROSPECTIVE",
         "claim_class": ..., "economic_cost_fields": [...],
         "required": [...], "present": [...], "missing": [...]}

    Status semantics:
      COMPLETE            - every required field for the class is present.
      INVALID_PROSPECTIVE - a PROSPECTIVE run (artifact declares ``prospective``
                            or a #531 reproducibility-package marker) is missing
                            required collectors. A defect: the run should have
                            measured them; the promotion gate blocks the verdict.
      CANNOT_CHECK        - a HISTORICAL run explicitly marks the missing data
                            unrecoverable (``telemetry_unrecoverable``); the gap
                            is real but cannot be filled retroactively.
      PARTIAL             - some required present, some missing, with no marker
                            (the default historical gap: data not recorded).

    Missing data is reported explicitly; it is NEVER silently defaulted to zero.
    """
    required = required_fields_for(claim_class, economic_cost_fields=economic_cost_fields)
    present: List[str] = []
    missing: List[str] = []
    for req in required:
        (present if _alias_present(artifact, req["aliases"]) else missing).append(req["requirement"])

    if not missing:
        status = "COMPLETE"
    else:
        prospective = (
            _alias_present(artifact, ["prospective", "is_prospective"])
            or _alias_present(artifact, ["reproducibility_package", "reproducibility_package_v1"])
        )
        unrecoverable = _alias_present(artifact, ["telemetry_unrecoverable"])
        if prospective:
            status = "INVALID_PROSPECTIVE"
        elif unrecoverable:
            status = "CANNOT_CHECK"
        else:
            status = "PARTIAL"
    return {
        "status": status,
        "claim_class": claim_class,
        "economic_cost_fields": economic_cost_fields or [],
        "required": [r["requirement"] for r in required],
        "present": present,
        "missing": missing,
    }



def get_schema_dict() -> Dict[str, Any]:
    """Export schema as dictionary for JSON serialization."""
    return {
        "schema_version": "orion-telemetry-v1",
        "grants_scientific_authority": False,
        "fields": {k: v.to_dict() for k, v in CANONICAL_FIELDS.items()},
        "#544_claim_class_requirements": {
            cls: reqs for cls, reqs in CLAIM_CLASS_REQUIREMENTS.items()
        },
        "#544_field_aliases": {
            req: aliases for req, aliases in FIELD_ALIASES.items()
        },
        "#544_efficiency_claim_classes": sorted(EFFICIENCY_CLAIM_CLASSES),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_schema_dict(), indent=2))
