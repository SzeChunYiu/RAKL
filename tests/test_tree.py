from rakl.tree import (
    BranchMetrics,
    ResearchNode,
    ResearchNodeStatus,
    ResearchTree,
)


def test_tree_preserves_refuted_history_and_children():
    tree = ResearchTree()
    tree.add_node(ResearchNode("root", "F", "baseline"))
    tree.add_node(ResearchNode("a", "F", "mechanism A", parent_id="root"))
    tree.add_node(ResearchNode("b", "F", "mechanism B", parent_id="root"))
    tree.set_status("a", ResearchNodeStatus.REFUTED, evidence_id="receipt-a")

    assert tree.nodes["a"].status == ResearchNodeStatus.REFUTED
    assert tree.nodes["a"].evidence_ids == ["receipt-a"]
    assert set(tree.nodes["root"].child_ids) == {"a", "b"}
    assert "a" in tree.nodes


def test_pareto_frontier_does_not_collapse_tradeoffs_to_one_score():
    tree = ResearchTree()
    tree.add_node(
        ResearchNode(
            "fast",
            "F",
            "cheap discriminator",
            mechanism_family="M1",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(
                expected_information_gain=4,
                decision_impact=3,
                semantic_novelty=2,
                cost=1,
                authority_risk=0.1,
            ),
        )
    )
    tree.add_node(
        ResearchNode(
            "deep",
            "F",
            "deep discriminator",
            mechanism_family="M2",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(
                expected_information_gain=9,
                decision_impact=8,
                semantic_novelty=6,
                cost=8,
                authority_risk=0.2,
            ),
        )
    )

    frontier = {node.node_id for node in tree.pareto_frontier()}
    assert frontier == {"fast", "deep"}


def test_dominated_branch_can_leave_frontier_without_being_deleted():
    tree = ResearchTree()
    tree.add_node(
        ResearchNode(
            "weak",
            "F",
            "weak",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(1, 1, 1, 5, 0.5),
        )
    )
    tree.add_node(
        ResearchNode(
            "strong",
            "F",
            "strong",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(2, 2, 2, 4, 0.4),
        )
    )
    assert [node.node_id for node in tree.pareto_frontier()] == ["strong"]
    assert "weak" in tree.nodes


def test_diverse_frontier_keeps_distinct_mechanism_families():
    tree = ResearchTree()
    tree.add_node(
        ResearchNode(
            "m1",
            "F",
            "one",
            mechanism_family="M1",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(4, 4, 4, 2, 0.1),
        )
    )
    tree.add_node(
        ResearchNode(
            "m2",
            "F",
            "two",
            mechanism_family="M2",
            status=ResearchNodeStatus.ACTIVE,
            metrics=BranchMetrics(5, 3, 5, 3, 0.1),
        )
    )
    families = {node.mechanism_family for node in tree.diverse_frontier()}
    assert families == {"M1", "M2"}
