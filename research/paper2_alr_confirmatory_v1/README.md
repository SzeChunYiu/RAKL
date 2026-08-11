# Paper II confirmatory ALR v1 (#324)

**Terminal:** `CANNOT_EXECUTE_CONFIRMATORY_MODEL_COMPARISON`

Freezes confirmatory protocol, V2 panel binding, arms, prompt-parity rules,
and co-primary ALR + valid-upgrade-recall inference plan. Execution remains
fail-closed under the #247 capability floor and unexecuted typed-authority arm.

Non-confirmatory #154 baselines are retained as instrument history only.

Reproduce:

```bash
PYTHONPATH=src python scripts/paper2_alr_confirmatory_finalize.py
pytest tests/test_paper2_alr_confirmatory.py -q
```
