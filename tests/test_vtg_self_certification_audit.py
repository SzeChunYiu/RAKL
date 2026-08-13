from __future__ import annotations

from scripts.audit_vtg_self_certification import audit_file, audited_paths


def test_registered_vtg_modules_have_no_forbidden_self_certifying_gate():
    problems = []
    for path in audited_paths():
        problems.extend(audit_file(path))
    assert problems == []
