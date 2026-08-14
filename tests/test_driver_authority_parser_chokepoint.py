from __future__ import annotations

from pathlib import Path

from rakl.authority_chokepoint import audit_source_tree


def _write(root: Path, rel: str, body: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_registered_learning_turn_is_only_allowed_raw_agent_parser_caller(tmp_path):
    _write(
        tmp_path,
        "src/rakl/driver_learning.py",
        "from .agent_authority_gateway import parse_raw_untrusted_agent_authority_json\n"
        "def f(raw):\n    return parse_raw_untrusted_agent_authority_json(raw)\n",
    )
    report = audit_source_tree(tmp_path)
    assert report.passed


def test_second_production_raw_agent_parser_path_is_detected(tmp_path):
    _write(
        tmp_path,
        "src/rakl/driver_learning.py",
        "from .agent_authority_gateway import parse_raw_untrusted_agent_authority_json\n"
        "def f(raw):\n    return parse_raw_untrusted_agent_authority_json(raw)\n",
    )
    _write(
        tmp_path,
        "src/rakl/alternate_model_runtime.py",
        "from .agent_authority_gateway import parse_raw_untrusted_agent_authority_json as parse\n"
        "def g(raw):\n    return parse(raw)\n",
    )
    report = audit_source_tree(tmp_path)
    assert not report.passed
    assert len(report.findings) == 1
    assert report.findings[0].surface == "raw_agent_authority_parser_call"
    assert report.findings[0].path == "src/rakl/alternate_model_runtime.py"


def test_module_qualified_second_parser_path_is_detected(tmp_path):
    _write(
        tmp_path,
        "src/rakl/bypass.py",
        "import rakl.agent_authority_gateway as gateway\n"
        "def g(raw):\n    return gateway.parse_raw_untrusted_agent_authority_json(raw)\n",
    )
    report = audit_source_tree(tmp_path)
    assert not report.passed
    assert report.findings[0].surface == "raw_agent_authority_parser_call"
