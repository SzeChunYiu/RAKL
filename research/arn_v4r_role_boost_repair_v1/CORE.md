# ARN v4 role_boost repair — CORE

**Terminal: `REPAIR_FAILED__LEAK_PERSISTS`.** The negative is not revivable by its recorded lever,
and the lever itself is refuted by execution.

## What was attempted

`p2-arn-v4-battery-failed` is one of twelve `REVIVABLE_LOCAL` negatives. Its recorded lever:

> restore v3's instance-paired property (remove/instance-pair role_boost)

and its recorded cause: *the role_boost component (exact token matches) introduced marginal
statistics that survive label shuffling.* The battery failed on `B3_shuffled_gold` at advantage
**0.1347**, CI [0.105, 0.163].

Exactly one term was changed, behind a weight defaulting to the current value so the leaking arm
stays byte-reproducible. Support was declared before freezing — the population demonstrably supports
the measurement, since B3 produced the leak on it.

## What happened

| Arm | B3 advantage | CI |
|---|---|---|
| committed v4 | 0.1346739299610895 | [0.1054, 0.1634] |
| baseline, w=0.2 | **0.1346739299610895** | [0.1054, 0.1634] |
| repair, w=0.0 | 0.1340513618677043 | [0.1049, 0.1627] |

The baseline reproduces the committed v4 exactly. Removing `role_boost` **entirely** moves the
shuffled-gold advantage by **0.000623**.

`R1_leak_must_die` fails. Per the frozen rule the confirmatory advantage is deliberately **not**
read: reporting a G1 number from an instrument that still leaks is the defect under repair.

## The finding

**The lever is wrong.** The leak was never in `role_boost`, so restoring the instance-paired
property cannot repair this battery — and no weight sweep would help, which is why the protocol
froze the single value 0.0 in advance.

Where it actually is, already established on `main` and independently confirmed by this run:
Paper II, *Case 4 — the shuffle null measured abstention, not binding* (#709, #712). Where the
decision space includes abstention and the statistic is a proper score, the shuffle probe measures
**differential abstention** rather than binding. An instrument that abstains more than its control
cannot pass it, whatever its scoring terms — because under shuffled labels abstention (Brier 0.25)
beats confident error (Brier ~0.96) by construction.

## Consequence for the frontier

`research/negative_frontier_v1` record `p2-arn-v4-battery-failed` carries a `core_lever` that
predates #709. It is **stale**. The negative is not revivable as written, and the successor route is
the repaired probe restricted to items on which both compared arms are decisive.

That successor is a different experiment and needs its own freeze. Continuing into it under this
protocol would be the post-hoc amendment the invariants forbid.

## What this cost and what it bought

One deterministic local run, no hosted model, no new annotation. It converts a negative whose stated
revival path looked cheap into one whose stated revival path is **known false** — and it does so by
execution rather than by re-reading the record.

## Reproduce

```bash
PYTHONPATH=src RAKL_ARN_ROLE_BOOST_WEIGHT=0.0 python scripts/paper2_external_corpus_confirmatory_v4.py \
  --csv research/paper2_external_corpus_v1/data/arn.csv --out /tmp/v4_repair
python research/arn_v4r_role_boost_repair_v1/record_result.py
```
