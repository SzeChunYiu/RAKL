# Paper III confirmatory power design (#248)

Status: `CONFIRMATORY_PACKET_POWER_LIMITED` (path C)

## Hard chronology

- Zero-label status at decision: `ZERO_LABELS_VERIFIED`
- Git subject: `e10f2320b0ee38c45bcc57e76d07be5e6055e016`

## Registered primary quantity

- `paired_item_brier_reduction`
- Material MDE: **0.05** mean paired Brier reduction
- Target power: 0.8 at alpha=0.05

## Headline simulation result

- n=16 power at MDE: **0.225**
- Smallest n in grid reaching target: `None`
- LOFO train n on current packet: 12

## Decision

n=16 Monte Carlo power at MDE=0.05 is 0.225, below target 0.8. No n in the registered grid reached target power under the simulation model. Retain v2.1 as an exploratory / limited-sample human validation. Wide nulls and INDISTINGUISHABLE / UNDERPOWERED outcomes are inconclusive, not refutation. Do not expand after any label arrives.

## Manuscript wording

power-limited exploratory/limited-sample human validation

## Interpretation rules

- UNDERPOWERED/INDISTINGUISHABLE: Treat as inconclusive for confirmatory claims; do not market as refutation of structural-witness value.
- Decoupling rate: If post-adjudication decoupling_rate==0 for transfer_valid vs AND(invariant,boundary,qoi,directional), report witnessed_structure as NOT_INFORMATIVE regardless of AUC.

## Family metadata

Before #217 annotator work, export an annotator-facing packet that omits or hashes `family` while preserving opaque item_id. Do not change source texts after labels.

## Authority

Proposal-only design freeze. Grants no scientific authority and does not authorize training.
