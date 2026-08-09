from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import product
from typing import Mapping, Optional, Tuple

from .formalism import FormalEquation, FormalExpression, MechanismEdge, MechanismNode
from .invention import InventionOperator, ResidualSignature, invention_tasks_for_residual


class KnowledgeAtomKind(str, Enum):
    OBSERVABLE = "OBSERVABLE"
    REPRESENTATION = "REPRESENTATION"
    MECHANISM_NODE = "MECHANISM_NODE"
    MECHANISM_EDGE = "MECHANISM_EDGE"
    EQUATION = "EQUATION"
    EXPRESSION = "EXPRESSION"
    ASSUMPTION = "ASSUMPTION"
    REGIME = "REGIME"
    OBSERVATION_MODEL = "OBSERVATION_MODEL"
    COARSE_GRAINING = "COARSE_GRAINING"
    INVARIANT = "INVARIANT"
    SYMMETRY = "SYMMETRY"
    FALSIFIER = "FALSIFIER"
    DATA_PRODUCT = "DATA_PRODUCT"
    INFERENCE_METHOD = "INFERENCE_METHOD"
    QOI = "QOI"
    CAUSAL_RELATION = "CAUSAL_RELATION"
    FAILURE_MOTIF = "FAILURE_MOTIF"
    ANALOGY_MOTIF = "ANALOGY_MOTIF"


@dataclass(frozen=True)
class KnowledgeAtom:
    atom_id: str
    fiber_id: str
    kind: KnowledgeAtomKind
    label: str
    evidence_ids: Tuple[str, ...] = ()
    equation: Optional[FormalEquation] = None
    expression: Optional[FormalExpression] = None
    mechanism_node: Optional[MechanismNode] = None
    mechanism_edge: Optional[MechanismEdge] = None
    payload: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.atom_id or not self.fiber_id or not self.label:
            raise ValueError("atom identity, fiber identity and label are required")
        typed_payloads = sum(
            item is not None
            for item in (
                self.equation,
                self.expression,
                self.mechanism_node,
                self.mechanism_edge,
            )
        )
        if typed_payloads > 1:
            raise ValueError("a lattice atom may own at most one primary typed payload")
        expected = {
            KnowledgeAtomKind.EQUATION: self.equation,
            KnowledgeAtomKind.EXPRESSION: self.expression,
            KnowledgeAtomKind.MECHANISM_NODE: self.mechanism_node,
            KnowledgeAtomKind.MECHANISM_EDGE: self.mechanism_edge,
        }
        if self.kind in expected and expected[self.kind] is None:
            raise ValueError(f"typed payload required for atom kind {self.kind.value}")


class LatticeCompatibility(str, Enum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    CONDITIONAL = "CONDITIONAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CompatibilityWitness:
    left_atom_id: str
    right_atom_id: str
    relation: LatticeCompatibility
    reason: str
    condition: Optional[str] = None
    evidence_ids: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.left_atom_id or not self.right_atom_id or not self.reason:
            raise ValueError("compatibility witness identities and reason are required")
        if self.relation is LatticeCompatibility.CONDITIONAL and not self.condition:
            raise ValueError("conditional compatibility requires an explicit condition")


@dataclass(frozen=True)
class ConstructiveLatticePath:
    path_id: str
    atom_ids: Tuple[str, ...]
    conditions: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    source_fiber_ids: Tuple[str, ...]


@dataclass(frozen=True)
class LatticeSynthesisSeed:
    seed_id: str
    path: ConstructiveLatticePath
    residual_id: str
    suggested_operators: Tuple[InventionOperator, ...]
    typed_equation_ids: Tuple[str, ...]
    mechanism_node_ids: Tuple[str, ...]
    mechanism_edge_ids: Tuple[str, ...]
    prompt: str


@dataclass
class TypedKnowledgeLattice:
    atoms: dict[str, KnowledgeAtom]
    witnesses: dict[frozenset[str], CompatibilityWitness]

    @classmethod
    def empty(cls) -> "TypedKnowledgeLattice":
        return cls({}, {})

    def add_atom(self, atom: KnowledgeAtom) -> None:
        existing = self.atoms.get(atom.atom_id)
        if existing is not None and existing != atom:
            raise ValueError(f"knowledge atom identity is immutable: {atom.atom_id}")
        self.atoms[atom.atom_id] = atom

    def add_witness(self, witness: CompatibilityWitness) -> None:
        if witness.left_atom_id not in self.atoms or witness.right_atom_id not in self.atoms:
            raise KeyError("compatibility witness references unknown atom")
        key = frozenset((witness.left_atom_id, witness.right_atom_id))
        existing = self.witnesses.get(key)
        if existing is not None and existing != witness:
            raise ValueError("conflicting compatibility witness for atom pair")
        self.witnesses[key] = witness

    def compatibility(self, left: str, right: str) -> LatticeCompatibility:
        if left == right:
            return LatticeCompatibility.COMPATIBLE
        witness = self.witnesses.get(frozenset((left, right)))
        return witness.relation if witness is not None else LatticeCompatibility.UNKNOWN

    def _path_status(self, atom_ids: Tuple[str, ...], *, allow_unknown: bool) -> tuple[bool, Tuple[str, ...], Tuple[str, ...]]:
        conditions: list[str] = []
        evidence: list[str] = []
        for i, left in enumerate(atom_ids):
            for right in atom_ids[i + 1 :]:
                witness = self.witnesses.get(frozenset((left, right)))
                if witness is None:
                    if not allow_unknown:
                        return False, (), ()
                    continue
                if witness.relation is LatticeCompatibility.INCOMPATIBLE:
                    return False, (), ()
                if witness.relation is LatticeCompatibility.UNKNOWN and not allow_unknown:
                    return False, (), ()
                if witness.relation is LatticeCompatibility.CONDITIONAL and witness.condition:
                    conditions.append(witness.condition)
                evidence.extend(witness.evidence_ids)
        return True, tuple(dict.fromkeys(conditions)), tuple(dict.fromkeys(evidence))

    def construct_paths(
        self,
        required_kinds: Tuple[KnowledgeAtomKind, ...],
        *,
        max_paths: int = 256,
        allow_unknown: bool = False,
    ) -> Tuple[ConstructiveLatticePath, ...]:
        if not required_kinds:
            raise ValueError("required_kinds cannot be empty")
        pools = [
            tuple(atom for atom in self.atoms.values() if atom.kind is kind)
            for kind in required_kinds
        ]
        if any(not pool for pool in pools):
            return ()
        paths: list[ConstructiveLatticePath] = []
        for index, combination in enumerate(product(*pools)):
            atom_ids = tuple(atom.atom_id for atom in combination)
            if len(atom_ids) != len(set(atom_ids)):
                continue
            admissible, conditions, relation_evidence = self._path_status(
                atom_ids,
                allow_unknown=allow_unknown,
            )
            if not admissible:
                continue
            atom_evidence = tuple(
                dict.fromkeys(
                    evidence_id
                    for atom in combination
                    for evidence_id in atom.evidence_ids
                )
            )
            paths.append(
                ConstructiveLatticePath(
                    path_id=f"path:{index}",
                    atom_ids=atom_ids,
                    conditions=conditions,
                    evidence_ids=tuple(dict.fromkeys(atom_evidence + relation_evidence)),
                    source_fiber_ids=tuple(dict.fromkeys(atom.fiber_id for atom in combination)),
                )
            )
            if len(paths) >= max_paths:
                break
        return tuple(paths)

    def synthesis_seeds(
        self,
        residual: ResidualSignature,
        required_kinds: Tuple[KnowledgeAtomKind, ...],
        *,
        max_paths: int = 64,
        allow_unknown: bool = False,
    ) -> Tuple[LatticeSynthesisSeed, ...]:
        paths = self.construct_paths(
            required_kinds,
            max_paths=max_paths,
            allow_unknown=allow_unknown,
        )
        operators = tuple(
            dict.fromkeys(task.operator for task in invention_tasks_for_residual(residual, max_operators=12))
        )
        seeds = []
        for index, path in enumerate(paths):
            atoms = [self.atoms[atom_id] for atom_id in path.atom_ids]
            equations = tuple(
                atom.equation.equation_id
                for atom in atoms
                if atom.equation is not None
            )
            nodes = tuple(
                atom.mechanism_node.node_id
                for atom in atoms
                if atom.mechanism_node is not None
            )
            edges = tuple(
                atom.mechanism_edge.edge_id
                for atom in atoms
                if atom.mechanism_edge is not None
            )
            labels = "; ".join(f"{atom.kind.value}:{atom.label}" for atom in atoms)
            seeds.append(
                LatticeSynthesisSeed(
                    seed_id=f"seed:{residual.residual_id}:{index}",
                    path=path,
                    residual_id=residual.residual_id,
                    suggested_operators=operators,
                    typed_equation_ids=equations,
                    mechanism_node_ids=nodes,
                    mechanism_edge_ids=edges,
                    prompt=(
                        f"Construct a typed theory delta for residual {residual.residual_id} using "
                        f"this compatibility-witnessed lattice path: {labels}. Preserve path conditions "
                        f"{path.conditions}; do not exceed the evidence supported by {path.evidence_ids}."
                    ),
                )
            )
        return tuple(seeds)


def atoms_by_kind(lattice: TypedKnowledgeLattice) -> Mapping[KnowledgeAtomKind, Tuple[KnowledgeAtom, ...]]:
    output: dict[KnowledgeAtomKind, list[KnowledgeAtom]] = {}
    for atom in lattice.atoms.values():
        output.setdefault(atom.kind, []).append(atom)
    return {kind: tuple(values) for kind, values in output.items()}
