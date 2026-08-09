def test_constructive_invention_public_facade_imports():
    from rakl.invention_api import (
        ConstructiveKnowledgeState,
        InventionRuntime,
        PositiveGoalContract,
        SymbolicDiscoverySpec,
        TypedKnowledgeLattice,
        compile_mechanism_equations,
        polymarket_crypto_spot_gate_contract,
    )

    assert ConstructiveKnowledgeState is not None
    assert InventionRuntime is not None
    assert PositiveGoalContract is not None
    assert SymbolicDiscoverySpec is not None
    assert TypedKnowledgeLattice is not None
    assert compile_mechanism_equations is not None
    assert polymarket_crypto_spot_gate_contract().requirements
