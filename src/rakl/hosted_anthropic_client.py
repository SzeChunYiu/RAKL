"""Anthropic-compatible hosted client for GLM-5.2 via the Z.AI gateway.

Matches the ``claude-cn`` operator profile: same base URL, auth header pattern,
and environment variable names. Credentials are read from the process environment
only and must never be written to result artifacts.

Required environment variables::

    ANTHROPIC_BASE_URL   e.g. https://api.z.ai/api/anthropic
    ANTHROPIC_AUTH_TOKEN provider API key (``x-api-key`` header)

Optional (same names as ``~/.claude-cn.env``)::

    ANTHROPIC_MODEL              default model id (``glm-5.2``)
    RUN_MODEL                    script override; wins when set after import
    API_TIMEOUT_MS               request timeout in milliseconds
    GLM52_MAX_RETRIES            transport retries (default 2)

Typical setup::

    source ~/.claude-cn.env
    export RUN_MODEL=glm-5.2   # optional override for harness scripts
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

REQUIRED_ENV_VARS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")
DEFAULT_MODEL = "glm-5.2"
DEFAULT_TIMEOUT_MS = 300000
DEFAULT_MAX_RETRIES = 2


@dataclass(frozen=True)
class HostedAnthropicConfig:
    base_url: str
    model: str
    timeout_s: float
    max_retries: int

    @classmethod
    def from_environ(cls) -> HostedAnthropicConfig:
        missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(
                f"missing required hosted-provider environment variable(s): {joined}. "
                "Source ~/.claude-cn.env or export ANTHROPIC_BASE_URL and "
                "ANTHROPIC_AUTH_TOKEN before running hosted GLM harnesses."
            )
        model = os.environ.get("RUN_MODEL") or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
        timeout_ms = int(os.environ.get("API_TIMEOUT_MS", str(DEFAULT_TIMEOUT_MS)))
        max_retries = int(os.environ.get("GLM52_MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))
        return cls(
            base_url=os.environ["ANTHROPIC_BASE_URL"].rstrip("/"),
            model=model,
            timeout_s=max(1.0, timeout_ms / 1000.0),
            max_retries=max(0, max_retries),
        )


@dataclass(frozen=True)
class ProviderResponse:
    text: str | None
    error: str | None
    latency_s: float
    usage: dict[str, Any]


class AnthropicCompatClient:
    """Minimal Anthropic Messages API client for hosted GLM-5.2 endpoints."""

    def __init__(self, config: HostedAnthropicConfig | None = None) -> None:
        self._config = config or HostedAnthropicConfig.from_environ()
        self._token = os.environ["ANTHROPIC_AUTH_TOKEN"]

    @property
    def base_url(self) -> str:
        return self._config.base_url

    @property
    def model(self) -> str:
        return self._config.model

    def complete(
        self,
        *,
        user: str,
        system: str = "",
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        body: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            body["system"] = system
        payload = json.dumps(body).encode("utf-8")
        last_error: str | None = None
        for attempt in range(self._config.max_retries + 1):
            req = urllib.request.Request(
                f"{self._config.base_url}/v1/messages",
                data=payload,
                headers={
                    "x-api-key": self._token,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            started = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=self._config.timeout_s) as resp:
                    data = json.load(resp)
                text = "".join(
                    part.get("text", "")
                    for part in data.get("content", [])
                    if part.get("type") == "text"
                )
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                return ProviderResponse(
                    text=text,
                    error=None,
                    latency_s=time.monotonic() - started,
                    usage=usage,
                )
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self._config.max_retries:
                    time.sleep(min(2**attempt, 4))
        return ProviderResponse(text=None, error=last_error, latency_s=0.0, usage={})

    def __repr__(self) -> str:
        return f"AnthropicCompatClient(base_url={self._config.base_url!r}, model={self._config.model!r})"


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse one JSON object from a model response without accepting trailing prose."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1])
            if stripped.lstrip().startswith("json"):
                stripped = stripped.lstrip()[4:].lstrip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found")
    obj = json.loads(stripped[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON value is not an object")
    return obj
