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


def get_schema_dict() -> Dict[str, Any]:
    """Export schema as dictionary for JSON serialization."""
    return {
        "schema_version": "orion-telemetry-v1",
        "grants_scientific_authority": False,
        "fields": {k: v.to_dict() for k, v in CANONICAL_FIELDS.items()}
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_schema_dict(), indent=2))
