from __future__ import annotations
import pytest
from rakl.math_research_assurance import ProofReceipt
from rakl.proof_dag import ProofDAG, ProofEdge, ProofNode, ProofNodeKind, ProofRelation, add_edge
from rakl.proof_dag_v2 import DependencyManifestReceipt, dag_dependency_statement_hashes, verify_checkpoint_with_dependency_manifest


def _node(n, statement, kind=ProofNodeKind.LEMMA): return ProofNode(n,kind,statement)
def _dag(include_b=True):
    dag=ProofDAG(nodes=(_node("A","hash-A"),_node("B","hash-B"),_node("T","hash-T",ProofNodeKind.THEOREM)))
    dag=add_edge(dag,ProofEdge("A","T",ProofRelation.IMPLIES))
    if include_b: dag=add_edge(dag,ProofEdge("B","T",ProofRelation.IMPLIES))
    return dag

def _proof(source="proof-T"):
    return ProofReceipt("T","hash-T","lean","4.32.1",True,(),"comparator","pinned",True,True,source)

def _manifest(deps=("hash-A","hash-B"), source="proof-T"):
    return DependencyManifestReceipt("manifest-T",source,"hash-T",deps,"lean-environment-dependency-extractor",True)

def test_omitted_real_dependency_is_rejected_even_when_dag_shape_is_valid():
    dag=_dag(include_b=False)
    assert dag_dependency_statement_hashes(dag,"T") == ("hash-A",)
    with pytest.raises(ValueError,match="missing=.*hash-B"):
        verify_checkpoint_with_dependency_manifest(dag,node_id="T",receipt=_proof(),manifest=_manifest())

def test_extra_dag_dependency_not_in_proof_manifest_is_rejected():
    dag=_dag(include_b=True)
    with pytest.raises(ValueError,match="extra=.*hash-B"):
        verify_checkpoint_with_dependency_manifest(dag,node_id="T",receipt=_proof(),manifest=_manifest(("hash-A",)))

def test_dependency_manifest_cannot_be_reused_across_proof_source():
    with pytest.raises(ValueError,match="proof-source mismatch"):
        verify_checkpoint_with_dependency_manifest(_dag(),node_id="T",receipt=_proof("proof-new"),manifest=_manifest(source="proof-old"))

def test_exact_manifest_allows_existing_strict_checkpoint_verification():
    verified=verify_checkpoint_with_dependency_manifest(_dag(),node_id="T",receipt=_proof(),manifest=_manifest())
    assert verified.node_map()["T"].receipt_id == "proof-T"
    assert _manifest().grants_scientific_authority is False
