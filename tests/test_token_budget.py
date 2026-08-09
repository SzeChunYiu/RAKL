import json
import sys
from pathlib import Path

from rakl.reference_profile import get_reference_profile
from rakl.token_budget import (
    PacketBudgetVerdict,
    TokenCountAuthority,
    TokenCountVerdict,
    TokenCounterContract,
    certify_packet_budget,
    count_tokens_exact,
)


def _script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / f"counter-{len(list(tmp_path.glob('counter-*.py')))}.py"
    path.write_text(body, encoding="utf-8")
    return path


def _contract(path: Path, *args: str) -> TokenCounterContract:
    return TokenCounterContract("test-counter", "v1", (sys.executable, str(path), *args))


def test_exact_counter_certificate_binds_subject_and_counter(tmp_path):
    script = _script(tmp_path, "import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({'tokens':len(r['text'].split())}))\n")
    payload = b"one two three"
    report = count_tokens_exact(payload, _contract(script))
    assert report.verdict == TokenCountVerdict.COUNTED
    cert = report.certificate
    assert cert.measured_tokens == 3
    assert cert.authority == TokenCountAuthority.EXACT_EXECUTED_COUNTER
    assert cert.authority_scope == "ENGINEERING_TOKEN_MEASUREMENT_ONLY"
    assert cert.payload_size_bytes == len(payload)


def test_counter_failures_never_invent_count(tmp_path):
    nonzero = _script(tmp_path, "import sys\nsys.exit(3)\n")
    malformed = _script(tmp_path, "print('oops')\n")
    negative = _script(tmp_path, "print('{\"tokens\":-1}')\n")
    for script in (nonzero, malformed, negative):
        report = count_tokens_exact(b"abc", _contract(script))
        assert report.verdict == TokenCountVerdict.CANNOT_CHECK
        assert report.certificate is None


def test_different_payload_has_different_certificate_subject(tmp_path):
    script = _script(tmp_path, "import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({'tokens':1}))\n")
    a = count_tokens_exact(b"a", _contract(script)).certificate
    b = count_tokens_exact(b"b", _contract(script)).certificate
    assert a.payload_sha256 != b.payload_sha256


def test_strict_budget_without_counter_is_cannot_check():
    report = certify_packet_budget(b"{}", get_reference_profile("ordinary-8k"), counter=None)
    assert report.verdict == PacketBudgetVerdict.CANNOT_CHECK
    assert report.exact_packet_tokens is None


def test_exact_budget_boundaries(tmp_path):
    profile = get_reference_profile("ordinary-8k")
    limit = profile.input_budget_tokens + profile.reserved_protocol_tokens
    script = _script(tmp_path, "import json,sys\nr=json.load(sys.stdin)\nprint(json.dumps({'tokens':int(sys.argv[1])}))\n")
    within = certify_packet_budget(b"{}", profile, counter=_contract(script, str(limit)))
    over = certify_packet_budget(b"{}", profile, counter=_contract(script, str(limit + 1)))
    assert within.verdict == PacketBudgetVerdict.WITHIN_BUDGET
    assert over.verdict == PacketBudgetVerdict.OVER_BUDGET


def test_shell_metacharacters_are_literal_counter_args(tmp_path):
    marker = tmp_path / "SHOULD_NOT_EXIST"
    literal = f";touch {marker}"
    script = _script(tmp_path, "import json,sys\nr=json.load(sys.stdin)\nassert sys.argv[1].startswith(';touch ')\nprint(json.dumps({'tokens':1}))\n")
    report = count_tokens_exact(b"abc", _contract(script, literal))
    assert report.verdict == TokenCountVerdict.COUNTED
    assert not marker.exists()
