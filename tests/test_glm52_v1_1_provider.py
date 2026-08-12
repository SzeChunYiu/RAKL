from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "research" / "glm52_mechanism_suite_v1_1"

if str(SUITE) not in sys.path:
    sys.path.insert(0, str(SUITE))


def test_provider_reexports_canonical_client():
    provider = importlib.import_module("provider")
    from rakl.hosted_anthropic_client import AnthropicCompatClient, REQUIRED_ENV_VARS

    assert provider.REQUIRED_ENV_VARS == REQUIRED_ENV_VARS
    assert provider.AnthropicCompatClient is AnthropicCompatClient


def test_hosted_provider_config_matches_claude_cn_profile():
    cfg = json.loads((SUITE / "HOSTED_PROVIDER_CONFIG.json").read_text(encoding="utf-8"))
    assert cfg["hosted_api_profile"] == "claude-cn"
    assert cfg["required_env_vars"] == ["ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"]
    assert cfg["default_base_url"] == "https://api.z.ai/api/anthropic"
    assert cfg["default_model"] == "glm-5.2"
    assert cfg["credential_policy"]["env_only"] is True
    assert "72bd139f" not in json.dumps(cfg)


def test_protocol_and_docs_contain_no_credential_values():
    protocol = (SUITE / "PROTOCOL_V1_1.md").read_text(encoding="utf-8")
    adapter_spec = (SUITE / "FRAMEWORK_ADAPTER_SPEC.md").read_text(encoding="utf-8")
    readme = (SUITE / "README.md").read_text(encoding="utf-8")
    for text in (protocol, adapter_spec, readme):
        assert "ANTHROPIC_AUTH_TOKEN" in text or "ANTHROPIC_BASE_URL" in text
        assert "72bd139f" not in text
        assert "export ANTHROPIC_AUTH_TOKEN=" not in text
