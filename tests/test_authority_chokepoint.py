from __future__ import annotations

from pathlib import Path

from rakl.authority_chokepoint import audit_source_tree


def _write(root: Path, rel: str, body: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _audit_fixture(tmp_path: Path, rel: str, body: str):
    _write(tmp_path, rel, body)
    return audit_source_tree(tmp_path)


def test_registered_gateway_and_protected_runtime_are_allowed(tmp_path):
    _write(
        tmp_path,
        "src/rakl/agent_authority_gateway.py",
        "from .authority_ledger import AuthorityProposal\n"
        "from .v3_scientific_authority import promote_scientific_authority\n"
        "def f():\n    AuthorityProposal()\n    promote_scientific_authority()\n",
    )
    _write(
        tmp_path,
        "src/rakl/v3_scientific_authority.py",
        "def f(ledger):\n"
        "    ledger.commit_verified()\n"
        "    ledger.revoke()\n"
        "    ledger.supersede()\n",
    )
    report = audit_source_tree(tmp_path)
    assert report.passed
    assert report.grants_scientific_authority is False


def test_direct_authority_proposal_bypass_is_detected(tmp_path):
    report = _audit_fixture(
        tmp_path,
        "src/rakl/bypass.py",
        "from .authority_ledger import AuthorityProposal\nAuthorityProposal()\n",
    )
    assert not report.passed
    assert {x.surface for x in report.findings} == {"AuthorityProposal_constructor"}


def test_aliased_authority_proposal_bypass_is_detected(tmp_path):
    report = _audit_fixture(
        tmp_path,
        "src/rakl/bypass.py",
        "from .authority_ledger import AuthorityProposal as AP\nAP()\n",
    )
    assert not report.passed
    assert report.findings[0].surface == "AuthorityProposal_constructor"


def test_module_qualified_authority_proposal_bypass_is_detected(tmp_path):
    report = _audit_fixture(
        tmp_path,
        "src/rakl/bypass.py",
        "import rakl.authority_ledger as al\nal.AuthorityProposal()\n",
    )
    assert not report.passed
    assert report.findings[0].surface == "AuthorityProposal_constructor"


def test_direct_promotion_bypass_is_detected(tmp_path):
    report = _audit_fixture(
        tmp_path,
        "src/rakl/bypass.py",
        "from .v3_scientific_authority import promote_scientific_authority as promote\npromote()\n",
    )
    assert not report.passed
    assert report.findings[0].surface == "promote_scientific_authority_call"


def test_direct_ledger_mutations_are_detected(tmp_path):
    report = _audit_fixture(
        tmp_path,
        "src/rakl/bypass.py",
        "def f(ledger):\n"
        "    ledger.commit_verified()\n"
        "    ledger.revoke()\n"
        "    ledger.supersede()\n",
    )
    assert not report.passed
    assert {x.surface for x in report.findings} == {
        "AuthorityLedger_commit_verified_call",
        "AuthorityLedger_revoke_call",
        "AuthorityLedger_supersede_call",
    }


def test_unparsable_production_source_fails_closed(tmp_path):
    report = _audit_fixture(tmp_path, "src/rakl/broken.py", "def broken(:\n")
    assert not report.passed
    assert report.findings[0].surface == "source_parse"
