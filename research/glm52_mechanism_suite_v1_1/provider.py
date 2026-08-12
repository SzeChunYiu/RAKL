"""Suite-local provider binding — delegates to canonical hosted client.

Matches the claude-cn operator profile (Z.AI Anthropic-compatible gateway).
Credentials are env-only; never serialized to suite artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rakl.hosted_anthropic_client import (
    AnthropicCompatClient,
    HostedAnthropicConfig,
    ProviderResponse,
    REQUIRED_ENV_VARS,
    extract_json_object,
)

__all__ = [
    "AnthropicCompatClient",
    "HostedAnthropicConfig",
    "ProviderResponse",
    "REQUIRED_ENV_VARS",
    "extract_json_object",
]
