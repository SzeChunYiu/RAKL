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

## Mac-local runs (hosted API)

**Yes — GLM-5.2 runs from a Mac with network.** There is no local-weight path for
GLM in this repository; inference is always via the Z.AI hosted gateway. LUNARC is
not required for GLM specifically unless you need batch scale or unrelated local
transformers jobs (e.g. sealed 7B oracle runs).

Operator profile: `source ~/.claude-cn.env` (file must define at least
`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN`; optional `ANTHROPIC_MODEL=glm-5.2`).

### Offline (no API)

```bash
python research/glm52_mechanism_suite_v1_1/offline_selftest.py
python research/glm52_mechanism_suite_v1/offline_selftest.py
pytest tests/test_hosted_anthropic_client.py tests/test_glm52_v1_1_provider.py tests/test_glm52_v1_1_wave2_harness.py
```

### Hosted smoke (one cheap call; non-confirmatory)

```bash
source ~/.claude-cn.env
python scripts/glm52_hosted_smoke.py
```

### Non-confirmatory pilot harnesses (authorized; API cost)

Wave 2 v1.1 lanes are **offline stubs only** until dev gates pass. v1 dev runs
may call the API from Mac:

```bash
source ~/.claude-cn.env
cd research/glm52_mechanism_suite_v1
python run_suite.py dev --n 8
```

Historical hosted diagnostics (not sealed, not weight-attested):

```bash
source ~/.claude-cn.env
python research/paper2_hosted_capability_probe_v1/run_hosted_arm_comparison.py
```

### Blocked on Mac (same gates as cluster)

- **Confirmatory empirics** for GLM52 mechanism suite v1/v1.1 until all non-RAKL
  dev gates pass (`outcome_access: NO_NEW_GLM_OUTCOME`).
- **Sealed local-provider confirmatory** — requires weight-attested local
  transformers runs (LUNARC); hosted GLM cannot substitute.
- **Wave-2 confirmatory unlock** while `CAPABLE_MODEL_AVAILABLE=NO_REFUTED` on
  frozen oracle receipts (`wave2_confirmatory_unlocked: false`).

## Consumers

- `research/paper2_hosted_capability_probe_v1/`
- `research/paper2_graded_battery_v1/`
- `research/glm52_mechanism_suite_v1/` (main) — migrate provider to shared client
- `research/glm52_mechanism_suite_v1_1/` (scaffold) — bind `FRAMEWORK_ADAPTER_SPEC` here
- `scripts/glm52_hosted_smoke.py` — Mac/cluster connectivity smoke
