from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Tuple

from .math_research_assurance import AssuranceVerdict, ProofReceipt, audit_proof_receipt


class ProofNodeKind(str, Enum):
    DEFINITION = "DEFINITION"
    CONJECTURE = "CONJECTURE"
    LEMMA = "LEMMA"
    THEOREM = "THEOREM"
    COUNTEREXAMPLE = "COUNTEREXAMPLE"
    COMPUTATION = "COMPUTATION"
    REPRESENTATION = "REPRESENTATION"
    PROOF_OBLIGATION = "PROOF_OBLIGATION"
    IMPORTED_THEOREM = "IMPORTED_THEOREM"


class ProofNodeStatus(str, Enum):
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    BLOCKED = "BLOCKED"


class ProofRelation(str, Enum):
    REQUIRES = "REQUIRES"
    IMPLIES = "IMPLIES"
    REDUCES_TO = "REDUCES_TO"
    REFUTES = "REFUTES"
    SPECIALIZES = "SPECIALIZES"
    GENERALIZES = "GENERALIZES"


DEPENDENCY_RELATIONS = frozenset(
    {ProofRelation.REQUIRES, ProofRelation.IMPLIES, ProofRelation.REDUCES_TO}
)


@dataclass(frozen=True)
class ProofNode:
    node_id: str
    kind: ProofNodeKind
    statement_hash: str
    status: ProofNodeStatus = ProofNodeStatus.PROPOSED
    receipt_id: str | None = None
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.node_id or not self.statement_hash:
            raise ValueError("proof nodes require node and statement identities")
        if self.status is ProofNodeStatus.VERIFIED and not self.receipt_id:
            raise ValueError("verified nodes require a receipt identity")


@dataclass(frozen=True)
class ProofEdge:
    source: str
    target: str
    relation: ProofRelation


@dataclass(frozen=True)
class ProofDAG:
    nodes: Tuple[ProofNode, ...] = ()
    edges: Tuple[ProofEdge, ...] = ()

    def node_map(self) -> dict[str, ProofNode]:
        return {node.node_id: node for node in self.nodes}


@dataclass(frozen=True)
class ProofDAGReport:
    valid: bool
    reasons: Tuple[str, ...]


def validate_proof_dag(dag: ProofDAG) -> ProofDAGReport:
    reasons: list[str] = []
    node_map = dag.node_map()
    if len(node_map) != len(dag.nodes):
        reasons.append("duplicate_proof_node_id")

    for edge in dag.edges:
        if edge.source not in node_map:
            reasons.append(f"missing_edge_source:{edge.source}")
        if edge.target not in node_map:
            reasons.append(f"missing_edge_target:{edge.target}")

    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_map}
    for edge in dag.edges:
        if (
            edge.relation in DEPENDENCY_RELATIONS
            and edge.source in node_map
            and edge.target in node_map
        ):
            adjacency[edge.source].append(edge.target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited or "dependency_cycle" in reasons:
            return
        if node_id in visiting:
            reasons.append("dependency_cycle")
            return
        visiting.add(node_id)
        for child in adjacency[node_id]:
            visit(child)
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in adjacency:
        visit(node_id)

    return ProofDAGReport(not reasons, tuple(reasons))


def add_node(dag: ProofDAG, node: ProofNode) -> ProofDAG:
    if node.node_id in dag.node_map():
        raise ValueError(f"duplicate proof node {node.node_id!r}")
    return replace(dag, nodes=dag.nodes + (node,))


def add_edge(dag: ProofDAG, edge: ProofEdge) -> ProofDAG:
    node_map = dag.node_map()
    if edge.source not in node_map or edge.target not in node_map:
        raise ValueError("proof edge endpoints must already exist")
    candidate = replace(dag, edges=dag.edges + (edge,))
    report = validate_proof_dag(candidate)
    if not report.valid:
        raise ValueError(";".join(report.reasons))
    return candidate


def verify_checkpoint(
    dag: ProofDAG,
    *,
    node_id: str,
    receipt: ProofReceipt,
) -> ProofDAG:
    """Promote one exact node to a persistent verified checkpoint.

    The receipt must pass the strict proof audit and its statement hash must match
    the node.  This changes only that node; failed/rejected branches remain in the
    DAG and are not deleted.
    """

    node_map = dag.node_map()
    if node_id not in node_map:
        raise ValueError(f"unknown proof node {node_id!r}")
    node = node_map[node_id]
    if receipt.theorem_statement_hash != node.statement_hash:
        raise ValueError("proof receipt statement hash does not match DAG node")
    audit = audit_proof_receipt(receipt)
    if audit.verdict is not AssuranceVerdict.PASS:
        raise ValueError("proof receipt failed strict assurance: " + ",".join(audit.reasons))

    verified = replace(
        node,
        status=ProofNodeStatus.VERIFIED,
        receipt_id=receipt.source_hash,
    )
    nodes = tuple(verified if item.node_id == node_id else item for item in dag.nodes)
    return replace(dag, nodes=nodes)


def refute_node(dag: ProofDAG, *, node_id: str, evidence_id: str) -> ProofDAG:
    if not evidence_id:
        raise ValueError("refutation requires evidence identity")
    node_map = dag.node_map()
    if node_id not in node_map:
        raise ValueError(f"unknown proof node {node_id!r}")
    node = node_map[node_id]
    refuted = replace(
        node,
        status=ProofNodeStatus.REFUTED,
        receipt_id=evidence_id,
    )
    nodes = tuple(refuted if item.node_id == node_id else item for item in dag.nodes)
    return replace(dag, nodes=nodes)


def dependency_closure(dag: ProofDAG, node_id: str) -> Tuple[str, ...]:
    node_map = dag.node_map()
    if node_id not in node_map:
        raise ValueError(f"unknown proof node {node_id!r}")
    reverse: dict[str, list[str]] = {item: [] for item in node_map}
    for edge in dag.edges:
        if edge.relation in DEPENDENCY_RELATIONS:
            # source is a premise/input for target under the convention used by
            # the runtime, so traverse backwards from conclusion to premises.
            reverse[edge.target].append(edge.source)
    found: set[str] = set()
    stack = list(reverse[node_id])
    while stack:
        current = stack.pop()
        if current in found:
            continue
        found.add(current)
        stack.extend(reverse[current])
    return tuple(sorted(found))


def all_dependencies_verified(
    dag: ProofDAG,
    *,
    node_id: str,
    exempt_kinds: Iterable[ProofNodeKind] = (ProofNodeKind.DEFINITION,),
) -> bool:
    node_map = dag.node_map()
    exempt = frozenset(exempt_kinds)
    for dependency_id in dependency_closure(dag, node_id):
        node = node_map[dependency_id]
        if node.kind in exempt:
            continue
        if node.status is not ProofNodeStatus.VERIFIED:
            return False
    return True
