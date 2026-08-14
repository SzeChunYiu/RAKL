from __future__ import annotations

import json

import paper2_robustness_confirmatory as confirmatory


SMOKE_SEED = 20260812993


if __name__ == "__main__":
    result = confirmatory.summarize(
        seed=SMOKE_SEED,
        n_per_cell=2,
        bootstrap_reps=200,
        bootstrap_seed=993,
    )
    assert result["seed"] == SMOKE_SEED
    assert result["seed"] != confirmatory.CONFIRMATORY_SEED
    assert result["n"] == 108
    print(json.dumps({
        "status": "ENTRYPOINT_IMPORT_AND_ANALYSIS_SMOKE_PASS",
        "seed": result["seed"],
        "n": result["n"],
        "confirmatory_seed_not_accessed": True,
    }, sort_keys=True))
