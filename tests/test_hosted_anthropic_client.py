import os

import pytest

from rakl.hosted_anthropic_client import (
    AnthropicCompatClient,
    DEFAULT_MODEL,
    HostedAnthropicConfig,
    REQUIRED_ENV_VARS,
)


def test_required_env_vars_list_matches_claude_cn_profile():
    assert REQUIRED_ENV_VARS == ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")


def test_from_environ_missing_vars_fail_closed(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_BASE_URL"):
        HostedAnthropicConfig.from_environ()


def test_from_environ_reads_claude_cn_style_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("ANTHROPIC_MODEL", "glm-5.2")
    monkeypatch.setenv("API_TIMEOUT_MS", "120000")
    monkeypatch.setenv("GLM52_MAX_RETRIES", "1")
    monkeypatch.delenv("RUN_MODEL", raising=False)
    cfg = HostedAnthropicConfig.from_environ()
    assert cfg.base_url == "https://api.z.ai/api/anthropic"
    assert cfg.model == "glm-5.2"
    assert cfg.timeout_s == 120.0
    assert cfg.max_retries == 1


def test_run_model_overrides_anthropic_model(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("ANTHROPIC_MODEL", "glm-5.2")
    monkeypatch.setenv("RUN_MODEL", "glm-5.2-custom")
    cfg = HostedAnthropicConfig.from_environ()
    assert cfg.model == "glm-5.2-custom"


def test_default_model_when_optional_vars_absent(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic/")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("RUN_MODEL", raising=False)
    cfg = HostedAnthropicConfig.from_environ()
    assert cfg.base_url == "https://api.z.ai/api/anthropic"
    assert cfg.model == DEFAULT_MODEL


def test_client_repr_never_contains_token(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "super-secret-token-value")
    client = AnthropicCompatClient()
    text = repr(client)
    assert "super-secret-token-value" not in text
    assert "ANTHROPIC_AUTH_TOKEN" not in text
