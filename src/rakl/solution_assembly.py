from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Tuple

from .math_research_assurance import AssuranceVerdict, ProofReceipt, audit_proof_receipt
from .proof_dag import ProofDAG, ProofNodeStatus, ProofRelation, all_dependencies_verified, dependency_closure, validate_proof_dag


def proof_dag_content_hash(dag: ProofDAG) -> str:
    payload = {
        "schema": "orion.proof_dag.content.v1",
        "nodes": [{"node_id": node.node_id, "kind": node.kind.value, "statement_hash": node.statement_hash, "status": node.status.value, "receipt_id": node.receipt_id, "notes": list(node.notes)} for node in sorted(dag.nodes, key=lambda item: item.node_id)],
        "edges": [{"source": edge.source, "target": edge.target, "relation": edge.relation.value} for edge in sorted(dag.edges, key=lambda item: (item.source, item.target, item.relation.value))],
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class AssemblyVerdict(str, Enum):
    READY_FOR_EXTERNAL_AUTHORITY_GATE = "READY_FOR_EXTERNAL_AUTHORITY_GATE"
    INCOMPLETE = "INCOMPLETE"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SolutionAssemblyReceipt:
    assembly_id: str
    root_node_id: str
    trajectory_episode_ids: Tuple[str, ...]
    selected_node_ids: Tuple[str, ...]
    discarded_branch_ids: Tuple[str, ...]
    proof_dag_hash: str
    certificate_artifact_hash: str
    proof_receipt: ProofReceipt | None

    def __post_init__(self) -> None:
        if not all((self.assembly_id, self.root_node_id, self.proof_dag_hash, self.certificate_artifact_hash)):
            raise ValueError("solution assembly requires bound identities")
        if len(set(self.trajectory_episode_ids)) != len(self.trajectory_episode_ids):
            raise ValueError("trajectory episode ids must be unique")
        if len(set(self.selected_node_ids)) != len(self.selected_node_ids):
            raise ValueError("selected node ids must be unique")

    @property
    def grants_solution_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SolutionAssemblyReport:
    verdict: AssemblyVerdict
    reasons: Tuple[str, ...]

    @property
    def grants_solution_authority(self) -> bool:
        return False


def validate_solution_assembly(dag: ProofDAG, receipt: SolutionAssemblyReceipt) -> SolutionAssemblyReport:
    dag_report = validate_proof_dag(dag)
    if not dag_report.valid:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("invalid_proof_dag",) + dag_report.reasons)
    if receipt.proof_dag_hash != proof_dag_content_hash(dag):
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("proof_dag_hash_mismatch",))
    node_map = dag.node_map()
    if receipt.root_node_id not in node_map:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("root_node_missing",))
    if set(receipt.selected_node_ids) - set(node_map):
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("selected_node_missing",))
    required = set(dependency_closure(dag, receipt.root_node_id)) | {receipt.root_node_id}
    # Conflict-freeness integrity constraint (audit U5a): no node inside the
    # certificate scope (root, its dependency closure, or the selected set) may
    # be VERIFIED while a VERIFIED node REFUTES it. A certificate asserting both
    # |-P and |-not-P is internally inconsistent and must fail closed before the
    # positive checks can report READY.
    conflict_scope = required | set(receipt.selected_node_ids)
    for edge in dag.edges:
        if edge.relation is not ProofRelation.REFUTES or edge.target not in conflict_scope:
            continue
        refuter = node_map.get(edge.source)
        refuted = node_map.get(edge.target)
        if (
            refuter is not None
            and refuted is not None
            and refuter.status is ProofNodeStatus.VERIFIED
            and refuted.status is ProofNodeStatus.VERIFIED
        ):
            return SolutionAssemblyReport(
                AssemblyVerdict.REJECT,
                ("verified_refutation_conflict", f"refutes_edge:{edge.source}->{edge.target}"),
            )
    if not required.issubset(set(receipt.selected_node_ids)):
        return SolutionAssemblyReport(AssemblyVerdict.INCOMPLETE, ("selected_nodes_do_not_cover_root_dependency_closure",))
    if not all_dependencies_verified(dag, node_id=receipt.root_node_id):
        return SolutionAssemblyReport(AssemblyVerdict.INCOMPLETE, ("root_dependencies_not_verified",))
    root = node_map[receipt.root_node_id]
    if root.status is not ProofNodeStatus.VERIFIED:
        return SolutionAssemblyReport(AssemblyVerdict.INCOMPLETE, ("root_node_not_verified",))
    if receipt.proof_receipt is None:
        return SolutionAssemblyReport(AssemblyVerdict.CANNOT_CHECK, ("proof_receipt_missing",))
    proof = receipt.proof_receipt
    if proof.theorem_id != receipt.root_node_id:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("proof_receipt_root_identity_mismatch",))
    if proof.theorem_statement_hash != root.statement_hash:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("proof_receipt_statement_hash_mismatch",))
    if proof.source_hash != receipt.certificate_artifact_hash:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("proof_receipt_source_hash_not_bound_to_certificate_artifact",))
    proof_audit = audit_proof_receipt(proof)
    if proof_audit.verdict is AssuranceVerdict.CANNOT_CHECK:
        return SolutionAssemblyReport(AssemblyVerdict.CANNOT_CHECK, ("proof_receipt_cannot_check",) + proof_audit.reasons)
    if proof_audit.verdict is AssuranceVerdict.FAIL:
        return SolutionAssemblyReport(AssemblyVerdict.REJECT, ("proof_receipt_assurance_failed",) + proof_audit.reasons)
    return SolutionAssemblyReport(
        AssemblyVerdict.READY_FOR_EXTERNAL_AUTHORITY_GATE,
        (
            "proof_dag_valid",
            "root_dependency_closure_selected",
            "dependencies_verified",
            "root_verified",
            "proof_receipt_bound_to_root_statement_and_certificate_artifact",
            "proof_receipt_and_trust_audit_passed",
            "ordinary_authority_gate_still_required",
        ),
    )
