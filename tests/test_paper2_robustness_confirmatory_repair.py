from __future__ import annotations

import subprocess
import sys

from rakl.objective_transfer_robustness import generate
from rakl.robustness_analysis import (
    binary_probability as repaired_binary_probability,
    brier as repaired_brier,
    lexical_predict as repaired_lexical_predict,
    twin_predict as repaired_twin_predict,
)
from scripts.paper2_robustness_development import (
    binary_probability as frozen_binary_probability,
    brier as frozen_brier,
    lexical_predict as frozen_lexical_predict,
    twin_predict as frozen_twin_predict,
)


def test_repaired_shared_helpers_match_frozen_development_helpers() -> None:
    tasks = generate(20260812994, n_per_cell=1)
    threshold = 0.40064102564102566
    for task in tasks:
        assert repaired_twin_predict(task) is frozen_twin_predict(task)
        assert repaired_lexical_predict(task, threshold) is frozen_lexical_predict(task, threshold)
        for decision in (
            repaired_twin_predict(task),
            repaired_lexical_predict(task, threshold),
        ):
            assert repaired_binary_probability(decision) == frozen_binary_probability(decision)
        gold = __import__("rakl.objective_transfer_robustness", fromlist=["verify"]).verify(task)
        if gold.value != "CANNOT_CHECK":
            p = repaired_binary_probability(repaired_twin_predict(task))
            assert repaired_brier(p, gold) == frozen_brier(p, gold)


def test_repaired_script_entrypoint_runs_fresh_smoke_without_confirmatory_seed() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/paper2_robustness_confirmatory_smoke.py"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "ENTRYPOINT_IMPORT_AND_ANALYSIS_SMOKE_PASS" in proc.stdout
    assert '"confirmatory_seed_not_accessed": true' in proc.stdout.lower()
