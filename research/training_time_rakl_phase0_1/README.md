# Training-time RAKL Phase 0/1 (#461)

**Parent:** #455  
**Lane:** separate from GLM/Paper-II metrology and Paper-V causal arms  
**Status:** protocol frozen pre-outcome; no learner runs executed

## Scientific question

Does a learner-conditioned structural residual exist that is measurable via
registered exposure curves before any adaptive allocation policy is studied?

## Claim boundary

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).

## Artifacts

| File | Role |
|------|------|
| `PROTOCOL_FREEZE_PACKET.json` | Pre-outcome freeze |
| `PROTOCOL_FREEZE_RECEIPT.json` | Freeze validation receipt |

## Code

| Path | Role |
|------|------|
| `src/rakl/training_ladder/` | Generator, verifier, hostile controls, exposure scaffold |
| `experiments/training_ladder/freeze_protocol.py` | Freeze builder/validator |

## Hard blocks

- **#466** — blocked until `MECHANISM_SIGNAL_PRESENT`
- **#467** — blocked until `ADAPTIVE_RESIDUAL_SUPPORTED` from #466
