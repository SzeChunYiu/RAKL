"""Reference-only conformance model for proposed RAKL Recursive Framework Audit.

Not the RAKL implementation.  It makes the action vocabulary and fail-closed semantics
executable in this handoff package.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

class Coordinate(str, Enum):
    QUESTION="QUESTION"
    FRAMEWORK="FRAMEWORK"
    DECOMPOSITION="DECOMPOSITION"
    INTERFACE="INTERFACE"
    ATOM="ATOM"
    MEASUREMENT="MEASUREMENT"
    EVALUATOR="EVALUATOR"
    EVIDENCE="EVIDENCE"
    METHOD="METHOD"

class Action(str, Enum):
    SOLVE_CURRENT="SOLVE_CURRENT"
    REFRAME_QUESTION="REFRAME_QUESTION"
    CHALLENGE_FRAMEWORK="CHALLENGE_FRAMEWORK"
    SPLIT="SPLIT"
    MERGE="MERGE"
    REPAIR_INTERFACE="REPAIR_INTERFACE"
    REVISE_MEASUREMENT="REVISE_MEASUREMENT"
    AUDIT_EVALUATOR="AUDIT_EVALUATOR"
    RUN_DISCRIMINATOR="RUN_DISCRIMINATOR"
    ASCEND="ASCEND"
    EXTERNAL_TRUST_ROOT="EXTERNAL_TRUST_ROOT"
    STOP_BOUNDED="STOP_BOUNDED"
    CANNOT_CHECK="CANNOT_CHECK"

@dataclass(frozen=True)
class Residual:
    plausible_causes: Tuple[Coordinate,...]=()
    split_required: bool=False
    merge_required: bool=False
    parent_challenge_supported: bool=False
    distinct_local_repair_families_failed: int=0
    evaluator_invalid: bool=False
    external_trust_root: bool=False
    resource_bound: bool=False

@dataclass(frozen=True)
class Node:
    closure_coordinates_pass: bool=False
    material_open_residual: bool=True

@dataclass(frozen=True)
class Decision:
    action: Action
    grants_scientific_authority: bool=False
    grants_method_promotion_authority: bool=False

def decide(node: Node, residual: Residual) -> Decision:
    if residual.evaluator_invalid:
        return Decision(Action.AUDIT_EVALUATOR)
    if residual.external_trust_root:
        return Decision(Action.EXTERNAL_TRUST_ROOT)
    if residual.resource_bound and (node.material_open_residual or residual.plausible_causes):
        return Decision(Action.CANNOT_CHECK)
    if residual.parent_challenge_supported and residual.distinct_local_repair_families_failed >= 2:
        return Decision(Action.ASCEND)
    if len(set(residual.plausible_causes)) > 1:
        return Decision(Action.RUN_DISCRIMINATOR)
    if residual.split_required:
        return Decision(Action.SPLIT)
    if residual.merge_required:
        return Decision(Action.MERGE)
    if len(residual.plausible_causes)==1:
        c=residual.plausible_causes[0]
        mapping={
            Coordinate.QUESTION:Action.REFRAME_QUESTION,
            Coordinate.FRAMEWORK:Action.CHALLENGE_FRAMEWORK,
            Coordinate.DECOMPOSITION:Action.SPLIT,
            Coordinate.INTERFACE:Action.REPAIR_INTERFACE,
            Coordinate.ATOM:Action.SPLIT,
            Coordinate.MEASUREMENT:Action.REVISE_MEASUREMENT,
            Coordinate.EVALUATOR:Action.AUDIT_EVALUATOR,
            Coordinate.EVIDENCE:Action.SOLVE_CURRENT,
            Coordinate.METHOD:Action.SOLVE_CURRENT,
        }
        return Decision(mapping[c])
    if node.closure_coordinates_pass and not node.material_open_residual:
        return Decision(Action.STOP_BOUNDED)
    return Decision(Action.SOLVE_CURRENT)
