from __future__ import annotations

from rakl.experience_substrate import EpisodeOutcome
from rakl.gluing_learning import gluing_episode_outcome, gluing_residual_signature
from rakl.problem_fibre import LocalSection, ProblemAtom, ProblemDecomposition, glue_local_sections


def test_gluing_conflict_maps_to_failure_residual() -> None:
    decomposition = ProblemDecomposition(
        "P",
        (
            ProblemAtom("A1", "produce x", "ctx", ("x",), ("produce",)),
            ProblemAtom("A2", "consume x", "ctx", ("x",), ("consume",), dependencies=("A1",)),
        ),
    )
    report = glue_local_sections(
        decomposition,
        (
            LocalSection("S1", "A1", (("x", "1"),), (), ("op1",), ("ev1",), True),
            LocalSection("S2", "A2", (("x", "2"),), (), ("op2",), ("ev2",), True),
        ),
    )
    assert gluing_episode_outcome(report) is EpisodeOutcome.FAILURE
    residual = gluing_residual_signature(report)
    assert "gluing:interface_conflict:x:A1:A2" in residual


def test_compatible_but_unverified_gluing_is_partial_success() -> None:
    decomposition = ProblemDecomposition(
        "P",
        (ProblemAtom("A1", "solve", "ctx", ("x",), ("solve",)),),
    )
    report = glue_local_sections(
        decomposition,
        (LocalSection("S1", "A1", (("x", "1"),), (), ("op",), ("ev",), False),),
    )
    assert report.compatible and report.complete_coverage
    assert gluing_episode_outcome(report) is EpisodeOutcome.PARTIAL_SUCCESS
    assert gluing_residual_signature(report) == ("gluing:unverified_local_section",)
