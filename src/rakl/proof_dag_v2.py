"""Dependency-manifest hardening for Paper V's persistent ProofDAG."""
from __future__ import annotations
from dataclasses import dataclass
from .math_research_assurance import ProofReceipt
from .proof_dag import ProofDAG, dependency_closure, verify_checkpoint

@dataclass(frozen=True)
class DependencyManifestReceipt:
    manifest_id: str
    proof_source_hash: str
    theorem_statement_hash: str
    dependency_statement_hashes: tuple[str, ...]
    extracted_by: str
    extracted_before_checkpoint_promotion: bool
    def __post_init__(self):
        for n in ("manifest_id","proof_source_hash","theorem_statement_hash","extracted_by"):
            if not getattr(self,n).strip(): raise ValueError(f"{n} cannot be blank")
        if any(not x.strip() for x in self.dependency_statement_hashes): raise ValueError("dependency hashes cannot be blank")
        if len(set(self.dependency_statement_hashes)) != len(self.dependency_statement_hashes): raise ValueError("dependency manifest contains duplicate statement hashes")
    @property
    def grants_scientific_authority(self): return False


def dag_dependency_statement_hashes(dag: ProofDAG, node_id: str) -> tuple[str, ...]:
    nodes=dag.node_map()
    return tuple(sorted({nodes[x].statement_hash for x in dependency_closure(dag,node_id)}))


def verify_checkpoint_with_dependency_manifest(dag: ProofDAG, *, node_id: str, receipt: ProofReceipt, manifest: DependencyManifestReceipt) -> ProofDAG:
    """Verify only when proof-source and exact transitive DAG dependencies agree."""
    node=dag.node_map().get(node_id)
    if node is None: raise ValueError(f"unknown proof node {node_id!r}")
    if receipt.source_hash != manifest.proof_source_hash: raise ValueError("dependency manifest proof-source mismatch")
    if receipt.theorem_statement_hash != manifest.theorem_statement_hash: raise ValueError("dependency manifest theorem-statement mismatch")
    if node.statement_hash != manifest.theorem_statement_hash: raise ValueError("dependency manifest not bound to target DAG statement")
    if manifest.extracted_before_checkpoint_promotion is not True: raise ValueError("dependency manifest was not frozen before checkpoint promotion")
    dag_hashes=dag_dependency_statement_hashes(dag,node_id)
    manifest_hashes=tuple(sorted(manifest.dependency_statement_hashes))
    if dag_hashes != manifest_hashes:
        missing=tuple(sorted(set(manifest_hashes)-set(dag_hashes)))
        extra=tuple(sorted(set(dag_hashes)-set(manifest_hashes)))
        raise ValueError(f"dependency manifest mismatch; missing={missing}; extra={extra}")
    return verify_checkpoint(dag,node_id=node_id,receipt=receipt)
