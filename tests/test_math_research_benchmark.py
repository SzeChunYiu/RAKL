from pathlib import Path

from rakl.math_research_benchmark import run_benchmark


def test_hostile_math_research_assurance_benchmark_passes():
    benchmark = (
        Path(__file__).resolve().parents[1]
        / "benchmarks"
        / "math_research_assurance"
        / "tasks_v0.json"
    )
    result = run_benchmark(benchmark)
    assert result["task_count"] == 10
    assert result["failed"] == 0, result["results"]
    assert result["all_passed"] is True
