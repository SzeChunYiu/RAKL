# Hosted GLM-5.2 API — claude-cn alignment

GLM-5.2 harnesses in this repository call the **Z.AI** Anthropic-compatible
Messages API—the same gateway configured for the operator ``claude-cn`` profile
(`~/.claude-cn.env`, `~/.claude-cn/settings.json`).

## Environment variables

| Variable | Required | Role |
|---|---|---|
| `ANTHROPIC_BASE_URL` | yes | Gateway base URL (`https://api.z.ai/api/anthropic`) |
| `ANTHROPIC_AUTH_TOKEN` | yes | API key sent as `x-api-key` |
| `ANTHROPIC_MODEL` | no | Default model id (`glm-5.2`) |
| `RUN_MODEL` | no | Harness override (wins over `ANTHROPIC_MODEL`) |
| `API_TIMEOUT_MS` | no | Request timeout in ms (claude-cn default: `300000`) |
| `GLM52_MAX_RETRIES` | no | Transport retries (default: `2`) |

Claude Code tier aliases (`ANTHROPIC_DEFAULT_SONNET_MODEL`, etc.) are set in
`~/.claude-cn.env` for the IDE agent only; harness scripts do not require them.

## Canonical implementation

`src/rakl/hosted_anthropic_client.py` — shared by Paper II hosted probes and
intended for `research/glm52_mechanism_suite_v1_1/` provider bindings.

## Security

- Env-only credentials; never commit keys or mirror them into result JSON.
- `source ~/.claude-cn.env` is the supported operator workflow.
- Result artifacts must not contain `ANTHROPIC_AUTH_TOKEN`.

## Consumers

- `research/paper2_hosted_capability_probe_v1/`
- `research/paper2_graded_battery_v1/`
- `research/glm52_mechanism_suite_v1/` (main) — migrate provider to shared client
- `research/glm52_mechanism_suite_v1_1/` (scaffold) — bind `FRAMEWORK_ADAPTER_SPEC` here
