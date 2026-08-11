# Paper 5 active sham-memory policy v1

**Status:** algorithm identity frozen; confirmatory four-arm execution unauthorized  
**Grants scientific authority:** no  
**Authorizes confirmatory execution:** no  
**Evaluated results accessed:** no

## What this is

Frozen construction policy + matcher/validator for the `RAKL_SHAM_MEMORY` arm required by `experiments/paper5/ATTRIBUTION_PREREGISTRATION_V1.md` §4 and by `--sham-policy-hash` in `experiments/paper5/build_executor_contract.py`.

Artifacts:

| File | Role |
|---|---|
| `SHAM_POLICY.json` | Frozen algorithm identity (`policy_canonical_sha256`) |
| `SHAM_POLICY_FREEZE_RECEIPT.json` | Hash binding of policy, schema, matcher module, preregistration |
| `../experiments/paper5/active_sham.py` | Active construction matcher + hostile leakage validator |
| `../../schemas/paper5-sham-policy-v1.schema.json` | Schema |

## What this is not

- Not a confirmatory packet freeze (`CONFIRMATORY_PACKET_FROZEN_AND_EXECUTABLE` remains forbidden).
- Not authorization to run the four-arm study (#251 lineage).
- Not a claim that memory content matters; that contrast still requires a capable model and a full packet freeze.

## Policy hash

Use `SHAM_POLICY.json` → `policy_canonical_sha256` as `--sham-policy-hash` when assembling a *non-confirmatory* contract draft. Confirmatory execution stays blocked until `CAPABLE_MODEL` + full packet freeze.

Validate:

```bash
python experiments/paper5/active_sham.py validate-policy
python -m pytest tests/test_paper5_active_sham.py -q
```
