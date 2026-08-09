from rakl.formalism import (
    EquationKind,
    FormalEquation,
    FormalExpression,
    MechanismEdge,
    MechanismNode,
    MechanismNodeKind,
    MechanismRelation,
)
from rakl.invention import ResidualKind, ResidualSignature
from rakl.typed_lattice import (
    CompatibilityWitness,
    KnowledgeAtom,
    KnowledgeAtomKind,
    LatticeCompatibility,
    TypedKnowledgeLattice,
)


def _lattice():
    lattice = TypedKnowledgeLattice.empty()
    equation = FormalEquation(
        "eq-flow",
        FormalExpression.sym("r"),
        FormalExpression.sym("q"),
        EquationKind.STRUCTURAL,
    )
    node = MechanismNode("n-flow", MechanismNodeKind.OBSERVABLE, "flow", symbol="q")
    edge = MechanismEdge("e-flow", "n-flow", "n-return", MechanismRelation.CAUSES)
    atoms = (
        KnowledgeAtom("a-eq", "fiber:repr", KnowledgeAtomKind.EQUATION, "flow law", equation=equation, evidence_ids=("paper:1",)),
        KnowledgeAtom("a-node", "fiber:mechanism", KnowledgeAtomKind.MECHANISM_NODE, "flow node", mechanism_node=node, evidence_ids=("paper:2",)),
        KnowledgeAtom("a-edge", "fiber:mechanism", KnowledgeAtomKind.MECHANISM_EDGE, "flow causes return", mechanism_edge=edge, evidence_ids=("paper:2",)),
        KnowledgeAtom("a-regime", "fiber:regime", KnowledgeAtomKind.REGIME, "high-volatility regime", evidence_ids=("paper:3",)),
    )
    for atom in atoms:
        lattice.add_atom(atom)
    for left, right in (("a-eq", "a-node"), ("a-eq", "a-regime"), ("a-node", "a-regime")):
        lattice.add_witness(
            CompatibilityWitness(left, right, LatticeCompatibility.COMPATIBLE, "aligned scope", evidence_ids=("map:1",))
        )
    return lattice


def test_constructive_paths_require_compatibility_witnesses():
    lattice = _lattice()
    paths = lattice.construct_paths(
        (KnowledgeAtomKind.EQUATION, KnowledgeAtomKind.MECHANISM_NODE, KnowledgeAtomKind.REGIME)
    )
    assert len(paths) == 1
    assert set(paths[0].atom_ids) == {"a-eq", "a-node", "a-regime"}
    assert {"paper:1", "paper:2", "paper:3", "map:1"}.issubset(paths[0].evidence_ids)


def test_missing_pair_witness_prevents_strict_path():
    lattice = _lattice()
    assert lattice.construct_paths(
        (KnowledgeAtomKind.EQUATION, KnowledgeAtomKind.MECHANISM_EDGE, KnowledgeAtomKind.REGIME)
    ) == ()


def test_lattice_path_becomes_residual_specific_synthesis_seed():
    lattice = _lattice()
    residual = ResidualSignature(
        "r1",
        (ResidualKind.REGIME, ResidualKind.PREDICTIVE),
        "prediction fails specifically in high-volatility states",
    )
    seeds = lattice.synthesis_seeds(
        residual,
        (KnowledgeAtomKind.EQUATION, KnowledgeAtomKind.MECHANISM_NODE, KnowledgeAtomKind.REGIME),
    )
    assert len(seeds) == 1
    assert seeds[0].typed_equation_ids == ("eq-flow",)
    assert seeds[0].mechanism_node_ids == ("n-flow",)
    assert seeds[0].suggested_operators
