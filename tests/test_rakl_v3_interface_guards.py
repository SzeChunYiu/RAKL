from __future__ import annotations

import pytest

from rakl.failure_lattice import FailureDiagnosisStatus
from rakl.failure_learning import FailureDiagnosisRevisionSpec
from rakl.problem_fibre import LocalSection, ProblemAtom, ProblemDecomposition, glue_local_sections


def test_explicit_interface_keys_hide_private_local_assignments() -> None:
    decomposition = ProblemDecomposition(
        "P",
        (
            ProblemAtom(
                "A1",
                "produce shared value",
                "ctx",
                ("shared",),
                ("produce",),
                interface_keys=("shared",),
            ),
            ProblemAtom(
                "A2",
                "consume shared value",
                "ctx",
                ("shared",),
                ("consume",),
                dependencies=("A1",),
                interface_keys=("shared",),
            ),
        ),
    )
    report = glue_local_sections(
        decomposition,
        (
            LocalSection(
                "S1",
                "A1",
                (("shared", "1"), ("private", "left")),
                (),
                ("op1",),
                ("ev1",),
                True,
            ),
            LocalSection(
                "S2",
                "A2",
                (("shared", "1"), ("private", "right")),
                (),
                ("op2",),
                ("ev2",),
                True,
            ),
        ),
    )
    assert report.compatible
    assert report.global_assignments == (("shared", "1"),)
    # Structural compatibility is not a proof certificate.  The deprecated
    # verified booleans cannot grant solution authority.
    assert not report.grants_solution_authority


def test_declared_interface_must_be_present_in_local_section() -> None:
    decomposition = ProblemDecomposition(
        "P",
        (
            ProblemAtom(
                "A1",
                "produce x",
                "ctx",
                ("x",),
                ("produce",),
                interface_keys=("x",),
            ),
        ),
    )
    report = glue_local_sections(
        decomposition,
        (LocalSection("S1", "A1", (("private", "1"),), (), ("op",), ("ev",), True),),
    )
    assert not report.compatible
    assert report.obstructions[0].key == "x"
    assert "absent" in report.obstructions[0].reason


def test_diagnosis_revision_cannot_use_non_active_status() -> None:
    with pytest.raises(ValueError, match="active evidential diagnosis state"):
        FailureDiagnosisRevisionSpec(
            new_failure_id="F2",
            selected_diagnosis="superseded diagnosis",
            diagnosis_status=FailureDiagnosisStatus.SUPERSEDED,
            new_evidence_pointers=("evidence",),
            artifact_hash="sha256:F2",
            timestamp="2026-08-11T09:20:00+00:00",
        )
