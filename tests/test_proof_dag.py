from __future__ import annotations

import pytest

from rakl.math_research_assurance import ProofReceipt
from rakl.proof_dag import (
    ProofDAG,
    ProofEdge,
    ProofNode,
    ProofNodeKind,
    ProofNodeStatus,
    ProofRelation,
    add_edge,
    add_node,
    all_dependencies_verified,
    dependency_closure,
    refute_node,
    validate_proof_dag,
    verify_checkpoint,
)


def _receipt(statement_hash: str, *, axioms=()) -> ProofReceipt:
    return ProofReceipt(
        theorem_id="T",
        theorem_statement_hash=statement_hash,
        checker="lean",
        checker_version="4.32.1",
        accepted=True,
        axioms=axioms,
        independent_checker="comparator",
        independent_checker_version="pinned",
        independent_accepted=True,
        isolated_recheck=True,
        source_hash=f"proof:{statement_hash}",
    )


def test_dependency_cycle_is_rejected() -> None:
    dag = ProofDAG()
    dag = add_node(dag, ProofNode("A", ProofNodeKind.LEMMA, "a"))
    dag = add_node(dag, ProofNode("B", ProofNodeKind.LEMMA, "b"))
    dag = add_edge(dag, ProofEdge("A", "B", ProofRelation.REQUIRES))
    with pytest.raises(ValueError, match="dependency_cycle"):
        add_edge(dag, ProofEdge("B", "A", ProofRelation.REQUIRES))


def test_verified_checkpoint_requires_exact_statement_hash() -> None:
    dag = add_node(ProofDAG(), ProofNode("L", ProofNodeKind.LEMMA, "lemma-hash"))
    with pytest.raises(ValueError, match="statement hash"):
        verify_checkpoint(dag, node_id="L", receipt=_receipt("other-hash"))


def test_sorry_dependency_cannot_create_verified_checkpoint() -> None:
    dag = add_node(ProofDAG(), ProofNode("L", ProofNodeKind.LEMMA, "lemma-hash"))
    with pytest.raises(ValueError, match="strict assurance"):
        verify_checkpoint(
            dag,
            node_id="L",
            receipt=_receipt("lemma-hash", axioms=("sorryAx",)),
        )


def test_verified_lemma_becomes_persistent_checkpoint() -> None:
    dag = add_node(ProofDAG(), ProofNode("L", ProofNodeKind.LEMMA, "lemma-hash"))
    updated = verify_checkpoint(dag, node_id="L", receipt=_receipt("lemma-hash"))
    assert updated.node_map()["L"].status is ProofNodeStatus.VERIFIED
    assert updated.node_map()["L"].receipt_id == "proof:lemma-hash"


def test_dependency_closure_and_verified_dependency_gate() -> None:
    dag = ProofDAG()
    dag = add_node(
        dag,
        ProofNode(
            "D",
            ProofNodeKind.DEFINITION,
            "definition-hash",
            status=ProofNodeStatus.PROPOSED,
        ),
    )
    dag = add_node(dag, ProofNode("L", ProofNodeKind.LEMMA, "lemma-hash"))
    dag = add_node(dag, ProofNode("T", ProofNodeKind.THEOREM, "theorem-hash"))
    dag = add_edge(dag, ProofEdge("D", "L", ProofRelation.REQUIRES))
    dag = add_edge(dag, ProofEdge("L", "T", ProofRelation.REQUIRES))
    assert dependency_closure(dag, "T") == ("D", "L")
    assert not all_dependencies_verified(dag, node_id="T")
    dag = verify_checkpoint(dag, node_id="L", receipt=_receipt("lemma-hash"))
    assert all_dependencies_verified(dag, node_id="T")


def test_refutation_preserves_node_as_negative_history_object() -> None:
    dag = add_node(ProofDAG(), ProofNode("C", ProofNodeKind.CONJECTURE, "claim-hash"))
    refuted = refute_node(dag, node_id="C", evidence_id="counterexample:17")
    assert refuted.node_map()["C"].status is ProofNodeStatus.REFUTED
    assert refuted.node_map()["C"].receipt_id == "counterexample:17"
    assert validate_proof_dag(refuted).valid
