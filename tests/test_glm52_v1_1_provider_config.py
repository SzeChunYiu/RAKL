import os

import pytest

from rakl.hosted_anthropic_client import (
    AnthropicCompatClient,
    DEFAULT_MODEL,
    HostedAnthropicConfig,
    REQUIRED_ENV_VARS,
)


def test_required_env_vars_match_claude_cn_profile():
    assert REQUIRED_ENV_VARS == ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")


def test_suite_provider_reexports_shared_client():
    import importlib
    import sys
    from pathlib import Path

    suite = Path(__file__).resolve().parents[1] / "research" / "glm52_mechanism_suite_v1_1"
    sys.path.insert(0, str(suite))
    provider = importlib.import_module("provider")
    assert provider.REQUIRED_ENV_VARS == REQUIRED_ENV_VARS
    assert provider.AnthropicCompatClient is AnthropicCompatClient


def test_from_environ_uses_claude_cn_style_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("ANTHROPIC_MODEL", "glm-5.2")
    monkeypatch.delenv("RUN_MODEL", raising=False)
    cfg = HostedAnthropicConfig.from_environ()
    assert cfg.base_url == "https://api.z.ai/api/anthropic"
    assert cfg.model == "glm-5.2"


def test_missing_env_fail_closed(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_BASE_URL"):
        HostedAnthropicConfig.from_environ()


def test_v1_1_docs_reference_env_only_credentials():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    protocol = (root / "research/glm52_mechanism_suite_v1_1/PROTOCOL_V1_1.md").read_text(encoding="utf-8")
    assert "source ~/.claude-cn.env" in protocol
    assert "ANTHROPIC_BASE_URL" in protocol
    assert "72bd139f" not in protocol


def test_client_repr_never_contains_token(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "super-secret-token-value")
    client = AnthropicCompatClient()
    text = repr(client)
    assert "super-secret-token-value" not in text
    assert os.environ["ANTHROPIC_AUTH_TOKEN"] not in text
